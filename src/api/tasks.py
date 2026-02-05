"""
Task Queue API Router
======================

REST API endpoints for the enhanced task queue system.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


# Request/Response models
class CreateTaskRequest(BaseModel):
    description: str
    priority: str = "normal"  # low, normal, high, urgent
    context: Optional[Dict[str, Any]] = None
    scheduled_for: Optional[str] = None  # ISO datetime
    depends_on: Optional[List[str]] = None
    publish_to: Optional[List[str]] = None
    project_id: Optional[str] = None


class AddStepRequest(BaseModel):
    name: str
    description: str
    agent: str
    action: str
    depends_on: Optional[List[str]] = None


class CompleteStepRequest(BaseModel):
    result: Optional[Dict[str, Any]] = None


class AddArtifactRequest(BaseModel):
    artifact_type: str  # image, video, audio, text, file, etc.
    name: str
    url: Optional[str] = None
    content: Optional[str] = None
    file_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class UpdateTaskRequest(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    final_summary: Optional[str] = None


@router.get("")
async def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    project_id: Optional[str] = None,
    limit: int = 50,
):
    """List all tasks with optional filters."""
    try:
        from src.tools.task_queue_engine import get_task_queue_engine, TaskStatus, TaskPriority
        queue = get_task_queue_engine()
        
        # Convert string filters to enums
        status_filter = TaskStatus(status) if status else None
        priority_filter = TaskPriority[priority.upper()] if priority else None
        
        tasks = queue.list_tasks(
            status=status_filter,
            priority=priority_filter,
            project_id=project_id,
            limit=limit,
        )
        
        return {
            "success": True,
            "count": len(tasks),
            "tasks": [t.to_dict() for t in tasks],
        }
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_task(request: CreateTaskRequest):
    """Create a new task."""
    try:
        from src.tools.task_queue_engine import get_task_queue_engine, TaskPriority
        from datetime import datetime
        
        queue = get_task_queue_engine()
        
        # Parse priority
        priority_map = {
            "low": TaskPriority.LOW,
            "normal": TaskPriority.NORMAL,
            "high": TaskPriority.HIGH,
            "urgent": TaskPriority.URGENT,
        }
        priority = priority_map.get(request.priority.lower(), TaskPriority.NORMAL)
        
        # Parse scheduled time
        scheduled = None
        if request.scheduled_for:
            scheduled = datetime.fromisoformat(request.scheduled_for)
        
        task = queue.create_task(
            description=request.description,
            priority=priority,
            context=request.context,
            scheduled_for=scheduled,
            depends_on=request.depends_on,
            publish_to=request.publish_to,
            project_id=request.project_id,
        )
        
        return {
            "success": True,
            "task": task.to_dict(),
        }
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}")
async def get_task(task_id: str):
    """Get a specific task by ID."""
    try:
        from src.tools.task_queue_engine import get_task_queue_engine
        queue = get_task_queue_engine()
        
        task = queue.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "success": True,
            "task": task.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{task_id}")
async def update_task(task_id: str, request: UpdateTaskRequest):
    """Update a task."""
    try:
        from src.tools.task_queue_engine import get_task_queue_engine
        queue = get_task_queue_engine()
        
        updates = {}
        if request.status:
            updates["status"] = request.status
        if request.priority:
            updates["priority"] = {"low": 1, "normal": 2, "high": 3, "urgent": 4}.get(request.priority, 2)
        if request.context:
            updates["context"] = request.context
        if request.final_summary:
            updates["final_summary"] = request.final_summary
        
        task = queue.update_task(task_id, updates)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "success": True,
            "task": task.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    """Delete a task."""
    try:
        from src.tools.task_queue_engine import get_task_queue_engine
        queue = get_task_queue_engine()
        
        success = queue.delete_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {"success": True, "message": "Task deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel a running or pending task."""
    try:
        from src.tools.task_queue_engine import get_task_queue_engine
        queue = get_task_queue_engine()
        
        success = queue.cancel_task(task_id)
        if not success:
            raise HTTPException(status_code=400, detail="Cannot cancel task")
        
        return {"success": True, "message": "Task cancelled"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/start")
async def start_task(task_id: str):
    """Start executing a task."""
    try:
        from src.tools.task_queue_engine import get_task_queue_engine
        queue = get_task_queue_engine()
        
        success = await queue.start_task(task_id)
        if not success:
            raise HTTPException(status_code=400, detail="Cannot start task")
        
        return {"success": True, "message": "Task started"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/complete")
async def complete_task(task_id: str, summary: str = ""):
    """Mark a task as complete."""
    try:
        from src.tools.task_queue_engine import get_task_queue_engine
        queue = get_task_queue_engine()
        
        success = await queue.complete_task(task_id, summary)
        if not success:
            raise HTTPException(status_code=400, detail="Cannot complete task")
        
        return {"success": True, "message": "Task completed"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to complete task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# STEP MANAGEMENT
# ============================================

@router.post("/{task_id}/steps")
async def add_step(task_id: str, request: AddStepRequest):
    """Add a step to a task."""
    try:
        from src.tools.task_queue_engine import get_task_queue_engine
        queue = get_task_queue_engine()
        
        step = queue.add_step(
            task_id=task_id,
            name=request.name,
            description=request.description,
            agent=request.agent,
            action=request.action,
            depends_on=request.depends_on,
        )
        
        if not step:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "success": True,
            "step": step.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add step: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/steps/{step_id}/complete")
async def complete_step(task_id: str, step_id: str, request: CompleteStepRequest):
    """Mark a step as complete."""
    try:
        from src.tools.task_queue_engine import get_task_queue_engine
        queue = get_task_queue_engine()
        
        success = queue.complete_step(task_id, step_id, request.result)
        if not success:
            raise HTTPException(status_code=400, detail="Cannot complete step")
        
        return {"success": True, "message": "Step completed"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to complete step: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/steps/{step_id}/fail")
async def fail_step(task_id: str, step_id: str, error: str):
    """Mark a step as failed."""
    try:
        from src.tools.task_queue_engine import get_task_queue_engine
        queue = get_task_queue_engine()
        
        success = queue.fail_step(task_id, step_id, error)
        if not success:
            raise HTTPException(status_code=400, detail="Cannot fail step")
        
        return {"success": True, "message": "Step marked as failed"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fail step: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ARTIFACT MANAGEMENT
# ============================================

@router.post("/{task_id}/artifacts")
async def add_artifact(task_id: str, request: AddArtifactRequest):
    """Add an artifact to a task."""
    try:
        from src.tools.task_queue_engine import get_task_queue_engine, ArtifactType
        queue = get_task_queue_engine()
        
        artifact_type = ArtifactType(request.artifact_type)
        
        artifact = queue.add_artifact(
            task_id=task_id,
            artifact_type=artifact_type,
            name=request.name,
            url=request.url,
            content=request.content,
            file_path=request.file_path,
            metadata=request.metadata,
        )
        
        if not artifact:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "success": True,
            "artifact": artifact.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add artifact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}/artifacts")
async def get_task_artifacts(task_id: str):
    """Get all artifacts for a task."""
    try:
        from src.tools.task_queue_engine import get_task_queue_engine
        queue = get_task_queue_engine()
        
        task = queue.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "success": True,
            "count": len(task.artifacts),
            "artifacts": [a.to_dict() for a in task.artifacts],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get artifacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# STATISTICS
# ============================================

@router.get("/stats/summary")
async def get_statistics():
    """Get task queue statistics."""
    try:
        from src.tools.task_queue_engine import get_task_queue_engine
        queue = get_task_queue_engine()
        
        stats = queue.get_statistics()
        return {
            "success": True,
            "statistics": stats,
        }
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
