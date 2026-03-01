"""
Base Channel Interface

Abstract base for all messaging platform integrations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class ChannelType(Enum):
    """Supported channel types"""
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    SLACK = "slack"
    SIGNAL = "signal"
    IMESSAGE = "imessage"
    TEAMS = "teams"


@dataclass
class ChannelMessage:
    """Universal message format across channels"""
    message_id: str
    channel: ChannelType
    sender_id: str
    sender_name: str
    content: str
    timestamp: str
    chat

_id: str
    chat_name: Optional[str] = None
    is_group: bool = False
    reply_to: Optional[str] = None
    media_type: Optional[str] = None
    media_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "channel": self.channel.value,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "content": self.content,
            "timestamp": self.timestamp,
            "chat_id": self.chat_id,
            "chat_name": self.chat_name,
            "is_group": self.is_group,
            "reply_to": self.reply_to,
            "media_type": self.media_type,
            "media_url": self.media_url
        }


class BaseChannel(ABC):
    """Base class for all channel integrations"""
    
    def __init__(self, gateway, config: Dict[str, Any]):
        self.gateway = gateway
        self.config = config
        self.is_connected = False
        
    @abstractmethod
    async def connect(self):
        """Connect to the channel"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect from the channel"""
        pass
    
    @abstractmethod
    async def send_message(
        self,
        chat_id: str,
        content: str,
        reply_to: Optional[str] = None,
        media_path: Optional[str] = None
    ) -> str:
        """Send message to a chat"""
        pass
    
    @abstractmethod
    async def get_chat_history(
        self,
        chat_id: str,
        limit: int = 50
    ) -> List[ChannelMessage]:
        """Get recent messages from a chat"""
        pass
    
    async def on_message(self, message: ChannelMessage):
        """Handle incoming message"""
        # Broadcast to gateway
        await self.gateway.broadcast_event(
            "chat",
            {
                "source": "channel",
                "channel": message.channel.value,
                "message": message.to_dict()
            }
        )
