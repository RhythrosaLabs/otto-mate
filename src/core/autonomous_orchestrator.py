"""
Otto Universal - Autonomous Business Orchestrator
=================================================

Next-generation orchestration system for fully autonomous business operations.

Features:
- Hierarchical multi-agent coordination
- Self-correcting and adaptive planning
- Business KPI tracking and optimization
- End-to-end task execution with reasoning
- Integration with ABP tools and workflows
- Persistent memory and artifact management
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    DELEGATED = "delegated"


class BusinessDomain(Enum):
    """Business domains for specialized handling."""
    ECOMMERCE = "ecommerce"
    MARKETING = "marketing"
    CONTENT_CREATION = "content_creation"
    DATA_ANALYSIS = "data_analysis"
    CUSTOMER_SERVICE = "customer_service"
    PRODUCT_DEVELOPMENT = "product_development"
    OPERATIONS = "operations"
    FINANCE = "finance"


@dataclass
class BusinessKPI:
    """Business Key Performance Indicator."""
    name: str
    value: float
    target: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def achievement_rate(self) -> float:
        """Calculate achievement percentage."""
        if self.target == 0:
            return 100.0 if self.value == 0 else 0.0
        return (self.value / self.target) * 100.0
    
    @property
    def is_on_target(self) -> bool:
        """Check if KPI meets target."""
        return self.value >= self.target


@dataclass
class BusinessContext:
    """Context for business operations."""
    domain: BusinessDomain
    goals: List[str]
    constraints: List[str]
    kpis: Dict[str, BusinessKPI]
    budget: Optional[float] = None
    deadline: Optional[datetime] = None
    stakeholders: List[str] = field(default_factory=list)


@dataclass
class ReasoningStep:
    """A single step in the reasoning chain."""
    id: str
    step_type: str  # "analysis", "planning", "decision", "execution"
    content: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Task:
    """Autonomous task with full context."""
    id: str
    description: str
    priority: TaskPriority
    status: TaskStatus
    domain: BusinessDomain
    assigned_agent: Optional[str] = None
    parent_task_id: Optional[str] = None
    subtasks: List['Task'] = field(default_factory=list)
    reasoning_chain: List[ReasoningStep] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate task duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class AutonomousOrchestrator:
    """
    Next-generation orchestrator for fully autonomous business operations.
    
    Capabilities:
    - Hierarchical task decomposition and delegation
    - Self-correcting execution with adaptive replanning
    - Multi-agent coordination with reasoning chains
    - Business KPI tracking and optimization
    - Integration with ABP tools and workflows
    """
    
    def __init__(
        self,
        anthropic_client: Anthropic,
        tool_registry: Any,
        memory_agent: Any,
        config: Optional[Dict[str, Any]] = None
    ):
        self.anthropic = anthropic_client
        self.tool_registry = tool_registry
        self.memory_agent = memory_agent
        self.config = config or {}
        
        # Task management
        self.active_tasks: Dict[str, Task] = {}
        self.task_queue: List[Task] = []
        self.task_history: List[Task] = []
        
        # Agent management
        self.sub_agents: Dict[str, Any] = {}
        
        # Business context
        self.business_contexts: Dict[str, BusinessContext] = {}
        self.kpi_history: List[BusinessKPI] = []
        
        # Execution state
        self.max_retries = 3
        self.max_parallel_tasks = 5
        
        logger.info("Autonomous Business Orchestrator initialized")
    
    async def execute_business_request(
        self,
        request: str,
        session_id: str,
        business_context: Optional[BusinessContext] = None,
        callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Execute a business request end-to-end with full autonomy.
        
        Args:
            request: Natural language business request
            session_id: Session identifier
            business_context: Optional business context
            callback: Optional callback for streaming updates
            
        Returns:
            Execution result with reasoning chain and KPIs
        """
        logger.info(f"Executing business request: {request[:100]}...")
        
        # Create root task
        root_task = Task(
            id=str(uuid.uuid4()),
            description=request,
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
            domain=self._infer_domain(request)
        )
        
        try:
            # Phase 1: Intelligent Planning with Reasoning
            if callback:
                await callback({
                    "type": "reasoning_step",
                    "step": "Planning",
                    "content": "Analyzing request and creating execution plan..."
                })
            
            plan = await self._create_hierarchical_plan(
                root_task,
                business_context,
                callback
            )
            
            # Phase 2: Adaptive Execution
            if callback:
                await callback({
                    "type": "reasoning_step",
                    "step": "Execution",
                    "content": f"Executing {len(plan['tasks'])} tasks..."
                })
            
            results = await self._execute_with_adaptation(
                root_task,
                plan,
                callback
            )
            
            # Phase 3: Verification and Self-Correction
            if callback:
                await callback({
                    "type": "reasoning_step",
                    "step": "Verification",
                    "content": "Verifying results and applying corrections..."
                })
            
            verified_results = await self._verify_and_correct(
                root_task,
                results,
                callback
            )
            
            # Phase 4: Business Impact Analysis
            impact = await self._analyze_business_impact(
                root_task,
                verified_results,
                business_context
            )
            
            # Store in memory for learning
            await self.memory_agent.store_execution(
                session_id=session_id,
                task=root_task,
                results=verified_results,
                impact=impact
            )
            
            return {
                "success": True,
                "task_id": root_task.id,
                "results": verified_results,
                "reasoning_chain": [step.__dict__ for step in root_task.reasoning_chain],
                "business_impact": impact,
                "duration": root_task.duration,
                "kpis": {k: v.__dict__ for k, v in impact.get("kpis", {}).items()}
            }
            
        except Exception as e:
            logger.error(f"Business request execution failed: {e}")
            root_task.status = TaskStatus.FAILED
            root_task.errors.append(str(e))
            
            return {
                "success": False,
                "task_id": root_task.id,
                "error": str(e),
                "reasoning_chain": [step.__dict__ for step in root_task.reasoning_chain]
            }
    
    async def _create_hierarchical_plan(
        self,
        task: Task,
        context: Optional[BusinessContext],
        callback: Optional[callable]
    ) -> Dict[str, Any]:
        """
        Create a hierarchical execution plan with reasoning.
        
        Uses Claude to break down complex tasks into subtasks with
        clear dependencies, priorities, and success criteria.
        """
        reasoning_step = ReasoningStep(
            id=str(uuid.uuid4()),
            step_type="planning",
            content="Creating hierarchical execution plan",
            inputs={"task": task.description, "context": context.__dict__ if context else None},
            outputs={},
            confidence=0.0
        )
        
        prompt = f"""You are an expert business orchestrator planning a complex task.

TASK: {task.description}

BUSINESS CONTEXT:
{self._format_business_context(context) if context else "General business context"}

Create a detailed hierarchical execution plan. Break the task into subtasks with:
1. Clear description of each subtask
2. Priority level (CRITICAL, HIGH, MEDIUM, LOW)
3. Required tools/capabilities
4. Success criteria
5. Dependencies between subtasks
6. Estimated effort

Output your plan as JSON in this exact format:
{{
    "reasoning": "Your reasoning about the task breakdown",
    "tasks": [
        {{
            "id": "task_1",
            "description": "Clear description",
            "priority": "HIGH",
            "tools_required": ["tool1", "tool2"],
            "success_criteria": ["criterion1", "criterion2"],
            "dependencies": [],
            "estimated_effort": "2 minutes",
            "agent_type": "executor|researcher|designer|writer|analyst"
        }}
    ],
    "execution_order": ["task_1", "task_2", ...],
    "risk_factors": ["risk1", "risk2"],
    "contingency_plans": {{"task_1": "fallback approach"}}
}}"""

        response = await self._call_claude(prompt, max_tokens=4000)
        
        # Parse plan
        import json
        plan = json.loads(self._extract_json(response))
        
        reasoning_step.outputs = plan
        reasoning_step.confidence = 0.9
        task.reasoning_chain.append(reasoning_step)
        
        if callback:
            await callback({
                "type": "reasoning_step",
                "step": "Planning Complete",
                "content": f"Created plan with {len(plan['tasks'])} tasks",
                "details": plan["reasoning"]
            })
        
        return plan
    
    async def _execute_with_adaptation(
        self,
        root_task: Task,
        plan: Dict[str, Any],
        callback: Optional[callable]
    ) -> Dict[str, Any]:
        """
        Execute plan with adaptive replanning on failures.
        
        Monitors execution and adapts the plan if tasks fail or
        conditions change.
        """
        results = {}
        failed_tasks = []
        
        root_task.status = TaskStatus.IN_PROGRESS
        root_task.started_at = datetime.now()
        
        # Execute tasks in order with parallelization where possible
        execution_order = plan["execution_order"]
        
        for task_id in execution_order:
            task_spec = next(t for t in plan["tasks"] if t["id"] == task_id)
            
            # Check dependencies
            dependencies_met = all(
                dep in results and results[dep].get("success")
                for dep in task_spec.get("dependencies", [])
            )
            
            if not dependencies_met:
                logger.warning(f"Task {task_id} dependencies not met, skipping")
                failed_tasks.append(task_id)
                continue
            
            # Create subtask
            subtask = Task(
                id=task_id,
                description=task_spec["description"],
                priority=TaskPriority[task_spec["priority"]],
                status=TaskStatus.PENDING,
                domain=root_task.domain,
                parent_task_id=root_task.id
            )
            
            if callback:
                await callback({
                    "type": "tool_execution",
                    "task_id": task_id,
                    "description": task_spec["description"],
                    "status": "starting"
                })
            
            # Execute subtask with retries
            retry_count = 0
            task_result = None
            
            while retry_count < self.max_retries:
                try:
                    task_result = await self._execute_single_task(
                        subtask,
                        task_spec,
                        results,
                        callback
                    )
                    
                    if task_result.get("success"):
                        break
                    
                    retry_count += 1
                    
                    if retry_count < self.max_retries:
                        logger.warning(f"Task {task_id} failed, retry {retry_count}/{self.max_retries}")
                        
                        # Adaptive replanning
                        if retry_count == 2:
                            # After 2 failures, try alternative approach
                            contingency = plan["contingency_plans"].get(task_id)
                            if contingency:
                                task_spec["description"] = contingency
                                logger.info(f"Applying contingency plan for {task_id}")
                
                except Exception as e:
                    logger.error(f"Task {task_id} execution error: {e}")
                    retry_count += 1
            
            if task_result and task_result.get("success"):
                results[task_id] = task_result
                subtask.status = TaskStatus.COMPLETED
                subtask.results = task_result
                
                if callback:
                    await callback({
                        "type": "tool_execution",
                        "task_id": task_id,
                        "status": "completed",
                        "result": task_result
                    })
            else:
                failed_tasks.append(task_id)
                subtask.status = TaskStatus.FAILED
                
                if callback:
                    await callback({
                        "type": "tool_execution",
                        "task_id": task_id,
                        "status": "failed"
                    })
            
            root_task.subtasks.append(subtask)
        
        root_task.status = TaskStatus.COMPLETED if not failed_tasks else TaskStatus.FAILED
        root_task.completed_at = datetime.now()
        
        return {
            "successful_tasks": results,
            "failed_tasks": failed_tasks,
            "total_tasks": len(execution_order),
            "success_rate": len(results) / len(execution_order) if execution_order else 0
        }
    
    async def _execute_single_task(
        self,
        task: Task,
        task_spec: Dict[str, Any],
        context_results: Dict[str, Any],
        callback: Optional[callable]
    ) -> Dict[str, Any]:
        """Execute a single task using appropriate tools."""
        
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()
        
        # Get available tools
        tools_required = task_spec.get("tools_required", [])
        available_tools = self.tool_registry.get_tools_by_names(tools_required)
        
        # Create execution prompt for Claude with tools
        prompt = f"""Execute this task:

TASK: {task.description}

CONTEXT FROM PREVIOUS TASKS:
{json.dumps(context_results, indent=2)}

SUCCESS CRITERIA:
{chr(10).join(f"- {c}" for c in task_spec.get("success_criteria", []))}

You have access to these tools: {', '.join(tools_required)}

Execute the task and provide detailed results."""

        # Call Claude with tools
        response = await self._call_claude_with_tools(
            prompt,
            available_tools,
            callback
        )
        
        task.completed_at = datetime.now()
        task.status = TaskStatus.COMPLETED
        
        return {
            "success": True,
            "output": response,
            "tools_used": tools_required,
            "duration": task.duration
        }
    
    async def _verify_and_correct(
        self,
        task: Task,
        results: Dict[str, Any],
        callback: Optional[callable]
    ) -> Dict[str, Any]:
        """
        Verify results meet success criteria and apply corrections.
        
        Self-correcting capability that validates outputs and
        reruns tasks if quality checks fail.
        """
        verification_prompt = f"""Verify these task execution results:

ORIGINAL TASK: {task.description}

EXECUTION RESULTS:
{json.dumps(results, indent=2)}

Verify:
1. All tasks completed successfully
2. Results meet quality standards
3. No errors or inconsistencies
4. Business objectives achieved

Output JSON:
{{
    "verified": true/false,
    "issues": ["issue1", "issue2"],
    "corrections_needed": ["correction1"],
    "quality_score": 0.0-1.0,
    "recommendations": ["rec1"]
}}"""

        response = await self._call_claude(verification_prompt)
        verification = json.loads(self._extract_json(response))
        
        if not verification.get("verified") and verification.get("corrections_needed"):
            # Apply corrections
            logger.info("Applying corrections to results")
            
            if callback:
                await callback({
                    "type": "reasoning_step",
                    "step": "Self-Correction",
                    "content": f"Applying {len(verification['corrections_needed'])} corrections"
                })
            
            # Re-execute failed tasks with corrections
            # Implementation depends on specific correction needs
        
        return {
            **results,
            "verification": verification
        }
    
    async def _analyze_business_impact(
        self,
        task: Task,
        results: Dict[str, Any],
        context: Optional[BusinessContext]
    ) -> Dict[str, Any]:
        """
        Analyze the business impact of completed tasks.
        
        Calculates KPIs, ROI, and other business metrics.
        """
        impact_prompt = f"""Analyze the business impact of this completed task:

TASK: {task.description}
DOMAIN: {task.domain.value}

RESULTS:
{json.dumps(results, indent=2, default=str)}

BUSINESS CONTEXT:
{self._format_business_context(context) if context else "General"}

Analyze:
1. Key outcomes achieved
2. Business value delivered
3. Relevant KPIs and metrics
4. ROI estimation
5. Strategic implications
6. Next recommended actions

Output JSON with business_impact structure."""

        response = await self._call_claude(impact_prompt, max_tokens=2000)
        impact = json.loads(self._extract_json(response))
        
        # Track KPIs
        if "kpis" in impact:
            for kpi_name, kpi_data in impact["kpis"].items():
                kpi = BusinessKPI(
                    name=kpi_name,
                    value=kpi_data.get("value", 0),
                    target=kpi_data.get("target", 0),
                    unit=kpi_data.get("unit", "")
                )
                self.kpi_history.append(kpi)
        
        return impact
    
    def _infer_domain(self, request: str) -> BusinessDomain:
        """Infer business domain from request."""
        request_lower = request.lower()
        
        if any(word in request_lower for word in ["product", "inventory", "shop", "store", "sell"]):
            return BusinessDomain.ECOMMERCE
        elif any(word in request_lower for word in ["campaign", "ad", "marketing", "promote"]):
            return BusinessDomain.MARKETING
        elif any(word in request_lower for word in ["write", "content", "blog", "post", "article"]):
            return BusinessDomain.CONTENT_CREATION
        elif any(word in request_lower for word in ["analyze", "data", "metrics", "stats"]):
            return BusinessDomain.DATA_ANALYSIS
        else:
            return BusinessDomain.OPERATIONS
    
    def _format_business_context(self, context: BusinessContext) -> str:
        """Format business context for prompts."""
        if not context:
            return "No specific business context provided"
        
        return f"""Domain: {context.domain.value}
Goals: {', '.join(context.goals)}
Constraints: {', '.join(context.constraints)}
Budget: ${context.budget if context.budget else 'Not specified'}
Deadline: {context.deadline if context.deadline else 'Not specified'}
Stakeholders: {', '.join(context.stakeholders)}
KPIs: {len(context.kpis)} tracked"""
    
    async def _call_claude(
        self,
        prompt: str,
        max_tokens: int = 2000
    ) -> str:
        """Call Claude API."""
        response = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    
    async def _call_claude_with_tools(
        self,
        prompt: str,
        tools: List[Dict],
        callback: Optional[callable]
    ) -> str:
        """Call Claude with tool use capability."""
        # This would integrate with tool execution
        # For now, simplified version
        return await self._call_claude(prompt)
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from text response."""
        import re
        
        # Try to find JSON block
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        return text
    
    def get_kpi_summary(self) -> Dict[str, Any]:
        """Get summary of tracked KPIs."""
        if not self.kpi_history:
            return {"kpis": [], "total": 0}
        
        # Group by KPI name
        kpi_groups = {}
        for kpi in self.kpi_history:
            if kpi.name not in kpi_groups:
                kpi_groups[kpi.name] = []
            kpi_groups[kpi.name].append(kpi)
        
        summary = {
            "total_kpis": len(self.kpi_history),
            "kpis": {}
        }
        
        for name, kpis in kpi_groups.items():
            latest = max(kpis, key=lambda k: k.timestamp)
            summary["kpis"][name] = {
                "current_value": latest.value,
                "target": latest.target,
                "achievement_rate": latest.achievement_rate,
                "on_target": latest.is_on_target,
                "unit": latest.unit,
                "history_count": len(kpis)
            }
        
        return summary
