"""
Task Queue Management System
============================
Autonomous task planning, execution, and artifact management.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import json
from pathlib import Path

# Import shared task models
from .task_models import (
    TaskStatus, 
    TaskPriority, 
    ArtifactType, 
    Artifact, 
    TaskStep, 
    Task
)

logger = logging.getLogger(__name__)


class TaskQueueManager:
    """Manages task queue with planning and execution."""
    
    def __init__(self, data_dir: str = "data/task_queue"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.tasks: Dict[str, Task] = {}
        self.queue: List[str] = []  # Task IDs in priority order
        
    def queue_task(
        self,
        description: str,
        priority: str = "normal",
        schedule_for: Optional[datetime] = None,
        publish_to: Optional[List[str]] = None,
        recurring: bool = False,
        recurrence_pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add task to queue."""
        import uuid
        
        task_id = str(uuid.uuid4())
        priority_enum = TaskPriority[priority.upper()]
        
        task = Task(
            id=task_id,
            description=description,
            priority=priority_enum,
            scheduled_for=schedule_for,
            publish_to=publish_to or [],
            recurring=recurring,
            recurrence_pattern=recurrence_pattern
        )
        
        self.tasks[task_id] = task
        self._insert_by_priority(task_id)
        self._save_task(task)
        
        logger.info(f"Queued task {task_id}: {description}")
        
        return {
            "success": True,
            "task_id": task_id,
            "status": task.status.value,
            "priority": priority,
            "queue_position": self.queue.index(task_id) + 1
        }
    
    def _insert_by_priority(self, task_id: str):
        """Insert task in queue by priority."""
        task = self.tasks[task_id]
        
        # Find insertion point based on priority
        for i, existing_id in enumerate(self.queue):
            existing_task = self.tasks[existing_id]
            if task.priority.value > existing_task.priority.value:
                self.queue.insert(i, task_id)
                return
        
        # Add to end if lowest priority
        self.queue.append(task_id)
    
    async def plan_task(self, task_id: str, planning_agent: Any) -> Dict[str, Any]:
        """Use planning agent to break task into steps."""
        if task_id not in self.tasks:
            return {"success": False, "error": "Task not found"}
        
        task = self.tasks[task_id]
        task.status = TaskStatus.PLANNING
        
        try:
            # Use super planning agent to create execution plan
            plan = await planning_agent.create_plan(
                objective=task.description,
                context=task.context
            )
            
            # Convert plan steps to TaskStep objects
            steps = []
            for i, step in enumerate(plan.get("steps", [])):
                task_step = TaskStep(
                    id=f"step_{i}",
                    name=step.get("name", f"Step {i+1}"),
                    description=step.get("description", ""),
                    agent=step.get("agent", "orchestrator"),
                    action=step.get("tool", ""),
                    tool_name=step.get("tool", ""),
                    parameters=step.get("parameters", {}),
                    depends_on=step.get("depends_on", [])
                )
                steps.append(task_step)
            
            task.steps = steps
            task.status = TaskStatus.READY
            self._save_task(task)
            
            logger.info(f"Planned task {task_id} with {len(steps)} steps")
            
            return {
                "success": True,
                "task_id": task_id,
                "step_count": len(steps),
                "steps": [s.to_dict() for s in steps]
            }
            
        except Exception as e:
            logger.error(f"Failed to plan task {task_id}: {e}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            return {"success": False, "error": str(e)}
    
    async def execute_task(
        self,
        task_id: str,
        execution_agent: Any,
        background: bool = False
    ) -> Dict[str, Any]:
        """Execute queued task."""
        if task_id not in self.tasks:
            return {"success": False, "error": "Task not found"}
        
        task = self.tasks[task_id]
        
        if task.status != TaskStatus.READY:
            return {"success": False, "error": f"Task not ready (status: {task.status.value})"}
        
        if background:
            # Start async execution
            asyncio.create_task(self._execute_task_steps(task, execution_agent))
            return {
                "success": True,
                "task_id": task_id,
                "status": "running_background"
            }
        else:
            # Execute synchronously
            result = await self._execute_task_steps(task, execution_agent)
            return result
    
    async def _execute_task_steps(self, task: Task, execution_agent: Any) -> Dict[str, Any]:
        """Execute all task steps."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        try:
            for i, step in enumerate(task.steps):
                task.current_step = i
                step.status = TaskStatus.RUNNING
                self._save_task(task)
                
                logger.info(f"Executing step {i+1}/{len(task.steps)}: {step.name}")
                
                # Execute step using execution agent
                result = await execution_agent.execute_tool(
                    tool_name=step.tool_name,
                    parameters=step.parameters
                )
                
                step.result = result
                step.status = TaskStatus.COMPLETED
                
                # Extract artifacts from result
                if result.get("success"):
                    self._extract_artifacts(step, result, task)
                
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            self._save_task(task)
            
            return {
                "success": True,
                "task_id": task.id,
                "status": task.status.value,
                "artifacts": [a.to_dict() for a in task.artifacts]
            }
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            self._save_task(task)
            return {"success": False, "error": str(e)}
    
    def _extract_artifacts(self, step: TaskStep, result: Dict, task: Task):
        """Extract artifacts from step result."""
        import uuid
        
        # Check for image outputs
        if "image_url" in result or "images" in result:
            url = result.get("image_url") or result.get("images", [None])[0]
            if url:
                artifact = Artifact(
                    id=str(uuid.uuid4()),
                    type=ArtifactType.IMAGE,
                    name=f"{step.name} - Image",
                    url=url,
                    metadata={"step_id": step.id, "tool": step.tool_name}
                )
                step.artifacts.append(artifact)
                task.artifacts.append(artifact)
        
        # Check for video outputs
        if "video_url" in result or "video" in result:
            url = result.get("video_url") or result.get("video")
            if url:
                artifact = Artifact(
                    id=str(uuid.uuid4()),
                    type=ArtifactType.VIDEO,
                    name=f"{step.name} - Video",
                    url=url,
                    metadata={"step_id": step.id, "tool": step.tool_name}
                )
                step.artifacts.append(artifact)
                task.artifacts.append(artifact)
        
        # Check for product outputs
        if "product_id" in result:
            artifact = Artifact(
                id=str(uuid.uuid4()),
                type=ArtifactType.PRODUCT,
                name=f"{step.name} - Product",
                content=result.get("product_id"),
                metadata={"step_id": step.id, "tool": step.tool_name, "result": result}
            )
            step.artifacts.append(artifact)
            task.artifacts.append(artifact)
    
    def track_progress(self, task_id: str) -> Dict[str, Any]:
        """Get task execution status."""
        if task_id not in self.tasks:
            return {"success": False, "error": "Task not found"}
        
        task = self.tasks[task_id]
        
        progress = 0
        if task.steps:
            completed = sum(1 for s in task.steps if s.status == TaskStatus.COMPLETED)
            progress = (completed / len(task.steps)) * 100
        
        return {
            "success": True,
            "task_id": task_id,
            "status": task.status.value,
            "current_step": task.current_step + 1,
            "total_steps": len(task.steps),
            "progress": round(progress, 1),
            "artifacts": [a.to_dict() for a in task.artifacts],
            "error": task.error
        }
    
    def manage_artifacts(
        self,
        task_id: str,
        artifact_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get task artifacts."""
        if task_id not in self.tasks:
            return {"success": False, "error": "Task not found"}
        
        task = self.tasks[task_id]
        artifacts = task.artifacts
        
        if artifact_type:
            type_enum = ArtifactType[artifact_type.upper()]
            artifacts = [a for a in artifacts if a.type == type_enum]
        
        return {
            "success": True,
            "task_id": task_id,
            "artifacts": [a.to_dict() for a in artifacts],
            "count": len(artifacts)
        }
    
    def _save_task(self, task: Task):
        """Save task to disk."""
        task_file = self.data_dir / f"{task.id}.json"
        with open(task_file, 'w') as f:
            json.dump(task.to_dict(), f, indent=2)


# Global queue instance
_queue_manager = None

def get_task_queue_manager() -> TaskQueueManager:
    """Get or create global task queue manager."""
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = TaskQueueManager()
    return _queue_manager
