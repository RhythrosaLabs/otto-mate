"""
Discord Channel Integration

Discord bot integration using discord.py.
Install: pip install discord.py
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    import discord
    from discord.ext import commands
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False

from src.channels.base import BaseChannel, ChannelMessage, ChannelType

logger = logging.getLogger(__name__)


class DiscordChannel(BaseChannel):
    """Discord integration via Bot API"""
    
    def __init__(self, gateway, config: Dict[str, Any]):
        super().__init__(gateway, config)
        self.bot_token = config.get("token") or config.get("DISCORD_BOT_TOKEN")
        self.allowed_guilds = config.get("guilds", {})
        self.allowed_users = config.get("allow_from", [])
        self.bot = None
        
        if not DISCORD_AVAILABLE:
            raise ImportError("discord.py not installed. Run: pip install discord.py")
        
        if not self.bot_token:
            raise ValueError("Discord bot token required")
    
    async def connect(self):
        """Start Discord bot"""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        self.bot = commands.Bot(command_prefix="!", intents=intents)
        
        @self.bot.event
        async def on_ready():
            logger.info(f"✅ Discord bot logged in as {self.bot.user}")
            self.is_connected = True
        
        @self.bot.event
        async def on_message(message):
            # Ignore own messages
            if message.author == self.bot.user:
                return
            
            # Check authorization
            if not self._is_allowed(message):
                return
            
            # Convert to standard format
            channel_message = ChannelMessage(
                message_id=str(message.id),
                channel=ChannelType.DISCORD,
                sender_id=str(message.author.id),
                sender_name=message.author.display_name,
                content=message.content,
                timestamp=message.created_at.isoformat(),
                chat_id=str(message.channel.id),
                chat_name=message.channel.name if hasattr(message.channel, 'name') else "DM",
                is_group=message.guild is not None,
                reply_to=str(message.reference.message_id) if message.reference else None,
                media_type="attachment" if message.attachments else None,
                media_url=message.attachments[0].url if message.attachments else None
            )
            
            # Forward to gateway
            await self.on_message(channel_message)
            
            # Process commands
            await self.bot.process_commands(message)
        
        # Add commands
        @self.bot.command(name="status")
        async def status_command(ctx):
            stats = self.gateway.get_stats()
            await ctx.send(
                f"🤖 **Otto Gateway Status**\n\n"
                f"✅ Connected clients: {stats['active_clients']}\n"
                f"⏱ Uptime: {int(stats['uptime_seconds'])}s\n"
                f"📡 Channels: {stats['channels']}"
            )
        
        @self.bot.command(name="help")
        async def help_command(ctx):
            await ctx.send(
                "👋 **Otto AI Assistant**\n\n"
                "Just mention me or send a message!\n"
                "Commands:\n"
                "• `!status` - Check gateway status\n"
                "• `!help` - Show this message"
            )
        
        # Start bot (non-blocking)
        import asyncio
        asyncio.create_task(self.bot.start(self.bot_token))
    
    async def disconnect(self):
        """Stop Discord bot"""
        if self.bot:
            await self.bot.close()
        
        self.is_connected = False
        logger.info("❌ Discord bot disconnected")
    
    async def send_message(
        self,
        chat_id: str,
        content: str,
        reply_to: Optional[str] = None,
        media_path: Optional[str] = None
    ) -> str:
        """Send message via Discord"""
        if not self.bot:
            raise RuntimeError("Discord not connected")
        
        try:
            channel = self.bot.get_channel(int(chat_id))
            if not channel:
                raise ValueError(f"Channel not found: {chat_id}")
            
            # Get reference message if replying
            reference = None
            if reply_to:
                try:
                    ref_message = await channel.fetch_message(int(reply_to))
                    reference = ref_message
                except:
                    pass
            
            # Send message
            if media_path:
                with open(media_path, 'rb') as f:
                    file = discord.File(f)
                    message = await channel.send(content=content, file=file, reference=reference)
            else:
                message = await channel.send(content=content, reference=reference)
            
            return str(message.id)
        except Exception as e:
            logger.error(f"Failed to send Discord message: {e}")
            raise
    
    async def get_chat_history(self, chat_id: str, limit: int = 50) -> List[ChannelMessage]:
        """Get recent messages from a channel"""
        if not self.bot:
            return []
        
        try:
            channel = self.bot.get_channel(int(chat_id))
            if not channel:
                return []
            
            messages = []
            async for msg in channel.history(limit=limit):
                messages.append(ChannelMessage(
                    message_id=str(msg.id),
                    channel=ChannelType.DISCORD,
                    sender_id=str(msg.author.id),
                    sender_name=msg.author.display_name,
                    content=msg.content,
                    timestamp=msg.created_at.isoformat(),
                    chat_id=chat_id,
                    chat_name=channel.name if hasattr(channel, 'name') else "DM",
                    is_group=msg.guild is not None
                ))
            
            return messages
        except Exception as e:
            logger.error(f"Failed to get Discord history: {e}")
            return []
    
    def _is_allowed(self, message) -> bool:
        """Check if message is from allowed source"""
        # Check guild allowlist
        if message.guild:
            if "*" not in self.allowed_guilds and str(message.guild.id) not in self.allowed_guilds:
                return False
        
        # Check user allowlist
        if "*" not in self.allowed_users and str(message.author.id) not in self.allowed_users:
            return False
        
        return True
