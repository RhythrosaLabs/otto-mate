"""
Database Module
===============

SQLAlchemy-based database for structured data storage.
Replaces scattered JSON files with proper relational database.
"""

from .models import (
    Base,
    Conversation,
    Message,
    Project,
    Task,
    ScheduledTask,
    GeneratedAsset,
    UserProfile,
    Workflow,
    WorkflowStep,
    APIUsage,
    ProductRecord,
)
from .database import (
    Database,
    get_db,
    init_db,
)
from .crud import (
    ConversationCRUD,
    MessageCRUD,
    ProjectCRUD,
    TaskCRUD,
    AssetCRUD,
    WorkflowCRUD,
)

__all__ = [
    # Models
    "Base",
    "Conversation",
    "Message", 
    "Project",
    "Task",
    "ScheduledTask",
    "GeneratedAsset",
    "UserProfile",
    "Workflow",
    "WorkflowStep",
    "APIUsage",
    "ProductRecord",
    # Database
    "Database",
    "get_db",
    "init_db",
    # CRUD
    "ConversationCRUD",
    "MessageCRUD",
    "ProjectCRUD",
    "TaskCRUD",
    "AssetCRUD",
    "WorkflowCRUD",
]
