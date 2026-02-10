"""
Otto Universal Tools - Export all tools including autonomous capabilities.
"""

from .core import tool, ToolBase
from .printify import PrintifyTools
from .image_generation import ImageGenerationTools
from .research import ResearchTools
from .shopify import ShopifyTools
from .content import ContentTools
from .browser import BrowserTools
from .file_storage import FileStorageTools
from .replicate_universal import ReplicateUniversal
from .code_execution import CodeExecutionTools, DataProcessingTools
from .youtube import YouTubeTools

# Advanced video and audio production modules
from .video_generation import (
    AdvancedVideoGenerator,
    get_video_generator,
    VOICE_MAP,
    MUSIC_PROMPTS,
    CAMERA_DIRECTIONS
)
from .audio_processing import (
    AudioProcessor,
    get_audio_processor,
    compose_video_with_audio,
    concatenate_video_segments
)
from .promo_video import PromoVideoService, get_promo_video_service

# Chat history and project management
from .chat_history import ChatHistoryManager, get_chat_history_manager
from .project_manager import ProjectManager, ProjectStatus, get_project_manager

# Brand management
from .brand_brain import BrandBrain, get_brand_brain

# Social media automation
from .social_poster import (
    MultiPlatformPoster,
    get_multi_platform_poster,
    PostingMetrics,
    BrowserPerformanceConfig,
    PLATFORM_CONFIG,
    get_available_platforms,
    quick_post,
)

# Email marketing
from .email_marketing import EmailMarketingService, get_email_service

# Contacts management (CRM)
from .contacts import ContactsTools, contacts_tools, load_contacts, save_contacts

# Enhanced task queue engine
from .task_queue_engine import (
    EnhancedTaskQueueEngine,
    get_task_queue_engine,
    Task,
    TaskStep,
    TaskStatus,
    TaskPriority,
    Artifact,
    ArtifactType,
)

# ==========================================
# NEW ADVANCED INTEGRATIONS
# ==========================================

# Advanced Shopify (bulk operations, metafields, webhooks, discounts)
from .shopify_advanced import ShopifyAdvancedTools, create_shopify_advanced_tools

# Browser-Use Integration (AI-powered browser automation with stealth)
from .browser_use_advanced import BrowserUseTools, create_browser_use_tools
from .browser_stealth import (
    create_stealth_profile, 
    create_social_media_profile,
    BROWSER_USE_AVAILABLE as BROWSER_STEALTH_AVAILABLE,
)

# Advanced Replicate (webhooks, chaining, batch processing)
from .replicate_advanced import (
    ReplicateAdvancedTools,
    ReplicateWebhookHandler,
    create_replicate_advanced_tools
)

# Task Scheduler (cron jobs, recurring tasks)
from .scheduler import (
    TaskScheduler,
    ScheduledTask,
    TaskExecution,
    ScheduleType,
    ScheduledTaskStatus,
    SCHEDULE_PRESETS,
    create_task_scheduler
)

# AI File Editor (AI-powered code editing)
from .ai_file_editor import AIFileEditor, get_ai_file_editor

# Universal Media Editor (images, video, audio, 3D, text)
from .universal_editor import UniversalEditor, get_universal_editor, REPLICATE_MODELS, MediaType

# Codebase Awareness (Otto's self-knowledge)
from .codebase_awareness import CodebaseAwareness, OTTO_ARCHITECTURE, OTTO_CAPABILITIES

# Social Media Ads (professional ad generation)
from .social_media_ads import SocialMediaAdsTools, create_social_media_ads_tools

__all__ = [
    "tool", "ToolBase",
    "PrintifyTools", "ImageGenerationTools", "ResearchTools",
    "ShopifyTools", "ContentTools", "BrowserTools", "FileStorageTools",
    "ReplicateUniversal", "CodeExecutionTools", "DataProcessingTools",
    "YouTubeTools",
    # Video production
    "AdvancedVideoGenerator", "get_video_generator",
    "VOICE_MAP", "MUSIC_PROMPTS", "CAMERA_DIRECTIONS",
    # Audio processing
    "AudioProcessor", "get_audio_processor",
    "compose_video_with_audio", "concatenate_video_segments",
    # Promo video service
    "PromoVideoService", "get_promo_video_service",
    # Chat history and project management
    "ChatHistoryManager", "get_chat_history_manager",
    "ProjectManager", "ProjectStatus", "get_project_manager",
    # Brand management
    "BrandBrain", "get_brand_brain",
    # Social media automation
    "MultiPlatformPoster", "get_multi_platform_poster",
    "PostingMetrics", "BrowserPerformanceConfig", "PLATFORM_CONFIG",
    "get_available_platforms", "quick_post",
    # Email marketing
    "EmailMarketingService", "get_email_service",
    # Contacts management (CRM)
    "ContactsTools", "contacts_tools", "load_contacts", "save_contacts",
    # Enhanced task queue engine
    "EnhancedTaskQueueEngine", "get_task_queue_engine",
    "Task", "TaskStep", "TaskStatus", "TaskPriority",
    "Artifact", "ArtifactType",
    # ==========================================
    # NEW ADVANCED INTEGRATIONS
    # ==========================================
    # Advanced Shopify
    "ShopifyAdvancedTools", "create_shopify_advanced_tools",
    # Browser-Use Integration (with stealth)
    "BrowserUseTools", "create_browser_use_tools",
    "create_stealth_profile", "create_social_media_profile",
    # Advanced Replicate
    "ReplicateAdvancedTools", "ReplicateWebhookHandler", "create_replicate_advanced_tools",
    # Task Scheduler
    "TaskScheduler", "ScheduledTask", "TaskExecution",
    "ScheduleType", "ScheduledTaskStatus", "SCHEDULE_PRESETS", "create_task_scheduler",
    # AI File Editor
    "AIFileEditor", "get_ai_file_editor",
    # Universal Media Editor
    "UniversalEditor", "get_universal_editor", "REPLICATE_MODELS", "MediaType",
    # Codebase Awareness
    "CodebaseAwareness", "OTTO_ARCHITECTURE", "OTTO_CAPABILITIES",
    # Social Media Ads
    "SocialMediaAdsTools", "create_social_media_ads_tools",
]
