"""
Otto Universal - WhatsApp Webhook Handler
=========================================

Webhook endpoint for receiving messages from WhatsApp Business API.
Supports both the official WhatsApp Business API and third-party providers.

Setup:
1. Get a WhatsApp Business API account
2. Configure the webhook URL to point to /api/webhooks/whatsapp
3. Set WHATSAPP_VERIFY_TOKEN and WHATSAPP_ACCESS_TOKEN in .env

Supported Providers:
- Meta WhatsApp Business API (official)
- Twilio WhatsApp
- MessageBird WhatsApp
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request, BackgroundTasks
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks/whatsapp", tags=["whatsapp"])


# ============================================================================
# MODELS
# ============================================================================

class WhatsAppMessage(BaseModel):
    """Incoming WhatsApp message."""
    message_id: str = Field(..., alias="id")
    from_number: str = Field(..., alias="from")
    timestamp: str
    type: str  # text, image, document, audio, video, location, contacts, interactive
    text: Optional[Dict[str, Any]] = None
    image: Optional[Dict[str, Any]] = None
    document: Optional[Dict[str, Any]] = None
    audio: Optional[Dict[str, Any]] = None
    video: Optional[Dict[str, Any]] = None
    location: Optional[Dict[str, Any]] = None
    contacts: Optional[List[Dict[str, Any]]] = None
    interactive: Optional[Dict[str, Any]] = None
    
    class Config:
        populate_by_name = True


class WhatsAppWebhookPayload(BaseModel):
    """Meta WhatsApp Business API webhook payload."""
    object: str
    entry: List[Dict[str, Any]]


class WhatsAppOutgoingMessage(BaseModel):
    """Outgoing WhatsApp message."""
    to: str
    type: str = "text"
    text: Optional[Dict[str, str]] = None
    image: Optional[Dict[str, str]] = None
    document: Optional[Dict[str, str]] = None
    template: Optional[Dict[str, Any]] = None


# ============================================================================
# MESSAGE QUEUE
# ============================================================================

class WhatsAppMessageQueue:
    """Simple in-memory message queue for pending messages."""
    
    def __init__(self, max_size: int = 1000):
        self.queue: List[Dict[str, Any]] = []
        self.max_size = max_size
    
    def add(self, message: Dict[str, Any]):
        """Add a message to the queue."""
        if len(self.queue) >= self.max_size:
            self.queue.pop(0)  # Remove oldest
        
        message["queued_at"] = datetime.now().isoformat()
        self.queue.append(message)
    
    def get_pending(self) -> List[Dict[str, Any]]:
        """Get all pending messages."""
        return self.queue.copy()
    
    def get_for_number(self, phone_number: str) -> List[Dict[str, Any]]:
        """Get messages for a specific phone number."""
        return [m for m in self.queue if m.get("from_number") == phone_number]
    
    def clear(self):
        """Clear all messages."""
        self.queue = []


# Singleton instance
_message_queue = WhatsAppMessageQueue()


def get_message_queue() -> WhatsAppMessageQueue:
    """Get the message queue singleton."""
    return _message_queue


# ============================================================================
# WEBHOOK HANDLERS
# ============================================================================

@router.get("")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    """
    Webhook verification endpoint for Meta WhatsApp Business API.
    
    Meta sends a GET request with:
    - hub.mode: should be "subscribe"
    - hub.verify_token: should match your configured token
    - hub.challenge: return this to verify
    """
    import os
    verify_token = os.environ.get("WHATSAPP_VERIFY_TOKEN", "otto_whatsapp_verify")
    
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        logger.info("WhatsApp webhook verified successfully")
        return int(hub_challenge)
    
    logger.warning(f"WhatsApp webhook verification failed: mode={hub_mode}")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Receive incoming WhatsApp messages.
    
    Handles messages from Meta WhatsApp Business API.
    Messages are queued for processing by the Otto orchestrator.
    """
    try:
        body = await request.json()
        logger.debug(f"WhatsApp webhook received: {json.dumps(body, indent=2)}")
        
        # Validate webhook (optional - check signature)
        await _validate_webhook_signature(request)
        
        # Parse messages from webhook payload
        messages = _extract_messages(body)
        
        if not messages:
            logger.debug("No messages in webhook payload")
            return {"status": "ok", "message_count": 0}
        
        queue = get_message_queue()
        processed_count = 0
        
        for msg in messages:
            # Queue for processing
            queue.add(msg)
            processed_count += 1
            
            # Process in background
            background_tasks.add_task(
                _process_whatsapp_message,
                msg
            )
            
            logger.info(
                f"WhatsApp message queued: {msg.get('message_id')} "
                f"from {msg.get('from_number')}"
            )
        
        return {
            "status": "ok",
            "message_count": processed_count
        }
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages")
async def get_messages(
    phone_number: Optional[str] = None,
    limit: int = 50
):
    """
    Get queued WhatsApp messages.
    
    Used for debugging and monitoring.
    """
    queue = get_message_queue()
    
    if phone_number:
        messages = queue.get_for_number(phone_number)
    else:
        messages = queue.get_pending()
    
    return {
        "messages": messages[-limit:],
        "total": len(queue.queue)
    }


@router.post("/send")
async def send_message(
    message: WhatsAppOutgoingMessage
):
    """
    Send a WhatsApp message.
    
    Requires WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID to be configured.
    """
    import os
    
    access_token = os.environ.get("WHATSAPP_ACCESS_TOKEN")
    phone_number_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
    
    if not access_token or not phone_number_id:
        raise HTTPException(
            status_code=503,
            detail="WhatsApp not configured. Set WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID"
        )
    
    try:
        import httpx
        
        url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload: Dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": message.to,
            "type": message.type,
        }
        
        if message.type == "text" and message.text:
            payload["text"] = message.text
        elif message.type == "template" and message.template:
            payload["template"] = message.template
        elif message.type == "image" and message.image:
            payload["image"] = message.image
        elif message.type == "document" and message.document:
            payload["document"] = message.document
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
            
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """
    Get WhatsApp integration status.
    """
    import os
    
    access_token = bool(os.environ.get("WHATSAPP_ACCESS_TOKEN"))
    phone_id = bool(os.environ.get("WHATSAPP_PHONE_NUMBER_ID"))
    verify_token = bool(os.environ.get("WHATSAPP_VERIFY_TOKEN"))
    
    queue = get_message_queue()
    
    return {
        "configured": access_token and phone_id,
        "verification_ready": verify_token,
        "pending_messages": len(queue.queue),
        "settings": {
            "access_token": "✓ Set" if access_token else "✗ Not set",
            "phone_number_id": "✓ Set" if phone_id else "✗ Not set",
            "verify_token": "✓ Set" if verify_token else "✗ Not set"
        }
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def _validate_webhook_signature(request: Request) -> bool:
    """
    Validate webhook signature from Meta.
    
    Meta signs webhooks with X-Hub-Signature-256 header.
    """
    import os
    
    app_secret = os.environ.get("WHATSAPP_APP_SECRET")
    if not app_secret:
        # Skip validation if app secret not configured
        return True
    
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not signature.startswith("sha256="):
        logger.warning("Invalid webhook signature format")
        return False
    
    expected_sig = signature[7:]  # Remove "sha256=" prefix
    
    body = await request.body()
    computed_sig = hmac.new(
        app_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(expected_sig, computed_sig):
        logger.warning("Webhook signature mismatch")
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    return True


def _extract_messages(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract messages from WhatsApp webhook payload.
    
    Handles Meta WhatsApp Business API format.
    """
    messages = []
    
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            
            # Get message metadata
            metadata = value.get("metadata", {})
            phone_number_id = metadata.get("phone_number_id")
            
            # Process messages
            for msg in value.get("messages", []):
                message_data = {
                    "message_id": msg.get("id"),
                    "from_number": msg.get("from"),
                    "timestamp": msg.get("timestamp"),
                    "type": msg.get("type"),
                    "phone_number_id": phone_number_id,
                    "raw": msg
                }
                
                # Extract content based on type
                msg_type = msg.get("type")
                if msg_type == "text":
                    message_data["content"] = msg.get("text", {}).get("body", "")
                elif msg_type == "image":
                    message_data["media_id"] = msg.get("image", {}).get("id")
                    message_data["caption"] = msg.get("image", {}).get("caption", "")
                elif msg_type == "document":
                    message_data["media_id"] = msg.get("document", {}).get("id")
                    message_data["filename"] = msg.get("document", {}).get("filename", "")
                elif msg_type == "audio":
                    message_data["media_id"] = msg.get("audio", {}).get("id")
                elif msg_type == "video":
                    message_data["media_id"] = msg.get("video", {}).get("id")
                elif msg_type == "location":
                    loc = msg.get("location", {})
                    message_data["latitude"] = loc.get("latitude")
                    message_data["longitude"] = loc.get("longitude")
                    message_data["name"] = loc.get("name")
                elif msg_type == "interactive":
                    interactive = msg.get("interactive", {})
                    message_data["interactive_type"] = interactive.get("type")
                    if interactive.get("type") == "button_reply":
                        message_data["button_id"] = interactive.get("button_reply", {}).get("id")
                        message_data["button_title"] = interactive.get("button_reply", {}).get("title")
                    elif interactive.get("type") == "list_reply":
                        message_data["list_id"] = interactive.get("list_reply", {}).get("id")
                        message_data["list_title"] = interactive.get("list_reply", {}).get("title")
                
                messages.append(message_data)
    
    return messages


async def _process_whatsapp_message(message: Dict[str, Any]):
    """
    Process a WhatsApp message through Otto.
    
    This is run as a background task.
    """
    try:
        logger.info(f"Processing WhatsApp message: {message.get('message_id')}")
        
        # Get the orchestrator
        from ..main import orchestrator
        
        if not orchestrator:
            logger.error("Orchestrator not available for WhatsApp processing")
            return
        
        # Extract message content
        content = message.get("content", "")
        if not content:
            logger.debug("No text content in message, skipping")
            return
        
        # Create session ID from phone number
        session_id = f"whatsapp_{message.get('from_number', 'unknown')}"
        
        # Process through orchestrator
        result = await orchestrator.process(
            message=content,
            session_id=session_id,
            user_id=message.get("from_number"),
            context={
                "channel": "whatsapp",
                "message_id": message.get("message_id"),
                "phone_number": message.get("from_number")
            }
        )
        
        # Send response back via WhatsApp
        response_text = result.get("response", "")
        from_number = message.get("from_number")
        if response_text and from_number:
            await _send_response(
                to=from_number,
                text=response_text
            )
        
        logger.info(f"WhatsApp message processed: {message.get('message_id')}")
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp message: {e}", exc_info=True)


async def _send_response(to: str, text: str):
    """Send a response back via WhatsApp."""
    import os
    import httpx
    
    access_token = os.environ.get("WHATSAPP_ACCESS_TOKEN")
    phone_number_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
    
    if not access_token or not phone_number_id:
        logger.warning("WhatsApp not configured for sending responses")
        return
    
    try:
        url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": text[:4096]}  # WhatsApp text limit
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"WhatsApp response sent to {to}")
            
    except Exception as e:
        logger.error(f"Failed to send WhatsApp response: {e}")
