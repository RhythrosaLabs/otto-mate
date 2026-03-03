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
- Background task handling for rate limits
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
# FALLBACK STRATEGIES - Enhanced with comprehensive fallbacks
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
    "printify_get_top_products": {
        # If no top products found, fall back to listing all products
        "fallback_tools": ["printify_list_products"],
        "fallback_params": {"limit": 10}
    },
    
    # Shopify fallbacks
    "shopify_get_top_products": {
        # If no top products found, fall back to listing all products
        "fallback_tools": ["shopify_list_products"],
        "fallback_params": {"limit": 10}
    },
    
    # Image generation fallbacks - multiple models to try
    "generate_image": {
        "fallback_tools": ["replicate_run_model", "replicate_smart_generate"],
        "fallback_params": {"model": "black-forest-labs/flux-schnell"},
        "alternative_models": [
            "black-forest-labs/flux-schnell",
            "stability-ai/sdxl",
            "ideogram-ai/ideogram-v2",
            "stability-ai/stable-diffusion-3",
            "playgroundai/playground-v2.5-1024px-aesthetic"
        ]
    },
    "generate_tshirt_design": {
        "fallback_tools": ["generate_image"],
        "fallback_params": {"style": "vector"}
    },
    
    # Video generation fallbacks
    "generate_video": {
        "fallback_tools": ["replicate_run_model"],
        "fallback_params": {"model": "minimax/video-01"},
        "alternative_models": [
            "minimax/video-01",
            "stability-ai/stable-video-diffusion",
            "anotherjesse/zeroscope-v2-xl"
        ]
    },
    "create_product_promo_video": {
        "fallback_tools": ["generate_video_from_mockup", "replicate_run_model"],
        "fallback_params": {"model": "stability-ai/stable-video-diffusion"}
    },
    
    # Research fallbacks
    "search_web": {
        "fallback_tools": ["browse_url", "research_topic"]
    },
    "research_topic": {
        "fallback_tools": ["search_web"]
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
    - Intelligence System integration for learning from failures
    """
    
    def __init__(self, anthropic_client: Anthropic):
        self.anthropic = anthropic_client
        self.artifacts: List[Artifact] = []  # Collected artifacts from execution
        self.max_retries = 5  # Increased from 3 to 5 for rate limits
        self.retry_delay_base = 2  # Increased base delay to 2 seconds
        self.rate_limit_delay = 60  # Special delay for rate limits (1 minute)
        self.progress_callback = None  # Optional callback for streaming updates
        self.tool_registry = None  # Set during execution for fallback access
        
        # Initialize Intelligence System integration
        try:
            from .intelligence_system import get_intelligence_system
            self.intelligence = get_intelligence_system()
        except Exception as e:
            logger.warning(f"Intelligence system not available: {e}")
            self.intelligence = None
        
    async def execute_plan(
        self,
        plan: Dict[str, Any],
        tool_registry: Any,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a plan created by the Planning Agent.
        Supports parallel execution of independent steps.
        
        Args:
            plan: Execution plan with steps and parallel_groups
            tool_registry: Registry of available tools
            context: Execution context
            
        Returns:
            Dict with execution results and collected artifacts
        """
        self.tool_registry = tool_registry  # Store for fallback access
        steps = plan.get("steps", [])
        if not steps:
            return {"status": "no_steps", "results": [], "artifacts": []}
        
        results = []
        step_outputs = {}  # Store outputs by step index for dependencies
        self.artifacts = []  # Reset artifacts for this plan
        
        # Context that gets updated as steps execute
        running_context = dict(context)
        
        # Get parallel groups if available
        parallel_groups = plan.get("parallel_groups", [])
        
        try:
            if parallel_groups and len(parallel_groups) > 1:
                # Execute with parallel groups
                logger.info(f"🚀 Executing plan with {len(parallel_groups)} parallel groups")
                results = await self._execute_parallel_groups(
                    steps=steps,
                    parallel_groups=parallel_groups,
                    tool_registry=tool_registry,
                    context=running_context,
                    step_outputs=step_outputs
                )
            else:
                # Sequential execution (fallback)
                results = await self._execute_sequential(
                    steps=steps,
                    tool_registry=tool_registry,
                    context=running_context,
                    step_outputs=step_outputs
                )
            
            return {
                "status": "completed",
                "results": results,
                "artifacts": [a.to_dict() for a in self.artifacts],
                "step_outputs": step_outputs
            }
            
        except Exception as e:
            logger.error(f"Plan execution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "results": results,
                "artifacts": [a.to_dict() for a in self.artifacts]
            }
    
    async def _execute_parallel_groups(
        self,
        steps: List[Dict],
        parallel_groups: List[List[int]],
        tool_registry: Any,
        context: Dict[str, Any],
        step_outputs: Dict
    ) -> List[Dict]:
        """Execute steps in parallel groups."""
        results = [None] * len(steps)
        running_context = dict(context)
        
        for group_idx, group in enumerate(parallel_groups):
            logger.info(f"⚡ Executing parallel group {group_idx + 1}/{len(parallel_groups)}: steps {group}")
            
            # Create tasks for all steps in this group
            tasks = []
            for step_idx in group:
                if step_idx >= len(steps):
                    continue
                step = steps[step_idx]
                
                # Prepare dependency data
                depends_on = step.get("depends_on", [])
                if depends_on:
                    dependency_data = {
                        f"step_{dep}": step_outputs.get(dep)
                        for dep in depends_on
                    }
                    step["dependency_data"] = dependency_data
                
                # Create async task
                task = self._execute_step_async(
                    step_idx=step_idx,
                    step=step,
                    tool_registry=tool_registry,
                    context=running_context
                )
                tasks.append((step_idx, task))
            
            # Execute all tasks in parallel
            if tasks:
                task_results = await asyncio.gather(
                    *[t[1] for t in tasks],
                    return_exceptions=True
                )
                
                # Process results
                for (step_idx, _), result in zip(tasks, task_results):
                    step = steps[step_idx]
                    
                    if isinstance(result, Exception):
                        result = {"success": False, "error": str(result)}
                    
                    # Collect artifacts
                    self._collect_artifacts(result, step)
                    
                    # Update context
                    if result.get("success") and result.get("data"):
                        running_context = self._update_context(running_context, result["data"], step["tool"])
                    
                    # Store result
                    step_outputs[step_idx] = result
                    results[step_idx] = {
                        "step": step_idx,
                        "tool": step["tool"],
                        "description": step.get("description"),
                        "status": "success" if result.get("success") else "failed",
                        "result": result
                    }
        
        # Filter out None results
        return [r for r in results if r is not None]
    
    async def _execute_step_async(
        self,
        step_idx: int,
        step: Dict,
        tool_registry: Any,
        context: Dict
    ) -> Dict:
        """Execute a single step asynchronously."""
        logger.info(f"  → Step {step_idx}: {step.get('description', step['tool'])}")
        
        result = await self._execute_with_retry(
            tool_name=step["tool"],
            parameters=step.get("parameters", {}),
            tool_registry=tool_registry,
            context=context,
            step_data=step
        )
        
        return result
    
    async def _execute_sequential(
        self,
        steps: List[Dict],
        tool_registry: Any,
        context: Dict[str, Any],
        step_outputs: Dict
    ) -> List[Dict]:
        """Execute steps sequentially (fallback mode)."""
        results = []
        running_context = dict(context)
        
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
            
            # Handle failures intelligently
            is_critical = step.get("critical", step.get("required", False))  # Default to non-critical
            if not result.get("success"):
                error_msg = result.get("error", "")
                
                # Check if it's a rate limit (should auto-retry in background)
                if self._is_rate_limit_error(str(error_msg)):
                    logger.info(f"⏳ Step {idx} hit rate limit, scheduling background retry...")
                    results[-1]["status"] = "background_processing"
                    results[-1]["message"] = "Working on it in the background - will complete automatically"
                    
                    # Create background task to retry this step
                    from .background_tasks import get_task_manager
                    task_manager = get_task_manager()
                    task_id = task_manager.create_task(
                        step=step,
                        tool_registry=tool_registry,
                        execution_agent=self,
                        retry_delay=60
                    )
                    results[-1]["background_task_id"] = task_id
                    results[-1]["task_name"] = step.get("description", step["tool"])
                    logger.info(f"📋 Created background task {task_id} for step {idx}")
                    # Continue with other steps
                    
                elif is_critical:
                    # Only stop for critical non-rate-limit failures
                    fallback_result = await self._try_fallback(step, tool_registry, running_context)
                    if fallback_result and fallback_result.get("success"):
                        logger.info(f"Fallback succeeded for step {idx}")
                        results[-1]["result"] = fallback_result
                        results[-1]["status"] = "success"
                        step_outputs[idx] = fallback_result
                        self._collect_artifacts(fallback_result, step)
                    else:
                        logger.warning(f"Critical step {idx} failed, but continuing with remaining work")
                else:
                    logger.info(f"Non-critical step {idx} failed, continuing to next steps")
        
        return results
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        tool_registry: Any,
        context: Dict[str, Any],
        step_data: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Execute a single tool with smart retry logic and auto-healing.
        
        Smart Features:
        - Automatically fixes parameter mismatches by inspecting function signatures
        - Adds missing parameters with intelligent defaults
        - Detects and handles known API errors (Printify 10300, rate limits, etc.)
        - Applies exponential backoff for temporary failures
        - Converts image formats when needed (WebP → PNG for Printify)
        
        Args:
            tool_name: Name of tool to execute
            parameters: Tool parameters
            tool_registry: Registry of available tools
            context: Execution context
            step_data: Additional step data including dependencies
            max_retries: Maximum number of retry attempts
            
        Returns:
            Tool execution result
        """
        last_error = None
        
        # Pre-filter known meta-parameters that should never be passed to tools
        meta_params_to_remove = {'task_description', 'task_type', 'task_id', 'step_id', 'execution_context'}
        for meta_param in meta_params_to_remove:
            if meta_param in parameters:
                logger.debug(f"Pre-filtering meta parameter '{meta_param}' from tool call")
                parameters = {k: v for k, v in parameters.items() if k != meta_param}
        
        for attempt in range(max_retries):
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
                logger.info(f"Executing {tool_name} (attempt {attempt + 1}/{max_retries}) with params: {parameters}")
                result = await tool_func(**parameters)
                
                # UNIVERSAL FILE CAPTURE: Auto-save ALL generated files
                # This captures images, videos, audio, documents, 3D models, etc.
                try:
                    from ..storage.universal_capture import auto_capture_result
                    prompt = parameters.get("prompt") or parameters.get("description") or parameters.get("text")
                    session_id = context.get("session_id") or context.get("user_id")
                    result = await auto_capture_result(
                        result=result if isinstance(result, dict) else {"output": result},
                        tool_name=tool_name,
                        session_id=session_id,
                        prompt=prompt
                    )
                    if result.get("_captured"):
                        logger.info(f"✓ File auto-captured: {result['_captured'].get('local_path')}")
                except Exception as e:
                    logger.debug(f"Universal capture skipped: {e}")
                
                # LEGACY: Also save Replicate images via old method (backup)
                if "replicate" in tool_name.lower() and isinstance(result, dict):
                    image_url = result.get("image_url") or result.get("url")
                    if image_url and image_url.startswith("http"):
                        logger.info(f"Auto-saving Replicate image to permanent storage: {image_url}")
                        try:
                            save_tool = self.tool_registry.get_tool("save_image_from_url")
                            if save_tool:
                                save_result = await save_tool(
                                    url=image_url,
                                    filename=f"replicate_{tool_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                                    tags=["replicate", "auto-saved"]
                                )
                                if save_result.get("success"):
                                    # Replace the temporary Replicate URL with the permanent file URL
                                    result["saved_image_url"] = save_result["url"]
                                    result["file_id"] = save_result["file_id"]
                                    logger.info(f"✓ Image saved to permanent storage: {save_result['url']}")
                        except Exception as e:
                            logger.warning(f"Could not auto-save image (continuing anyway): {e}")
                
                logger.info(f"Tool {tool_name} completed successfully")
                return {
                    "success": True,
                    "data": result
                }
                
            except TypeError as e:
                # Parameter mismatch - try to fix it
                error_msg = str(e)
                logger.warning(f"Parameter error on attempt {attempt + 1}: {error_msg}")
                
                if attempt < max_retries - 1:
                    fixed_params = await self._fix_parameter_error(
                        tool_name, parameters, error_msg, tool_func
                    )
                    if fixed_params:
                        logger.info(f"Auto-fixed parameters, retrying...")
                        parameters = fixed_params
                        continue
                
                last_error = e
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Tool execution failed (attempt {attempt + 1}): {error_msg}", exc_info=True)
                
                # INTELLIGENCE: Record failure for learning
                if self.intelligence:
                    try:
                        self.intelligence.record_failure(tool_name, error_msg, parameters)
                        
                        # Check if we have a known fix from past learnings
                        known_fix = self.intelligence.get_known_fix(tool_name, error_msg)
                        if known_fix and attempt < max_retries - 1:
                            logger.info(f"Applying learned fix: {known_fix}")
                            parameters.update(known_fix)
                            await asyncio.sleep(1)
                            continue
                        
                        # Try intelligent parameter fix
                        param_fix = self.intelligence.get_parameter_fix(tool_name, error_msg, parameters)
                        if param_fix and attempt < max_retries - 1:
                            logger.info(f"Applying intelligent parameter fix")
                            parameters = param_fix
                            await asyncio.sleep(1)
                            continue
                    except Exception as intel_e:
                        logger.debug(f"Intelligence fix attempt failed: {intel_e}")
                
                # Check if it's a known API error we can fix
                if attempt < max_retries - 1:
                    should_retry, fixed_params = await self._analyze_and_fix_error(
                        tool_name, parameters, error_msg, e
                    )
                    if should_retry:
                        if fixed_params:
                            parameters = fixed_params
                        logger.info(f"Error analyzed, retrying with adjusted approach...")
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                
                last_error = e
        
        # All retries failed - try intelligent fallback
        if self.intelligence and self.tool_registry:
            try:
                fallback_options = self.intelligence.get_fallback_options(tool_name)
                for fallback in fallback_options[:2]:  # Try up to 2 fallbacks
                    fallback_tool = fallback.get("tool")
                    param_map = fallback.get("param_map", {})
                    
                    logger.info(f"Trying fallback tool: {fallback_tool}")
                    fallback_func = self.tool_registry.get_tool(fallback_tool)
                    if fallback_func:
                        # Transform parameters
                        fallback_params = {}
                        for k, v in parameters.items():
                            new_key = param_map.get(k, k)
                            fallback_params[new_key] = v
                        
                        try:
                            result = await fallback_func(**fallback_params)
                            self.intelligence.record_fallback_result(tool_name, fallback_tool, True)
                            logger.info(f"Fallback {fallback_tool} succeeded!")
                            return {"success": True, "data": result, "fallback_used": fallback_tool}
                        except Exception as fb_e:
                            self.intelligence.record_fallback_result(tool_name, fallback_tool, False)
                            logger.warning(f"Fallback {fallback_tool} failed: {fb_e}")
            except Exception as fallback_e:
                logger.debug(f"Fallback system error: {fallback_e}")
        
        # All retries and fallbacks failed
        logger.error(f"Tool {tool_name} failed after {max_retries} attempts")
        return {
            "success": False,
            "error": str(last_error),
            "retries": max_retries
        }
    
    def _resolve_parameters(
        self,
        parameters: Dict[str, Any],
        dependency_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve parameter values that reference previous step outputs.
        Only auto-injects image_url if explicitly referenced in parameters.
        Detects failed dependency steps and raises appropriate errors.
        """
        logger.info(f"Resolving parameters: {parameters}")
        logger.info(f"Available dependency data keys: {list(dependency_data.keys())}")
        resolved = {}
        
        # Don't auto-inject image_url anymore - only resolve if explicitly referenced
        # This prevents injecting parameters into tools that don't need them
        
        for key, value in parameters.items():
            # Handle list of templates (e.g., reference_images: ["{{step_0_output}}", ...])
            if isinstance(value, list):
                resolved_list = []
                for item in value:
                    if isinstance(item, str) and "{{" in item and "}}" in item:
                        resolved_item = self._resolve_single_template(item, dependency_data)
                        if resolved_item:
                            resolved_list.append(resolved_item)
                    else:
                        resolved_list.append(item)
                resolved[key] = resolved_list
                logger.info(f"Resolved list parameter {key}: {resolved_list[:2]}...")  # Log first 2
                continue
                
            if isinstance(value, str):
                # Handle {{step_X_output}} template syntax
                if "{{" in value and "}}" in value:
                    logger.info(f"Found template in parameter {key}: {value}")
                    
                    # Extract all template patterns
                    import re
                    templates = re.findall(r'\{\{([^}]+)\}\}', value)
                    
                    for template in templates:
                        # Parse template: step_X_property or step_X_output
                        parts = template.split('_')
                        if len(parts) >= 2 and parts[0] == 'step':
                            step_key = f"{parts[0]}_{parts[1]}"  # e.g., "step_0"
                            property_name = '_'.join(parts[2:]) if len(parts) > 2 else 'output'  # e.g., "title" or "output"
                            
                            if step_key in dependency_data:
                                step_output = dependency_data[step_key]
                                placeholder = f"{{{{{template}}}}}"
                                
                                # CHECK FOR FAILED STEP - Don't proceed if dependency failed
                                if isinstance(step_output, dict):
                                    # Check if the step itself failed
                                    if step_output.get("success") == False or step_output.get("status") == "error":
                                        error_msg = step_output.get("error", "Unknown error")
                                        logger.error(f"Dependency {step_key} failed: {error_msg}")
                                        raise ValueError(f"Cannot proceed - dependency step {step_key} failed: {error_msg}")
                                    
                                    # Check nested data for failure
                                    data = step_output.get("data", step_output)
                                    if isinstance(data, dict) and data.get("success") == False:
                                        error_msg = data.get("error", "Unknown error")
                                        logger.error(f"Dependency {step_key} returned failure in data: {error_msg}")
                                        raise ValueError(f"Cannot proceed - dependency step {step_key} failed: {error_msg}")
                                
                                # Extract the requested property
                                if isinstance(step_output, dict):
                                    data = step_output.get("data", step_output)
                                    
                                    # Try to get the specific property
                                    if property_name == 'output':
                                        # Handle output specially
                                        if isinstance(data, dict):
                                            # PRIORITY: Use saved_image_url if available (permanent storage)
                                            if "saved_image_url" in data:
                                                replacement = data["saved_image_url"]
                                            elif "images" in data:
                                                replacement = data["images"][0]
                                            elif "image_url" in data:
                                                replacement = data["image_url"]
                                            elif "output" in data:
                                                output = data["output"]
                                                replacement = output[0] if isinstance(output, list) and output else str(output)
                                            else:
                                                replacement = str(data)
                                        else:
                                            replacement = str(data)
                                    elif property_name == 'image_url':
                                        # PRIORITY: Use saved_image_url if available (permanent storage)
                                        if isinstance(data, dict):
                                            replacement = data.get("saved_image_url") or data.get("image_url") or str(data)
                                        else:
                                            replacement = str(data)
                                    elif isinstance(data, dict) and property_name in data:
                                        # Direct property access
                                        replacement = str(data[property_name])
                                    else:
                                        # Fallback to string representation
                                        replacement = str(data)
                                    
                                    value = value.replace(placeholder, replacement)
                                    logger.info(f"Replaced {placeholder} with: {replacement}")
                                else:
                                    replacement = str(step_output)
                                    value = value.replace(placeholder, replacement)
                                    logger.info(f"Replaced {placeholder} with output: {replacement}")
                    
                    resolved[key] = value
                    logger.info(f"Final resolved value for {key}: {resolved[key]}")
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
        
        # Type conversion for numeric parameters
        # Convert string numbers to proper types (e.g., "15" -> 15 for duration)
        for key in ['duration', 'width', 'height', 'price', 'price_cents', 'blueprint_id', 'print_provider_id']:
            if key in resolved and isinstance(resolved[key], str):
                try:
                    resolved[key] = int(resolved[key])
                    logger.info(f"Converted {key} to int: {resolved[key]}")
                except (ValueError, TypeError):
                    pass  # Keep as string if conversion fails
        
        logger.info(f"Final resolved parameters: {resolved}")
        return resolved
    
    def _resolve_single_template(self, value: str, dependency_data: Dict[str, Any]) -> Optional[str]:
        """
        Resolve a single template string like {{step_0_output}} to its actual value.
        """
        import re
        templates = re.findall(r'\{\{([^}]+)\}\}', value)
        
        for template in templates:
            parts = template.split('_')
            if len(parts) >= 2 and parts[0] == 'step':
                step_key = f"{parts[0]}_{parts[1]}"
                property_name = '_'.join(parts[2:]) if len(parts) > 2 else 'output'
                
                if step_key in dependency_data:
                    step_output = dependency_data[step_key]
                    
                    if isinstance(step_output, dict):
                        data = step_output.get("data", step_output)
                        
                        if property_name == 'output':
                            if isinstance(data, dict):
                                if "saved_image_url" in data:
                                    return data["saved_image_url"]
                                elif "images" in data:
                                    return data["images"][0]
                                elif "image_url" in data:
                                    return data["image_url"]
                                elif "output" in data:
                                    output = data["output"]
                                    return output[0] if isinstance(output, list) and output else str(output)
                        elif property_name == 'image_url':
                            if isinstance(data, dict):
                                return data.get("saved_image_url") or data.get("image_url")
                        elif isinstance(data, dict) and property_name in data:
                            return str(data[property_name])
                    else:
                        return str(step_output)
        
        return None

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
                    step_data=step_data,
                    max_retries=1  # Don't nest retries - _execute_with_retry handles retry logic
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
                # Use longer delay for rate limits
                if self._is_rate_limit_error(str(last_error)):
                    # Rate limit: Use much longer delay (starts at 60s)
                    delay = self.rate_limit_delay * (attempt + 1)  # 60s, 120s, 180s, etc.
                    logger.warning(f"🚦 Rate limit detected. Waiting {delay}s before retry...")
                    logger.info(f"💡 This is normal for free/limited API tiers. Otto will automatically retry.")
                else:
                    # Regular exponential backoff for other errors
                    delay = self.retry_delay_base * (2 ** attempt)  # 2s, 4s, 8s, etc.
                    logger.info(f"Retrying {tool_name} in {delay}s (attempt {attempt + 2}/{self.max_retries})")
                
                # Stream progress update if callback available
                if self.progress_callback:
                    await self.progress_callback({
                        "type": "retry",
                        "tool": tool_name,
                        "attempt": attempt + 2,
                        "max_attempts": self.max_retries,
                        "delay": delay,
                        "reason": "rate_limit" if self._is_rate_limit_error(str(last_error)) else "error"
                    })
                
                await asyncio.sleep(delay)
        
        return {
            "success": False,
            "error": f"Failed after {self.max_retries} attempts: {last_error}"
        }
    
    def _is_retryable_error(self, error: str) -> bool:
        """Determine if an error is retryable."""
        error_lower = error.lower() if error else ""
        
        # Non-retryable errors (fundamental issues)
        non_retryable = [
            "not found",
            "invalid api key",
            "unauthorized",
            "forbidden",
            "invalid parameter",
            "missing required parameter",
            "authentication failed",
            "does not exist",
        ]
        
        for term in non_retryable:
            if term in error_lower:
                return False
        
        # Retryable errors (rate limits, timeouts, temporary failures)
        retryable = [
            "timeout",
            "rate limit",
            "rate_limit",
            "ratelimit",
            "too many requests",
            "429",
            "quota",
            "throttle",
            "service unavailable",
            "connection",
            "temporary",
            "try again",
            "502",
            "503",
            "504",
            "insufficient credits",
            "credit",
        ]
        
        for term in retryable:
            if term in error_lower:
                return True
        
        # Default: retry on unknown errors
        return True
    
    def _is_rate_limit_error(self, error: str) -> bool:
        """Check if error is specifically a rate limit (needs longer delay)."""
        error_lower = error.lower() if error else ""
        rate_limit_indicators = [
            "rate limit",
            "rate_limit",
            "ratelimit",
            "too many requests",
            "429",
            "quota exceeded",
            "throttle",
            "insufficient credits",
            "per minute",
            "requests per",
        ]
        return any(indicator in error_lower for indicator in rate_limit_indicators)
    
    async def _try_simplified_prompt(
        self,
        original_params: Dict[str, Any],
        tool_name: str,
        tool_registry: Any,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Recovery strategy: Simplify the prompt and retry.
        Based on printify_clean/ultra_smart_executor.py pattern.
        """
        prompt = original_params.get("prompt", "")
        if not prompt:
            return None
        
        import re
        
        # Simplify: remove special characters, shorten to 20 words max
        simplified_prompt = re.sub(r"[^\w\s,]", "", prompt)
        simplified_prompt = " ".join(simplified_prompt.split()[:20])
        
        # Add quality boosters back
        simplified_prompt = f"{simplified_prompt}, high quality, detailed"
        
        simplified_params = {**original_params, "prompt": simplified_prompt}
        
        logger.info(f"🔄 Trying simplified prompt: {simplified_prompt[:50]}...")
        
        result = await self._execute_with_retry(
            tool_name=tool_name,
            parameters=simplified_params,
            tool_registry=tool_registry,
            context=context
        )
        
        if result.get("success"):
            result["recovery_used"] = "simplified_prompt"
            return result
        
        return None
    
    async def _try_with_different_size(
        self,
        original_params: Dict[str, Any],
        tool_name: str,
        tool_registry: Any,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Recovery strategy: Try with different image size (1:1 square is safest).
        Based on printify_clean/ultra_smart_executor.py pattern.
        """
        # Try with square aspect ratio as it's the most universally supported
        size_variants = [
            {"aspect_ratio": "1:1", "width": 1024, "height": 1024},
            {"aspect_ratio": "1:1", "width": 512, "height": 512},
            {"width": 768, "height": 768},
        ]
        
        for size_params in size_variants:
            try_params = {**original_params, **size_params}
            
            logger.info(f"🔄 Trying with size: {size_params}")
            
            result = await self._execute_with_retry(
                tool_name=tool_name,
                parameters=try_params,
                tool_registry=tool_registry,
                context=context
            )
            
            if result.get("success"):
                result["recovery_used"] = "different_size"
                return result
        
        return None
    
    def _auto_fill_missing_params(
        self,
        params: Dict[str, Any],
        step: Dict[str, Any],
        running_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Auto-fill missing parameters from context.
        Based on printify_clean/ultra_smart_executor.py _enrich_config pattern.
        """
        filled_params = dict(params)
        tool_name = step.get("tool", "").lower()
        
        # Auto-fill image inputs for editing/upscaling tools
        if any(kw in tool_name for kw in ["edit", "upscale", "enhance", "background", "inpaint"]):
            if not filled_params.get("image") and not filled_params.get("input_image"):
                # Try to get from context
                context_image = (
                    running_context.get("last_generated_image") or
                    running_context.get("current_image") or
                    running_context.get("image_url")
                )
                if context_image:
                    filled_params["image"] = context_image
                    logger.info(f"Auto-filled image parameter from context")
        
        # Auto-fill prompt if missing
        if "image" in tool_name or "generate" in tool_name:
            if not filled_params.get("prompt"):
                # Try to construct from step description
                description = step.get("description", "")
                if description:
                    filled_params["prompt"] = f"{description}, high quality, detailed, professional"
                    logger.info(f"Auto-filled prompt from step description")
        
        # Auto-fill video image inputs
        if "video" in tool_name:
            if not filled_params.get("image_url") and not filled_params.get("first_frame_image"):
                context_image = running_context.get("last_generated_image")
                if context_image:
                    filled_params["image_url"] = context_image
                    filled_params["first_frame_image"] = context_image
                    logger.info(f"Auto-filled video image from context")
        
        # Add quality boosters to prompts if short
        if filled_params.get("prompt"):
            prompt = filled_params["prompt"]
            if len(prompt) < 100 and "quality" not in prompt.lower():
                filled_params["prompt"] = f"{prompt}, high quality, detailed"
        
        return filled_params
    
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
            
            # Try alternative models if available (for AI model tools)
            if "alternative_models" in strategy:
                original_params = step.get("parameters", {})
                for alt_model in strategy["alternative_models"]:
                    logger.info(f"Trying alternative model: {alt_model}")
                    # Try with replicate_run_model using the alternative model
                    alt_params = {
                        **original_params,
                        "model": alt_model,
                        "model_name": alt_model,
                        "inputs": {"prompt": original_params.get("prompt", "")}
                    }
                    result = await self._execute_with_retry(
                        tool_name="replicate_run_model",
                        parameters=alt_params,
                        tool_registry=tool_registry,
                        context=context,
                        step_data=step
                    )
                    if result.get("success"):
                        logger.info(f"✓ Alternative model {alt_model} succeeded!")
                        return result
        
        # NEW: Try recovery strategies for image generation (simplified prompt, different size)
        original_params = step.get("parameters", {})
        if any(kw in tool_name.lower() for kw in ["image", "generate", "design"]):
            # Try simplified prompt
            result = await self._try_simplified_prompt(original_params, tool_name, tool_registry, context)
            if result and result.get("success"):
                logger.info("✓ Simplified prompt strategy succeeded!")
                return result
            
            # Try with different size
            result = await self._try_with_different_size(original_params, tool_name, tool_registry, context)
            if result and result.get("success"):
                logger.info("✓ Different size strategy succeeded!")
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
        
        # CRITICAL FIX: Check for saved file IDs (from save_generated_image tool)
        # Convert file IDs to proper URLs
        if "id" in data and ("file" in tool_name.lower() or "save" in tool_name.lower()):
            file_id = data["id"]
            file_type = data.get("type", "unknown")
            if file_type.startswith("image/"):
                # Add as /files/{id} URL which the frontend will handle
                images.append(f"/files/{file_id}")
        
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
    
    async def _fix_parameter_error(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        error_msg: str,
        tool_func: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Automatically fix parameter errors by analyzing function signature.
        """
        import inspect
        
        try:
            # Get function signature
            sig = inspect.signature(tool_func)
            expected_params = set(sig.parameters.keys()) - {'self', 'cls'}
            provided_params = set(parameters.keys())
            
            # Find missing required parameters
            missing = []
            for param_name, param in sig.parameters.items():
                if param_name in {'self', 'cls'}:
                    continue
                if param.default == inspect.Parameter.empty and param_name not in provided_params:
                    missing.append(param_name)
            
            # Find unexpected parameters
            unexpected = provided_params - expected_params
            
            if missing or unexpected:
                logger.info(f"Parameter mismatch detected:")
                logger.info(f"  Missing: {missing}")
                logger.info(f"  Unexpected: {unexpected}")
                
                # Create fixed parameters
                fixed = parameters.copy()
                
                # Try to map common parameter synonyms before removing
                param_mappings = {
                    'prompt': 'description',
                    'text': 'description',
                    'query': 'description',
                    'task': 'content_type',
                    'description': 'body_html',  # For Shopify products
                    'content': 'body_html',  # For Shopify blog posts
                    'design': 'design_description',  # For mockup generation
                    'product': 'product_type',  # For mockup generation
                    'include_audio': None,  # Remove this, not supported
                    'weight': None,  # Remove, not supported in create_product
                    'inventory_quantity': None,  # Remove, not supported in create_product
                    'requires_shipping': None,  # Remove, not supported in create_product
                    # Video tool mappings
                    'reference_images': 'image_url',  # For video from images
                    'input_image': 'image_url',  # For video from images
                    'style': None,  # Remove unsupported video style param
                    # Task parameters that don't belong in tool calls
                    'task_description': None,  # Remove, this is task metadata not tool param
                    'task_type': None,  # Remove, this is task metadata not tool param
                    'task_id': None,  # Remove, this is task metadata not tool param
                }
                
                # Map unexpected parameters to expected ones
                for unexpected_param in list(unexpected):
                    if unexpected_param in param_mappings:
                        mapped_to = param_mappings[unexpected_param]
                        if mapped_to and mapped_to in missing:
                            # Get the value
                            value = fixed.pop(unexpected_param)
                            
                            # If it's a list (like reference_images), extract first element
                            if isinstance(value, list) and len(value) > 0:
                                value = value[0]
                                logger.info(f"  Extracted first element from list for {unexpected_param}")
                            
                            # Move the value from unexpected to expected
                            logger.info(f"  Mapping parameter: {unexpected_param} -> {mapped_to}")
                            fixed[mapped_to] = value
                            missing.remove(mapped_to)
                            unexpected.remove(unexpected_param)
                        elif mapped_to is None:
                            # Remove it
                            logger.info(f"  Removing unsupported parameter: {unexpected_param}")
                            fixed.pop(unexpected_param, None)
                            unexpected.remove(unexpected_param)
                
                # Remove remaining unexpected parameters
                for param in unexpected:
                    logger.info(f"  Removing unexpected parameter: {param}")
                    fixed.pop(param, None)
                
                # Add missing parameters with smart defaults
                for param in missing:
                    default_value = self._get_smart_default(param, tool_name, parameters)
                    if default_value is not None:
                        logger.info(f"  Adding missing parameter {param} = {default_value}")
                        fixed[param] = default_value
                
                return fixed
        
        except Exception as e:
            logger.error(f"Failed to auto-fix parameters: {e}")
        
        return None
    
    def _get_smart_default(self, param_name: str, tool_name: str, existing_params: Dict) -> Any:
        """
        Generate smart default values for common parameters.
        """
        # Title parameter - common for products and content
        if param_name == 'title':
            return (existing_params.get('title') or
                    existing_params.get('product_title') or
                    existing_params.get('name') or
                    existing_params.get('product_type', '').replace('_', ' ').title() + ' Product' or
                    'Generated Product')
        
        # Common parameter patterns
        if param_name in ['prompt', 'text', 'content', 'description', 'body_html']:
            # Try to find description-like values from existing params
            return (existing_params.get('body_html') or
                    existing_params.get('description') or 
                    existing_params.get('prompt') or 
                    existing_params.get('text') or
                    existing_params.get('query') or
                    existing_params.get('title', 'Generated content'))
        
        if param_name in ['width', 'height']:
            return 1024
        
        if param_name == 'duration':
            # Check if duration was provided in existing params
            if 'duration' in existing_params:
                return existing_params['duration']
            return 15 if 'video' in tool_name.lower() else 30
        
        if param_name in ['style', 'art_style']:
            return existing_params.get('style', 'professional')
        
        if param_name == 'content_type':
            # Try to infer from task or existing params
            if 'task' in existing_params:
                task = str(existing_params['task']).lower()
                if 'video' in task:
                    return 'video'
                elif 'audio' in task or 'music' in task:
                    return 'audio'
                elif 'image' in task:
                    return 'image'
            return 'auto'
        
        if param_name == 'format':
            if 'image' in tool_name.lower():
                return 'png'
            elif 'video' in tool_name.lower():
                return 'mp4'
        
        if param_name == 'quality':
            return existing_params.get('quality', 'high')
        
        if param_name in ['model', 'model_name']:
            if 'image' in tool_name.lower():
                return 'flux-schnell'
            elif 'video' in tool_name.lower():
                return 'stable-video'
        
        # Browser tool specific defaults
        if param_name == 'data_description':
            # For browser_extract_data - infer from URL or task
            url = existing_params.get('url', '')
            if 'reddit' in url.lower():
                return 'subreddits, posts, and community information'
            elif 'linkedin' in url.lower():
                return 'profiles, companies, and job listings'
            elif 'twitter' in url.lower() or 'x.com' in url.lower():
                return 'tweets, profiles, and trending topics'
            return 'structured data, text content, links, and relevant information'
        
        if param_name == 'niche':
            # For browser_find_influencers - infer from context
            task = existing_params.get('task', '') or existing_params.get('description', '')
            if task:
                # Try to extract niche keywords from task
                task_lower = task.lower()
                for niche_keyword in ['fitness', 'beauty', 'tech', 'fashion', 'food', 'travel', 
                                      'gaming', 'music', 'art', 'lifestyle', 'business', 'health']:
                    if niche_keyword in task_lower:
                        return niche_keyword
            return 'lifestyle'  # Default fallback niche
        
        if param_name == 'platform':
            # For social media/influencer tools
            task = existing_params.get('task', '') or existing_params.get('description', '')
            if task:
                task_lower = task.lower()
                if 'tiktok' in task_lower:
                    return 'tiktok'
                elif 'instagram' in task_lower:
                    return 'instagram'
                elif 'youtube' in task_lower:
                    return 'youtube'
                elif 'twitter' in task_lower or 'x.com' in task_lower:
                    return 'twitter'
            return 'instagram'  # Default platform
        
        if param_name == 'url' and 'browser' in tool_name.lower():
            # Try to infer URL from task description
            task = existing_params.get('task', '') or existing_params.get('description', '')
            if task:
                task_lower = task.lower()
                if 'reddit' in task_lower:
                    return 'https://www.reddit.com'
                elif 'tiktok' in task_lower:
                    return 'https://www.tiktok.com'
                elif 'instagram' in task_lower:
                    return 'https://www.instagram.com'
                elif 'twitter' in task_lower:
                    return 'https://twitter.com'
        
        return None
    
    async def _analyze_and_fix_error(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        error_msg: str,
        exception: Exception
    ) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Analyze errors and determine if retry is worthwhile with fixes.
        
        Returns:
            (should_retry, fixed_parameters)
        """
        error_lower = error_msg.lower()
        
        # Printify API errors
        if 'printify' in tool_name.lower():
            # Error 10300: Image upload failed
            if '10300' in error_msg or 'image upload failed' in error_lower:
                logger.info("Detected Printify image upload error - checking image format...")
                
                # Check if we have an image URL parameter
                image_param = parameters.get('image_url') or parameters.get('design_url') or parameters.get('url')
                if image_param and isinstance(image_param, str):
                    # If it's a WebP, suggest conversion
                    if image_param.endswith('.webp'):
                        logger.info("Image is WebP format - Printify may prefer PNG")
                        # We can't convert here, but can suggest adding conversion step
                        return (False, None)  # Need external conversion
                
                return (True, None)  # Retry as-is (might be temporary API issue)
            
            # Missing API credentials
            if 'api key' in error_lower or 'unauthorized' in error_lower:
                logger.error("Printify API credentials missing or invalid")
                return (False, None)
        
        # Replicate API errors
        if 'replicate' in tool_name.lower():
            # Rate limiting or insufficient credits
            if any(x in error_lower for x in ['rate limit', '429', 'quota', 'credit', 'throttle']):
                logger.warning("🚦 Replicate API rate limit/quota detected")
                logger.info("💡 Will automatically retry with extended delay (60s intervals)")
                logger.info("💡 Consider adding credits to your Replicate account for faster processing")
                return (True, None)  # Will use extended rate_limit_delay
            
            # Model not found
            if 'model not found' in error_lower or '404' in error_msg:
                logger.error("Model not found - cannot retry")
                return (False, None)
        
        # Video generation errors
        if 'video' in tool_name.lower():
            # Missing prompt
            if 'prompt' in error_lower and ('required' in error_lower or 'missing' in error_lower):
                fixed = parameters.copy()
                if 'prompt' not in fixed:
                    # Use description or title as prompt
                    fixed['prompt'] = parameters.get('description', parameters.get('title', 'Product video'))
                    logger.info(f"Added missing video prompt: {fixed['prompt']}")
                    return (True, fixed)
            
            # Invalid duration
            if 'duration' in error_lower:
                fixed = parameters.copy()
                fixed['duration'] = 15  # Default to 15 seconds
                logger.info("Fixed video duration to 15 seconds")
                return (True, fixed)
        
        # Network/timeout errors - always retry
        if any(x in error_lower for x in ['timeout', 'connection', 'network', 'temporary']):
            logger.info("Network/timeout error - will retry")
            return (True, None)
        
        # Generic API errors that might be temporary
        if any(x in error_lower for x in ['500', '502', '503', '504', 'internal server', 'service unavailable']):
            logger.info("Server error - will retry")
            return (True, None)
        
        # Unknown error - don't retry by default
        logger.info("Unknown error type - not retrying automatically")
        return (False, None)
    
    def get_artifacts(self) -> List[Dict[str, Any]]:
        """Get all collected artifacts as dicts for JSON serialization."""
        return [a.to_dict() for a in self.artifacts]
