"""Agent API routes (v1)."""
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from ...core.services import AgentService
from .dependencies import get_agent_service
from .schemas import (
    AgentCreateRequest,
    AgentResponse,
    AgentListResponse,
    ToolSchema,
    SuccessResponse
)

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/", response_model=AgentListResponse)
async def list_agents(
    agent_service: AgentService = Depends(get_agent_service)
):
    """List all agents."""
    agents = await agent_service.list_agents()
    
    agent_responses = [
        AgentResponse(
            id=agent.id,
            name=agent.name,
            role=agent.role,
            description=agent.description,
            tools=[
                ToolSchema(
                    name=tool.name,
                    description=tool.description,
                    category=tool.category,
                    parameters=tool.parameters,
                    enabled=tool.enabled
                )
                for tool in agent.tools
            ],
            model=agent.model,
            temperature=agent.temperature,
            max_tokens=agent.max_tokens
        )
        for agent in agents
    ]
    
    return AgentListResponse(
        agents=agent_responses,
        total=len(agent_responses)
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    agent_service: AgentService = Depends(get_agent_service)
):
    """Get agent details."""
    agent = await agent_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        role=agent.role,
        description=agent.description,
        tools=[
            ToolSchema(
                name=tool.name,
                description=tool.description,
                category=tool.category,
                parameters=tool.parameters,
                enabled=tool.enabled
            )
            for tool in agent.tools
        ],
        model=agent.model,
        temperature=agent.temperature,
        max_tokens=agent.max_tokens
    )


@router.post("/", response_model=AgentResponse)
async def create_agent(
    request: AgentCreateRequest,
    agent_service: AgentService = Depends(get_agent_service)
):
    """Create a new agent."""
    try:
        agent = await agent_service.create_agent(
            name=request.name,
            role=request.role,
            description=request.description,
            system_prompt=request.system_prompt,
            tools=request.tools
        )
        
        return AgentResponse(
            id=agent.id,
            name=agent.name,
            role=agent.role,
            description=agent.description,
            tools=[
                ToolSchema(
                    name=tool.name,
                    description=tool.description,
                    category=tool.category,
                    parameters=tool.parameters,
                    enabled=tool.enabled
                )
                for tool in agent.tools
            ],
            model=agent.model,
            temperature=agent.temperature,
            max_tokens=agent.max_tokens
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agent_id}", response_model=SuccessResponse)
async def delete_agent(
    agent_id: str,
    agent_service: AgentService = Depends(get_agent_service)
):
    """Delete an agent."""
    success = await agent_service.delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return SuccessResponse(
        success=True,
        message=f"Agent {agent_id} deleted"
    )


@router.get("/tools/list")
async def list_tools(
    agent_service: AgentService = Depends(get_agent_service)
):
    """List all available tools."""
    tools = await agent_service.list_tools()
    
    return {
        "tools": [
            ToolSchema(
                name=tool.name,
                description=tool.description,
                category=tool.category,
                parameters=tool.parameters,
                enabled=tool.enabled
            ).dict()
            for tool in tools
        ],
        "total": len(tools)
    }


@router.get("/workflows")
async def list_workflows(
    agent_service: AgentService = Depends(get_agent_service)
):
    """List all available workflows."""
    workflows = await agent_service.list_workflows()
    
    # Group by category
    categories = {}
    for wf in workflows:
        cat = wf.category or "general"
        if cat not in categories:
            categories[cat] = {"id": cat, "name": cat.title(), "icon": "⚡"}
        
    return {
        "workflows": [
            {
                "id": wf.id,
                "name": wf.name,
                "description": wf.description,
                "category": wf.category or "general",
                "icon": "⚡",
                "steps": wf.steps,
                "is_template": wf.is_template
            }
            for wf in workflows
        ],
        "categories": list(categories.values()),
        "total": len(workflows)
    }
