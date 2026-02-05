"""Agent service - Pure business logic for agent operations."""
from typing import List, Optional, Dict, Any

from ..models.agent import Agent, Tool, Workflow


class AgentService:
    """
    Business logic for agent operations.
    
    Manages agents, tools, and workflows without any HTTP dependencies.
    """
    
    def __init__(self, orchestrator):
        """Initialize with orchestrator dependency."""
        self.orchestrator = orchestrator
        self._agents = {}  # In-memory storage (replace with DB)
        self._workflows = {}  # In-memory storage
    
    async def create_agent(
        self,
        name: str,
        role: str,
        description: str,
        system_prompt: str,
        tools: Optional[List[str]] = None
    ) -> Agent:
        """
        Create a new agent.
        
        Args:
            name: Agent name
            role: Agent role
            description: Agent description
            system_prompt: System prompt for the agent
            tools: List of tool names to attach
            
        Returns:
            Agent domain model
        """
        # Get tool objects
        tool_objects = []
        if tools:
            available_tools = await self.list_tools()
            tool_map = {t.name: t for t in available_tools}
            tool_objects = [tool_map[name] for name in tools if name in tool_map]
        
        # Create agent
        agent = Agent.create(
            name=name,
            role=role,
            description=description,
            system_prompt=system_prompt,
            tools=tool_objects
        )
        
        # Register agent
        self._agents[agent.id] = agent
        
        return agent
    
    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID."""
        return self._agents.get(agent_id)
    
    async def list_agents(self) -> List[Agent]:
        """List all agents."""
        return list(self._agents.values())
    
    async def update_agent(
        self,
        agent_id: str,
        **updates: Any
    ) -> Optional[Agent]:
        """Update agent properties."""
        agent = self._agents.get(agent_id)
        if not agent:
            return None
        
        # Update allowed fields
        for key, value in updates.items():
            if hasattr(agent, key):
                setattr(agent, key, value)
        
        return agent
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent."""
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False
    
    async def list_tools(self) -> List[Tool]:
        """List all available tools."""
        # Get tools from orchestrator's tool registry
        try:
            tools = self.orchestrator.tool_registry.list_tools()
        except Exception:
            tools = []
        
        # Convert to Tool domain models
        tool_objects = []
        for tool_data in tools:
            tool = Tool(
                name=tool_data.get("name", "unknown"),
                description=tool_data.get("description", ""),
                category=tool_data.get("category", "general"),
                parameters=tool_data.get("parameters", {}),
                enabled=tool_data.get("enabled", True)
            )
            tool_objects.append(tool)
        
        return tool_objects
    
    async def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Get tool by name."""
        tools = await self.list_tools()
        for tool in tools:
            if tool.name == tool_name:
                return tool
        return None
    
    async def create_workflow(
        self,
        name: str,
        description: str,
        steps: List[Dict[str, Any]]
    ) -> Workflow:
        """Create a new workflow."""
        workflow = Workflow.create(
            name=name,
            description=description,
            steps=[]  # Convert step dicts to WorkflowStep objects
        )
        
        self._workflows[workflow.id] = workflow
        
        return workflow
    
    async def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID."""
        return self._workflows.get(workflow_id)
    
    async def list_workflows(self) -> List[Workflow]:
        """List all workflows."""
        return list(self._workflows.values())
    
    async def execute_workflow(
        self,
        workflow_id: str,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a workflow with given inputs."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Execute through orchestrator
        # This is where workflow execution logic would go
        result = {
            "workflow_id": workflow_id,
            "status": "completed",
            "outputs": {}
        }
        
        return result
