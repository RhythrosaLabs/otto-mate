"""
Gateway WebSocket Server

FastAPI integration for Otto Gateway WebSocket control plane.
"""

import logging
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, Any

from src.core.gateway import (
    OttoGateway,
    GatewayClient,
    GatewayProtocol,
    ClientRole,
    DeviceIdentity,
    NodeCapabilities,
    ConnectionState
)

logger = logging.getLogger(__name__)

# Singleton gateway instance
_gateway_instance: OttoGateway = None


def get_gateway() -> OttoGateway:
    """Get or create gateway instance"""
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = OttoGateway()
        logger.info(f"🚀 Gateway initialized on ws://{_gateway_instance.host}:{_gateway_instance.port}")
    return _gateway_instance


router = APIRouter(prefix="/gateway", tags=["gateway"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Gateway WebSocket endpoint
    
    Protocol:
    1. Client connects
    2. Send connect frame with device identity
    3. Gateway responds with hello-ok or pairing_required
    4. Client sends requests, receives responses and events
    """
    
    gateway = get_gateway()
    client_id = str(uuid.uuid4())
    client: GatewayClient = None
    
    await websocket.accept()
    logger.info(f"🔌 WebSocket connection: {client_id}")
    
    try:
        # Wait for connect frame (must be first)
        connect_frame = await websocket.receive_text()
        
        try:
            msg = GatewayProtocol.parse_message(connect_frame)
        except ValueError as e:
            await websocket.send_text(
                GatewayProtocol.create_response("", False, error=f"Invalid message: {e}")
            )
            await websocket.close(code=1002)
            return
        
        # Must be a connect request
        if msg.get("type") != GatewayProtocol.TYPE_REQ or msg.get("method") != "connect":
            await websocket.send_text(
                GatewayProtocol.create_response("", False, error="First frame must be connect request")
            )
            await websocket.close(code=1002)
            return
        
        req_id = msg.get("id")
        params = msg.get("params", {})
        
        # Extract device identity
        device_dict = params.get("device", {})
        device = DeviceIdentity(
            device_id=device_dict.get("device_id", f"unknown-{client_id}"),
            device_name=device_dict.get("device_name", "Unknown Device"),
            platform=device_dict.get("platform", "unknown"),
            app_version=device_dict.get("app_version")
        )
        
        # Extract role
        role_str = params.get("role", "client")
        try:
            role = ClientRole(role_str)
        except ValueError:
            role = ClientRole.CLIENT
        
        # Extract capabilities if node
        capabilities = None
        if role == ClientRole.NODE:
            caps_dict = params.get("capabilities", {})
            capabilities = NodeCapabilities(
                commands=caps_dict.get("commands", []),
                permissions=caps_dict.get("permissions", {})
            )
        
        # Create client
        client = GatewayClient(
            client_id=client_id,
            websocket=websocket,
            role=role,
            device=device,
            capabilities=capabilities
        )
        
        gateway.clients[client_id] = client
        
        # Handle connect
        try:
            connect_result = await gateway.handle_connect(client, params)
            
            # Send response
            await websocket.send_text(
                GatewayProtocol.create_response(req_id, True, payload=connect_result)
            )
            
            # If pairing required, wait for disconnect
            if connect_result.get("status") == "pairing_required":
                logger.info(f"⏳ Waiting for pairing approval: {device.device_id}")
                # TODO: Could keep connection open and send event when approved
                return
            
            # Broadcast presence event
            await gateway.broadcast_event(
                "presence",
                {
                    "client_id": client_id,
                    "device": device.to_dict(),
                    "role": role.value,
                    "status": "connected"
                },
                exclude_client=client_id
            )
            
        except Exception as e:
            logger.error(f"Connect failed: {e}")
            await websocket.send_text(
                GatewayProtocol.create_response(req_id, False, error=str(e))
            )
            await websocket.close(code=1011)
            return
        
        # Main message loop
        while True:
            message = await websocket.receive_text()
            
            try:
                msg = GatewayProtocol.parse_message(message)
            except ValueError as e:
                await websocket.send_text(
                    GatewayProtocol.create_response("", False, error=f"Invalid message: {e}")
                )
                continue
            
            msg_type = msg.get("type")
            
            if msg_type == GatewayProtocol.TYPE_REQ:
                # Handle request
                req_id = msg.get("id")
                method = msg.get("method")
                params = msg.get("params", {})
                
                try:
                    result = await gateway.handle_request(client, req_id, method, params)
                    await websocket.send_text(
                        GatewayProtocol.create_response(req_id, True, payload=result)
                    )
                except Exception as e:
                    logger.error(f"Request failed ({method}): {e}")
                    await websocket.send_text(
                        GatewayProtocol.create_response(req_id, False, error=str(e))
                    )
            else:
                # Unknown message type
                await websocket.send_text(
                    GatewayProtocol.create_response("", False, error=f"Unknown message type: {msg_type}")
                )
    
    except WebSocketDisconnect:
        logger.info(f"🔌 Client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        # Cleanup
        if client_id in gateway.clients:
            client = gateway.clients.pop(client_id)
            client.state = ConnectionState.DISCONNECTED
            
            # Broadcast presence event
            await gateway.broadcast_event(
                "presence",
                {
                    "client_id": client_id,
                    "status": "disconnected"
                }
            )


@router.get("/stats")
async def get_gateway_stats():
    """Get gateway statistics"""
    gateway = get_gateway()
    return gateway.get_stats()


@router.get("/clients")
async def list_clients():
    """List connected clients"""
    gateway = get_gateway()
    return {
        "clients": [
            client.to_dict()
            for client in gateway.clients.values()
        ]
    }


@router.get("/pairing/pending")
async def list_pending_pairings():
    """List pending device pairings"""
    gateway = get_gateway()
    return {
        "pending": gateway.pairing_store.get_pending_approvals()
    }


@router.post("/pairing/approve")
async def approve_pairing(code: str):
    """Approve a device pairing"""
    gateway = get_gateway()
    
    device_token = gateway.pairing_store.approve_pairing(code)
    if not device_token:
        raise HTTPException(status_code=404, detail="Invalid or expired pairing code")
    
    return {
        "status": "approved",
        "device_token": device_token
    }


@router.post("/broadcast")
async def broadcast_event(event: str, payload: Dict[str, Any]):
    """Broadcast event to all clients (admin/testing)"""
    gateway = get_gateway()
    await gateway.broadcast_event(event, payload)
    return {"status": "broadcasted", "event": event}
