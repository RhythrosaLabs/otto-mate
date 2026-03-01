"""
Creative Platform API
=====================

REST API endpoints for managing autonomous creative projects.
"""

import uuid
from typing import Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from ..core.creative_platform import (
    get_creative_platform,
    init_creative_platform,
    CreativePlatformEngine,
    ProjectStatus,
    MultiProjectScheduler
)

router = APIRouter(prefix="/api/creative", tags=["creative_platform"])


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateProjectRequest(BaseModel):
    """Request to create a new creative project."""
    goal: str = Field(..., description="The creative goal for the project")
    project_id: Optional[str] = Field(None, description="Custom project ID (optional)")
    initial_assets: Optional[dict] = Field(None, description="Pre-existing assets to use")


class CreateProjectResponse(BaseModel):
    """Response after creating a project."""
    project_id: str
    status: str
    message: str


class ProjectStatusResponse(BaseModel):
    """Project status details."""
    project_id: str
    goal: str
    status: str
    current_step: str
    retry_count: int
    products_created: int
    assets_generated: int
    errors: List[str]
    audit_flags: List[str]
    created_at: Optional[str]
    updated_at: Optional[str]


class ProjectListItem(BaseModel):
    """Project summary for list views."""
    project_id: str
    status: str
    created_at: str
    updated_at: str


class BatchProjectRequest(BaseModel):
    """Request to create multiple projects."""
    projects: List[dict] = Field(..., description="List of {goal: str} objects")


class BatchProjectResponse(BaseModel):
    """Response for batch project creation."""
    scheduled: List[str]
    message: str


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/projects", response_model=CreateProjectResponse)
async def create_project(request: CreateProjectRequest, background_tasks: BackgroundTasks):
    """
    Create a new creative project.
    
    The project will be initialized but not started automatically.
    Use the /projects/{id}/start endpoint to begin execution.
    """
    platform = get_creative_platform()
    project_id = request.project_id or f"project-{uuid.uuid4().hex[:8]}"
    
    initial_state = {}
    if request.initial_assets:
        initial_state["assets"] = request.initial_assets
    
    await platform.create_project(project_id, request.goal, initial_state)
    
    return CreateProjectResponse(
        project_id=project_id,
        status="created",
        message=f"Project '{request.goal}' created successfully"
    )


@router.post("/projects/{project_id}/start")
async def start_project(project_id: str, background_tasks: BackgroundTasks):
    """
    Start executing a creative project.
    
    The project will run asynchronously in the background.
    """
    platform = get_creative_platform()
    
    status = platform.get_project_status(project_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")
    
    if status["status"] == ProjectStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Project is already running")
    
    result = await platform.run_project_async(project_id)
    
    return {
        "project_id": project_id,
        "status": result,
        "message": "Project started successfully"
    }


@router.post("/projects/{project_id}/run")
async def run_project_sync(project_id: str, max_steps: int = 50):
    """
    Run a project synchronously and return final state.
    
    Use this for debugging or when you need to wait for completion.
    """
    platform = get_creative_platform()
    
    status = platform.get_project_status(project_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")
    
    final_state = await platform.run_project(project_id, max_steps)
    
    return {
        "project_id": project_id,
        "status": final_state.get("status"),
        "current_step": final_state.get("current_step"),
        "products_created": len(final_state.get("printify_products", {})),
        "assets_generated": len(final_state.get("assets", {})),
        "logs": final_state.get("logs", [])[-10:],
        "errors": final_state.get("errors", [])
    }


@router.get("/projects/{project_id}", response_model=ProjectStatusResponse)
async def get_project_status(project_id: str):
    """Get the current status of a project."""
    platform = get_creative_platform()
    status = platform.get_project_status(project_id)
    
    if not status:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")
    
    return ProjectStatusResponse(**status)


@router.get("/projects/{project_id}/state")
async def get_project_full_state(project_id: str):
    """Get the complete state of a project (for debugging)."""
    platform = get_creative_platform()
    state = platform.state_store.load_state(project_id)
    
    if not state:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")
    
    return state


@router.get("/projects/{project_id}/history")
async def get_project_history(project_id: str, limit: int = 20):
    """Get the execution history of a project."""
    platform = get_creative_platform()
    history = platform.state_store.get_history(project_id, limit)
    
    if not history:
        raise HTTPException(status_code=404, detail=f"Project not found or no history: {project_id}")
    
    return {"project_id": project_id, "history": history}


@router.post("/projects/{project_id}/pause")
async def pause_project(project_id: str):
    """Pause a running project."""
    platform = get_creative_platform()
    success = platform.pause_project(project_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")
    
    return {"project_id": project_id, "status": "paused"}


@router.post("/projects/{project_id}/resume")
async def resume_project(project_id: str, background_tasks: BackgroundTasks):
    """Resume a paused project."""
    platform = get_creative_platform()
    success = platform.resume_project(project_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")
    
    # Restart execution
    await platform.run_project_async(project_id)
    
    return {"project_id": project_id, "status": "resumed"}


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project and all its data."""
    platform = get_creative_platform()
    platform.delete_project(project_id)
    
    return {"project_id": project_id, "deleted": True}


@router.get("/projects", response_model=List[ProjectListItem])
async def list_projects(status: Optional[str] = None):
    """List all projects, optionally filtered by status."""
    platform = get_creative_platform()
    projects = platform.list_projects(status)
    
    return [ProjectListItem(**p) for p in projects]


# ============================================================================
# Batch Operations
# ============================================================================

@router.post("/batch/create", response_model=BatchProjectResponse)
async def batch_create_projects(request: BatchProjectRequest):
    """Create multiple projects for batch processing."""
    platform = get_creative_platform()
    scheduler = MultiProjectScheduler(platform)
    
    projects = [
        {
            "project_id": f"batch-{uuid.uuid4().hex[:6]}",
            "goal": p.get("goal", "Creative project")
        }
        for p in request.projects
    ]
    
    scheduled = await scheduler.schedule_projects(projects)
    
    return BatchProjectResponse(
        scheduled=scheduled,
        message=f"Scheduled {len(scheduled)} projects"
    )


@router.post("/batch/run")
async def batch_run_projects(request: BatchProjectRequest, background_tasks: BackgroundTasks):
    """Create and immediately run multiple projects."""
    platform = get_creative_platform()
    scheduler = MultiProjectScheduler(platform)
    
    projects = [
        {
            "project_id": f"batch-{uuid.uuid4().hex[:6]}",
            "goal": p.get("goal", "Creative project")
        }
        for p in request.projects
    ]
    
    # Run in background
    async def run_batch():
        return await scheduler.run_all(projects)
    
    background_tasks.add_task(run_batch)
    
    return {
        "scheduled": [p["project_id"] for p in projects],
        "message": f"Started {len(projects)} projects in background",
        "status": "running"
    }


# ============================================================================
# Quick Actions
# ============================================================================

@router.post("/quick/create-product")
async def quick_create_product(
    goal: str,
    product_types: Optional[List[str]] = None,
    run_immediately: bool = True
):
    """
    Quick action to create a product project.
    
    Creates a project configured for immediate product creation.
    """
    platform = get_creative_platform()
    project_id = f"quick-{uuid.uuid4().hex[:8]}"
    
    initial_state = {}
    if product_types:
        initial_state["creative_brief"] = {"product_targets": product_types}
    
    await platform.create_project(project_id, goal, initial_state)
    
    if run_immediately:
        await platform.run_project_async(project_id)
        return {
            "project_id": project_id,
            "status": "running",
            "message": f"Creating products for: {goal}"
        }
    
    return {
        "project_id": project_id,
        "status": "created",
        "message": f"Project created, use /projects/{project_id}/start to begin"
    }


@router.post("/quick/generate-assets")
async def quick_generate_assets(
    concept: str,
    style: Optional[str] = "modern",
    asset_types: Optional[List[str]] = None
):
    """Quick action to generate creative assets only."""
    platform = get_creative_platform()
    project_id = f"assets-{uuid.uuid4().hex[:8]}"
    
    initial_state = {
        "selected_concept": {"title": concept, "aesthetic": style},
        "creative_brief": {
            "concept": concept,
            "aesthetic": style,
            "product_targets": []  # No products, just assets
        }
    }
    
    await platform.create_project(project_id, f"Generate assets: {concept}", initial_state)
    
    # Run just the asset generation steps
    state = platform.state_store.load_state(project_id)
    if state:
        state["current_step"] = "generate_assets"
        platform.state_store.save_state(project_id, state)
    
    final_state = await platform.run_project(project_id, max_steps=10)
    
    return {
        "project_id": project_id,
        "assets": final_state.get("assets", {}),
        "image_assets": final_state.get("image_assets", {}),
        "status": final_state.get("status")
    }
