"""
Scheduler API Router
====================

API endpoints for managing scheduled tasks.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..tools.scheduler import (
    create_task_scheduler,
    ScheduledTask,
    ScheduleType,
    SCHEDULE_PRESETS
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scheduler", tags=["Scheduler"])

# Global scheduler reference
_scheduler = None


def get_scheduler():
    """Get the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = create_task_scheduler()
    return _scheduler


def set_scheduler(scheduler):
    """Set the global scheduler instance."""
    global _scheduler
    _scheduler = scheduler


# ==========================================
# PYDANTIC MODELS
# ==========================================

class TaskCreate(BaseModel):
    """Create a new scheduled task."""
    name: str
    description: Optional[str] = None
    schedule_type: str  # once, interval, cron, daily, weekly, monthly
    schedule_config: Dict[str, Any]
    action_type: str  # tool, webhook, workflow, script
    action_config: Dict[str, Any]
    enabled: bool = True
    tags: Optional[List[str]] = None
    max_retries: int = 3
    retry_delay_seconds: int = 60


class TaskUpdate(BaseModel):
    """Update an existing task."""
    name: Optional[str] = None
    description: Optional[str] = None
    schedule_type: Optional[str] = None
    schedule_config: Optional[Dict[str, Any]] = None
    action_type: Optional[str] = None
    action_config: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None
    tags: Optional[List[str]] = None
    max_retries: Optional[int] = None
    retry_delay_seconds: Optional[int] = None


# ==========================================
# TASK MANAGEMENT ENDPOINTS
# ==========================================

@router.post("/tasks")
async def create_task(task: TaskCreate):
    """Create a new scheduled task."""
    scheduler = get_scheduler()
    
    try:
        result = await scheduler.create_task(
            name=task.name,
            description=task.description,
            schedule_type=task.schedule_type,
            schedule_config=task.schedule_config,
            action_type=task.action_type,
            action_config=task.action_config,
            enabled=task.enabled,
            tags=task.tags,
            max_retries=task.max_retries,
            retry_delay_seconds=task.retry_delay_seconds
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks")
async def list_tasks(
    enabled_only: bool = False,
    tag: Optional[str] = None
):
    """List all scheduled tasks."""
    scheduler = get_scheduler()
    result = await scheduler.list_tasks(enabled_only=enabled_only, tag=tag)
    return result


@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Get a specific task by ID."""
    scheduler = get_scheduler()
    result = await scheduler.get_task(task_id=task_id)
    
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.put("/tasks/{task_id}")
async def update_task(task_id: str, update: TaskUpdate):
    """Update a scheduled task."""
    scheduler = get_scheduler()
    
    result = await scheduler.update_task(
        task_id=task_id,
        **{k: v for k, v in update.dict().items() if v is not None}
    )
    
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a scheduled task."""
    scheduler = get_scheduler()
    result = await scheduler.delete_task(task_id=task_id)
    
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


# ==========================================
# TASK CONTROL ENDPOINTS
# ==========================================

@router.post("/tasks/{task_id}/run")
async def run_task_now(task_id: str):
    """Run a task immediately."""
    scheduler = get_scheduler()
    result = await scheduler.run_task_now(task_id=task_id)
    
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.post("/tasks/{task_id}/pause")
async def pause_task(task_id: str):
    """Pause a scheduled task."""
    scheduler = get_scheduler()
    result = await scheduler.pause_task(task_id=task_id)
    
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.post("/tasks/{task_id}/resume")
async def resume_task(task_id: str):
    """Resume a paused task."""
    scheduler = get_scheduler()
    result = await scheduler.resume_task(task_id=task_id)
    
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


# ==========================================
# HISTORY ENDPOINTS
# ==========================================

@router.get("/tasks/{task_id}/history")
async def get_task_history(task_id: str, limit: int = 50):
    """Get execution history for a task."""
    scheduler = get_scheduler()
    result = await scheduler.get_history(task_id=task_id, limit=limit)
    return result


@router.get("/history")
async def get_all_history(limit: int = 100):
    """Get execution history for all tasks."""
    scheduler = get_scheduler()
    result = await scheduler.get_history(limit=limit)
    return result


# ==========================================
# UTILITY ENDPOINTS
# ==========================================

@router.get("/presets")
async def get_schedule_presets():
    """Get available schedule presets."""
    return {
        "presets": {
            name: {
                "schedule_type": preset.get("type"),
                "schedule_config": preset.get("config")
            }
            for name, preset in SCHEDULE_PRESETS.items()
        },
        "schedule_types": [t.value for t in ScheduleType],
        "action_types": ["tool", "webhook", "workflow", "script"],
        "examples": {
            "daily_report": {
                "name": "Daily Sales Report",
                "schedule_type": "cron",
                "schedule_config": {"hour": 9, "minute": 0},
                "action_type": "tool",
                "action_config": {
                    "tool_name": "generate_sales_report",
                    "parameters": {"period": "daily"}
                }
            },
            "hourly_inventory_check": {
                "name": "Inventory Check",
                "schedule_type": "interval",
                "schedule_config": {"hours": 1},
                "action_type": "tool",
                "action_config": {
                    "tool_name": "shopify_get_inventory_levels",
                    "parameters": {}
                }
            },
            "weekly_backup": {
                "name": "Weekly Backup",
                "schedule_type": "weekly",
                "schedule_config": {"day_of_week": "sunday", "hour": 2, "minute": 0},
                "action_type": "webhook",
                "action_config": {
                    "url": "https://api.example.com/backup",
                    "method": "POST"
                }
            }
        }
    }


@router.get("/status")
async def get_scheduler_status():
    """Get scheduler status."""
    scheduler = get_scheduler()
    
    tasks = await scheduler.list_tasks()
    enabled_count = len([t for t in tasks.get("tasks", []) if t.get("enabled")])
    
    return {
        "running": scheduler.is_running,
        "total_tasks": tasks.get("count", 0),
        "enabled_tasks": enabled_count,
        "next_run_times": [
            {
                "task_id": t.get("id"),
                "name": t.get("name"),
                "next_run": t.get("next_run")
            }
            for t in tasks.get("tasks", [])[:10]
            if t.get("enabled") and t.get("next_run")
        ]
    }
