"""
Settings API
============

Endpoints for managing application settings.
"""

import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException
from datetime import datetime

logger = logging.getLogger(__name__)

# Settings file path
SETTINGS_FILE = Path("./data/settings.json")


class AISettings(BaseModel):
    """AI model settings."""
    default_model: str = "claude-sonnet-4-20250514"
    fallback_model: str = "gpt-4o"
    reasoning_model: str = "claude-opus-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.7
    enable_streaming: bool = True


class VoiceSettings(BaseModel):
    """Voice settings."""
    stt_model: str = "whisper-large-v3"
    tts_provider: str = "openai"  # openai, elevenlabs
    tts_voice: str = "nova"
    tts_speed: float = 1.0
    auto_play_responses: bool = True
    voice_activation: bool = False


class ImageSettings(BaseModel):
    """Image generation and editing settings."""
    default_model: str = "flux_pro"
    fallback_model: str = "sdxl"
    default_style: str = "auto"  # auto-detect from prompt
    default_size: str = "1024x1024"
    default_aspect_ratio: str = "1:1"  # 1:1, 16:9, 9:16, 2:3, 3:2, etc.
    default_quality: str = "standard"  # standard, hd
    editing_model: str = "sdxl"  # for image-to-image editing
    upscale_model: str = "real-esrgan"
    auto_remove_background: bool = False
    save_generated_images: bool = True


class VideoSettings(BaseModel):
    """Video generation and editing settings."""
    default_model: str = "kling"  # kling, minimax, svd, runway
    fallback_model: str = "svd"
    default_duration: int = 5  # seconds
    default_fps: int = 24
    default_aspect_ratio: str = "16:9"
    editing_model: str = "kling"
    upscale_model: str = "real-esrgan-video"
    stabilization_enabled: bool = True
    save_generated_videos: bool = True


class AudioSettings(BaseModel):
    """Audio generation and editing settings."""
    default_music_model: str = "musicgen"
    default_voice_model: str = "bark"
    voice_clone_model: str = "xtts-v2"
    transcription_model: str = "whisper-large-v3"
    enhancement_model: str = "resemble-enhance"
    save_generated_audio: bool = True


class PrintifySettings(BaseModel):
    """Printify integration settings."""
    enabled: bool = True
    shop_id: str = ""
    default_blueprint: int = 6  # Unisex Jersey Short Sleeve Tee
    default_print_provider: int = 99  # Monster Digital
    auto_publish: bool = False
    default_tags: List[str] = []


class ShopifySettings(BaseModel):
    """Shopify integration settings."""
    enabled: bool = True
    shop_name: str = ""
    auto_sync: bool = False
    sync_interval_minutes: int = 60


class StorageSettings(BaseModel):
    """Storage settings."""
    provider: str = "local"  # local, s3, gcs
    max_file_size_mb: int = 100
    auto_cleanup_days: int = 30
    image_compression: bool = True
    image_max_dimension: int = 4096


class NotificationSettings(BaseModel):
    """Notification settings."""
    email_notifications: bool = False
    email_address: str = ""
    webhook_url: str = ""
    notify_on_order: bool = True
    notify_on_error: bool = True
    daily_digest: bool = False


class UISettings(BaseModel):
    """UI preferences."""
    theme: str = "dark"  # dark, light, system
    language: str = "en"
    timezone: str = "UTC"
    date_format: str = "YYYY-MM-DD"
    compact_mode: bool = False
    show_tool_details: bool = True


class ExtensionSettings(BaseModel):
    """Extension enable/disable settings."""
    printify: bool = True
    shopify: bool = True
    replicate: bool = True
    browser: bool = True
    web_search: bool = True
    file_storage: bool = True
    content_generation: bool = True
    code_execution: bool = True
    data_processing: bool = True
    task_queue: bool = True
    model_chaining: bool = True


class AppSettings(BaseModel):
    """Complete application settings."""
    ai: AISettings = Field(default_factory=AISettings)
    voice: VoiceSettings = Field(default_factory=VoiceSettings)
    image: ImageSettings = Field(default_factory=ImageSettings)
    video: VideoSettings = Field(default_factory=VideoSettings)
    audio: AudioSettings = Field(default_factory=AudioSettings)
    printify: PrintifySettings = Field(default_factory=PrintifySettings)
    shopify: ShopifySettings = Field(default_factory=ShopifySettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    ui: UISettings = Field(default_factory=UISettings)
    extensions: ExtensionSettings = Field(default_factory=ExtensionSettings)
    updated_at: Optional[str] = None


class SettingsManager:
    """Manages application settings persistence."""
    
    def __init__(self, settings_path: Path = SETTINGS_FILE):
        self.settings_path = settings_path
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self._settings: Optional[AppSettings] = None
    
    def load(self) -> AppSettings:
        """Load settings from file."""
        if self._settings is not None:
            return self._settings
        
        if self.settings_path.exists():
            try:
                with open(self.settings_path, "r") as f:
                    data = json.load(f)
                    self._settings = AppSettings(**data)
            except Exception as e:
                logger.error(f"Failed to load settings: {e}")
                self._settings = AppSettings()
        else:
            self._settings = AppSettings()
        
        return self._settings
    
    def save(self, settings: AppSettings) -> bool:
        """Save settings to file."""
        try:
            settings.updated_at = datetime.now().isoformat()
            with open(self.settings_path, "w") as f:
                json.dump(settings.dict(), f, indent=2)
            self._settings = settings
            logger.info("Settings saved successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False
    
    def update(self, section: str, values: Dict[str, Any]) -> AppSettings:
        """Update a specific settings section."""
        settings = self.load()
        
        if not hasattr(settings, section):
            raise ValueError(f"Unknown settings section: {section}")
        
        section_obj = getattr(settings, section)
        for key, value in values.items():
            if hasattr(section_obj, key):
                setattr(section_obj, key, value)
        
        self.save(settings)
        return settings
    
    def reset(self, section: Optional[str] = None) -> AppSettings:
        """Reset settings to defaults."""
        if section:
            settings = self.load()
            if section == "ai":
                settings.ai = AISettings()
            elif section == "voice":
                settings.voice = VoiceSettings()
            elif section == "image":
                settings.image = ImageSettings()
            elif section == "video":
                settings.video = VideoSettings()
            elif section == "audio":
                settings.audio = AudioSettings()
            elif section == "printify":
                settings.printify = PrintifySettings()
            elif section == "shopify":
                settings.shopify = ShopifySettings()
            elif section == "storage":
                settings.storage = StorageSettings()
            elif section == "notifications":
                settings.notifications = NotificationSettings()
            elif section == "ui":
                settings.ui = UISettings()
            elif section == "extensions":
                settings.extensions = ExtensionSettings()
            self.save(settings)
        else:
            settings = AppSettings()
            self.save(settings)
        
        return settings


# Global settings manager
settings_manager = SettingsManager()


# Create router
router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=AppSettings)
async def get_settings():
    """Get all application settings."""
    return settings_manager.load()


@router.put("", response_model=AppSettings)
async def update_all_settings(settings: AppSettings):
    """Update all settings at once."""
    if settings_manager.save(settings):
        return settings
    raise HTTPException(status_code=500, detail="Failed to save settings")


@router.get("/{section}")
async def get_settings_section(section: str):
    """Get a specific settings section."""
    settings = settings_manager.load()
    
    if not hasattr(settings, section):
        raise HTTPException(status_code=404, detail=f"Section '{section}' not found")
    
    return getattr(settings, section)


@router.patch("/{section}")
async def update_settings_section(section: str, values: Dict[str, Any]):
    """Update a specific settings section."""
    try:
        settings = settings_manager.update(section, values)
        return getattr(settings, section)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reset")
async def reset_settings(section: Optional[str] = None):
    """Reset settings to defaults."""
    settings = settings_manager.reset(section)
    return {
        "message": f"Settings reset{'for ' + section if section else ''}",
        "settings": settings
    }


@router.get("/export")
async def export_settings():
    """Export settings as JSON."""
    settings = settings_manager.load()
    return {
        "settings": settings.dict(),
        "exported_at": datetime.now().isoformat()
    }


@router.post("/import")
async def import_settings(data: Dict[str, Any]):
    """Import settings from JSON."""
    try:
        settings = AppSettings(**data.get("settings", data))
        if settings_manager.save(settings):
            return {"message": "Settings imported successfully", "settings": settings}
        raise HTTPException(status_code=500, detail="Failed to import settings")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid settings format: {e}")
