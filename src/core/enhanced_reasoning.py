"""
Enhanced Reasoning System
=========================

Implements chain-of-thought reasoning, self-reflection, and 
multi-strategy problem solving for smarter AI responses.

Features:
- Chain of thought with explicit reasoning steps
- Self-critique and refinement
- Multi-attempt with best selection
- Confidence scoring
- Strategy switching based on problem type
- Learning from past solutions
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from anthropic import AsyncAnthropic
import json
import hashlib

logger = logging.getLogger(__name__)


class ReasoningStrategy(Enum):
    """Different reasoning approaches."""
    DIRECT = "direct"  # Simple direct answer
    CHAIN_OF_THOUGHT = "chain_of_thought"  # Step by step reasoning
    DECOMPOSITION = "decomposition"  # Break into sub-problems
    ANALOGICAL = "analogical"  # Use similar solved problems
    ADVERSARIAL = "adversarial"  # Generate and critique
    CONSENSUS = "consensus"  # Multiple attempts, vote on best


class ProblemType(Enum):
    """Types of problems for strategy selection."""
    FACTUAL = "factual"  # Lookup/recall
    ANALYTICAL = "analytical"  # Analysis/reasoning
    CREATIVE = "creative"  # Generation/creation
    PROCEDURAL = "procedural"  # Step-by-step execution
    DEBUGGING = "debugging"  # Finding/fixing issues
    OPTIMIZATION = "optimization"  # Improving existing


@dataclass
class ReasoningStep:
    """A single step in the reasoning chain."""
    step_number: int
    thought: str
    action: Optional[str] = None
    observation: Optional[str] = None
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ReasoningResult:
    """Result of enhanced reasoning."""
    answer: str
    confidence: float
    strategy_used: ReasoningStrategy
    steps: List[ReasoningStep] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    self_critique: Optional[str] = None
    refinements_made: int = 0
    duration_ms: float = 0
    problem_type: Optional[ProblemType] = None


class EnhancedReasoner:
    """
    Multi-strategy reasoning engine for smarter AI responses.
    """
    
    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        max_refinements: int = 2,
        confidence_threshold: float = 0.8
    ):
        self.client = AsyncAnthropic()
        self.model = model
        self.max_refinements = max_refinements
        self.confidence_threshold = confidence_threshold
        self._solution_cache: Dict[str, ReasoningResult] = {}
        
    async def reason(
        self,
        query: str,
        context: Optional[str] = None,
        strategy: Optional[ReasoningStrategy] = None,
        require_steps: bool = False
    ) -> ReasoningResult:
        """
        Apply enhanced reasoning to solve a problem.
        
        Args:
            query: The problem or question
            context: Additional context
            strategy: Force a specific strategy (auto-selects if None)
            require_steps: Whether to return detailed steps
        """
        start_time = datetime.now()
        
        # Check cache for similar problems
        cache_key = self._get_cache_key(query, context)
        if cache_key in self._solution_cache:
            cached = self._solution_cache[cache_key]
            if cached.confidence >= self.confidence_threshold:
                return cached
        
        # Auto-detect problem type and strategy
        problem_type = await self._detect_problem_type(query)
        if strategy is None:
            strategy = self._select_strategy(problem_type, query)
        
        # Execute reasoning with selected strategy
        if strategy == ReasoningStrategy.DIRECT:
            result = await self._reason_direct(query, context)
        elif strategy == ReasoningStrategy.CHAIN_OF_THOUGHT:
            result = await self._reason_chain_of_thought(query, context)
        elif strategy == ReasoningStrategy.DECOMPOSITION:
            result = await self._reason_decomposition(query, context)
        elif strategy == ReasoningStrategy.ADVERSARIAL:
            result = await self._reason_adversarial(query, context)
        elif strategy == ReasoningStrategy.CONSENSUS:
            result = await self._reason_consensus(query, context)
        else:
            result = await self._reason_direct(query, context)
        
        # Self-critique and refine if confidence is low
        if result.confidence < self.confidence_threshold:
            result = await self._refine_answer(query, result, context)
        
        # Calculate duration
        result.duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        result.problem_type = problem_type
        result.strategy_used = strategy
        
        # Cache successful results
        if result.confidence >= 0.7:
            self._solution_cache[cache_key] = result
        
        return result
    
    async def _detect_problem_type(self, query: str) -> ProblemType:
        """Detect the type of problem for strategy selection."""
        prompt = f"""Classify this query into ONE of these categories:
- FACTUAL: Looking up information, facts, definitions
- ANALYTICAL: Analysis, reasoning, comparisons, explanations
- CREATIVE: Creating content, generating ideas, writing
- PROCEDURAL: Step-by-step tasks, how-to, workflows
- DEBUGGING: Finding problems, fixing issues, troubleshooting
- OPTIMIZATION: Improving existing things, making better

Query: {query}

Respond with just the category name (e.g., CREATIVE)."""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result = response.content[0].text.strip().upper()
        try:
            return ProblemType[result]
        except KeyError:
            return ProblemType.ANALYTICAL
    
    def _select_strategy(self, problem_type: ProblemType, query: str) -> ReasoningStrategy:
        """Select the best reasoning strategy for the problem type."""
        strategy_map = {
            ProblemType.FACTUAL: ReasoningStrategy.DIRECT,
            ProblemType.ANALYTICAL: ReasoningStrategy.CHAIN_OF_THOUGHT,
            ProblemType.CREATIVE: ReasoningStrategy.ADVERSARIAL,
            ProblemType.PROCEDURAL: ReasoningStrategy.DECOMPOSITION,
            ProblemType.DEBUGGING: ReasoningStrategy.CHAIN_OF_THOUGHT,
            ProblemType.OPTIMIZATION: ReasoningStrategy.CONSENSUS,
        }
        return strategy_map.get(problem_type, ReasoningStrategy.CHAIN_OF_THOUGHT)
    
    async def _reason_direct(self, query: str, context: Optional[str]) -> ReasoningResult:
        """Direct answer without explicit reasoning steps."""
        prompt = query
        if context:
            prompt = f"Context: {context}\n\nQuestion: {query}"
        
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        
        answer = response.content[0].text
        confidence = self._estimate_confidence(answer)
        
        return ReasoningResult(
            answer=answer,
            confidence=confidence,
            strategy_used=ReasoningStrategy.DIRECT
        )
    
    async def _reason_chain_of_thought(self, query: str, context: Optional[str]) -> ReasoningResult:
        """Step-by-step reasoning with explicit thought process."""
        prompt = f"""Think through this step-by-step. For each step:
1. State what you're thinking about
2. Make observations or deductions
3. Rate your confidence (0-100%)

Problem: {query}
{"Context: " + context if context else ""}

Format your response as:
STEP 1: [thought]
OBSERVATION: [what you notice]
CONFIDENCE: [X%]

STEP 2: [thought]
...

FINAL ANSWER: [your conclusion]
OVERALL CONFIDENCE: [X%]"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        
        text = response.content[0].text
        steps, answer, confidence = self._parse_cot_response(text)
        
        return ReasoningResult(
            answer=answer,
            confidence=confidence,
            strategy_used=ReasoningStrategy.CHAIN_OF_THOUGHT,
            steps=steps
        )
    
    async def _reason_decomposition(self, query: str, context: Optional[str]) -> ReasoningResult:
        """Break problem into sub-problems, solve each, combine."""
        # First, decompose
        decompose_prompt = f"""Break this problem into 2-4 smaller sub-problems that can be solved independently:

Problem: {query}
{"Context: " + context if context else ""}

Format: List each sub-problem on a new line starting with "- " """

        decompose_response = await self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{"role": "user", "content": decompose_prompt}]
        )
        
        sub_problems = [
            line.strip()[2:] 
            for line in decompose_response.content[0].text.split('\n')
            if line.strip().startswith('- ')
        ]
        
        # Solve each sub-problem
        sub_solutions = []
        steps = []
        for i, sub in enumerate(sub_problems):
            sub_response = await self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": f"Solve this: {sub}"}]
            )
            solution = sub_response.content[0].text
            sub_solutions.append(solution)
            steps.append(ReasoningStep(
                step_number=i + 1,
                thought=f"Sub-problem: {sub}",
                observation=solution,
                confidence=0.8
            ))
        
        # Combine solutions
        newline = chr(10)
        combine_prompt = f"""Original problem: {query}

Sub-problems and their solutions:
{newline.join(f'{i+1}. {sub}{newline}Solution: {sol}' for i, (sub, sol) in enumerate(zip(sub_problems, sub_solutions)))}

Now combine these into a complete answer:"""

        combine_response = await self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": combine_prompt}]
        )
        
        answer = combine_response.content[0].text
        
        return ReasoningResult(
            answer=answer,
            confidence=0.85,
            strategy_used=ReasoningStrategy.DECOMPOSITION,
            steps=steps
        )
    
    async def _reason_adversarial(self, query: str, context: Optional[str]) -> ReasoningResult:
        """Generate answer, critique it, then refine."""
        # Generate initial answer
        initial = await self._reason_direct(query, context)
        
        # Self-critique
        critique_prompt = f"""Critique this answer. Find weaknesses, errors, or areas for improvement:

Question: {query}
Answer: {initial.answer}

Be specific about what could be better:"""

        critique_response = await self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{"role": "user", "content": critique_prompt}]
        )
        
        critique = critique_response.content[0].text
        
        # Refine based on critique
        refine_prompt = f"""Improve this answer based on the critique:

Question: {query}
Original Answer: {initial.answer}
Critique: {critique}

Provide an improved answer:"""

        refine_response = await self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": refine_prompt}]
        )
        
        refined_answer = refine_response.content[0].text
        
        return ReasoningResult(
            answer=refined_answer,
            confidence=0.85,
            strategy_used=ReasoningStrategy.ADVERSARIAL,
            self_critique=critique,
            alternatives=[initial.answer],
            refinements_made=1
        )
    
    async def _reason_consensus(self, query: str, context: Optional[str], attempts: int = 3) -> ReasoningResult:
        """Generate multiple answers, select the best."""
        # Generate multiple answers in parallel
        tasks = [
            self._reason_direct(query, context)
            for _ in range(attempts)
        ]
        results = await asyncio.gather(*tasks)
        
        # Have the model select the best
        answers = [r.answer for r in results]
        select_prompt = f"""Question: {query}

Here are {len(answers)} different answers:

{chr(10).join(f'ANSWER {i+1}:{chr(10)}{a}{chr(10)}' for i, a in enumerate(answers))}

Evaluate each answer and either:
1. Select the best one (respond with "BEST: [number]")
2. Synthesize a better answer from the best parts (respond with "SYNTHESIZED: [new answer]")"""

        select_response = await self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": select_prompt}]
        )
        
        selection = select_response.content[0].text
        
        if selection.startswith("BEST:"):
            try:
                idx = int(selection.split(":")[1].strip()) - 1
                best_answer = answers[idx]
            except:
                best_answer = answers[0]
        elif selection.startswith("SYNTHESIZED:"):
            best_answer = selection.replace("SYNTHESIZED:", "").strip()
        else:
            best_answer = selection
        
        return ReasoningResult(
            answer=best_answer,
            confidence=0.9,
            strategy_used=ReasoningStrategy.CONSENSUS,
            alternatives=answers
        )
    
    async def _refine_answer(
        self, 
        query: str, 
        result: ReasoningResult,
        context: Optional[str]
    ) -> ReasoningResult:
        """Refine a low-confidence answer."""
        if result.refinements_made >= self.max_refinements:
            return result
        
        refine_prompt = f"""Your previous answer may not be complete or accurate. Please try again with more care.

Question: {query}
Previous Answer: {result.answer}
{"Context: " + context if context else ""}

Tips:
- Think more carefully about edge cases
- Consider if you made any assumptions
- Be more thorough

New Answer:"""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": refine_prompt}]
        )
        
        new_answer = response.content[0].text
        new_confidence = self._estimate_confidence(new_answer)
        
        return ReasoningResult(
            answer=new_answer,
            confidence=min(new_confidence + 0.1, 1.0),  # Boost confidence slightly
            strategy_used=result.strategy_used,
            steps=result.steps,
            alternatives=result.alternatives + [result.answer],
            refinements_made=result.refinements_made + 1
        )
    
    def _parse_cot_response(self, text: str) -> Tuple[List[ReasoningStep], str, float]:
        """Parse chain-of-thought response into structured steps."""
        steps = []
        lines = text.split('\n')
        current_step = None
        answer = ""
        confidence = 0.5
        
        for line in lines:
            line = line.strip()
            if line.startswith('STEP'):
                if current_step:
                    steps.append(current_step)
                try:
                    step_num = int(line.split(':')[0].replace('STEP', '').strip())
                except:
                    step_num = len(steps) + 1
                thought = ':'.join(line.split(':')[1:]).strip()
                current_step = ReasoningStep(step_number=step_num, thought=thought)
            elif line.startswith('OBSERVATION:') and current_step:
                current_step.observation = line.replace('OBSERVATION:', '').strip()
            elif line.startswith('CONFIDENCE:') and current_step:
                try:
                    conf = float(line.replace('CONFIDENCE:', '').replace('%', '').strip()) / 100
                    current_step.confidence = conf
                except:
                    pass
            elif line.startswith('FINAL ANSWER:'):
                if current_step:
                    steps.append(current_step)
                answer = line.replace('FINAL ANSWER:', '').strip()
            elif line.startswith('OVERALL CONFIDENCE:'):
                try:
                    confidence = float(line.replace('OVERALL CONFIDENCE:', '').replace('%', '').strip()) / 100
                except:
                    pass
            elif current_step is None and not any(line.startswith(x) for x in ['STEP', 'FINAL', 'OVERALL']):
                answer += line + "\n"
        
        if current_step and current_step not in steps:
            steps.append(current_step)
        
        return steps, answer.strip() or text, confidence
    
    def _estimate_confidence(self, answer: str) -> float:
        """Estimate confidence based on answer characteristics."""
        confidence = 0.7  # Base confidence
        
        # Hedging words reduce confidence
        hedges = ['maybe', 'perhaps', 'might', 'possibly', 'not sure', 'unclear', "don't know"]
        for hedge in hedges:
            if hedge in answer.lower():
                confidence -= 0.1
        
        # Definitive language increases confidence
        definitive = ['definitely', 'certainly', 'clearly', 'the answer is']
        for d in definitive:
            if d in answer.lower():
                confidence += 0.05
        
        # Longer, more detailed answers get slight boost
        if len(answer) > 500:
            confidence += 0.05
        
        return max(0.3, min(1.0, confidence))
    
    def _get_cache_key(self, query: str, context: Optional[str]) -> str:
        """Generate cache key for a query."""
        combined = f"{query}|{context or ''}"
        return hashlib.md5(combined.encode()).hexdigest()


# Singleton instance
_reasoner: Optional[EnhancedReasoner] = None

def get_reasoner() -> EnhancedReasoner:
    """Get the singleton reasoner instance."""
    global _reasoner
    if _reasoner is None:
        _reasoner = EnhancedReasoner()
    return _reasoner
