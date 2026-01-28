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
from typing import Any, Dict, List, Optional
from datetime import datetime
from anthropic import Anthropic
from openai import AsyncOpenAI

from .super_planning_agent import SuperPlanningAgent as PlanningAgent
from .master_agent import MasterOrchestrator
from .execution_agent import ExecutionAgent
from .memory_agent import MemoryAgent
from .tool_registry import ToolRegistry

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
        
        # Initialize tool registry
        self.tool_registry = ToolRegistry()
        self.tool_registry.discover_tools()
        
        # Initialize master orchestrator for multi-agent coordination
        self.master = MasterOrchestrator(self.anthropic, self.tool_registry)
        
        # File storage reference (set during tool registration)
        self.file_storage = None
        
        # Register tool classes with their API keys
        self._register_tool_classes()
        
        # Session management
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Agent Orchestrator initialized")
    
    def _register_tool_classes(self):
        """Initialize and register all tool classes."""
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
            
            # === CORE AUTONOMOUS TOOLS ===
            
            # Universal Replicate - access to ANY AI model
            if self.config.get("replicate_api_token"):
                replicate = ReplicateUniversal(
                    api_token=self.config["replicate_api_token"]
                )
                self.tool_registry.register_tool_class(replicate)
                logger.info("Registered Universal Replicate tools (ANY AI model access)")
            
            # Code execution - write and run code autonomously
            code_tools = CodeExecutionTools(workspace_dir="./workspace")
            self.tool_registry.register_tool_class(code_tools)
            logger.info("Registered Code Execution tools")
            
            # Data processing
            data_tools = DataProcessingTools(workspace_dir="./workspace")
            self.tool_registry.register_tool_class(data_tools)
            logger.info("Registered Data Processing tools")
            
            # === INTEGRATION TOOLS ===
            
            # Printify tools
            printify_key = self.config.get("printify_api_key") or self.config.get("printify_api_token")
            if printify_key:
                printify = PrintifyTools(
                    api_token=printify_key,
                    shop_id=self.config.get("printify_shop_id", "")
                )
                self.tool_registry.register_tool_class(printify)
                logger.info("Registered Printify tools")
            
            # Image generation tools
            if self.config.get("replicate_api_token"):
                image_gen = ImageGenerationTools(
                    replicate_token=self.config["replicate_api_token"]
                )
                self.tool_registry.register_tool_class(image_gen)
                logger.info("Registered Image Generation tools")
            
            # Research tools
            research = ResearchTools(
                config={"serper_api_key": self.config.get("serper_api_key", "")}
            )
            self.tool_registry.register_tool_class(research)
            logger.info("Registered Research tools")
            
            # Shopify tools
            shopify_url = self.config.get("shopify_shop_name") or self.config.get("shopify_store_url")
            shopify_token = self.config.get("shopify_access_token") or self.config.get("shopify_api_key")
            if shopify_url and shopify_token:
                shopify = ShopifyTools(
                    shop_url=shopify_url,
                    access_token=shopify_token
                )
                self.tool_registry.register_tool_class(shopify)
                logger.info("Registered Shopify tools")
            
            # Content tools
            content = ContentTools(
                anthropic_client=self.anthropic
            )
            self.tool_registry.register_tool_class(content)
            logger.info("Registered Content tools")
            
            # Browser tools (optional)
            try:
                browser = BrowserTools()
                self.tool_registry.register_tool_class(browser)
                logger.info("Registered Browser tools")
            except Exception as e:
                logger.warning(f"Browser tools not available: {e}")
            
            # File storage tools - always available
            storage = FileStorage(StorageConfig())
            file_tools = FileStorageTools(storage)
            self.tool_registry.register_tool_class(file_tools)
            self.file_storage = storage  # Store reference for use by other tools
            logger.info("Registered File Storage tools")
            
        except Exception as e:
            logger.error(f"Error registering tool classes: {e}", exc_info=True)
        
    async def process(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and return a response.
        
        Args:
            message: User's input message
            context: Additional context (platform, user info, etc.)
            session_id: Session identifier for context tracking
            
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
            
            # Get relevant memories
            memories = await self.memory_agent.recall(
                query=message,
                session_id=session["id"],
                k=5
            )
            
            # Create planning prompt with context - limit tools to avoid token overflow
            all_tools = self.tool_registry.list_tools()
            # Only pass essential tool info
            limited_tools = [
                {"name": t["name"], "description": t.get("description", "")[:150], "category": t.get("category", "general")}
                for t in all_tools[:50]  # Limit to 50 most important tools
            ]
            
            planning_context = {
                "message": message,
                "memories": memories[:5],  # Limit memories
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
                    "content": f"""You are Otto, a friendly and capable AI assistant.
                    
Previous context:
{memory_context}

User message: {message}

Respond naturally and helpfully. If you can help with the request directly, do so.
If the request requires using tools you don't currently have access to, explain what you would need."""
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
        for result in execution_result.get("results", []):
            results_text += f"\nTool: {result.get('tool', 'unknown')}\n"
            # Check both 'status' field and nested 'result.success' for success determination
            is_success = result.get('status') == 'success' or result.get('result', {}).get('success', False)
            results_text += f"Status: {'Success' if is_success else 'Failed'}\n"
            # Extract data from nested result structure if present - TRUNCATE to prevent token overflow
            data = result.get('data') or result.get('result', {}).get('data')
            if data:
                data_str = str(data)[:2000]  # Limit data size
                results_text += f"Data: {data_str}\n"
            error = result.get('error') or result.get('result', {}).get('error')
            if error:
                error_str = str(error)[:500]  # Limit error size
                results_text += f"Error: {error_str}\n"
        
        # Truncate total results if too large
        if len(results_text) > 10000:
            results_text = results_text[:10000] + "\n... (truncated)"
        
        response = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": f"""You are Otto, a capable AI assistant that just completed some tasks.

User's original request: {message}

Plan that was executed:
{plan.get('summary', 'Multi-step operation')}

Results:
{results_text}

Generate a clear, helpful response that:
1. Summarizes what was accomplished
2. Highlights any important information or data
3. Mentions any errors or issues encountered
4. Suggests next steps if appropriate

Be concise but thorough."""
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
