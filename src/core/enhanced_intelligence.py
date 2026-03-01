"""
Enhanced Intelligence Integration
================================

Integrates all advanced intelligence modules with SuperIntelligentChat:
- Advanced Reasoning Engine
- Proactive Intelligence
- Smart Tool Router
- Self-Improvement Loop

This creates an enhanced wrapper that makes Otto significantly more capable.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, AsyncIterator, Union
from datetime import datetime
from anthropic import Anthropic, AsyncAnthropic

from .super_intelligent_chat import SuperIntelligentChat, ConversationSession, ChatMessage, MessageRole
from .advanced_reasoning import AdvancedReasoningEngine, ReasoningStrategy
from .proactive_intelligence import ProactiveIntelligence, UserContext
from .smart_tool_router import SmartToolRouter, RoutingDecision
from .self_improvement_loop import SelfImprovementLoop, OutcomeType

logger = logging.getLogger(__name__)


class EnhancedIntelligentChat:
    """
    Enhanced chat interface with advanced AI capabilities.
    
    This wraps SuperIntelligentChat and adds:
    - Advanced reasoning for complex queries
    - Proactive suggestions and anticipation
    - Smart tool routing for optimal execution
    - Self-improvement from every interaction
    
    The result is an AI that thinks deeper, anticipates needs,
    routes intelligently, and gets better over time.
    """
    
    def __init__(
        self,
        anthropic_client: Optional[Anthropic] = None,
        async_anthropic_client: Optional[AsyncAnthropic] = None,
        tool_registry: Any = None,
        agent_crew: Any = None
    ):
        # Core chat
        self.anthropic = anthropic_client or Anthropic()
        self.async_anthropic = async_anthropic_client or AsyncAnthropic()
        
        self.base_chat = SuperIntelligentChat(
            anthropic_client=self.anthropic,
            async_anthropic_client=self.async_anthropic,
            tool_registry=tool_registry,
            agent_crew=agent_crew
        )
        
        # Enhanced modules
        self.reasoning = AdvancedReasoningEngine(self.anthropic)
        self.proactive = ProactiveIntelligence(self.anthropic)
        self.router = SmartToolRouter(self.anthropic, tool_registry)
        self.improvement = SelfImprovementLoop(self.anthropic)
        
        # User contexts for proactive suggestions
        self.user_contexts: Dict[str, UserContext] = {}
        
        # Configuration
        self.config = {
            "use_advanced_reasoning": True,
            "use_proactive_suggestions": True,
            "use_smart_routing": True,
            "use_self_improvement": True,
            "min_reasoning_complexity": 0.7,  # Only use advanced reasoning for complex queries
            "max_proactive_suggestions": 3
        }
        
        logger.info("Enhanced Intelligent Chat initialized with all modules")
    
    async def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        images: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False,
        use_tools: bool = True,
        use_vision: bool = False,
        system_prompt: Optional[str] = None
    ) -> Union[str, AsyncIterator[str]]:
        """
        Send a message and get an enhanced response.
        
        This goes beyond simple chat by:
        1. Analyzing query complexity for optimal reasoning
        2. Routing to best tools
        3. Applying learned knowledge
        4. Generating proactive suggestions
        5. Recording outcomes for improvement
        """
        start_time = datetime.now()
        
        # Get user context
        user_ctx = self._get_user_context(user_id or session_id or "default")
        
        try:
            # Step 1: Apply learned knowledge
            learned_adjustments = {}
            if self.config["use_self_improvement"]:
                learned_adjustments = self.improvement.apply_learned_knowledge(
                    message,
                    {"user_id": user_id, "session_id": session_id}
                )
                
                # Log any warnings from past failures
                for warning in learned_adjustments.get("warnings", []):
                    logger.warning(f"Learned warning: {warning}")
            
            # Step 2: Smart tool routing
            routing_decision = None
            if self.config["use_smart_routing"] and use_tools:
                routing_decision = self.router.route(
                    message,
                    context={"user_id": user_id, "last_tool": user_ctx.last_action}
                )
                logger.info(f"Routing decision: {routing_decision.primary_tool} (confidence: {routing_decision.confidence:.2f})")
            
            # Step 3: Check if advanced reasoning is needed
            enhanced_message = message
            reasoning_used = None
            
            if self.config["use_advanced_reasoning"]:
                complexity = self._assess_complexity(message)
                
                if complexity >= self.config["min_reasoning_complexity"]:
                    # Use advanced reasoning
                    reasoning_result = self.reasoning.reason(
                        message,
                        context={"routing": routing_decision.__dict__ if routing_decision else None}
                    )
                    
                    # Enhance the message with reasoning insights
                    if reasoning_result["verification"]["score"] > 0.7:
                        enhanced_message = self._enhance_with_reasoning(message, reasoning_result)
                        reasoning_used = reasoning_result["strategy"]
                        logger.info(f"Used {reasoning_used} reasoning for complex query")
            
            # Step 4: Get response from base chat
            response = await self.base_chat.chat(
                message=enhanced_message,
                session_id=session_id,
                user_id=user_id,
                images=images,
                stream=stream,
                use_tools=use_tools,
                use_vision=use_vision,
                system_prompt=self._enhance_system_prompt(system_prompt, learned_adjustments)
            )
            
            # Step 5: Add proactive suggestions
            final_response = response
            if self.config["use_proactive_suggestions"] and not stream:
                suggestions = await self._get_proactive_suggestions(message, response, user_ctx)
                if suggestions:
                    final_response = self._append_suggestions(response, suggestions)
            
            # Step 6: Record successful outcome
            if self.config["use_self_improvement"]:
                duration = (datetime.now() - start_time).total_seconds() * 1000
                self.improvement.record_outcome(
                    user_request=message,
                    outcome_type=OutcomeType.SUCCESS,
                    tool_used=routing_decision.primary_tool if routing_decision else None,
                    parameters_used={
                        "duration_ms": duration,
                        "reasoning_used": reasoning_used
                    },
                    result={"response_length": len(final_response) if isinstance(final_response, str) else 0}
                )
            
            # Update user context
            user_ctx.last_query = message
            user_ctx.last_action = routing_decision.primary_tool if routing_decision else None
            user_ctx.query_count += 1
            
            return final_response
            
        except Exception as e:
            # Record failure for learning
            if self.config["use_self_improvement"]:
                self.improvement.record_outcome(
                    user_request=message,
                    outcome_type=OutcomeType.ERROR,
                    error_message=str(e)
                )
            raise
    
    def _assess_complexity(self, message: str) -> float:
        """Assess query complexity to decide reasoning strategy."""
        complexity = 0.0
        
        # Length indicates complexity
        if len(message) > 200:
            complexity += 0.3
        elif len(message) > 100:
            complexity += 0.2
        
        # Question words indicate reasoning needed
        question_words = ["why", "how", "should", "could", "would", "compare", "analyze", "evaluate"]
        if any(w in message.lower() for w in question_words):
            complexity += 0.3
        
        # Multi-part requests
        if any(c in message for c in [",", ";", "1.", "2.", "first", "second", "then"]):
            complexity += 0.2
        
        # Technical or domain-specific
        technical_indicators = ["implement", "architecture", "design", "system", "algorithm", "strategy"]
        if any(w in message.lower() for w in technical_indicators):
            complexity += 0.2
        
        return min(complexity, 1.0)
    
    def _enhance_with_reasoning(self, message: str, reasoning_result: Dict) -> str:
        """Enhance message with reasoning insights."""
        # Add context from reasoning to help the chat
        insights = []
        
        if reasoning_result.get("reasoning_trace"):
            # Extract key insights from trace
            trace = reasoning_result["reasoning_trace"]
            
            # Get the conclusion or key points
            if "causal_chain" in trace:
                insights.append(f"Causal relationships: {trace['causal_chain'][:200]}")
            if "decomposed_problem" in trace:
                insights.append(f"Problem breakdown: {trace['decomposed_problem'][:200]}")
        
        if insights:
            return f"{message}\n\n[Reasoning context: {'; '.join(insights)}]"
        
        return message
    
    def _enhance_system_prompt(
        self,
        base_prompt: Optional[str],
        learned_adjustments: Dict[str, Any]
    ) -> Optional[str]:
        """Enhance system prompt with learned knowledge."""
        if not learned_adjustments:
            return base_prompt
        
        additions = []
        
        for suggestion in learned_adjustments.get("suggestions", []):
            additions.append(f"- {suggestion}")
        
        if not additions:
            return base_prompt
        
        base = base_prompt or ""
        enhancement = "\n\nLearned behavior adjustments:\n" + "\n".join(additions)
        
        return base + enhancement
    
    async def _get_proactive_suggestions(
        self,
        message: str,
        response: str,
        user_ctx: UserContext
    ) -> List[str]:
        """Get proactive suggestions for follow-up."""
        if not isinstance(response, str):
            return []
        
        suggestions = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.proactive.get_suggestions(message, user_ctx)
        )
        
        # Limit and format
        formatted = []
        for s in suggestions[:self.config["max_proactive_suggestions"]]:
            formatted.append(f"💡 {s.suggestion_text}")
        
        return formatted
    
    def _append_suggestions(
        self,
        response: str,
        suggestions: List[str]
    ) -> str:
        """Append proactive suggestions to response."""
        if not suggestions:
            return response
        
        suggestion_text = "\n\n---\n**You might also want to:**\n" + "\n".join(suggestions)
        return response + suggestion_text
    
    def _get_user_context(self, user_id: str) -> UserContext:
        """Get or create user context."""
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = UserContext(user_id=user_id)
        return self.user_contexts[user_id]
    
    def record_user_feedback(
        self,
        original_request: str,
        original_response: str,
        feedback: str
    ):
        """Record user feedback for improvement."""
        if self.config["use_self_improvement"]:
            self.improvement.record_user_correction(
                original_request,
                original_response,
                feedback
            )
    
    def get_improvement_stats(self) -> Dict[str, Any]:
        """Get self-improvement statistics."""
        return self.improvement.get_stats()
    
    def get_improvement_suggestions(self) -> List[Dict[str, Any]]:
        """Get suggestions for system improvement."""
        suggestions = self.improvement.get_improvement_suggestions()
        return [
            {
                "area": s.area.value,
                "description": s.description,
                "priority": s.priority,
                "action": s.suggested_action
            }
            for s in suggestions
        ]


# Factory function
def get_enhanced_chat(
    anthropic_client: Optional[Anthropic] = None,
    async_anthropic_client: Optional[AsyncAnthropic] = None,
    tool_registry: Any = None,
    agent_crew: Any = None
) -> EnhancedIntelligentChat:
    """Create an enhanced intelligent chat instance."""
    return EnhancedIntelligentChat(
        anthropic_client=anthropic_client,
        async_anthropic_client=async_anthropic_client,
        tool_registry=tool_registry,
        agent_crew=agent_crew
    )
