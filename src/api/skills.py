"""
Skills API - Skills system management endpoints
==============================================
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

from ..core.skills_system import get_skills_registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("/")
async def list_skills():
    """List all available skills."""
    try:
        registry = get_skills_registry()
        skills = []
        
        for skill_name in registry.list_skills():
            skill = registry.get_skill(skill_name)
            if skill:
                skills.append({
                    'name': skill_name,
                    'description': skill.description,
                    'capabilities': skill.capabilities,
                    'tools_count': len(skill.tools_required),
                    'workflows_count': len(skill.workflows),
                    'domain': skill.metadata.get('domain', 'general'),
                    'complexity': skill.metadata.get('complexity', 'medium')
                })
        
        return {"skills": skills}
    except Exception as e:
        logger.error(f"Error listing skills: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{skill_name}")
async def get_skill(skill_name: str):
    """Get detailed information about a specific skill."""
    try:
        registry = get_skills_registry()
        skill = registry.get_skill(skill_name)
        
        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")
        
        return {
            'name': skill_name,
            'description': skill.description,
            'capabilities': skill.capabilities,
            'tools_required': skill.tools_required,
            'workflows': [{'name': wf['name'], 'definition': wf['definition']} for wf in skill.workflows],
            'best_practices': skill.best_practices,
            'error_handling': skill.error_handling,
            'dependencies': skill.dependencies,
            'metadata': skill.metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting skill: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{skill_name}/workflows")
async def get_skill_workflows(skill_name: str):
    """Get workflows for a specific skill."""
    try:
        registry = get_skills_registry()
        skill = registry.get_skill(skill_name)
        
        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")
        
        return {"workflows": skill.workflows}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting skill workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{skill_name}/workflows/{workflow_name}")
async def get_workflow(skill_name: str, workflow_name: str):
    """Get a specific workflow from a skill."""
    try:
        registry = get_skills_registry()
        skill = registry.get_skill(skill_name)
        
        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")
        
        workflow = skill.get_workflow(workflow_name)
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return {"workflow": workflow}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/capability")
async def search_by_capability(q: str):
    """Find skills by capability."""
    try:
        registry = get_skills_registry()
        skills = registry.find_skills_by_capability(q)
        
        return {
            "query": q,
            "skills": [{
                'name': s.name,
                'description': s.description,
                'capabilities': s.capabilities
            } for s in skills]
        }
    except Exception as e:
        logger.error(f"Error searching skills: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend")
async def recommend_skill(request: Dict[str, str]):
    """Recommend a skill for a given task."""
    try:
        task_description = request.get('task', '')
        
        if not task_description:
            raise HTTPException(status_code=400, detail="Task description required")
        
        registry = get_skills_registry()
        skill = registry.recommend_skill(task_description)
        
        if not skill:
            return {"skill": None, "message": "No matching skill found"}
        
        return {
            "skill": {
                'name': skill.name,
                'description': skill.description,
                'capabilities': skill.capabilities,
                'workflows': [wf['name'] for wf in skill.workflows]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recommending skill: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/all")
async def get_skills_summary():
    """Get summary of all skills."""
    try:
        registry = get_skills_registry()
        summary = registry.get_skills_summary()
        return summary
    except Exception as e:
        logger.error(f"Error getting skills summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
