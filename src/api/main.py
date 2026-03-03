"""
Otto Universal API - FastAPI Application
========================================

Main API server providing REST and WebSocket endpoints.
"""

import logging
import json
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse, Response, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv

from ..core.agent_orchestrator import AgentOrchestrator
from ..core.slash_commands import get_slash_processor
from ..utils.config import get_settings
from ..utils.logger import setup_logging

# Import routers
from .settings import router as settings_router
from .files import router as files_router
from .connections import router as connections_router
from .agents import router as agents_router, set_orchestrator as set_agents_orchestrator
from .models import router as models_router, set_orchestrator as set_models_orchestrator
from .workflows import router as workflows_router, set_orchestrator as set_workflows_orchestrator
from .business import router as business_router, set_business_orchestrator
from .projects import router as projects_router
from .skills import router as skills_router
from .extensions import router as extensions_router
from .profile import router as profile_router
from .conversations import router as conversations_router
from .brand import router as brand_router
from .social import router as social_router
from .email import router as email_router
from .tasks import router as tasks_router
from .webhooks import router as webhooks_router
from .scheduler_routes import router as scheduler_router, set_scheduler
from .browser import router as browser_router
from .intelligence import router as intelligence_router
from .creative_platform import router as creative_platform_router
from .plugins import router as plugins_router
from .integrations import router as integrations_router
from .whatsapp import router as whatsapp_router
from .telegram import router as telegram_router
from .discord import router as discord_router
from .auth import router as auth_router
from .setup import router as setup_router
from .email_webhook import router as email_webhook_router
from .ollama import router as ollama_router
from .model_manager import router as model_manager_router
from ..core.session_manager import router as sessions_router
from .gateway_ws import router as gateway_router

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Import enhanced Printify router (after logger is defined)
try:
    from ..core.printify_enhanced import create_printify_router
    printify_enhanced_router = create_printify_router()
    logger.info("✅ Enhanced Printify router loaded")
except Exception as e:
    printify_enhanced_router = None
    logger.warning(f"Enhanced Printify router not available: {e}")

# Global orchestrator instance
orchestrator: Optional[AgentOrchestrator] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup on startup/shutdown."""
    global orchestrator
    
    settings = get_settings()
    
    # Initialize database
    logger.info("Initializing Database...")
    from ..database import init_db, get_db
    database_url = settings.database_url if hasattr(settings, 'database_url') else "sqlite:///./data/otto.db"
    db = init_db(database_url)
    logger.info(f"✨ Database ready: {database_url.split('://')[0]}")
    
    # Initialize orchestrator with full config
    logger.info("Initializing Agent Orchestrator...")
    orchestrator = AgentOrchestrator(
        anthropic_api_key=settings.anthropic_api_key,
        openai_api_key=settings.openai_api_key,
        config={
            **settings.model_dump(),
            # Ensure API keys are passed with their expected names
            "printify_api_key": settings.printify_api_key or settings.printify_api_token,
            "printify_shop_id": settings.printify_shop_id,
            "replicate_api_token": settings.replicate_api_token,
            "shopify_api_key": settings.shopify_api_key,
            "shopify_api_secret": settings.shopify_api_secret,
            "shopify_shop_name": settings.shopify_shop_name,
            "serper_api_key": settings.serper_api_key,
        }
    )
    
    # Initialize autonomous business orchestrator
    logger.info("Initializing Autonomous Business Orchestrator...")
    from ..core.autonomous_orchestrator import AutonomousOrchestrator
    from ..core.business_workflows import BusinessWorkflowGenerator
    
    autonomous_orchestrator = AutonomousOrchestrator(
        anthropic_client=orchestrator.anthropic,
        tool_registry=orchestrator.tool_registry,
        memory_agent=orchestrator.memory_agent,
        config=orchestrator.config
    )
    
    workflow_generator = BusinessWorkflowGenerator(autonomous_orchestrator)
    
    set_agents_orchestrator(orchestrator)
    set_models_orchestrator(orchestrator)
    set_workflows_orchestrator(orchestrator)
    set_business_orchestrator(autonomous_orchestrator, workflow_generator)
    
    # Initialize skills and projects systems
    logger.info("Loading Skills System...")
    from ..core.skills_system import get_skills_registry
    skills_registry = get_skills_registry()
    logger.info(f"✨ Skills System ready: {len(skills_registry.list_skills())} skills loaded")
    
    logger.info("Initializing Project Management...")
    from ..core.project_manager import get_project_manager
    project_manager = get_project_manager()
    logger.info(f"✨ Project Manager ready: {len(project_manager.list_projects())} projects loaded")
    
    # Initialize Task Scheduler
    logger.info("Initializing Task Scheduler...")
    from ..tools.scheduler import create_task_scheduler
    task_scheduler = create_task_scheduler(
        data_dir="data/task_queue",
        tool_executor=lambda tool, params: orchestrator.execute_tool(tool, params) if orchestrator else None
    )
    task_scheduler.start()
    set_scheduler(task_scheduler)
    logger.info("✨ Task Scheduler: ACTIVE")
    
    logger.info("Otto Universal API is ready!")
    logger.info("✨ Autonomous Business Operations: ACTIVE")
    logger.info(f"✨ Skills Available: {len(skills_registry.list_skills())}")
    logger.info(f"✨ Projects: {len(project_manager.list_projects())}")
    
    # Initialize Plugin System
    logger.info("Initializing Plugin System...")
    try:
        from ..core.plugin_system import init_plugins
        plugin_manager = await init_plugins()
        active_plugins = len(plugin_manager.get_active_plugins())
        logger.info(f"✨ Plugin System: {active_plugins} plugins active")
    except Exception as e:
        logger.warning(f"Plugin system initialization skipped: {e}")
    
    # Initialize Creative Platform
    logger.info("Initializing Creative Platform...")
    try:
        from ..core.creative_platform import init_creative_platform
        creative_platform = init_creative_platform(
            tool_registry=orchestrator.tool_registry,
            execution_agent=None  # Will use direct tool calls
        )
        logger.info("✨ Creative Platform: ACTIVE")
    except Exception as e:
        logger.warning(f"Creative Platform initialization skipped: {e}")
    
    # Initialize Gateway and Channels
    logger.info("Initializing Otto Gateway...")
    try:
        from ..core.gateway import OttoGateway
        from ..core.channel_manager import ChannelManager
        
        gateway = OttoGateway(orchestrator)
        
        # Load channel config
        channels_config = settings.model_dump().get("channels", {})
        if channels_config:
            channel_manager = ChannelManager(gateway, {"channels": channels_config})
            await channel_manager.start_channels()
            logger.info(f"✨ Gateway: {len(channel_manager.list_channels())} channels active")
        else:
            channel_manager = None
            logger.info("✨ Gateway: Ready (no channels configured)")
        
        # Store in app.state
        app.state.gateway = gateway
        app.state.channel_manager = channel_manager
    except Exception as e:
        logger.warning(f"Gateway initialization skipped: {e}")
        app.state.gateway = None
        app.state.channel_manager = None
    
    # Initialize Voice Capabilities
    logger.info("Initializing Voice Capabilities...")
    try:
        from ..core.voice import VoiceCapabilities, VoiceConfig
        
        voice_config = VoiceConfig(
            enable_wake_word=settings.model_dump().get("enable_wake_word", False),
            enable_talk_mode=settings.model_dump().get("enable_talk_mode", True),
            wake_word=settings.model_dump().get("wake_word", "hey otto")
        )
        
        # Agent callback for voice
        async def voice_agent_callback(text: str) -> str:
            if orchestrator:
                response = await orchestrator.process_message(text, session_id="voice")
                return response.get("message", "")
            return "Sorry, I couldn't process that."
        
        voice = VoiceCapabilities(voice_config, voice_agent_callback)
        
        if voice_config.enable_wake_word or voice_config.enable_talk_mode:
            await voice.start()
            logger.info(f"✨ Voice: Wake={voice_config.enable_wake_word}, Talk={voice_config.enable_talk_mode}")
        
        app.state.voice = voice
    except Exception as e:
        logger.warning(f"Voice capabilities initialization skipped: {e}")
        app.state.voice = None
    
    # Store references in app.state for health checks
    app.state.start_time = datetime.now()
    app.state.orchestrator = orchestrator
    
    yield
    
    # Cleanup
    logger.info("Shutting down...")
    task_scheduler.stop()
    
    # Shutdown channels
    if hasattr(app.state, 'channel_manager') and app.state.channel_manager:
        await app.state.channel_manager.stop_channels()
    
    # Shutdown voice
    if hasattr(app.state, 'voice') and app.state.voice:
        app.state.voice.stop()
    
    # Shutdown skills
    if hasattr(app.state, 'skills_registry') and app.state.skills_registry:
        await app.state.skills_registry.shutdown_all()


# Create FastAPI app
app = FastAPI(
    title="Otto Universal API",
    description="Universal AI Assistant - Control Everything Through Conversation",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(settings_router)
app.include_router(files_router)
app.include_router(connections_router)
app.include_router(agents_router)
app.include_router(models_router)
app.include_router(workflows_router)
app.include_router(business_router)
app.include_router(projects_router)
app.include_router(skills_router)
app.include_router(extensions_router)
app.include_router(profile_router)
app.include_router(conversations_router)
app.include_router(brand_router)
app.include_router(social_router)
app.include_router(email_router)
app.include_router(tasks_router)
app.include_router(webhooks_router)
app.include_router(scheduler_router)
app.include_router(browser_router)
app.include_router(intelligence_router)
app.include_router(creative_platform_router)
app.include_router(plugins_router)
app.include_router(integrations_router)
app.include_router(gateway_router)
app.include_router(whatsapp_router)
app.include_router(telegram_router)
app.include_router(discord_router)
app.include_router(sessions_router)
app.include_router(auth_router)
app.include_router(setup_router)
app.include_router(email_webhook_router)
app.include_router(ollama_router)
app.include_router(model_manager_router)

# Include enhanced Printify router if available
if printify_enhanced_router:
    app.include_router(printify_enhanced_router)

# Add CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(",") if settings.cors_origins and settings.cors_origins != "*" else ["*"],
    allow_credentials=settings.cors_origins != "*" if settings.cors_origins else False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================
# Root-level Upload Endpoint (convenience alias)
# =====================

@app.post("/upload")
async def upload_file_root(file: UploadFile = File(...)):
    """
    Convenience upload endpoint at root level.
    Delegates to /files/upload for actual processing.
    """
    from .files import upload_file
    return await upload_file(file=file)


# =====================
# Task Queue Frontend Compatibility Endpoints
# =====================
# The frontend uses /task_queue but the backend API is at /api/tasks.
# These endpoints bridge the gap so the sidebar queue works.

@app.get("/task_queue")
async def get_task_queue_compat():
    """Compatibility endpoint: list tasks for sidebar queue."""
    try:
        from src.tools.task_queue_engine import get_task_queue_engine
        queue = get_task_queue_engine()
        tasks = queue.list_tasks(limit=100)
        # Convert Task objects to frontend format
        frontend_tasks = []
        for t in tasks:
            td = t.to_dict() if hasattr(t, 'to_dict') else t
            frontend_tasks.append({
                "id": td.get("id", ""),
                "title": (td.get("description") or "")[:80],
                "instruction": td.get("description", ""),
                "type": "general",
                "status": _map_backend_status(td.get("status", "PENDING")),
                "created": td.get("created_at", ""),
                "priority": td.get("priority", "NORMAL").lower() if isinstance(td.get("priority"), str) else "normal",
                "scheduledDate": td.get("scheduled_for"),
            })
        return {"tasks": frontend_tasks}
    except Exception as e:
        logger.warning(f"Task queue compat GET failed: {e}")
        return {"tasks": []}

@app.post("/task_queue")
async def add_task_queue_compat(request: Request):
    """Compatibility endpoint: add task from sidebar queue."""
    try:
        body = await request.json()
        from src.tools.task_queue_engine import get_task_queue_engine, TaskPriority
        queue = get_task_queue_engine()
        
        description = body.get("instruction") or body.get("title") or body.get("description", "")
        priority_str = (body.get("priority") or "normal").upper()
        scheduled_for_str = body.get("scheduledDate") or body.get("scheduled_for")
        
        # Convert priority string to enum
        try:
            priority = TaskPriority[priority_str]
        except (KeyError, ValueError):
            priority = TaskPriority.NORMAL
        
        # Convert scheduled_for string to datetime
        scheduled_for = None
        if scheduled_for_str:
            try:
                from datetime import datetime as _datetime
                scheduled_for = _datetime.fromisoformat(scheduled_for_str.replace("Z", "+00:00"))
            except Exception:
                pass
        
        task = queue.create_task(
            description=description,
            priority=priority,
            scheduled_for=scheduled_for,
        )
        return {"success": True, "task_id": task.id if hasattr(task, 'id') else str(task)}
    except Exception as e:
        logger.warning(f"Task queue compat POST failed: {e}")
        return {"success": False, "error": str(e)}  # Report failure to frontend

@app.delete("/task_queue/{task_id}")
async def delete_task_queue_compat(task_id: str):
    """Compatibility endpoint: delete task from sidebar queue."""
    try:
        from src.tools.task_queue_engine import get_task_queue_engine
        queue = get_task_queue_engine()
        queue.delete_task(task_id)
        return {"success": True}
    except Exception as e:
        logger.warning(f"Task queue compat DELETE failed: {e}")
        return {"success": True}

def _map_backend_status(status: str) -> str:
    """Map backend task status to frontend format."""
    mapping = {
        "PENDING": "queued",
        "SCHEDULED": "scheduled",
        "PLANNING": "queued",
        "READY": "queued",
        "RUNNING": "running",
        "PAUSED": "queued",
        "COMPLETED": "completed",
        "FAILED": "failed",
        "CANCELLED": "cancelled",
    }
    return mapping.get(str(status).upper(), "queued")


# Pydantic models
class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = "default"
    local_mode: Optional[bool] = False


class ChatResponse(BaseModel):
    response: str
    type: str
    session_id: str
    plan: Optional[Dict[str, Any]] = None
    results: Optional[List[Dict[str, Any]]] = None


class VoiceRequest(BaseModel):
    audio_base64: str
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    format: Optional[str] = "webm"


class TranscribeRequest(BaseModel):
    """Request for speech-to-text only."""
    audio_base64: str
    format: Optional[str] = "webm"
    language: Optional[str] = None


class WorkflowRequest(BaseModel):
    workflow: List[Dict[str, Any]]
    context: Optional[Dict[str, Any]] = None


# Dependency to get orchestrator
def get_orchestrator() -> AgentOrchestrator:
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    return orchestrator


def is_first_run() -> bool:
    """Check if this is first run (no Anthropic API key configured)."""
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    return not anthropic_key or anthropic_key.strip() == ""


# Routes
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the web chat interface, or redirect to onboarding if first run."""
    
    # Check if first run
    if is_first_run():
        return RedirectResponse(url="/onboarding", status_code=302)
    
    web_path = Path(__file__).parent.parent / "web" / "chat.html"
    if web_path.exists():
        content = web_path.read_text()
        return Response(
            content=content,
            media_type="text/html",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    return """
    <html>
        <body>
            <h1>Otto Universal API</h1>
            <p>API is running. Web interface not found.</p>
            <p>API Docs: <a href="/docs">/docs</a></p>
        </body>
    </html>
    """


def serve_html_page(filename: str) -> Response:
    """Generic HTML page server."""
    web_path = Path(__file__).parent.parent / "web" / filename
    if web_path.exists():
        return Response(
            content=web_path.read_text(),
            media_type="text/html",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    return HTMLResponse(content=f"<html><body><h1>{filename} not found</h1></body></html>", status_code=404)


@app.get("/onboarding", response_class=HTMLResponse)
async def onboarding_page():
    """Serve the onboarding wizard."""
    return serve_html_page("onboarding.html")


@app.get("/setup")
async def setup_redirect():
    """Redirect to the setup wizard."""
    return RedirectResponse(url="/api/setup/")


@app.get("/{page}.html", response_class=HTMLResponse)
async def html_pages(page: str):
    """Serve HTML pages from web directory."""
    allowed_pages = ["chat", "settings", "files", "agents", "workflows", "onboarding"]
    if page in allowed_pages:
        return serve_html_page(f"{page}.html")
    raise HTTPException(status_code=404, detail="Page not found")


@app.get("/api")
async def api_root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "Otto Universal API is running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """
    Enhanced health check with system information.
    
    Returns:
        - status: Overall health status (healthy, degraded, unhealthy)
        - version: Otto version
        - uptime: Server uptime
        - services: Status of core services
        - resources: System resource usage (if psutil available)
    """
    start_time = getattr(app.state, 'start_time', datetime.now())
    uptime_seconds = (datetime.now() - start_time).total_seconds()
    
    # Check services
    orchestrator_healthy = hasattr(app.state, 'orchestrator') and app.state.orchestrator is not None
    
    # Get tool count
    tool_count = 0
    try:
        if orchestrator_healthy and hasattr(app.state.orchestrator, 'tool_registry'):
            tools = app.state.orchestrator.tool_registry.list_tools()
            tool_count = len(tools) if tools else 0
    except Exception:
        pass
    
    # System resources (optional)
    resources = {}
    try:
        import psutil
        mem = psutil.virtual_memory()
        resources = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": mem.percent,
            "memory_available_gb": round(mem.available / (1024**3), 2)
        }
    except ImportError:
        resources = {"note": "psutil not installed for detailed metrics"}
    
    # Determine overall status
    status = "healthy"
    if not orchestrator_healthy:
        status = "degraded"
    
    return {
        "status": status,
        "version": "2.0.0",
        "codename": "Universal",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": round(uptime_seconds, 2),
        "uptime_human": f"{int(uptime_seconds // 3600)}h {int((uptime_seconds % 3600) // 60)}m",
        "services": {
            "orchestrator": "active" if orchestrator_healthy else "inactive",
            "tools": f"{tool_count} registered"
        },
        "resources": resources,
        "endpoints": {
            "chat": "/chat",
            "stream": "/chat/stream",
            "docs": "/docs"
        }
    }


@app.get("/health/detailed")
async def health_detailed():
    """
    Detailed health check with all component statuses.
    OpenClaw-style comprehensive health endpoint.
    """
    from ..core.slash_commands import get_slash_processor
    
    checks = {}
    warnings = []
    
    # API check
    checks["api"] = {"status": "healthy", "message": "API responding"}
    
    # Orchestrator check
    orchestrator = getattr(app.state, 'orchestrator', None)
    if orchestrator:
        checks["orchestrator"] = {"status": "healthy", "message": "AI processing available"}
    else:
        checks["orchestrator"] = {"status": "unavailable", "message": "Orchestrator not initialized"}
        warnings.append("Orchestrator not available")
    
    # Database/Storage check
    data_dir = Path("data")
    if data_dir.exists():
        checks["storage"] = {"status": "healthy", "message": f"Data directory accessible"}
    else:
        checks["storage"] = {"status": "warning", "message": "Data directory missing"}
        warnings.append("Data directory not found")
    
    # Memory check
    try:
        import psutil
        mem = psutil.virtual_memory()
        if mem.percent < 80:
            checks["memory"] = {"status": "healthy", "usage_percent": mem.percent}
        elif mem.percent < 95:
            checks["memory"] = {"status": "warning", "usage_percent": mem.percent}
            warnings.append(f"High memory usage: {mem.percent}%")
        else:
            checks["memory"] = {"status": "critical", "usage_percent": mem.percent}
            warnings.append(f"Critical memory usage: {mem.percent}%")
        
        # Disk check  
        disk = psutil.disk_usage('/')
        if disk.percent < 80:
            checks["disk"] = {"status": "healthy", "usage_percent": disk.percent}
        elif disk.percent < 95:
            checks["disk"] = {"status": "warning", "usage_percent": disk.percent}
            warnings.append(f"High disk usage: {disk.percent}%")
        else:
            checks["disk"] = {"status": "critical", "usage_percent": disk.percent}
    except ImportError:
        checks["system"] = {"status": "unknown", "message": "psutil not installed"}
    
    # Tools check
    try:
        if orchestrator and hasattr(orchestrator, 'tool_registry'):
            tools = orchestrator.tool_registry.list_tools()
            checks["tools"] = {"status": "healthy", "count": len(tools) if tools else 0}
        else:
            checks["tools"] = {"status": "unavailable", "message": "Tool registry not initialized"}
    except Exception as e:
        checks["tools"] = {"status": "error", "message": str(e)}
    
    # Determine overall status
    statuses = [c.get("status", "unknown") for c in checks.values()]
    if "critical" in statuses:
        overall = "unhealthy"
    elif "error" in statuses or "unavailable" in statuses:
        overall = "degraded"
    elif "warning" in statuses:
        overall = "warning"
    else:
        overall = "healthy"
    
    return {
        "status": overall,
        "timestamp": datetime.now().isoformat(),
        "checks": checks,
        "warnings": warnings,
        "version": "2.0.0"
    }


@app.get("/api/tasks/background")
async def get_background_tasks():
    """Get status of all background tasks."""
    from ..core.background_tasks import get_task_manager
    task_manager = get_task_manager()
    return {
        "tasks": task_manager.get_all_tasks(),
        "pending": task_manager.get_pending_tasks()
    }


@app.get("/api/tasks/background/{task_id}")
async def get_background_task(task_id: str):
    """Get status of a specific background task."""
    from ..core.background_tasks import get_task_manager
    task_manager = get_task_manager()
    status = task_manager.get_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return status


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    otto: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    Process a chat message (non-streaming).
    
    Supports slash commands like /help, /status, /models, /tools, /reset.
    
    Example:
        POST /chat
        {
            "message": "Create a t-shirt design with mountains",
            "session_id": "user123",
            "user_id": "default"
        }
    """
    try:
        message = request.message.strip()
        session_id = request.session_id or "default"
        
        # Check for slash commands
        if message.startswith('/'):
            slash_processor = get_slash_processor(
                orchestrator=otto,
                tool_registry=otto.tool_registry if hasattr(otto, 'tool_registry') else None
            )
            command_result = await slash_processor.execute(message)
            
            if command_result.get("success"):
                return ChatResponse(
                    response=command_result.get("message", "Command executed"),
                    type=command_result.get("type", "slash_command"),
                    session_id=session_id
                )
            else:
                # If slash command failed, it might be an unknown command
                # Let the orchestrator handle it as a regular message
                error = command_result.get("error", "")
                if "Unknown command" not in error:
                    return ChatResponse(
                        response=f"Command error: {error}",
                        type="error",
                        session_id=session_id
                    )
        
        # Regular message processing
        result = await otto.process(
            message=request.message,
            context=request.context,
            session_id=request.session_id,
            user_id=request.user_id or "default"
        )
        
        return ChatResponse(**result)
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    otto: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    Process a chat message with streaming responses.
    Returns Server-Sent Events (SSE) stream.
    """
    async def generate():
        try:
            async for chunk in otto.process_streaming(
                message=request.message,
                context=request.context,
                session_id=request.session_id,
                local_mode=request.local_mode or False
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield f"data: {{\"error\": \"{str(e)}\", \"type\": \"error\"}}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/api/chat/history/{session_id}")
async def get_chat_history(
    session_id: str,
    limit: int = 50,
    otto: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    Get chat history for a session.
    
    Args:
        session_id: The session identifier
        limit: Maximum number of messages to return
        
    Returns:
        List of messages with role and content
    """
    try:
        history = await otto.memory_agent.get_session_history(
            session_id=session_id,
            limit=limit
        )
        return {"messages": history, "session_id": session_id}
    except Exception as e:
        logger.error(f"Failed to get chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/chat/history/{session_id}")
async def clear_chat_history(
    session_id: str,
    otto: AgentOrchestrator = Depends(get_orchestrator)
):
    """Clear chat history for a session."""
    try:
        success = await otto.memory_agent.clear_session(session_id)
        return {"success": success, "session_id": session_id}
    except Exception as e:
        logger.error(f"Failed to clear chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memory/stats")
async def get_memory_stats(otto: AgentOrchestrator = Depends(get_orchestrator)):
    """Get memory usage statistics."""
    return otto.memory_agent.get_stats()


@app.post("/transcribe")
async def transcribe_audio(
    request: TranscribeRequest,
    otto: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    Transcribe audio to text (speech-to-text only).
    
    Returns just the transcribed text without processing or TTS response.
    Useful for voice input that user wants to review/edit before sending.
    """
    try:
        import base64
        from ..voice.speech_to_text import SpeechToText
        
        # Check if OpenAI client is available
        if otto.openai is None:
            raise HTTPException(
                status_code=503,
                detail="Voice transcription requires OpenAI API key. Please set OPENAI_API_KEY in your environment."
            )
        
        # Decode audio
        audio_data = base64.b64decode(request.audio_base64)
        
        # Create STT instance
        stt = SpeechToText(otto.openai)
        
        # Transcribe
        result = await stt.transcribe(
            audio_data=audio_data,
            format=request.format or "webm",
            language=request.language
        )
        
        return {
            "success": result.get("success", False),
            "text": result.get("text", ""),
            "language": result.get("language"),
            "duration": result.get("duration"),
            "error": result.get("error")
        }
        
    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/voice")
async def voice(
    request: VoiceRequest,
    otto: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    Process voice input and return voice output.
    
    Expects base64-encoded audio.
    Full voice pipeline: Speech -> Text -> AI -> Text -> Speech
    """
    try:
        import base64
        
        # Decode audio
        audio_data = base64.b64decode(request.audio_base64)
        
        result = await otto.process_voice(
            audio_data=audio_data,
            context=request.context,
            session_id=request.session_id
        )
        
        # Encode audio response
        if "audio" in result:
            result["audio"] = base64.b64encode(result["audio"]).decode()
        
        return result
        
    except Exception as e:
        logger.error(f"Voice error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workflow")
async def execute_workflow(
    request: WorkflowRequest,
    otto: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    Execute a predefined workflow.
    
    Example:
        POST /workflow
        {
            "workflow": [
                {"tool": "generate_design", "params": {"theme": "nature"}},
                {"tool": "create_mockup", "params": {"product": "t-shirt"}}
            ]
        }
    """
    try:
        results = await otto.execute_workflow(
            workflow=request.workflow,
            context=request.context
        )
        
        return {"results": results}
        
    except Exception as e:
        logger.error(f"Workflow error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/capabilities")
async def get_capabilities(otto: AgentOrchestrator = Depends(get_orchestrator)):
    """Get Otto's capabilities and available tools."""
    return otto.get_capabilities()


@app.get("/tools")
async def list_tools(
    category: Optional[str] = None,
    otto: AgentOrchestrator = Depends(get_orchestrator)
):
    """List available tools."""
    return {
        "tools": otto.tool_registry.list_tools(category=category),
        "categories": otto.tool_registry.get_categories()
    }


# =====================
# AI File Editor API
# =====================

class AIEditRequest(BaseModel):
    file_path: str
    instruction: str
    model: str = "qwen"

class AIReviewRequest(BaseModel):
    file_path: str
    model: str = "qwen"

class AIRefactorRequest(BaseModel):
    file_path: str
    refactor_type: str = "general"
    model: str = "qwen"


@app.get("/api/files/tree")
async def get_file_tree(dir: Optional[str] = None):
    """Get file tree for the project."""
    try:
        project_root = Path(__file__).parent.parent.parent
        
        if dir:
            target = project_root / dir
        else:
            target = project_root
        
        # Security: ensure target is within project root
        try:
            target.resolve().relative_to(project_root.resolve())
        except ValueError:
            return {"files": [], "error": "Access denied: path outside project"}
        
        if not target.exists():
            return {"files": [], "error": "Directory not found"}
        
        # Only show certain directories and files
        allowed_dirs = {'src', 'skills', 'config', 'scripts', 'docs', 'examples'}
        allowed_extensions = {'.py', '.js', '.ts', '.html', '.css', '.json', '.yaml', '.yml', '.md', '.txt', '.sh'}
        
        files = []
        items = sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        
        for item in items[:50]:  # Limit to 50 items
            # Skip hidden and cache directories
            if item.name.startswith(('.', '__pycache__')):
                continue
            
            if item.is_dir():
                # At root, only show allowed directories
                if target == project_root and item.name not in allowed_dirs:
                    continue
                files.append({
                    "name": item.name + "/",
                    "path": str(item.relative_to(project_root)),
                    "is_dir": True
                })
            else:
                if item.suffix in allowed_extensions:
                    files.append({
                        "name": item.name,
                        "path": str(item.relative_to(project_root)),
                        "is_dir": False
                    })
        
        return {"files": files, "directory": str(target.relative_to(project_root) if dir else ".")}
        
    except Exception as e:
        logger.error(f"File tree error: {e}")
        return {"files": [], "error": str(e)}


@app.get("/api/files/content")
async def get_file_content(path: str):
    """Get content of a file."""
    try:
        project_root = Path(__file__).parent.parent.parent
        file_path = project_root / path
        
        # Security: ensure path is within project
        try:
            file_path.resolve().relative_to(project_root.resolve())
        except ValueError:
            return {"content": None, "error": "Access denied: path outside project"}
        
        if not file_path.exists():
            return {"content": None, "error": "File not found"}
        
        if file_path.stat().st_size > 500000:  # 500KB limit
            return {"content": None, "error": "File too large"}
        
        with open(file_path, 'r', errors='ignore') as f:
            content = f.read()
        
        return {"content": content, "path": path, "lines": len(content.splitlines())}
        
    except Exception as e:
        logger.error(f"File content error: {e}")
        return {"content": None, "error": str(e)}


@app.post("/api/ai/edit")
async def ai_edit_file(request: AIEditRequest):
    """Use AI to edit a file based on instructions."""
    try:
        from ..tools.ai_file_editor import AIFileEditor
        
        editor = AIFileEditor()
        result = await editor.ai_edit_file(
            file_path=request.file_path,
            instruction=request.instruction,
            model=request.model
        )
        
        return result
        
    except Exception as e:
        logger.error(f"AI edit error: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/ai/review")
async def ai_review_code(request: AIReviewRequest):
    """Use AI to review code."""
    try:
        from ..tools.ai_file_editor import AIFileEditor
        
        editor = AIFileEditor()
        result = await editor.ai_code_review(
            file_path=request.file_path,
            model=request.model
        )
        
        return result
        
    except Exception as e:
        logger.error(f"AI review error: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/ai/explain")
async def ai_explain_code(request: AIReviewRequest):
    """Use AI to explain code."""
    try:
        from ..tools.ai_file_editor import AIFileEditor
        
        editor = AIFileEditor()
        result = await editor.ai_explain_code(
            file_path=request.file_path,
            model=request.model
        )
        
        return result
        
    except Exception as e:
        logger.error(f"AI explain error: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/ai/refactor")
async def ai_refactor_code(request: AIRefactorRequest):
    """Use AI to refactor code."""
    try:
        from ..tools.ai_file_editor import AIFileEditor
        
        editor = AIFileEditor()
        result = await editor.ai_refactor_code(
            file_path=request.file_path,
            refactor_type=request.refactor_type,
            model=request.model
        )
        
        return result
        
    except Exception as e:
        logger.error(f"AI refactor error: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/ai/fix")
async def ai_fix_code(request: AIReviewRequest):
    """Use AI to fix bugs in code."""
    try:
        from ..tools.ai_file_editor import AIFileEditor
        
        editor = AIFileEditor()
        result = await editor.ai_fix_code(
            file_path=request.file_path,
            model=request.model
        )
        
        return result
        
    except Exception as e:
        logger.error(f"AI fix error: {e}")
        return {"success": False, "error": str(e)}


# =====================
# Universal Media Editor API
# =====================

class MediaEditRequest(BaseModel):
    file_url: str
    instruction: str
    media_type: Optional[str] = None


@app.post("/api/media/edit")
async def edit_media(request: MediaEditRequest):
    """
    Universal media editor - edit images, videos, audio, 3D models with AI.
    
    Just describe what you want to do and it figures out the right models.
    
    Examples:
    - "remove background" on an image
    - "upscale 4x" on an image
    - "animate this" on an image → creates video
    - "separate vocals" on audio
    - "make slow motion" on video
    - "convert to 3D" on an image
    """
    try:
        from ..tools.universal_editor import UniversalEditor
        
        editor = UniversalEditor()
        result = await editor.edit(
            file_path=request.file_url,
            instruction=request.instruction
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Media edit error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/media/capabilities")
async def get_media_capabilities(media_type: Optional[str] = None):
    """Get available media editing capabilities."""
    try:
        from ..tools.universal_editor import UniversalEditor
        
        editor = UniversalEditor()
        result = await editor.list_capabilities(media_type=media_type)
        
        return result
        
    except Exception as e:
        return {"error": str(e)}


# =========================================================================
# Browser Proxy API - For embedding external sites in iframe
# =========================================================================

@app.get("/api/browser/proxy")
async def browser_proxy(url: str):
    """Proxy external websites to bypass X-Frame-Options restrictions."""
    import httpx
    from urllib.parse import urlparse
    import ipaddress
    
    try:
        # Validate URL scheme
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return Response(
                content="<html><body><h1>Invalid URL scheme</h1></body></html>",
                media_type="text/html",
                status_code=400
            )
        
        # Block private/internal IPs to prevent SSRF
        import socket
        try:
            hostname = parsed.hostname
            if hostname:
                resolved_ip = socket.gethostbyname(hostname)
                ip = ipaddress.ip_address(resolved_ip)
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                    return Response(
                        content="<html><body><h1>Access denied</h1><p>Cannot proxy to internal addresses.</p></body></html>",
                        media_type="text/html",
                        status_code=403
                    )
        except (socket.gaierror, ValueError):
            return Response(
                content="<html><body><h1>Invalid hostname</h1></body></html>",
                media_type="text/html",
                status_code=400
            )
        
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = await client.get(url, headers=headers)
            
            # Modify the HTML to fix relative URLs
            content = response.text
            from urllib.parse import urljoin, urlparse
            
            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            
            # Inject base tag to fix relative URLs
            if "<head>" in content.lower():
                content = content.replace("<head>", f'<head><base href="{base_url}/">', 1)
                content = content.replace("<HEAD>", f'<HEAD><base href="{base_url}/">', 1)
            
            return Response(
                content=content,
                media_type="text/html",
                headers={"X-Frame-Options": "ALLOWALL"}
            )
    except Exception as e:
        logger.error(f"Browser proxy error: {e}")
        return Response(
            content=f"<html><body><h1>Error loading page</h1><p>{str(e)}</p></body></html>",
            media_type="text/html"
        )


@app.get("/api/browser/history")
async def get_browser_history():
    """Get browser history from backend."""
    return {"success": True, "history": []}


# =========================================================================
# Import API - For contacts and schedule import
# =========================================================================

@app.post("/api/import/contacts")
async def import_contacts(file: UploadFile = File(...)):
    """Import contacts from spreadsheet (CSV, Excel)."""
    import csv
    import io
    
    try:
        content = await file.read()
        contacts = []
        
        if file.filename.endswith('.csv'):
            # Parse CSV
            text = content.decode('utf-8')
            reader = csv.DictReader(io.StringIO(text))
            for row in reader:
                contact = {
                    "name": row.get("name") or row.get("Name") or row.get("full_name") or "",
                    "email": row.get("email") or row.get("Email") or row.get("e-mail") or "",
                    "phone": row.get("phone") or row.get("Phone") or row.get("telephone") or "",
                    "company": row.get("company") or row.get("Company") or row.get("organization") or "",
                    "notes": row.get("notes") or row.get("Notes") or ""
                }
                if contact["name"] or contact["email"]:
                    contacts.append(contact)
        
        elif file.filename.endswith(('.xlsx', '.xls')):
            # Parse Excel
            try:
                import openpyxl
                from io import BytesIO
                
                wb = openpyxl.load_workbook(BytesIO(content))
                ws = wb.active
                
                headers = [cell.value for cell in ws[1]]
                for row in ws.iter_rows(min_row=2, values_only=True):
                    row_dict = dict(zip(headers, row))
                    contact = {
                        "name": row_dict.get("name") or row_dict.get("Name") or "",
                        "email": row_dict.get("email") or row_dict.get("Email") or "",
                        "phone": row_dict.get("phone") or row_dict.get("Phone") or "",
                        "company": row_dict.get("company") or row_dict.get("Company") or "",
                        "notes": row_dict.get("notes") or row_dict.get("Notes") or ""
                    }
                    if contact["name"] or contact["email"]:
                        contacts.append(contact)
            except ImportError:
                return {"success": False, "error": "openpyxl not installed for Excel support"}
        
        return {
            "success": True,
            "imported": len(contacts),
            "contacts": contacts
        }
        
    except Exception as e:
        logger.error(f"Contact import error: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/import/schedule")
async def import_schedule(file: UploadFile = File(...)):
    """Import schedule/calendar from spreadsheet (CSV, Excel)."""
    import csv
    import io
    from datetime import datetime
    
    try:
        content = await file.read()
        events = []
        
        if file.filename.endswith('.csv'):
            text = content.decode('utf-8')
            reader = csv.DictReader(io.StringIO(text))
            for row in reader:
                event = {
                    "title": row.get("title") or row.get("Title") or row.get("event") or row.get("Event") or "",
                    "date": row.get("date") or row.get("Date") or row.get("scheduled_date") or "",
                    "time": row.get("time") or row.get("Time") or row.get("scheduled_time") or "",
                    "description": row.get("description") or row.get("Description") or row.get("notes") or "",
                    "repeat": row.get("repeat") or row.get("Repeat") or "once"
                }
                if event["title"] and event["date"]:
                    events.append(event)
        
        elif file.filename.endswith(('.xlsx', '.xls')):
            try:
                import openpyxl
                from io import BytesIO
                
                wb = openpyxl.load_workbook(BytesIO(content))
                ws = wb.active
                
                headers = [cell.value for cell in ws[1]]
                for row in ws.iter_rows(min_row=2, values_only=True):
                    row_dict = dict(zip(headers, row))
                    event = {
                        "title": row_dict.get("title") or row_dict.get("Title") or "",
                        "date": str(row_dict.get("date") or row_dict.get("Date") or ""),
                        "time": str(row_dict.get("time") or row_dict.get("Time") or ""),  
                        "description": row_dict.get("description") or row_dict.get("Description") or "",
                        "repeat": row_dict.get("repeat") or "once"
                    }
                    if event["title"] and event["date"]:
                        events.append(event)
            except ImportError:
                return {"success": False, "error": "openpyxl not installed for Excel support"}
        
        return {
            "success": True,
            "imported": len(events),
            "events": events
        }
        
    except Exception as e:
        logger.error(f"Schedule import error: {e}")
        return {"success": False, "error": str(e)}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time communication.
    
    Supports streaming responses and real-time voice.
    """
    await websocket.accept()
    logger.info("WebSocket client connected")
    
    otto = get_orchestrator()
    session_id = None
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            message_type = data.get("type", "chat")
            session_id = data.get("session_id", session_id)
            
            if message_type == "chat":
                # Process chat message
                result = await otto.process(
                    message=data.get("message", ""),
                    context=data.get("context"),
                    session_id=session_id
                )
                
                # Send response
                await websocket.send_json({
                    "type": "response",
                    **result
                })
            
            elif message_type == "voice":
                # Process voice (audio should be base64)
                import base64
                audio_b64 = data.get("audio")
                if not audio_b64:
                    await websocket.send_json({"type": "error", "error": "Missing audio data"})
                    continue
                audio_data = base64.b64decode(audio_b64)
                
                result = await otto.process_voice(
                    audio_data=audio_data,
                    context=data.get("context"),
                    session_id=session_id
                )
                
                # Encode audio response
                if "audio" in result:
                    result["audio"] = base64.b64encode(result["audio"]).decode()
                
                await websocket.send_json({
                    "type": "voice_response",
                    **result
                })
            
            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "error": str(e)
            })
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug_mode,
        workers=1 if settings.debug_mode else settings.api_workers
    )
