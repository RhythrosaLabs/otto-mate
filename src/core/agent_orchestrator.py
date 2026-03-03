"""
Otto Universal Core - Agent Orchestrator
========================================

The central brain that coordinates all agents and tool execution.
SUPERCHARGED with autonomous problem solving, dynamic AI model discovery,
and code execution capabilities.
"""

import asyncio
import logging
import uuid
import json
from typing import Any, Dict, List, Optional, AsyncGenerator
from datetime import datetime
from anthropic import Anthropic
from openai import AsyncOpenAI

from .super_planning_agent import SuperPlanningAgent as PlanningAgent
from .master_agent import MasterOrchestrator
from .execution_agent import ExecutionAgent
from .memory_agent import MemoryAgent
from .tool_registry import ToolRegistry
from .extension_registry import get_extension_registry
from .slash_commands import get_slash_processor
from .platform_intelligence import get_platform_intelligence, PlatformIntelligence

logger = logging.getLogger(__name__)

# ============================================================================
# ACTION vs QUESTION DETECTION PATTERNS
# From chat_assistant.py patterns for intelligent request routing
# ============================================================================

ACTION_KEYWORDS = [
    # Design/Create actions
    "create", "generate", "make", "design", "build", "produce",
    # Product requests
    "mockup", "mock-up", "mock up", "t-shirt", "tshirt", "hoodie", 
    "mug", "poster", "sticker", "product",
    # Content requests  
    "image", "picture", "artwork", "graphic", "logo", "video",
    "commercial", "ad", "advertisement", "write", "blog", "post",
    "content", "copy", "script",
    # Workflow triggers
    "campaign", "workflow", "end to end", "complete", "full",
    # Action verbs
    "upload", "publish", "launch", "start", "run", "execute",
    # Service sync
    "sync", "printify", "shopify", "youtube",
    # Media generation
    "render", "animate", "compose", "music", "audio", "song",
    # File operations
    "save", "download", "export", "convert", "compress"
]

QUESTION_PATTERNS = [
    "what is", "how do", "can you explain", "tell me about",
    "what are", "how does", "why", "when", "where",
    "what's the", "how can i", "what should", "is there",
    "do you know", "could you tell", "?", "help me understand"
]

# ============================================================================
# BROWSER USE vs DEEP RESEARCH DETECTION
# ============================================================================
#
# The orchestrator needs to distinguish between:
# 1. DEEP RESEARCH: Tasks AI can do via reasoning + web search APIs
# 2. BROWSER USE: Tasks requiring direct website interaction
#
# Key principle: Only use browser when we need to INTERACT with a website,
# not just LEARN about something.
# ============================================================================

# Patterns that REQUIRE direct browser interaction
BROWSER_REQUIRED_PATTERNS = [
    # Navigation and interaction
    "go to", "navigate to", "open website", "open url", "visit the site",
    "click on", "click the", "press the button", "tap on",
    "fill out", "fill in", "fill form", "submit form", "enter text",
    
    # Authentication/Account actions
    "login to", "log in to", "sign in to", "authenticate",
    "logout", "sign out", "create account on",
    
    # E-commerce actions (on external sites)
    "add to cart", "checkout on", "buy on amazon", "purchase on",
    "place order on", "order from",
    
    # Social media direct posting (not via API)
    "post to twitter directly", "tweet from browser",
    "post to facebook directly", "instagram post browser",
    
    # Screenshot and visual capture
    "take screenshot of", "screenshot of website", "capture page",
    "screenshot this page", "get screenshot from",
    
    # Data scraping from dynamic pages
    "scrape website", "scrape the page", "scrape data from",
    "extract from website", "extract from page",
    "download from website", "download file from",
    
    # Multi-step web workflows
    "navigate through", "go through the steps on",
    "complete the form on", "follow the link",
    
    # Specific URL/site interaction verbs
    "on the website", "on this page", "in the browser",
    "using the browser", "automate the website",
    "interact with", "automation on"
]

# Keywords that suggest deep research (AI + search APIs, NO browser needed)
DEEP_RESEARCH_KEYWORDS = [
    # Research verbs
    "research", "investigate", "study", "analyze", "examine",
    "learn about", "find out about", "discover", "explore",
    
    # Information gathering
    "what is", "who is", "when did", "where is", "how does", 
    "why do", "explain", "tell me about", "describe",
    "summarize", "overview of", "history of", "background on",
    
    # Analysis tasks
    "analyze trends", "market analysis", "competitor analysis",
    "compare", "contrast", "evaluate", "assess", "review",
    
    # Data gathering (via search, not scraping)
    "find information", "gather data", "collect information",
    "look up", "search for information about",
    
    # Report generation
    "write a report", "create a summary", "compile information",
    "research report", "analysis report",
    
    # Knowledge questions
    "best practices", "recommendations", "strategies",
    "tips for", "guide to", "how to guide"
]

# Ambiguous patterns that need context to decide
AMBIGUOUS_WEB_PATTERNS = [
    "search for",  # Could be web search API or browser search
    "check",  # Could be "check information" or "check website"
    "browse",  # Could mean casual reading or browser automation
    "find",  # Could be search or navigate+find
    "get from",  # Could be API or browser
    "extract",  # Could be scrape or API
]

# Legacy list for backwards compatibility (now more precise)
BROWSER_KEYWORDS = BROWSER_REQUIRED_PATTERNS

# Response formatting patterns for different artifact types
ARTIFACT_DISPLAY_CONFIG = {
    "image": {"emoji": "🖼️", "verb": "Generated", "show_url": True},
    "video": {"emoji": "🎬", "verb": "Created", "show_url": True},
    "audio": {"emoji": "🎵", "verb": "Produced", "show_url": True},
    "file": {"emoji": "📄", "verb": "Created", "show_path": True},
    "code": {"emoji": "💻", "verb": "Generated", "show_content": True},
    "product": {"emoji": "🛍️", "verb": "Published", "show_url": True},
    "3d": {"emoji": "🎮", "verb": "Rendered", "show_url": True},
}


class AgentOrchestrator:
    """
    The master orchestrator that coordinates all Otto agents.
    
    Responsibilities:
    - Receive user requests
    - Route to appropriate agents
    - Coordinate multi-step workflows
    - Manage context and memory
    - Return unified responses
    """
    
    def __init__(
        self,
        anthropic_api_key: str,
        openai_api_key: str = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.config = config or {}
        
        # Initialize AI clients (OpenAI is optional - only needed for voice)
        self.anthropic = Anthropic(api_key=anthropic_api_key)
        self.openai = AsyncOpenAI(api_key=openai_api_key) if openai_api_key and not openai_api_key.startswith("your_") else None
        
        # Initialize agents
        self.planning_agent = PlanningAgent(self.anthropic)
        self.execution_agent = ExecutionAgent(self.anthropic)
        self.memory_agent = MemoryAgent()
        
        # Wrap memory agent with enhanced memory (SQLite + ChromaDB)
        from .enhanced_memory import get_enhanced_memory
        self.enhanced_memory = get_enhanced_memory(self.memory_agent)
        
        # Initialize Intelligence System (enhanced memory, learning, fallbacks)
        from .intelligence_system import get_intelligence_system
        self.intelligence = get_intelligence_system(self.anthropic)
        
        # Inject skills registry into planning agent
        from .skills_system import get_skills_registry
        self.planning_agent.skills_registry = get_skills_registry()
        
        # Initialize tool registry
        self.tool_registry = ToolRegistry()
        self.tool_registry.discover_tools()
        
        # Initialize extension registry
        self.extension_registry = get_extension_registry()
        
        # Initialize master orchestrator for multi-agent coordination
        self.master = MasterOrchestrator(self.anthropic, self.tool_registry)
        
        # File storage reference (set during tool registration)
        self.file_storage = None
        
        # Register tool classes with their API keys (only enabled extensions)
        self._register_tool_classes()
        
        # Session management
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
        # Initialize enhanced delegation manager for intelligent task routing
        try:
            from .enhanced_agent_delegation import get_delegation_manager
            self.delegation_manager = get_delegation_manager(
                anthropic_client=self.anthropic,
                tool_registry=self.tool_registry
            )
            logger.info("Enhanced Delegation Manager initialized")
        except Exception as e:
            logger.warning(f"Enhanced delegation not available: {e}")
            self.delegation_manager = None
        
        # Initialize Enhanced Workflow Orchestrator (MODALITY → MODEL enforcement)
        try:
            from .enhanced_workflow_orchestrator import get_enhanced_orchestrator
            self.enhanced_orchestrator = get_enhanced_orchestrator(
                anthropic_client=self.anthropic,
                tool_registry=self.tool_registry,
                config=self.config
            )
            logger.info("✨ Enhanced Workflow Orchestrator initialized")
            logger.info("   → MODALITY → MODEL selection enforced")
            logger.info("   → LangChain task interpretation enabled")
            logger.info("   → CrewAI delegation enabled")
        except Exception as e:
            logger.warning(f"Enhanced orchestrator not available: {e}")
            self.enhanced_orchestrator = None
        
        logger.info("Agent Orchestrator initialized")
    
    def _register_tool_classes(self):
        """Initialize and register all tool classes from enabled extensions."""
        try:
            from ..tools import (
                PrintifyTools,
                ImageGenerationTools,
                ResearchTools,
                ShopifyTools,
                ContentTools,
                BrowserTools,
                FileStorageTools
            )
            from ..tools.browser_use_advanced import BrowserUseTools, BROWSER_USE_AVAILABLE
            from ..tools.replicate_universal import ReplicateUniversal
            from ..tools.code_execution import CodeExecutionTools, DataProcessingTools
            from ..storage import FileStorage, StorageConfig
            
            enabled_extensions = self.extension_registry.get_enabled_extensions()
            enabled_ext_ids = [ext.id for ext in enabled_extensions]
            
            logger.info(f"Loading {len(enabled_extensions)} enabled extensions...")
            
            # === CORE AUTONOMOUS TOOLS ===
            
            # Universal Replicate - access to ANY AI model
            replicate = None
            if "replicate" in enabled_ext_ids and self.config.get("replicate_api_token"):
                replicate = ReplicateUniversal(api_token=self.config["replicate_api_token"])
                self.tool_registry.register_tool_class(replicate)
                logger.info("Registered Universal Replicate tools (ANY AI model access)")
            
            # Code execution - write and run code autonomously (always enabled)
            if "code_execution" in enabled_ext_ids:
                code_tools = CodeExecutionTools(workspace_dir="./workspace")
                self.tool_registry.register_tool_class(code_tools)
                logger.info("Registered Code Execution tools")
            
            # Data processing (always enabled)
            if "data_processing" in enabled_ext_ids:
                data_tools = DataProcessingTools(workspace_dir="./workspace")
                self.tool_registry.register_tool_class(data_tools)
                logger.info("Registered Data Processing tools")
            
            # === INTEGRATION TOOLS ===
            
            # Shopify tools - initialize FIRST so Printify can sync to it
            shopify = None
            if "shopify" in enabled_ext_ids:
                shopify_url = self.config.get("shopify_shop_name") or self.config.get("shopify_store_url")
                shopify_token = self.config.get("shopify_access_token") or self.config.get("shopify_api_key")
                if shopify_url and shopify_token:
                    shopify = ShopifyTools(
                        shop_url=shopify_url,
                        access_token=shopify_token
                    )
                    self.tool_registry.register_tool_class(shopify)
                    logger.info("✓ Shopify tools registered")
                else:
                    logger.warning("Shopify extension enabled but not fully configured")
            
            # Printify tools - with Shopify sync
            if "printify" in enabled_ext_ids:
                printify_key = self.config.get("printify_api_key") or self.config.get("printify_api_token")
                printify_shop_id = self.config.get("printify_shop_id")
                if printify_key and printify_shop_id:
                    try:
                        printify = PrintifyTools(
                            api_token=printify_key,
                            shop_id=str(printify_shop_id),
                            shopify_tools=shopify  # Pass Shopify for cross-platform sync
                        )
                        self.tool_registry.register_tool_class(printify)
                        sync_status = "with Shopify sync" if shopify else "without Shopify sync"
                        logger.info(f"✓ Printify tools registered (shop: {printify_shop_id}) {sync_status}")
                    except Exception as e:
                        logger.error(f"Failed to initialize Printify: {e}")
                else:
                    logger.warning(f"Printify credentials missing - key: {bool(printify_key)}, shop_id: {bool(printify_shop_id)}")
            
            # Image generation tools
            if "replicate" in enabled_ext_ids:
                if self.config.get("replicate_api_token"):
                    image_gen = ImageGenerationTools(
                        replicate_token=self.config["replicate_api_token"]
                    )
                    self.tool_registry.register_tool_class(image_gen)
                    logger.info("Registered Image Generation tools")
            
            # Research tools
            if "web_search" in enabled_ext_ids:
                research = ResearchTools(
                    config={"serper_api_key": self.config.get("serper_api_key", "")}
                )
                self.tool_registry.register_tool_class(research)
                logger.info("Registered Research tools")
            
            # Content tools (always enabled)
            if "content_generation" in enabled_ext_ids:
                content = ContentTools(
                    anthropic_client=self.anthropic,
                    replicate_token=self.config.get("replicate_api_token")  # Enable AI image generation for blogs/emails
                )
                self.tool_registry.register_tool_class(content)
                logger.info("Registered Content tools" + (" with AI image generation" if self.config.get("replicate_api_token") else ""))
            
            # Browser tools (optional)
            if "browser" in enabled_ext_ids:
                try:
                    browser = BrowserTools()
                    self.tool_registry.register_tool_class(browser)
                    logger.info("Registered Browser tools")
                except Exception as e:
                    logger.warning(f"Browser tools not available: {e}")
                
                # Advanced Browser-Use tools (AI-powered browser automation)
                if BROWSER_USE_AVAILABLE:
                    try:
                        browser_use = BrowserUseTools(
                            llm_provider=self.config.get("browser_llm_provider", "anthropic"),
                            headless=self.config.get("browser_headless", False)  # Visible by default
                        )
                        self.tool_registry.register_tool_class(browser_use)
                        logger.info("Registered Browser-Use advanced tools (AI browser automation)")
                    except Exception as e:
                        logger.warning(f"Browser-Use advanced tools not available: {e}")
                else:
                    logger.info("Browser-Use not installed - run: pip install browser-use playwright && playwright install")
            
            # File storage tools - always available
            if "file_storage" in enabled_ext_ids:
                storage = FileStorage(StorageConfig())
                file_tools = FileStorageTools(storage)
                self.tool_registry.register_tool_class(file_tools)
                self.file_storage = storage  # Store reference for use by other tools
                logger.info("Registered File Storage tools")
            
            # Task Queue tools - autonomous task management
            if "task_queue" in enabled_ext_ids:
                try:
                    from ..tools.task_queue import TaskQueueTools
                    task_queue = TaskQueueTools(
                        planning_agent=self.planning_agent,
                        execution_agent=self.execution_agent
                    )
                    self.tool_registry.register_tool_class(task_queue)
                    logger.info("Registered Task Queue tools")
                except Exception as e:
                    logger.warning(f"Task Queue tools not available: {e}")
            
            # Model Chaining tools - sequential AI pipelines
            if "model_chaining" in enabled_ext_ids:
                try:
                    from ..tools.model_chaining import ModelChainingTools
                    model_chaining = ModelChainingTools(
                        execution_agent=self.execution_agent
                    )
                    self.tool_registry.register_tool_class(model_chaining)
                    logger.info("Registered Model Chaining tools")
                except Exception as e:
                    logger.warning(f"Model Chaining tools not available: {e}")
            
            # Promo Video tools - complete video ad creation
            if "replicate" in enabled_ext_ids:
                try:
                    from ..tools.promo_video import PromoVideoService
                    
                    # Get Printify tools if available
                    printify_tools = None
                    printify_key = self.config.get("printify_api_key") or self.config.get("printify_api_token")
                    printify_shop_id = self.config.get("printify_shop_id")
                    if printify_key and printify_shop_id:
                        printify_tools = PrintifyTools(
                            api_token=printify_key,
                            shop_id=str(printify_shop_id)
                        )
                    
                    promo_video = PromoVideoService(
                        replicate_api=replicate if replicate is not None else None,
                        anthropic_client=self.anthropic,
                        printify_tools=printify_tools
                    )
                    self.tool_registry.register_tool_class(promo_video)
                    logger.info("✓ Promo Video tools registered")
                except Exception as e:
                    logger.warning(f"Promo Video tools not available: {e}")
            
            # YouTube tools - video management
            if "youtube" in enabled_ext_ids:
                youtube_api_key = self.config.get("youtube_api_key")
                youtube_client_id = self.config.get("youtube_client_id")
                youtube_client_secret = self.config.get("youtube_client_secret")
                youtube_refresh_token = self.config.get("youtube_refresh_token")
                
                if youtube_api_key or (youtube_client_id and youtube_client_secret):
                    try:
                        from ..tools.youtube import YouTubeTools
                        youtube = YouTubeTools(
                            api_key=youtube_api_key,
                            client_id=youtube_client_id,
                            client_secret=youtube_client_secret,
                            refresh_token=youtube_refresh_token
                        )
                        self.tool_registry.register_tool_class(youtube)
                        logger.info(f"✓ YouTube tools registered (API: {bool(youtube_api_key)}, OAuth: {bool(youtube_client_id)})")
                    except Exception as e:
                        logger.error(f"Failed to initialize YouTube: {e}")
                else:
                    logger.warning("YouTube extension enabled but not configured (need API key or OAuth credentials)")
            
            # Email Marketing tools - send HTML emails via chat
            if "email" in enabled_ext_ids or "content_generation" in enabled_ext_ids:
                try:
                    from ..tools.email_marketing import get_email_tools
                    email_tools = get_email_tools()
                    self.tool_registry.register_tool_class(email_tools)
                    logger.info(f"✓ Email Marketing tools registered (provider: {email_tools.service.provider or 'none'})")
                except Exception as e:
                    logger.warning(f"Email tools not available: {e}")
            
            # Creative Platform tools - autonomous creative project management
            try:
                from ..tools.creative_platform import register_creative_platform_tools
                register_creative_platform_tools(self.tool_registry)
                logger.info("✓ Creative Platform tools registered")
            except Exception as e:
                logger.warning(f"Creative Platform tools not available: {e}")
            
            # Agent Delegation tools - intelligent task routing to specialized agents
            try:
                from ..tools.agent_delegation import get_agent_delegation_tools
                delegation_tools = get_agent_delegation_tools(
                    anthropic_client=self.anthropic,
                    tool_registry=self.tool_registry
                )
                self.tool_registry.register_tool_class(delegation_tools)
                logger.info("✓ Agent Delegation tools registered (17 specialized agents)")
            except Exception as e:
                logger.warning(f"Agent Delegation tools not available: {e}")
        
        except Exception as e:
            logger.error(f"Error registering tool classes: {e}", exc_info=True)
        
    async def process(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Process a user message and return a response.
        
        Args:
            message: User's input message
            context: Additional context (platform, user info, etc.)
            session_id: Session identifier for context tracking
            user_id: User identifier for profile context
            
        Returns:
            Dict containing response and metadata
        """
        try:
            # Create or retrieve session
            session = self._get_or_create_session(session_id, context)
            
            # Detect request type for intelligent routing
            request_type = self._detect_request_type(message)
            logger.info(f"Request analysis: {request_type}")
            
            # ==========================================
            # SLASH COMMAND PROCESSING (HIGHEST PRIORITY)
            # ==========================================
            if message.strip().startswith("/"):
                logger.info(f"⚡ Processing slash command: {message[:50]}...")
                slash_processor = get_slash_processor(orchestrator=self)
                
                if slash_processor.is_slash_command(message):
                    result = await slash_processor.execute(message)
                    
                    if result.get("success"):
                        response = result.get("message", "✅ Command executed")
                        
                        # Format based on result type
                        if result.get("type") == "file":
                            filename = result.get("filename", "file")
                            filepath = result.get("filepath", "")
                            content = result.get("content", "")
                            ext = result.get("file_type", "txt")
                            
                            response = f"✅ **Generated File:** `{filename}`\n\n"
                            if content and len(content) < 1500:
                                response += f"```{ext}\n{content}\n```\n\n"
                            elif content:
                                response += f"```{ext}\n{content[:1500]}...\n```\n\n"
                            if filepath:
                                response += f"📁 Saved to: `{filepath}`"
                        
                        elif result.get("type") == "help":
                            response = result.get("message", "")
                        
                        elif result.get("type") == "media":
                            media_type = result.get("media_type", "media")
                            response = f"✅ **Generated {media_type.title()}**\n\n"
                            response += result.get("message", "")
                            
                            # Add artifacts
                            artifacts = result.get("artifacts", [])
                            if artifacts:
                                response += self._format_artifacts_for_display(artifacts)
                        
                        elif result.get("type") == "chain":
                            steps_completed = result.get("steps_completed", 0)
                            steps_total = result.get("steps_total", 0)
                            response = f"✅ **Chain Completed:** {steps_completed}/{steps_total} steps\n\n"
                            
                            for step_result in result.get("results", []):
                                status = "✅" if step_result.get("success") else "❌"
                                cmd = step_result.get("command", "step")
                                response += f"{status} Step {step_result.get('step')}: /{cmd}\n"
                            
                            artifacts = result.get("artifacts", [])
                            if artifacts:
                                response += self._format_artifacts_for_display(artifacts)
                        
                        return {
                            "response": response,
                            "type": "slash_command",
                            "session_id": session["id"],
                            "artifacts": result.get("artifacts", [])
                        }
                    else:
                        return {
                            "response": f"❌ **Command failed:** {result.get('error', 'Unknown error')}",
                            "type": "error",
                            "session_id": session["id"]
                        }
            
            # Add to memory (flatten context for ChromaDB compatibility)
            flat_context = {}
            if context:
                for k, v in context.items():
                    if isinstance(v, (str, int, float, bool)) or v is None:
                        flat_context[k] = v
                    else:
                        flat_context[k] = str(v)[:500]  # Truncate complex values
            
            await self.memory_agent.store_message(
                session_id=session["id"],
                role="user",
                content=message,
                metadata=flat_context
            )
            
            # Get full context including user profile
            full_context = await self.memory_agent.get_full_context(
                session_id=session["id"],
                query=message,
                user_id=user_id
            )
            
            # Get CHRONOLOGICAL conversation history (not semantic search)
            # This is critical for understanding follow-up requests like "change the name"
            session_history = await self.memory_agent.get_session_history(
                session_id=session["id"],
                limit=15
            )
            
            # Convert to memories format with role info
            memories = [
                {
                    "content": msg.get("content", ""),
                    "role": msg.get("metadata", {}).get("role", "unknown"),
                    "metadata": msg.get("metadata", {})
                }
                for msg in session_history[-10:]  # Last 10 messages in order
            ]
            
            # Create planning prompt with context - limit tools to avoid token overflow
            all_tools = self.tool_registry.list_tools()
            # Only pass essential tool info
            limited_tools = [
                {"name": t["name"], "description": t.get("description", "")[:150], "category": t.get("category", "general")}
                for t in all_tools[:50]  # Limit to 50 most important tools
            ]
            
            # ==========================================
            # ENHANCED WORKFLOW ORCHESTRATOR (MODALITY → MODEL)
            # ==========================================
            # Use enhanced orchestrator for complex multi-modal requests
            if (self.enhanced_orchestrator and 
                request_type.get("is_action") and
                (any(kw in message.lower() for kw in ["create", "generate", "make", "design", "build", "workflow", "campaign"]) or
                 request_type.get("platform_context", {}).get("is_multi_step"))):
                
                logger.info("🚀 Using Enhanced Workflow Orchestrator (MODALITY → MODEL)")
                
                try:
                    workflow_result = await self.enhanced_orchestrator.execute_workflow(
                        user_request=message,
                        session_id=session["id"],
                        context={
                            "memories": memories[:5],
                            "user_id": user_id,
                            "request_type": request_type
                        }
                    )
                    
                    if workflow_result.success:
                        logger.info(f"✅ Enhanced workflow completed: quality={workflow_result.quality_score:.2f}")
                        
                        # Store result in memory
                        await self.memory_agent.store_message(
                            session_id=session["id"],
                            role="assistant",
                            content=str(workflow_result.final_output),
                            metadata={
                                "type": "enhanced_workflow",
                                "workflow_id": workflow_result.workflow_id,
                                "modalities": [m.modality.value for m in workflow_result.detected_modalities],
                                "quality_score": workflow_result.quality_score
                            }
                        )
                        
                        return {
                            "response": workflow_result.final_output,
                            "type": "enhanced_workflow",
                            "session_id": session["id"],
                            "workflow_id": workflow_result.workflow_id,
                            "modalities": [m.modality.value for m in workflow_result.detected_modalities],
                            "quality_score": workflow_result.quality_score,
                            "artifacts": []
                        }
                    else:
                        logger.warning(f"⚠️ Enhanced workflow failed, falling back to standard execution")
                
                except Exception as e:
                    logger.error(f"Enhanced workflow error: {e}, falling back to standard execution")
            
            # Extract platform intelligence context for enhanced planning
            platform_ctx = request_type.get("platform_context", {})
            
            planning_context = {
                "message": message,
                "memories": memories[:10],  # More memories for better context understanding
                "session": {"id": session["id"]},  # Only pass session ID
                "available_tools": limited_tools,
                "request_type": request_type,  # Action detection for intelligent routing
                # NEW: Platform intelligence context for smarter planning
                "platform_intelligence": {
                    "primary_intent": platform_ctx.get("primary_intent"),
                    "all_intents": platform_ctx.get("all_intents", []),
                    "confidence": platform_ctx.get("confidence", 0),
                    "workflow_template": platform_ctx.get("workflow_template"),
                    "recommended_model": platform_ctx.get("recommended_model"),
                    "model_category": platform_ctx.get("model_category"),
                    "creative_tool": platform_ctx.get("creative_tool"),
                    "agent_persona": platform_ctx.get("agent_persona"),
                    "is_multi_step": platform_ctx.get("is_multi_step", False)
                }
            }
            
            # Step 1: Planning - figure out what to do
            logger.info(f"Planning for: {message}")
            plan = await self.planning_agent.create_plan(planning_context)
            
            if not plan.get("steps"):
                # Simple response, no tools needed
                response = await self._generate_simple_response(message, memories)
                await self.memory_agent.store_message(
                    session_id=session["id"],
                    role="assistant",
                    content=response,
                    metadata={"type": "simple_response"}
                )
                return {
                    "response": response,
                    "type": "simple",
                    "session_id": session["id"]
                }
            
            # Step 2: Execution - run the tools
            logger.info(f"Executing {len(plan['steps'])} steps")
            execution_result = await self.execution_agent.execute_plan(
                plan=plan,
                tool_registry=self.tool_registry,
                context={"session": session, "memories": memories}
            )
            
            # Step 3: Generate final response based on results
            response = await self._generate_final_response(
                message=message,
                plan=plan,
                execution_result=execution_result,
                memories=memories
            )
            
            # Collect artifacts from execution
            artifacts = []
            if hasattr(self.execution_agent, 'get_artifacts'):
                artifacts = self.execution_agent.get_artifacts()
            
            # Append formatted artifact display to response
            if artifacts:
                artifact_display = self._format_artifacts_for_display(artifacts)
                response = response + artifact_display
            
            # Store response in memory (serialize complex objects for ChromaDB)
            import json
            await self.memory_agent.store_message(
                session_id=session["id"],
                role="assistant",
                content=response,
                metadata={
                    "type": "tool_response",
                    "plan_json": json.dumps(plan) if plan else None,
                    "num_steps": len(plan.get("steps", [])) if plan else 0,
                    "artifact_count": len(artifacts)
                }
            )
            
            return {
                "response": response,
                "type": "tool_execution",
                "session_id": session["id"],
                "plan": plan,
                "results": execution_result.get("results", []),
                "artifacts": artifacts
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return {
                "response": f"I encountered an error: {str(e)}. Please try again.",
                "type": "error",
                "session_id": session_id or "error_session"
            }
    
    async def process_voice(
        self,
        audio_data: bytes,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process voice input and return voice + text response.
        """
        try:
            from ..voice import transcribe_audio, synthesize_speech
            
            # Transcribe audio
            transcription = await transcribe_audio(
                audio_data,
                client=self.openai
            )
            
            # Process as text
            result = await self.process(
                message=transcription,
                context={**(context or {}), "input_type": "voice"},
                session_id=session_id
            )
            
            # Synthesize response
            audio_response = await synthesize_speech(
                text=result["response"],
                client=self.openai
            )
            
            return {
                **result,
                "transcription": transcription,
                "audio": audio_response
            }
            
        except Exception as e:
            logger.error(f"Voice processing error: {e}", exc_info=True)
            return {
                "response": "I had trouble processing your voice. Please try again.",
                "type": "error"
            }
    
    async def execute_workflow(
        self,
        workflow: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a predefined workflow.
        
        Args:
            workflow: List of workflow steps with tool names and parameters
            context: Additional context
        """
        results = []
        
        for step in workflow:
            tool_name = step.get("tool")
            parameters = step.get("parameters", {})
            
            # Execute tool
            result = await self.execution_agent.execute_tool(
                tool_name=tool_name,
                parameters=parameters,
                tool_registry=self.tool_registry,
                context=context or {}
            )
            
            results.append({
                "step": step.get("name", tool_name),
                "tool": tool_name,
                "result": result
            })
            
            # Check for errors
            if result.get("error"):
                if not step.get("continue_on_error", False):
                    break
        
        return {
            "success": all(r["result"].get("success", True) for r in results),
            "results": results
        }
    
    def _get_or_create_session(
        self,
        session_id: Optional[str],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get existing session or create new one."""
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
            session["last_activity"] = datetime.now()
            return session
        
        # Create new session
        new_id = session_id or str(uuid.uuid4())
        session = {
            "id": new_id,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "context": context or {},
            "turn_count": 0
        }
        self.sessions[new_id] = session
        return session
    
    async def _generate_simple_response(
        self,
        message: str,
        memories: List[Dict],
        agent_persona: Optional[Dict] = None
    ) -> str:
        """Generate a simple conversational response, optionally using agent persona."""
        # Build rich memory context including previous assistant responses
        memory_parts = []
        for m in memories:
            role = m.get('role', 'unknown')
            content = m.get('content', '')
            if content:
                prefix = '👤 User' if role == 'user' else '✦ Otto' if role == 'assistant' else role
                # Include more of assistant responses so follow-ups work
                max_len = 2000 if role == 'assistant' else 500
                memory_parts.append(f"{prefix}: {content[:max_len]}")
        memory_context = "\n".join(memory_parts) if memory_parts else "No previous context."
        
        # Check for agent persona from platform intelligence
        persona_context = ""
        if agent_persona:
            persona_name = agent_persona.get('name', 'Otto')
            persona_role = agent_persona.get('role', 'Assistant')
            persona_prompt = agent_persona.get('system_prompt', '')
            persona_context = f"""
=== AGENT PERSONA ===
You are {persona_name}, the {persona_role}.
{persona_prompt}
"""
        else:
            # Try to detect persona from message context
            platform_intel = get_platform_intelligence()
            detected_persona = platform_intel.match_agent_persona(message)
            if detected_persona:
                persona_name = detected_persona.get('name', 'Otto')
                persona_role = detected_persona.get('role', 'Assistant')
                persona_prompt = detected_persona.get('system_prompt', '')
                persona_context = f"""
=== AGENT PERSONA ===
You are {persona_name}, the {persona_role}.
{persona_prompt}
"""
        
        # Enhanced system prompt with platform capabilities
        platform_capabilities = """
=== PLATFORM CAPABILITIES ===
You have access to powerful capabilities inspired by leading platforms:

🎨 CREATIVE (Canva/Firefly-style):
- Image generation with multiple models (flux, sdxl, ideogram)
- Background removal, upscaling, style transfer
- Video generation and editing
- Audio/music generation

⚡ AUTOMATION (n8n/Zapier-style):
- Multi-step workflow automation
- Data sync between platforms
- Scheduled tasks and triggers
- Pre-built workflow templates

🌐 BROWSER (browser-use-style):
- AI-powered web scraping
- Form automation
- Data extraction
- Price monitoring

💬 SUPPORT (Quivr-style):
- Intelligent ticket routing
- Draft response composition
- Knowledge retrieval
- Sentiment analysis

🛒 E-COMMERCE:
- Product creation on Printify/Shopify
- Mockup generation
- Promo video creation
"""
        
        response = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": f"""You are Otto, a FULLY AUTONOMOUS AI assistant with the capabilities of the best AI platforms combined.
{persona_context}
{platform_capabilities}

=== CONVERSATION HISTORY ===
{memory_context}

=== CURRENT USER MESSAGE ===
{message}

=== INSTRUCTIONS ===

CRITICAL RULE: If the user is asking about results, asking to see something, or following up on previous work:
- Look at the CONVERSATION HISTORY above
- Find what was previously done/created/discussed
- PROVIDE THE ACTUAL DETAILS, DATA, RESULTS, LINKS, etc.
- NEVER just say "Done!" - that tells the user NOTHING

If repeating/summarizing previous results:
- Include specific names, URLs, prices, quantities, details
- Format nicely with bullets, links, etc.
- If the previous response was your own, expand on it with more detail

For new requests:
- Be decisive and action-oriented
- Make smart choices, use sensible defaults
- Never ask for confirmation or present options

IMPORTANT CAPABILITIES TO MENTION WHEN RELEVANT:
- For creative tasks: Mention you can generate images, videos, remove backgrounds, upscale, etc.
- For automation: Mention you can create workflows, sync data, schedule tasks
- For research: Mention you can scrape websites, extract data, monitor prices
- For support: Mention you can draft responses, analyze sentiment, route tickets

🚫 ABSOLUTELY FORBIDDEN RESPONSES:
- "Done!" by itself (provides no information)
- "Here you go!" without content
- Any response shorter than 2 sentences unless it's a simple factual answer
- Asking "Would you like me to...?" or "Should I...?"

Respond with SUBSTANCE. Every response must contain actual information, results, or actions."""
                }
            ]
        )
        
        return response.content[0].text
    
    async def _generate_final_response(
        self,
        message: str,
        plan: Dict[str, Any],
        execution_result: Dict[str, Any],
        memories: List[Dict]
    ) -> str:
        """Generate final response based on tool execution results."""
        # Build a clean, readable summary of what happened
        results_text = ""
        code_content = ""
        
        for result in execution_result.get("results", []):
            # Handle both structured results and raw results
            tool_name = result.get('tool', result.get('tool_name', 'unknown'))
            description = result.get('description', '')
            
            # Determine success
            is_success = (
                result.get('status') == 'success' or 
                result.get('success', False) or
                result.get('result', {}).get('success', False)
            )
            
            # Extract data from various nesting levels
            data = (
                result.get('data') or 
                result.get('result', {}).get('data') or 
                result.get('result', {}) or
                {}
            )
            
            results_text += f"\n--- Tool: {tool_name} ---\n"
            if description:
                results_text += f"Task: {description}\n"
            results_text += f"Status: {'✅ Success' if is_success else '❌ Failed'}\n"
            
            # Format data cleanly instead of raw dict dump
            if isinstance(data, dict):
                results_text += self._format_result_data(data, tool_name)
            elif data:
                data_str = str(data)[:2000]
                results_text += f"Result: {data_str}\n"
            
            # Extract errors
            error = (
                result.get('error') or 
                result.get('result', {}).get('error') or
                (data.get('error') if isinstance(data, dict) else None)
            )
            if error:
                results_text += f"Error: {str(error)[:500]}\n"
            
            # Special handling for create_file - extract code content
            if tool_name == 'create_file' and isinstance(data, dict) and data.get('content'):
                language = data.get('language', 'text')
                content = data.get('content', '')
                path = data.get('path', 'file')
                code_content += f"\n\n**File: {path}**\n```{language}\n{content}\n```\n"
        
        # Truncate total results if too large
        if len(results_text) > 12000:
            results_text = results_text[:12000] + "\n... (truncated)"
        
        # Add code content instruction if we have code to show
        code_instruction = ""
        if code_content:
            code_instruction = f"\n\nCODE CREATED (include in response with markdown code blocks):\n{code_content}"
        
        response = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": f"""You are Otto, an AI assistant that just completed work for the user.

User asked: {message}

=== EXECUTION RESULTS ===
{results_text}
{code_instruction}

=== INSTRUCTIONS ===

1. REPORT what you actually accomplished based on the results above
2. Include SPECIFIC details: product names, URLs, prices, file names, counts, etc.
3. If something failed, explain what happened and what you're doing about it
4. Format with markdown: links, bullets, bold for key info
5. For products: show → [Product Name](url) - $price
6. For images: mention they were generated and saved
7. For errors: explain briefly and mention any automatic retries

🚫 NEVER write just "Done!" — that tells the user NOTHING
🚫 NEVER ask follow-up questions like "Would you like me to..."
🚫 NEVER respond with less than 2 meaningful sentences

✅ Every response MUST include:
- What was created/done (with specifics)
- Key details (names, URLs, prices, counts)
- Status of any issues encountered

Write your response now:"""
                }
            ]
        )
        
        return response.content[0].text
    
    def _format_result_data(self, data: dict, tool_name: str) -> str:
        """Format tool result data into readable text for the response generator."""
        lines = []
        
        # Extract the most useful fields based on common patterns
        key_fields = [
            'title', 'name', 'product_id', 'product_url', 'url', 
            'price', 'product_type', 'variants_count', 'published',
            'shopify_status', 'success', 'message', 'note',
            'image_url', 'file_path', 'saved_path', 'output',
            'results', 'items', 'count', 'total',
            'content', 'summary', 'description',
            'error', 'error_type', 'hint', 'suggestion'
        ]
        
        for key in key_fields:
            if key in data and data[key] is not None:
                val = data[key]
                if isinstance(val, (list, dict)):
                    val_str = str(val)[:500]
                else:
                    val_str = str(val)[:300]
                lines.append(f"  {key}: {val_str}")
        
        # Also include any other keys not in the list (but limit size)
        remaining_keys = [k for k in data.keys() if k not in key_fields and not k.startswith('_')]
        for key in remaining_keys[:10]:
            val = data[key]
            if val is not None and str(val).strip():
                val_str = str(val)[:200]
                lines.append(f"  {key}: {val_str}")
        
        return "\n".join(lines) + "\n" if lines else "  (no data returned)\n"
    
    def _detect_request_type(self, message: str) -> Dict[str, Any]:
        """
        ENHANCED: Detect request type using Platform Intelligence.
        Integrates knowledge from n8n, Zapier, Quivr, Canva, Firefly, browser-use,
        Replicate, and other researched platforms.
        
        Returns:
            Dict with:
                - is_action: bool - True if user wants us to DO something
                - is_question: bool - True if asking a question
                - is_browser: bool - True if requires browser automation
                - action_type: str - Detected action category
                - keywords_found: List[str] - Which keywords matched
                - platform_context: Dict - Enhanced context from platform intelligence
        """
        msg_lower = message.lower()
        
        # ========================================
        # PLATFORM INTELLIGENCE ENHANCED DETECTION
        # ========================================
        platform_intel = get_platform_intelligence()
        platform_context = platform_intel.get_task_context(message)
        
        # Get primary intent from enhanced detection
        primary_intent = platform_context.get("primary_intent", "")
        intents = platform_context.get("intents", [])
        
        # Check for action keywords (legacy + enhanced)
        action_matches = [kw for kw in ACTION_KEYWORDS if kw in msg_lower]
        is_action = len(action_matches) > 0 or primary_intent not in ["", "question_answering", "conversation"]
        
        # Check for question patterns
        is_question = any(pattern in msg_lower for pattern in QUESTION_PATTERNS)
        
        # ========================================
        # ENHANCED BROWSER VS DEEP RESEARCH DETECTION
        # ========================================
        
        # Check for EXPLICIT browser-required patterns
        browser_required_matches = [kw for kw in BROWSER_REQUIRED_PATTERNS if kw in msg_lower]
        
        # Check for deep research patterns (can be done via AI + search APIs)
        deep_research_matches = [kw for kw in DEEP_RESEARCH_KEYWORDS if kw in msg_lower]
        
        # Check for ambiguous patterns that need context
        ambiguous_matches = [kw for kw in AMBIGUOUS_WEB_PATTERNS if kw in msg_lower]
        
        # Determine if browser is truly required
        browser_intents = ["web_scraping", "form_automation", "browser_navigation", "screenshot_analysis"]
        
        # Browser is required if:
        # 1. Explicit browser-required pattern found AND no strong deep research signal, OR
        # 2. Platform intent is clearly browser-related
        has_browser_pattern = len(browser_required_matches) > 0
        has_deep_research_pattern = len(deep_research_matches) > 0
        browser_intent_detected = primary_intent in browser_intents
        
        # Smart disambiguation: 
        # - If BOTH browser and research patterns found, prefer research (cheaper/faster)
        # - If only ambiguous patterns, check if URL or specific site mentioned
        has_specific_url = any(x in msg_lower for x in ['http://', 'https://', '.com', '.org', '.net', '.io', 'www.'])
        has_specific_site_action = any(x in msg_lower for x in ['on amazon', 'on ebay', 'on twitter', 'on facebook', 'on linkedin', 'on the website'])
        
        # Decision logic for browser use
        if has_browser_pattern and not has_deep_research_pattern:
            # Clear browser task
            is_browser = True
            research_method = "browser_automation"
        elif has_deep_research_pattern and not has_browser_pattern:
            # Clear research task
            is_browser = False
            research_method = "deep_research"
        elif has_browser_pattern and has_deep_research_pattern:
            # Both patterns - favor deep research unless specific site action
            is_browser = has_specific_site_action or has_specific_url
            research_method = "browser_automation" if is_browser else "deep_research"
        elif len(ambiguous_matches) > 0:
            # Ambiguous - use URL/site presence as tiebreaker
            is_browser = has_specific_url or has_specific_site_action
            research_method = "browser_automation" if is_browser else "web_search_api"
        elif browser_intent_detected:
            is_browser = True
            research_method = "browser_automation"
        else:
            # Default: favor deep research (cheaper/faster)
            is_browser = False
            research_method = "ai_reasoning"
        
        # ========================================
        # ENHANCED ACTION TYPE DETECTION
        # Uses platform intelligence for richer categorization
        # ========================================
        action_type = "general"
        
        # Map platform intelligence intents to action types
        intent_to_action = {
            "image_generation": "image_generation",
            "image_editing": "image_editing",
            "background_removal": "image_editing",
            "upscaling": "image_editing",
            "style_transfer": "image_editing",
            "video_generation": "video_generation",
            "video_editing": "video_editing",
            "audio_generation": "audio_generation",
            "design_creation": "design_creation",
            "content_writing": "content_creation",
            "copywriting": "content_creation",
            "social_media": "social_media",
            "email_marketing": "email_marketing",
            "product_creation": "product_creation",
            "inventory_management": "ecommerce",
            "order_processing": "ecommerce",
            "pricing_optimization": "ecommerce",
            "workflow_automation": "workflow",
            "data_sync": "workflow",
            "trigger_action": "workflow",
            "scheduled_task": "workflow",
            "multi_step_workflow": "workflow",
            "web_scraping": "browser_automation",
            "form_automation": "browser_automation",
            "browser_navigation": "browser_automation",
            "data_extraction": "browser_automation",
            "ticket_handling": "support",
            "customer_support": "support",
            "draft_response": "support",
            "knowledge_retrieval": "support",
            "sentiment_analysis": "analysis",
            "market_research": "research",
            "competitor_analysis": "research",
            "trend_analysis": "research",
            "data_analysis": "analysis",
            "code_generation": "code",
            "code_review": "code",
            "debugging": "code",
            "api_integration": "code",
        }
        
        if primary_intent and primary_intent in intent_to_action:
            action_type = intent_to_action[primary_intent]
        elif any(kw in action_matches for kw in ["create", "generate", "make", "design", "build"]):
            # Fallback to legacy detection
            if any(kw in action_matches for kw in ["image", "picture", "artwork", "graphic", "logo"]):
                action_type = "image_generation"
            elif any(kw in action_matches for kw in ["video", "commercial", "ad", "animate"]):
                action_type = "video_generation"
            elif any(kw in action_matches for kw in ["music", "audio", "song"]):
                action_type = "audio_generation"
            elif any(kw in action_matches for kw in ["product", "mockup", "t-shirt", "hoodie", "mug"]):
                action_type = "product_creation"
            elif any(kw in action_matches for kw in ["blog", "post", "content", "copy", "script", "write"]):
                action_type = "content_creation"
            else:
                action_type = "creation"
        elif any(kw in action_matches for kw in ["sync", "upload", "publish", "launch"]):
            action_type = "publishing"
        elif any(kw in action_matches for kw in ["campaign", "workflow"]):
            action_type = "workflow"
        
        # ========================================
        # ENHANCED RESULT WITH PLATFORM CONTEXT
        # ========================================
        return {
            "is_action": is_action and not is_question,
            "is_question": is_question,
            "is_browser": is_browser,
            "action_type": action_type,
            "keywords_found": action_matches + browser_required_matches,
            # NEW: Research method determination
            "research_method": research_method,  # browser_automation, deep_research, web_search_api, ai_reasoning
            "can_use_deep_research": not is_browser and len(deep_research_matches) > 0,
            "browser_required_patterns": browser_required_matches,
            "deep_research_patterns": deep_research_matches,
            # Platform intelligence context
            "platform_context": {
                "primary_intent": primary_intent,
                "all_intents": intents,
                "confidence": platform_context.get("confidence", 0),
                "workflow_template": platform_context.get("workflow"),
                "recommended_model": platform_context.get("recommended_model"),
                "model_category": platform_context.get("model_category"),
                "creative_tool": platform_context.get("creative_tool"),
                "agent_persona": platform_context.get("agent_persona"),
                "is_multi_step": platform_context.get("is_multi_step", False)
            }
        }
    
    def _format_artifacts_for_display(self, artifacts: List[Dict]) -> str:
        """
        Format artifacts list for nice display in chat response.
        Based on chat_assistant.py artifact display patterns.
        """
        if not artifacts:
            return ""
        
        lines = ["\n\n---\n**Generated Assets:**\n"]
        
        # Count by type for summary
        type_counts = {}
        
        for artifact in artifacts:
            art_type = artifact.get("type", "file")
            config = ARTIFACT_DISPLAY_CONFIG.get(art_type, {"emoji": "📁", "verb": "Created"})
            
            type_counts[art_type] = type_counts.get(art_type, 0) + 1
            count_label = f" {type_counts[art_type]}" if type_counts[art_type] > 1 else ""
            
            emoji = config["emoji"]
            
            # Format based on artifact type
            if art_type == "image":
                url = artifact.get("url", "")
                path = artifact.get("filepath", artifact.get("path", ""))
                lines.append(f"{emoji} **Image{count_label}:** {url}")
                if path:
                    lines.append(f"   📁 Saved: `{path}`")
            
            elif art_type == "video":
                url = artifact.get("url", "")
                path = artifact.get("filepath", artifact.get("path", ""))
                lines.append(f"{emoji} **Video{count_label}:** {url}")
                if path:
                    lines.append(f"   📁 Saved: `{path}`")
            
            elif art_type == "audio":
                url = artifact.get("url", "")
                path = artifact.get("filepath", artifact.get("path", ""))
                lines.append(f"{emoji} **Audio{count_label}:** {url}")
                if path:
                    lines.append(f"   📁 Saved: `{path}`")
            
            elif art_type == "product":
                title = artifact.get("title", artifact.get("name", "Product"))
                url = artifact.get("url", artifact.get("product_url", ""))
                price = artifact.get("price", "")
                lines.append(f"{emoji} **{title}**")
                if url:
                    lines.append(f"   🔗 [{url}]({url})")
                if price:
                    lines.append(f"   💰 {price}")
            
            elif art_type == "code" or art_type == "file":
                path = artifact.get("filepath", artifact.get("path", "file"))
                content = artifact.get("content", "")
                lines.append(f"{emoji} **File:** `{path}`")
                if content and len(content) < 500:
                    lang = artifact.get("language", "")
                    lines.append(f"```{lang}\n{content}\n```")
            
            else:
                # Generic artifact
                url = artifact.get("url", "")
                path = artifact.get("filepath", artifact.get("path", ""))
                lines.append(f"📁 **{art_type.title()}:** {url or path}")
        
        return "\n".join(lines)

    def get_capabilities(self) -> Dict[str, Any]:
        """Get Otto's current capabilities."""
        tools = self.tool_registry.list_tools()
        categories = self.tool_registry.get_categories()
        
        return {
            "name": "Otto Universal",
            "version": "1.0.0",
            "tools_count": len(tools),
            "categories": categories,
            "tools_by_category": {
                cat: [t for t in tools if t.get("category") == cat]
                for cat in categories
            },
            "features": [
                "Natural language processing",
                "Multi-step task planning",
                "Tool execution",
                "Voice interaction",
                "Memory and context",
                "File storage",
                "Settings management"
            ]
        }

    async def process_streaming(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        local_mode: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a message with real-time streaming responses.
        
        Yields chunks: thinking, tool_start, tool_end, text, artifact, complete, error
        
        Args:
            message: User's input message
            context: Additional context dictionary
            session_id: Session identifier for conversation tracking
            local_mode: If True, use only locally installed models (no Replicate/cloud APIs)
        """
        execution_start_time = datetime.now()
        try:
            # Store local_mode in context for tool execution
            if context is None:
                context = {}
            context["local_mode"] = local_mode
            
            if local_mode:
                yield {"type": "status", "message": "🖥️ Local Mode Active - Using local models only", "icon": "🖥️", "state": "info"}
            
            yield {"type": "thinking", "content": "Analyzing your request...", "metadata": {"step": "initialization"}}
            yield {"type": "status", "message": "Analyzing your request...", "icon": "🔍", "state": "generating"}
            
            session = self._get_or_create_session(session_id, context)
            user_id = context.get("user_id", "default") if context else "default"
            
            # INTELLIGENCE: Extract entities from user message
            try:
                await self.intelligence.extract_entities(message, user_id)
            except Exception as e:
                logger.debug(f"Entity extraction skipped: {e}")
            
            # INTELLIGENCE: Get enhanced context from past learnings
            enhanced_context = ""
            try:
                enhanced_context = self.intelligence.get_enhanced_context(message, user_id)
            except Exception as e:
                logger.debug(f"Enhanced context skipped: {e}")
            
            # Get CHRONOLOGICAL history for follow-up understanding
            session_history = await self.memory_agent.get_session_history(
                session_id=session["id"],
                limit=15
            )
            memories = [
                {
                    "content": msg.get("content", ""),
                    "role": msg.get("metadata", {}).get("role", "unknown"),
                    "metadata": msg.get("metadata", {})
                }
                for msg in session_history[-10:]
            ]
            
            yield {"type": "thinking", "content": "Creating execution plan...", "metadata": {"step": "planning"}}
            yield {"type": "status", "message": "Planning approach...", "icon": "📋", "state": "generating"}
            
            available_tools = self.tool_registry.list_tools()
            limited_tools = [{"name": t["name"], "description": t["description"], "category": t.get("category", "general")} for t in available_tools[:50]]
            
            # INTELLIGENCE: Add task suggestions from past learnings
            task_suggestions = self.intelligence.get_task_suggestions(message)
            
            planning_context = {
                "message": message,
                "memories": memories[:10],  # More memories for better context
                "session": {"id": session["id"]},
                "available_tools": limited_tools,
                "enhanced_context": enhanced_context,  # Intelligence-enhanced context
                "task_suggestions": task_suggestions  # Learnings from past executions
            }
            
            plan = await self.planning_agent.create_plan(planning_context)
            
            if not plan.get("steps"):
                yield {"type": "thinking", "content": "Formulating response...", "metadata": {"step": "generation"}}
                yield {"type": "status", "message": "Generating response...", "icon": "💭", "state": "generating"}
                response = await self._generate_simple_response(message, memories)
                
                # Stream word-by-word for REAL-TIME display like ChatGPT
                words = response.split(' ')
                for word_idx, word in enumerate(words):
                    # Add space before word (except first)
                    if word_idx > 0:
                        word = ' ' + word
                    yield {"type": "text", "content": word, "metadata": {"progress": (word_idx+1)/len(words)}}
                    # Small delay for smooth streaming (10ms per word)
                    await asyncio.sleep(0.01)
                
                await self.memory_agent.store_message(session_id=session["id"], role="assistant", content=response, metadata={"type": "simple_response"})
                yield {"type": "complete", "session_id": session["id"]}
                return
            
            # Tool execution
            steps = plan.get("steps", [])
            yield {"type": "thinking", "content": f"Executing {len(steps)} steps...", "metadata": {"step": "execution", "total_steps": len(steps)}}
            yield {"type": "status", "message": f"Running {len(steps)} step{'s' if len(steps) != 1 else ''}...", "icon": "⚡", "state": "generating"}
            
            step_outputs = {}
            artifacts = []
            background_tasks = []
            
            for idx, step in enumerate(steps):
                step_name = step.get("description", step.get("tool", "Unknown"))
                tool_name = step.get("tool", "")
                progress_pct = int((idx / len(steps)) * 100)
                yield {"type": "tool_start", "content": step_name, "metadata": {"step_index": idx+1, "total_steps": len(steps), "tool": tool_name}}
                # Also emit as tool_use + status for frontend compatibility
                yield {"type": "tool_use", "tool": tool_name, "name": tool_name, "content": step_name}
                yield {"type": "status", "message": f"Step {idx+1}/{len(steps)}: {step_name}", "icon": "🔄", "state": "generating", "progress": progress_pct}
                
                try:
                    # Check for local mode restriction
                    is_local_mode = context.get("local_mode", False)
                    tool_name = step.get("tool")
                    
                    # Block Replicate/cloud tools if local mode is active
                    if is_local_mode and tool_name:
                        # List of cloud/Replicate tools that require internet
                        cloud_tools = [
                            "replicate_run_model", "replicate_smart_generate", "replicate_get_model_info",
                            "replicate_search_models", "replicate_list_collections", "replicate_get_collection",
                            "replicate_create_product_design", "replicate_create_video", "replicate_generate_music",
                            "universal_edit"  # Uses Replicate internally
                        ]
                        
                        if any(cloud_tool in tool_name for cloud_tool in cloud_tools):
                            yield {
                                "type": "error",
                                "content": f"⚠️ Local Mode: Cannot use cloud tool '{tool_name}'. Please disable Local Mode or download the required model to use it locally.",
                                "metadata": {"tool": tool_name, "reason": "local_mode_restriction"}
                            }
                            yield {"type": "tool_end", "content": "Skipped (Local Mode)", "metadata": {"step_index": idx+1, "status": "skipped"}}
                            continue
                    
                    # Inject dependency data from previous steps
                    step_data = step.copy()
                    step_data["dependency_data"] = step_outputs
                    
                    result = await self.execution_agent.execute_tool(
                        tool_name=tool_name,
                        parameters=step.get("parameters", {}),
                        tool_registry=self.tool_registry,
                        context={"session": session, "memories": memories, "local_mode": is_local_mode},
                        step_data=step_data
                    )
                    
                    # Store result with step_X key for template resolution
                    step_outputs[f"step_{idx}"] = result
                    
                    # CALENDAR INTEGRATION: If this was a queue_task call, emit schedule_add event
                    # so tasks go to the calendar/schedule instead of immediate queue
                    if tool_name in ("queue_task",) and result.get("success"):
                        queue_data = result.get("data", result)
                        yield {
                            "type": "schedule_add",
                            "task": {
                                "id": queue_data.get("task_id", f"task_{datetime.now().timestamp()}"),
                                "title": step.get("parameters", {}).get("description", step_name)[:80],
                                "instruction": step.get("parameters", {}).get("description", step_name),
                                "type": "general",
                                "status": "scheduled",
                                "priority": step.get("parameters", {}).get("priority", "normal"),
                                "scheduledDate": step.get("parameters", {}).get("schedule_for") or datetime.now().isoformat(),
                            }
                        }
                    
                    # Check if this created a background task
                    if result.get("background_task_id"):
                        task_info = {
                            "task_id": result["background_task_id"],
                            "task_name": result.get("task_name", step_name)
                        }
                        background_tasks.append(task_info)
                        yield {"type": "background_task", "task_id": task_info["task_id"], "task_name": task_info["task_name"], "metadata": {"step": idx+1}}
                    
                    # Extract media (images, videos, audio) from result
                    if result.get("success") and result.get("data"):
                        data = result["data"]
                        media_found = []  # List of (url, media_type) tuples
                        if isinstance(data, dict):
                            # --- VIDEO detection ---
                            if "video_url" in data:
                                media_found.append((data["video_url"], "video"))
                            if "video_path" in data:
                                media_found.append((data["video_path"], "video"))
                            # --- AUDIO detection ---
                            if "audio_url" in data:
                                media_found.append((data["audio_url"], "audio"))
                            if "audio_path" in data:
                                media_found.append((data["audio_path"], "audio"))
                            # --- IMAGE detection ---
                            if "images" in data:
                                img_data = data["images"]
                                if isinstance(img_data, list):
                                    media_found.extend((u, "image") for u in img_data)
                                elif isinstance(img_data, str):
                                    media_found.append((img_data, "image"))
                            if "image_url" in data:
                                media_found.append((data["image_url"], "image"))
                            if "url" in data and not any(data["url"] == m[0] for m in media_found):
                                media_found.append((data["url"], "image"))
                            if "image" in data and isinstance(data["image"], str):
                                media_found.append((data["image"], "image"))
                            if "output" in data:
                                output = data["output"]
                                if isinstance(output, list):
                                    for item in output:
                                        if isinstance(item, str) and (item.startswith("http") or item.startswith("/")):
                                            media_found.append((item, "image"))
                                elif isinstance(output, str) and (output.startswith("http") or output.startswith("/")):
                                    media_found.append((output, "image"))
                            if "file_path" in data:
                                media_found.append((data["file_path"], "image"))
                            if "saved_path" in data:
                                media_found.append((data["saved_path"], "image"))
                        
                        # Deduplicate and process
                        seen = set()
                        for media_url, media_type in media_found:
                            if media_url and media_url not in seen:
                                seen.add(media_url)
                                
                                # Detect type from URL extension if not already video/audio
                                url_lower = media_url.lower()
                                if any(ext in url_lower for ext in [".mp4", ".webm", ".mov", ".avi"]):
                                    media_type = "video"
                                elif any(ext in url_lower for ext in [".mp3", ".wav", ".ogg", ".flac"]):
                                    media_type = "audio"
                                
                                # AUTO-SAVE remote media to local storage
                                if media_url.startswith("http") and self.file_storage:
                                    try:
                                        import os
                                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                        # Use correct extension based on media type
                                        if media_type == "video":
                                            ext = ".mp4" if ".mp4" in url_lower else ".webm" if ".webm" in url_lower else ".mp4"
                                            category = "videos"
                                        elif media_type == "audio":
                                            ext = ".mp3" if ".mp3" in url_lower else ".wav" if ".wav" in url_lower else ".mp3"
                                            category = "audio"
                                        else:
                                            ext = ".png" if ".png" in url_lower else ".webp" if ".webp" in url_lower else ".jpg"
                                            category = "images"
                                        save_filename = f"generated_{timestamp}_{len(artifacts)}{ext}"
                                        
                                        metadata = await self.file_storage.store_from_url(
                                            url=media_url,
                                            filename=save_filename,
                                            category=category,
                                            tags=["generated", step.get("tool", media_type)]
                                        )
                                        
                                        media_url = metadata.url
                                        logger.info(f"Auto-saved {media_type} to local storage: {media_url}")
                                    except Exception as save_error:
                                        logger.warning(f"Failed to auto-save {media_type}: {save_error}")
                                
                                # Convert local paths to URLs
                                elif media_url.startswith("/Users/") or media_url.startswith("./data/"):
                                    import os
                                    filename = os.path.basename(media_url)
                                    media_url = f"/files/{filename}"
                                
                                artifact = {
                                    "type": media_type, 
                                    "url": media_url,
                                    "name": f"{media_type.title()} from {step.get('tool', 'generation')}"
                                }
                                artifacts.append(artifact)
                                yield {"type": "artifact", "artifact": artifact, "metadata": {"step": idx+1}}
                    
                    step_done_pct = int(((idx + 1) / len(steps)) * 100)
                    yield {"type": "tool_end", "content": step_name, "metadata": {"step_index": idx+1, "success": result.get("success", True)}}
                    # Also emit as tool_result + status for frontend compatibility
                    yield {"type": "tool_result", "tool": tool_name, "result": result.get("data") if result.get("success") else None, "success": result.get("success", True)}
                    yield {"type": "status", "message": f"Step {idx+1}/{len(steps)} complete ✓", "icon": "✅", "state": "success", "progress": step_done_pct}
                    
                except Exception as e:
                    logger.error(f"Step {idx+1} failed: {e}")
                    yield {"type": "tool_end", "content": step_name, "metadata": {"step_index": idx+1, "success": False, "error": str(e)}}
                    yield {"type": "status", "message": f"Step {idx+1} encountered an issue, continuing...", "icon": "⚠️", "state": "error"}
            
            # Final response
            yield {"type": "thinking", "content": "Synthesizing results...", "metadata": {"step": "synthesis"}}
            yield {"type": "status", "message": "Preparing response...", "icon": "✨", "state": "generating", "progress": 95}
            
            execution_result = {"status": "success", "results": [
                {
                    "step": idx,
                    "tool": steps[idx].get("tool", "unknown"),
                    "description": steps[idx].get("description", ""),
                    "status": "success" if v.get("success") else "failed",
                    "result": v,
                    "data": v.get("data", v)
                }
                for idx, v in enumerate(step_outputs.values())
            ], "artifacts": artifacts}
            response = await self._generate_final_response(message=message, plan=plan, execution_result=execution_result, memories=memories)
            
            # Stream word-by-word for REAL-TIME display like ChatGPT/Claude
            words = response.split(' ')
            for word_idx, word in enumerate(words):
                # Add space before word (except first)
                if word_idx > 0:
                    word = ' ' + word
                yield {"type": "text", "content": word, "metadata": {"progress": (word_idx+1)/len(words)}}
                # Small delay for smooth streaming (10ms per word)
                await asyncio.sleep(0.01)
            
            # Store message with simplified metadata (ChromaDB doesn't accept nested dicts)
            await self.memory_agent.store_message(
                session_id=session["id"], 
                role="assistant", 
                content=response, 
                metadata={
                    "type": "tool_execution",
                    "tools_count": len(steps),
                    "has_artifacts": len(artifacts) > 0
                }
            )
            
            # INTELLIGENCE: Self-reflection on execution
            try:
                execution_duration = (datetime.now() - execution_start_time).total_seconds()
                step_results = [
                    {
                        "tool": step_outputs.get(f"step_{i}", {}).get("tool", steps[i].get("tool") if i < len(steps) else "unknown"),
                        "status": "success" if step_outputs.get(f"step_{i}", {}).get("success") else "failed",
                        "result": step_outputs.get(f"step_{i}", {})
                    }
                    for i in range(len(steps))
                ]
                await self.intelligence.reflect_on_execution(
                    request=message,
                    plan=plan,
                    results=step_results,
                    duration=execution_duration
                )
                
                # Index successful outputs for future reference
                for i, step in enumerate(steps):
                    step_result = step_outputs.get(f"step_{i}", {})
                    if step_result.get("success") and step_result.get("data"):
                        try:
                            self.intelligence.index_output(
                                tool_name=step.get("tool", "unknown"),
                                output=step_result.get("data"),
                                prompt=str(step.get("parameters", {}).get("prompt", step.get("parameters", {}).get("description", "")))
                            )
                        except Exception as idx_e:
                            logger.debug(f"Output indexing skipped: {idx_e}")
            except Exception as reflect_e:
                logger.debug(f"Self-reflection skipped: {reflect_e}")
            
            yield {"type": "complete", "session_id": session["id"], "artifacts": artifacts}
            
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield {"type": "error", "content": str(e), "metadata": {"error_type": type(e).__name__}}
