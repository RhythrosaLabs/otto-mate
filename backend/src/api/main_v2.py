"""
Otto Universal API - New Modular Main Entry Point
================================================

Clean API-only server with versioned routes and service layer.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Import v1 API routes
from backend.src.api.v1 import router as v1_router
from backend.src.api.orchestrator_bridge import get_orchestrator_bridge

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("🚀 Otto Universal API v2 starting...")
    logger.info("✅ Modular architecture enabled")
    
    # Initialize orchestrator bridge
    try:
        bridge = get_orchestrator_bridge()
        logger.info("✅ Orchestrator bridge initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize orchestrator: {e}")
        raise
    
    yield
    logger.info("👋 Otto Universal API v2 shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Otto Universal API",
    description="AI Assistant API with modular architecture",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 API routes
app.include_router(v1_router, prefix="/api/v1")

# Health endpoint
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "architecture": "modular"
    }

@app.get("/api")
async def api_info():
    """API information."""
    return {
        "name": "Otto Universal API",
        "version": "2.0.0",
        "architecture": "modular",
        "available_versions": ["v1"],
        "endpoints": {
            "health": "/health",
            "api_info": "/api",
            "v1": "/api/v1",
            "docs": "/docs",
            "openapi": "/openapi.json"
        }
    }

# Serve frontend static files (production)
frontend_path = Path(__file__).parent.parent.parent.parent / "frontends" / "vanilla-js" / "public"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="static")
    logger.info(f"📁 Serving frontend from: {frontend_path}")
else:
    logger.warning(f"⚠️ Frontend path not found: {frontend_path}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.src.api.main_v2:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
