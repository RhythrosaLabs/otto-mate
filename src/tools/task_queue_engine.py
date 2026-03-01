"""
Enhanced Task Queue Engine for Otto
====================================

A powerful autonomous task queue system that:
1. Manages complex multi-step tasks with full planning
2. Supports task chaining and dependencies
3. Persists artifacts to session and filesystem
4. Enables scheduling and recurring tasks
5. Handles batch operations and parallel execution

Ported from printify_clean with enhancements.
"""

import asyncio
import json
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

# Import shared task models
from ..core.task_models import (
    TaskStatus,
    TaskPriority,
    ArtifactType,
    Artifact,
    TaskStep,
    Task
)

logger = logging.getLogger(__name__)


class EnhancedTaskQueueEngine:
    """
    Advanced task queue with full service integration.
    
    Features:
    - Multi-step task planning and execution
    - Artifact generation and storage
    - Task dependencies and chaining
    - Scheduling and recurrence
    - Parallel execution support
    - Persistence to filesystem
    """

    def __init__(
        self,
        storage_dir: str = "data/task_queue_engine",
        max_workers: int = 4,
    ):
        """
        Initialize the task queue engine.

        Args:
            storage_dir: Directory for task persistence
            max_workers: Maximum parallel workers
        """
        self.storage_dir = Path(storage_dir)
        self.artifact_dir = self.storage_dir / "artifacts"
        self.tasks_dir = self.storage_dir / "tasks"

        # Create directories
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.artifact_dir.mkdir(exist_ok=True)
        self.tasks_dir.mkdir(exist_ok=True)

        # In-memory task queue
        self.tasks: Dict[str, Task] = {}
        self.task_order: List[str] = []  # Maintains insertion order

        # Executor for parallel operations
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # Load persisted tasks
        self._load_tasks()

        logger.info(f"TaskQueueEngine initialized with {len(self.tasks)} persisted tasks")

    def _load_tasks(self):
        """Load tasks from filesystem."""
        for task_file in self.tasks_dir.glob("*.json"):
            try:
                with open(task_file) as f:
                    data = json.load(f)
                    task = self._task_from_dict(data)
                    self.tasks[task.id] = task
                    self.task_order.append(task.id)
            except Exception as e:
                logger.error(f"Failed to load task {task_file}: {e}")

    def _save_task(self, task: Task):
        """Save task to filesystem."""
        task_file = self.tasks_dir / f"{task.id}.json"
        with open(task_file, "w") as f:
            json.dump(task.to_dict(), f, indent=2)

    def _task_from_dict(self, data: Dict) -> Task:
        """Create Task from dictionary."""
        task = Task(
            id=data.get("id", str(uuid.uuid4())),
            description=data.get("description", ""),
            status=TaskStatus(data.get("status", "pending")),
            priority=TaskPriority(data.get("priority", 2)),
        )
        task.plan = data.get("plan")
        task.context = data.get("context", {})
        task.current_step = data.get("current_step", 0)
        task.final_summary = data.get("final_summary", "")
        task.error = data.get("error")
        task.publish_to = data.get("publish_to", [])
        task.recurring = data.get("recurring", False)
        task.recurrence_pattern = data.get("recurrence_pattern")
        task.project_id = data.get("project_id")

        # Parse steps
        for step_data in data.get("steps", []):
            step = TaskStep(
                id=step_data.get("id"),
                name=step_data.get("name"),
                description=step_data.get("description"),
                agent=step_data.get("agent"),
                action=step_data.get("action"),
                status=TaskStatus(step_data.get("status", "pending")),
                result=step_data.get("result"),
                error=step_data.get("error"),
                depends_on=step_data.get("depends_on", []),
            )
            task.steps.append(step)

        # Parse artifacts
        for artifact_data in data.get("artifacts", []):
            artifact = Artifact.from_dict(artifact_data)
            task.artifacts.append(artifact)

        return task

    # ============================================
    # TASK MANAGEMENT
    # ============================================

    def create_task(
        self,
        description: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        context: Optional[Dict] = None,
        scheduled_for: Optional[datetime] = None,
        depends_on: Optional[List[str]] = None,
        publish_to: Optional[List[str]] = None,
        project_id: Optional[str] = None,
    ) -> Task:
        """
        Create a new task.

        Args:
            description: Task description
            priority: Task priority
            context: Additional context
            scheduled_for: Scheduled execution time
            depends_on: List of task IDs this depends on
            publish_to: Publishing targets
            project_id: Associated project ID

        Returns:
            Created Task object
        """
        task = Task(
            id=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}",
            description=description,
            priority=priority,
            context=context or {},
            scheduled_for=scheduled_for,
            depends_on=depends_on or [],
            publish_to=publish_to or [],
            project_id=project_id,
        )

        if scheduled_for:
            task.status = TaskStatus.SCHEDULED

        self.tasks[task.id] = task
        self.task_order.append(task.id)
        self._save_task(task)

        logger.info(f"Created task: {task.id} - {description[:50]}...")
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        project_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Task]:
        """
        List tasks with optional filters.

        Args:
            status: Filter by status
            priority: Filter by priority
            project_id: Filter by project
            limit: Maximum tasks to return

        Returns:
            List of matching tasks
        """
        tasks = []
        for task_id in reversed(self.task_order):  # Most recent first
            task = self.tasks.get(task_id)
            if not task:
                continue

            if status and task.status != status:
                continue
            if priority and task.priority != priority:
                continue
            if project_id and task.project_id != project_id:
                continue

            tasks.append(task)
            if len(tasks) >= limit:
                break

        return tasks

    def update_task(self, task_id: str, updates: Dict) -> Optional[Task]:
        """
        Update a task.

        Args:
            task_id: Task ID
            updates: Fields to update

        Returns:
            Updated task or None
        """
        task = self.tasks.get(task_id)
        if not task:
            return None

        # Update allowed fields
        if "status" in updates:
            task.status = TaskStatus(updates["status"])
        if "priority" in updates:
            task.priority = TaskPriority(updates["priority"])
        if "context" in updates:
            task.context.update(updates["context"])
        if "final_summary" in updates:
            task.final_summary = updates["final_summary"]
        if "error" in updates:
            task.error = updates["error"]

        self._save_task(task)
        return task

    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        if task_id not in self.tasks:
            return False

        del self.tasks[task_id]
        self.task_order.remove(task_id)

        # Delete file
        task_file = self.tasks_dir / f"{task_id}.json"
        task_file.unlink(missing_ok=True)

        logger.info(f"Deleted task: {task_id}")
        return True

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        task = self.tasks.get(task_id)
        if not task:
            return False

        if task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            return False

        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()
        self._save_task(task)

        logger.info(f"Cancelled task: {task_id}")
        return True

    # ============================================
    # STEP MANAGEMENT
    # ============================================

    def add_step(
        self,
        task_id: str,
        name: str,
        description: str,
        agent: str,
        action: str,
        depends_on: Optional[List[str]] = None,
    ) -> Optional[TaskStep]:
        """
        Add a step to a task.

        Args:
            task_id: Task ID
            name: Step name
            description: Step description
            agent: Agent type (designer, writer, video, etc.)
            action: Action to perform
            depends_on: List of step IDs this depends on

        Returns:
            Created TaskStep or None
        """
        task = self.tasks.get(task_id)
        if not task:
            return None

        step = TaskStep(
            id=f"step_{uuid.uuid4().hex[:8]}",
            name=name,
            description=description,
            agent=agent,
            action=action,
            depends_on=depends_on or [],
        )

        task.steps.append(step)
        self._save_task(task)

        return step

    def complete_step(
        self,
        task_id: str,
        step_id: str,
        result: Optional[Dict] = None,
        artifacts: Optional[List[Artifact]] = None,
    ) -> bool:
        """
        Mark a step as complete.

        Args:
            task_id: Task ID
            step_id: Step ID
            result: Step result
            artifacts: Generated artifacts

        Returns:
            Success status
        """
        task = self.tasks.get(task_id)
        if not task:
            return False

        for step in task.steps:
            if step.id == step_id:
                step.status = TaskStatus.COMPLETED
                step.completed_at = datetime.now()
                step.result = result

                if artifacts:
                    step.artifacts.extend(artifacts)
                    task.artifacts.extend(artifacts)

                self._save_task(task)
                return True

        return False

    def fail_step(self, task_id: str, step_id: str, error: str) -> bool:
        """Mark a step as failed."""
        task = self.tasks.get(task_id)
        if not task:
            return False

        for step in task.steps:
            if step.id == step_id:
                step.status = TaskStatus.FAILED
                step.completed_at = datetime.now()
                step.error = error
                self._save_task(task)
                return True

        return False

    # ============================================
    # ARTIFACT MANAGEMENT
    # ============================================

    def add_artifact(
        self,
        task_id: str,
        artifact_type: ArtifactType,
        name: str,
        url: Optional[str] = None,
        content: Optional[str] = None,
        file_path: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Optional[Artifact]:
        """
        Add an artifact to a task.

        Args:
            task_id: Task ID
            artifact_type: Type of artifact
            name: Artifact name
            url: URL if remote
            content: Content if text
            file_path: Local file path
            metadata: Additional metadata

        Returns:
            Created Artifact or None
        """
        task = self.tasks.get(task_id)
        if not task:
            return None

        artifact = Artifact(
            id=f"artifact_{uuid.uuid4().hex[:8]}",
            type=artifact_type,
            name=name,
            url=url,
            content=content,
            file_path=file_path,
            metadata=metadata or {},
        )

        task.artifacts.append(artifact)
        self._save_task(task)

        return artifact

    def save_artifact_file(
        self,
        task_id: str,
        data: bytes,
        filename: str,
        artifact_type: ArtifactType,
    ) -> Optional[Artifact]:
        """
        Save artifact file to storage.

        Args:
            task_id: Task ID
            data: File data
            filename: Filename
            artifact_type: Type of artifact

        Returns:
            Created Artifact or None
        """
        task = self.tasks.get(task_id)
        if not task:
            return None

        # Create task-specific artifact directory
        task_artifact_dir = self.artifact_dir / task_id
        task_artifact_dir.mkdir(exist_ok=True)

        # Save file
        file_path = task_artifact_dir / filename
        with open(file_path, "wb") as f:
            f.write(data)

        # Create artifact
        artifact = self.add_artifact(
            task_id=task_id,
            artifact_type=artifact_type,
            name=filename,
            file_path=str(file_path),
        )

        return artifact

    # ============================================
    # EXECUTION
    # ============================================

    async def start_task(self, task_id: str) -> bool:
        """Start executing a task."""
        task = self.tasks.get(task_id)
        if not task:
            return False

        if task.status == TaskStatus.RUNNING:
            return False

        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        self._save_task(task)

        logger.info(f"Started task: {task_id}")
        return True

    async def complete_task(
        self,
        task_id: str,
        summary: str = "",
    ) -> bool:
        """Mark task as complete."""
        task = self.tasks.get(task_id)
        if not task:
            return False

        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        task.final_summary = summary
        self._save_task(task)

        logger.info(f"Completed task: {task_id}")

        # Handle recurrence
        if task.recurring and task.recurrence_pattern:
            await self._schedule_next_recurrence(task)

        return True

    async def fail_task(self, task_id: str, error: str) -> bool:
        """Mark task as failed."""
        task = self.tasks.get(task_id)
        if not task:
            return False

        task.status = TaskStatus.FAILED
        task.completed_at = datetime.now()
        task.error = error
        self._save_task(task)

        logger.error(f"Task failed: {task_id} - {error}")
        return True

    async def _schedule_next_recurrence(self, task: Task):
        """Schedule next occurrence of recurring task."""
        if not task.recurrence_pattern:
            return

        intervals = {
            "daily": timedelta(days=1),
            "weekly": timedelta(weeks=1),
            "monthly": timedelta(days=30),
            "hourly": timedelta(hours=1),
        }

        interval = intervals.get(task.recurrence_pattern)
        if not interval:
            return

        next_time = datetime.now() + interval

        # Create new task
        new_task = self.create_task(
            description=task.description,
            priority=task.priority,
            context=task.context,
            scheduled_for=next_time,
            publish_to=task.publish_to,
            project_id=task.project_id,
        )
        new_task.recurring = True
        new_task.recurrence_pattern = task.recurrence_pattern
        self._save_task(new_task)

        logger.info(f"Scheduled next recurrence: {new_task.id} for {next_time}")

    # ============================================
    # STATISTICS
    # ============================================

    def get_statistics(self) -> Dict[str, Any]:
        """Get queue statistics."""
        tasks = list(self.tasks.values())

        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = len([t for t in tasks if t.status == status])

        completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED]
        avg_duration = (
            sum(t.duration() or 0 for t in completed_tasks) / len(completed_tasks)
            if completed_tasks else 0
        )

        return {
            "total_tasks": len(tasks),
            "status_counts": status_counts,
            "total_artifacts": sum(len(t.artifacts) for t in tasks),
            "avg_completion_time": avg_duration,
            "pending_count": status_counts.get("pending", 0),
            "running_count": status_counts.get("running", 0),
            "completed_count": status_counts.get("completed", 0),
            "failed_count": status_counts.get("failed", 0),
        }


# Singleton instance
_task_queue_engine = None


def get_task_queue_engine() -> EnhancedTaskQueueEngine:
    """Get the singleton TaskQueueEngine instance."""
    global _task_queue_engine
    if _task_queue_engine is None:
        _task_queue_engine = EnhancedTaskQueueEngine()
    return _task_queue_engine
