"""
Otto Universal - Business API Endpoints
=======================================

REST API endpoints for autonomous business operations.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from enum import Enum

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/business", tags=["Business Operations"])

# Global reference to orchestrator (set by main.py)
_autonomous_orchestrator = None
_workflow_generator = None


def set_business_orchestrator(orchestrator, workflow_gen):
    """Set the autonomous orchestrator and workflow generator."""
    global _autonomous_orchestrator, _workflow_generator
    _autonomous_orchestrator = orchestrator
    _workflow_generator = workflow_gen


# Request/Response Models

class BusinessDomainEnum(str, Enum):
    """Business domains."""
    ECOMMERCE = "ecommerce"
    MARKETING = "marketing"
    CONTENT_CREATION = "content_creation"
    DATA_ANALYSIS = "data_analysis"
    CUSTOMER_SERVICE = "customer_service"
    PRODUCT_DEVELOPMENT = "product_development"
    OPERATIONS = "operations"
    FINANCE = "finance"


class TaskPriorityEnum(str, Enum):
    """Task priorities."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BusinessContextModel(BaseModel):
    """Business context for operations."""
    domain: BusinessDomainEnum
    goals: List[str]
    constraints: List[str] = []
    budget: Optional[float] = None
    deadline: Optional[datetime] = None
    stakeholders: List[str] = []
    

class BusinessRequestModel(BaseModel):
    """Request for autonomous business execution."""
    request: str = Field(..., description="Natural language business request")
    session_id: str = Field(..., description="Session identifier")
    priority: TaskPriorityEnum = TaskPriorityEnum.MEDIUM
    context: Optional[BusinessContextModel] = None
    stream: bool = False


class WorkflowTypeEnum(str, Enum):
    """Workflow types."""
    PRODUCT_LAUNCH = "product_launch"
    MARKETING_CAMPAIGN = "marketing_campaign"
    CONTENT_PIPELINE = "content_pipeline"
    EMAIL_SEQUENCE = "email_sequence"


class WorkflowExecutionModel(BaseModel):
    """Request to execute a workflow."""
    workflow_type: WorkflowTypeEnum
    params: Dict[str, Any]
    session_id: str


class CustomWorkflowModel(BaseModel):
    """Request to generate custom workflow."""
    goal: str
    constraints: List[str] = []
    available_tools: List[str] = []


# API Endpoints

@router.post("/execute")
async def execute_business_request(request: BusinessRequestModel):
    """
    Execute a business request with full autonomy.
    
    This endpoint handles end-to-end business operations:
    - Intelligent planning with reasoning chains
    - Adaptive execution with self-correction
    - Business impact analysis with KPIs
    - Persistent memory and learning
    """
    if not _autonomous_orchestrator:
        raise HTTPException(status_code=503, detail="Autonomous orchestrator not initialized")
    
    try:
        # Convert Pydantic models to dataclass instances
        from ..core.autonomous_orchestrator import BusinessContext, BusinessDomain
        
        business_context = None
        if request.context:
            business_context = BusinessContext(
                domain=BusinessDomain[request.context.domain.value.upper()],
                goals=request.context.goals,
                constraints=request.context.constraints,
                kpis={},
                budget=request.context.budget,
                deadline=request.context.deadline,
                stakeholders=request.context.stakeholders
            )
        
        # Execute business request
        result = await _autonomous_orchestrator.execute_business_request(
            request=request.request,
            session_id=request.session_id,
            business_context=business_context
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Business execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows")
async def list_workflows():
    """
    List all available business workflow templates.
    
    Returns pre-built workflows for common business operations
    like product launches, marketing campaigns, content pipelines, etc.
    """
    if not _workflow_generator:
        raise HTTPException(status_code=503, detail="Workflow generator not initialized")
    
    try:
        workflows = _workflow_generator.list_available_workflows()
        return {
            "workflows": workflows,
            "total": len(workflows)
        }
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows/execute")
async def execute_workflow(request: WorkflowExecutionModel):
    """
    Execute a pre-built business workflow.
    
    Workflows are structured sequences of tasks optimized for
    specific business operations. They include:
    - Step-by-step execution plan
    - Tool orchestration
    - Error handling and retries
    - KPI tracking
    """
    if not _workflow_generator:
        raise HTTPException(status_code=503, detail="Workflow generator not initialized")
    
    try:
        # Get workflow template
        from ..core.business_workflows import WorkflowType
        workflow_type = WorkflowType[request.workflow_type.value.upper()]
        workflow = _workflow_generator.templates.get(workflow_type)
        
        if not workflow:
            raise HTTPException(status_code=404, detail=f"Workflow {request.workflow_type} not found")
        
        # Execute workflow
        result = await _workflow_generator.execute_workflow(
            workflow=workflow,
            params=request.params
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows/custom")
async def generate_custom_workflow(request: CustomWorkflowModel):
    """
    Generate a custom workflow based on business requirements.
    
    Uses AI to create a tailored workflow for specific needs.
    The generated workflow can be saved and reused.
    """
    if not _workflow_generator:
        raise HTTPException(status_code=503, detail="Workflow generator not initialized")
    
    try:
        workflow = await _workflow_generator.generate_custom_workflow(
            goal=request.goal,
            constraints=request.constraints,
            available_tools=request.available_tools or []
        )
        
        return {
            "success": True,
            "workflow": {
                "name": workflow.name,
                "description": workflow.description,
                "steps": len(workflow.steps),
                "estimated_duration": workflow.estimated_duration,
                "kpis": workflow.kpis
            }
        }
        
    except Exception as e:
        logger.error(f"Custom workflow generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kpis")
async def get_kpi_summary():
    """
    Get summary of tracked business KPIs.
    
    Returns current values, targets, achievement rates, and
    historical trends for all tracked KPIs.
    """
    if not _autonomous_orchestrator:
        raise HTTPException(status_code=503, detail="Autonomous orchestrator not initialized")
    
    try:
        summary = _autonomous_orchestrator.get_kpi_summary()
        return summary
    except Exception as e:
        logger.error(f"Failed to get KPI summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
async def get_active_tasks():
    """
    Get all active and recent tasks.
    
    Returns task status, progress, reasoning chains, and results.
    """
    if not _autonomous_orchestrator:
        raise HTTPException(status_code=503, detail="Autonomous orchestrator not initialized")
    
    try:
        return {
            "active_tasks": [
                {
                    "id": task.id,
                    "description": task.description,
                    "status": task.status.value,
                    "priority": task.priority.value,
                    "domain": task.domain.value,
                    "created_at": task.created_at.isoformat(),
                    "duration": task.duration
                }
                for task in _autonomous_orchestrator.active_tasks.values()
            ],
            "recent_history": [
                {
                    "id": task.id,
                    "description": task.description,
                    "status": task.status.value,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "duration": task.duration
                }
                for task in _autonomous_orchestrator.task_history[-10:]
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}")
async def get_task_detail(task_id: str):
    """
    Get detailed information about a specific task.
    
    Includes full reasoning chain, subtasks, results, and business impact.
    """
    if not _autonomous_orchestrator:
        raise HTTPException(status_code=503, detail="Autonomous orchestrator not initialized")
    
    try:
        # Check active tasks
        task = _autonomous_orchestrator.active_tasks.get(task_id)
        
        # Check history if not active
        if not task:
            task = next(
                (t for t in _autonomous_orchestrator.task_history if t.id == task_id),
                None
            )
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "id": task.id,
            "description": task.description,
            "status": task.status.value,
            "priority": task.priority.value,
            "domain": task.domain.value,
            "assigned_agent": task.assigned_agent,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "duration": task.duration,
            "reasoning_chain": [
                {
                    "id": step.id,
                    "type": step.step_type,
                    "content": step.content,
                    "confidence": step.confidence,
                    "timestamp": step.timestamp.isoformat()
                }
                for step in task.reasoning_chain
            ],
            "subtasks": [
                {
                    "id": st.id,
                    "description": st.description,
                    "status": st.status.value
                }
                for st in task.subtasks
            ],
            "results": task.results,
            "errors": task.errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analytics/impact")
async def analyze_business_impact(
    task_id: str,
    timeframe_days: int = 30
):
    """
    Analyze the business impact of completed tasks.
    
    Provides insights on:
    - Revenue impact
    - Efficiency gains
    - Cost savings
    - Strategic value
    """
    if not _autonomous_orchestrator:
        raise HTTPException(status_code=503, detail="Autonomous orchestrator not initialized")
    
    try:
        # Get task
        task = next(
            (t for t in _autonomous_orchestrator.task_history if t.id == task_id),
            None
        )
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Calculate impact (simplified - real implementation would query actual data)
        impact = {
            "task_id": task_id,
            "domain": task.domain.value,
            "metrics": {
                "completion_rate": 1.0 if task.status.value == "completed" else 0.0,
                "execution_time": task.duration,
                "efficiency_score": 0.85,  # Placeholder
                "quality_score": 0.90  # Placeholder
            },
            "business_value": {
                "estimated_revenue_impact": 0,  # Would calculate from actual results
                "time_saved_hours": task.duration / 3600 if task.duration else 0,
                "cost_savings": 0,
                "strategic_value": "high"  # Would analyze from context
            }
        }
        
        return impact
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze impact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize")
async def optimize_workflow(
    workflow_type: WorkflowTypeEnum,
    historical_data: Dict[str, Any]
):
    """
    Optimize a workflow based on historical performance data.
    
    Uses machine learning and heuristics to:
    - Identify bottlenecks
    - Suggest improvements
    - Reorder steps for efficiency
    - Adjust parameters
    """
    return {
        "message": "Workflow optimization coming in next iteration",
        "workflow_type": workflow_type,
        "recommendations": [
            "Parallel execution of independent steps",
            "Caching of repeated operations",
            "Pre-loading of resources"
        ]
    }


@router.get("/health")
async def business_health():
    """Health check for business operations system."""
    return {
        "status": "operational",
        "components": {
            "autonomous_orchestrator": _autonomous_orchestrator is not None,
            "workflow_generator": _workflow_generator is not None
        }
    }
