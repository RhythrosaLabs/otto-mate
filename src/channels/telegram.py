"""
Telegram Channel Integration

Telegram bot integration using python-telegram-bot.
Install: pip install python-telegram-bot
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

from src.channels.base import BaseChannel, ChannelMessage, ChannelType

logger = logging.getLogger(__name__)


class TelegramChannel(BaseChannel):
    """Telegram integration via Bot API"""
    
    def __init__(self, gateway, config: Dict[str, Any]):
        super().__init__(gateway, config)
        self.bot_token = config.get("bot_token") or config.get("TELEGRAM_BOT_TOKEN")
        self.allowed_users = config.get("allow_from", [])
        self.allowed_groups = config.get("groups", {})
        self.application = None
        
        if not TELEGRAM_AVAILABLE:
            raise ImportError("python-telegram-bot not installed. Run: pip install python-telegram-bot")
        
        if not self.bot_token:
            raise ValueError("Telegram bot token required")
    
    async def connect(self):
        """Start Telegram bot"""
        self.application = Application.builder().token(self.bot_token).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self._handle_start))
        self.application.add_handler(CommandHandler("status", self._handle_status))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        self.application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.VOICE, self._handle_media))
        
        # Start bot
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        self.is_connected = True
        logger.info("✅ Telegram bot connected")
    
    async def disconnect(self):
        """Stop Telegram bot"""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
        
        self.is_connected = False
        logger.info("❌ Telegram bot disconnected")
    
    async def send_message(
        self,
        chat_id: str,
        content: str,
        reply_to: Optional[str] = None,
        media_path: Optional[str] = None
    ) -> str:
        """Send message via Telegram"""
        if not self.application:
            raise RuntimeError("Telegram not connected")
        
        try:
            if media_path:
                # Determine media type and send
                if media_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    await self.application.bot.send_photo(
                        chat_id=int(chat_id),
                        photo=media_path,
                        caption=content,
                        reply_to_message_id=int(reply_to) if reply_to else None
                    )
                else:
                    await self.application.bot.send_document(
                        chat_id=int(chat_id),
                        document=media_path,
                        caption=content,
                        reply_to_message_id=int(reply_to) if reply_to else None
                    )
            else:
                # Text only
                message = await self.application.bot.send_message(
                    chat_id=int(chat_id),
                    text=content,
                    reply_to_message_id=int(reply_to) if reply_to else None
                )
                return str(message.message_id)
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            raise
    
    async def get_chat_history(self, chat_id: str, limit: int = 50) -> List[ChannelMessage]:
        """Get recent messages (not supported natively, would need message storage)"""
        return []
    
    def _is_allowed(self, user_id: int, chat_id: int, is_group: bool) -> bool:
        """Check if user/chat is allowed"""
        if not is_group:
            # DM: check allowlist
            if "*" in self.allowed_users:
                return True
            return str(user_id) in self.allowed_users
        else:
            # Group: check group allowlist
            if "*" in self.allowed_groups:
                return True
            return str(chat_id) in self.allowed_groups
    
    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        await update.message.reply_text(
            "👋 Hi! I'm Otto, your AI assistant.\n\n"
            "Send me any message and I'll help you out!"
        )
    
    async def _handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        stats = self.gateway.get_stats()
        await update.message.reply_text(
            f"🤖 Otto Gateway Status\n\n"
            f"✅ Connected clients: {stats['active_clients']}\n"
            f"⏱ Uptime: {int(stats['uptime_seconds'])}s\n"
            f"📡 Channels: {stats['channels']}"
        )
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming text message"""
        user = update.effective_user
        chat = update.effective_chat
        message = update.message
        
        # Check authorization
        if not self._is_allowed(user.id, chat.id, chat.type in ["group", "supergroup"]):
            await message.reply_text("❌ Unauthorized. Contact admin for access.")
            return
        
        # Convert to standard format
        channel_message = ChannelMessage(
            message_id=str(message.message_id),
            channel=ChannelType.TELEGRAM,
            sender_id=str(user.id),
            sender_name=user.full_name,
            content=message.text,
            timestamp=message.date.isoformat(),
            chat_id=str(chat.id),
            chat_name=chat.title if chat.title else user.full_name,
            is_group=chat.type in ["group", "supergroup"],
            reply_to=str(message.reply_to_message.message_id) if message.reply_to_message else None
        )
        
        # Forward to gateway
        await self.on_message(channel_message)
    
    async def _handle_media(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming media"""
        user = update.effective_user
        chat = update.effective_chat
        message = update.message
        
        # Check authorization
        if not self._is_allowed(user.id, chat.id, chat.type in ["group", "supergroup"]):
            await message.reply_text("❌ Unauthorized. Contact admin for access.")
            return
        
        # Determine media type
        media_type = None
        media_url = None
        
        if message.photo:
            media_type = "photo"
            # Get highest res photo
            media_url = message.photo[-1].file_id
        elif message.video:
            media_type = "video"
            media_url = message.video.file_id
        elif message.audio:
            media_type = "audio"
            media_url = message.audio.file_id
        elif message.voice:
            media_type = "voice"
            media_url = message.voice.file_id
        
        # Convert to standard format
        channel_message = ChannelMessage(
            message_id=str(message.message_id),
            channel=ChannelType.TELEGRAM,
            sender_id=str(user.id),
            sender_name=user.full_name,
            content=message.caption or "",
            timestamp=message.date.isoformat(),
            chat_id=str(chat.id),
            chat_name=chat.title if chat.title else user.full_name,
            is_group=chat.type in ["group", "supergroup"],
            media_type=media_type,
            media_url=media_url
        )
        
        # Forward to gateway
        await self.on_message(channel_message)
