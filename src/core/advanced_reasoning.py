"""
Advanced Reasoning Engine
=========================

Enables Otto to think deeper, reason through complex problems,
and self-correct before providing answers.

Key Capabilities:
- Chain-of-thought reasoning with explicit steps
- Self-verification and critique before responding
- Multi-perspective analysis (consider alternatives)
- Uncertainty quantification (know what you don't know)
- Causal reasoning (understand why, not just what)
- Metacognition (thinking about thinking)
"""

import logging
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class ReasoningStrategy(Enum):
    """Different reasoning strategies for different problem types."""
    DIRECT = "direct"  # Simple, direct response
    CHAIN_OF_THOUGHT = "chain_of_thought"  # Step-by-step reasoning
    TREE_OF_THOUGHT = "tree_of_thought"  # Explore multiple branches
    SELF_CRITIQUE = "self_critique"  # Generate + critique + improve
    DEBATE = "debate"  # Consider opposing viewpoints
    DECOMPOSE = "decompose"  # Break into subproblems
    ANALOGICAL = "analogical"  # Reason by analogy
    CAUSAL = "causal"  # Trace cause and effect


@dataclass
class ReasoningStep:
    """A single step in the reasoning process."""
    step_number: int
    thought: str
    conclusion: Optional[str] = None
    confidence: float = 0.0
    alternatives_considered: List[str] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)


@dataclass
class ReasoningResult:
    """Complete reasoning result with full trace."""
    query: str
    strategy_used: ReasoningStrategy
    steps: List[ReasoningStep]
    final_answer: str
    confidence: float
    reasoning_time_ms: int
    self_critique: Optional[str] = None
    improvements_made: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AdvancedReasoningEngine:
    """
    Multi-strategy reasoning engine that thinks before responding.
    
    Features:
    - Automatic strategy selection based on query type
    - Chain-of-thought for complex problems
    - Self-verification to catch errors
    - Uncertainty awareness
    - Multi-perspective consideration
    """
    
    def __init__(self, anthropic_client: Anthropic):
        self.anthropic = anthropic_client
        self.model = "claude-sonnet-4-20250514"
        
        # Query type classifiers
        self.complex_indicators = [
            "why", "how would", "explain", "analyze", "compare",
            "what if", "should i", "help me think", "figure out",
            "trade-off", "pros and cons", "best way", "strategy"
        ]
        
        self.causal_indicators = [
            "because", "cause", "effect", "result", "lead to",
            "consequence", "impact", "influence", "why did"
        ]
        
        self.creative_indicators = [
            "brainstorm", "ideas", "alternatives", "options",
            "different ways", "creative", "innovative", "novel"
        ]
        
        logger.info("Advanced Reasoning Engine initialized")
    
    def _classify_query(self, query: str) -> ReasoningStrategy:
        """Determine best reasoning strategy for query."""
        query_lower = query.lower()
        
        # Check for causal questions
        if any(ind in query_lower for ind in self.causal_indicators):
            return ReasoningStrategy.CAUSAL
        
        # Check for creative/brainstorm requests
        if any(ind in query_lower for ind in self.creative_indicators):
            return ReasoningStrategy.TREE_OF_THOUGHT
        
        # Check for complex analytical questions
        if any(ind in query_lower for ind in self.complex_indicators):
            # Multi-part or comparison questions benefit from decomposition
            if "and" in query_lower or "compare" in query_lower:
                return ReasoningStrategy.DECOMPOSE
            return ReasoningStrategy.CHAIN_OF_THOUGHT
        
        # Check query length/complexity
        words = query.split()
        if len(words) > 30:
            return ReasoningStrategy.CHAIN_OF_THOUGHT
        
        # Simple queries get direct responses
        return ReasoningStrategy.DIRECT
    
    async def reason(
        self,
        query: str,
        context: Optional[str] = None,
        strategy: Optional[ReasoningStrategy] = None,
        force_verification: bool = False
    ) -> ReasoningResult:
        """
        Apply reasoning to a query.
        
        Args:
            query: The question/request to reason about
            context: Optional context information
            strategy: Force a specific strategy, or auto-detect
            force_verification: Always run self-verification
        
        Returns:
            ReasoningResult with complete thinking trace
        """
        start_time = datetime.now()
        
        # Auto-select strategy if not specified
        if strategy is None:
            strategy = self._classify_query(query)
        
        # Route to appropriate reasoning method
        if strategy == ReasoningStrategy.DIRECT:
            result = await self._direct_response(query, context)
        elif strategy == ReasoningStrategy.CHAIN_OF_THOUGHT:
            result = await self._chain_of_thought(query, context)
        elif strategy == ReasoningStrategy.TREE_OF_THOUGHT:
            result = await self._tree_of_thought(query, context)
        elif strategy == ReasoningStrategy.SELF_CRITIQUE:
            result = await self._self_critique(query, context)
        elif strategy == ReasoningStrategy.DECOMPOSE:
            result = await self._decompose_and_solve(query, context)
        elif strategy == ReasoningStrategy.CAUSAL:
            result = await self._causal_reasoning(query, context)
        else:
            result = await self._chain_of_thought(query, context)
        
        # Apply self-verification for complex strategies
        if force_verification or strategy in [
            ReasoningStrategy.CHAIN_OF_THOUGHT,
            ReasoningStrategy.DECOMPOSE,
            ReasoningStrategy.CAUSAL
        ]:
            result = await self._verify_and_improve(result)
        
        # Calculate timing
        elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        result.reasoning_time_ms = elapsed_ms
        result.strategy_used = strategy
        
        return result
    
    async def _direct_response(
        self,
        query: str,
        context: Optional[str]
    ) -> ReasoningResult:
        """Simple direct response for straightforward queries."""
        system = """You are Otto, a super-intelligent assistant.
Provide a clear, helpful response. Be concise but complete."""
        
        user_content = query
        if context:
            user_content = f"Context:\n{context}\n\nQuestion: {query}"
        
        response = self.anthropic.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": user_content}]
        )
        
        answer = response.content[0].text
        
        return ReasoningResult(
            query=query,
            strategy_used=ReasoningStrategy.DIRECT,
            steps=[ReasoningStep(step_number=1, thought="Direct response", confidence=0.9)],
            final_answer=answer,
            confidence=0.9,
            reasoning_time_ms=0
        )
    
    async def _chain_of_thought(
        self,
        query: str,
        context: Optional[str]
    ) -> ReasoningResult:
        """Step-by-step reasoning with explicit thinking."""
        system = """You are Otto, a super-intelligent reasoning engine.

For this query, think step-by-step explicitly. Use this format:

<thinking>
Step 1: [First observation or understanding of the problem]
Step 2: [Build on step 1, consider implications]
Step 3: [Continue reasoning...]
...
</thinking>

<uncertainties>
- List any uncertainties or assumptions you're making
</uncertainties>

<conclusion>
Your final answer based on the reasoning above.
</conclusion>

Be thorough. Show your work. Consider edge cases."""
        
        user_content = query
        if context:
            user_content = f"Context:\n{context}\n\nQuestion: {query}"
        
        response = self.anthropic.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user_content}]
        )
        
        full_response = response.content[0].text
        
        # Parse the structured response
        steps = []
        thinking_match = re.search(r'<thinking>(.*?)</thinking>', full_response, re.DOTALL)
        if thinking_match:
            thinking = thinking_match.group(1)
            step_matches = re.findall(r'Step (\d+):\s*(.+?)(?=Step \d+:|$)', thinking, re.DOTALL)
            for num, thought in step_matches:
                steps.append(ReasoningStep(
                    step_number=int(num),
                    thought=thought.strip(),
                    confidence=0.8
                ))
        
        # Get uncertainties
        uncertainties = []
        unc_match = re.search(r'<uncertainties>(.*?)</uncertainties>', full_response, re.DOTALL)
        if unc_match:
            unc_text = unc_match.group(1)
            uncertainties = [u.strip().lstrip('- ') for u in unc_text.strip().split('\n') if u.strip()]
        
        # Get conclusion
        conclusion = ""
        conc_match = re.search(r'<conclusion>(.*?)</conclusion>', full_response, re.DOTALL)
        if conc_match:
            conclusion = conc_match.group(1).strip()
        else:
            conclusion = full_response
        
        # Add uncertainties to last step
        if steps and uncertainties:
            steps[-1].uncertainties = uncertainties
        
        return ReasoningResult(
            query=query,
            strategy_used=ReasoningStrategy.CHAIN_OF_THOUGHT,
            steps=steps if steps else [ReasoningStep(1, "Analyzed the query", conclusion=conclusion)],
            final_answer=conclusion,
            confidence=0.85 - (len(uncertainties) * 0.05),  # Lower confidence with more uncertainty
            reasoning_time_ms=0
        )
    
    async def _tree_of_thought(
        self,
        query: str,
        context: Optional[str]
    ) -> ReasoningResult:
        """Explore multiple reasoning branches for creative/complex problems."""
        system = """You are Otto, a super-intelligent creative reasoning engine.

For this query, explore MULTIPLE possible approaches before settling on the best one.

<branch_1>
Approach: [First possible approach/solution]
Reasoning: [Why this might work]
Pros: [Advantages]
Cons: [Disadvantages]
</branch_1>

<branch_2>
Approach: [Second possible approach/solution]
Reasoning: [Why this might work]
Pros: [Advantages]
Cons: [Disadvantages]
</branch_2>

<branch_3>
Approach: [Third possible approach/solution]
Reasoning: [Why this might work]
Pros: [Advantages]
Cons: [Disadvantages]
</branch_3>

<synthesis>
After considering all branches, the best approach is:
[Your synthesized answer combining the best elements]
</synthesis>

Explore genuinely different alternatives, not minor variations."""
        
        user_content = query
        if context:
            user_content = f"Context:\n{context}\n\nQuestion: {query}"
        
        response = self.anthropic.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user_content}]
        )
        
        full_response = response.content[0].text
        
        # Parse branches
        steps = []
        branch_pattern = r'<branch_(\d+)>(.*?)</branch_\1>'
        branches = re.findall(branch_pattern, full_response, re.DOTALL)
        
        for num, content in branches:
            approach_match = re.search(r'Approach:\s*(.+?)(?=\n|$)', content)
            approach = approach_match.group(1) if approach_match else f"Branch {num}"
            
            steps.append(ReasoningStep(
                step_number=int(num),
                thought=content.strip(),
                conclusion=approach,
                confidence=0.7,
                alternatives_considered=[approach]
            ))
        
        # Get synthesis
        synthesis = ""
        synth_match = re.search(r'<synthesis>(.*?)</synthesis>', full_response, re.DOTALL)
        if synth_match:
            synthesis = synth_match.group(1).strip()
        else:
            synthesis = full_response
        
        return ReasoningResult(
            query=query,
            strategy_used=ReasoningStrategy.TREE_OF_THOUGHT,
            steps=steps,
            final_answer=synthesis,
            confidence=0.85,
            reasoning_time_ms=0,
            metadata={"branches_explored": len(branches)}
        )
    
    async def _decompose_and_solve(
        self,
        query: str,
        context: Optional[str]
    ) -> ReasoningResult:
        """Break complex problem into subproblems and solve each."""
        system = """You are Otto, a super-intelligent problem decomposition engine.

For complex queries, break them into smaller, manageable subproblems:

<decomposition>
Subproblem 1: [First component of the problem]
Subproblem 2: [Second component]
Subproblem 3: [Third component if needed]
...
</decomposition>

<solution_1>
Solving subproblem 1: [Solution]
</solution_1>

<solution_2>
Solving subproblem 2: [Solution]
</solution_2>

<integration>
Combining the solutions: [Integrated final answer that addresses the original complex question]
</integration>

Focus on meaningful decomposition that makes the problem tractable."""
        
        user_content = query
        if context:
            user_content = f"Context:\n{context}\n\nQuestion: {query}"
        
        response = self.anthropic.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user_content}]
        )
        
        full_response = response.content[0].text
        steps = []
        
        # Parse decomposition
        decomp_match = re.search(r'<decomposition>(.*?)</decomposition>', full_response, re.DOTALL)
        if decomp_match:
            steps.append(ReasoningStep(
                step_number=1,
                thought="Problem decomposition: " + decomp_match.group(1).strip(),
                confidence=0.9
            ))
        
        # Parse solutions
        solution_pattern = r'<solution_(\d+)>(.*?)</solution_\1>'
        solutions = re.findall(solution_pattern, full_response, re.DOTALL)
        for num, content in solutions:
            steps.append(ReasoningStep(
                step_number=int(num) + 1,
                thought=content.strip(),
                confidence=0.85
            ))
        
        # Get integration
        integration = ""
        int_match = re.search(r'<integration>(.*?)</integration>', full_response, re.DOTALL)
        if int_match:
            integration = int_match.group(1).strip()
        else:
            integration = full_response
        
        return ReasoningResult(
            query=query,
            strategy_used=ReasoningStrategy.DECOMPOSE,
            steps=steps,
            final_answer=integration,
            confidence=0.88,
            reasoning_time_ms=0,
            metadata={"subproblems_solved": len(solutions)}
        )
    
    async def _causal_reasoning(
        self,
        query: str,
        context: Optional[str]
    ) -> ReasoningResult:
        """Trace cause and effect relationships."""
        system = """You are Otto, a super-intelligent causal reasoning engine.

For causal questions, explicitly trace cause-effect relationships:

<causal_chain>
Root Cause: [The fundamental cause or starting point]
↓
Effect 1: [First consequence] 
  └─ Mechanism: [How the cause leads to this effect]
↓
Effect 2: [Second-order consequence]
  └─ Mechanism: [How effect 1 leads to effect 2]
↓
[Continue the chain as needed]
</causal_chain>

<alternative_causes>
Other potential causes or contributing factors:
- [Alternative explanation 1]
- [Alternative explanation 2]
</alternative_causes>

<conclusion>
[Final causal explanation with confidence level]
</conclusion>

Be rigorous about the causal mechanisms, not just correlations."""
        
        user_content = query
        if context:
            user_content = f"Context:\n{context}\n\nQuestion: {query}"
        
        response = self.anthropic.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user_content}]
        )
        
        full_response = response.content[0].text
        
        steps = [ReasoningStep(
            step_number=1,
            thought="Causal analysis: " + full_response,
            confidence=0.8
        )]
        
        # Extract conclusion
        conclusion = ""
        conc_match = re.search(r'<conclusion>(.*?)</conclusion>', full_response, re.DOTALL)
        if conc_match:
            conclusion = conc_match.group(1).strip()
        else:
            conclusion = full_response
        
        return ReasoningResult(
            query=query,
            strategy_used=ReasoningStrategy.CAUSAL,
            steps=steps,
            final_answer=conclusion,
            confidence=0.8,
            reasoning_time_ms=0
        )
    
    async def _self_critique(
        self,
        query: str,
        context: Optional[str]
    ) -> ReasoningResult:
        """Generate, critique, and improve response."""
        # Step 1: Generate initial response
        initial = await self._chain_of_thought(query, context)
        
        # Step 2: Critique
        critique_system = """You are a rigorous critic. 
Review this response and identify:
1. Logical errors or gaps
2. Missing considerations
3. Unsupported claims
4. Ways to improve

Be constructively critical. Find real issues."""
        
        critique_response = self.anthropic.messages.create(
            model=self.model,
            max_tokens=2048,
            system=critique_system,
            messages=[
                {"role": "user", "content": f"Query: {query}\n\nResponse to critique:\n{initial.final_answer}"}
            ]
        )
        
        critique = critique_response.content[0].text
        
        # Step 3: Improve based on critique
        improve_system = """You are Otto. You've received critique on your response.
Incorporate the valid feedback and provide an improved answer.
Don't be defensive - use the critique constructively."""
        
        improved = self.anthropic.messages.create(
            model=self.model,
            max_tokens=2048,
            system=improve_system,
            messages=[
                {"role": "user", "content": f"""Original query: {query}

Your initial response: {initial.final_answer}

Critique received: {critique}

Provide an improved response:"""}
            ]
        )
        
        improved_answer = improved.content[0].text
        
        # Combine results
        initial.self_critique = critique
        initial.improvements_made = ["Applied self-critique loop"]
        initial.final_answer = improved_answer
        initial.confidence += 0.05  # Boost confidence after verification
        
        return initial
    
    async def _verify_and_improve(
        self,
        result: ReasoningResult
    ) -> ReasoningResult:
        """Verify reasoning and improve if needed."""
        verify_system = """You are a verification agent. Check this reasoning for:
1. Logical consistency
2. Factual accuracy (flag if uncertain)
3. Completeness of answer
4. Clarity of explanation

If issues found, provide corrections. If sound, confirm.
Format: VERIFIED or NEEDS_IMPROVEMENT: [issues]"""
        
        response = self.anthropic.messages.create(
            model=self.model,
            max_tokens=1024,
            system=verify_system,
            messages=[
                {"role": "user", "content": f"""Query: {result.query}

Reasoning steps:
{json.dumps([{"step": s.step_number, "thought": s.thought} for s in result.steps], indent=2)}

Final answer:
{result.final_answer}"""}
            ]
        )
        
        verification = response.content[0].text
        
        if "VERIFIED" in verification:
            result.confidence = min(result.confidence + 0.05, 0.99)
            result.metadata["verified"] = True
        else:
            result.self_critique = verification
            result.metadata["needs_review"] = True
        
        return result


def get_reasoning_engine(anthropic_client: Anthropic) -> AdvancedReasoningEngine:
    """Factory function to create reasoning engine."""
    return AdvancedReasoningEngine(anthropic_client)
