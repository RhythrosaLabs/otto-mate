"""
Tool Composer
=============

Enables intelligent tool chaining and composition for complex tasks.

Features:
- Automatic tool chain planning
- Parallel execution where possible
- Data flow between tools
- Error handling with fallbacks
- Progress tracking
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)


class ToolStatus(Enum):
    """Status of a tool in the chain."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ToolNode:
    """A node in the tool execution graph."""
    tool_id: str
    tool_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Dependencies
    depends_on: List[str] = field(default_factory=list)
    
    # Data flow: maps parameter name to (source_tool_id, output_key)
    data_from: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    
    # Execution state
    status: ToolStatus = ToolStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def duration_ms(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return None


@dataclass 
class ToolChain:
    """A chain of tools to execute."""
    chain_id: str
    description: str
    nodes: List[ToolNode] = field(default_factory=list)
    
    # Global state
    status: ToolStatus = ToolStatus.PENDING
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Execution tracking
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def progress(self) -> float:
        """Calculate completion progress 0-1."""
        if not self.nodes:
            return 1.0
        completed = sum(1 for n in self.nodes if n.status == ToolStatus.COMPLETED)
        return completed / len(self.nodes)
    
    @property
    def final_result(self) -> Optional[Any]:
        """Get result from the last completed node."""
        for node in reversed(self.nodes):
            if node.status == ToolStatus.COMPLETED and node.result is not None:
                return node.result
        return None
    
    def get_node(self, tool_id: str) -> Optional[ToolNode]:
        """Get a node by ID."""
        for node in self.nodes:
            if node.tool_id == tool_id:
                return node
        return None


class ToolComposer:
    """
    Composes and executes tool chains.
    """
    
    def __init__(
        self,
        tool_registry: Dict[str, Callable] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        self.tool_registry = tool_registry or {}
        self.client = AsyncAnthropic()
        self.model = model
        self._active_chains: Dict[str, ToolChain] = {}
    
    def register_tool(self, name: str, func: Callable, metadata: Dict[str, Any] = None) -> None:
        """Register a tool for use in chains."""
        self.tool_registry[name] = {
            "func": func,
            "metadata": metadata or {}
        }
    
    async def plan_chain(
        self,
        goal: str,
        available_tools: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ToolChain:
        """
        Plan a tool chain to achieve a goal.
        Uses AI to determine optimal tool sequence.
        """
        tools = available_tools or list(self.tool_registry.keys())
        
        # Get tool descriptions
        tool_descriptions = []
        for name in tools:
            if name in self.tool_registry:
                meta = self.tool_registry[name].get("metadata", {})
                desc = meta.get("description", "No description")
                params = meta.get("parameters", {})
                tool_descriptions.append(f"- {name}: {desc}\n  Parameters: {json.dumps(params)}")
        
        prompt = f"""Plan a sequence of tool calls to accomplish this goal:

Goal: {goal}

Available Tools:
{chr(10).join(tool_descriptions)}

{"Context: " + json.dumps(context) if context else ""}

Respond in JSON format:
{{
  "chain_id": "unique_id",
  "description": "what this chain does",
  "steps": [
    {{
      "tool_id": "step_1",
      "tool_name": "tool_name",
      "parameters": {{"param": "value"}},
      "depends_on": [],
      "reason": "why this step"
    }},
    {{
      "tool_id": "step_2", 
      "tool_name": "tool_name",
      "parameters": {{"param": "{{{{step_1.result}}}}"}},
      "depends_on": ["step_1"],
      "reason": "why this step"
    }}
  ]
}}

Use {{{{step_id.result}}}} or {{{{step_id.result.key}}}} to reference outputs from previous steps."""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        text = response.content[0].text
        
        # Parse JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', text)
        if not json_match:
            raise ValueError("Could not parse chain plan from AI response")
        
        plan = json.loads(json_match.group())
        
        # Convert to ToolChain
        chain = ToolChain(
            chain_id=plan.get("chain_id", f"chain_{datetime.now().timestamp()}"),
            description=plan.get("description", goal),
            context=context or {}
        )
        
        for step in plan.get("steps", []):
            # Parse data flow references
            data_from = {}
            for param, value in step.get("parameters", {}).items():
                if isinstance(value, str) and "{{" in value:
                    # Extract reference like {{step_1.result.key}}
                    match = re.search(r'\{\{(\w+)\.(\w+)(?:\.(\w+))?\}\}', value)
                    if match:
                        source_id = match.group(1)
                        output_key = match.group(2)
                        if match.group(3):
                            output_key += f".{match.group(3)}"
                        data_from[param] = (source_id, output_key)
            
            node = ToolNode(
                tool_id=step["tool_id"],
                tool_name=step["tool_name"],
                parameters=step.get("parameters", {}),
                depends_on=step.get("depends_on", []),
                data_from=data_from
            )
            chain.nodes.append(node)
        
        return chain
    
    async def execute_chain(
        self,
        chain: ToolChain,
        on_progress: Optional[Callable[[ToolChain, ToolNode], None]] = None
    ) -> ToolChain:
        """
        Execute a tool chain, respecting dependencies.
        """
        chain.status = ToolStatus.RUNNING
        chain.started_at = datetime.now()
        self._active_chains[chain.chain_id] = chain
        
        # Build dependency graph
        remaining = set(n.tool_id for n in chain.nodes)
        completed = set()
        results = {}
        
        try:
            while remaining:
                # Find nodes ready to run (all dependencies satisfied)
                ready = []
                for node in chain.nodes:
                    if node.tool_id in remaining:
                        if all(dep in completed for dep in node.depends_on):
                            ready.append(node)
                
                if not ready:
                    # Deadlock or error
                    logger.error("No nodes ready to execute - possible deadlock")
                    break
                
                # Execute ready nodes in parallel
                tasks = [
                    self._execute_node(node, results, chain.context)
                    for node in ready
                ]
                
                node_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Update state
                for node, result in zip(ready, node_results):
                    remaining.discard(node.tool_id)
                    
                    if isinstance(result, Exception):
                        node.status = ToolStatus.FAILED
                        node.error = str(result)
                    else:
                        node.status = ToolStatus.COMPLETED
                        node.result = result
                        results[node.tool_id] = result
                        completed.add(node.tool_id)
                    
                    if on_progress:
                        on_progress(chain, node)
            
            # Check if all completed successfully
            all_success = all(n.status == ToolStatus.COMPLETED for n in chain.nodes)
            chain.status = ToolStatus.COMPLETED if all_success else ToolStatus.FAILED
            
        except Exception as e:
            logger.error(f"Chain execution error: {e}")
            chain.status = ToolStatus.FAILED
        
        chain.completed_at = datetime.now()
        return chain
    
    async def _execute_node(
        self,
        node: ToolNode,
        previous_results: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Any:
        """Execute a single node in the chain."""
        node.status = ToolStatus.RUNNING
        node.started_at = datetime.now()
        
        try:
            # Build parameters, resolving data flow references
            params = {}
            for key, value in node.parameters.items():
                if key in node.data_from:
                    source_id, output_key = node.data_from[key]
                    source_result = previous_results.get(source_id)
                    
                    if source_result is not None:
                        # Navigate to nested key if needed
                        if "." in output_key:
                            parts = output_key.split(".")
                            result_val = source_result
                            for part in parts:
                                if isinstance(result_val, dict):
                                    result_val = result_val.get(part)
                                else:
                                    result_val = getattr(result_val, part, None)
                            params[key] = result_val
                        elif output_key == "result":
                            params[key] = source_result
                        elif isinstance(source_result, dict):
                            params[key] = source_result.get(output_key)
                        else:
                            params[key] = source_result
                    else:
                        params[key] = value
                else:
                    params[key] = value
            
            # Add context if not already in params
            params["_context"] = context
            
            # Get and execute tool
            tool_info = self.tool_registry.get(node.tool_name)
            if not tool_info:
                raise ValueError(f"Tool '{node.tool_name}' not found")
            
            func = tool_info["func"]
            
            # Remove _context if tool doesn't accept it
            import inspect
            sig = inspect.signature(func)
            if "_context" not in sig.parameters:
                params.pop("_context", None)
            
            # Execute
            if asyncio.iscoroutinefunction(func):
                result = await func(**params)
            else:
                result = func(**params)
            
            node.completed_at = datetime.now()
            return result
            
        except Exception as e:
            node.completed_at = datetime.now()
            node.error = str(e)
            raise
    
    async def compose_and_run(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
        on_progress: Optional[Callable] = None
    ) -> ToolChain:
        """
        Convenience method to plan and execute in one call.
        """
        chain = await self.plan_chain(goal, context=context)
        return await self.execute_chain(chain, on_progress)
    
    def get_active_chains(self) -> List[ToolChain]:
        """Get all active chains."""
        return list(self._active_chains.values())
    
    def get_chain(self, chain_id: str) -> Optional[ToolChain]:
        """Get a specific chain by ID."""
        return self._active_chains.get(chain_id)


# Preset chain templates
CHAIN_TEMPLATES = {
    "research_and_summarize": {
        "description": "Research a topic and create a summary",
        "steps": [
            {"tool_name": "web_search", "parameters": {"query": "{{topic}}"}},
            {"tool_name": "summarize", "parameters": {"text": "{{step_1.result}}"}}
        ]
    },
    "generate_and_refine": {
        "description": "Generate content and refine it",
        "steps": [
            {"tool_name": "generate_text", "parameters": {"prompt": "{{prompt}}"}},
            {"tool_name": "refine_text", "parameters": {"text": "{{step_1.result}}"}}
        ]
    },
    "image_pipeline": {
        "description": "Generate and process an image",
        "steps": [
            {"tool_name": "generate_image", "parameters": {"prompt": "{{prompt}}"}},
            {"tool_name": "upscale_image", "parameters": {"image": "{{step_1.result}}"}},
            {"tool_name": "remove_background", "parameters": {"image": "{{step_2.result}}"}}
        ]
    }
}


def create_from_template(
    template_name: str,
    variables: Dict[str, Any]
) -> ToolChain:
    """Create a tool chain from a template."""
    template = CHAIN_TEMPLATES.get(template_name)
    if not template:
        raise ValueError(f"Template '{template_name}' not found")
    
    chain = ToolChain(
        chain_id=f"{template_name}_{datetime.now().timestamp()}",
        description=template["description"],
        context=variables
    )
    
    for i, step in enumerate(template["steps"]):
        params = {}
        for key, value in step.get("parameters", {}).items():
            # Replace variables in templates
            if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
                var_name = value[2:-2]
                if var_name in variables:
                    params[key] = variables[var_name]
                else:
                    params[key] = value
            else:
                params[key] = value
        
        node = ToolNode(
            tool_id=f"step_{i+1}",
            tool_name=step["tool_name"],
            parameters=params,
            depends_on=[f"step_{i}"] if i > 0 else []
        )
        chain.nodes.append(node)
    
    return chain


# Singleton instance
_composer: Optional[ToolComposer] = None

def get_composer() -> ToolComposer:
    """Get the singleton composer instance."""
    global _composer
    if _composer is None:
        _composer = ToolComposer()
    return _composer
