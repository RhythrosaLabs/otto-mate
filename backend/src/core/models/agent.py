"""Domain models for agent functionality."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Literal
from uuid import uuid4


@dataclass
class Tool:
    """Domain model for a tool."""
    
    name: str
    description: str
    category: str
    parameters: Dict[str, Any]
    function: Optional[Any] = None
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parameters": self.parameters,
            "enabled": self.enabled,
            "metadata": self.metadata
        }


@dataclass
class Agent:
    """Domain model for an agent."""
    
    id: str
    name: str
    role: str
    description: str
    tools: List[Tool]
    system_prompt: str
    model: str = "claude-sonnet-4"
    temperature: float = 0.7
    max_tokens: int = 4000
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        name: str,
        role: str,
        description: str,
        system_prompt: str,
        tools: Optional[List[Tool]] = None
    ) -> "Agent":
        """Create a new agent."""
        return cls(
            id=str(uuid4()),
            name=name,
            role=role,
            description=description,
            system_prompt=system_prompt,
            tools=tools or [],
            metadata={}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "description": self.description,
            "tools": [tool.to_dict() for tool in self.tools],
            "system_prompt": self.system_prompt,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "metadata": self.metadata
        }


@dataclass
class WorkflowStep:
    """A single step in a workflow."""
    
    id: str
    name: str
    agent_id: str
    input_mapping: Dict[str, str]
    output_mapping: Dict[str, str]
    order: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "agent_id": self.agent_id,
            "input_mapping": self.input_mapping,
            "output_mapping": self.output_mapping,
            "order": self.order
        }


@dataclass
class Workflow:
    """Domain model for a workflow."""
    
    id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    created_at: datetime
    updated_at: datetime
    status: Literal["draft", "active", "archived"] = "draft"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        steps: Optional[List[WorkflowStep]] = None
    ) -> "Workflow":
        """Create a new workflow."""
        now = datetime.now()
        return cls(
            id=str(uuid4()),
            name=name,
            description=description,
            steps=steps or [],
            created_at=now,
            updated_at=now,
            status="draft",
            metadata={}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "steps": [step.to_dict() for step in self.steps],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status,
            "metadata": self.metadata
        }
