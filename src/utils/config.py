"""
Configuration Management
========================

Centralized configuration using Pydantic settings.
"""

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Core AI APIs (Anthropic is required for core functionality)
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    replicate_api_token: Optional[str] = None
    
    # Voice APIs
    elevenlabs_api_key: Optional[str] = None
    
    # Messaging APIs
    whatsapp_phone_id: Optional[str] = None
    whatsapp_access_token: Optional[str] = None
    whatsapp_verify_token: Optional[str] = None
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    
    # Business APIs
    printify_api_token: Optional[str] = None
    printify_api_key: Optional[str] = None  # Alias for api_token
    printify_shop_id: Optional[str] = None
    shopify_api_key: Optional[str] = None
    shopify_api_secret: Optional[str] = None
    shopify_shop_name: Optional[str] = None
    shopify_password: Optional[str] = None
    shopify_store_url: Optional[str] = None
    shopify_access_token: Optional[str] = None
    serper_api_key: Optional[str] = None
    youtube_client_id: Optional[str] = None
    youtube_client_secret: Optional[str] = None
    youtube_api_key: Optional[str] = None
    youtube_refresh_token: Optional[str] = None
    
    # Database
    database_url: str = "sqlite:///./otto.db"
    database_pool_size: int = 20
    database_max_overflow: int = 40
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 50
    
    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_persist_directory: str = "./data/chroma"
    
    # Ray (Distributed Computing)
    ray_address: Optional[str] = None
    ray_dashboard_port: int = 8265
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    api_reload: bool = False
    debug_mode: bool = False
    
    # Security
    jwt_secret_key: str = "change-this-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080
    api_key_header: str = "X-API-Key"
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/otto.log"
    sentry_dsn: Optional[str] = None
    
    # Model Configurations
    default_ai_model: str = "claude-sonnet-4-20250514"
    fallback_ai_model: str = "gpt-4-turbo-preview"
    max_tokens: int = 4096
    temperature: float = 0.7
    
    # Voice Settings
    voice_model: str = "whisper-1"
    tts_model: str = "eleven_multilingual_v2"
    tts_voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    sample_rate: int = 16000
    audio_format: str = "wav"
    
    # WebSocket
    ws_heartbeat_interval: int = 30
    ws_max_connections: int = 1000
    
    # Tool Execution
    max_tool_retries: int = 3
    tool_timeout_seconds: int = 300
    parallel_tool_limit: int = 10
    
    # Memory Settings
    memory_max_history: int = 50
    memory_similarity_threshold: float = 0.7
    memory_top_k: int = 5
    
    # Browser Automation
    playwright_headless: bool = True
    browser_timeout: int = 30000
    screenshot_path: str = "./data/screenshots"
    
    # File Storage
    upload_dir: str = "./data/uploads"
    max_upload_size: str = "100MB"
    allowed_extensions: str = ".jpg,.jpeg,.png,.gif,.mp4,.mp3,.pdf,.doc,.docx"
    
    # Monitoring
    prometheus_port: int = 9090
    health_check_interval: int = 30
    
    # Development
    mock_external_apis: bool = False
    enable_profiling: bool = False
    cors_origins: str = "http://localhost:3000,http://localhost:8000"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from env file


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
