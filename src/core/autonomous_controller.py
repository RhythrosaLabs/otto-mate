"""
Autonomous Agent Controller
===========================

Wraps the execution agent with autonomous behavior:
- Streams progress updates in real-time
- Automatically retries with smart backoff
- Continues working through errors
- Provides status updates while waiting
- Never gives up on retryable tasks
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class AutonomousController:
    """
    Controller that makes execution truly autonomous.
    
    Features:
    - Real-time progress streaming
    - Automatic retry with adaptive delays
    - Error recovery and continuation
    - Status updates during waits
    - Parallel execution where possible
    """
    
    def __init__(self, execution_agent):
        self.execution_agent = execution_agent
        self.status_callback = None
        
    def set_status_callback(self, callback: Callable):
        """Set callback for streaming status updates."""
        self.status_callback = callback
        self.execution_agent.progress_callback = callback
        
    async def execute_autonomous(
        self,
        plan: Dict[str, Any],
        tool_registry: Any,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute plan with full autonomy - never stops, always adapts.
        
        Behavior:
        - Executes steps in order with dependencies
        - Streams progress updates to user
        - Retries automatically with smart delays
        - Continues with remaining tasks when one fails
        - Provides helpful status messages during waits
        """
        steps = plan.get("steps", [])
        if not steps:
            return {"status": "no_steps", "results": [], "artifacts": []}
        
        await self._send_status(\"starting\", f\"Starting execution of {len(steps)} tasks...\")\n        \n        # Analyze step dependencies\n        independent_steps, dependent_steps = self._analyze_dependencies(steps)\n        \n        results = []
        step_outputs = {}
        running_context = dict(context)
        
        # Execute independent steps in parallel
        if independent_steps:
            await self._send_status(\"parallel\", f\"Executing {len(independent_steps)} independent tasks in parallel...\")\n            parallel_results = await self._execute_parallel(independent_steps, tool_registry, running_context)\n            results.extend(parallel_results)
            for idx, result in zip(independent_steps, parallel_results):
                step_outputs[idx] = result
        
        # Execute dependent steps in sequence
        for idx in dependent_steps:
            step = steps[idx]
            await self._send_status(\"executing\", f\"Task {idx + 1}/{len(steps)}: {step.get('description', 'Processing...')}\")\n            \n            # Resolve dependencies
            depends_on = step.get(\"depends_on\", [])
            if depends_on:
                dependency_data = {f\"step_{dep}\": step_outputs.get(dep) for dep in depends_on}
                step[\"dependency_data\"] = dependency_data
            
            # Execute with full retry logic
            result = await self.execution_agent._execute_with_retry(
                tool_name=step[\"tool\"],
                parameters=step.get(\"parameters\", {}),
                tool_registry=tool_registry,
                context=running_context,
                step_data=step
            )
            
            step_outputs[idx] = result
            results.append({
                \"step\": idx,
                \"tool\": step[\"tool\"],
                \"description\": step.get(\"description\"),
                \"status\": \"success\" if result.get(\"success\") else \"failed\",
                \"result\": result
            })
            
            # Update context if successful
            if result.get(\"success\") and result.get(\"data\"):
                running_context = self.execution_agent._update_context(running_context, result[\"data\"], step[\"tool\"])
                await self._send_status(\"completed\", f\"✓ Completed: {step.get('description', step['tool'])}\")
            else:
                # Task failed - determine if we can continue
                error_msg = result.get(\"error\", \"Unknown error\")
                is_critical = step.get(\"critical\", step.get(\"required\", False))
                
                if is_critical:
                    await self._send_status(\"error\", f\"✗ Critical task failed: {step.get('description')}. Trying alternative approach...\")
                    # Try fallback
                    fallback_result = await self.execution_agent._try_fallback(step, tool_registry, running_context)
                    if fallback_result and fallback_result.get(\"success\"):
                        step_outputs[idx] = fallback_result
                        results[-1][\"result\"] = fallback_result
                        results[-1][\"status\"] = \"success\"
                        await self._send_status(\"recovered\", f\"✓ Alternative approach worked: {step.get('description')}\")
                    else:
                        await self._send_status(\"blocked\", f\"Cannot proceed: Critical task failed and no alternatives available.\")
                        break
                else:
                    await self._send_status(\"skipped\", f\"⚠ Task failed but continuing with remaining work: {step.get('description')}\")
                    logger.warning(f\"Non-critical step {idx} failed: {error_msg}, continuing with next steps\")
        
        # Collect all artifacts
        artifacts = self.execution_agent.get_artifacts()
        
        # Final summary
        successful = sum(1 for r in results if r[\"status\"] == \"success\")
        failed = len(results) - successful
        await self._send_status(\"summary\", f\"Completed {successful}/{len(results)} tasks successfully. {failed} tasks could not be completed.\")
        
        return {
            \"status\": \"completed\",
            \"results\": results,
            \"step_outputs\": step_outputs,
            \"artifacts\": artifacts,
            \"summary\": {
                \"total\": len(results),
                \"successful\": successful,
                \"failed\": failed
            }
        }
    
    def _analyze_dependencies(self, steps: List[Dict]) -> tuple:
        \"\"\"Separate independent steps from dependent ones.\"\"\"
        independent = []
        dependent = []
        
        for idx, step in enumerate(steps):
            if step.get(\"depends_on\"):
                dependent.append(idx)
            else:
                independent.append(idx)
        
        return independent, dependent
    
    async def _execute_parallel(
        self,
        step_indices: List[int],
        tool_registry: Any,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        \"\"\"Execute multiple independent steps in parallel.\"\"\"
        # For now, execute sequentially to avoid overwhelming APIs
        # TODO: Implement true parallel execution with rate limit coordination
        results = []
        for idx in step_indices:
            # This would be async parallel in production
            result = await self.execution_agent._execute_with_retry(
                tool_name=step[\"tool\"],
                parameters=step.get(\"parameters\", {}),
                tool_registry=tool_registry,
                context=context,
                step_data=step
            )
            results.append(result)
        return results
    
    async def _send_status(self, status_type: str, message: str):
        \"\"\"Send status update to user if callback is set.\"\"\"
        if self.status_callback:
            await self.status_callback({
                \"type\": status_type,
                \"message\": message,
                \"timestamp\": datetime.now().isoformat()
            })
        logger.info(f\"[{status_type.upper()}] {message}\")


def create_autonomous_agent(execution_agent):
    \"\"\"Factory function to create autonomous controller.\"\"\"
    return AutonomousController(execution_agent)
