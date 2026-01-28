"""
Otto Universal API - FastAPI Application
========================================

Main API server providing REST and WebSocket endpoints.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
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

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global orchestrator instance
orchestrator: Optional[AgentOrchestrator] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup on startup/shutdown."""
    global orchestrator
    
    settings = get_settings()
    
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
    
    logger.info("Otto Universal API is ready!")
    logger.info("✨ Autonomous Business Operations: ACTIVE")
    yield
    
    # Cleanup
    logger.info("Shutting down...")


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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


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
    from fastapi.responses import RedirectResponse
    
    # Check if first run
    if is_first_run():
        return RedirectResponse(url="/onboarding", status_code=302)
    
    web_path = Path(__file__).parent.parent / "web" / "chat.html"
    if web_path.exists():
        return web_path.read_text()
    return """
    <html>
        <body>
            <h1>Otto Universal API</h1>
            <p>API is running. Web interface not found.</p>
            <p>API Docs: <a href="/docs">/docs</a></p>
        </body>
    </html>
    """


@app.get("/settings-page", response_class=HTMLResponse)
async def settings_page():
    """Serve the settings page."""
    web_path = Path(__file__).parent.parent / "web" / "settings.html"
    if web_path.exists():
        return web_path.read_text()
    return "<html><body><h1>Settings page not found</h1></body></html>"


@app.get("/files-page", response_class=HTMLResponse)
async def files_page():
    """Serve the files management page."""
    web_path = Path(__file__).parent.parent / "web" / "files.html"
    if web_path.exists():
        return web_path.read_text()
    return "<html><body><h1>Files page not found</h1></body></html>"


@app.get("/chat.html", response_class=HTMLResponse)
async def chat_interface():
    """Serve the full-featured Otto Universal interface."""
    web_path = Path(__file__).parent.parent / "web" / "chat.html"
    if web_path.exists():
        return web_path.read_text()
    return "<html><body><h1>Chat interface not found</h1></body></html>"


@app.get("/agents-page", response_class=HTMLResponse)
async def agents_page():
    """Serve the agents management page."""
    web_path = Path(__file__).parent.parent / "web" / "agents.html"
    if web_path.exists():
        return web_path.read_text()
    return "<html><body><h1>Agents page not found</h1></body></html>"





@app.get("/onboarding", response_class=HTMLResponse)
async def onboarding_page():
    """Serve the onboarding wizard."""
    web_path = Path(__file__).parent.parent / "web" / "onboarding.html"
    if web_path.exists():
        return web_path.read_text()
    return "<html><body><h1>Onboarding page not found</h1></body></html>"


@app.get("/agents.html", response_class=HTMLResponse)
async def agents_html():
    """Serve the agents management page."""
    web_path = Path(__file__).parent.parent / "web" / "agents.html"
    if web_path.exists():
        return web_path.read_text()
    return "<html><body><h1>Agents page not found</h1></body></html>"


@app.get("/files.html", response_class=HTMLResponse)
async def files_html():
    """Serve the files management page."""
    web_path = Path(__file__).parent.parent / "web" / "files.html"
    if web_path.exists():
        return web_path.read_text()
    return "<html><body><h1>Files page not found</h1></body></html>"


@app.get("/settings.html", response_class=HTMLResponse)
async def settings_html():
    """Serve the settings page."""
    web_path = Path(__file__).parent.parent / "web" / "settings.html"
    if web_path.exists():
        return web_path.read_text()
    return "<html><body><h1>Settings page not found</h1></body></html>"


@app.get("/onboarding.html", response_class=HTMLResponse)
async def onboarding_html():
    """Serve the onboarding wizard."""
    web_path = Path(__file__).parent.parent / "web" / "onboarding.html"
    if web_path.exists():
        return web_path.read_text()
    return "<html><body><h1>Onboarding page not found</h1></body></html>"


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
    """Detailed health check."""
    otto = get_orchestrator()
    return {
        "status": "healthy",
        "capabilities": otto.get_capabilities()
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    otto: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    Process a chat message.
    
    Example:
        POST /chat
        {
            "message": "Create a t-shirt design with mountains",
            "session_id": "user123"
        }
    """
    try:
        result = await otto.process(
            message=request.message,
            context=request.context,
            session_id=request.session_id
        )
        
        return ChatResponse(**result)
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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


@app.post("/voice")
async def voice(
    request: VoiceRequest,
    otto: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    Process voice input and return voice output.
    
    Expects base64-encoded audio.
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
