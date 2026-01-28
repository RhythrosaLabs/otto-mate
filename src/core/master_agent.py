"""
Otto Universal - Master Agent Architecture
==========================================

A sophisticated multi-agent system with:
- Master Orchestrator that coordinates specialized sub-agents
- User-customizable agents with persistent configurations
- Hierarchical task delegation and result synthesis
- Self-healing and adaptive capabilities
"""

import logging
import json
import uuid
import asyncio
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
from pathlib import Path
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Specialized agent roles."""
    MASTER = "master"
    PLANNER = "planner"
    RESEARCHER = "researcher"
    DESIGNER = "designer"
    WRITER = "writer"
    DEVELOPER = "developer"
    ANALYST = "analyst"
    MARKETER = "marketer"
    EXECUTOR = "executor"
    CUSTOM = "custom"


class AgentCapability(Enum):
    """Capabilities that agents can have."""
    IMAGE_GENERATION = "image_generation"
    VIDEO_GENERATION = "video_generation"
    AUDIO_GENERATION = "audio_generation"
    TEXT_GENERATION = "text_generation"
    CODE_EXECUTION = "code_execution"
    WEB_RESEARCH = "web_research"
    DATA_ANALYSIS = "data_analysis"
    FILE_MANAGEMENT = "file_management"
    API_INTEGRATION = "api_integration"
    BROWSER_AUTOMATION = "browser_automation"
    CONTENT_WRITING = "content_writing"
    MARKETING = "marketing"
    PRODUCT_DESIGN = "product_design"


@dataclass
class AgentConfig:
    """Configuration for a sub-agent."""
    id: str
    name: str
    role: AgentRole
    description: str
    capabilities: List[AgentCapability]
    system_prompt: str
    model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.7
    max_tokens: int = 4096
    tools: List[str] = field(default_factory=list)
    color: str = "#6366f1"  # Default indigo
    icon: str = "🤖"
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'role': self.role.value,
            'capabilities': [c.value for c in self.capabilities]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AgentConfig':
        data['role'] = AgentRole(data['role'])
        data['capabilities'] = [AgentCapability(c) for c in data['capabilities']]
        return cls(**data)


class SubAgent:
    """
    A specialized sub-agent that handles specific types of tasks.
    """
    
    def __init__(self, config: AgentConfig, anthropic_client: Anthropic, tool_registry: Any):
        self.config = config
        self.anthropic = anthropic_client
        self.tool_registry = tool_registry
        self.execution_history: List[Dict] = []
        
    async def process(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task assigned by the master agent."""
        try:
            # Build prompt with agent's personality and capabilities
            prompt = self._build_prompt(task, context)
            
            # Execute with AI
            response = self.anthropic.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=self.config.system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = {
                "agent_id": self.config.id,
                "agent_name": self.config.name,
                "task": task,
                "response": response.content[0].text,
                "success": True,
                "timestamp": datetime.now().isoformat()
            }
            
            self.execution_history.append(result)
            return result
            
        except Exception as e:
            logger.error(f"Agent {self.config.name} failed: {e}")
            return {
                "agent_id": self.config.id,
                "agent_name": self.config.name,
                "task": task,
                "error": str(e),
                "success": False,
                "timestamp": datetime.now().isoformat()
            }
    
    def _build_prompt(self, task: str, context: Dict) -> str:
        """Build a task-specific prompt."""
        context_str = json.dumps(context, indent=2, default=str)[:2000]
        
        return f"""Task assigned to you: {task}

Context:
{context_str}

Your capabilities: {', '.join([c.value for c in self.config.capabilities])}

Execute this task to the best of your ability. Be thorough and provide actionable results."""


class MasterOrchestrator:
    """
    The Master Agent that coordinates all sub-agents.
    
    Responsibilities:
    - Understand user intent
    - Delegate to appropriate sub-agents
    - Synthesize results
    - Handle failures gracefully
    - Learn from interactions
    """
    
    # Default sub-agent configurations
    DEFAULT_AGENTS = [
        AgentConfig(
            id="planner",
            name="Strategic Planner",
            role=AgentRole.PLANNER,
            description="Analyzes requests and creates detailed execution plans",
            capabilities=[AgentCapability.TEXT_GENERATION, AgentCapability.DATA_ANALYSIS],
            system_prompt="""You are a strategic planning agent. Your job is to:
1. Analyze user requests deeply
2. Break complex tasks into actionable steps
3. Identify required resources and tools
4. Estimate time and complexity
5. Plan for potential failures

Always return structured, actionable plans.""",
            color="#8b5cf6",
            icon="🎯"
        ),
        AgentConfig(
            id="researcher",
            name="Research Specialist",
            role=AgentRole.RESEARCHER,
            description="Gathers information, analyzes trends, and provides insights",
            capabilities=[AgentCapability.WEB_RESEARCH, AgentCapability.DATA_ANALYSIS, AgentCapability.TEXT_GENERATION],
            system_prompt="""You are a research specialist agent. Your job is to:
1. Search for relevant information
2. Analyze data and trends
3. Synthesize findings into actionable insights
4. Cite sources when possible
5. Identify gaps in available information

Be thorough and objective in your research.""",
            color="#06b6d4",
            icon="🔍"
        ),
        AgentConfig(
            id="designer",
            name="Creative Designer",
            role=AgentRole.DESIGNER,
            description="Creates visual content, designs, and creative assets",
            capabilities=[AgentCapability.IMAGE_GENERATION, AgentCapability.VIDEO_GENERATION, AgentCapability.PRODUCT_DESIGN],
            system_prompt="""You are a creative design agent. Your job is to:
1. Understand design requirements
2. Generate creative concepts
3. Create or specify visual assets
4. Ensure brand consistency
5. Optimize for target platforms

Focus on aesthetics, usability, and impact.""",
            color="#f43f5e",
            icon="🎨"
        ),
        AgentConfig(
            id="writer",
            name="Content Writer",
            role=AgentRole.WRITER,
            description="Creates written content, copy, and documentation",
            capabilities=[AgentCapability.CONTENT_WRITING, AgentCapability.TEXT_GENERATION],
            system_prompt="""You are a content writing agent. Your job is to:
1. Write compelling copy
2. Adapt tone to target audience
3. Optimize for engagement
4. Ensure clarity and accuracy
5. Follow brand guidelines

Write with purpose and impact.""",
            color="#f97316",
            icon="✍️"
        ),
        AgentConfig(
            id="developer",
            name="Code Developer",
            role=AgentRole.DEVELOPER,
            description="Writes code, builds solutions, and solves technical problems",
            capabilities=[AgentCapability.CODE_EXECUTION, AgentCapability.TEXT_GENERATION, AgentCapability.DATA_ANALYSIS],
            system_prompt="""You are a software development agent. Your job is to:
1. Write clean, efficient code
2. Solve technical problems
3. Debug and fix issues
4. Optimize performance
5. Follow best practices

Write production-quality code with proper error handling.""",
            color="#22c55e",
            icon="💻"
        ),
        AgentConfig(
            id="analyst",
            name="Data Analyst",
            role=AgentRole.ANALYST,
            description="Analyzes data, generates insights, and creates reports",
            capabilities=[AgentCapability.DATA_ANALYSIS, AgentCapability.TEXT_GENERATION],
            system_prompt="""You are a data analysis agent. Your job is to:
1. Process and analyze data
2. Identify patterns and trends
3. Generate actionable insights
4. Create clear visualizations
5. Write comprehensive reports

Be precise and data-driven.""",
            color="#a855f7",
            icon="📊"
        ),
        AgentConfig(
            id="marketer",
            name="Marketing Expert",
            role=AgentRole.MARKETER,
            description="Creates marketing strategies, campaigns, and promotional content",
            capabilities=[AgentCapability.MARKETING, AgentCapability.CONTENT_WRITING, AgentCapability.DATA_ANALYSIS],
            system_prompt="""You are a marketing expert agent. Your job is to:
1. Develop marketing strategies
2. Create compelling campaigns
3. Optimize for conversions
4. Analyze market trends
5. Target the right audiences

Focus on ROI and engagement.""",
            color="#ec4899",
            icon="📢"
        ),
        AgentConfig(
            id="executor",
            name="Task Executor",
            role=AgentRole.EXECUTOR,
            description="Executes tools, APIs, and automated workflows",
            capabilities=[AgentCapability.API_INTEGRATION, AgentCapability.FILE_MANAGEMENT, AgentCapability.BROWSER_AUTOMATION],
            system_prompt="""You are a task execution agent. Your job is to:
1. Execute tools and APIs correctly
2. Handle errors gracefully
3. Verify results
4. Report status accurately
5. Clean up after execution

Be reliable and thorough.""",
            color="#64748b",
            icon="⚡"
        ),
    ]
    
    def __init__(
        self,
        anthropic_client: Anthropic,
        tool_registry: Any,
        agents_dir: str = "./data/agents"
    ):
        self.anthropic = anthropic_client
        self.tool_registry = tool_registry
        self.agents_dir = Path(agents_dir)
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize sub-agents
        self.sub_agents: Dict[str, SubAgent] = {}
        self._load_agents()
        
        # Master system prompt
        self.system_prompt = """You are Otto, the Master AI Orchestrator - an extraordinarily capable assistant.

YOUR ARCHITECTURE:
You coordinate a team of specialized sub-agents:
{agent_list}

YOUR CAPABILITIES:
1. UNDERSTAND user intent deeply, even when vague
2. DELEGATE tasks to the most appropriate sub-agents
3. SYNTHESIZE results from multiple agents
4. EXECUTE tools and APIs directly when needed
5. ADAPT plans when things don't work
6. LEARN from each interaction

DECISION FRAMEWORK:
- For planning tasks → Strategic Planner
- For research/info gathering → Research Specialist  
- For visual/design tasks → Creative Designer
- For writing/content → Content Writer
- For coding/technical → Code Developer
- For data/analytics → Data Analyst
- For marketing/promotion → Marketing Expert
- For tool execution → Task Executor

RESPONSE STYLE:
- Be concise but thorough
- Show progress and reasoning
- Provide actionable results
- Admit uncertainty when appropriate
- Suggest next steps proactively"""
    
    def _load_agents(self):
        """Load agents from config files and defaults."""
        # Load default agents first
        for config in self.DEFAULT_AGENTS:
            self.sub_agents[config.id] = SubAgent(config, self.anthropic, self.tool_registry)
        
        # Load custom agents from files
        for agent_file in self.agents_dir.glob("*.json"):
            try:
                with open(agent_file) as f:
                    data = json.load(f)
                config = AgentConfig.from_dict(data)
                self.sub_agents[config.id] = SubAgent(config, self.anthropic, self.tool_registry)
                logger.info(f"Loaded custom agent: {config.name}")
            except Exception as e:
                logger.error(f"Failed to load agent {agent_file}: {e}")
    
    def save_agent(self, config: AgentConfig) -> bool:
        """Save a custom agent configuration."""
        try:
            filepath = self.agents_dir / f"{config.id}.json"
            with open(filepath, 'w') as f:
                json.dump(config.to_dict(), f, indent=2)
            
            # Register the agent
            self.sub_agents[config.id] = SubAgent(config, self.anthropic, self.tool_registry)
            return True
        except Exception as e:
            logger.error(f"Failed to save agent: {e}")
            return False
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete a custom agent."""
        try:
            filepath = self.agents_dir / f"{agent_id}.json"
            if filepath.exists():
                filepath.unlink()
            if agent_id in self.sub_agents:
                del self.sub_agents[agent_id]
            return True
        except Exception as e:
            logger.error(f"Failed to delete agent: {e}")
            return False
    
    def get_agent_list(self) -> List[Dict]:
        """Get list of all agents."""
        return [
            {
                "id": agent.config.id,
                "name": agent.config.name,
                "role": agent.config.role.value,
                "description": agent.config.description,
                "icon": agent.config.icon,
                "color": agent.config.color,
                "is_active": agent.config.is_active,
                "is_default": agent.config.id in [a.id for a in self.DEFAULT_AGENTS]
            }
            for agent in self.sub_agents.values()
        ]
    
    async def delegate(
        self,
        task: str,
        agent_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Delegate a task to a specific sub-agent."""
        if agent_id not in self.sub_agents:
            return {"success": False, "error": f"Agent not found: {agent_id}"}
        
        agent = self.sub_agents[agent_id]
        return await agent.process(task, context)
    
    async def orchestrate(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Main orchestration method - analyzes request and coordinates agents.
        """
        # Build agent list for system prompt
        agent_list = "\n".join([
            f"- {a.config.icon} {a.config.name}: {a.config.description}"
            for a in self.sub_agents.values()
            if a.config.is_active
        ])
        
        system = self.system_prompt.format(agent_list=agent_list)
        
        # Get orchestration decision from Claude
        response = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            temperature=0.4,
            system=system,
            messages=[{
                "role": "user",
                "content": f"""User request: {message}

Context: {json.dumps(context, default=str)[:2000]}

Analyze this request and determine:
1. What is the user's ultimate goal?
2. Which sub-agents should be involved?
3. In what order should they work?
4. What should each agent do specifically?

Return a JSON plan:
{{
    "understanding": "Your interpretation of the request",
    "delegation_plan": [
        {{"agent_id": "...", "task": "Specific task for this agent", "depends_on": []}}
    ],
    "direct_response": "If no agents needed, your direct response",
    "requires_agents": true/false
}}"""
            }]
        )
        
        # Parse the orchestration plan
        try:
            import re
            text = response.content[0].text
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                plan = json.loads(match.group())
            else:
                plan = {"requires_agents": False, "direct_response": text}
        except:
            plan = {"requires_agents": False, "direct_response": response.content[0].text}
        
        # If no agents needed, return direct response
        if not plan.get("requires_agents", False):
            return {
                "response": plan.get("direct_response", response.content[0].text),
                "type": "direct",
                "understanding": plan.get("understanding", "")
            }
        
        # Execute delegation plan
        results = []
        for step in plan.get("delegation_plan", []):
            agent_id = step.get("agent_id")
            task = step.get("task")
            
            if agent_id and task:
                result = await self.delegate(task, agent_id, {
                    **context,
                    "previous_results": results,
                    "original_request": message
                })
                results.append(result)
        
        # Synthesize final response
        synthesis = await self._synthesize_results(message, results, plan)
        
        return {
            "response": synthesis,
            "type": "orchestrated",
            "understanding": plan.get("understanding", ""),
            "delegation_plan": plan.get("delegation_plan", []),
            "agent_results": results
        }
    
    async def _synthesize_results(
        self,
        original_request: str,
        results: List[Dict],
        plan: Dict
    ) -> str:
        """Synthesize results from multiple agents into a coherent response."""
        results_text = "\n\n".join([
            f"**{r.get('agent_name', 'Agent')}**:\n{r.get('response', r.get('error', 'No response'))}"
            for r in results
        ])
        
        response = self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": f"""Original request: {original_request}

Understanding: {plan.get('understanding', '')}

Results from agents:
{results_text}

Synthesize these results into a clear, actionable response for the user. 
- Highlight key findings
- Provide concrete next steps
- Note any issues or limitations
- Be concise but thorough"""
            }]
        )
        
        return response.content[0].text


# Export for use
__all__ = [
    'MasterOrchestrator',
    'SubAgent', 
    'AgentConfig',
    'AgentRole',
    'AgentCapability'
]
