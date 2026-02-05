"""
Task Queue API routes (v1).

Integrates task queue with orchestrator for actual execution.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


# Request/Response models
class CreateTaskRequest(BaseModel):
    description: str
    priority: str = "normal"  # low, normal, high, urgent
    context: Optional[Dict[str, Any]] = None
    scheduled_for: Optional[str] = None  # ISO datetime
    depends_on: Optional[List[str]] = None
    publish_to: Optional[List[str]] = None
    project_id: Optional[str] = None
    auto_execute: bool = False  # Whether to start execution immediately


class ExecuteTaskRequest(BaseModel):
    """Request to execute a task immediately."""
    background: bool = True  # Run in background (non-blocking)


class UpdateTaskRequest(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    final_summary: Optional[str] = None


# Task execution helper
async def _execute_task_with_orchestrator(task_id: str, task_description: str):
    """Execute a task using the orchestrator."""
    try:
        from src.tools.task_queue_engine import get_task_queue_engine
        from backend.src.api.orchestrator_bridge import get_orchestrator
        
        queue = get_task_queue_engine()
        orchestrator = get_orchestrator()
        
        # Mark task as running
        await queue.start_task(task_id)
        logger.info(f"Executing task {task_id}: {task_description[:100]}...")
        
        # Execute using orchestrator
        result = await orchestrator.process(
            message=task_description,
            user_id=f"task_{task_id}",
            session_id=f"task_session_{task_id}"
        )
        
        # Mark complete
        summary = result.get("response", str(result))[:500] if isinstance(result, dict) else str(result)[:500]
        await queue.complete_task(task_id, summary)
        
        logger.info(f"Task {task_id} completed successfully")
        return {"success": True, "result": result}
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        from src.tools.task_queue_engine import get_task_queue_engine
        queue = get_task_queue_engine()
        await queue.fail_task(task_id, str(e))
        return {"success": False, "error": str(e)}


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
async def create_task(request: CreateTaskRequest, background_tasks: BackgroundTasks):
    """Create a new task, optionally starting execution immediately."""
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
        
        response = {
            "success": True,
            "task": task.to_dict(),
        }
        
        # Auto-execute if requested
        if request.auto_execute:
            background_tasks.add_task(
                _execute_task_with_orchestrator,
                task.id,
                request.description
            )
            response["execution_started"] = True
        
        return response
        
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


@router.post("/{task_id}/execute")
async def execute_task(
    task_id: str,
    request: ExecuteTaskRequest,
    background_tasks: BackgroundTasks
):
    """
    Execute a task using the orchestrator.
    
    This is the key endpoint that actually runs tasks.
    """
    try:
        from src.tools.task_queue_engine import get_task_queue_engine, TaskStatus
        queue = get_task_queue_engine()
        
        task = queue.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Check if task can be executed
        if task.status == TaskStatus.RUNNING:
            raise HTTPException(status_code=400, detail="Task is already running")
        if task.status == TaskStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Task is already completed")
        
        if request.background:
            # Run in background
            background_tasks.add_task(
                _execute_task_with_orchestrator,
                task_id,
                task.description
            )
            return {
                "success": True,
                "message": "Task execution started in background",
                "task_id": task_id
            }
        else:
            # Run synchronously
            result = await _execute_task_with_orchestrator(task_id, task.description)
            return {
                "success": result.get("success", False),
                "task_id": task_id,
                "result": result
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/start")
async def start_task(task_id: str, background_tasks: BackgroundTasks):
    """
    Start a task (marks as running and begins execution).
    
    This is an alias for execute with background=True.
    """
    try:
        from src.tools.task_queue_engine import get_task_queue_engine
        queue = get_task_queue_engine()
        
        task = queue.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Start execution in background
        background_tasks.add_task(
            _execute_task_with_orchestrator,
            task_id,
            task.description
        )
        
        return {
            "success": True,
            "message": "Task execution started",
            "task_id": task_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/complete")
async def complete_task(task_id: str, summary: str = ""):
    """Mark a task as complete (manual completion)."""
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


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel a task."""
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
