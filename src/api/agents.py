# Agents API Router

import logging
import uuid
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agents", tags=["agents"])

_orchestrator = None

def set_orchestrator(orch):
    global _orchestrator
    _orchestrator = orch

def get_orchestrator():
    if _orchestrator is None:
        raise HTTPException(status_code=503, detail="Not initialized")
    return _orchestrator

class AgentCreate(BaseModel):
    name: str
    description: str = ""
    capabilities: List[str] = []
    system_prompt: Optional[str] = None
    model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.7
    max_tokens: int = 4096
    tools: List[str] = []
    color: str = "#6366f1"
    icon: str = "bot"

@router.get("")
async def list_agents():
    otto = get_orchestrator()
    return {"agents": otto.master.get_agent_list()}

@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    otto = get_orchestrator()
    for a in otto.master.get_agent_list():
        if a["id"] == agent_id:
            return a
    raise HTTPException(status_code=404, detail="Not found")

@router.post("")
async def create_agent(req: AgentCreate):
    from ..core.master_agent import AgentConfig, AgentRole, AgentCapability
    otto = get_orchestrator()
    aid = "custom_" + uuid.uuid4().hex[:8]
    caps = []
    for c in req.capabilities:
        try:
            caps.append(AgentCapability(c))
        except:
            pass
    cfg = AgentConfig(
        id=aid, name=req.name, role=AgentRole.CUSTOM, description=req.description,
        capabilities=caps, system_prompt=req.system_prompt or "You are " + req.name,
        model=req.model, temperature=req.temperature, max_tokens=req.max_tokens,
        tools=req.tools, color=req.color, icon=req.icon)
    otto.master.save_agent(cfg)
    return {"success": True, "agent": cfg.to_dict()}

@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    otto = get_orchestrator()
    if not agent_id.startswith("custom_"):
        raise HTTPException(status_code=400, detail="Cannot delete default")
    if otto.master.delete_agent(agent_id):
        return {"success": True}
    raise HTTPException(status_code=404, detail="Not found")
