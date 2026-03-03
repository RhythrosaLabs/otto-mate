"""
Unified Agent System - Otto Universal
======================================

A super-intelligent agent framework combining the best patterns from:
- CrewAI: Multi-agent collaboration and memory
- Claude SDK: Bidirectional communication and streaming  
- AutoGPT: Autonomous execution and workflows
- Browser-Use: Vision and state management
- AgentOps: Observability and monitoring

This system provides:
- Autonomous task execution with self-correction
- Multi-agent collaboration and delegation
- Real-time streaming and bidirectional communication
- Vision-enabled perception
- Comprehensive observability
- Memory and learning
- Tool execution with retry and fallback
"""

import asyncio
import logging
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Union, Literal
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from anthropic import Anthropic, AsyncAnthropic

from .agent_health_monitor import get_health_monitor
from .error_recovery import get_recovery_manager
from .agent_analytics import get_analytics
from .agent_communication import get_message_bus, MessageType
from .context_manager import ContextManager
from .memory_agent import MemoryAgent

# Import new intelligence systems (optional, graceful fallback)
try:
    from .enhanced_reasoning import get_reasoner, ReasoningStrategy
    ENHANCED_REASONING_AVAILABLE = True
except ImportError:
    ENHANCED_REASONING_AVAILABLE = False

try:
    from .result_verifier import get_verifier, VerificationLevel
    RESULT_VERIFIER_AVAILABLE = True
except ImportError:
    RESULT_VERIFIER_AVAILABLE = False

try:
    from .tool_composer import get_composer
    TOOL_COMPOSER_AVAILABLE = True
except ImportError:
    TOOL_COMPOSER_AVAILABLE = False

logger = logging.getLogger(__name__)


# ============================================================================
# Core Types and Enums
# ============================================================================

class AgentRole(Enum):
    """Specialized agent roles."""
    ORCHESTRATOR = "orchestrator"
    PLANNER = "planner"
    EXECUTOR = "executor"
    RESEARCHER = "researcher"
    ANALYZER = "analyzer"
    VERIFIER = "verifier"
    MEMORY = "memory"
    TOOL_SPECIALIST = "tool_specialist"
    VISION = "vision"


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class AgentMode(Enum):
    """Agent execution modes."""
    AUTONOMOUS = "autonomous"  # Fully autonomous
    INTERACTIVE = "interactive"  # Requires human confirmation
    COLLABORATIVE = "collaborative"  # Multi-agent
    SUPERVISED = "supervised"  # Human oversight


# ============================================================================
# Agent Configuration
# ============================================================================

@dataclass
class AgentConfig:
    """Configuration for an intelligent agent."""
    agent_id: str
    role: AgentRole
    name: str
    description: str
    
    # Capabilities
    capabilities: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    
    # Behavior
    mode: AgentMode = AgentMode.AUTONOMOUS
    max_iterations: int = 10
    max_retries: int = 3
    temperature: float = 0.7
    
    # Features
    use_memory: bool = True
    use_vision: bool = False
    use_thinking: bool = True
    use_planning: bool = True
    use_enhanced_reasoning: bool = True  # Use multi-strategy reasoning
    use_result_verification: bool = True  # Verify outputs
    use_tool_composition: bool = True  # Chain tools automatically
    
    # Model config
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    
    # Reasoning config
    reasoning_strategy: Optional[str] = None  # Force specific strategy
    min_confidence: float = 0.7  # Minimum confidence for results
    verification_level: str = "standard"  # quick, standard, thorough, critical
    
    # System prompts
    system_prompt: Optional[str] = None
    backstory: Optional[str] = None
    
    # Collaboration
    can_delegate: bool = True
    delegate_to: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "role": self.role.value,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "tools": self.tools,
            "mode": self.mode.value,
            "use_memory": self.use_memory,
            "use_vision": self.use_vision,
        }


# ============================================================================
# Task Definition
# ============================================================================

@dataclass
class AgentTask:
    """A task to be executed by an agent."""
    task_id: str
    description: str
    goal: str
    
    # Assignment
    assigned_to: Optional[str] = None
    created_by: Optional[str] = None
    
    # Execution
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 1
    max_steps: int = 20
    
    # Context
    context: Dict[str, Any] = field(default_factory=dict)
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    
    # Dependencies
    depends_on: List[str] = field(default_factory=list)
    blocks: List[str] = field(default_factory=list)
    
    # Tracking
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results
    result: Optional[Any] = None
    error: Optional[str] = None
    steps_taken: int = 0
    
    # Observability
    thinking_log: List[str] = field(default_factory=list)
    action_log: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate task duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


# ============================================================================
# Intelligent Agent
# ============================================================================

class IntelligentAgent:
    """
    A super-intelligent agent that can understand and do anything.
    
    Features:
    - Autonomous reasoning and planning
    - Tool execution with retry and fallback
    - Memory and learning
    - Vision capabilities
    - Self-correction and verification
    - Multi-agent collaboration
    - Real-time streaming
    """
    
    def __init__(
        self,
        config: AgentConfig,
        anthropic_client: Anthropic,
        tool_registry: Any,
        memory_agent: Optional[MemoryAgent] = None
    ):
        self.config = config
        self.anthropic = anthropic_client
        # Create async client for use in async methods
        self.async_anthropic = AsyncAnthropic(api_key=anthropic_client.api_key)
        self.tool_registry = tool_registry
        self.memory_agent = memory_agent or MemoryAgent()
        
        # Monitoring systems
        self.health_monitor = get_health_monitor()
        self.recovery_manager = get_recovery_manager()
        self.analytics = get_analytics()
        self.message_bus = get_message_bus()
        
        # Context management
        self.context_manager = ContextManager(self.memory_agent)
        
        # Register with health monitor
        self.health_monitor.register_agent(config.agent_id, config.role.value)
        
        # Register with message bus
        self.endpoint = self.message_bus.register_agent(config.agent_id)
        
        # State
        self.current_task: Optional[AgentTask] = None
        self.is_running = False
        
        logger.info(f"Initialized {config.role.value} agent: {config.name}")
    
    async def execute_task(
        self,
        task: AgentTask,
        stream: bool = False
    ) -> Union[Dict[str, Any], AsyncIterator[Dict[str, Any]]]:
        """
        Execute a task with full autonomy and intelligence.
        
        Args:
            task: The task to execute
            stream: Whether to stream progress
            
        Returns:
            Task result or stream of progress updates
        """
        start_time = datetime.now()
        self.current_task = task
        self.is_running = True
        
        task.status = TaskStatus.PLANNING
        task.started_at = start_time
        
        try:
            # 1. THINK & PLAN
            if self.config.use_thinking:
                plan = await self._create_execution_plan(task)
                task.thinking_log.append(f"Plan created: {plan}")
            
            # 2. EXECUTE with self-correction
            task.status = TaskStatus.EXECUTING
            result = await self._execute_with_intelligence(task, stream)
            
            # 3. VERIFY if enabled
            if self.config.use_planning:
                task.status = TaskStatus.VERIFYING
                verified = await self._verify_result(task, result)
                if not verified:
                    # Self-correct
                    result = await self._self_correct(task, result)
            
            # 4. COMPLETE
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            
            # Record success
            duration_ms = (task.completed_at - start_time).total_seconds() * 1000
            self.analytics.record_task_execution(
                task_id=task.task_id,
                agent_id=self.config.agent_id,
                agent_type=self.config.role.value,
                start_time=start_time,
                end_time=task.completed_at,
                success=True,
                steps_executed=task.steps_taken,
                tools_used=[a["tool"] for a in task.action_log if "tool" in a]
            )
            
            self.health_monitor.record_task_execution(
                agent_id=self.config.agent_id,
                success=True,
                response_time_ms=duration_ms
            )
            
            return {
                "status": "success",
                "task_id": task.task_id,
                "result": result,
                "duration": task.duration,
                "steps_taken": task.steps_taken
            }
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}", exc_info=True)
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error = str(e)
            
            # Record failure
            duration_ms = (task.completed_at - start_time).total_seconds() * 1000
            self.health_monitor.record_task_execution(
                agent_id=self.config.agent_id,
                success=False,
                response_time_ms=duration_ms,
                error=str(e)
            )
            
            return {
                "status": "failed",
                "task_id": task.task_id,
                "error": str(e),
                "duration": task.duration
            }
            
        finally:
            self.is_running = False
            self.current_task = None
    
    async def _create_execution_plan(self, task: AgentTask) -> Dict[str, Any]:
        """Create an intelligent execution plan."""
        system_prompt = f"""You are {self.config.name}, a {self.config.role.value} agent.

Your capabilities: {', '.join(self.config.capabilities)}
Available tools: {', '.join(self.config.tools)}

Task: {task.description}
Goal: {task.goal}

Create a step-by-step execution plan to accomplish this task.
Think carefully about:
1. What information you need
2. What tools to use
3. The optimal sequence of actions
4. Potential failure points and fallbacks
5. Success criteria

Respond with a detailed plan in JSON format."""

        response = await self.async_anthropic.messages.create(
            model=self.config.model,
            max_tokens=2048,
            temperature=self.config.temperature,
            messages=[{
                "role": "user",
                "content": system_prompt
            }]
        )
        
        # Parse plan from response
        plan_text = response.content[0].text
        # Simple plan extraction - in production, use structured output
        return {"plan": plan_text, "steps": []}
    
    async def _execute_with_intelligence(
        self,
        task: AgentTask,
        stream: bool
    ) -> Any:
        """Execute task with intelligence and self-correction."""
        iteration = 0
        last_result = None
        
        while iteration < self.config.max_iterations:
            iteration += 1
            task.steps_taken = iteration
            
            # Get context
            context = self.context_manager.get_context_for_agent(
                session_id=task.task_id,
                agent_type=self.config.role.value
            )
            
            # Decide next action
            action = await self._decide_next_action(task, context, last_result)
            
            if action["type"] == "complete":
                return action["result"]
            
            # Execute action with recovery
            success, result, error = await self.recovery_manager.execute_with_recovery(
                service_name=f"{self.config.agent_id}_action",
                func=self._execute_action,
                action=action,
                task=task
            )
            
            # Log action
            task.action_log.append({
                "iteration": iteration,
                "action": action,
                "success": success,
                "result": result if success else None,
                "error": error
            })
            
            last_result = result
            
            # Check if we should continue
            if not success and iteration >= self.config.max_retries:
                raise Exception(f"Max retries reached. Last error: {error}")
        
        # Max iterations reached
        return last_result
    
    async def _decide_next_action(
        self,
        task: AgentTask,
        context: Dict[str, Any],
        last_result: Any
    ) -> Dict[str, Any]:
        """Intelligently decide the next action using enhanced reasoning if available."""
        
        # Use enhanced reasoning for complex decisions
        if ENHANCED_REASONING_AVAILABLE and self.config.use_enhanced_reasoning:
            try:
                reasoner = get_reasoner()
                
                decision_query = f"""Decide the next action for this task:
Task: {task.description}
Goal: {task.goal}
Progress: {len(task.action_log)} actions taken
Available tools: {', '.join(self.config.tools)}
Previous result: {last_result}

What should be done next? Options: use a specific tool, delegate, or mark complete."""

                result = await reasoner.reason(
                    query=decision_query,
                    context=str(context),
                    require_steps=False
                )
                
                decision_text = result.answer
                task.thinking_log.append(
                    f"Decision (confidence: {result.confidence:.2f}): {decision_text[:200]}..."
                )
                
                # Parse enhanced decision
                if "complete" in decision_text.lower() and result.confidence >= 0.7:
                    return {"type": "complete", "result": last_result}
                
                # Try to extract tool from response
                for tool_name in self.config.tools:
                    if tool_name.lower() in decision_text.lower():
                        return {
                            "type": "tool",
                            "tool": tool_name,
                            "parameters": {},
                            "reasoning": decision_text
                        }
                
            except Exception as e:
                logger.warning(f"Enhanced reasoning failed, using fallback: {e}")
        
        # Fallback to original decision logic
        prompt = f"""Task: {task.description}
Goal: {task.goal}
Current progress: {len(task.action_log)} actions taken

Available tools: {', '.join(self.config.tools)}

Previous result: {last_result}

Context: {context}

What should you do next to accomplish this task?
Options:
1. Use a tool
2. Delegate to another agent
3. Complete the task

Think step by step and decide the optimal next action."""

        response = await self.async_anthropic.messages.create(
            model=self.config.model,
            max_tokens=1024,
            temperature=self.config.temperature,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # Parse decision - in production, use structured output
        decision_text = response.content[0].text
        
        # Simple decision parsing
        if "complete" in decision_text.lower():
            return {"type": "complete", "result": last_result}
        
        # Extract tool name and parameters
        return {
            "type": "tool",
            "tool": "example_tool",
            "parameters": {}
        }
    
    async def _execute_action(
        self,
        action: Dict[str, Any],
        task: AgentTask
    ) -> Any:
        """Execute a specific action."""
        if action["type"] == "tool":
            tool = self.tool_registry.get_tool(action["tool"])
            if not tool:
                raise ValueError(f"Tool not found: {action['tool']}")
            
            # Pre-filter known meta-parameters that should never be passed to tools
            params = action.get("parameters", {})
            meta_params_to_remove = {'task_description', 'task_type', 'task_id', 'step_id', 'execution_context'}
            params = {k: v for k, v in params.items() if k not in meta_params_to_remove}
            
            result = await tool(**params)
            return result
        
        elif action["type"] == "delegate":
            # Delegate to another agent via message bus
            response = await self.endpoint.request(
                to_agent=action["delegate_to"],
                content={
                    "action": "execute_task",
                    "task": task.to_dict()
                },
                timeout=60.0
            )
            return response
        
        return None
    
    async def _verify_result(self, task: AgentTask, result: Any) -> bool:
        """Verify if the result meets the goal."""
        # Use enhanced verification if available
        if RESULT_VERIFIER_AVAILABLE and self.config.use_result_verification:
            try:
                verifier = get_verifier()
                level_map = {
                    "quick": VerificationLevel.QUICK,
                    "standard": VerificationLevel.STANDARD,
                    "thorough": VerificationLevel.THOROUGH,
                    "critical": VerificationLevel.CRITICAL
                }
                level = level_map.get(self.config.verification_level, VerificationLevel.STANDARD)
                
                report = await verifier.verify(
                    result=result,
                    task_description=f"{task.description} - Goal: {task.goal}",
                    level=level,
                    retry_on_fail=False  # We handle retry in _self_correct
                )
                
                task.thinking_log.append(
                    f"Verification: {report.result.value} (confidence: {report.confidence:.2f})"
                )
                
                # Update result if improved version available
                if report.improved_result:
                    task.result = report.improved_result
                
                return report.confidence >= self.config.min_confidence
                
            except Exception as e:
                logger.warning(f"Enhanced verification failed, using fallback: {e}")
        
        # Fallback to simple verification
        prompt = f"""Task: {task.description}
Goal: {task.goal}
Result: {result}

Does this result successfully accomplish the goal?
Respond with YES or NO and explain why."""

        response = await self.async_anthropic.messages.create(
            model=self.config.model,
            max_tokens=512,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        verification = response.content[0].text
        return "yes" in verification.lower()
    
    async def _self_correct(self, task: AgentTask, result: Any) -> Any:
        """Self-correct a failed result."""
        prompt = f"""The previous attempt to complete this task was not successful.

Task: {task.description}
Goal: {task.goal}
Previous result: {result}

What went wrong and how can you fix it?
Create a corrected approach."""

        response = await self.async_anthropic.messages.create(
            model=self.config.model,
            max_tokens=1024,
            temperature=self.config.temperature,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # Re-execute with corrected approach
        return await self._execute_with_intelligence(task, False)
    
    async def delegate_task(
        self,
        task: AgentTask,
        to_agent_id: str
    ) -> Dict[str, Any]:
        """Delegate a task to another agent."""
        response = await self.endpoint.request(
            to_agent=to_agent_id,
            content={
                "action": "execute_task",
                "task": {
                    "task_id": task.task_id,
                    "description": task.description,
                    "goal": task.goal,
                    "context": task.context
                }
            },
            timeout=120.0
        )
        
        return response or {}
    
    async def collaborate(
        self,
        task: AgentTask,
        collaborators: List[str]
    ) -> Dict[str, Any]:
        """Collaborate with multiple agents on a task."""
        # Initiate collaboration
        collab_id = await self.message_bus.initiate_collaboration(
            initiator_agent=self.config.agent_id,
            participating_agents=collaborators,
            task_description=task.description,
            shared_context=task.context
        )
        
        # Execute collaborative workflow
        results = {}
        for agent_id in collaborators:
            response = await self.endpoint.request(
                to_agent=agent_id,
                content={
                    "collaboration_id": collab_id,
                    "action": "contribute",
                    "task": task.description
                }
            )
            results[agent_id] = response
        
        return {
            "collaboration_id": collab_id,
            "results": results
        }


# ============================================================================
# Agent Crew (Multi-Agent System)
# ============================================================================

class AgentCrew:
    """
    A crew of specialized agents working together.
    
    Inspired by CrewAI but enhanced with:
    - Real-time communication
    - Autonomous coordination
    - Shared memory
    - Health monitoring
    """
    
    def __init__(
        self,
        name: str,
        anthropic_client: Anthropic,
        tool_registry: Any
    ):
        self.name = name
        self.anthropic = anthropic_client
        self.async_anthropic = AsyncAnthropic(api_key=anthropic_client.api_key)
        self.tool_registry = tool_registry
        self.agents: Dict[str, IntelligentAgent] = {}
        self.memory = MemoryAgent()
        
        logger.info(f"Created crew: {name}")
    
    def add_agent(self, config: AgentConfig) -> IntelligentAgent:
        """Add an agent to the crew."""
        agent = IntelligentAgent(
            config=config,
            anthropic_client=self.anthropic,
            tool_registry=self.tool_registry,
            memory_agent=self.memory
        )
        self.agents[config.agent_id] = agent
        logger.info(f"Added {config.role.value} to crew: {config.name}")
        return agent
    
    async def execute_task(
        self,
        task: AgentTask,
        coordinator: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a task with the crew."""
        # Assign to coordinator or orchestrator
        if coordinator and coordinator in self.agents:
            agent = self.agents[coordinator]
        else:
            # Find best agent for the task
            agent = self._select_best_agent(task)
        
        # Execute with the selected agent
        result = await agent.execute_task(task)
        
        return {
            "task_id": task.task_id,
            "executed_by": agent.config.agent_id,
            "result": result
        }
    
    def _select_best_agent(self, task: AgentTask) -> IntelligentAgent:
        """Select the best agent for a task based on capabilities."""
        # Simple selection - in production, use intelligent matching
        for agent in self.agents.values():
            if agent.config.role == AgentRole.ORCHESTRATOR:
                return agent
        
        # Return first agent if no orchestrator
        return list(self.agents.values())[0]
    
    def get_crew_status(self) -> Dict[str, Any]:
        """Get status of all agents in the crew."""
        return {
            "crew_name": self.name,
            "total_agents": len(self.agents),
            "agents": {
                agent_id: {
                    "name": agent.config.name,
                    "role": agent.config.role.value,
                    "is_running": agent.is_running,
                    "current_task": agent.current_task.task_id if agent.current_task else None
                }
                for agent_id, agent in self.agents.items()
            }
        }
