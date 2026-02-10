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
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv

from ..core.agent_orchestrator import AgentOrchestrator
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
            **settings.dict(),
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
    
    yield
    
    # Cleanup
    logger.info("Shutting down...")
    task_scheduler.stop()


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

# Include enhanced Printify router if available
if printify_enhanced_router:
    app.include_router(printify_enhanced_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================
# Root-level Upload Endpoint (convenience alias)
# =====================

from fastapi import UploadFile, File

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

import json as _json
from datetime import datetime as _dt

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
        return {"success": True}  # Don't break frontend

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
    from fastapi.responses import RedirectResponse, Response
    
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


def serve_html_page(filename: str) -> str:
    """Generic HTML page server."""
    from fastapi.responses import Response
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
    return f"<html><body><h1>{filename} not found</h1></body></html>"


@app.get("/onboarding", response_class=HTMLResponse)
async def onboarding_page():
    """Serve the onboarding wizard."""
    return serve_html_page("onboarding.html")


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
    """Simple health check."""
    return {
        "status": "healthy",
        "timestamp": str(datetime.now())
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
    
    Example:
        POST /chat
        {
            "message": "Create a t-shirt design with mountains",
            "session_id": "user123",
            "user_id": "default"
        }
    """
    try:
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
                session_id=request.session_id
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield f"data: {{\"error\": \"{str(e)}\", \"type\": \"error\"}}\n\n"
    
    from fastapi.responses import StreamingResponse
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
        file_path.resolve().relative_to(project_root.resolve())
        
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
                    message=data["message"],
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
                audio_data = base64.b64decode(data["audio"])
                
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
        except:
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
