"""
Otto Universal - Discord Webhook Handler
=========================================

Webhook endpoint for receiving messages from Discord bots.

Setup:
1. Create a Discord application at https://discord.com/developers
2. Create a bot and get the token
3. Set DISCORD_BOT_TOKEN in .env
4. Invite bot to server with message permissions

For interactions webhook:
- Set Interactions Endpoint URL to: YOUR_URL/api/webhooks/discord/interactions
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import hashlib
import hmac

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Header
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks/discord", tags=["discord"])


# ============================================================================
# MODELS
# ============================================================================

class DiscordUser(BaseModel):
    id: str
    username: str
    discriminator: str = "0"
    avatar: Optional[str] = None
    bot: bool = False


class DiscordMessage(BaseModel):
    id: str
    channel_id: str
    author: DiscordUser
    content: str
    timestamp: str
    guild_id: Optional[str] = None
    attachments: List[Dict[str, Any]] = []
    mentions: List[DiscordUser] = []


# ============================================================================
# MESSAGE QUEUE
# ============================================================================

class DiscordMessageQueue:
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
    
    def get_for_channel(self, channel_id: str) -> List[Dict[str, Any]]:
        return [m for m in self.queue if m.get("channel_id") == channel_id]


_message_queue = DiscordMessageQueue()


# ============================================================================
# INTERACTION TYPES
# ============================================================================

INTERACTION_PING = 1
INTERACTION_APPLICATION_COMMAND = 2
INTERACTION_MESSAGE_COMPONENT = 3
INTERACTION_AUTOCOMPLETE = 4
INTERACTION_MODAL_SUBMIT = 5


# ============================================================================
# WEBHOOK HANDLERS
# ============================================================================

@router.post("/interactions")
async def handle_interaction(
    request: Request,
    background_tasks: BackgroundTasks,
    x_signature_ed25519: str = Header(None),
    x_signature_timestamp: str = Header(None)
):
    """
    Handle Discord Interactions (slash commands, buttons, etc).
    
    Discord sends interactions to this endpoint when users use
    slash commands or interact with components.
    """
    import os
    
    body = await request.body()
    
    # Verify signature if public key is configured
    public_key = os.environ.get("DISCORD_PUBLIC_KEY")
    if public_key and x_signature_ed25519 and x_signature_timestamp:
        if not _verify_discord_signature(
            public_key, x_signature_ed25519, x_signature_timestamp, body
        ):
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        data = json.loads(body)
        interaction_type = data.get("type")
        
        # Respond to PING (required for Discord verification)
        if interaction_type == INTERACTION_PING:
            return {"type": 1}  # PONG
        
        # Handle application commands (slash commands)
        if interaction_type == INTERACTION_APPLICATION_COMMAND:
            return await _handle_slash_command(data, background_tasks)
        
        # Handle message components (buttons, selects)
        if interaction_type == INTERACTION_MESSAGE_COMPONENT:
            return await _handle_component(data, background_tasks)
        
        # Default acknowledge
        return {"type": 1}
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error(f"Discord interaction error: {e}", exc_info=True)
        return {"type": 4, "data": {"content": f"Error: {str(e)}"}}


@router.post("/message")
async def receive_message(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Receive a message event from Discord bot gateway.
    
    Note: This is for bot-based message handling, not interactions.
    Your bot needs to forward MESSAGE_CREATE events here.
    """
    try:
        body = await request.json()
        
        message_data = {
            "message_id": body.get("id"),
            "channel_id": body.get("channel_id"),
            "guild_id": body.get("guild_id"),
            "author_id": body.get("author", {}).get("id"),
            "author_name": body.get("author", {}).get("username"),
            "content": body.get("content", ""),
            "timestamp": body.get("timestamp"),
            "has_attachments": len(body.get("attachments", [])) > 0
        }
        
        _message_queue.add(message_data)
        
        # Process in background
        background_tasks.add_task(
            _process_discord_message,
            message_data
        )
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Discord message error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages")
async def get_messages(
    channel_id: Optional[str] = None,
    limit: int = 50
):
    """Get queued Discord messages."""
    if channel_id:
        messages = _message_queue.get_for_channel(channel_id)
    else:
        messages = _message_queue.get_pending()
    
    return {
        "messages": messages[-limit:],
        "total": len(_message_queue.queue)
    }


@router.post("/send")
async def send_message(
    channel_id: str,
    content: str,
    embed: Optional[Dict[str, Any]] = None
):
    """
    Send a message to a Discord channel.
    
    Requires DISCORD_BOT_TOKEN to be configured.
    """
    import os
    import httpx
    
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        raise HTTPException(
            status_code=503,
            detail="Discord not configured. Set DISCORD_BOT_TOKEN"
        )
    
    try:
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        headers = {
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json"
        }
        
        payload: Dict[str, Any] = {"content": content}
        if embed:
            payload["embeds"] = [embed]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
            
    except Exception as e:
        logger.error(f"Failed to send Discord message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """Get Discord integration status."""
    import os
    
    token = bool(os.environ.get("DISCORD_BOT_TOKEN"))
    public_key = bool(os.environ.get("DISCORD_PUBLIC_KEY"))
    app_id = os.environ.get("DISCORD_APPLICATION_ID")
    
    return {
        "configured": token,
        "interactions_ready": public_key,
        "application_id": app_id,
        "pending_messages": len(_message_queue.queue),
        "endpoints": {
            "interactions": "/api/webhooks/discord/interactions",
            "messages": "/api/webhooks/discord/message"
        }
    }


@router.post("/register-commands")
async def register_commands():
    """
    Register global slash commands with Discord.
    
    Call this once to set up Otto's slash commands in Discord.
    """
    import os
    import httpx
    
    token = os.environ.get("DISCORD_BOT_TOKEN")
    app_id = os.environ.get("DISCORD_APPLICATION_ID")
    
    if not token or not app_id:
        raise HTTPException(
            status_code=503,
            detail="Set DISCORD_BOT_TOKEN and DISCORD_APPLICATION_ID"
        )
    
    # Define Otto's Discord slash commands
    commands = [
        {
            "name": "otto",
            "description": "Chat with Otto AI assistant",
            "options": [
                {
                    "name": "message",
                    "description": "Your message to Otto",
                    "type": 3,  # STRING
                    "required": True
                }
            ]
        },
        {
            "name": "otto-status",
            "description": "Get Otto system status"
        },
        {
            "name": "otto-help",
            "description": "Show Otto's available commands"
        },
        {
            "name": "otto-image",
            "description": "Generate an AI image",
            "options": [
                {
                    "name": "prompt",
                    "description": "Image description",
                    "type": 3,
                    "required": True
                }
            ]
        }
    ]
    
    try:
        url = f"https://discord.com/api/v10/applications/{app_id}/commands"
        headers = {
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.put(url, headers=headers, json=commands)
            response.raise_for_status()
            return {
                "status": "success",
                "commands_registered": len(commands),
                "response": response.json()
            }
            
    except Exception as e:
        logger.error(f"Failed to register Discord commands: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _verify_discord_signature(
    public_key: str,
    signature: str,
    timestamp: str,
    body: bytes
) -> bool:
    """Verify Discord interaction signature."""
    try:
        from nacl.signing import VerifyKey
        from nacl.exceptions import BadSignature
        
        verify_key = VerifyKey(bytes.fromhex(public_key))
        verify_key.verify(timestamp.encode() + body, bytes.fromhex(signature))
        return True
    except ImportError:
        logger.warning("nacl not installed, skipping signature verification")
        return True
    except BadSignature:
        return False
    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return False


async def _handle_slash_command(
    data: Dict[str, Any],
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Handle a Discord slash command."""
    command_name = data.get("data", {}).get("name", "")
    options = {
        opt["name"]: opt.get("value")
        for opt in data.get("data", {}).get("options", [])
    }
    
    user = data.get("member", {}).get("user", {}) or data.get("user", {})
    channel_id = data.get("channel_id")
    
    # Map Discord commands to Otto
    if command_name == "otto":
        message = options.get("message", "")
        # Process async and respond with deferred
        background_tasks.add_task(
            _process_otto_command,
            channel_id,
            message,
            user.get("id")
        )
        return {
            "type": 5  # DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
        }
    
    elif command_name == "otto-status":
        return {
            "type": 4,  # CHANNEL_MESSAGE_WITH_SOURCE
            "data": {
                "content": "🟢 **Otto Status**: Online and ready!\n\nUse `/otto <message>` to chat."
            }
        }
    
    elif command_name == "otto-help":
        return {
            "type": 4,
            "data": {
                "content": """**Otto AI Commands**

`/otto <message>` - Chat with Otto
`/otto-status` - Check Otto's status
`/otto-help` - Show this help
`/otto-image <prompt>` - Generate an AI image

**Examples:**
- `/otto What can you help me with?`
- `/otto-image a sunset over mountains`
"""
            }
        }
    
    elif command_name == "otto-image":
        prompt = options.get("prompt", "")
        background_tasks.add_task(
            _process_otto_command,
            channel_id,
            f"/image {prompt}",
            user.get("id")
        )
        return {
            "type": 5  # DEFERRED
        }
    
    return {"type": 4, "data": {"content": "Unknown command"}}


async def _handle_component(
    data: Dict[str, Any],
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Handle a Discord component interaction (buttons, etc)."""
    custom_id = data.get("data", {}).get("custom_id", "")
    
    # Handle based on custom_id
    return {
        "type": 6  # DEFERRED_UPDATE_MESSAGE
    }


async def _process_discord_message(message: Dict[str, Any]):
    """Process a Discord message through Otto."""
    try:
        logger.info(f"Processing Discord message: {message.get('message_id')}")
        
        content = message.get("content", "").strip()
        if not content:
            return
        
        from ..main import orchestrator
        
        if not orchestrator:
            logger.error("Orchestrator not available")
            return
        
        session_id = f"discord_{message.get('channel_id', 'unknown')}"
        
        result = await orchestrator.process(
            message=content,
            session_id=session_id,
            user_id=message.get("author_id"),
            context={
                "channel": "discord",
                "channel_id": message.get("channel_id"),
                "guild_id": message.get("guild_id")
            }
        )
        
        response_text = result.get("response", "")
        if response_text and message.get("channel_id"):
            await _send_response(message["channel_id"], response_text)
        
    except Exception as e:
        logger.error(f"Error processing Discord message: {e}", exc_info=True)


async def _process_otto_command(
    channel_id: str,
    message: str,
    user_id: str
):
    """Process an Otto command from Discord."""
    try:
        from ..main import orchestrator
        
        if not orchestrator:
            await _send_response(channel_id, "❌ Otto is currently unavailable")
            return
        
        session_id = f"discord_{channel_id}"
        
        result = await orchestrator.process(
            message=message,
            session_id=session_id,
            user_id=user_id,
            context={"channel": "discord"}
        )
        
        response = result.get("response", "No response")
        
        # Truncate for Discord (2000 char limit)
        if len(response) > 1900:
            response = response[:1900] + "\n\n*[Response truncated]*"
        
        await _send_response(channel_id, response)
        
    except Exception as e:
        logger.error(f"Error processing Otto command: {e}")
        await _send_response(channel_id, f"❌ Error: {str(e)[:100]}")


async def _send_response(channel_id: str, content: str):
    """Send a response to Discord channel."""
    import os
    import httpx
    
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        return
    
    try:
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        headers = {
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json"
        }
        
        # Split long messages
        chunks = [content[i:i+1900] for i in range(0, len(content), 1900)]
        
        async with httpx.AsyncClient() as client:
            for chunk in chunks:
                await client.post(url, headers=headers, json={"content": chunk})
        
    except Exception as e:
        logger.error(f"Failed to send Discord response: {e}")
