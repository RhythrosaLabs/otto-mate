"""
Extension Registry - Modular Integration Management
===================================================

Manages available integrations as extensions that can be enabled/disabled.
"""

import logging
from typing import Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class ExtensionCategory(str, Enum):
    """Categories for extensions."""
    ECOMMERCE = "ecommerce"
    AI_MODELS = "ai_models"
    AUTOMATION = "automation"
    MEDIA = "media"
    PRODUCTIVITY = "productivity"
    RESEARCH = "research"
    STORAGE = "storage"
    COMMUNICATION = "communication"


@dataclass
class Extension:
    """Extension definition."""
    id: str
    name: str
    description: str
    category: ExtensionCategory
    icon: str
    enabled: bool = True
    required_keys: List[str] = field(default_factory=list)
    optional_keys: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)


class ExtensionRegistry:
    """Manages available and enabled extensions."""
    
    def __init__(self):
        self.extensions: Dict[str, Extension] = {}
        self._register_default_extensions()
        logger.info("Extension Registry initialized")
    
    def _register_default_extensions(self):
        """Register all available extensions."""
        
        # E-Commerce
        self.register(Extension(
            id="printify",
            name="Printify",
            description="Create and manage print-on-demand products",
            category=ExtensionCategory.ECOMMERCE,
            icon="👕",
            required_keys=["printify_api_key", "printify_shop_id"],
            tools=[
                "printify_create_product",
                "printify_list_products",
                "printify_get_product",
                "printify_publish_product",
                "printify_delete_product",
                "printify_upload_image",
                "printify_list_blueprints",
                "printify_get_variants",
                "printify_get_print_providers",
                "printify_create_tshirt",
                "printify_create_mug"
            ]
        ))
        
        self.register(Extension(
            id="shopify",
            name="Shopify",
            description="Manage Shopify store products and orders",
            category=ExtensionCategory.ECOMMERCE,
            icon="🛒",
            required_keys=["shopify_api_key", "shopify_shop_name"],
            optional_keys=["shopify_api_secret"],
            tools=[
                "shopify_list_products",
                "shopify_create_product",
                "shopify_update_product",
                "shopify_delete_product",
                "shopify_list_orders",
                "shopify_get_order",
                "shopify_update_inventory",
                "shopify_list_collections",
                "shopify_add_to_collection",
                "shopify_list_blogs",
                "shopify_create_blog_post",
                "shopify_get_analytics"
            ]
        ))
        
        # AI Models
        self.register(Extension(
            id="replicate",
            name="Replicate",
            description="Access 1000+ AI models for image, video, audio generation",
            category=ExtensionCategory.AI_MODELS,
            icon="🤖",
            required_keys=["replicate_api_token"],
            tools=[
                "replicate_run_model",
                "replicate_get_model_info",
                "replicate_search_models",
                "replicate_list_collections",
                "replicate_get_collection",
                "replicate_smart_generate",
                "generate_image",
                "generate_tshirt_design",
                "generate_product_mockup",
                "generate_lifestyle_scene",
                "upscale_image",
                "remove_background"
            ]
        ))
        
        # Automation
        self.register(Extension(
            id="browser",
            name="Browser Automation",
            description="Control browsers, scrape websites, automate web tasks",
            category=ExtensionCategory.AUTOMATION,
            icon="🌐",
            required_keys=[],
            tools=[
                "browser_navigate",
                "browser_click",
                "browser_type",
                "browser_scroll",
                "browser_screenshot",
                "browser_get_text",
                "browser_get_page_content",
                "browser_fill_form",
                "browser_execute_script",
                "browser_wait",
                "browser_social_post"
            ]
        ))
        
        # Research
        self.register(Extension(
            id="web_search",
            name="Web Search",
            description="Search the web and get real-time information",
            category=ExtensionCategory.RESEARCH,
            icon="🔍",
            required_keys=["serper_api_key"],
            tools=[
                "search_web",
                "search_images",
                "browse_url",
                "research_topic",
                "get_trending_topics",
                "analyze_competitor"
            ]
        ))
        
        # Storage (always enabled)
        self.register(Extension(
            id="file_storage",
            name="File Storage",
            description="Save, retrieve, and manage files",
            category=ExtensionCategory.STORAGE,
            icon="📁",
            required_keys=[],
            enabled=True,
            tools=[
                "save_file",
                "get_file",
                "list_files",
                "delete_file",
                "get_storage_stats",
                "save_generated_image",
                "save_image_from_url"
            ]
        ))
        
        # Content Generation (always enabled)
        self.register(Extension(
            id="content_generation",
            name="Content Generation",
            description="Generate marketing copy, blog posts, and more",
            category=ExtensionCategory.PRODUCTIVITY,
            icon="✍️",
            required_keys=[],
            enabled=True,
            tools=[
                "generate_blog_post",
                "generate_product_description",
                "generate_email_campaign",
                "generate_social_media_posts",
                "generate_ad_copy",
                "generate_seo_content",
                "improve_text"
            ]
        ))
        
        # Code Execution (always enabled)
        self.register(Extension(
            id="code_execution",
            name="Code Execution",
            description="Run Python code and shell commands",
            category=ExtensionCategory.PRODUCTIVITY,
            icon="💻",
            required_keys=[],
            enabled=True,
            tools=[
                "execute_python",
                "execute_shell",
                "solve_with_code",
                "create_file",
                "read_file",
                "list_workspace_files",
                "install_package"
            ]
        ))
        
        # Task Queue
        self.register(Extension(
            id="task_queue",
            name="Task Queue",
            description="Background task execution and scheduling",
            category=ExtensionCategory.PRODUCTIVITY,
            icon="⏰",
            required_keys=[],
            enabled=True,
            tools=[
                "queue_task",
                "execute_task",
                "list_queued_tasks",
                "cancel_task",
                "track_task_progress",
                "manage_task_artifacts"
            ]
        ))
        
        # Model Chaining
        self.register(Extension(
            id="model_chaining",
            name="Model Chaining",
            description="Chain multiple AI models together",
            category=ExtensionCategory.AI_MODELS,
            icon="🔗",
            required_keys=[],
            enabled=True,
            tools=[
                "create_model_chain",
                "execute_model_chain",
                "save_chain_template",
                "list_chain_templates"
            ]
        ))
        
        # Data Processing
        self.register(Extension(
            id="data_processing",
            name="Data Processing",
            description="Process and transform data",
            category=ExtensionCategory.PRODUCTIVITY,
            icon="📊",
            required_keys=[],
            enabled=True,
            tools=[
                "convert_format",
                "process_json"
            ]
        ))
        
        # YouTube
        self.register(Extension(
            id="youtube",
            name="YouTube",
            description="Upload videos, search YouTube, and manage your channel",
            category=ExtensionCategory.MEDIA,
            icon="📺",
            required_keys=[],
            optional_keys=["youtube_api_key", "youtube_client_id", "youtube_client_secret", "youtube_refresh_token"],
            enabled=True,
            tools=[
                "youtube_search",
                "youtube_get_video",
                "youtube_upload_video",
                "youtube_list_my_videos"
            ]
        ))
    
    def register(self, extension: Extension):
        """Register an extension."""
        self.extensions[extension.id] = extension
        logger.debug(f"Registered extension: {extension.name}")
    
    def enable(self, extension_id: str) -> bool:
        """Enable an extension."""
        if extension_id in self.extensions:
            self.extensions[extension_id].enabled = True
            logger.info(f"Enabled extension: {extension_id}")
            return True
        return False
    
    def disable(self, extension_id: str) -> bool:
        """Disable an extension."""
        if extension_id in self.extensions:
            self.extensions[extension_id].enabled = False
            logger.info(f"Disabled extension: {extension_id}")
            return True
        return False
    
    def get_enabled_extensions(self) -> List[Extension]:
        """Get list of enabled extensions."""
        return [ext for ext in self.extensions.values() if ext.enabled]
    
    def get_extension(self, extension_id: str) -> Optional[Extension]:
        """Get extension by ID."""
        return self.extensions.get(extension_id)
    
    def get_all_extensions(self) -> List[Extension]:
        """Get all extensions."""
        return list(self.extensions.values())
    
    def get_enabled_tools(self) -> List[str]:
        """Get list of tool IDs from enabled extensions."""
        tools = []
        for ext in self.get_enabled_extensions():
            tools.extend(ext.tools)
        return tools
    
    def is_extension_configured(self, extension_id: str, config: Dict) -> bool:
        """Check if extension has required API keys configured."""
        extension = self.get_extension(extension_id)
        if not extension:
            return False
        
        for key in extension.required_keys:
            if not config.get(key):
                return False
        
        return True
    
    def get_by_category(self, category: ExtensionCategory) -> List[Extension]:
        """Get extensions by category."""
        return [ext for ext in self.extensions.values() if ext.category == category]
    
    def get_missing_keys(self, extension_id: str, config: Dict) -> List[str]:
        """Get list of missing required keys for an extension."""
        extension = self.get_extension(extension_id)
        if not extension:
            return []
        
        return [key for key in extension.required_keys if not config.get(key)]


# Global registry
_extension_registry: Optional[ExtensionRegistry] = None


def get_extension_registry() -> ExtensionRegistry:
    """Get or create the global extension registry."""
    global _extension_registry
    if _extension_registry is None:
        _extension_registry = ExtensionRegistry()
    return _extension_registry
