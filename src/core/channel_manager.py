"""
Channel Manager

Manages all messaging channel integrations.
Dynamically loads and starts channels based on configuration.
"""

import logging
from typing import Dict, Any, List
from pathlib import Path

from src.channels.base import BaseChannel, ChannelType
from src.core.gateway import OttoGateway

logger = logging.getLogger(__name__)


class ChannelManager:
    """
    Manages all active messaging channels
    
    Loads channels from config and starts/stops them.
    """
    
    def __init__(self, gateway: OttoGateway, config: Dict[str, Any]):
        self.gateway = gateway
        self.config = config
        self.channels: Dict[ChannelType, BaseChannel] = {}
    
    async def start_channels(self):
        """Start all configured channels"""
        channels_config = self.config.get("channels", {})
        
        for channel_type, channel_config in channels_config.items():
            if not channel_config.get("enabled", False):
                logger.info(f"⏭️  Skipping disabled channel: {channel_type}")
                continue
            
            try:
                await self._start_channel(channel_type, channel_config)
            except Exception as e:
                logger.error(f"Failed to start channel {channel_type}: {e}")
    
    async def _start_channel(self, channel_type: str, config: Dict[str, Any]):
        """Start a single channel"""
        logger.info(f"🚀 Starting channel: {channel_type}")
        
        try:
            # Import channel class dynamically
            if channel_type == "telegram":
                from src.channels.telegram import TelegramChannel
                channel = TelegramChannel(self.gateway, config)
            
            elif channel_type == "discord":
                from src.channels.discord import DiscordChannel
                channel = DiscordChannel(self.gateway, config)
            
            elif channel_type == "slack":
                from src.channels.slack import SlackChannel
                channel = SlackChannel(self.gateway, config)
            
            else:
                logger.warning(f"Unknown channel type: {channel_type}")
                return
            
            # Connect channel
            await channel.connect()
            
            # Register with gateway
            channel_enum = ChannelType[channel_type.upper()]
            self.channels[channel_enum] = channel
            self.gateway.register_channel(channel_enum, channel)
            
            logger.info(f"✅ Channel started: {channel_type}")
        
        except ImportError as e:
            logger.warning(f"Channel {channel_type} not available: {e}")
        except Exception as e:
            logger.error(f"Failed to start {channel_type}: {e}")
            raise
    
    async def stop_channels(self):
        """Stop all channels"""
        for channel_type, channel in self.channels.items():
            try:
                logger.info(f"🛑 Stopping channel: {channel_type.value}")
                await channel.disconnect()
            except Exception as e:
                logger.error(f"Error stopping {channel_type.value}: {e}")
        
        self.channels.clear()
    
    def get_channel(self, channel_type: ChannelType) -> BaseChannel:
        """Get a channel by type"""
        return self.channels.get(channel_type)
    
    def list_channels(self) -> List[Dict[str, Any]]:
        """List all active channels"""
        return [
            {
                "type": channel_type.value,
                "connected": channel.is_connected,
                "config": channel.config
            }
            for channel_type, channel in self.channels.items()
        ]
