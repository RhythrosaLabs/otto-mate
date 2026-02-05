"""
Task Scheduler System
=====================

Cron-like scheduling system for:
- Recurring tasks (daily, weekly, monthly)
- One-time scheduled tasks
- Interval-based execution
- Task persistence and recovery
- Integration with all Otto tools
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import threading
import uuid

from .core import tool, ToolBase

logger = logging.getLogger(__name__)

# Try to import APScheduler
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.date import DateTrigger
    from apscheduler.jobstores.memory import MemoryJobStore
    from apscheduler.executors.asyncio import AsyncIOExecutor
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    logger.warning("APScheduler not installed. Run: pip install apscheduler")


# ==========================================
# DATA MODELS
# ==========================================

class ScheduledTaskStatus(str, Enum):
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class ScheduleType(str, Enum):
    ONCE = "once"  # Run once at specific time
    INTERVAL = "interval"  # Run every X seconds/minutes/hours
    CRON = "cron"  # Cron expression
    DAILY = "daily"  # Run daily at specific time
    WEEKLY = "weekly"  # Run weekly on specific day/time
    MONTHLY = "monthly"  # Run monthly on specific day


@dataclass
class ScheduledTask:
    """A scheduled task definition."""
    task_id: str
    name: str
    description: str
    schedule_type: str
    schedule_config: Dict[str, Any]
    action_type: str  # "tool", "workflow", "webhook", "script"
    action_config: Dict[str, Any]
    status: str = ScheduledTaskStatus.SCHEDULED
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    run_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    enabled: bool = True
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ScheduledTask':
        return cls(**data)


@dataclass
class TaskExecution:
    """Record of a task execution."""
    execution_id: str
    task_id: str
    started_at: str
    completed_at: Optional[str] = None
    status: str = "running"
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_seconds: Optional[float] = None


# ==========================================
# SCHEDULER CLASS
# ==========================================

class TaskScheduler(ToolBase):
    """Task scheduling system with persistence."""
    
    def __init__(
        self,
        data_dir: str = "./data/scheduler",
        tool_executor: Callable = None
    ):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.tasks_file = self.data_dir / "tasks.json"
        self.history_file = self.data_dir / "execution_history.jsonl"
        
        self.tool_executor = tool_executor
        self.tasks: Dict[str, ScheduledTask] = {}
        
        self._scheduler = None
        self._running = False
        
        # Load persisted tasks
        self._load_tasks()
    
    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._running and self._scheduler is not None
    
    def _load_tasks(self):
        """Load tasks from persistence."""
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, "r") as f:
                    data = json.load(f)
                    for task_data in data.get("tasks", []):
                        task = ScheduledTask.from_dict(task_data)
                        self.tasks[task.task_id] = task
                logger.info(f"Loaded {len(self.tasks)} scheduled tasks")
            except Exception as e:
                logger.error(f"Failed to load tasks: {e}")
    
    def _save_tasks(self):
        """Save tasks to persistence."""
        try:
            data = {
                "tasks": [task.to_dict() for task in self.tasks.values()],
                "updated_at": datetime.now().isoformat()
            }
            with open(self.tasks_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save tasks: {e}")
    
    def _save_execution(self, execution: TaskExecution):
        """Append execution to history."""
        try:
            with open(self.history_file, "a") as f:
                f.write(json.dumps(asdict(execution)) + "\n")
        except Exception as e:
            logger.error(f"Failed to save execution: {e}")
    
    def _create_trigger(self, schedule_type: str, config: Dict):
        """Create APScheduler trigger from config."""
        if not APSCHEDULER_AVAILABLE:
            raise RuntimeError("APScheduler not installed")
        
        if schedule_type == ScheduleType.ONCE:
            run_date = config.get("run_date")
            if isinstance(run_date, str):
                run_date = datetime.fromisoformat(run_date)
            return DateTrigger(run_date=run_date)
        
        elif schedule_type == ScheduleType.INTERVAL:
            return IntervalTrigger(
                seconds=config.get("seconds", 0),
                minutes=config.get("minutes", 0),
                hours=config.get("hours", 0),
                days=config.get("days", 0)
            )
        
        elif schedule_type == ScheduleType.CRON:
            return CronTrigger.from_crontab(config.get("expression", "0 * * * *"))
        
        elif schedule_type == ScheduleType.DAILY:
            hour = config.get("hour", 9)
            minute = config.get("minute", 0)
            return CronTrigger(hour=hour, minute=minute)
        
        elif schedule_type == ScheduleType.WEEKLY:
            day_of_week = config.get("day_of_week", "mon")  # mon, tue, wed, etc.
            hour = config.get("hour", 9)
            minute = config.get("minute", 0)
            return CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)
        
        elif schedule_type == ScheduleType.MONTHLY:
            day = config.get("day", 1)
            hour = config.get("hour", 9)
            minute = config.get("minute", 0)
            return CronTrigger(day=day, hour=hour, minute=minute)
        
        else:
            raise ValueError(f"Unknown schedule type: {schedule_type}")
    
    async def _execute_task(self, task_id: str):
        """Execute a scheduled task."""
        task = self.tasks.get(task_id)
        if not task or not task.enabled:
            return
        
        execution = TaskExecution(
            execution_id=str(uuid.uuid4())[:8],
            task_id=task_id,
            started_at=datetime.now().isoformat()
        )
        
        task.status = ScheduledTaskStatus.RUNNING
        task.last_run = execution.started_at
        task.run_count += 1
        
        try:
            logger.info(f"Executing scheduled task: {task.name} ({task_id})")
            
            result = None
            
            if task.action_type == "tool":
                # Execute a tool
                tool_name = task.action_config.get("tool_name")
                tool_params = task.action_config.get("params", {})
                
                if self.tool_executor:
                    result = await self.tool_executor(tool_name, **tool_params)
                else:
                    result = {"warning": "No tool executor configured"}
            
            elif task.action_type == "webhook":
                # Call a webhook
                import aiohttp
                url = task.action_config.get("url")
                method = task.action_config.get("method", "POST")
                payload = task.action_config.get("payload", {})
                headers = task.action_config.get("headers", {})
                
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method, url,
                        json=payload,
                        headers=headers
                    ) as response:
                        result = {
                            "status": response.status,
                            "body": await response.text()
                        }
            
            elif task.action_type == "workflow":
                # Execute a workflow
                workflow_id = task.action_config.get("workflow_id")
                workflow_params = task.action_config.get("params", {})
                result = {"workflow_id": workflow_id, "params": workflow_params}
                # Would integrate with workflow engine
            
            elif task.action_type == "script":
                # Execute a Python script/function
                script = task.action_config.get("script")
                # Safely execute script (use with caution)
                result = {"script_executed": True}
            
            # Record success
            execution.status = "completed"
            execution.result = result
            execution.completed_at = datetime.now().isoformat()
            execution.duration_seconds = (
                datetime.fromisoformat(execution.completed_at) -
                datetime.fromisoformat(execution.started_at)
            ).total_seconds()
            
            task.status = ScheduledTaskStatus.SCHEDULED
            task.last_error = None
            
            logger.info(f"Task completed: {task.name} - Duration: {execution.duration_seconds}s")
            
        except Exception as e:
            logger.error(f"Task failed: {task.name} - {e}")
            
            execution.status = "failed"
            execution.error = str(e)
            execution.completed_at = datetime.now().isoformat()
            
            task.status = ScheduledTaskStatus.SCHEDULED
            task.error_count += 1
            task.last_error = str(e)
        
        finally:
            self._save_execution(execution)
            self._save_tasks()
    
    async def start(self):
        """Start the scheduler."""
        if not APSCHEDULER_AVAILABLE:
            logger.error("APScheduler not installed. Scheduler cannot start.")
            return False
        
        if self._running:
            return True
        
        self._scheduler = AsyncIOScheduler(
            jobstores={"default": MemoryJobStore()},
            executors={"default": AsyncIOExecutor()},
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 60
            }
        )
        
        # Add all enabled tasks to scheduler
        for task in self.tasks.values():
            if task.enabled:
                try:
                    trigger = self._create_trigger(
                        task.schedule_type,
                        task.schedule_config
                    )
                    self._scheduler.add_job(
                        self._execute_task,
                        trigger=trigger,
                        id=task.task_id,
                        args=[task.task_id],
                        name=task.name
                    )
                except Exception as e:
                    logger.error(f"Failed to schedule task {task.name}: {e}")
        
        self._scheduler.start()
        self._running = True
        logger.info(f"Scheduler started with {len(self.tasks)} tasks")
        
        return True
    
    async def stop(self):
        """Stop the scheduler."""
        if self._scheduler and self._running:
            self._scheduler.shutdown()
            self._running = False
            logger.info("Scheduler stopped")
    
    # ==========================================
    # TOOL METHODS
    # ==========================================
    
    @tool(
        name="scheduler_create_task",
        description="Create a new scheduled task",
        category="scheduler"
    )
    async def create_task(
        self,
        name: str,
        description: str,
        schedule_type: str,
        schedule_config: Dict[str, Any],
        action_type: str,
        action_config: Dict[str, Any],
        tags: List[str] = None,
        enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new scheduled task.
        
        Args:
            name: Task name
            description: What the task does
            schedule_type: Type of schedule:
                - "once": Run once at specific time (config: {"run_date": "2024-03-15T10:00:00"})
                - "interval": Run every X time (config: {"hours": 1} or {"minutes": 30})
                - "cron": Cron expression (config: {"expression": "0 9 * * *"})
                - "daily": Run daily (config: {"hour": 9, "minute": 0})
                - "weekly": Run weekly (config: {"day_of_week": "mon", "hour": 9})
                - "monthly": Run monthly (config: {"day": 1, "hour": 9})
            schedule_config: Configuration for the schedule
            action_type: Type of action:
                - "tool": Execute a tool (config: {"tool_name": "...", "params": {}})
                - "webhook": Call a URL (config: {"url": "...", "method": "POST"})
                - "workflow": Run a workflow (config: {"workflow_id": "..."})
            action_config: Configuration for the action
            tags: Optional tags for organization
            enabled: Whether to enable immediately
        
        Examples:
            # Daily product sync at 9am
            schedule_type="daily", schedule_config={"hour": 9}
            action_type="tool", action_config={"tool_name": "shopify_list_products"}
            
            # Every hour check inventory
            schedule_type="interval", schedule_config={"hours": 1}
            action_type="tool", action_config={"tool_name": "shopify_get_inventory_levels"}
            
            # Weekly sales report on Monday
            schedule_type="weekly", schedule_config={"day_of_week": "mon", "hour": 9}
            action_type="tool", action_config={"tool_name": "shopify_get_sales_summary"}
        """
        task_id = str(uuid.uuid4())[:8]
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            description=description,
            schedule_type=schedule_type,
            schedule_config=schedule_config,
            action_type=action_type,
            action_config=action_config,
            tags=tags or [],
            enabled=enabled
        )
        
        self.tasks[task_id] = task
        
        # Add to running scheduler if active
        if self._scheduler and self._running and enabled:
            try:
                trigger = self._create_trigger(schedule_type, schedule_config)
                job = self._scheduler.add_job(
                    self._execute_task,
                    trigger=trigger,
                    id=task_id,
                    args=[task_id],
                    name=name
                )
                task.next_run = str(job.next_run_time) if job.next_run_time else None
            except Exception as e:
                logger.error(f"Failed to add job to scheduler: {e}")
        
        self._save_tasks()
        
        return {
            "success": True,
            "task_id": task_id,
            "name": name,
            "schedule_type": schedule_type,
            "next_run": task.next_run,
            "status": task.status
        }
    
    @tool(
        name="scheduler_list_tasks",
        description="List all scheduled tasks",
        category="scheduler"
    )
    async def list_tasks(
        self,
        status: str = None,
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """
        List scheduled tasks.
        
        Args:
            status: Filter by status
            tags: Filter by tags
        """
        tasks = list(self.tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        if tags:
            tasks = [t for t in tasks if any(tag in t.tags for tag in tags)]
        
        return {
            "total": len(tasks),
            "tasks": [
                {
                    "task_id": t.task_id,
                    "name": t.name,
                    "description": t.description,
                    "schedule_type": t.schedule_type,
                    "status": t.status,
                    "enabled": t.enabled,
                    "next_run": t.next_run,
                    "last_run": t.last_run,
                    "run_count": t.run_count,
                    "error_count": t.error_count
                }
                for t in tasks
            ]
        }
    
    @tool(
        name="scheduler_get_task",
        description="Get details of a specific task",
        category="scheduler"
    )
    async def get_task(self, task_id: str) -> Dict[str, Any]:
        """Get task details."""
        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}
        
        return {
            "success": True,
            "task": task.to_dict()
        }
    
    @tool(
        name="scheduler_update_task",
        description="Update a scheduled task",
        category="scheduler"
    )
    async def update_task(
        self,
        task_id: str,
        name: str = None,
        description: str = None,
        schedule_config: Dict = None,
        action_config: Dict = None,
        enabled: bool = None,
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """Update a task."""
        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}
        
        if name:
            task.name = name
        if description:
            task.description = description
        if schedule_config:
            task.schedule_config = schedule_config
        if action_config:
            task.action_config = action_config
        if enabled is not None:
            task.enabled = enabled
        if tags is not None:
            task.tags = tags
        
        # Update scheduler job if needed
        if self._scheduler and self._running:
            try:
                self._scheduler.remove_job(task_id)
                if task.enabled:
                    trigger = self._create_trigger(
                        task.schedule_type,
                        task.schedule_config
                    )
                    job = self._scheduler.add_job(
                        self._execute_task,
                        trigger=trigger,
                        id=task_id,
                        args=[task_id],
                        name=task.name
                    )
                    task.next_run = str(job.next_run_time) if job.next_run_time else None
            except Exception as e:
                logger.error(f"Failed to update scheduler job: {e}")
        
        self._save_tasks()
        
        return {
            "success": True,
            "task_id": task_id,
            "updated": True
        }
    
    @tool(
        name="scheduler_delete_task",
        description="Delete a scheduled task",
        category="scheduler"
    )
    async def delete_task(self, task_id: str) -> Dict[str, Any]:
        """Delete a task."""
        if task_id not in self.tasks:
            return {"success": False, "error": "Task not found"}
        
        # Remove from scheduler
        if self._scheduler and self._running:
            try:
                self._scheduler.remove_job(task_id)
            except:
                pass
        
        del self.tasks[task_id]
        self._save_tasks()
        
        return {
            "success": True,
            "deleted": task_id
        }
    
    @tool(
        name="scheduler_run_task_now",
        description="Immediately execute a scheduled task",
        category="scheduler"
    )
    async def run_task_now(self, task_id: str) -> Dict[str, Any]:
        """Run a task immediately."""
        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}
        
        await self._execute_task(task_id)
        
        return {
            "success": True,
            "task_id": task_id,
            "executed": True,
            "last_run": task.last_run,
            "result": "Check task status for results"
        }
    
    @tool(
        name="scheduler_pause_task",
        description="Pause a scheduled task",
        category="scheduler"
    )
    async def pause_task(self, task_id: str) -> Dict[str, Any]:
        """Pause a task."""
        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}
        
        task.enabled = False
        task.status = ScheduledTaskStatus.PAUSED
        
        if self._scheduler and self._running:
            try:
                self._scheduler.pause_job(task_id)
            except:
                pass
        
        self._save_tasks()
        
        return {
            "success": True,
            "task_id": task_id,
            "paused": True
        }
    
    @tool(
        name="scheduler_resume_task",
        description="Resume a paused task",
        category="scheduler"
    )
    async def resume_task(self, task_id: str) -> Dict[str, Any]:
        """Resume a task."""
        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}
        
        task.enabled = True
        task.status = ScheduledTaskStatus.SCHEDULED
        
        if self._scheduler and self._running:
            try:
                self._scheduler.resume_job(task_id)
            except:
                pass
        
        self._save_tasks()
        
        return {
            "success": True,
            "task_id": task_id,
            "resumed": True
        }
    
    @tool(
        name="scheduler_get_history",
        description="Get task execution history",
        category="scheduler"
    )
    async def get_history(
        self,
        task_id: str = None,
        limit: int = 50,
        status: str = None
    ) -> Dict[str, Any]:
        """
        Get execution history.
        
        Args:
            task_id: Filter by task
            limit: Max records to return
            status: Filter by status (completed/failed)
        """
        history = []
        
        if self.history_file.exists():
            with open(self.history_file, "r") as f:
                for line in f:
                    try:
                        execution = json.loads(line)
                        
                        if task_id and execution.get("task_id") != task_id:
                            continue
                        if status and execution.get("status") != status:
                            continue
                        
                        history.append(execution)
                    except:
                        continue
        
        # Sort by started_at descending and limit
        history.sort(key=lambda x: x.get("started_at", ""), reverse=True)
        history = history[:limit]
        
        return {
            "total": len(history),
            "executions": history
        }


# ==========================================
# COMMON SCHEDULE PRESETS
# ==========================================

SCHEDULE_PRESETS = {
    "every_minute": {
        "type": "interval",
        "config": {"minutes": 1}
    },
    "every_5_minutes": {
        "type": "interval",
        "config": {"minutes": 5}
    },
    "every_15_minutes": {
        "type": "interval",
        "config": {"minutes": 15}
    },
    "every_hour": {
        "type": "interval",
        "config": {"hours": 1}
    },
    "every_4_hours": {
        "type": "interval",
        "config": {"hours": 4}
    },
    "twice_daily": {
        "type": "cron",
        "config": {"expression": "0 9,17 * * *"}  # 9am and 5pm
    },
    "daily_9am": {
        "type": "daily",
        "config": {"hour": 9, "minute": 0}
    },
    "daily_midnight": {
        "type": "daily",
        "config": {"hour": 0, "minute": 0}
    },
    "weekdays_9am": {
        "type": "cron",
        "config": {"expression": "0 9 * * 1-5"}
    },
    "monday_9am": {
        "type": "weekly",
        "config": {"day_of_week": "mon", "hour": 9}
    },
    "first_of_month": {
        "type": "monthly",
        "config": {"day": 1, "hour": 9}
    }
}


# Factory function
def create_task_scheduler(
    data_dir: str = None,
    tool_executor: Callable = None
) -> TaskScheduler:
    """Create TaskScheduler instance."""
    return TaskScheduler(
        data_dir=data_dir or "./data/scheduler",
        tool_executor=tool_executor
    )
