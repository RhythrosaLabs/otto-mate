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

logger = logging.getLogger(__name__)


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
            from ..tools.replicate_universal import ReplicateUniversal
            from ..tools.code_execution import CodeExecutionTools, DataProcessingTools
            from ..storage import FileStorage, StorageConfig
            
            enabled_extensions = self.extension_registry.get_enabled_extensions()
            enabled_ext_ids = [ext.id for ext in enabled_extensions]
            
            logger.info(f"Loading {len(enabled_extensions)} enabled extensions...")
            
            # === CORE AUTONOMOUS TOOLS ===
            
            # Universal Replicate - access to ANY AI model
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
                    anthropic_client=self.anthropic
                )
                self.tool_registry.register_tool_class(content)
                logger.info("Registered Content tools")
            
            # Browser tools (optional)
            if "browser" in enabled_ext_ids:
                try:
                    browser = BrowserTools()
                    self.tool_registry.register_tool_class(browser)
                    logger.info("Registered Browser tools")
                except Exception as e:
                    logger.warning(f"Browser tools not available: {e}")
            
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
                        replicate_api=replicate if 'replicate' in dir() else None,
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
            
            planning_context = {
                "message": message,
                "memories": memories[:10],  # More memories for better context understanding
                "session": {"id": session["id"]},  # Only pass session ID
                "available_tools": limited_tools
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
                tool_registry=self.tool_registry
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
        memories: List[Dict]
    ) -> str:
        """Generate a simple conversational response."""
        memory_context = "\n".join([
            f"- {m.get('content', '')}"
            for m in memories
        ]) if memories else "No previous context."
        
        response = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"""You are Otto, a FULLY AUTONOMOUS AI assistant. You take initiative and get things done.
                    
Previous context:
{memory_context}

User message: {message}

🚫 ABSOLUTELY FORBIDDEN:
- NEVER ask "Should I...?", "Would you like me to...?", "Which do you prefer?"
- NEVER ask for confirmation, permission, or clarification
- NEVER present options and ask user to choose
- NEVER say "I can do A, B, or C" - just pick the best one and do it
- NEVER say "Let me know if..." or "Would you like..." or "Do you want..."

✅ MANDATORY BEHAVIOR:
- BE DECISIVE: Make smart choices and state what you're doing
- BE ACTION-ORIENTED: "Creating...", "Done!", "Here's what I made..."
- BE AUTONOMOUS: If something seems like a good idea, just do it
- USE DEFAULTS: When parameters aren't specified, use sensible defaults
- ANTICIPATE NEEDS: If they ask for X, also do related things Y and Z that help
- BE CONFIDENT: "I made..." not "I could make..."

💡 AUTONOMY EXAMPLES:
- User: "make something cool" → Just create something creative, don't ask what
- User: "I need a logo" → Generate a logo with smart defaults, don't ask about colors
- User: "help me with my store" → Analyze their store and give recommendations, don't ask what kind of help

Respond naturally. Be the assistant that gets things done without hand-holding."""
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
        # Format results for the prompt with size limits
        results_text = ""
        code_content = ""  # Track code content separately to ensure it's displayed
        
        for result in execution_result.get("results", []):
            tool_name = result.get('tool', 'unknown')
            results_text += f"\nTool: {tool_name}\n"
            # Check both 'status' field and nested 'result.success' for success determination
            is_success = result.get('status') == 'success' or result.get('result', {}).get('success', False)
            results_text += f"Status: {'Success' if is_success else 'Failed'}\n"
            
            # Extract data from nested result structure if present
            data = result.get('data') or result.get('result', {}).get('data') or result.get('result', {})
            
            # Special handling for create_file - extract code content for display
            if tool_name == 'create_file' and isinstance(data, dict):
                if data.get('content'):
                    language = data.get('language', 'text')
                    content = data.get('content', '')
                    path = data.get('path', 'file')
                    code_content += f"\n\n**File: {path}**\n```{language}\n{content}\n```\n"
                    results_text += f"Path: {data.get('path')}\n"
                    results_text += f"Size: {data.get('size')} bytes\n"
                    results_text += f"Language: {language}\n"
                    results_text += "Content: [Code content will be displayed in response]\n"
                else:
                    data_str = str(data)[:2000]
                    results_text += f"Data: {data_str}\n"
            elif data:
                data_str = str(data)[:2000]  # Limit data size
                results_text += f"Data: {data_str}\n"
                
            error = result.get('error') or result.get('result', {}).get('error')
            if error:
                error_str = str(error)[:500]  # Limit error size
                results_text += f"Error: {error_str}\n"
        
        # Truncate total results if too large
        if len(results_text) > 10000:
            results_text = results_text[:10000] + "\n... (truncated)"
        
        # Add code content instruction if we have code to show
        code_instruction = ""
        if code_content:
            code_instruction = f"""

IMPORTANT: Code was created. You MUST include the code in your response using markdown code blocks.
Here is the code to include:
{code_content}

ALWAYS show the full code in a properly formatted code block."""
        
        response = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,  # Increased for code content
            messages=[
                {
                    "role": "user",
                    "content": f"""You are Otto, a FULLY AUTONOMOUS AI agent that just completed work.

User asked: {message}

What was done:
{results_text}
{code_instruction}

🎯 YOUR JOB - BE AUTONOMOUS:
- Report what you DID, never what you "could" or "will" do
- Be direct, confident, and clear
- Show URLs as markdown links: [Product](url)
- If code was created, show the FULL code in markdown code blocks
- Background tasks: Say "Handling that now" not "Should I retry?"
- NEVER ask follow-up questions like "Would you like me to..." or "Should I also..."

🚫 FORBIDDEN PHRASES:
- "Would you like me to..."
- "Should I also..."
- "Let me know if..."
- "Do you want me to..."
- "I could also..."
- "Options: A, B, or C"

✅ GOOD PHRASES:
- "Done! Here's what I created..."
- "Created your..."
- "Working on additional improvements..."
- "Also optimized..."
- "Next, I'm handling..."

📝 FORMAT:
✓ Completed: [what was done]
→ Link: [Product Name](url)
⏳ Processing: [background task] (completing automatically)

🎁 PROACTIVE BEHAVIOR:
If the task naturally leads to additional helpful actions, mention that you're doing them:
- Created a t-shirt design? → "Also setting up matching mug and hoodie variants..."
- Wrote code? → "Added documentation and error handling..."
- Made a logo? → "Creating social media sized versions..."

Write your response - be confident and action-oriented:"""
                }
            ]
        )
        
        return response.content[0].text
    
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
        session_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a message with real-time streaming responses.
        
        Yields chunks: thinking, tool_start, tool_end, text, artifact, complete, error
        """
        execution_start_time = datetime.now()
        try:
            yield {"type": "thinking", "content": "Analyzing your request...", "metadata": {"step": "initialization"}}
            
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
            
            step_outputs = {}
            artifacts = []
            background_tasks = []
            
            for idx, step in enumerate(steps):
                step_name = step.get("description", step.get("tool", "Unknown"))
                yield {"type": "tool_start", "content": step_name, "metadata": {"step_index": idx+1, "total_steps": len(steps), "tool": step.get("tool")}}
                
                try:
                    # Inject dependency data from previous steps
                    step_data = step.copy()
                    step_data["dependency_data"] = step_outputs
                    
                    result = await self.execution_agent.execute_tool(
                        tool_name=step.get("tool"),
                        parameters=step.get("parameters", {}),
                        tool_registry=self.tool_registry,
                        context={"session": session, "memories": memories},
                        step_data=step_data
                    )
                    
                    # Store result with step_X key for template resolution
                    step_outputs[f"step_{idx}"] = result
                    
                    # Check if this created a background task
                    if result.get("background_task_id"):
                        task_info = {
                            "task_id": result["background_task_id"],
                            "task_name": result.get("task_name", step_name)
                        }
                        background_tasks.append(task_info)
                        yield {"type": "background_task", "task_id": task_info["task_id"], "task_name": task_info["task_name"], "metadata": {"step": idx+1}}
                    
                    # Extract images from result
                    if result.get("success") and result.get("data"):
                        data = result["data"]
                        # Check various places where images might be
                        images_found = []
                        if isinstance(data, dict):
                            # Check all common image output formats
                            if "images" in data:
                                img_data = data["images"]
                                if isinstance(img_data, list):
                                    images_found.extend(img_data)
                                elif isinstance(img_data, str):
                                    images_found.append(img_data)
                            if "image_url" in data:
                                images_found.append(data["image_url"])
                            if "url" in data:
                                images_found.append(data["url"])
                            if "image" in data and isinstance(data["image"], str):
                                images_found.append(data["image"])
                            if "output" in data:
                                output = data["output"]
                                if isinstance(output, list):
                                    for item in output:
                                        if isinstance(item, str) and (item.startswith("http") or item.startswith("/")):
                                            images_found.append(item)
                                elif isinstance(output, str) and (output.startswith("http") or output.startswith("/")):
                                    images_found.append(output)
                            if "file_path" in data:
                                images_found.append(data["file_path"])
                            if "saved_path" in data:
                                images_found.append(data["saved_path"])
                        
                        # Deduplicate and filter valid URLs
                        seen = set()
                        for img_url in images_found:
                            if img_url and img_url not in seen:
                                seen.add(img_url)
                                
                                # AUTO-SAVE remote images to local storage
                                if img_url.startswith("http") and self.file_storage:
                                    try:
                                        import os
                                        # Generate unique filename
                                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                        ext = ".png" if ".png" in img_url.lower() else ".webp" if ".webp" in img_url.lower() else ".jpg"
                                        save_filename = f"generated_{timestamp}_{len(artifacts)}{ext}"
                                        
                                        # Save to storage
                                        metadata = await self.file_storage.store_from_url(
                                            url=img_url,
                                            filename=save_filename,
                                            category="images",
                                            tags=["generated", step.get("tool", "image")]
                                        )
                                        
                                        # Use local URL (metadata.url is /files/{id})
                                        img_url = metadata.url
                                        logger.info(f"Auto-saved image to local storage: {img_url}")
                                    except Exception as save_error:
                                        logger.warning(f"Failed to auto-save image: {save_error}")
                                        # Keep using remote URL as fallback
                                
                                # Convert local paths to URLs
                                elif img_url.startswith("/Users/") or img_url.startswith("./data/"):
                                    # Extract just the filename for the files endpoint
                                    import os
                                    filename = os.path.basename(img_url)
                                    img_url = f"/files/{filename}"
                                
                                artifact = {
                                    "type": "image", 
                                    "url": img_url,
                                    "name": f"Image from {step.get('tool', 'generation')}"
                                }
                                artifacts.append(artifact)
                                yield {"type": "artifact", "artifact": artifact, "metadata": {"step": idx+1}}
                    
                    yield {"type": "tool_end", "content": step_name, "metadata": {"step_index": idx+1, "success": result.get("success", True)}}
                    
                except Exception as e:
                    logger.error(f"Step {idx+1} failed: {e}")
                    yield {"type": "tool_end", "content": step_name, "metadata": {"step_index": idx+1, "success": False, "error": str(e)}}
            
            # Final response
            yield {"type": "thinking", "content": "Synthesizing results...", "metadata": {"step": "synthesis"}}
            
            execution_result = {"status": "success", "results": list(step_outputs.values()), "artifacts": artifacts}
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
