"""
Super Intelligent Chat Interface
=================================

A conversational interface that provides:
- Natural language understanding
- Bidirectional streaming communication
- Tool execution and delegation
- Memory and context awareness
- Vision capabilities
- Self-improving through feedback

Inspired by Claude Agent SDK but enhanced for Otto.
"""

import asyncio
import logging
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from anthropic import Anthropic, AsyncAnthropic

from .unified_agent_system import (
    IntelligentAgent,
    AgentConfig,
    AgentRole,
    AgentTask,
    TaskStatus
)
from .memory_agent import MemoryAgent

logger = logging.getLogger(__name__)


# ============================================================================
# Message Types
# ============================================================================

class MessageRole(Enum):
    """Chat message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class ChatMessage:
    """A message in the conversation."""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Tool execution
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    tool_results: List[Dict[str, Any]] = field(default_factory=list)
    
    # Vision
    images: List[Dict[str, Any]] = field(default_factory=list)
    
    # Thinking
    thinking: Optional[str] = None
    
    def to_anthropic_format(self) -> Dict[str, Any]:
        """Convert to Anthropic API format."""
        content_parts = []
        
        # Add images if present
        for img in self.images:
            content_parts.append({
                "type": "image",
                "source": img
            })
        
        # Add text content
        if self.content:
            content_parts.append({
                "type": "text",
                "text": self.content
            })
        
        # Add tool results if present
        for result in self.tool_results:
            content_parts.append({
                "type": "tool_result",
                "tool_use_id": result["id"],
                "content": result["content"]
            })
        
        return {
            "role": self.role.value,
            "content": content_parts if len(content_parts) > 1 else self.content
        }


# ============================================================================
# Conversation Session
# ============================================================================

@dataclass
class ConversationSession:
    """A conversation session with memory and context."""
    session_id: str
    user_id: Optional[str] = None
    
    # Messages
    messages: List[ChatMessage] = field(default_factory=list)
    
    # Context
    context: Dict[str, Any] = field(default_factory=dict)
    system_prompt: Optional[str] = None
    
    # State
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    
    # Tasks
    active_tasks: List[str] = field(default_factory=list)
    completed_tasks: List[str] = field(default_factory=list)
    
    # Memory
    short_term_memory: Dict[str, Any] = field(default_factory=dict)
    long_term_memory: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, message: ChatMessage):
        """Add a message to the conversation."""
        self.messages.append(message)
        self.last_activity = datetime.now()
    
    def get_recent_messages(self, limit: int = 10) -> List[ChatMessage]:
        """Get recent messages."""
        return self.messages[-limit:]
    
    def get_anthropic_messages(self) -> List[Dict[str, Any]]:
        """Get messages in Anthropic API format."""
        return [msg.to_anthropic_format() for msg in self.messages]


# ============================================================================
# Super Intelligent Chat
# ============================================================================

class SuperIntelligentChat:
    """
    A super intelligent chat that can understand and do anything.
    
    Features:
    - Natural conversation with context awareness
    - Autonomous task execution
    - Tool use and delegation
    - Vision capabilities
    - Memory and learning
    - Streaming responses
    - Self-correction and verification
    """
    
    def __init__(
        self,
        anthropic_client: Optional[Anthropic] = None,
        async_anthropic_client: Optional[AsyncAnthropic] = None,
        tool_registry: Any = None,
        agent_crew: Any = None
    ):
        self.anthropic = anthropic_client or Anthropic()
        self.async_anthropic = async_anthropic_client or AsyncAnthropic()
        self.tool_registry = tool_registry
        self.agent_crew = agent_crew
        
        # Memory
        self.memory = MemoryAgent()
        
        # Sessions
        self.sessions: Dict[str, ConversationSession] = {}
        
        # Default system prompt
        self.default_system = """You are Otto, a super-intelligent autonomous AI assistant that can understand and do anything.

Your capabilities:
- Natural conversation and deep understanding
- Autonomous task execution and problem solving
- Tool use across 70+ integrated services
- Vision and multimodal understanding
- Memory and learning from interactions
- Multi-agent collaboration and delegation
- Self-correction and verification
- Creative content generation
- Business automation
- Research and analysis
- Contact/CRM management - add, search, update, and manage contacts

You can:
1. Understand complex requests in natural language
2. Break down problems into actionable steps
3. Execute tasks autonomously with tools
4. Delegate to specialized agents when needed
5. Learn and improve from feedback
6. Handle errors gracefully with self-correction
7. Work across text, images, code, and data
8. Research people/influencers and automatically add them to the contacts list using add_contact or add_multiple_contacts tools
9. Send emails to contacts using the email marketing tools

When the user asks you to research influencers, contacts, or people:
- Search the web for relevant information
- Extract names, emails, companies, and social links
- Use the add_contact or add_multiple_contacts tools to save them to the CRM
- Always confirm when contacts have been added

Be helpful, accurate, and autonomous. When you need to do something, do it - don't just describe it."""
        
        logger.info("Initialized SuperIntelligentChat")
    
    async def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        images: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False,
        use_tools: bool = True,
        use_vision: bool = False,
        system_prompt: Optional[str] = None
    ) -> Union[str, AsyncIterator[str]]:
        """
        Send a message and get a response.
        
        Args:
            message: The user's message
            session_id: Optional session ID for conversation continuity
            user_id: Optional user ID
            images: Optional list of images for vision
            stream: Whether to stream the response
            use_tools: Whether to enable tool use
            use_vision: Whether to enable vision
            system_prompt: Optional custom system prompt
            
        Returns:
            Response text or stream of response chunks
        """
        # Get or create session
        session = self._get_or_create_session(session_id, user_id, system_prompt)
        
        # Add user message
        user_msg = ChatMessage(
            role=MessageRole.USER,
            content=message,
            images=images or []
        )
        session.add_message(user_msg)
        
        # Get response
        if stream:
            return self._stream_response(session, use_tools, use_vision)
        else:
            return await self._get_response(session, use_tools, use_vision)
    
    async def _get_response(
        self,
        session: ConversationSession,
        use_tools: bool,
        use_vision: bool
    ) -> str:
        """Get a complete response."""
        # Build request
        messages = session.get_anthropic_messages()
        system_prompt = session.system_prompt or self.default_system
        
        # Prepare tools if enabled
        tools = None
        if use_tools and self.tool_registry:
            tools = self._get_available_tools()
        
        # Call Claude
        response = await self.async_anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            temperature=0.7,
            system=system_prompt,
            messages=messages,
            tools=tools if tools else None
        )
        
        # Process response
        assistant_content = ""
        tool_calls = []
        
        for block in response.content:
            if block.type == "text":
                assistant_content += block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })
        
        # Execute tools if needed
        if tool_calls:
            tool_results = await self._execute_tools(tool_calls, session)
            
            # Add assistant message with tool calls
            assistant_msg = ChatMessage(
                role=MessageRole.ASSISTANT,
                content=assistant_content,
                tool_calls=tool_calls
            )
            session.add_message(assistant_msg)
            
            # Add tool results
            tool_msg = ChatMessage(
                role=MessageRole.TOOL,
                content="",
                tool_results=tool_results
            )
            session.add_message(tool_msg)
            
            # Get follow-up response
            return await self._get_response(session, use_tools, use_vision)
        
        # Add assistant message
        assistant_msg = ChatMessage(
            role=MessageRole.ASSISTANT,
            content=assistant_content
        )
        session.add_message(assistant_msg)
        
        # Store in memory
        await self._update_memory(session)
        
        return assistant_content
    
    async def _stream_response(
        self,
        session: ConversationSession,
        use_tools: bool,
        use_vision: bool
    ) -> AsyncIterator[str]:
        """Stream response in real-time."""
        messages = session.get_anthropic_messages()
        system_prompt = session.system_prompt or self.default_system
        
        tools = None
        if use_tools and self.tool_registry:
            tools = self._get_available_tools()
        
        async with self.async_anthropic.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            temperature=0.7,
            system=system_prompt,
            messages=messages,
            tools=tools if tools else None
        ) as stream:
            assistant_content = ""
            
            async for text in stream.text_stream:
                assistant_content += text
                yield text
            
            # Get final message
            final_message = await stream.get_final_message()
            
            # Check for tool calls
            tool_calls = []
            for block in final_message.content:
                if block.type == "tool_use":
                    tool_calls.append({
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })
            
            # Execute tools if needed
            if tool_calls:
                tool_results = await self._execute_tools(tool_calls, session)
                
                # Add messages
                assistant_msg = ChatMessage(
                    role=MessageRole.ASSISTANT,
                    content=assistant_content,
                    tool_calls=tool_calls
                )
                session.add_message(assistant_msg)
                
                tool_msg = ChatMessage(
                    role=MessageRole.TOOL,
                    content="",
                    tool_results=tool_results
                )
                session.add_message(tool_msg)
                
                # Stream follow-up
                async for chunk in self._stream_response(session, use_tools, use_vision):
                    yield chunk
            else:
                # Add final message
                assistant_msg = ChatMessage(
                    role=MessageRole.ASSISTANT,
                    content=assistant_content
                )
                session.add_message(assistant_msg)
                
                await self._update_memory(session)
    
    async def _execute_tools(
        self,
        tool_calls: List[Dict[str, Any]],
        session: ConversationSession
    ) -> List[Dict[str, Any]]:
        """Execute tool calls."""
        results = []
        
        for tool_call in tool_calls:
            try:
                tool_name = tool_call["name"]
                tool_input = tool_call["input"]
                
                # Pre-filter known meta-parameters that should never be passed to tools
                meta_params_to_remove = {'task_description', 'task_type', 'task_id', 'step_id', 'execution_context'}
                tool_input = {k: v for k, v in tool_input.items() if k not in meta_params_to_remove}
                
                # Check if this should be delegated to an agent
                if self._should_delegate(tool_name):
                    result = await self._delegate_to_agent(tool_name, tool_input, session)
                else:
                    # Execute tool directly
                    tool = self.tool_registry.get_tool(tool_name)
                    result = await tool(**tool_input)
                
                results.append({
                    "id": tool_call["id"],
                    "content": str(result)
                })
                
            except Exception as e:
                logger.error(f"Tool execution failed: {e}", exc_info=True)
                results.append({
                    "id": tool_call["id"],
                    "content": f"Error: {str(e)}",
                    "is_error": True
                })
        
        return results
    
    def _should_delegate(self, tool_name: str) -> bool:
        """Check if a tool should be delegated to an agent."""
        # Complex tools that benefit from agent intelligence
        complex_tools = {
            "research", "analyze", "create_content", "design",
            "automate", "optimize", "plan", "verify"
        }
        return any(keyword in tool_name.lower() for keyword in complex_tools)
    
    async def _delegate_to_agent(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        session: ConversationSession
    ) -> Any:
        """Delegate a complex task to a specialized agent."""
        if not self.agent_crew:
            raise ValueError("Agent crew not available for delegation")
        
        # Create task
        task = AgentTask(
            task_id=f"task_{datetime.now().timestamp()}",
            description=f"Execute {tool_name} with parameters: {tool_input}",
            goal=tool_input.get("goal", "Complete the task successfully"),
            context=tool_input,
            inputs=tool_input
        )
        
        # Add to session
        session.active_tasks.append(task.task_id)
        
        # Execute with agent crew
        result = await self.agent_crew.execute_task(task)
        
        # Update session
        session.active_tasks.remove(task.task_id)
        session.completed_tasks.append(task.task_id)
        
        return result
    
    def _get_available_tools(self) -> List[Dict[str, Any]]:
        """Get available tools in Claude format."""
        if not self.tool_registry:
            return []
        
        tools = []
        for tool_name, tool in self.tool_registry.tools.items():
            tools.append({
                "name": tool_name,
                "description": tool.get("description", ""),
                "input_schema": tool.get("input_schema", {
                    "type": "object",
                    "properties": {},
                    "required": []
                })
            })
        
        return tools
    
    def _get_or_create_session(
        self,
        session_id: Optional[str],
        user_id: Optional[str],
        system_prompt: Optional[str]
    ) -> ConversationSession:
        """Get existing session or create new one."""
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]
        
        # Create new session
        new_session_id = session_id or f"session_{datetime.now().timestamp()}"
        session = ConversationSession(
            session_id=new_session_id,
            user_id=user_id,
            system_prompt=system_prompt
        )
        
        self.sessions[new_session_id] = session
        return session
    
    async def _update_memory(self, session: ConversationSession):
        """Update memory with conversation context."""
        # Store important information in memory
        recent_messages = session.get_recent_messages(5)
        context = {
            "session_id": session.session_id,
            "messages": [
                {"role": msg.role.value, "content": msg.content}
                for msg in recent_messages
            ],
            "timestamp": datetime.now()
        }
        
        # Store in memory
        try:
            await self.memory.store_knowledge(
                content=str(context),
                metadata={
                    "session_id": session.session_id,
                    "key": "conversation_context",
                    "type": "conversation_update"
                }
            )
        except Exception as e:
            logger.warning(f"Failed to store memory: {e}")
    
    async def execute_task(
        self,
        task_description: str,
        session_id: Optional[str] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a complex task autonomously.
        
        This is for tasks that require:
        - Multiple steps
        - Tool usage
        - Agent collaboration
        - Verification
        
        Args:
            task_description: Natural language task description
            session_id: Optional session for context
            stream: Whether to stream progress
            
        Returns:
            Task result
        """
        # Create task
        task = AgentTask(
            task_id=f"task_{datetime.now().timestamp()}",
            description=task_description,
            goal="Complete the task successfully with high quality",
            context={}
        )
        
        # Get session context
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
            task.context = {
                "conversation_history": [
                    {"role": msg.role.value, "content": msg.content}
                    for msg in session.get_recent_messages(5)
                ],
                "user_id": session.user_id
            }
        
        # Execute with agent crew
        if self.agent_crew:
            result = await self.agent_crew.execute_task(task)
        else:
            # Execute with chat interface
            response = await self.chat(
                message=f"Please complete this task: {task_description}",
                session_id=session_id,
                stream=False,
                use_tools=True
            )
            result = {"result": response}
        
        return result
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get a conversation session."""
        return self.sessions.get(session_id)
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions."""
        return [
            {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "message_count": len(session.messages),
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "is_active": session.is_active
            }
            for session in self.sessions.values()
        ]
    
    async def clear_session(self, session_id: str):
        """Clear a conversation session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleared session: {session_id}")
