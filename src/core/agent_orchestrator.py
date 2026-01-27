"""
Otto Universal Core - Agent Orchestrator
========================================

The central brain that coordinates all agents and tool execution.
This is where the magic happens - understanding intent, planning execution,
and delivering results through natural conversation.
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime
from anthropic import Anthropic
from openai import AsyncOpenAI

from .planning_agent import PlanningAgent
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
        openai_api_key: str,
        config: Optional[Dict[str, Any]] = None
    ):
        self.config = config or {}
        
        # Initialize AI clients
        self.anthropic = Anthropic(api_key=anthropic_api_key)
        self.openai = AsyncOpenAI(api_key=openai_api_key)
        
        # Initialize agents
        self.planning_agent = PlanningAgent(self.anthropic)
        self.execution_agent = ExecutionAgent(self.anthropic)
        self.memory_agent = MemoryAgent()
        
        # Initialize tool registry
        self.tool_registry = ToolRegistry()
        self.tool_registry.discover_tools()
        
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
            from ..storage import FileStorage, StorageConfig
            
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
            
            # Add to memory
            await self.memory_agent.store_message(
                session_id=session["id"],
                role="user",
                content=message,
                metadata=context or {}
            )
            
            # Get relevant memories
            memories = await self.memory_agent.recall(
                query=message,
                session_id=session["id"],
                k=5
            )
            
            # Create planning prompt with context
            planning_context = {
                "message": message,
                "memories": memories,
                "session": session,
                "available_tools": self.tool_registry.list_tools()
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
            
            # Store response in memory
            await self.memory_agent.store_message(
                session_id=session["id"],
                role="assistant",
                content=response,
                metadata={
                    "type": "tool_response",
                    "plan": plan,
                    "results": execution_result
                }
            )
            
            return {
                "response": response,
                "type": "tool_execution",
                "session_id": session["id"],
                "plan": plan,
                "results": execution_result.get("results", [])
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return {
                "response": f"I encountered an error: {str(e)}. Please try again.",
                "type": "error",
                "session_id": session_id
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
        # Format results for the prompt
        results_text = ""
        for result in execution_result.get("results", []):
            results_text += f"\nTool: {result.get('tool', 'unknown')}\n"
            results_text += f"Status: {'Success' if result.get('success') else 'Failed'}\n"
            if result.get("data"):
                results_text += f"Data: {result['data']}\n"
            if result.get("error"):
                results_text += f"Error: {result['error']}\n"
        
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
