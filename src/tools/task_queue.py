"""
Task Queue Tools
================
Tools for interacting with the task queue management system.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from .core import tool, ToolBase
from ..core.task_queue_manager import get_task_queue_manager

logger = logging.getLogger(__name__)


class TaskQueueTools(ToolBase):
    """Task queue management tools."""
    
    def __init__(self, planning_agent=None, execution_agent=None):
        self.queue_manager = get_task_queue_manager()
        self.planning_agent = planning_agent
        self.execution_agent = execution_agent
    
    @tool(
        name="queue_task",
        description="Add a task to the autonomous execution queue with priority and scheduling",
        category="task_queue"
    )
    async def queue_task(
        self,
        description: str,
        priority: str = "normal",
        schedule_for: Optional[str] = None,
        publish_to: Optional[List[str]] = None,
        recurring: bool = False,
        recurrence_pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add task to execution queue.
        
        Args:
            description: Natural language task description
            priority: low, normal, high, or urgent
            schedule_for: ISO datetime string for delayed execution
            publish_to: List of platforms (printify, shopify, youtube, instagram)
            recurring: Whether task should repeat
            recurrence_pattern: daily, weekly, or monthly
            
        Returns:
            Task ID and status
        """
        # Parse schedule datetime if provided
        scheduled_datetime = None
        if schedule_for:
            try:
                scheduled_datetime = datetime.fromisoformat(schedule_for)
            except:
                logger.warning(f"Invalid schedule format: {schedule_for}")
        
        result = self.queue_manager.queue_task(
            description=description,
            priority=priority,
            schedule_for=scheduled_datetime,
            publish_to=publish_to,
            recurring=recurring,
            recurrence_pattern=recurrence_pattern
        )
        
        # Auto-plan the task if planning agent available
        if result.get("success") and self.planning_agent:
            task_id = result["task_id"]
            await self.queue_manager.plan_task(task_id, self.planning_agent)
        
        return result
    
    @tool(
        name="execute_task",
        description="Execute a queued task with real-time progress tracking",
        category="task_queue"
    )
    async def execute_task(
        self,
        task_id: str,
        background: bool = False
    ) -> Dict[str, Any]:
        """
        Execute task from queue.
        
        Args:
            task_id: Task to execute
            background: Run in background without blocking
            
        Returns:
            Execution status and artifacts
        """
        if not self.execution_agent:
            return {"success": False, "error": "Execution agent not configured"}
        
        return await self.queue_manager.execute_task(
            task_id=task_id,
            execution_agent=self.execution_agent,
            background=background
        )
    
    @tool(
        name="track_task_progress",
        description="Monitor task execution status and retrieve results",
        category="task_queue"
    )
    def track_task_progress(self, task_id: str) -> Dict[str, Any]:
        """
        Get task status and progress.
        
        Args:
            task_id: Task to track
            
        Returns:
            Status, progress percentage, and artifacts
        """
        return self.queue_manager.track_progress(task_id)
    
    @tool(
        name="manage_task_artifacts",
        description="Collect and organize generated content from tasks",
        category="task_queue"
    )
    def manage_task_artifacts(
        self,
        task_id: str,
        artifact_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get task artifacts.
        
        Args:
            task_id: Task to get artifacts from
            artifact_type: Filter by image, video, text, product, blog, social_post
            
        Returns:
            List of artifacts with URLs and metadata
        """
        return self.queue_manager.manage_artifacts(task_id, artifact_type)
    
    @tool(
        name="list_queued_tasks",
        description="Get all tasks in the queue with their statuses",
        category="task_queue"
    )
    def list_queued_tasks(self, status_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        List all tasks in queue.
        
        Args:
            status_filter: Filter by pending, running, completed, failed
            
        Returns:
            List of tasks
        """
        tasks = []
        
        for task_id in self.queue_manager.queue:
            task = self.queue_manager.tasks.get(task_id)
            if task:
                if status_filter and task.status.value != status_filter:
                    continue
                tasks.append(task.to_dict())
        
        return {
            "success": True,
            "tasks": tasks,
            "count": len(tasks)
        }
    
    @tool(
        name="cancel_task",
        description="Cancel a queued or running task",
        category="task_queue"
    )
    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """
        Cancel task execution.
        
        Args:
            task_id: Task to cancel
            
        Returns:
            Cancellation confirmation
        """
        if task_id not in self.queue_manager.tasks:
            return {"success": False, "error": "Task not found"}
        
        task = self.queue_manager.tasks[task_id]
        
        from ..core.task_queue_manager import TaskStatus
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            return {"success": False, "error": f"Task already {task.status.value}"}
        
        task.status = TaskStatus.CANCELLED
        self.queue_manager._save_task(task)
        
        return {
            "success": True,
            "task_id": task_id,
            "status": "cancelled"
        }
