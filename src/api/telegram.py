"""
Otto Universal - Telegram Webhook Handler
==========================================

Webhook endpoint for receiving messages from Telegram Bot API.

Setup:
1. Create a Telegram bot via @BotFather
2. Set TELEGRAM_BOT_TOKEN in .env
3. Set webhook URL: https://api.telegram.org/bot<TOKEN>/setWebhook?url=YOUR_URL/api/webhooks/telegram
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks/telegram", tags=["telegram"])


# ============================================================================
# MODELS
# ============================================================================

class TelegramUser(BaseModel):
    id: int
    is_bot: bool = False
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None


class TelegramChat(BaseModel):
    id: int
    type: str  # private, group, supergroup, channel
    title: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class TelegramMessage(BaseModel):
    message_id: int
    date: int
    chat: TelegramChat
    from_user: Optional[TelegramUser] = None
    text: Optional[str] = None
    photo: Optional[List[Dict[str, Any]]] = None
    document: Optional[Dict[str, Any]] = None
    voice: Optional[Dict[str, Any]] = None
    video: Optional[Dict[str, Any]] = None
    caption: Optional[str] = None
    
    class Config:
        populate_by_name = True
        
    def __init__(self, **data):
        # Handle 'from' field which is a reserved keyword
        if 'from' in data:
            data['from_user'] = data.pop('from')
        super().__init__(**data)


class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[TelegramMessage] = None
    edited_message: Optional[TelegramMessage] = None
    callback_query: Optional[Dict[str, Any]] = None


# ============================================================================
# MESSAGE QUEUE
# ============================================================================

class TelegramMessageQueue:
    """Simple in-memory message queue."""
    
    def __init__(self, max_size: int = 1000):
        self.queue: List[Dict[str, Any]] = []
        self.max_size = max_size
    
    def add(self, message: Dict[str, Any]):
        if len(self.queue) >= self.max_size:
            self.queue.pop(0)
        message["queued_at"] = datetime.now().isoformat()
        self.queue.append(message)
    
    def get_pending(self) -> List[Dict[str, Any]]:
        return self.queue.copy()
    
    def get_for_chat(self, chat_id: int) -> List[Dict[str, Any]]:
        return [m for m in self.queue if m.get("chat_id") == chat_id]


_message_queue = TelegramMessageQueue()


# ============================================================================
# WEBHOOK HANDLERS
# ============================================================================

@router.post("")
async def receive_update(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Receive incoming Telegram updates.
    
    This endpoint receives updates from Telegram's webhook.
    Messages are queued for processing by the Otto orchestrator.
    """
    try:
        body = await request.json()
        logger.debug(f"Telegram update received: {json.dumps(body, indent=2)}")
        
        update = TelegramUpdate(**body)
        
        # Handle message
        message = update.message or update.edited_message
        if message:
            message_data = {
                "update_id": update.update_id,
                "message_id": message.message_id,
                "chat_id": message.chat.id,
                "chat_type": message.chat.type,
                "user_id": message.from_user.id if message.from_user else None,
                "username": message.from_user.username if message.from_user else None,
                "text": message.text or message.caption or "",
                "has_media": bool(message.photo or message.document or message.voice or message.video),
                "timestamp": datetime.fromtimestamp(message.date).isoformat()
            }
            
            _message_queue.add(message_data)
            
            # Process in background
            background_tasks.add_task(
                _process_telegram_message,
                message_data
            )
            
            logger.info(f"Telegram message queued from chat {message.chat.id}")
        
        # Handle callback query (button clicks)
        if update.callback_query:
            callback = update.callback_query
            callback_data = {
                "update_id": update.update_id,
                "callback_id": callback.get("id"),
                "chat_id": callback.get("message", {}).get("chat", {}).get("id"),
                "user_id": callback.get("from", {}).get("id"),
                "data": callback.get("data"),
                "timestamp": datetime.now().isoformat()
            }
            
            background_tasks.add_task(
                _process_callback_query,
                callback_data
            )
        
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}", exc_info=True)
        # Always return 200 to Telegram to prevent re-sends
        return {"ok": False, "error": str(e)}


@router.get("/messages")
async def get_messages(
    chat_id: Optional[int] = None,
    limit: int = 50
):
    """Get queued Telegram messages."""
    if chat_id:
        messages = _message_queue.get_for_chat(chat_id)
    else:
        messages = _message_queue.get_pending()
    
    return {
        "messages": messages[-limit:],
        "total": len(_message_queue.queue)
    }


@router.post("/send")
async def send_message(
    chat_id: int,
    text: str,
    parse_mode: Optional[str] = "Markdown",
    reply_markup: Optional[Dict[str, Any]] = None
):
    """
    Send a message to a Telegram chat.
    
    Requires TELEGRAM_BOT_TOKEN to be configured.
    """
    import os
    import httpx
    
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise HTTPException(
            status_code=503,
            detail="Telegram not configured. Set TELEGRAM_BOT_TOKEN"
        )
    
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
            
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """Get Telegram integration status."""
    import os
    
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    # Try to get bot info if token exists
    bot_info = None
    if token:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"https://api.telegram.org/bot{token}/getMe")
                if response.status_code == 200:
                    bot_info = response.json().get("result", {})
        except:
            pass
    
    return {
        "configured": bool(token),
        "bot_info": bot_info,
        "pending_messages": len(_message_queue.queue),
        "webhook_path": "/api/webhooks/telegram"
    }


@router.post("/set-webhook")
async def set_webhook(webhook_url: str):
    """
    Set the Telegram webhook URL.
    
    Call this after deploying to set up the webhook.
    """
    import os
    import httpx
    
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise HTTPException(
            status_code=503,
            detail="TELEGRAM_BOT_TOKEN not configured"
        )
    
    try:
        url = f"https://api.telegram.org/bot{token}/setWebhook"
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={"url": webhook_url})
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def _process_telegram_message(message: Dict[str, Any]):
    """Process a Telegram message through Otto."""
    try:
        logger.info(f"Processing Telegram message: {message.get('message_id')}")
        
        text = message.get("text", "").strip()
        if not text:
            logger.debug("No text content in message, skipping")
            return
        
        # Get the orchestrator
        from ..main import orchestrator
        
        if not orchestrator:
            logger.error("Orchestrator not available for Telegram processing")
            return
        
        # Create session ID from chat_id
        session_id = f"telegram_{message.get('chat_id', 'unknown')}"
        
        # Process through orchestrator
        result = await orchestrator.process(
            message=text,
            session_id=session_id,
            user_id=str(message.get("user_id", "")),
            context={
                "channel": "telegram",
                "message_id": message.get("message_id"),
                "chat_id": message.get("chat_id"),
                "username": message.get("username")
            }
        )
        
        # Send response back via Telegram
        response_text = result.get("response", "")
        if response_text and message.get("chat_id"):
            await _send_response(
                chat_id=message["chat_id"],
                text=response_text
            )
        
        logger.info(f"Telegram message processed: {message.get('message_id')}")
        
    except Exception as e:
        logger.error(f"Error processing Telegram message: {e}", exc_info=True)


async def _process_callback_query(callback: Dict[str, Any]):
    """Process a Telegram callback query (button click)."""
    try:
        logger.info(f"Processing callback query: {callback.get('callback_id')}")
        
        # Answer the callback to remove loading state
        import os
        import httpx
        
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if token:
            url = f"https://api.telegram.org/bot{token}/answerCallbackQuery"
            async with httpx.AsyncClient() as client:
                await client.post(url, json={
                    "callback_query_id": callback.get("callback_id")
                })
        
        # Process the callback data if needed
        # This could trigger specific actions based on button clicks
        
    except Exception as e:
        logger.error(f"Error processing callback query: {e}", exc_info=True)


async def _send_response(chat_id: int, text: str):
    """Send a response back via Telegram."""
    import os
    import httpx
    
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.warning("Telegram not configured for sending responses")
        return
    
    try:
        # Split long messages (Telegram limit is 4096 chars)
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        
        async with httpx.AsyncClient() as client:
            for chunk in chunks:
                await client.post(url, json={
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "Markdown"
                })
        
        logger.info(f"Telegram response sent to chat {chat_id}")
        
    except Exception as e:
        logger.error(f"Failed to send Telegram response: {e}")
