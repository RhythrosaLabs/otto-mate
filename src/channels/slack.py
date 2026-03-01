"""
Slack Channel Integration

Slack integration using Slack Bolt for Python.
Install: pip install slack-bolt
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    from slack_bolt.async_app import AsyncApp
    from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False

from src.channels.base import BaseChannel, ChannelMessage, ChannelType

logger = logging.getLogger(__name__)


class SlackChannel(BaseChannel):
    """Slack integration via Bolt framework"""
    
    def __init__(self, gateway, config: Dict[str, Any]):
        super().__init__(gateway, config)
        self.bot_token = config.get("bot_token") or config.get("SLACK_BOT_TOKEN")
        self.app_token = config.get("app_token") or config.get("SLACK_APP_TOKEN")
        self.allowed_workspaces = config.get("workspaces", {})
        self.allowed_channels = config.get("channels", {})
        self.app = None
        self.handler = None
        
        if not SLACK_AVAILABLE:
            raise ImportError("slack-bolt not installed. Run: pip install slack-bolt")
        
        if not self.bot_token or not self.app_token:
            raise ValueError("Slack bot_token and app_token required")
    
    async def connect(self):
        """Start Slack bot via Socket Mode"""
        self.app = AsyncApp(token=self.bot_token)
        
        # Handle messages
        @self.app.event("message")
        async def handle_message(event, say, client):
            # Ignore bot messages
            if event.get("bot_id"):
                return
            
            # Check authorization
            channel_id = event.get("channel")
            if not self._is_allowed_channel(channel_id):
                return
            
            # Get user info
            user_id = event.get("user")
            user_info = await client.users_info(user=user_id)
            user_name = user_info["user"]["real_name"]
            
            # Get channel info
            channel_info = await client.conversations_info(channel=channel_id)
            channel_name = channel_info["channel"]["name"]
            is_group = not channel_info["channel"]["is_im"]
            
            # Handle files
            media_type = None
            media_url = None
            if event.get("files"):
                file = event["files"][0]
                media_type = file.get("mimetype", "file")
                media_url = file.get("url_private")
            
            # Convert to standard format
            channel_message = ChannelMessage(
                message_id=event["ts"],
                channel=ChannelType.SLACK,
                sender_id=user_id,
                sender_name=user_name,
                content=event.get("text", ""),
                timestamp=datetime.fromtimestamp(float(event["ts"])).isoformat(),
                chat_id=channel_id,
                chat_name=channel_name,
                is_group=is_group,
                reply_to=event.get("thread_ts"),
                media_type=media_type,
                media_url=media_url
            )
            
            # Forward to gateway
            await self.on_message(channel_message)
        
        # Handle slash commands
        @self.app.command("/otto")
        async def handle_otto_command(ack, command, respond):
            await ack()
            await respond(
                "👋 Hi! I'm Otto, your AI assistant.\n"
                "Just message me directly and I'll help you out!"
            )
        
        @self.app.command("/status")
        async def handle_status_command(ack, command, respond):
            await ack()
            stats = self.gateway.get_stats()
            await respond(
                f"🤖 *Otto Gateway Status*\n\n"
                f"✅ Connected clients: {stats['active_clients']}\n"
                f"⏱ Uptime: {int(stats['uptime_seconds'])}s\n"
                f"📡 Channels: {stats['channels']}"
            )
        
        # Handle app mentions
        @self.app.event("app_mention")
        async def handle_mention(event, say, client):
            # Same as regular message handling
            await handle_message(event, say, client)
        
        # Start socket mode handler
        self.handler = AsyncSocketModeHandler(self.app, self.app_token)
        await self.handler.start_async()
        
        self.is_connected = True
        logger.info("✅ Slack bot connected")
    
    async def disconnect(self):
        """Stop Slack bot"""
        if self.handler:
            await self.handler.close_async()
        
        self.is_connected = False
        logger.info("❌ Slack bot disconnected")
    
    async def send_message(
        self,
        chat_id: str,
        content: str,
        reply_to: Optional[str] = None,
        media_path: Optional[str] = None
    ) -> str:
        """Send message via Slack"""
        if not self.app:
            raise RuntimeError("Slack not connected")
        
        try:
            client = self.app.client
            
            # Send message
            kwargs = {
                "channel": chat_id,
                "text": content
            }
            
            if reply_to:
                kwargs["thread_ts"] = reply_to
            
            if media_path:
                # Upload file
                response = await client.files_upload_v2(
                    channel=chat_id,
                    file=media_path,
                    initial_comment=content,
                    thread_ts=reply_to
                )
                return response["file"]["id"]
            else:
                response = await client.chat_postMessage(**kwargs)
                return response["ts"]
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            raise
    
    async def get_chat_history(self, chat_id: str, limit: int = 50) -> List[ChannelMessage]:
        """Get recent messages from a channel"""
        if not self.app:
            return []
        
        try:
            client = self.app.client
            response = await client.conversations_history(
                channel=chat_id,
                limit=limit
            )
            
            messages = []
            for msg in response["messages"]:
                # Skip bot messages
                if msg.get("bot_id"):
                    continue
                
                # Get user info
                user_id = msg.get("user")
                if user_id:
                    user_info = await client.users_info(user=user_id)
                    user_name = user_info["user"]["real_name"]
                else:
                    user_name = "Unknown"
                
                messages.append(ChannelMessage(
                    message_id=msg["ts"],
                    channel=ChannelType.SLACK,
                    sender_id=user_id or "unknown",
                    sender_name=user_name,
                    content=msg.get("text", ""),
                    timestamp=datetime.fromtimestamp(float(msg["ts"])).isoformat(),
                    chat_id=chat_id,
                    chat_name=chat_id
                ))
            
            return messages
        except Exception as e:
            logger.error(f"Failed to get Slack history: {e}")
            return []
    
    def _is_allowed_channel(self, channel_id: str) -> bool:
        """Check if channel is allowed"""
        if "*" in self.allowed_channels:
            return True
        return channel_id in self.allowed_channels
