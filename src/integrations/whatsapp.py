"""
WhatsApp Integration
====================

WhatsApp Business API integration for Otto Universal.
"""

import logging
import hmac
import hashlib
import json
from typing import Optional, Dict, Any, Callable
import aiohttp
from fastapi import APIRouter, Request, Response, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class WhatsAppMessage(BaseModel):
    """Incoming WhatsApp message."""
    from_number: str
    message_id: str
    timestamp: str
    text: Optional[str] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None


class WhatsAppClient:
    """WhatsApp Business API client."""
    
    BASE_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(
        self,
        phone_number_id: str,
        access_token: str,
        verify_token: str
    ):
        self.phone_number_id = phone_number_id
        self.access_token = access_token
        self.verify_token = verify_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Message handler callback
        self._message_handler: Optional[Callable] = None
    
    def set_message_handler(self, handler: Callable):
        """Set the async message handler callback."""
        self._message_handler = handler
    
    async def send_message(
        self,
        to: str,
        text: str,
        preview_url: bool = False
    ) -> Dict[str, Any]:
        """
        Send a text message.
        
        Args:
            to: Recipient phone number (with country code)
            text: Message text
            preview_url: Whether to show URL previews
        """
        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": preview_url,
                "body": text
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=data) as response:
                result = await response.json()
                
                if response.status >= 400:
                    logger.error(f"WhatsApp API error: {result}")
                    raise Exception(f"WhatsApp API error: {result}")
                
                logger.info(f"Sent message to {to}")
                return result
    
    async def send_image(
        self,
        to: str,
        image_url: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send an image message."""
        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "image",
            "image": {
                "link": image_url
            }
        }
        
        if caption:
            data["image"]["caption"] = caption
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=data) as response:
                result = await response.json()
                if response.status >= 400:
                    raise Exception(f"WhatsApp API error: {result}")
                return result
    
    async def send_audio(
        self,
        to: str,
        audio_url: str
    ) -> Dict[str, Any]:
        """Send an audio message."""
        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "audio",
            "audio": {
                "link": audio_url
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=data) as response:
                result = await response.json()
                if response.status >= 400:
                    raise Exception(f"WhatsApp API error: {result}")
                return result
    
    async def send_document(
        self,
        to: str,
        document_url: str,
        filename: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a document."""
        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "document",
            "document": {
                "link": document_url,
                "filename": filename
            }
        }
        
        if caption:
            data["document"]["caption"] = caption
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=data) as response:
                result = await response.json()
                if response.status >= 400:
                    raise Exception(f"WhatsApp API error: {result}")
                return result
    
    async def send_template(
        self,
        to: str,
        template_name: str,
        language_code: str = "en_US",
        components: Optional[list] = None
    ) -> Dict[str, Any]:
        """Send a template message."""
        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code}
            }
        }
        
        if components:
            data["template"]["components"] = components
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=data) as response:
                result = await response.json()
                if response.status >= 400:
                    raise Exception(f"WhatsApp API error: {result}")
                return result
    
    async def send_interactive_buttons(
        self,
        to: str,
        body_text: str,
        buttons: list,
        header: Optional[str] = None,
        footer: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send interactive buttons.
        
        Args:
            to: Recipient phone number
            body_text: Message body
            buttons: List of button dicts with 'id' and 'title'
            header: Optional header text
            footer: Optional footer text
        """
        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        
        interactive = {
            "type": "button",
            "body": {"text": body_text},
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {"id": btn["id"], "title": btn["title"][:20]}
                    }
                    for btn in buttons[:3]  # Max 3 buttons
                ]
            }
        }
        
        if header:
            interactive["header"] = {"type": "text", "text": header}
        if footer:
            interactive["footer"] = {"text": footer}
        
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=data) as response:
                result = await response.json()
                if response.status >= 400:
                    raise Exception(f"WhatsApp API error: {result}")
                return result
    
    async def send_interactive_list(
        self,
        to: str,
        body_text: str,
        button_text: str,
        sections: list,
        header: Optional[str] = None,
        footer: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send interactive list.
        
        Args:
            to: Recipient phone number
            body_text: Message body
            button_text: Button text to open list
            sections: List of section dicts with 'title' and 'rows'
            header: Optional header
            footer: Optional footer
        """
        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        
        interactive = {
            "type": "list",
            "body": {"text": body_text},
            "action": {
                "button": button_text[:20],
                "sections": sections
            }
        }
        
        if header:
            interactive["header"] = {"type": "text", "text": header}
        if footer:
            interactive["footer"] = {"text": footer}
        
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=data) as response:
                result = await response.json()
                if response.status >= 400:
                    raise Exception(f"WhatsApp API error: {result}")
                return result
    
    async def mark_as_read(self, message_id: str) -> Dict[str, Any]:
        """Mark a message as read."""
        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        
        data = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=data) as response:
                return await response.json()
    
    async def download_media(self, media_id: str) -> bytes:
        """Download media by ID."""
        # First get the media URL
        url = f"{self.BASE_URL}/{media_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                data = await response.json()
                media_url = data.get("url")
            
            # Then download the actual media
            async with session.get(media_url, headers=self.headers) as response:
                return await response.read()
    
    def parse_webhook(self, payload: Dict[str, Any]) -> list:
        """Parse incoming webhook payload into messages."""
        messages = []
        
        try:
            entry = payload.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            
            for msg in value.get("messages", []):
                message = WhatsAppMessage(
                    from_number=msg.get("from"),
                    message_id=msg.get("id"),
                    timestamp=msg.get("timestamp")
                )
                
                msg_type = msg.get("type")
                
                if msg_type == "text":
                    message.text = msg.get("text", {}).get("body")
                elif msg_type in ["image", "audio", "video", "document"]:
                    media = msg.get(msg_type, {})
                    message.media_type = msg_type
                    # Media ID needs to be downloaded separately
                    message.media_url = media.get("id")
                elif msg_type == "interactive":
                    interactive = msg.get("interactive", {})
                    if interactive.get("type") == "button_reply":
                        message.text = interactive.get("button_reply", {}).get("id")
                    elif interactive.get("type") == "list_reply":
                        message.text = interactive.get("list_reply", {}).get("id")
                
                messages.append(message)
                
        except Exception as e:
            logger.error(f"Error parsing webhook: {e}")
        
        return messages
    
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        app_secret: str
    ) -> bool:
        """Verify webhook signature."""
        expected = hmac.new(
            app_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected}", signature)


def create_whatsapp_router(
    client: WhatsAppClient,
    message_handler: Callable
) -> APIRouter:
    """
    Create FastAPI router for WhatsApp webhooks.
    
    Args:
        client: WhatsApp client instance
        message_handler: Async function to handle messages
    """
    router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])
    
    @router.get("/webhook")
    async def verify_webhook(request: Request):
        """Webhook verification endpoint."""
        params = request.query_params
        
        mode = params.get("hub.mode")
        token = params.get("hub.verify_token")
        challenge = params.get("hub.challenge")
        
        if mode == "subscribe" and token == client.verify_token:
            logger.info("WhatsApp webhook verified")
            return Response(content=challenge, media_type="text/plain")
        
        raise HTTPException(status_code=403, detail="Verification failed")
    
    @router.post("/webhook")
    async def receive_webhook(request: Request):
        """Receive incoming messages."""
        try:
            payload = await request.json()
            logger.debug(f"Webhook received: {json.dumps(payload)[:500]}")
            
            # Parse messages
            messages = client.parse_webhook(payload)
            
            # Process each message
            for msg in messages:
                try:
                    # Mark as read
                    await client.mark_as_read(msg.message_id)
                    
                    # Handle message
                    if message_handler:
                        response = await message_handler(msg)
                        
                        # Send response if any
                        if response:
                            if isinstance(response, str):
                                await client.send_message(msg.from_number, response)
                            elif isinstance(response, dict):
                                if response.get("type") == "image":
                                    await client.send_image(
                                        msg.from_number,
                                        response["url"],
                                        response.get("caption")
                                    )
                                elif response.get("type") == "buttons":
                                    await client.send_interactive_buttons(
                                        msg.from_number,
                                        response["body"],
                                        response["buttons"]
                                    )
                                else:
                                    await client.send_message(
                                        msg.from_number,
                                        response.get("text", str(response))
                                    )
                                    
                except Exception as e:
                    logger.error(f"Error handling message: {e}", exc_info=True)
                    await client.send_message(
                        msg.from_number,
                        "Sorry, I encountered an error. Please try again."
                    )
            
            return {"status": "ok"}
            
        except Exception as e:
            logger.error(f"Webhook error: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}
    
    return router
