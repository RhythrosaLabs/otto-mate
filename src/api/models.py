"""
AI Models API - Browse and Run AI Models
========================================

Provides endpoints to discover and run AI models from Replicate.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/models", tags=["AI Models"])

# Will be set by main.py
_orchestrator = None


def set_orchestrator(orchestrator):
    global _orchestrator
    _orchestrator = orchestrator


def get_orchestrator():
    if _orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    return _orchestrator


class ModelRunRequest(BaseModel):
    model: str
    inputs: Dict[str, Any]
    

class ModelSearchRequest(BaseModel):
    query: str
    limit: int = 20


@router.get("/")
async def list_models():
    """List popular AI model categories and shortcuts."""
    otto = get_orchestrator()
    
    # Default response
    default_response = {
        "models": [],
        "categories": [
            {"id": "image", "name": "Image Generation", "icon": "🎨"},
            {"id": "text", "name": "Text & Language", "icon": "📝"},
            {"id": "audio", "name": "Audio & Music", "icon": "🎵"},
            {"id": "video", "name": "Video Generation", "icon": "🎬"},
            {"id": "vision", "name": "Vision & Analysis", "icon": "👁️"},
        ],
        "popular": [
            {"name": "flux-pro", "description": "Best image generation", "category": "image"},
            {"name": "sdxl", "description": "Stable Diffusion XL", "category": "image"},
            {"name": "whisper", "description": "Speech to text", "category": "audio"},
            {"name": "musicgen", "description": "Music generation", "category": "audio"},
        ],
        "status": "ready"
    }
    
    # Try to get actual collections from Replicate
    try:
        tool = otto.tool_registry.get_tool("replicate_list_collections")
        if tool:
            collections = await tool["function"]()
            return {
                **default_response,
                "collections": collections.get("collections", []),
                "status": "connected"
            }
    except Exception as e:
        logger.warning(f"Could not fetch Replicate collections: {e}")
    
    return default_response


@router.get("/search")
async def search_models(query: str, limit: int = 20):
    """Search for AI models by query."""
    otto = get_orchestrator()
    
    try:
        tool = otto.tool_registry.get_tool("replicate_search_models")
        if tool:
            result = await tool["function"](query=query)
            return result
        else:
            return {"results": [], "error": "Search not available"}
    except Exception as e:
        logger.error(f"Model search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info/{owner}/{model}")
async def get_model_info(owner: str, model: str):
    """Get detailed information about a specific model."""
    otto = get_orchestrator()
    model_name = f"{owner}/{model}"
    
    try:
        tool = otto.tool_registry.get_tool("replicate_get_model_info")
        if tool:
            result = await tool["function"](model_name=model_name)
            return result
        
        return {"error": "Model info not available", "model": model_name}
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run")
async def run_model(request: ModelRunRequest):
    """Run an AI model with the given inputs."""
    otto = get_orchestrator()
    
    try:
        tool = otto.tool_registry.get_tool("replicate_run_model")
        if tool:
            result = await tool["function"](
                model=request.model,
                inputs=request.inputs
            )
            return result
        
        return {"error": "Model execution not available"}
    except Exception as e:
        logger.error(f"Model run failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections")
async def list_collections():
    """List all model collections from Replicate."""
    otto = get_orchestrator()
    
    try:
        tool = otto.tool_registry.get_tool("replicate_list_collections")
        if tool:
            result = await tool["function"]()
            return result
        
        return {"collections": [], "error": "Collections not available"}
    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))
