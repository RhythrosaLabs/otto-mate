"""
SQLAlchemy Database Models
==========================

Defines all database tables for Otto's structured data.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    Float, JSON, ForeignKey, Enum, Index, Table
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()


# ═══════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════

class TaskStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class AssetType(enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    MODEL_3D = "3d"
    CODE = "code"
    OTHER = "other"


class ScheduleType(enum.Enum):
    ONCE = "once"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CRON = "cron"


# ═══════════════════════════════════════════════════════════════════
# ASSOCIATION TABLES
# ═══════════════════════════════════════════════════════════════════

project_conversations = Table(
    'project_conversations',
    Base.metadata,
    Column('project_id', String(64), ForeignKey('projects.id'), primary_key=True),
    Column('conversation_id', String(64), ForeignKey('conversations.id'), primary_key=True)
)

project_assets = Table(
    'project_assets',
    Base.metadata,
    Column('project_id', String(64), ForeignKey('projects.id'), primary_key=True),
    Column('asset_id', String(64), ForeignKey('generated_assets.id'), primary_key=True)
)


# ═══════════════════════════════════════════════════════════════════
# CORE MODELS
# ═══════════════════════════════════════════════════════════════════

class UserProfile(Base):
    """User profile and preferences."""
    __tablename__ = 'user_profiles'
    
    id = Column(String(64), primary_key=True)
    name = Column(String(255))
    email = Column(String(255))
    preferences = Column(JSON, default=dict)
    context = Column(JSON, default=dict)  # Business context, goals, etc.
    
    # Stats
    total_messages = Column(Integer, default=0)
    total_tasks = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    projects = relationship("Project", back_populates="user")


class Conversation(Base):
    """Chat conversation session."""
    __tablename__ = 'conversations'
    
    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey('user_profiles.id'), nullable=True)
    title = Column(String(500), default="New Chat")
    summary = Column(Text)  # AI-generated summary
    
    # Metadata
    model_used = Column(String(100))
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    
    # Status
    is_archived = Column(Boolean, default=False)
    is_starred = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("UserProfile", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    projects = relationship("Project", secondary=project_conversations, back_populates="conversations")
    
    # Indexes
    __table_args__ = (
        Index('idx_conversation_user', 'user_id'),
        Index('idx_conversation_created', 'created_at'),
    )


class Message(Base):
    """Individual chat message."""
    __tablename__ = 'messages'
    
    id = Column(String(64), primary_key=True)
    conversation_id = Column(String(64), ForeignKey('conversations.id'), nullable=False)
    
    role = Column(String(20))  # user, assistant, system, tool
    content = Column(Text)
    
    # Tool execution data
    tool_name = Column(String(100))
    tool_input = Column(JSON)
    tool_output = Column(JSON)
    
    # Metadata
    tokens = Column(Integer, default=0)
    model = Column(String(100))
    latency_ms = Column(Integer)
    
    # For tool results
    is_error = Column(Boolean, default=False)
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    # Indexes
    __table_args__ = (
        Index('idx_message_conversation', 'conversation_id'),
        Index('idx_message_created', 'created_at'),
        Index('idx_message_role', 'role'),
    )


class Project(Base):
    """Project container for organizing work."""
    __tablename__ = 'projects'
    
    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey('user_profiles.id'), nullable=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="active")
    
    # Project metadata
    tags = Column(JSON, default=list)
    settings = Column(JSON, default=dict)
    
    # Progress tracking
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("UserProfile", back_populates="projects")
    conversations = relationship("Conversation", secondary=project_conversations, back_populates="projects")
    assets = relationship("GeneratedAsset", secondary=project_assets, back_populates="projects")
    tasks = relationship("Task", back_populates="project")
    workflows = relationship("Workflow", back_populates="project")
    
    # Indexes
    __table_args__ = (
        Index('idx_project_user', 'user_id'),
        Index('idx_project_status', 'status'),
    )


class Task(Base):
    """Task execution record."""
    __tablename__ = 'tasks'
    
    id = Column(String(64), primary_key=True)
    project_id = Column(String(64), ForeignKey('projects.id'), nullable=True)
    conversation_id = Column(String(64), ForeignKey('conversations.id'), nullable=True)
    
    # Task details
    name = Column(String(255))
    description = Column(Text)
    task_type = Column(String(50))  # generation, analysis, automation, etc.
    
    # Execution
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    priority = Column(Integer, default=5)  # 1-10
    
    # Input/Output
    input_data = Column(JSON)
    output_data = Column(JSON)
    
    # Timing
    scheduled_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="tasks")
    
    # Indexes
    __table_args__ = (
        Index('idx_task_status', 'status'),
        Index('idx_task_project', 'project_id'),
        Index('idx_task_scheduled', 'scheduled_at'),
    )


class ScheduledTask(Base):
    """Recurring/scheduled task definition."""
    __tablename__ = 'scheduled_tasks'
    
    id = Column(String(64), primary_key=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Schedule configuration
    schedule_type = Column(Enum(ScheduleType), nullable=False)
    cron_expression = Column(String(100))  # For cron type
    interval_seconds = Column(Integer)  # For simple intervals
    
    # Task definition
    task_type = Column(String(50))
    task_config = Column(JSON)  # Tool name, parameters, etc.
    
    # Execution state
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime)
    next_run = Column(DateTime)
    run_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_scheduled_active', 'is_active'),
        Index('idx_scheduled_next_run', 'next_run'),
    )


class GeneratedAsset(Base):
    """Generated file/asset tracking."""
    __tablename__ = 'generated_assets'
    
    id = Column(String(64), primary_key=True)
    conversation_id = Column(String(64), ForeignKey('conversations.id'), nullable=True)
    
    # Asset info
    asset_type = Column(Enum(AssetType), nullable=False)
    filename = Column(String(500))
    file_path = Column(String(1000))
    file_url = Column(String(2000))  # External URL if applicable
    file_size = Column(Integer)
    mime_type = Column(String(100))
    
    # Generation details
    model_used = Column(String(100))
    prompt = Column(Text)
    parameters = Column(JSON)
    generation_time_seconds = Column(Float)
    
    # Metadata
    title = Column(String(500))
    description = Column(Text)
    tags = Column(JSON, default=list)
    
    # External references
    external_id = Column(String(255))  # Printify product ID, etc.
    external_service = Column(String(100))  # printify, shopify, etc.
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    projects = relationship("Project", secondary=project_assets, back_populates="assets")
    
    # Indexes
    __table_args__ = (
        Index('idx_asset_type', 'asset_type'),
        Index('idx_asset_conversation', 'conversation_id'),
        Index('idx_asset_created', 'created_at'),
        Index('idx_asset_external', 'external_service', 'external_id'),
    )


class Workflow(Base):
    """Saved workflow/automation."""
    __tablename__ = 'workflows'
    
    id = Column(String(64), primary_key=True)
    project_id = Column(String(64), ForeignKey('projects.id'), nullable=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Workflow config
    trigger_type = Column(String(50))  # manual, scheduled, webhook
    trigger_config = Column(JSON)
    
    is_active = Column(Boolean, default=True)
    run_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="workflows")
    steps = relationship("WorkflowStep", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowStep(Base):
    """Individual step in a workflow."""
    __tablename__ = 'workflow_steps'
    
    id = Column(String(64), primary_key=True)
    workflow_id = Column(String(64), ForeignKey('workflows.id'), nullable=False)
    
    order = Column(Integer, nullable=False)
    name = Column(String(255))
    
    # Step config
    tool_name = Column(String(100))
    parameters = Column(JSON)
    
    # Conditions
    condition = Column(Text)  # Expression to evaluate
    on_failure = Column(String(50), default="stop")  # stop, continue, retry
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    workflow = relationship("Workflow", back_populates="steps")


class APIUsage(Base):
    """Track API usage for cost monitoring."""
    __tablename__ = 'api_usage'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    service = Column(String(50), nullable=False)  # anthropic, replicate, openai, etc.
    model = Column(String(100))
    operation = Column(String(100))
    
    # Usage metrics
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    compute_seconds = Column(Float, default=0)
    
    # Cost
    cost_usd = Column(Float, default=0)
    
    # Context
    conversation_id = Column(String(64))
    task_id = Column(String(64))
    
    created_at = Column(DateTime, default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_usage_service', 'service'),
        Index('idx_usage_created', 'created_at'),
        Index('idx_usage_conversation', 'conversation_id'),
    )


class ProductRecord(Base):
    """Track products created across platforms."""
    __tablename__ = 'product_records'
    
    id = Column(String(64), primary_key=True)
    
    # Product info
    title = Column(String(500), nullable=False)
    description = Column(Text)
    product_type = Column(String(100))  # t-shirt, mug, poster, etc.
    
    # Platform references
    printify_id = Column(String(100))
    shopify_id = Column(String(100))
    
    # Status
    status = Column(String(50), default="draft")  # draft, published, archived
    
    # Pricing
    base_cost = Column(Float)
    retail_price = Column(Float)
    
    # Media
    primary_image_url = Column(String(2000))
    mockup_urls = Column(JSON, default=list)
    
    # Metadata
    tags = Column(JSON, default=list)
    variants = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_product_printify', 'printify_id'),
        Index('idx_product_shopify', 'shopify_id'),
        Index('idx_product_status', 'status'),
        Index('idx_product_type', 'product_type'),
    )
