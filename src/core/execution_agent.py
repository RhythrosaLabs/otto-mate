"""
Execution Agent - Tool Execution and Results
============================================

This agent executes the plan created by the Planning Agent.
It runs tools, handles errors, and collects results.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class ExecutionAgent:
    """
    Agent responsible for executing tools and collecting results.
    """
    
    def __init__(self, anthropic_client: Anthropic):
        self.anthropic = anthropic_client
        
    async def execute_plan(
        self,
        plan: Dict[str, Any],
        tool_registry: Any,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a plan created by the Planning Agent.
        
        Args:
            plan: Execution plan with steps
            tool_registry: Registry of available tools
            context: Execution context
            
        Returns:
            Dict with execution results
        """
        steps = plan.get("steps", [])
        if not steps:
            return {"status": "no_steps", "results": []}
        
        results = []
        step_outputs = {}  # Store outputs by step index for dependencies
        
        try:
            for idx, step in enumerate(steps):
                logger.info(f"Executing step {idx + 1}/{len(steps)}: {step.get('description')}")
                
                # Check dependencies
                depends_on = step.get("depends_on", [])
                if depends_on:
                    # Wait for dependencies and gather their outputs
                    dependency_data = {
                        f"step_{dep}": step_outputs.get(dep)
                        for dep in depends_on
                    }
                    step["dependency_data"] = dependency_data
                
                # Execute the tool
                result = await self.execute_tool(
                    tool_name=step["tool"],
                    parameters=step.get("parameters", {}),
                    tool_registry=tool_registry,
                    context=context,
                    step_data=step
                )
                
                # Store result
                step_outputs[idx] = result
                results.append({
                    "step": idx,
                    "tool": step["tool"],
                    "description": step.get("description"),
                    "status": "success" if "error" not in result else "failed",
                    "result": result
                })
                
                # If this step failed and it's required, stop
                if "error" in result and step.get("required", True):
                    logger.error(f"Required step {idx} failed, stopping execution")
                    break
            
            return {
                "status": "completed",
                "results": results,
                "step_outputs": step_outputs
            }
            
        except Exception as e:
            logger.error(f"Execution failed: {e}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e),
                "results": results
            }
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        tool_registry: Any,
        context: Dict[str, Any],
        step_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a single tool.
        
        Args:
            tool_name: Name of tool to execute
            parameters: Tool parameters
            tool_registry: Registry of available tools
            context: Execution context
            step_data: Additional step data including dependencies
            
        Returns:
            Tool execution result
        """
        try:
            # Get tool from registry
            tool_func = tool_registry.get_tool(tool_name)
            if not tool_func:
                raise ValueError(f"Tool '{tool_name}' not found")
            
            # Resolve parameters with dependency data
            if step_data and "dependency_data" in step_data:
                parameters = self._resolve_parameters(
                    parameters,
                    step_data["dependency_data"]
                )
            
            # Execute tool
            logger.info(f"Executing {tool_name} with params: {parameters}")
            result = await tool_func(**parameters)
            
            logger.info(f"Tool {tool_name} completed successfully")
            return {
                "success": True,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _resolve_parameters(
        self,
        parameters: Dict[str, Any],
        dependency_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve parameter values that reference previous step outputs.
        
        Example:
            parameters = {"image": "from_step_0"}
            dependency_data = {"step_0": {"image_url": "https://..."}}
            Result: {"image": "https://..."}
        """
        resolved = {}
        
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith("from_step_"):
                # Extract step index
                step_ref = value.replace("from_step_", "step_")
                if step_ref in dependency_data:
                    # Try to get the most relevant value from that step
                    step_output = dependency_data[step_ref]
                    if isinstance(step_output, dict):
                        # Smart extraction - try common keys
                        for common_key in ["data", "result", "output", "url", "path"]:
                            if common_key in step_output:
                                resolved[key] = step_output[common_key]
                                break
                        else:
                            resolved[key] = step_output
                    else:
                        resolved[key] = step_output
                else:
                    logger.warning(f"Dependency {step_ref} not found")
                    resolved[key] = value
            else:
                resolved[key] = value
        
        return resolved
