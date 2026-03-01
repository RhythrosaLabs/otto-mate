"""
Task Models
===========

Shared task-related models, enums, and dataclasses used across the codebase.
Consolidates definitions from task_queue_manager.py and task_queue_engine.py.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    PLANNING = "planning"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class ArtifactType(Enum):
    """Types of artifacts that can be generated."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"
    FILE = "file"
    PRODUCT = "product"
    BLOG = "blog"
    SOCIAL_POST = "social_post"
    EMAIL = "email"
    UPLOAD = "upload"
    CODE = "code"
    DATA = "data"


@dataclass
class Artifact:
    """Represents a generated artifact from task execution."""
    id: str
    type: ArtifactType
    name: str
    url: Optional[str] = None
    content: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    file_path: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "url": self.url,
            "content": self.content[:500] if self.content and len(self.content) > 500 else self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "file_path": self.file_path,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Artifact":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            type=ArtifactType(data.get("type", "file")),
            name=data.get("name", "Untitled"),
            url=data.get("url"),
            content=data.get("content"),
            metadata=data.get("metadata", {}),
            file_path=data.get("file_path"),
        )


@dataclass
class TaskStep:
    """Represents a single step in task execution."""
    id: str
    name: str
    description: str
    agent: str  # designer, writer, video, publisher, browser, etc.
    action: str
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict] = None
    artifacts: List[Artifact] = field(default_factory=list)
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    depends_on: List[str] = field(default_factory=list)
    
    # Legacy compatibility fields
    tool_name: Optional[str] = None  # Alias for action
    parameters: Optional[Dict] = None  # For backwards compatibility

    def duration(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "agent": self.agent,
            "action": self.action,
            "tool_name": self.tool_name or self.action,
            "parameters": self.parameters or {},
            "status": self.status.value,
            "result": self.result,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "depends_on": self.depends_on,
            "duration": self.duration(),
        }


@dataclass
class Task:
    """Represents a complete task in the queue."""
    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL

    # Planning
    plan: Optional[Dict] = None
    steps: List[TaskStep] = field(default_factory=list)
    current_step: int = 0

    # Execution context
    context: Dict = field(default_factory=dict)
    artifacts: List[Artifact] = field(default_factory=list)

    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_for: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Dependencies
    depends_on: List[str] = field(default_factory=list)

    # Results
    final_summary: str = ""
    error: Optional[str] = None

    # Publishing targets
    publish_to: List[str] = field(default_factory=list)

    # Recurrence
    recurring: bool = False
    recurrence_pattern: Optional[str] = None

    # Project association
    project_id: Optional[str] = None

    def duration(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "plan": self.plan,
            "steps": [s.to_dict() for s in self.steps],
            "current_step": self.current_step,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "created_at": self.created_at.isoformat(),
            "scheduled_for": self.scheduled_for.isoformat() if self.scheduled_for else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "depends_on": self.depends_on,
            "final_summary": self.final_summary,
            "error": self.error,
            "publish_to": self.publish_to,
            "recurring": self.recurring,
            "recurrence_pattern": self.recurrence_pattern,
            "project_id": self.project_id,
            "duration": self.duration(),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Task":
        """Create a Task from a dictionary."""
        task = cls(
            id=data.get("id", str(uuid.uuid4())),
            description=data.get("description", ""),
            status=TaskStatus(data.get("status", "pending")),
            priority=TaskPriority(data.get("priority", 2)),
        )
        
        if data.get("plan"):
            task.plan = data["plan"]
        if data.get("context"):
            task.context = data["context"]
        if data.get("publish_to"):
            task.publish_to = data["publish_to"]
        if data.get("recurring"):
            task.recurring = data["recurring"]
        if data.get("recurrence_pattern"):
            task.recurrence_pattern = data["recurrence_pattern"]
        if data.get("project_id"):
            task.project_id = data["project_id"]
            
        return task
