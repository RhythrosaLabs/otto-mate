"""
Gateway & Channels Configuration Schema

Pydantic models for validating gateway and channel configuration.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class TelegramConfig(BaseModel):
    """Telegram channel configuration"""
    enabled: bool = False
    bot_token: Optional[str] = Field(None, env="TELEGRAM_BOT_TOKEN")
    allow_from: List[str] = ["*"]
    groups: Dict[str, bool] = {}


class DiscordConfig(BaseModel):
    """Discord channel configuration"""
    enabled: bool = False
    token: Optional[str] = Field(None, env="DISCORD_BOT_TOKEN")
    guilds: Dict[str, bool] = {"*": True}
    allow_from: List[str] = ["*"]


class SlackConfig(BaseModel):
    """Slack channel configuration"""
    enabled: bool = False
    bot_token: Optional[str] = Field(None, env="SLACK_BOT_TOKEN")
    app_token: Optional[str] = Field(None, env="SLACK_APP_TOKEN")
    workspaces: Dict[str, bool] = {"*": True}
    channels: Dict[str, bool] = {"*": True}


class VoiceConfig(BaseModel):
    """Voice capabilities configuration"""
    enable_wake_word: bool = False
    enable_talk_mode: bool = True
    wake_word: str = "hey otto"
    language: str = "en"
    stt_provider: str = "whisper"
    tts_provider: str = "elevenlabs"
    voice_id: Optional[str] = "Adam"
    silence_timeout: float = 2.0


class GatewayConfig(BaseModel):
    """Gateway configuration"""
    enabled: bool = True
    channels: Dict[str, Any] = {
        "telegram": TelegramConfig().dict(),
        "discord": DiscordConfig().dict(),
        "slack": SlackConfig().dict()
    }
    voice: VoiceConfig = VoiceConfig()
