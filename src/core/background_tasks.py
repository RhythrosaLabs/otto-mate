"""
Background Task Manager
Handles async retries for rate-limited operations
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"


class BackgroundTask:
    """Represents a background task that can retry automatically"""
    
    def __init__(
        self,
        task_id: str,
        step: Dict[str, Any],
        tool_registry,
        retry_delay: int = 60,
        max_retries: int = 5
    ):
        self.task_id = task_id
        self.step = step
        self.tool_registry = tool_registry
        self.retry_delay = retry_delay
        self.max_retries = max_retries
        self.status = TaskStatus.PENDING
        self.attempts = 0
        self.result = None
        self.error = None
        self.started_at = None
        self.completed_at = None
    
    async def execute(self, execution_agent) -> Dict[str, Any]:
        """Execute the task with automatic retry on rate limits"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()
        
        while self.attempts < self.max_retries:
            self.attempts += 1
            logger.info(f"⏳ Task {self.task_id}: Attempt {self.attempts}/{self.max_retries}")
            
            try:
                # Execute the step using execution agent's execute_tool method
                result = await execution_agent.execute_tool(
                    tool_name=self.step.get("tool"),
                    parameters=self.step.get("parameters", {}),
                    tool_registry=self.tool_registry,
                    context={},
                    step_data=self.step
                )
                
                if result.get("success"):
                    self.status = TaskStatus.COMPLETED
                    self.result = result
                    self.completed_at = datetime.now()
                    logger.info(f"✅ Task {self.task_id} completed successfully")
                    return result
                
                # Check if it's a rate limit error
                error_msg = str(result.get("error", ""))
                if "rate limit" in error_msg.lower() or "429" in error_msg:
                    self.status = TaskStatus.RATE_LIMITED
                    wait_time = self.retry_delay * self.attempts
                    logger.info(f"⏸️ Task {self.task_id}: Rate limited, waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    # Non-rate-limit error
                    self.status = TaskStatus.FAILED
                    self.error = error_msg
                    logger.warning(f"❌ Task {self.task_id} failed: {error_msg}")
                    return result
                    
            except Exception as e:
                logger.error(f"❌ Task {self.task_id} exception: {e}")
                self.error = str(e)
                if self.attempts >= self.max_retries:
                    self.status = TaskStatus.FAILED
                    return {"success": False, "error": str(e)}
                await asyncio.sleep(self.retry_delay)
        
        # Max retries exceeded
        self.status = TaskStatus.FAILED
        return {"success": False, "error": f"Max retries ({self.max_retries}) exceeded"}


class BackgroundTaskManager:
    """Manages background tasks that retry automatically"""
    
    def __init__(self):
        self.tasks: Dict[str, BackgroundTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
    
    def create_task(
        self,
        step: Dict[str, Any],
        tool_registry,
        execution_agent,
        retry_delay: int = 60
    ) -> str:
        """Create a new background task"""
        task_id = f"bg_task_{datetime.now().timestamp()}"
        bg_task = BackgroundTask(task_id, step, tool_registry, retry_delay)
        self.tasks[task_id] = bg_task
        
        # Start executing in background
        async_task = asyncio.create_task(bg_task.execute(execution_agent))
        self.running_tasks[task_id] = async_task
        
        logger.info(f"🚀 Created background task {task_id}: {step.get('tool', 'unknown')}")
        return task_id
    
    def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a background task"""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        return {
            "task_id": task_id,
            "status": task.status.value,
            "attempts": task.attempts,
            "max_retries": task.max_retries,
            "step_description": task.step.get("description", ""),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "result": task.result,
            "error": task.error
        }
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get status of all tasks"""
        return [self.get_status(tid) for tid in self.tasks.keys()]
    
    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """Get all pending/running tasks"""
        return [
            self.get_status(tid)
            for tid, task in self.tasks.items()
            if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.RATE_LIMITED]
        ]


# Global task manager instance
_task_manager = None


def get_task_manager() -> BackgroundTaskManager:
    """Get or create the global task manager"""
    global _task_manager
    if _task_manager is None:
        _task_manager = BackgroundTaskManager()
    return _task_manager
