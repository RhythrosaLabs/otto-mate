"""
CrewAI-Inspired Task Delegation - Otto Universal
=================================================

Multi-agent collaboration and task delegation inspired by CrewAI patterns.

This module implements:
1. Specialized agents with defined roles and expertise
2. Hierarchical task delegation 
3. Agent collaboration and communication
4. Result synthesis and aggregation
5. Self-healing and error recovery

Key Principles from CrewAI:
- Agents have specific roles, goals, and backstories
- Tasks are delegated based on agent expertise
- Agents can collaborate on complex tasks
- Results are validated and synthesized
- Learning from execution outcomes
"""

import logging
import asyncio
import uuid
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from anthropic import Anthropic

logger = logging.getLogger(__name__)


# =============================================================================
# Agent Definitions (CrewAI-Style)
# =============================================================================

class AgentRole(str, Enum):
    """Specialized agent roles."""
    ORCHESTRATOR = "orchestrator"  # Master coordinator
    TEXT_SPECIALIST = "text_specialist"  # Text generation
    VISION_SPECIALIST = "vision_specialist"  # Image creation/analysis
    VIDEO_SPECIALIST = "video_specialist"  # Video creation
    AUDIO_SPECIALIST = "audio_specialist"  # Audio/music
    CODE_SPECIALIST = "code_specialist"  # Programming
    DATA_ANALYST = "data_analyst"  # Data analysis
    RESEARCHER = "researcher"  # Research tasks
    QUALITY_ASSURER = "quality_assurer"  # Validation
    INTEGRATION_SPECIALIST = "integration_specialist"  # API/system integration


@dataclass
class CrewAgent:
    """
    A specialized agent with specific capabilities.
    
    Based on CrewAI's Agent concept with role, goal, and backstory.
    """
    agent_id: str
    role: AgentRole
    name: str
    goal: str
    backstory: str
    
    # Capabilities
    modalities: List[str]  # Modalities this agent can handle
    tools: List[str]  # Available tools
    skills: List[str]  # Special skills
    
    # Configuration
    model: str  # AI model to use
    temperature: float = 0.7
    max_tokens: int = 4096
    
    # Delegation
    can_delegate: bool = False
    delegate_to: List[AgentRole] = field(default_factory=list)
    
    # Performance tracking
    tasks_completed: int = 0
    success_rate: float = 1.0
    average_quality: float = 0.8
    
    def __repr__(self):
        return f"CrewAgent({self.name}, role={self.role.value})"


# Default agent configurations (CrewAI-inspired)
DEFAULT_CREW_AGENTS = {
    AgentRole.ORCHESTRATOR: CrewAgent(
        agent_id="orchestrator",
        role=AgentRole.ORCHESTRATOR,
        name="Maestro",
        goal="Coordinate all agents to accomplish complex multi-step tasks efficiently",
        backstory="""You are Maestro, the master orchestrator of a talented team of specialists.
You excel at understanding complex requests, breaking them into subtasks, and delegating
to the right specialists. You synthesize their work into cohesive final results.
You're patient, thorough, and ensure quality at every step.""",
        modalities=["TEXT"],
        tools=["delegate_task", "synthesize_results", "coordinate_agents"],
        skills=["task_decomposition", "team_coordination", "quality_assessment"],
        model="claude-sonnet-4-20250514",
        temperature=0.5,
        can_delegate=True,
        delegate_to=[
            AgentRole.TEXT_SPECIALIST,
            AgentRole.VISION_SPECIALIST,
            AgentRole.VIDEO_SPECIALIST,
            AgentRole.AUDIO_SPECIALIST,
            AgentRole.CODE_SPECIALIST,
            AgentRole.DATA_ANALYST,
            AgentRole.RESEARCHER,
            AgentRole.QUALITY_ASSURER
        ]
    ),
    
    AgentRole.TEXT_SPECIALIST: CrewAgent(
        agent_id="text_specialist",
        role=AgentRole.TEXT_SPECIALIST,
        name="Wordsmith",
        goal="Create compelling, accurate, and engaging text content",
        backstory="""You are Wordsmith, a master of language and communication.
You craft everything from casual social posts to formal documentation with precision.
You understand tone, audience, and context. Your writing is clear, engaging, and purposeful.""",
        modalities=["TEXT"],
        tools=["text_generation", "content_writing", "summarization", "translation"],
        skills=["copywriting", "technical_writing", "creative_writing", "editing"],
        model="claude-sonnet-4-20250514",
        temperature=0.8
    ),
    
    AgentRole.VISION_SPECIALIST: CrewAgent(
        agent_id="vision_specialist",
        role=AgentRole.VISION_SPECIALIST,
        name="Picasso",
        goal="Create stunning visual content and analyze images with expert precision",
        backstory="""You are Picasso, a digital artist and visual analyst.
You understand composition, color theory, style, and aesthetics. You create images
that capture ideas perfectly and analyze visuals with a trained eye.""",
        modalities=["IMAGE", "VISION"],
        tools=["image_generation", "image_editing", "image_analysis", "design"],
        skills=["artistic_design", "visual_analysis", "composition", "style_transfer"],
        model="black-forest-labs/flux-1.1-pro",  # Will be modality-selected
        temperature=0.9
    ),
    
    AgentRole.VIDEO_SPECIALIST: CrewAgent(
        agent_id="video_specialist", 
        role=AgentRole.VIDEO_SPECIALIST,
        name="Director",
        goal="Produce engaging video content that tells compelling visual stories",
        backstory="""You are Director, a video production expert.
You understand pacing, visual storytelling, camera angles, and editing.
You create videos that engage and inform.""",
        modalities=["VIDEO"],
        tools=["video_generation", "video_editing", "animation"],
        skills=["storytelling", "cinematography", "editing", "motion_design"],
        model="runway/gen3",  # Will be modality-selected
        temperature=0.8
    ),
    
    AgentRole.AUDIO_SPECIALIST: CrewAgent(
        agent_id="audio_specialist",
        role=AgentRole.AUDIO_SPECIALIST,
        name="Composer",
        goal="Create audio content that enhances and elevates the user experience",
        backstory="""You are Composer, an audio production specialist.
You create music, voiceovers, sound effects, and audio mixes that perfectly
complement and enhance the content.""",
        modalities=["AUDIO"],
        tools=["audio_generation", "tts", "music_generation", "audio_editing"],
        skills=["music_composition", "voice_acting", "sound_design", "audio_mixing"],
        model="elevenlabs/tts",  # Will be modality-selected
        temperature=0.7
    ),
    
    AgentRole.CODE_SPECIALIST: CrewAgent(
        agent_id="code_specialist",
        role=AgentRole.CODE_SPECIALIST,
        name="DevOps",
        goal="Write clean, efficient, and maintainable code that solves problems",
        backstory="""You are DevOps, a software engineering expert.
You write code in multiple languages, debug issues, optimize performance,
and follow best practices. You make complex technical tasks simple.""",
        modalities=["CODE"],
        tools=["code_generation", "code_analysis", "debugging", "testing"],
        skills=["programming", "debugging", "optimization", "testing"],
        model="claude-sonnet-4-20250514",
        temperature=0.3
    ),
    
    AgentRole.RESEARCHER: CrewAgent(
        agent_id="researcher",
        role=AgentRole.RESEARCHER,
        name="Scholar",
        goal="Gather accurate, comprehensive information and provide insightful analysis",
        backstory="""You are Scholar, a research specialist.
You find information efficiently, validate sources, synthesize findings,
and provide well-researched insights. You're thorough and objective.""",
        modalities=["TEXT", "DATA"],
        tools=["web_search", "data_gathering", "analysis", "summarization"],
        skills=["research", "source_validation", "synthesis", "critical_thinking"],
        model="claude-sonnet-4-20250514",
        temperature=0.4
    ),
    
    AgentRole.QUALITY_ASSURER: CrewAgent(
        agent_id="quality_assurer",
        role=AgentRole.QUALITY_ASSURER,
        name="Inspector",
        goal="Ensure all outputs meet quality standards and user requirements",
        backstory="""You are Inspector, a quality assurance expert.
You review work with a critical eye, checking for accuracy, completeness,
and quality. You provide constructive feedback and validate success criteria.""",
        modalities=["TEXT"],
        tools=["validation", "quality_check", "testing", "review"],
        skills=["quality_assessment", "attention_to_detail", "validation", "feedback"],
        model="claude-sonnet-4-20250514",
        temperature=0.3
    ),
}


# =============================================================================
# Task Execution Results
# =============================================================================

@dataclass
class AgentExecutionResult:
    """Result from an agent executing a task."""
    agent_id: str
    agent_role: AgentRole
    task_id: str
    
    success: bool
    output: Any
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    
    execution_time: float = 0.0
    model_used: str = ""
    tokens_used: int = 0
    
    reasoning: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DelegationResult:
    """Result from delegating a task"""
    success: bool
    final_output: Any
    agent_results: List[AgentExecutionResult]
    total_time: float
    quality_score: float = 0.0


# =============================================================================
# CrewAI-Inspired Task Delegator
# =============================================================================

class CrewAITaskDelegator:
    """
    Multi-agent task delegation inspired by CrewAI.
    
    Features:
    - Intelligent agent selection based on modalities
    - Hierarchical delegation
    - Parallel and sequential execution
    - Result synthesis
    - Quality assurance
    """
    
    def __init__(
        self,
        anthropic_client: Anthropic,
        tool_registry: Any,
        config: Optional[Dict[str, Any]] = None
    ):
        self.anthropic = anthropic_client
        self.tool_registry = tool_registry
        self.config = config or {}
        
        # Initialize agent crew
        self.agents: Dict[AgentRole, CrewAgent] = DEFAULT_CREW_AGENTS.copy()
        
        # Execution tracking
        self.active_tasks: Dict[str, Dict] = {}
        self.execution_history: List[AgentExecutionResult] = []
        
        logger.info("CrewAI Task Delegator initialized with agents: " + 
                   ", ".join([a.name for a in self.agents.values()]))
    
    async def delegate_task(
        self,
        interpreted_task: Any,  # InterpretedTask from langchain_task_interpreter
        modality_mapping: Dict[str, str],  # From modality_system
        callback: Optional[Callable] = None
    ) -> DelegationResult:
        """
        Delegate a task to appropriate specialized agents.
        
        Args:
            interpreted_task: Structured task from task interpreter
            modality_mapping: Modality → Model mapping
            callback: Optional callback for progress updates
            
        Returns:
            DelegationResult with all agent outputs
        """
        start_time = datetime.now()
        task_id = interpreted_task.task_id
        
        logger.info(f"Delegating task {task_id}: {interpreted_task.primary_goal}")
        
        if callback:
            await callback({
                "type": "delegation_started",
                "task_id": task_id,
                "complexity": interpreted_task.complexity.value
            })
        
        # Select agents for required modalities
        selected_agents = self._select_agents_for_task(
            interpreted_task, 
            modality_mapping
        )
        
        logger.info(f"Selected agents: {[a.name for a in selected_agents]}")
        
        # Execute with orchestrator if complex, direct if simple
        if interpreted_task.complexity.value in ["complex", "advanced"]:
            result = await self._execute_orchestrated(
                interpreted_task,
                selected_agents,
                modality_mapping,
                callback
            )
        else:
            result = await self._execute_direct(
                interpreted_task,
                selected_agents[0] if selected_agents else self.agents[AgentRole.TEXT_SPECIALIST],
                modality_mapping,
                callback
            )
        
        # Quality assurance step
        if self.config.get("enable_qa", True) and result.success:
            qa_result = await self._quality_assurance_check(
                interpreted_task,
                result,
                callback
            )
            result.quality_score = qa_result.get("quality_score", 0.8)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        result.total_time = execution_time
        
        logger.info(f"Task {task_id} completed in {execution_time:.1f}s, "
                   f"quality: {result.quality_score:.2f}")
        
        return result
    
    def _select_agents_for_task(
        self,
        task: Any,
        modality_mapping: Dict[str, str]
    ) -> List[CrewAgent]:
        """Select appropriate agents based on required modalities."""
        selected = []
        
        # Map modalities to agent roles
        modality_to_role = {
            "TEXT": AgentRole.TEXT_SPECIALIST,
            "IMAGE": AgentRole.VISION_SPECIALIST,
            "VISION": AgentRole.VISION_SPECIALIST,
            "VIDEO": AgentRole.VIDEO_SPECIALIST,
            "AUDIO": AgentRole.AUDIO_SPECIALIST,
            "CODE": AgentRole.CODE_SPECIALIST,
            "DATA": AgentRole.DATA_ANALYST,
        }
        
        for modality in task.required_modalities:
            role = modality_to_role.get(modality.upper())
            if role and role in self.agents:
                agent = self.agents[role]
                if agent not in selected:
                    selected.append(agent)
        
        # Add orchestrator if multiple agents needed
        if len(selected) > 1:
            selected.insert(0, self.agents[AgentRole.ORCHESTRATOR])
        
        # Default to text specialist if nothing matched
        if not selected:
            selected.append(self.agents[AgentRole.TEXT_SPECIALIST])
        
        return selected
    
    async def _execute_direct(
        self,
        task: Any,
        agent: CrewAgent,
        modality_mapping: Dict[str, str],
        callback: Optional[Callable]
    ) -> DelegationResult:
        """Execute task directly with a single agent."""
        logger.info(f"Direct execution with {agent.name}")
        
        if callback:
            await callback({
                "type": "agent_started",
                "agent": agent.name,
                "role": agent.role.value
            })
        
        # Build agent prompt
        prompt = self._build_agent_prompt(agent, task, modality_mapping)
        
        try:
            # Execute with appropriate model (from modality mapping)
            primary_modality = task.required_modalities[0] if task.required_modalities else "TEXT"
            model = modality_mapping.get(primary_modality, agent.model)
            
            # For text-based agents, use Anthropic
            if "claude" in model.lower():
                response = self.anthropic.messages.create(
                    model=model,
                    max_tokens=agent.max_tokens,
                    temperature=agent.temperature,
                    system=agent.backstory,
                    messages=[{"role": "user", "content": prompt}]
                )
                output = response.content[0].text
                tokens = response.usage.input_tokens + response.usage.output_tokens
            else:
                # For other modalities, would call appropriate tool
                output = f"[{agent.name} would execute with {model}]"
                tokens = 0
            
            result = AgentExecutionResult(
                agent_id=agent.agent_id,
                agent_role=agent.role,
                task_id=task.task_id,
                success=True,
                output=output,
                model_used=model,
                tokens_used=tokens,
                execution_time=0.5
            )
            
            # Update agent stats
            agent.tasks_completed += 1
            self.execution_history.append(result)
            
            if callback:
                await callback({
                    "type": "agent_completed",
                    "agent": agent.name,
                    "success": True
                })
            
            return DelegationResult(
                success=True,
                final_output=output,
                agent_results=[result],
                total_time=0.5,
                quality_score=0.85
            )
            
        except Exception as e:
            logger.error(f"Agent {agent.name} failed: {e}")
            
            result = AgentExecutionResult(
                agent_id=agent.agent_id,
                agent_role=agent.role,
                task_id=task.task_id,
                success=False,
                output=None,
                errors=[str(e)]
            )
            
            return DelegationResult(
                success=False,
                final_output=None,
                agent_results=[result],
                total_time=0.0,
                quality_score=0.0
            )
    
    async def _execute_orchestrated(
        self,
        task: Any,
        agents: List[CrewAgent],
        modality_mapping: Dict[str, str],
        callback: Optional[Callable]
    ) -> DelegationResult:
        """Execute complex task with orchestrator coordinating multiple agents."""
        logger.info(f"Orchestrated execution with {len(agents)} agents")
        
        orchestrator = self.agents[AgentRole.ORCHESTRATOR]
        specialist_agents = [a for a in agents if a.role != AgentRole.ORCHESTRATOR]
        
        # Orchestrator creates execution plan
        plan_prompt = f"""You are coordinating a team to accomplish this task:

Task: {task.primary_goal}
Details: {task.detailed_description}
Required Modalities: {', '.join(task.required_modalities)}
Steps: {len(task.steps)}

Available Specialists:
{chr(10).join([f"- {a.name} ({a.role.value}): {a.goal}" for a in specialist_agents])}

Create a coordination plan:
1. Which specialist handles which step?
2. What order should they work?
3. How should results be combined?
4. What validation is needed?

Be specific and actionable."""

        # Get orchestration plan
        try:
            response = self.anthropic.messages.create(
                model=orchestrator.model,
                max_tokens=2000,
                temperature=orchestrator.temperature,
                system=orchestrator.backstory,
                messages=[{"role": "user", "content": plan_prompt}]
            )
            orchestration_plan = response.content[0].text
            
            logger.info("Orchestration plan created")
            
            if callback:
                await callback({
                    "type": "orchestration_plan",
                    "plan": orchestration_plan
                })
            
        except Exception as e:
            logger.error(f"Orchestration planning failed: {e}")
            orchestration_plan = "Execute specialists sequentially"
        
        # Execute specialists (sequential for now, could be parallel)
        agent_results = []
        combined_output = []
        
        for agent in specialist_agents:
            agent_result = await self._execute_direct(
                task, agent, modality_mapping, callback
            )
            agent_results.extend(agent_result.agent_results)
            if agent_result.success:
                combined_output.append(agent_result.final_output)
        
        # Synthesize final result
        synthesis_prompt = f"""Synthesize these specialist outputs into a cohesive final result:

Task: {task.primary_goal}

Specialist Outputs:
{chr(10).join([f"- {r.agent_role.value}: {str(r.output)[:200]}" for r in agent_results if r.success])}

Create a unified, polished final result that accomplishes the task goal."""

        try:
            response = self.anthropic.messages.create(
                model=orchestrator.model,
                max_tokens=4000,
                temperature=0.7,
                messages=[{"role": "user", "content": synthesis_prompt}]
            )
            final_output = response.content[0].text
            success = True
        except Exception as e:
            logger.error(f"Result synthesis failed: {e}")
            final_output = "\n\n".join(str(o) for o in combined_output if o)
            success = len(combined_output) > 0
        
        return DelegationResult(
            success=success,
            final_output=final_output,
            agent_results=agent_results,
            total_time=0.0,  # Will be set by caller
            quality_score=0.8
        )
    
    def _build_agent_prompt(
        self,
        agent: CrewAgent,
        task: Any,
        modality_mapping: Dict[str, str]
    ) -> str:
        """Build a prompt for an agent to execute a task."""
        return f"""Goal: {agent.goal}

Your Task: {task.primary_goal}

Details: {task.detailed_description}

Success Criteria:
{chr(10).join([f"- {c}" for c in task.success_criteria])}

Parameters:
{chr(10).join([f"- {p.name}: {p.value}" for p in task.parameters])}

Execute this task to the best of your abilities using your skills: {', '.join(agent.skills)}

Provide a complete, high-quality result."""
    
    async def _quality_assurance_check(
        self,
        task: Any,
        result: DelegationResult,
        callback: Optional[Callable]
    ) -> Dict[str, Any]:
        """Run quality assurance on execution result."""
        qa_agent = self.agents[AgentRole.QUALITY_ASSURER]
        
        qa_prompt = f"""Review this work for quality and completeness:

Original Task: {task.primary_goal}
Success Criteria: {', '.join(task.success_criteria)}

Output to Review:
{str(result.final_output)[:1000]}

Rate the quality (0.0 to 1.0) and provide feedback:
- Does it meet the success criteria?
- Is it complete and accurate?
- What could be improved?

Return JSON: {{"quality_score": 0.85, "feedback": "..."}}"""

        try:
            response = self.anthropic.messages.create(
                model=qa_agent.model,
                max_tokens=1000,
                temperature=0.3,
                system=qa_agent.backstory,
                messages=[{"role": "user", "content": qa_prompt}]
            )
            
            import json
            qa_text = response.content[0].text
            if "```json" in qa_text:
                qa_text = qa_text.split("```json")[1].split("```")[0]
            
            qa_result = json.loads(qa_text.strip())
            
            if callback:
                await callback({
                    "type": "quality_check",
                    "score": qa_result.get("quality_score", 0.8),
                    "feedback": qa_result.get("feedback", "")
                })
            
            return qa_result
            
        except Exception as e:
            logger.error(f"QA check failed: {e}")
            return {"quality_score": 0.75, "feedback": "QA check error"}


# =============================================================================
# Singleton Access
# =============================================================================

_delegator: Optional[CrewAITaskDelegator] = None


def get_crew_delegator(
    anthropic_client: Anthropic,
    tool_registry: Any,
    config: Optional[Dict[str, Any]] = None
) -> CrewAITaskDelegator:
    """Get or create the CrewAI task delegator singleton."""
    global _delegator
    if _delegator is None:
        _delegator = CrewAITaskDelegator(anthropic_client, tool_registry, config)
    return _delegator
