"""
Unified Otto API - Super Intelligent System
===========================================

A completely refactored API that combines the best elements from:
- CrewAI: Multi-agent collaboration
- Claude SDK: Bidirectional communication
- AutoGPT: Autonomous execution
- browser-use: Vision and state management
- agentops: Observability

New Features:
- Super intelligent chat interface
- Autonomous task execution
- Multi-agent crews
- Real-time streaming
- Vision capabilities
- Comprehensive monitoring
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from anthropic import Anthropic, AsyncAnthropic

# Core systems
from src.core.unified_agent_system import (
    IntelligentAgent,
    AgentCrew,
    AgentConfig,
    AgentRole,
    AgentTask,
    TaskStatus,
    AgentMode
)
from src.core.super_intelligent_chat import (
    SuperIntelligentChat,
    ConversationSession,
    ChatMessage,
    MessageRole
)
from src.core.agent_health_monitor import get_health_monitor
from src.core.agent_analytics import get_analytics
from src.core.agent_communication import get_message_bus
from src.core.error_recovery import get_recovery_manager

# Existing systems
from src.core.tool_registry import ToolRegistry
from src.core.memory_agent import MemoryAgent

logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================

class ChatRequest(BaseModel):
    """Request for chat endpoint."""
    message: str = Field(..., description="The user's message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    user_id: Optional[str] = Field(None, description="User ID")
    images: Optional[List[Dict[str, Any]]] = Field(None, description="Images for vision")
    stream: bool = Field(False, description="Whether to stream the response")
    use_tools: bool = Field(True, description="Whether to enable tool use")
    use_vision: bool = Field(False, description="Whether to enable vision")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    message: str
    session_id: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}


class TaskRequest(BaseModel):
    """Request for task execution."""
    description: str = Field(..., description="Task description in natural language")
    goal: Optional[str] = Field(None, description="Desired outcome")
    session_id: Optional[str] = Field(None, description="Session for context")
    priority: int = Field(1, description="Task priority (1-10)")
    max_steps: int = Field(20, description="Maximum execution steps")
    use_crew: bool = Field(True, description="Whether to use agent crew")
    stream: bool = Field(False, description="Whether to stream progress")


class TaskResponse(BaseModel):
    """Response from task execution."""
    task_id: str
    status: str
    result: Optional[Any] = None
    duration: Optional[float] = None
    steps_taken: int = 0
    error: Optional[str] = None


class AgentCreationRequest(BaseModel):
    """Request to create a new agent."""
    agent_id: str
    role: str
    name: str
    description: str
    capabilities: List[str] = []
    tools: List[str] = []
    mode: str = "autonomous"
    use_memory: bool = True
    use_vision: bool = False
    can_delegate: bool = True


class CrewCreationRequest(BaseModel):
    """Request to create a new crew."""
    crew_name: str
    agents: List[AgentCreationRequest]


# ============================================================================
# Global State
# ============================================================================

class OttoState:
    """Global application state."""
    def __init__(self):
        self.anthropic: Optional[Anthropic] = None
        self.async_anthropic: Optional[AsyncAnthropic] = None
        self.tool_registry: Optional[ToolRegistry] = None
        self.super_chat: Optional[SuperIntelligentChat] = None
        self.default_crew: Optional[AgentCrew] = None
        self.crews: Dict[str, AgentCrew] = {}
        self.health_monitor = get_health_monitor()
        self.analytics = get_analytics()
        self.message_bus = get_message_bus()
        self.recovery_manager = get_recovery_manager()


state = OttoState()


# ============================================================================
# Lifespan Management
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources."""
    logger.info("Starting Otto Universal - Super Intelligent System")
    
    try:
        # Initialize Anthropic clients
        state.anthropic = Anthropic()
        state.async_anthropic = AsyncAnthropic()
        
        # Initialize tool registry
        state.tool_registry = ToolRegistry()
        
        # Discover tools from the tools package
        state.tool_registry.discover_tools("src.tools")
        
        # Register tool class instances for API-key dependent tools
        import os
        
        # Register Printify tools if API key available
        printify_api_key = os.getenv("PRINTIFY_API_KEY") or os.getenv("PRINTIFY_TOKEN")
        printify_shop_id = os.getenv("PRINTIFY_SHOP_ID")
        if printify_api_key and printify_shop_id:
            from src.tools.printify import PrintifyTools
            printify_tools = PrintifyTools(printify_api_key, printify_shop_id)
            state.tool_registry.register_tool_class(printify_tools)
            logger.info("Printify tools registered")
        
        # Register contacts tools
        from src.tools.contacts import ContactsTools
        contacts_tools = ContactsTools()
        state.tool_registry.register_tool_class(contacts_tools)
        logger.info("Contacts tools registered")
        
        # Create default agent crew
        state.default_crew = AgentCrew(
            name="Otto Core Crew",
            anthropic_client=state.anthropic,
            tool_registry=state.tool_registry
        )
        
        # Add core agents to the crew
        _create_core_agents(state.default_crew)
        
        # Initialize super intelligent chat
        state.super_chat = SuperIntelligentChat(
            anthropic_client=state.anthropic,
            async_anthropic_client=state.async_anthropic,
            tool_registry=state.tool_registry,
            agent_crew=state.default_crew
        )
        
        # Start monitoring services
        await state.health_monitor.start_monitoring()
        await state.message_bus.start()
        
        logger.info("Otto Universal initialized successfully")
        logger.info(f"- Crew: {state.default_crew.name}")
        logger.info(f"- Agents: {len(state.default_crew.agents)}")
        logger.info(f"- Tools: {len(state.tool_registry.tools)}")
        
        yield
        
    finally:
        # Cleanup
        logger.info("Shutting down Otto Universal")
        await state.health_monitor.stop_monitoring()
        await state.message_bus.stop()


def _create_core_agents(crew: AgentCrew):
    """Create core agents for the default crew."""
    # Orchestrator
    crew.add_agent(AgentConfig(
        agent_id="orchestrator",
        role=AgentRole.ORCHESTRATOR,
        name="Otto Orchestrator",
        description="Coordinates all agents and manages task execution",
        capabilities=["planning", "coordination", "delegation", "monitoring"],
        mode=AgentMode.AUTONOMOUS,
        can_delegate=True,
        use_thinking=True,
        use_planning=True
    ))
    
    # Planner
    crew.add_agent(AgentConfig(
        agent_id="planner",
        role=AgentRole.PLANNER,
        name="Otto Planner",
        description="Creates detailed execution plans for complex tasks",
        capabilities=["strategic_planning", "task_decomposition", "resource_allocation"],
        mode=AgentMode.AUTONOMOUS,
        use_thinking=True,
        use_planning=True
    ))
    
    # Executor
    crew.add_agent(AgentConfig(
        agent_id="executor",
        role=AgentRole.EXECUTOR,
        name="Otto Executor",
        description="Executes tasks and uses tools",
        capabilities=["tool_execution", "automation", "integration"],
        tools=["all"],  # Has access to all tools
        mode=AgentMode.AUTONOMOUS
    ))
    
    # Researcher
    crew.add_agent(AgentConfig(
        agent_id="researcher",
        role=AgentRole.RESEARCHER,
        name="Otto Researcher",
        description="Conducts research and gathers information",
        capabilities=["web_search", "data_collection", "analysis"],
        tools=["web_search", "scrape_website", "fetch_url"],
        mode=AgentMode.AUTONOMOUS,
        use_memory=True
    ))
    
    # Analyzer
    crew.add_agent(AgentConfig(
        agent_id="analyzer",
        role=AgentRole.ANALYZER,
        name="Otto Analyzer",
        description="Analyzes data and provides insights",
        capabilities=["data_analysis", "pattern_recognition", "insights"],
        mode=AgentMode.AUTONOMOUS,
        use_thinking=True
    ))
    
    # Verifier
    crew.add_agent(AgentConfig(
        agent_id="verifier",
        role=AgentRole.VERIFIER,
        name="Otto Verifier",
        description="Verifies results and ensures quality",
        capabilities=["quality_assurance", "verification", "testing"],
        mode=AgentMode.AUTONOMOUS,
        use_thinking=True
    ))
    
    # Vision Agent
    crew.add_agent(AgentConfig(
        agent_id="vision",
        role=AgentRole.VISION,
        name="Otto Vision",
        description="Processes and understands images",
        capabilities=["image_analysis", "visual_understanding", "ocr"],
        mode=AgentMode.AUTONOMOUS,
        use_vision=True
    ))


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Otto Universal - Super Intelligent System",
    description="A unified autonomous agent platform with super intelligence",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Chat Endpoints
# ============================================================================

@app.post("/api/v2/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Super intelligent chat endpoint.
    
    This is the main interface for conversational interaction.
    It can:
    - Understand natural language
    - Execute tasks autonomously
    - Use tools and delegate to agents
    - Maintain conversation context
    - Handle vision inputs
    """
    try:
        response = await state.super_chat.chat(
            message=request.message,
            session_id=request.session_id,
            user_id=request.user_id,
            images=request.images,
            stream=False,  # Non-streaming for HTTP
            use_tools=request.use_tools,
            use_vision=request.use_vision,
            system_prompt=request.system_prompt
        )
        
        # Get or create session for response
        session = state.super_chat._get_or_create_session(
            request.session_id,
            request.user_id,
            request.system_prompt
        )
        
        return ChatResponse(
            message=response,
            session_id=session.session_id,
            timestamp=datetime.now(),
            metadata={
                "message_count": len(session.messages),
                "tools_used": request.use_tools,
                "vision_enabled": request.use_vision
            }
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/api/v2/chat/stream")
async def chat_stream(websocket: WebSocket):
    """
    Streaming chat endpoint via WebSocket.
    
    Provides real-time bidirectional communication.
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            message = data.get("message")
            session_id = data.get("session_id")
            user_id = data.get("user_id")
            
            if not message:
                await websocket.send_json({"error": "Message required"})
                continue
            
            # Stream response
            async for chunk in await state.super_chat.chat(
                message=message,
                session_id=session_id,
                user_id=user_id,
                stream=True,
                use_tools=data.get("use_tools", True),
                use_vision=data.get("use_vision", False)
            ):
                await websocket.send_json({
                    "type": "chunk",
                    "content": chunk
                })
            
            # Send completion
            await websocket.send_json({
                "type": "complete",
                "session_id": session_id
            })
            
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        await websocket.send_json({"error": str(e)})


@app.get("/api/v2/chat/sessions")
async def list_sessions():
    """List all conversation sessions."""
    return state.super_chat.list_sessions()


@app.get("/api/v2/chat/sessions/{session_id}")
async def get_session(session_id: str):
    """Get a specific conversation session."""
    session = state.super_chat.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session.session_id,
        "user_id": session.user_id,
        "message_count": len(session.messages),
        "created_at": session.created_at.isoformat(),
        "last_activity": session.last_activity.isoformat(),
        "is_active": session.is_active,
        "messages": [
            {
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in session.messages
        ]
    }


@app.delete("/api/v2/chat/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear a conversation session."""
    await state.super_chat.clear_session(session_id)
    return {"status": "success", "message": f"Session {session_id} cleared"}


# ============================================================================
# Task Execution Endpoints
# ============================================================================

@app.post("/api/v2/tasks", response_model=TaskResponse)
async def execute_task(request: TaskRequest):
    """
    Execute a complex task autonomously.
    
    This endpoint is for tasks that require:
    - Multiple steps
    - Tool usage
    - Agent collaboration
    - Planning and verification
    """
    try:
        # Create task
        task = AgentTask(
            task_id=f"task_{datetime.now().timestamp()}",
            description=request.description,
            goal=request.goal or "Complete the task successfully",
            priority=request.priority,
            max_steps=request.max_steps
        )
        
        # Execute with crew
        if request.use_crew:
            result = await state.default_crew.execute_task(task)
        else:
            # Execute with super chat
            result = await state.super_chat.execute_task(
                task_description=request.description,
                session_id=request.session_id,
                stream=False
            )
        
        return TaskResponse(
            task_id=task.task_id,
            status=task.status.value,
            result=result,
            duration=task.duration,
            steps_taken=task.steps_taken,
            error=task.error
        )
        
    except Exception as e:
        logger.error(f"Task execution error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v2/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a task."""
    # TODO: Implement task tracking
    raise HTTPException(status_code=501, detail="Task tracking not yet implemented")


# ============================================================================
# Agent & Crew Management
# ============================================================================

@app.get("/api/v2/crews")
async def list_crews():
    """List all agent crews."""
    crews_info = {
        "default": state.default_crew.get_crew_status()
    }
    
    for name, crew in state.crews.items():
        crews_info[name] = crew.get_crew_status()
    
    return crews_info


@app.post("/api/v2/crews")
async def create_crew(request: CrewCreationRequest):
    """Create a new agent crew."""
    try:
        crew = AgentCrew(
            name=request.crew_name,
            anthropic_client=state.anthropic,
            tool_registry=state.tool_registry
        )
        
        # Add agents
        for agent_config in request.agents:
            config = AgentConfig(
                agent_id=agent_config.agent_id,
                role=AgentRole(agent_config.role),
                name=agent_config.name,
                description=agent_config.description,
                capabilities=agent_config.capabilities,
                tools=agent_config.tools,
                mode=AgentMode(agent_config.mode),
                use_memory=agent_config.use_memory,
                use_vision=agent_config.use_vision,
                can_delegate=agent_config.can_delegate
            )
            crew.add_agent(config)
        
        state.crews[request.crew_name] = crew
        
        return {
            "status": "success",
            "crew_name": request.crew_name,
            "agent_count": len(crew.agents)
        }
        
    except Exception as e:
        logger.error(f"Crew creation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v2/agents")
async def list_agents():
    """List all agents across all crews."""
    all_agents = {}
    
    # Default crew
    for agent_id, agent in state.default_crew.agents.items():
        all_agents[agent_id] = {
            "crew": state.default_crew.name,
            **agent.config.to_dict()
        }
    
    # Other crews
    for crew_name, crew in state.crews.items():
        for agent_id, agent in crew.agents.items():
            all_agents[agent_id] = {
                "crew": crew_name,
                **agent.config.to_dict()
            }
    
    return all_agents


# ============================================================================
# Contacts API
# ============================================================================

from src.tools.contacts import load_contacts, save_contacts, generate_contact_id


class ContactCreate(BaseModel):
    """Contact creation model."""
    name: str
    email: str = ""
    company: str = ""
    phone: str = ""
    type: str = "contact"
    notes: str = ""
    source: str = ""
    social_links: Dict[str, str] = {}


class ContactUpdate(BaseModel):
    """Contact update model."""
    name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    type: Optional[str] = None
    notes: Optional[str] = None
    source: Optional[str] = None
    social_links: Optional[Dict[str, str]] = None


@app.get("/api/contacts")
async def get_contacts():
    """Get all contacts."""
    contacts = load_contacts()
    return contacts


@app.post("/api/contacts")
async def create_contact(contact: ContactCreate):
    """Create a new contact."""
    contacts = load_contacts()
    
    # Check for duplicate email
    if contact.email:
        existing = next((c for c in contacts if c.get('email', '').lower() == contact.email.lower()), None)
        if existing:
            raise HTTPException(status_code=400, detail=f"Contact with email {contact.email} already exists")
    
    new_contact = {
        "id": generate_contact_id(),
        "name": contact.name,
        "email": contact.email,
        "company": contact.company,
        "phone": contact.phone,
        "type": contact.type,
        "notes": contact.notes,
        "source": contact.source or "manual",
        "social_links": contact.social_links,
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat()
    }
    
    contacts.append(new_contact)
    save_contacts(contacts)
    
    return new_contact


@app.get("/api/contacts/{contact_id}")
async def get_contact(contact_id: str):
    """Get a single contact by ID."""
    contacts = load_contacts()
    contact = next((c for c in contacts if c['id'] == contact_id), None)
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    return contact


@app.put("/api/contacts/{contact_id}")
async def update_contact(contact_id: str, updates: ContactUpdate):
    """Update a contact."""
    contacts = load_contacts()
    contact_idx = next((i for i, c in enumerate(contacts) if c['id'] == contact_id), None)
    
    if contact_idx is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Apply updates
    update_data = updates.dict(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            contacts[contact_idx][key] = value
    
    contacts[contact_idx]['updatedAt'] = datetime.now().isoformat()
    save_contacts(contacts)
    
    return contacts[contact_idx]


@app.delete("/api/contacts/{contact_id}")
async def delete_contact(contact_id: str):
    """Delete a contact."""
    contacts = load_contacts()
    original_count = len(contacts)
    contacts = [c for c in contacts if c['id'] != contact_id]
    
    if len(contacts) == original_count:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    save_contacts(contacts)
    
    return {"success": True, "message": "Contact deleted"}


# ============================================================================
# Monitoring Endpoints
# ============================================================================

@app.get("/api/v2/health")
async def health_check():
    """Get system health status."""
    health = state.health_monitor.get_system_health()
    
    return {
        "status": "healthy" if health["overall_health"] != "critical" else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        **health
    }


@app.get("/api/v2/analytics")
async def get_analytics():
    """Get system analytics."""
    return {
        "agent_profiles": state.analytics.get_agent_profiles(),
        "task_history": state.analytics.get_task_history(),
        "performance_summary": state.analytics.get_performance_summary()
    }


@app.get("/api/v2/tools")
async def list_tools():
    """List all available tools."""
    return {
        "tool_count": len(state.tool_registry.tools),
        "tools": list(state.tool_registry.tools.keys())
    }


# ============================================================================
# Root
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Otto Universal - Super Intelligent System",
        "version": "2.0.0",
        "status": "operational",
        "features": [
            "Super intelligent chat",
            "Autonomous task execution",
            "Multi-agent collaboration",
            "70+ integrated tools",
            "Vision capabilities",
            "Real-time streaming",
            "Memory and learning",
            "Comprehensive monitoring"
        ],
        "endpoints": {
            "chat": "/api/v2/chat",
            "chat_stream": "/api/v2/chat/stream",
            "tasks": "/api/v2/tasks",
            "crews": "/api/v2/crews",
            "agents": "/api/v2/agents",
            "health": "/api/v2/health",
            "analytics": "/api/v2/analytics",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
