"""
Streaming Support for Agent Orchestrator
=========================================

Extension to add real-time streaming responses.
"""

import logging
import json
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional

logger = logging.getLogger(__name__)


async def process_streaming(
    self,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Process a message with streaming responses.
    
    Yields chunks of:
    - type: "thinking" | "tool_start" | "tool_progress" | "tool_end" | "text" | "artifact" | "complete"
    - content: The content for this chunk
    - metadata: Additional context
    
    Example usage:
        async for chunk in otto.process_streaming(message):
            print(chunk)
    """
    try:
        # Yield thinking notification
        yield {
            "type": "thinking",
            "content": "Analyzing your request...",
            "metadata": {"step": "planning"}
        }
        
        # Get or create session
        session = self._get_or_create_session(session_id, context)
        
        # Retrieve relevant memories
        memories = await self.memory_agent.get_relevant_memories(
            query=message,
            session_id=session["id"],
            limit=5
        )
        
        yield {
            "type": "thinking",
            "content": "Creating execution plan...",
            "metadata": {"step": "planning", "memories_found": len(memories)}
        }
        
        # Build planning context
        available_tools = self.tool_registry.list_tools()
        limited_tools = [
            {"name": t["name"], "description": t["description"], "category": t.get("category", "general")}
            for t in available_tools[:50]  # Limit for token efficiency
        ]
        
        planning_context = {
            "message": message,
            "memories": memories[:5],
            "session": {"id": session["id"]},
            "available_tools": limited_tools
        }
        
        # Step 1: Planning
        logger.info(f"Planning for: {message}")
        plan = await self.planning_agent.create_plan(planning_context)
        
        if not plan.get("steps"):
            # Simple response, stream it
            yield {
                "type": "thinking",
                "content": "Formulating response...",
                "metadata": {"step": "generation"}
            }
            
            response = await self._generate_simple_response(message, memories)
            
            # Stream response word by word for typing effect
            words = response.split()
            partial = ""
            for i, word in enumerate(words):
                partial += word + " "
                yield {
                    "type": "text",
                    "content": word + " ",
                    "metadata": {"partial": partial.strip(), "progress": (i+1)/len(words)}
                }
                await asyncio.sleep(0.03)  # Typing effect delay
            
            # Store in memory
            await self.memory_agent.store_message(
                session_id=session["id"],
                role="assistant",
                content=response,
                metadata={"type": "simple_response"}
            )
            
            yield {
                "type": "complete",
                "session_id": session["id"]
            }
            return
        
        # Step 2: Execution with streaming updates
        steps = plan.get("steps", [])
        yield {
            "type": "thinking",
            "content": f"Executing {len(steps)} steps...",
            "metadata": {"step": "execution", "total_steps": len(steps)}
        }
        
        step_outputs = {}
        artifacts = []
        
        for idx, step in enumerate(steps):
            step_name = step.get("description", step.get("tool", "Unknown"))
            
            # Notify step start
            yield {
                "type": "tool_start",
                "content": step_name,
                "metadata": {
                    "step_index": idx,
                    "total_steps": len(steps),
                    "tool": step.get("tool")
                }
            }
            
            try:
                # Execute tool
                logger.info(f"Executing step {idx + 1}/{len(steps)}: {step_name}")
                result = await self.execution_agent.execute_tool(
                    tool_name=step.get("tool"),
                    parameters=step.get("parameters", {}),
                    tool_registry=self.tool_registry,
                    context={"session": session, "memories": memories},
                    step_data=step
                )
                
                step_outputs[str(idx)] = result
                
                # Check for artifacts
                if "artifact" in result:
                    artifacts.append(result["artifact"])
                    yield {
                        "type": "artifact",
                        "content": result["artifact"],
                        "metadata": {"step": idx, "tool": step.get("tool")}
                    }
                
                # Notify step completion
                yield {
                    "type": "tool_end",
                    "content": step_name,
                    "metadata": {
                        "step_index": idx,
                        "success": not result.get("error"),
                        "result_preview": str(result.get("result", ""))[:200]
                    }
                }
                
            except Exception as e:
                logger.error(f"Step {idx} failed: {e}")
                yield {
                    "type": "tool_end",
                    "content": step_name,
                    "metadata": {
                        "step_index": idx,
                        "success": False,
                        "error": str(e)
                    }
                }
        
        # Step 3: Generate final response with streaming
        yield {
            "type": "thinking",
            "content": "Formulating final response...",
            "metadata": {"step": "synthesis"}
        }
        
        execution_result = {
            "status": "success",
            "results": list(step_outputs.values()),
            "artifacts": artifacts
        }
        
        response = await self._generate_final_response(
            message=message,
            plan=plan,
            execution_result=execution_result,
            memories=memories
        )
        
        # Stream response
        words = response.split()
        partial = ""
        for i, word in enumerate(words):
            partial += word + " "
            yield {
                "type": "text",
                "content": word + " ",
                "metadata": {"partial": partial.strip(), "progress": (i+1)/len(words)}
            }
            await asyncio.sleep(0.02)
        
        # Store in memory
        await self.memory_agent.store_message(
            session_id=session["id"],
            role="assistant",
            content=response,
            metadata={
                "type": "tool_execution",
                "plan": plan,
                "execution_result": execution_result
            }
        )
        
        # Send completion with session ID
        yield {
            "type": "complete",
            "session_id": session["id"],
            "artifacts": artifacts
        }
        
    except Exception as e:
        logger.error(f"Streaming error: {e}", exc_info=True)
        yield {
            "type": "error",
            "content": str(e),
            "metadata": {"error_type": type(e).__name__}
        }


# Add to AgentOrchestrator class
def add_streaming_support(orchestrator_class):
    """Monkey-patch streaming support into AgentOrchestrator."""
    orchestrator_class.process_streaming = process_streaming
