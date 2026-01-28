"""
Execution Agent - Tool Execution and Results
============================================

This agent executes the plan created by the Planning Agent.
It runs tools, handles errors, and collects results.

ENHANCED with:
- Automatic retry with exponential backoff
- Smart fallback strategies
- Artifact collection
- Context propagation between steps
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from anthropic import Anthropic

logger = logging.getLogger(__name__)


# ============================================================================
# ARTIFACT SYSTEM - Collect outputs for display
# ============================================================================

@dataclass
class Artifact:
    """Represents a generated artifact (image, video, text, etc.)."""
    id: str
    type: str  # image, video, audio, text, file, code
    name: str
    url: Optional[str] = None
    content: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'type': self.type,
            'name': self.name,
            'url': self.url,
            'content': self.content[:500] if self.content and len(self.content) > 500 else self.content,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }


# ============================================================================
# FALLBACK STRATEGIES
# ============================================================================

FALLBACK_STRATEGIES = {
    # Printify fallbacks
    "printify_get_print_providers": {
        "default_params": {"blueprint_id": 6},  # T-shirt
        "error_handlers": {
            "invalid blueprint_id": {"blueprint_id": 6}
        }
    },
    "printify_create_product": {
        "default_params": {"blueprint_id": 6, "print_provider_id": 99},
        "error_handlers": {
            "provider": {"print_provider_id": 28}  # Try different provider
        }
    },
    # Image generation fallbacks
    "generate_image": {
        "fallback_tools": ["replicate_run_model"],
        "fallback_params": {"model": "black-forest-labs/flux-schnell"}
    }
}


class ExecutionAgent:
    """
    Agent responsible for executing tools and collecting results.
    
    ENHANCED with:
    - Automatic retry with exponential backoff (3 attempts)
    - Smart fallback strategies for common failures
    - Artifact collection for UI display
    - Better context propagation between steps
    """
    
    def __init__(self, anthropic_client: Anthropic):
        self.anthropic = anthropic_client
        self.artifacts: List[Artifact] = []  # Collected artifacts from execution
        self.max_retries = 3
        self.retry_delay_base = 1  # Base delay in seconds
        
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
            Dict with execution results and collected artifacts
        """
        steps = plan.get("steps", [])
        if not steps:
            return {"status": "no_steps", "results": [], "artifacts": []}
        
        results = []
        step_outputs = {}  # Store outputs by step index for dependencies
        self.artifacts = []  # Reset artifacts for this plan
        
        # Context that gets updated as steps execute
        running_context = dict(context)
        
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
                
                # Execute the tool WITH RETRY
                result = await self._execute_with_retry(
                    tool_name=step["tool"],
                    parameters=step.get("parameters", {}),
                    tool_registry=tool_registry,
                    context=running_context,
                    step_data=step
                )
                
                # Collect artifacts from result
                self._collect_artifacts(result, step)
                
                # Update running context with outputs
                if result.get("success") and result.get("data"):
                    running_context = self._update_context(running_context, result["data"], step["tool"])
                
                # Store result
                step_outputs[idx] = result
                results.append({
                    "step": idx,
                    "tool": step["tool"],
                    "description": step.get("description"),
                    "status": "success" if result.get("success") else "failed",
                    "result": result
                })
                
                # If this step failed and it's critical/required, try fallback or stop
                is_critical = step.get("critical", step.get("required", True))
                if not result.get("success") and is_critical:
                    # Try fallback strategy
                    fallback_result = await self._try_fallback(step, tool_registry, running_context)
                    if fallback_result and fallback_result.get("success"):
                        logger.info(f"Fallback succeeded for step {idx}")
                        results[-1]["result"] = fallback_result
                        results[-1]["status"] = "success"
                        step_outputs[idx] = fallback_result
                        self._collect_artifacts(fallback_result, step)
                    else:
                        logger.error(f"Critical step {idx} failed, stopping execution")
                        break
                elif not result.get("success"):
                    logger.warning(f"Non-critical step {idx} failed, continuing to next steps")
            
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
        Also auto-injects image_url from dependencies if not provided.
        """
        resolved = {}
        
        # First, check if we need to auto-resolve image_url
        # This handles cases where save_generated_image follows generate_* tools
        if "image_url" not in parameters:
            for step_key, step_output in dependency_data.items():
                if isinstance(step_output, dict):
                    # Look for image URLs in the step output
                    data = step_output.get("data", step_output)
                    if isinstance(data, dict):
                        # Check for images array (common in generate_* tools)
                        images = data.get("images", [])
                        if images and len(images) > 0:
                            resolved["image_url"] = images[0]
                            break
                        # Check for direct image_url
                        if "image_url" in data:
                            resolved["image_url"] = data["image_url"]
                            break
                        # Check for output URL
                        if "output" in data:
                            output = data["output"]
                            if isinstance(output, list) and output:
                                resolved["image_url"] = output[0]
                            elif isinstance(output, str) and output.startswith("http"):
                                resolved["image_url"] = output
                            break
        
        for key, value in parameters.items():
            if isinstance(value, str):
                # Handle {{step_X_output}} template syntax
                if "{{" in value and "}}" in value:
                    for step_key, step_output in dependency_data.items():
                        placeholder = f"{{{{{step_key}_output}}}}"
                        if placeholder in value:
                            if isinstance(step_output, dict):
                                data = step_output.get("data", step_output)
                                if isinstance(data, dict) and "images" in data:
                                    value = value.replace(placeholder, data["images"][0])
                                else:
                                    value = value.replace(placeholder, str(data))
                            else:
                                value = value.replace(placeholder, str(step_output))
                    resolved[key] = value
                elif value.startswith("from_step_"):
                    # Extract step index
                    step_ref = value.replace("from_step_", "step_")
                    if step_ref in dependency_data:
                        step_output = dependency_data[step_ref]
                        if isinstance(step_output, dict):
                            data = step_output.get("data", step_output)
                            if isinstance(data, dict):
                                # Smart extraction - try common keys
                                for common_key in ["images", "image_url", "url", "output", "path", "result"]:
                                    if common_key in data:
                                        extracted = data[common_key]
                                        if isinstance(extracted, list) and extracted:
                                            resolved[key] = extracted[0]
                                        else:
                                            resolved[key] = extracted
                                        break
                                else:
                                    resolved[key] = data
                            else:
                                resolved[key] = data
                        else:
                            resolved[key] = step_output
                    else:
                        logger.warning(f"Dependency {step_ref} not found")
                        resolved[key] = value
                else:
                    resolved[key] = value
            else:
                resolved[key] = value
        
        return resolved

    # ========================================================================
    # NEW METHODS: Retry, Fallback, Artifact Collection, Context Update
    # ========================================================================
    
    async def _execute_with_retry(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        tool_registry: Any,
        context: Dict[str, Any],
        step_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool with automatic retry and exponential backoff.
        
        Attempts up to max_retries times with increasing delays:
        - Attempt 1: immediate
        - Attempt 2: 1 second delay
        - Attempt 3: 2 second delay
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                result = await self.execute_tool(
                    tool_name=tool_name,
                    parameters=parameters,
                    tool_registry=tool_registry,
                    context=context,
                    step_data=step_data
                )
                
                if result.get("success"):
                    return result
                
                # If it failed, record the error
                last_error = result.get("error", "Unknown error")
                
                # Check if error is retryable
                if not self._is_retryable_error(last_error):
                    logger.warning(f"Non-retryable error: {last_error}")
                    return result
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
            
            # If not the last attempt, wait before retry
            if attempt < self.max_retries - 1:
                delay = self.retry_delay_base * (2 ** attempt)  # Exponential backoff
                logger.info(f"Retrying {tool_name} in {delay}s (attempt {attempt + 2}/{self.max_retries})")
                await asyncio.sleep(delay)
        
        return {
            "success": False,
            "error": f"Failed after {self.max_retries} attempts: {last_error}"
        }
    
    def _is_retryable_error(self, error: str) -> bool:
        """Determine if an error is retryable."""
        error_lower = error.lower() if error else ""
        
        # Non-retryable errors
        non_retryable = [
            "not found",
            "invalid api key",
            "unauthorized",
            "forbidden",
            "invalid parameter",
            "missing required",
        ]
        
        for term in non_retryable:
            if term in error_lower:
                return False
        
        # Retryable errors (rate limits, timeouts, temporary failures)
        retryable = [
            "timeout",
            "rate limit",
            "too many requests",
            "service unavailable",
            "connection",
            "temporary",
            "try again",
            "502",
            "503",
            "504"
        ]
        
        for term in retryable:
            if term in error_lower:
                return True
        
        # Default: retry on unknown errors
        return True
    
    async def _try_fallback(
        self,
        step: Dict[str, Any],
        tool_registry: Any,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Try fallback strategy for a failed step.
        """
        tool_name = step.get("tool", "")
        
        # Check if we have a fallback strategy
        if tool_name in FALLBACK_STRATEGIES:
            strategy = FALLBACK_STRATEGIES[tool_name]
            
            # Try with default params
            if "default_params" in strategy:
                logger.info(f"Trying fallback with default params for {tool_name}")
                new_params = {**step.get("parameters", {}), **strategy["default_params"]}
                result = await self._execute_with_retry(
                    tool_name=tool_name,
                    parameters=new_params,
                    tool_registry=tool_registry,
                    context=context,
                    step_data=step
                )
                if result.get("success"):
                    return result
            
            # Try fallback tools
            if "fallback_tools" in strategy:
                for fallback_tool in strategy["fallback_tools"]:
                    logger.info(f"Trying fallback tool: {fallback_tool}")
                    fallback_params = strategy.get("fallback_params", step.get("parameters", {}))
                    result = await self._execute_with_retry(
                        tool_name=fallback_tool,
                        parameters=fallback_params,
                        tool_registry=tool_registry,
                        context=context,
                        step_data=step
                    )
                    if result.get("success"):
                        return result
        
        return None
    
    def _collect_artifacts(self, result: Dict[str, Any], step: Dict[str, Any]):
        """
        Collect artifacts from a tool result for display.
        """
        import uuid
        
        if not result.get("success"):
            return
        
        data = result.get("data", {})
        if not isinstance(data, dict):
            return
        
        tool_name = step.get("tool", "unknown")
        step_desc = step.get("description", tool_name)
        
        # Check for images
        images = data.get("images", [])
        if not images and "image_url" in data:
            images = [data["image_url"]]
        if not images and "output" in data:
            output = data["output"]
            if isinstance(output, list):
                images = [u for u in output if isinstance(u, str) and u.startswith("http")]
            elif isinstance(output, str) and output.startswith("http"):
                images = [output]
        
        for i, img_url in enumerate(images):
            self.artifacts.append(Artifact(
                id=str(uuid.uuid4())[:8],
                type="image",
                name=f"{step_desc} - Image {i+1}" if len(images) > 1 else step_desc,
                url=img_url,
                metadata={"tool": tool_name, "step": step.get("step", 0)}
            ))
        
        # Check for videos
        video_url = data.get("video_url") or data.get("video")
        if video_url:
            self.artifacts.append(Artifact(
                id=str(uuid.uuid4())[:8],
                type="video",
                name=step_desc,
                url=video_url,
                metadata={"tool": tool_name}
            ))
        
        # Check for text/content
        content = data.get("content") or data.get("text")
        if content and isinstance(content, str) and len(content) > 50:
            self.artifacts.append(Artifact(
                id=str(uuid.uuid4())[:8],
                type="text",
                name=step_desc,
                content=content,
                metadata={"tool": tool_name}
            ))
        
        # Check for code
        code = data.get("code")
        if code:
            self.artifacts.append(Artifact(
                id=str(uuid.uuid4())[:8],
                type="code",
                name=step_desc,
                content=code,
                metadata={"tool": tool_name, "language": data.get("language", "python")}
            ))
    
    def _update_context(self, context: Dict[str, Any], data: Dict[str, Any], tool_name: str) -> Dict[str, Any]:
        """
        Update the running context with outputs from a tool execution.
        This enables automatic data flow between steps.
        """
        updated = dict(context)
        
        # Extract common output types and store them
        if isinstance(data, dict):
            # Images
            images = data.get("images", [])
            if images:
                updated["last_generated_image"] = images[0]
                updated["generated_images"] = images
            elif "image_url" in data:
                updated["last_generated_image"] = data["image_url"]
            elif "output" in data:
                output = data["output"]
                if isinstance(output, list) and output:
                    if isinstance(output[0], str) and output[0].startswith("http"):
                        updated["last_generated_image"] = output[0]
                elif isinstance(output, str) and output.startswith("http"):
                    updated["last_generated_image"] = output
            
            # Videos
            if "video_url" in data:
                updated["last_generated_video"] = data["video_url"]
            
            # Text content
            if "content" in data:
                updated["last_generated_text"] = data["content"]
            
            # Printify-specific
            if "id" in data and "printify" in tool_name.lower():
                if "upload" in tool_name.lower():
                    updated["printify_image_id"] = data["id"]
                elif "product" in tool_name.lower():
                    updated["printify_product_id"] = data["id"]
            
            # File paths
            if "path" in data:
                updated["last_file_path"] = data["path"]
            if "url" in data:
                updated["last_file_url"] = data["url"]
        
        return updated
    
    def get_artifacts(self) -> List[Dict[str, Any]]:
        """Get all collected artifacts as dicts for JSON serialization."""
        return [a.to_dict() for a in self.artifacts]
