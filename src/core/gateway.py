"""
Gateway WebSocket Control Plane

OpenClaw-inspired Gateway architecture for unified control plane.
Handles all messaging surfaces, clients, and nodes over a single WebSocket server.
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, Set, Optional, Any, List
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import secrets

logger = logging.getLogger(__name__)


class ClientRole(Enum):
    """Client connection roles"""
    CLIENT = "client"  # CLI, web UI, macOS app
    NODE = "node"      # iOS/Android/macOS nodes with device capabilities
    CHANNEL = "channel"  # Messaging platform connections


class ConnectionState(Enum):
    """Connection lifecycle states"""
    CONNECTING = "connecting"
    AUTHENTICATING = "authenticating"
    PAIRED = "paired"
    ACTIVE = "active"
    DISCONNECTED = "disconnected"


@dataclass
class DeviceIdentity:
    """Device identification for pairing"""
    device_id: str
    device_name: str
    platform: str  # macos, ios, android, web, cli
    app_version: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)


@dataclass
class NodeCapabilities:
    """Node device capabilities"""
    commands: List[str]  # e.g., ["canvas", "camera", "screen", "location"]
    permissions: Dict[str, bool]  # e.g., {"camera": true, "screen_recording": false}
    
    def to_dict(self):
        return asdict(self)


class GatewayClient:
    """Represents a connected client"""
    
    def __init__(
        self,
        client_id: str,
        websocket,
        role: ClientRole,
        device: DeviceIdentity,
        capabilities: Optional[NodeCapabilities] = None
    ):
        self.client_id = client_id
        self.websocket = websocket
        self.role = role
        self.device = device
        self.capabilities = capabilities
        self.state = ConnectionState.CONNECTING
        self.connected_at = datetime.now()
        self.last_seen = datetime.now()
        self.device_token: Optional[str] = None
        self.subscriptions: Set[str] = set()
        
    def to_dict(self):
        return {
            "client_id": self.client_id,
            "role": self.role.value,
            "device": self.device.to_dict(),
            "capabilities": self.capabilities.to_dict() if self.capabilities else None,
            "state": self.state.value,
            "connected_at": self.connected_at.isoformat(),
            "last_seen": self.last_seen.isoformat(),
        }


class GatewayProtocol:
    """Gateway WebSocket protocol handler"""
    
    # Protocol version
    VERSION = "1.0.0"
    
    # Message types
    TYPE_REQ = "req"      # Client request
    TYPE_RES = "res"      # Server response
    TYPE_EVENT = "event"  # Server-push event
    
    @staticmethod
    def create_response(req_id: str, ok: bool, payload: Any = None, error: str = None) -> str:
        """Create protocol response"""
        msg = {
            "type": GatewayProtocol.TYPE_RES,
            "id": req_id,
            "ok": ok
        }
        if payload is not None:
            msg["payload"] = payload
        if error is not None:
            msg["error"] = error
        return json.dumps(msg)
    
    @staticmethod
    def create_event(event: str, payload: Any, seq: Optional[int] = None) -> str:
        """Create protocol event"""
        msg = {
            "type": GatewayProtocol.TYPE_EVENT,
            "event": event,
            "payload": payload
        }
        if seq is not None:
            msg["seq"] = seq
        return json.dumps(msg)
    
    @staticmethod
    def parse_message(message: str) -> Dict[str, Any]:
        """Parse incoming message"""
        try:
            return json.loads(message)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")


class DevicePairingStore:
    """Store for approved device pairings"""
    
    def __init__(self):
        self._approved_devices: Dict[str, Dict[str, Any]] = {}
        self._pending_approvals: Dict[str, Dict[str, Any]] = {}
    
    def generate_device_token(self, device_id: str) -> str:
        """Generate secure device token"""
        return f"otto_device_{secrets.token_urlsafe(32)}"
    
    def request_approval(self, device: DeviceIdentity, challenge: str) -> str:
        """Request pairing approval, returns pairing code"""
        pairing_code = secrets.token_hex(3).upper()  # 6-char code
        self._pending_approvals[pairing_code] = {
            "device": device.to_dict(),
            "challenge": challenge,
            "requested_at": datetime.now().isoformat()
        }
        return pairing_code
    
    def approve_pairing(self, pairing_code: str) -> Optional[str]:
        """Approve a pending pairing, returns device token"""
        if pairing_code not in self._pending_approvals:
            return None
        
        pending = self._pending_approvals.pop(pairing_code)
        device_dict = pending["device"]
        device_id = device_dict["device_id"]
        
        device_token = self.generate_device_token(device_id)
        self._approved_devices[device_id] = {
            "device": device_dict,
            "token": device_token,
            "approved_at": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Device paired: {device_id} ({device_dict['device_name']})")
        return device_token
    
    def is_approved(self, device_id: str) -> bool:
        """Check if device is approved"""
        return device_id in self._approved_devices
    
    def verify_token(self, device_id: str, token: str) -> bool:
        """Verify device token"""
        if device_id not in self._approved_devices:
            return False
        return self._approved_devices[device_id]["token"] == token
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all pending approvals"""
        return [
            {"code": code, **data}
            for code, data in self._pending_approvals.items()
        ]


class OttoGateway:
    """
    Otto Gateway - Unified WebSocket control plane
    
    Inspired by OpenClaw's architecture:
    - Single daemon for all control
    - WebSocket protocol for clients/nodes
    - Device pairing with approval flow
    - Event streaming
    - Multi-channel support
    """
    
    def __init__(self, orchestrator=None, host: str = "127.0.0.1", port: int = 18789):
        self.orchestrator = orchestrator
        self.host = host
        self.port = port
        self.clients: Dict[str, GatewayClient] = {}
        self.pairing_store = DevicePairingStore()
        self.event_seq = 0
        self.started_at = datetime.now()
        
        # Messaging channels (to be integrated)
        self.channels: Dict[str, Any] = {}
        
        # Request deduplication cache
        self._idempotency_cache: Dict[str, Any] = {}
    
    def register_channel(self, channel_type, channel_instance):
        """Register a messaging channel"""
        self.channels[channel_type] = channel_instance
        logger.info(f"📡 Registered channel: {channel_type.value}")
        
    async def handle_connect(self, client: GatewayClient, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initial connect handshake"""
        
        # Extract device info
        device_dict = params.get("device", {})
        if not device_dict:
            raise ValueError("Device identity required")
        
        # Check authentication if required
        auth = params.get("auth", {})
        token = auth.get("token")
        
        # Check if device needs pairing
        device_id = device_dict.get("device_id")
        
        if client.role == ClientRole.NODE:
            # Nodes require pairing
            if not self.pairing_store.is_approved(device_id):
                # Request pairing
                challenge = secrets.token_hex(16)
                pairing_code = self.pairing_store.request_approval(client.device, challenge)
                
                logger.warning(f"🔐 Device pairing required: {device_id}")
                logger.info(f"📱 Pairing code: {pairing_code}")
                
                return {
                    "status": "pairing_required",
                    "pairing_code": pairing_code,
                    "message": f"Approve with: otto pairing approve {pairing_code}"
                }
            
            # Verify device token
            device_token = auth.get("device_token")
            if not device_token or not self.pairing_store.verify_token(device_id, device_token):
                raise ValueError("Invalid device token")
            
            client.device_token = device_token
            client.state = ConnectionState.PAIRED
        
        client.state = ConnectionState.ACTIVE
        
        # Send hello-ok with gateway state
        return {
            "status": "connected",
            "gateway_version": GatewayProtocol.VERSION,
            "client_id": client.client_id,
            "server_time": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - self.started_at).total_seconds()
        }
    
    async def handle_request(
        self,
        client: GatewayClient,
        req_id: str,
        method: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle client request"""
        
        # Check idempotency
        idempotency_key = params.get("idempotency_key")
        if idempotency_key:
            cache_key = f"{client.client_id}:{idempotency_key}"
            if cache_key in self._idempotency_cache:
                logger.debug(f"Returning cached response for {cache_key}")
                return self._idempotency_cache[cache_key]
        
        # Route method
        handler_map = {
            "health": self._handle_health,
            "status": self._handle_status,
            "send": self._handle_send,
            "agent": self._handle_agent,
            "sessions.list": self._handle_sessions_list,
            "nodes.list": self._handle_nodes_list,
            "nodes.invoke": self._handle_nodes_invoke,
            "pairing.pending": self._handle_pairing_pending,
            "pairing.approve": self._handle_pairing_approve,
        }
        
        handler = handler_map.get(method)
        if not handler:
            raise ValueError(f"Unknown method: {method}")
        
        result = await handler(client, params)
        
        # Cache if idempotent
        if idempotency_key:
            cache_key = f"{client.client_id}:{idempotency_key}"
            self._idempotency_cache[cache_key] = result
        
        return result
    
    async def _handle_health(self, client: GatewayClient, params: Dict[str, Any]) -> Dict[str, Any]:
        """Health check"""
        return {
            "status": "healthy",
            "version": GatewayProtocol.VERSION,
            "uptime_seconds": (datetime.now() - self.started_at).total_seconds(),
            "clients_connected": len([c for c in self.clients.values() if c.state == ConnectionState.ACTIVE]),
            "channels_active": len(self.channels)
        }
    
    async def _handle_status(self, client: GatewayClient, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get gateway status"""
        return {
            "clients": len(self.clients),
            "nodes": len([c for c in self.clients.values() if c.role == ClientRole.NODE]),
            "channels": list(self.channels.keys())
        }
    
    async def _handle_send(self, client: GatewayClient, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send message to a channel"""
        # TODO: Implement channel routing
        return {"status": "queued", "message_id": str(uuid.uuid4())}
    
    async def _handle_agent(self, client: GatewayClient, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run agent task"""
        # TODO: Integrate with existing agent system
        run_id = str(uuid.uuid4())
        return {
            "status": "accepted",
            "run_id": run_id
        }
    
    async def _handle_sessions_list(self, client: GatewayClient, params: Dict[str, Any]) -> Dict[str, Any]:
        """List active sessions"""
        # TODO: Integrate with session manager
        return {"sessions": []}
    
    async def _handle_nodes_list(self, client: GatewayClient, params: Dict[str, Any]) -> Dict[str, Any]:
        """List connected nodes"""
        nodes = [
            c.to_dict()
            for c in self.clients.values()
            if c.role == ClientRole.NODE and c.state == ConnectionState.ACTIVE
        ]
        return {"nodes": nodes}
    
    async def _handle_nodes_invoke(self, client: GatewayClient, params: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke command on a node"""
        node_id = params.get("node_id")
        command = params.get("command")
        
        # Find target node
        target_node = None
        for c in self.clients.values():
            if c.role == ClientRole.NODE and c.client_id == node_id:
                target_node = c
                break
        
        if not target_node:
            raise ValueError(f"Node not found: {node_id}")
        
        # TODO: Forward command to node and wait for response
        return {"status": "executed", "result": None}
    
    async def _handle_pairing_pending(self, client: GatewayClient, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get pending pairing approvals"""
        return {
            "pending": self.pairing_store.get_pending_approvals()
        }
    
    async def _handle_pairing_approve(self, client: GatewayClient, params: Dict[str, Any]) -> Dict[str, Any]:
        """Approve a pairing request"""
        pairing_code = params.get("code")
        if not pairing_code:
            raise ValueError("Pairing code required")
        
        device_token = self.pairing_store.approve_pairing(pairing_code)
        if not device_token:
            raise ValueError("Invalid or expired pairing code")
        
        return {
            "status": "approved",
            "device_token": device_token
        }
    
    async def broadcast_event(self, event: str, payload: Any, exclude_client: Optional[str] = None):
        """Broadcast event to all connected clients"""
        self.event_seq += 1
        message = GatewayProtocol.create_event(event, payload, self.event_seq)
        
        for client in self.clients.values():
            if client.state != ConnectionState.ACTIVE:
                continue
            if exclude_client and client.client_id == exclude_client:
                continue
            
            try:
                await client.websocket.send(message)
            except Exception as e:
                logger.error(f"Failed to send event to {client.client_id}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get gateway statistics"""
        return {
            "started_at": self.started_at.isoformat(),
            "uptime_seconds": (datetime.now() - self.started_at).total_seconds(),
            "total_clients": len(self.clients),
            "active_clients": len([c for c in self.clients.values() if c.state == ConnectionState.ACTIVE]),
            "nodes": len([c for c in self.clients.values() if c.role == ClientRole.NODE]),
            "channels": len(self.channels),
            "event_seq": self.event_seq
        }
