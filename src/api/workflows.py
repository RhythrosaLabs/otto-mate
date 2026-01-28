"""
Workflows API - Create and Execute Automated Workflows
=====================================================

Provides endpoints to create, save, and run multi-step workflows.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import json
from pathlib import Path
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workflows", tags=["Workflows"])

# Will be set by main.py
_orchestrator = None

# Workflow storage path
WORKFLOWS_DIR = Path(__file__).parent.parent.parent / "data" / "workflows"
WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)


def set_orchestrator(orchestrator):
    global _orchestrator
    _orchestrator = orchestrator


def get_orchestrator():
    if _orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    return _orchestrator


class WorkflowStep(BaseModel):
    tool: str
    params: Dict[str, Any]
    name: Optional[str] = None
    description: Optional[str] = None


class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    steps: List[WorkflowStep]
    category: Optional[str] = "custom"
    icon: Optional[str] = "⚙️"


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[List[WorkflowStep]] = None
    category: Optional[str] = None
    icon: Optional[str] = None


def _get_workflow_path(workflow_id: str) -> Path:
    return WORKFLOWS_DIR / f"{workflow_id}.json"


def _load_workflow(workflow_id: str) -> Dict[str, Any]:
    path = _get_workflow_path(workflow_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
    return json.loads(path.read_text())


def _save_workflow(workflow_id: str, data: Dict[str, Any]):
    path = _get_workflow_path(workflow_id)
    path.write_text(json.dumps(data, indent=2))


# Default workflow templates
DEFAULT_WORKFLOWS = [
    {
        "id": "product_launch",
        "name": "Product Launch Campaign",
        "description": "Generate product images, descriptions, and social media content",
        "icon": "🚀",
        "category": "marketing",
        "is_template": True,
        "steps": [
            {"tool": "generate_image", "params": {"prompt": "{{product_name}} product photo"}, "name": "Generate Product Image"},
            {"tool": "generate_product_description", "params": {"product": "{{product_name}}"}, "name": "Write Description"},
            {"tool": "generate_social_media_posts", "params": {"topic": "{{product_name}} launch"}, "name": "Create Social Posts"},
        ]
    },
    {
        "id": "content_creation",
        "name": "Blog Content Pipeline",
        "description": "Research, write, and create images for blog posts",
        "icon": "📝",
        "category": "content",
        "is_template": True,
        "steps": [
            {"tool": "research_topic", "params": {"topic": "{{topic}}"}, "name": "Research Topic"},
            {"tool": "generate_blog_post", "params": {"topic": "{{topic}}"}, "name": "Write Blog Post"},
            {"tool": "generate_image", "params": {"prompt": "Blog header image for {{topic}}"}, "name": "Create Header Image"},
        ]
    },
    {
        "id": "tshirt_design",
        "name": "T-Shirt Design to Store",
        "description": "Generate design, create product, and publish to Printify",
        "icon": "👕",
        "category": "ecommerce",
        "is_template": True,
        "steps": [
            {"tool": "generate_tshirt_design", "params": {"theme": "{{theme}}"}, "name": "Generate Design"},
            {"tool": "remove_background", "params": {}, "name": "Remove Background"},
            {"tool": "printify_create_product", "params": {"title": "{{title}}"}, "name": "Create Product"},
            {"tool": "printify_publish_product", "params": {}, "name": "Publish to Store"},
        ]
    },
    {
        "id": "competitor_analysis",
        "name": "Competitor Analysis",
        "description": "Research competitors and generate insights report",
        "icon": "🔍",
        "category": "research",
        "is_template": True,
        "steps": [
            {"tool": "analyze_competitor", "params": {"competitor": "{{competitor_url}}"}, "name": "Analyze Competitor"},
            {"tool": "search_web", "params": {"query": "{{competitor}} reviews"}, "name": "Find Reviews"},
            {"tool": "improve_text", "params": {"purpose": "analysis report"}, "name": "Generate Report"},
        ]
    }
]


@router.get("/")
async def list_workflows():
    """List all workflows including templates and custom."""
    workflows = []
    
    # Add default templates
    for template in DEFAULT_WORKFLOWS:
        workflows.append({**template, "is_template": True})
    
    # Add custom workflows from storage
    if WORKFLOWS_DIR.exists():
        for path in WORKFLOWS_DIR.glob("*.json"):
            try:
                workflow = json.loads(path.read_text())
                workflow["is_template"] = False
                workflows.append(workflow)
            except Exception as e:
                logger.error(f"Failed to load workflow {path}: {e}")
    
    return {
        "workflows": workflows,
        "categories": [
            {"id": "marketing", "name": "Marketing", "icon": "📢"},
            {"id": "content", "name": "Content", "icon": "📝"},
            {"id": "ecommerce", "name": "E-Commerce", "icon": "🛒"},
            {"id": "research", "name": "Research", "icon": "🔍"},
            {"id": "custom", "name": "Custom", "icon": "⚙️"},
        ]
    }


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get a specific workflow by ID."""
    # Check templates first
    for template in DEFAULT_WORKFLOWS:
        if template["id"] == workflow_id:
            return {**template, "is_template": True}
    
    # Check custom workflows
    return _load_workflow(workflow_id)


@router.post("/")
async def create_workflow(workflow: WorkflowCreate):
    """Create a new custom workflow."""
    workflow_id = str(uuid.uuid4())[:8]
    
    data = {
        "id": workflow_id,
        "name": workflow.name,
        "description": workflow.description,
        "icon": workflow.icon,
        "category": workflow.category,
        "steps": [step.dict() for step in workflow.steps],
        "created_at": datetime.now().isoformat(),
        "is_template": False
    }
    
    _save_workflow(workflow_id, data)
    logger.info(f"Created workflow: {workflow_id} - {workflow.name}")
    
    return data


@router.put("/{workflow_id}")
async def update_workflow(workflow_id: str, update: WorkflowUpdate):
    """Update an existing workflow."""
    # Can't update templates
    for template in DEFAULT_WORKFLOWS:
        if template["id"] == workflow_id:
            raise HTTPException(status_code=400, detail="Cannot modify template workflows")
    
    data = _load_workflow(workflow_id)
    
    if update.name:
        data["name"] = update.name
    if update.description:
        data["description"] = update.description
    if update.steps:
        data["steps"] = [step.dict() for step in update.steps]
    if update.category:
        data["category"] = update.category
    if update.icon:
        data["icon"] = update.icon
    
    data["updated_at"] = datetime.now().isoformat()
    _save_workflow(workflow_id, data)
    
    return data


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a custom workflow."""
    # Can't delete templates
    for template in DEFAULT_WORKFLOWS:
        if template["id"] == workflow_id:
            raise HTTPException(status_code=400, detail="Cannot delete template workflows")
    
    path = _get_workflow_path(workflow_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    path.unlink()
    logger.info(f"Deleted workflow: {workflow_id}")
    
    return {"deleted": True, "id": workflow_id}


@router.post("/{workflow_id}/run")
async def run_workflow(workflow_id: str, variables: Dict[str, Any] = {}):
    """Execute a workflow with the given variables."""
    otto = get_orchestrator()
    
    # Get workflow
    workflow = None
    for template in DEFAULT_WORKFLOWS:
        if template["id"] == workflow_id:
            workflow = template
            break
    
    if not workflow:
        workflow = _load_workflow(workflow_id)
    
    results = []
    
    try:
        for i, step in enumerate(workflow["steps"]):
            # Replace variables in params
            params = {}
            for key, value in step["params"].items():
                if isinstance(value, str):
                    for var_name, var_value in variables.items():
                        value = value.replace(f"{{{{{var_name}}}}}", str(var_value))
                params[key] = value
            
            # Execute the tool
            logger.info(f"Running step {i+1}: {step['tool']}")
            
            tool = otto.tool_registry.get_tool(step["tool"])
            if tool:
                try:
                    result = await tool["function"](**params)
                    results.append({
                        "step": i + 1,
                        "tool": step["tool"],
                        "name": step.get("name", step["tool"]),
                        "status": "success",
                        "result": result
                    })
                except Exception as e:
                    results.append({
                        "step": i + 1,
                        "tool": step["tool"],
                        "name": step.get("name", step["tool"]),
                        "status": "error",
                        "error": str(e)
                    })
            else:
                results.append({
                    "step": i + 1,
                    "tool": step["tool"],
                    "name": step.get("name", step["tool"]),
                    "status": "error",
                    "error": f"Tool not found: {step['tool']}"
                })
        
        return {
            "workflow_id": workflow_id,
            "workflow_name": workflow["name"],
            "status": "completed",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/from-chat")
async def create_workflow_from_chat(session_id: str):
    """Create a workflow from a chat conversation's executed steps."""
    otto = get_orchestrator()
    
    # Get session history
    try:
        history = await otto.memory_agent.get_session_history(session_id)
        
        # Extract tool executions from history
        steps = []
        for msg in history:
            meta = msg.get("metadata", {})
            if meta.get("type") == "tool_response":
                plan_json = meta.get("plan_json")
                if plan_json:
                    plan = json.loads(plan_json)
                    for step in plan.get("steps", []):
                        steps.append({
                            "tool": step.get("tool"),
                            "params": step.get("params", {}),
                            "name": step.get("description", step.get("tool"))
                        })
        
        if not steps:
            return {"error": "No tool executions found in this chat session"}
        
        return {
            "suggested_steps": steps,
            "session_id": session_id,
            "message": "Review and save these steps as a workflow"
        }
        
    except Exception as e:
        logger.error(f"Failed to create workflow from chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))
