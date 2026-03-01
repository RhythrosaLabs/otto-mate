"""
LangChain-Based Task Interpretation - Otto Universal
=====================================================

Strict prompt engineering and task parsing using LangChain patterns.

This module uses structured prompting and chain-of-thought to:
1. Parse user intent precisely
2. Extract task parameters and constraints
3. Identify dependencies and sequencing
4. Create executable task plans

Key Features:
- Structured prompt templates (LangChain pattern)
- Chain-of-thought reasoning
- Output parsing and validation
- Task decomposition
- Context-aware interpretation
"""

import logging
import json
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from anthropic import Anthropic

# Try to import LangChain if available
try:
    from langchain.prompts import PromptTemplate, ChatPromptTemplate
    from langchain.output_parsers import PydanticOutputParser, StructuredOutputParser
    from langchain_anthropic import ChatAnthropic
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("LangChain not available, using fallback interpretation")

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """Types of tasks Otto can handle."""
    CREATE = "create"  # Create new content
    ANALYZE = "analyze"  # Analyze existing content  
    TRANSFORM = "transform"  # Transform content
    WORKFLOW = "workflow"  # Multi-step workflow
    QUERY = "query"  # Answer questions
    AUTOMATE = "automate"  # Set up automation
    INTEGRATE = "integrate"  # Connect systems
    RESEARCH = "research"  # Gather information
    DESIGN = "design"  # Create designs
    CODE = "code"  # Write code


class TaskComplexity(str, Enum):
    """Task complexity levels."""
    TRIVIAL = "trivial"  # Single step, < 30 sec
    SIMPLE = "simple"  # Few steps, < 5 min
    MODERATE = "moderate"  # Multiple steps, < 30 min
    COMPLEX = "complex"  # Many steps, < 2 hours
    ADVANCED = "advanced"  # Very complex, > 2 hours


@dataclass
class TaskParameter:
    """A parameter for task execution."""
    name: str
    value: Any
    type: str  # text, number, boolean, array, object
    required: bool = True
    description: str = ""
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskDependency:
    """A dependency between tasks."""
    depends_on: str  # Task ID or step
    dependency_type: str  # sequential, parallel, conditional
    condition: Optional[str] = None  # For conditional dependencies


@dataclass
class InterpretedTask:
    """Fully interpreted and structured task."""
    task_id: str
    task_type: TaskType
    complexity: TaskComplexity
    
    # Core task info
    primary_goal: str
    detailed_description: str
    success_criteria: List[str]
    
    # Modality requirements (from modality system)
    required_modalities: List[str]
    
    # Parameters and constraints
    parameters: List[TaskParameter]
    constraints: Dict[str, Any]
    
    # Execution plan
    steps: List[Dict[str, Any]]
    estimated_duration_minutes: int
    dependencies: List[TaskDependency]
    
    # Context and metadata
    context: Dict[str, Any]
    priority: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    
    # Reasoning trail
    reasoning_chain: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "complexity": self.complexity.value,
            "primary_goal": self.primary_goal,
            "detailed_description": self.detailed_description,
            "success_criteria": self.success_criteria,
            "required_modalities": self.required_modalities,
            "parameters": [
                {
                    "name": p.name,
                    "value": p.value,
                    "type": p.type,
                    "required": p.required,
                    "description": p.description
                } for p in self.parameters
            ],
            "steps": self.steps,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "reasoning_chain": self.reasoning_chain
        }


# =============================================================================
# Prompt Templates (LangChain-Style)
# =============================================================================

TASK_INTERPRETATION_PROMPT = """You are Otto's Task Interpretation Engine. Your job is to analyze user requests with extreme precision and structure them for execution.

User Request: {user_request}

Additional Context: {context}

Follow this chain of thought:

1. IDENTIFY THE CORE TASK
   - What is the user fundamentally trying to accomplish?
   - What is the PRIMARY goal?
   - What would success look like?

2. DETERMINE TASK TYPE
   - CREATE: Making new content/artifacts
   - ANALYZE: Understanding existing content
   - TRANSFORM: Modifying existing content
   - WORKFLOW: Multi-step business process
   - QUERY: Answering questions
   - AUTOMATE: Setting up recurring processes
   - DESIGN: Creating designs/mockups
   - CODE: Programming tasks
   - RESEARCH: Information gathering

3. ASSESS COMPLEXITY
   - TRIVIAL: One simple action
   - SIMPLE: 2-3 straightforward steps
   - MODERATE: Multiple steps with some complexity
   - COMPLEX: Many steps, requires planning
   - ADVANCED: Very complex, multi-agent coordination

4. IDENTIFY REQUIRED MODALITIES
   - What TYPES of content need to be created or processed?
   - TEXT, IMAGE, VIDEO, AUDIO, CODE, VISION, 3D, DATA, DOCUMENT
   - List ALL modalities needed

5. EXTRACT PARAMETERS
   - What specific values/inputs are provided?
   - What information is missing that we need?
   - What constraints are mentioned?

6. BREAK INTO STEPS
   - What is the logical sequence of actions?
   - What dependencies exist between steps?
   - Can any steps run in parallel?

7. DEFINE SUCCESS CRITERIA
   - How will we know the task is complete?
   - What quality standards apply?
   - What validation is needed?

Return your analysis as JSON:
{{
  "task_type": "CREATE|ANALYZE|TRANSFORM|WORKFLOW|etc",
  "complexity": "TRIVIAL|SIMPLE|MODERATE|COMPLEX|ADVANCED",
  "primary_goal": "Clear statement of what user wants to achieve",
  "detailed_description": "Detailed explanation of the task",
  "success_criteria": ["criterion 1", "criterion 2", ...],
  "required_modalities": ["TEXT", "IMAGE", etc],
  "parameters": [
    {{
      "name": "param_name",
      "value": "extracted_value",
      "type": "text|number|boolean|array|object",
      "required": true,
      "description": "what this parameter is for"
    }}
  ],
  "steps": [
    {{
      "step_number": 1,
      "action": "What to do",
      "modality": "Which modality",
      "depends_on": [],
      "estimated_minutes": 5
    }}
  ],
  "estimated_duration_minutes": 30,
  "reasoning": ["thought 1", "thought 2", ...]
}}

CRITICAL: Return ONLY valid JSON, no other text."""

TASK_VALIDATION_PROMPT = """Validate this interpreted task for completeness and correctness.

Interpreted Task:
{interpreted_task}

Check for:
1. Are all required modalities identified?
2. Are parameters complete and correct?
3. Are steps logically sequenced?
4. Are dependencies properly captured?
5. Is the complexity assessment reasonable?
6. Are success criteria measurable?

If valid, return: {{"valid": true, "confidence": 0.95}}
If issues found, return: {{"valid": false, "issues": ["issue 1", ...], "suggestions": ["suggestion 1", ...]}}

Return JSON only."""


# =============================================================================
# LangChain Task Interpreter
# =============================================================================

class LangChainTaskInterpreter:
    """
    Interprets tasks using LangChain-style prompt engineering.
    
    Provides structured, validated task interpretation with:
    - Chain-of-thought reasoning
    - Structured output parsing
    - Parameter extraction
    - Step decomposition
    """
    
    def __init__(self, anthropic_client: Anthropic, use_langchain: bool = True):
        self.anthropic = anthropic_client
        self.use_langchain = use_langchain and LANGCHAIN_AVAILABLE
        
        if self.use_langchain:
            self.llm = ChatAnthropic(
                model="claude-sonnet-4-20250514",
                temperature=0.3,
                timeout=120
            )
            logger.info("LangChain task interpreter initialized")
        else:
            logger.info("Using fallback task interpreter (no LangChain)")
    
    async def interpret_task(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> InterpretedTask:
        """
        Interpret a user request into a structured, executable task.
        
        Args:
            user_request: Raw user input
            context: Additional context (session, user prefs, etc.)
            
        Returns:
            Fully interpreted and structured task
        """
        import uuid
        
        context = context or {}
        task_id = str(uuid.uuid4())[:8]
        
        logger.info(f"Interpreting task: {user_request[:100]}...")
        
        if self.use_langchain:
            result = await self._interpret_with_langchain(user_request, context, task_id)
        else:
            result = await self._interpret_fallback(user_request, context, task_id)
        
        # Validate the interpretation
        is_valid = await self._validate_interpretation(result)
        if not is_valid:
            logger.warning("Task interpretation validation failed, reinterpreting...")
            # Could retry with more specific prompting here
        
        logger.info(f"Task interpreted: {result.task_type.value} ({result.complexity.value})")
        return result
    
    async def _interpret_with_langchain(
        self,
        user_request: str,
        context: Dict[str, Any],
        task_id: str
    ) -> InterpretedTask:
        """Interpret using LangChain constructs."""
        try:
            from langchain.prompts import ChatPromptTemplate
            
            # Create prompt
            prompt = ChatPromptTemplate.from_template(TASK_INTERPRETATION_PROMPT)
            
            # Format with inputs
            formatted_prompt = prompt.format(
                user_request=user_request,
                context=json.dumps(context, indent=2, default=str)[:500]
            )
            
            # Get response
            response = self.llm.invoke(formatted_prompt)
            
            # Parse JSON response
            response_text = response.content if hasattr(response, 'content') else str(response)
            return self._parse_interpretation_response(response_text, task_id)
            
        except Exception as e:
            logger.error(f"LangChain interpretation failed: {e}")
            return await self._interpret_fallback(user_request, context, task_id)
    
    async def _interpret_fallback(
        self,
        user_request: str,
        context: Dict[str, Any],
        task_id: str
    ) -> InterpretedTask:
        """Fallback interpretation without LangChain."""
        try:
            # Use direct Anthropic API
            prompt = TASK_INTERPRETATION_PROMPT.format(
                user_request=user_request,
                context=json.dumps(context, indent=2, default=str)[:500]
            )
            
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            return self._parse_interpretation_response(response_text, task_id)
            
        except Exception as e:
            logger.error(f"Task interpretation failed: {e}")
            # Return minimal fallback task
            return InterpretedTask(
                task_id=task_id,
                task_type=TaskType.QUERY,
                complexity=TaskComplexity.SIMPLE,
                primary_goal=user_request,
                detailed_description=user_request,
                success_criteria=["Provide helpful response"],
                required_modalities=["TEXT"],
                parameters=[],
                constraints={},
                steps=[{
                    "step_number": 1,
                    "action": "Process request",
                    "modality": "TEXT",
                    "estimated_minutes": 1
                }],
                estimated_duration_minutes=1,
                dependencies=[],
                context=context,
                reasoning_chain=["Fallback interpretation due to error"]
            )
    
    def _parse_interpretation_response(
        self,
        response_text: str,
        task_id: str
    ) -> InterpretedTask:
        """Parse AI response into InterpretedTask."""
        try:
            # Extract JSON from response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            data = json.loads(response_text.strip())
            
            # Parse parameters
            parameters = []
            for p in data.get("parameters", []):
                parameters.append(TaskParameter(
                    name=p["name"],
                    value=p.get("value"),
                    type=p.get("type", "text"),
                    required=p.get("required", True),
                    description=p.get("description", "")
                ))
            
            # Parse dependencies (if any)
            dependencies = []
            for step in data.get("steps", []):
                for dep in step.get("depends_on", []):
                    dependencies.append(TaskDependency(
                        depends_on=str(dep),
                        dependency_type="sequential"
                    ))
            
            return InterpretedTask(
                task_id=task_id,
                task_type=TaskType(data["task_type"].lower()),
                complexity=TaskComplexity(data["complexity"].lower()),
                primary_goal=data["primary_goal"],
                detailed_description=data["detailed_description"],
                success_criteria=data.get("success_criteria", []),
                required_modalities=data.get("required_modalities", ["TEXT"]),
                parameters=parameters,
                constraints=data.get("constraints", {}),
                steps=data.get("steps", []),
                estimated_duration_minutes=data.get("estimated_duration_minutes", 5),
                dependencies=dependencies,
                context={},
                reasoning_chain=data.get("reasoning", [])
            )
            
        except Exception as e:
            logger.error(f"Failed to parse interpretation response: {e}")
            raise
    
    async def _validate_interpretation(self, task: InterpretedTask) -> bool:
        """Validate that the interpretation is complete and correct."""
        try:
            # Basic validation
            if not task.primary_goal:
                return False
            if not task.required_modalities:
                return False
            if not task.steps:
                return False
            
            # Could add AI-powered validation here with TASK_VALIDATION_PROMPT
            
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False


# =============================================================================
# Singleton Access
# =============================================================================

_interpreter: Optional[LangChainTaskInterpreter] = None


def get_task_interpreter(anthropic_client: Anthropic) -> LangChainTaskInterpreter:
    """Get or create the task interpreter singleton."""
    global _interpreter
    if _interpreter is None:
        _interpreter = LangChainTaskInterpreter(anthropic_client)
    return _interpreter
