"""
Projects API - Project and folder management endpoints
======================================================
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

from ..core.project_manager import get_project_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["projects"])


class CreateProjectRequest(BaseModel):
    name: str
    description: str = ""
    color: str = "#3b82f6"
    icon: str = "📁"
    tags: List[str] = []


class UpdateProjectRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    tags: Optional[List[str]] = None


class AddChatToProjectRequest(BaseModel):
    session_id: str


@router.get("/")
async def list_projects():
    """List all projects."""
    try:
        pm = get_project_manager()
        projects = pm.list_projects()
        return {"projects": projects}
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_project(request: CreateProjectRequest):
    """Create a new project."""
    try:
        pm = get_project_manager()
        project = pm.create_project(
            name=request.name,
            description=request.description,
            color=request.color,
            icon=request.icon,
            tags=request.tags
        )
        return {"project": project.to_dict()}
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}")
async def get_project(project_id: str):
    """Get a specific project."""
    try:
        pm = get_project_manager()
        project = pm.get_project(project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {"project": project.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{project_id}")
async def update_project(project_id: str, request: UpdateProjectRequest):
    """Update a project."""
    try:
        pm = get_project_manager()
        project = pm.update_project(
            project_id=project_id,
            name=request.name,
            description=request.description,
            color=request.color,
            icon=request.icon,
            tags=request.tags
        )
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {"project": project.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Delete a project."""
    try:
        pm = get_project_manager()
        success = pm.delete_project(project_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/chats")
async def add_chat_to_project(project_id: str, request: AddChatToProjectRequest):
    """Add a chat session to a project."""
    try:
        pm = get_project_manager()
        success = pm.add_chat_to_project(project_id, request.session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding chat to project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chats/{session_id}")
async def remove_chat_from_project(session_id: str):
    """Remove a chat from its project."""
    try:
        pm = get_project_manager()
        success = pm.remove_chat_from_project(session_id)
        return {"success": success}
    except Exception as e:
        logger.error(f"Error removing chat from project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chats/{session_id}/project")
async def get_chat_project(session_id: str):
    """Get the project for a specific chat."""
    try:
        pm = get_project_manager()
        project = pm.get_project_for_session(session_id)
        
        if not project:
            return {"project": None}
        
        return {"project": project.to_dict()}
    except Exception as e:
        logger.error(f"Error getting chat project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/chats")
async def get_project_chats(project_id: str):
    """Get all chats in a project."""
    try:
        pm = get_project_manager()
        chat_sessions = pm.get_project_chats(project_id)
        return {"session_ids": chat_sessions}
    except Exception as e:
        logger.error(f"Error getting project chats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/")
async def search_projects(q: str):
    """Search projects."""
    try:
        pm = get_project_manager()
        projects = pm.search_projects(q)
        return {"projects": projects}
    except Exception as e:
        logger.error(f"Error searching projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary")
async def get_project_stats():
    """Get project statistics."""
    try:
        pm = get_project_manager()
        stats = pm.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting project stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
