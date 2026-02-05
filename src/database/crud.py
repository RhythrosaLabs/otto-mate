"""
CRUD Operations
===============

Database CRUD (Create, Read, Update, Delete) operations.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

from .models import (
    Conversation, Message, Project, Task, TaskStatus,
    ScheduledTask, GeneratedAsset, AssetType, UserProfile,
    Workflow, WorkflowStep, APIUsage, ProductRecord
)

logger = logging.getLogger(__name__)


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix."""
    uid = str(uuid4())[:12]
    return f"{prefix}_{uid}" if prefix else uid


# ═══════════════════════════════════════════════════════════════════
# CONVERSATION CRUD
# ═══════════════════════════════════════════════════════════════════

class ConversationCRUD:
    """CRUD operations for conversations."""
    
    @staticmethod
    def create(
        db: Session,
        title: str = "New Chat",
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> Conversation:
        """Create a new conversation."""
        conv = Conversation(
            id=conversation_id or generate_id("conv"),
            user_id=user_id,
            title=title
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv
    
    @staticmethod
    def get(db: Session, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID."""
        return db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    @staticmethod
    def get_or_create(
        db: Session,
        conversation_id: str,
        user_id: Optional[str] = None
    ) -> Conversation:
        """Get existing conversation or create new one."""
        conv = ConversationCRUD.get(db, conversation_id)
        if not conv:
            conv = ConversationCRUD.create(db, conversation_id=conversation_id, user_id=user_id)
        return conv
    
    @staticmethod
    def list_recent(
        db: Session,
        user_id: Optional[str] = None,
        limit: int = 50,
        include_archived: bool = False
    ) -> List[Conversation]:
        """List recent conversations."""
        query = db.query(Conversation)
        
        if user_id:
            query = query.filter(Conversation.user_id == user_id)
        
        if not include_archived:
            query = query.filter(Conversation.is_archived == False)
        
        return query.order_by(desc(Conversation.updated_at)).limit(limit).all()
    
    @staticmethod
    def update(
        db: Session,
        conversation_id: str,
        **kwargs
    ) -> Optional[Conversation]:
        """Update conversation fields."""
        conv = ConversationCRUD.get(db, conversation_id)
        if conv:
            for key, value in kwargs.items():
                if hasattr(conv, key):
                    setattr(conv, key, value)
            conv.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(conv)
        return conv
    
    @staticmethod
    def delete(db: Session, conversation_id: str) -> bool:
        """Delete conversation and its messages."""
        conv = ConversationCRUD.get(db, conversation_id)
        if conv:
            db.delete(conv)
            db.commit()
            return True
        return False
    
    @staticmethod
    def archive(db: Session, conversation_id: str) -> Optional[Conversation]:
        """Archive a conversation."""
        return ConversationCRUD.update(db, conversation_id, is_archived=True)
    
    @staticmethod
    def search(
        db: Session,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Conversation]:
        """Search conversations by title or content."""
        q = db.query(Conversation).join(Message)
        
        if user_id:
            q = q.filter(Conversation.user_id == user_id)
        
        q = q.filter(
            or_(
                Conversation.title.ilike(f"%{query}%"),
                Message.content.ilike(f"%{query}%")
            )
        ).distinct()
        
        return q.order_by(desc(Conversation.updated_at)).limit(limit).all()


# ═══════════════════════════════════════════════════════════════════
# MESSAGE CRUD
# ═══════════════════════════════════════════════════════════════════

class MessageCRUD:
    """CRUD operations for messages."""
    
    @staticmethod
    def create(
        db: Session,
        conversation_id: str,
        role: str,
        content: str,
        tool_name: Optional[str] = None,
        tool_input: Optional[Dict] = None,
        tool_output: Optional[Dict] = None,
        tokens: int = 0,
        model: Optional[str] = None
    ) -> Message:
        """Create a new message."""
        msg = Message(
            id=generate_id("msg"),
            conversation_id=conversation_id,
            role=role,
            content=content,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            tokens=tokens,
            model=model
        )
        db.add(msg)
        
        # Update conversation's updated_at
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conv:
            conv.updated_at = datetime.utcnow()
            conv.total_tokens = (conv.total_tokens or 0) + tokens
        
        db.commit()
        db.refresh(msg)
        return msg
    
    @staticmethod
    def get_conversation_messages(
        db: Session,
        conversation_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Message]:
        """Get messages for a conversation."""
        return db.query(Message)\
            .filter(Message.conversation_id == conversation_id)\
            .order_by(Message.created_at)\
            .offset(offset)\
            .limit(limit)\
            .all()
    
    @staticmethod
    def get_recent_messages(
        db: Session,
        conversation_id: str,
        limit: int = 10
    ) -> List[Message]:
        """Get most recent messages (for context)."""
        messages = db.query(Message)\
            .filter(Message.conversation_id == conversation_id)\
            .order_by(desc(Message.created_at))\
            .limit(limit)\
            .all()
        return list(reversed(messages))  # Return in chronological order
    
    @staticmethod
    def count(db: Session, conversation_id: str) -> int:
        """Count messages in a conversation."""
        return db.query(Message)\
            .filter(Message.conversation_id == conversation_id)\
            .count()


# ═══════════════════════════════════════════════════════════════════
# PROJECT CRUD
# ═══════════════════════════════════════════════════════════════════

class ProjectCRUD:
    """CRUD operations for projects."""
    
    @staticmethod
    def create(
        db: Session,
        name: str,
        description: Optional[str] = None,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Project:
        """Create a new project."""
        project = Project(
            id=generate_id("proj"),
            name=name,
            description=description,
            user_id=user_id,
            tags=tags or []
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project
    
    @staticmethod
    def get(db: Session, project_id: str) -> Optional[Project]:
        """Get project by ID."""
        return db.query(Project).filter(Project.id == project_id).first()
    
    @staticmethod
    def list_all(
        db: Session,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Project]:
        """List projects."""
        query = db.query(Project)
        
        if user_id:
            query = query.filter(Project.user_id == user_id)
        if status:
            query = query.filter(Project.status == status)
        
        return query.order_by(desc(Project.updated_at)).limit(limit).all()
    
    @staticmethod
    def update(db: Session, project_id: str, **kwargs) -> Optional[Project]:
        """Update project fields."""
        project = ProjectCRUD.get(db, project_id)
        if project:
            for key, value in kwargs.items():
                if hasattr(project, key):
                    setattr(project, key, value)
            project.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(project)
        return project
    
    @staticmethod
    def delete(db: Session, project_id: str) -> bool:
        """Delete a project."""
        project = ProjectCRUD.get(db, project_id)
        if project:
            db.delete(project)
            db.commit()
            return True
        return False
    
    @staticmethod
    def add_conversation(db: Session, project_id: str, conversation_id: str) -> bool:
        """Link a conversation to a project."""
        project = ProjectCRUD.get(db, project_id)
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        
        if project and conv:
            if conv not in project.conversations:
                project.conversations.append(conv)
                db.commit()
            return True
        return False


# ═══════════════════════════════════════════════════════════════════
# TASK CRUD
# ═══════════════════════════════════════════════════════════════════

class TaskCRUD:
    """CRUD operations for tasks."""
    
    @staticmethod
    def create(
        db: Session,
        name: str,
        description: Optional[str] = None,
        task_type: str = "general",
        project_id: Optional[str] = None,
        input_data: Optional[Dict] = None,
        priority: int = 5
    ) -> Task:
        """Create a new task."""
        task = Task(
            id=generate_id("task"),
            name=name,
            description=description,
            task_type=task_type,
            project_id=project_id,
            input_data=input_data,
            priority=priority,
            status=TaskStatus.PENDING
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
    
    @staticmethod
    def get(db: Session, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return db.query(Task).filter(Task.id == task_id).first()
    
    @staticmethod
    def list_pending(db: Session, limit: int = 50) -> List[Task]:
        """List pending tasks by priority."""
        return db.query(Task)\
            .filter(Task.status == TaskStatus.PENDING)\
            .order_by(desc(Task.priority), Task.created_at)\
            .limit(limit)\
            .all()
    
    @staticmethod
    def update_status(
        db: Session,
        task_id: str,
        status: TaskStatus,
        output_data: Optional[Dict] = None,
        error_message: Optional[str] = None
    ) -> Optional[Task]:
        """Update task status."""
        task = TaskCRUD.get(db, task_id)
        if task:
            task.status = status
            
            if status == TaskStatus.RUNNING:
                task.started_at = datetime.utcnow()
            elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                task.completed_at = datetime.utcnow()
                if task.started_at:
                    task.duration_seconds = (task.completed_at - task.started_at).total_seconds()
            
            if output_data:
                task.output_data = output_data
            if error_message:
                task.error_message = error_message
            
            task.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(task)
        return task


# ═══════════════════════════════════════════════════════════════════
# ASSET CRUD
# ═══════════════════════════════════════════════════════════════════

class AssetCRUD:
    """CRUD operations for generated assets."""
    
    @staticmethod
    def create(
        db: Session,
        asset_type: AssetType,
        file_path: Optional[str] = None,
        file_url: Optional[str] = None,
        filename: Optional[str] = None,
        conversation_id: Optional[str] = None,
        model_used: Optional[str] = None,
        prompt: Optional[str] = None,
        parameters: Optional[Dict] = None,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> GeneratedAsset:
        """Create a new asset record."""
        asset = GeneratedAsset(
            id=generate_id("asset"),
            asset_type=asset_type,
            file_path=file_path,
            file_url=file_url,
            filename=filename,
            conversation_id=conversation_id,
            model_used=model_used,
            prompt=prompt,
            parameters=parameters,
            title=title,
            tags=tags or []
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)
        return asset
    
    @staticmethod
    def get(db: Session, asset_id: str) -> Optional[GeneratedAsset]:
        """Get asset by ID."""
        return db.query(GeneratedAsset).filter(GeneratedAsset.id == asset_id).first()
    
    @staticmethod
    def list_by_type(
        db: Session,
        asset_type: AssetType,
        limit: int = 50
    ) -> List[GeneratedAsset]:
        """List assets by type."""
        return db.query(GeneratedAsset)\
            .filter(GeneratedAsset.asset_type == asset_type)\
            .order_by(desc(GeneratedAsset.created_at))\
            .limit(limit)\
            .all()
    
    @staticmethod
    def list_by_conversation(
        db: Session,
        conversation_id: str
    ) -> List[GeneratedAsset]:
        """List assets from a conversation."""
        return db.query(GeneratedAsset)\
            .filter(GeneratedAsset.conversation_id == conversation_id)\
            .order_by(GeneratedAsset.created_at)\
            .all()
    
    @staticmethod
    def list_recent(db: Session, limit: int = 50) -> List[GeneratedAsset]:
        """List recent assets."""
        return db.query(GeneratedAsset)\
            .order_by(desc(GeneratedAsset.created_at))\
            .limit(limit)\
            .all()
    
    @staticmethod
    def search_by_prompt(
        db: Session,
        query: str,
        limit: int = 20
    ) -> List[GeneratedAsset]:
        """Search assets by prompt."""
        return db.query(GeneratedAsset)\
            .filter(GeneratedAsset.prompt.ilike(f"%{query}%"))\
            .order_by(desc(GeneratedAsset.created_at))\
            .limit(limit)\
            .all()


# ═══════════════════════════════════════════════════════════════════
# WORKFLOW CRUD
# ═══════════════════════════════════════════════════════════════════

class WorkflowCRUD:
    """CRUD operations for workflows."""
    
    @staticmethod
    def create(
        db: Session,
        name: str,
        description: Optional[str] = None,
        project_id: Optional[str] = None,
        trigger_type: str = "manual",
        steps: Optional[List[Dict]] = None
    ) -> Workflow:
        """Create a new workflow with steps."""
        workflow = Workflow(
            id=generate_id("wf"),
            name=name,
            description=description,
            project_id=project_id,
            trigger_type=trigger_type
        )
        db.add(workflow)
        db.flush()  # Get the workflow ID
        
        # Add steps
        if steps:
            for i, step_data in enumerate(steps):
                step = WorkflowStep(
                    id=generate_id("step"),
                    workflow_id=workflow.id,
                    order=i,
                    name=step_data.get("name", f"Step {i+1}"),
                    tool_name=step_data.get("tool"),
                    parameters=step_data.get("params", {}),
                    condition=step_data.get("condition"),
                    on_failure=step_data.get("on_failure", "stop")
                )
                db.add(step)
        
        db.commit()
        db.refresh(workflow)
        return workflow
    
    @staticmethod
    def get(db: Session, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID."""
        return db.query(Workflow).filter(Workflow.id == workflow_id).first()
    
    @staticmethod
    def list_all(db: Session, project_id: Optional[str] = None) -> List[Workflow]:
        """List all workflows."""
        query = db.query(Workflow)
        if project_id:
            query = query.filter(Workflow.project_id == project_id)
        return query.order_by(desc(Workflow.updated_at)).all()
    
    @staticmethod
    def get_steps(db: Session, workflow_id: str) -> List[WorkflowStep]:
        """Get workflow steps in order."""
        return db.query(WorkflowStep)\
            .filter(WorkflowStep.workflow_id == workflow_id)\
            .order_by(WorkflowStep.order)\
            .all()
    
    @staticmethod
    def increment_run_count(db: Session, workflow_id: str) -> None:
        """Increment the run count for a workflow."""
        workflow = WorkflowCRUD.get(db, workflow_id)
        if workflow:
            workflow.run_count = (workflow.run_count or 0) + 1
            db.commit()


# ═══════════════════════════════════════════════════════════════════
# API USAGE TRACKING
# ═══════════════════════════════════════════════════════════════════

class APIUsageCRUD:
    """Track API usage for cost monitoring."""
    
    @staticmethod
    def log(
        db: Session,
        service: str,
        model: Optional[str] = None,
        operation: Optional[str] = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        compute_seconds: float = 0,
        cost_usd: float = 0,
        conversation_id: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> APIUsage:
        """Log API usage."""
        usage = APIUsage(
            service=service,
            model=model,
            operation=operation,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            compute_seconds=compute_seconds,
            cost_usd=cost_usd,
            conversation_id=conversation_id,
            task_id=task_id
        )
        db.add(usage)
        db.commit()
        return usage
    
    @staticmethod
    def get_daily_usage(db: Session, service: Optional[str] = None) -> Dict[str, Any]:
        """Get usage stats for today."""
        from sqlalchemy import func
        
        today = datetime.utcnow().date()
        query = db.query(
            func.sum(APIUsage.input_tokens).label('total_input'),
            func.sum(APIUsage.output_tokens).label('total_output'),
            func.sum(APIUsage.cost_usd).label('total_cost'),
            func.count(APIUsage.id).label('request_count')
        ).filter(func.date(APIUsage.created_at) == today)
        
        if service:
            query = query.filter(APIUsage.service == service)
        
        result = query.first()
        
        return {
            "date": str(today),
            "input_tokens": result.total_input or 0,
            "output_tokens": result.total_output or 0,
            "total_cost_usd": float(result.total_cost or 0),
            "request_count": result.request_count or 0
        }
    
    @staticmethod
    def get_usage_by_service(db: Session, days: int = 30) -> List[Dict[str, Any]]:
        """Get usage breakdown by service."""
        from sqlalchemy import func
        from datetime import timedelta
        
        since = datetime.utcnow() - timedelta(days=days)
        
        results = db.query(
            APIUsage.service,
            func.sum(APIUsage.cost_usd).label('total_cost'),
            func.count(APIUsage.id).label('request_count')
        ).filter(APIUsage.created_at >= since)\
         .group_by(APIUsage.service)\
         .all()
        
        return [
            {
                "service": r.service,
                "total_cost_usd": float(r.total_cost or 0),
                "request_count": r.request_count
            }
            for r in results
        ]


# ═══════════════════════════════════════════════════════════════════
# PRODUCT RECORDS
# ═══════════════════════════════════════════════════════════════════

class ProductCRUD:
    """CRUD for product records."""
    
    @staticmethod
    def create(
        db: Session,
        title: str,
        product_type: str,
        description: Optional[str] = None,
        printify_id: Optional[str] = None,
        shopify_id: Optional[str] = None,
        base_cost: Optional[float] = None,
        retail_price: Optional[float] = None,
        primary_image_url: Optional[str] = None,
        mockup_urls: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> ProductRecord:
        """Create a product record."""
        product = ProductRecord(
            id=generate_id("prod"),
            title=title,
            product_type=product_type,
            description=description,
            printify_id=printify_id,
            shopify_id=shopify_id,
            base_cost=base_cost,
            retail_price=retail_price,
            primary_image_url=primary_image_url,
            mockup_urls=mockup_urls or [],
            tags=tags or []
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product
    
    @staticmethod
    def get_by_printify_id(db: Session, printify_id: str) -> Optional[ProductRecord]:
        """Get product by Printify ID."""
        return db.query(ProductRecord).filter(ProductRecord.printify_id == printify_id).first()
    
    @staticmethod
    def get_by_shopify_id(db: Session, shopify_id: str) -> Optional[ProductRecord]:
        """Get product by Shopify ID."""
        return db.query(ProductRecord).filter(ProductRecord.shopify_id == shopify_id).first()
    
    @staticmethod
    def list_all(
        db: Session,
        product_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[ProductRecord]:
        """List products."""
        query = db.query(ProductRecord)
        
        if product_type:
            query = query.filter(ProductRecord.product_type == product_type)
        if status:
            query = query.filter(ProductRecord.status == status)
        
        return query.order_by(desc(ProductRecord.created_at)).limit(limit).all()
    
    @staticmethod
    def update(db: Session, product_id: str, **kwargs) -> Optional[ProductRecord]:
        """Update product fields."""
        product = db.query(ProductRecord).filter(ProductRecord.id == product_id).first()
        if product:
            for key, value in kwargs.items():
                if hasattr(product, key):
                    setattr(product, key, value)
            product.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(product)
        return product
