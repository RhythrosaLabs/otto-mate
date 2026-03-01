"""
Proactive Intelligence System
============================

Enables Otto to anticipate needs, suggest actions, and be helpful
without being asked. Transforms Otto from reactive to proactive.

Key Capabilities:
- Pattern recognition in user behavior
- Intelligent suggestions based on context
- Anticipating follow-up needs
- Proactive error prevention
- Timing-aware recommendations
- Cross-session learning
"""

import logging
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class SuggestionType(Enum):
    """Types of proactive suggestions."""
    FOLLOW_UP_ACTION = "follow_up"  # "Would you like me to also..."
    IMPROVEMENT = "improvement"  # "I noticed we could improve..."
    REMINDER = "reminder"  # "You mentioned earlier..."
    OPTIMIZATION = "optimization"  # "A more efficient approach..."
    ERROR_PREVENTION = "error_prevention"  # "Before we do that, note..."
    RELATED_INSIGHT = "insight"  # "Interesting related fact..."
    WORKFLOW_SUGGESTION = "workflow"  # "Based on your pattern..."


@dataclass
class ProactiveSuggestion:
    """A proactive suggestion from Otto."""
    suggestion_type: SuggestionType
    text: str
    reasoning: str
    confidence: float
    priority: int  # 1-5, 5 being most important
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserContext:
    """Accumulated context about user and session."""
    session_id: str
    user_id: Optional[str] = None
    
    # Current session context
    topics_discussed: List[str] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    entities_mentioned: Dict[str, List[str]] = field(default_factory=dict)
    
    # User patterns
    preferred_tools: Dict[str, int] = field(default_factory=dict)
    common_workflows: List[List[str]] = field(default_factory=list)
    time_patterns: Dict[str, int] = field(default_factory=dict)
    
    # Goals and tasks
    stated_goals: List[str] = field(default_factory=list)
    incomplete_tasks: List[str] = field(default_factory=list)
    
    # Preferences learned
    preferences: Dict[str, Any] = field(default_factory=dict)


class ProactiveIntelligence:
    """
    Makes Otto anticipate needs and provide unprompted helpful suggestions.
    
    This system observes:
    - What the user is doing
    - What they have done before
    - What typically comes next
    - What could go wrong
    
    And suggests:
    - Next logical steps
    - Improvements to current approach
    - Related actions they might want
    - Potential issues to avoid
    """
    
    def __init__(self, anthropic_client: Anthropic):
        self.anthropic = anthropic_client
        self.model = "claude-sonnet-4-20250514"
        
        # User context cache
        self.contexts: Dict[str, UserContext] = {}
        
        # Common workflow patterns
        self.workflow_patterns = {
            # Product creation workflows
            "generate_image": ["create_product", "add_to_store"],
            "create_product": ["publish_product", "generate_social_media_posts"],
            "upload_image": ["generate_image", "create_product"],
            
            # Marketing workflows
            "generate_blog_post": ["publish_to_shopify", "generate_social_media_posts"],
            "generate_email_campaign": ["send_email", "schedule_email"],
            "generate_social_media_posts": ["schedule_post", "post_to_platform"],
            
            # Research workflows
            "web_search": ["summarize", "create_report"],
            "research_topic": ["generate_blog_post", "generate_email_campaign"],
            
            # Business workflows
            "get_shopify_orders": ["generate_report", "send_email"],
            "search_contacts": ["send_email", "add_to_campaign"],
        }
        
        # Common follow-up suggestions based on action
        self.follow_up_templates = {
            "generate_image": [
                ("Want me to create a product with this design?", 0.9),
                ("Should I generate variations of this image?", 0.7),
                ("Would you like social media posts featuring this?", 0.6),
            ],
            "create_product": [
                ("Should I publish this to your store?", 0.95),
                ("Want me to create matching products?", 0.7),
                ("Should I generate marketing content for this?", 0.8),
            ],
            "generate_blog_post": [
                ("Want me to publish this to your Shopify blog?", 0.9),
                ("Should I create social media posts to promote this?", 0.85),
                ("Would you like an email campaign about this topic?", 0.7),
            ],
            "research_topic": [
                ("Should I summarize the key findings?", 0.9),
                ("Want me to create content based on this research?", 0.8),
                ("Should I save this to your knowledge base?", 0.7),
            ],
            "send_email": [
                ("Should I schedule follow-up reminders?", 0.8),
                ("Want me to track responses?", 0.7),
            ],
        }
        
        logger.info("Proactive Intelligence initialized")
    
    def _get_or_create_context(self, session_id: str) -> UserContext:
        """Get or create user context for session."""
        if session_id not in self.contexts:
            self.contexts[session_id] = UserContext(session_id=session_id)
        return self.contexts[session_id]
    
    def update_context(
        self,
        session_id: str,
        action: Optional[str] = None,
        topic: Optional[str] = None,
        entities: Optional[Dict[str, List[str]]] = None,
        tool_used: Optional[str] = None,
        goal: Optional[str] = None
    ):
        """Update context based on user interaction."""
        ctx = self._get_or_create_context(session_id)
        
        if topic and topic not in ctx.topics_discussed:
            ctx.topics_discussed.append(topic)
        
        if tool_used:
            ctx.tools_used.append(tool_used)
            ctx.preferred_tools[tool_used] = ctx.preferred_tools.get(tool_used, 0) + 1
        
        if entities:
            for entity_type, values in entities.items():
                if entity_type not in ctx.entities_mentioned:
                    ctx.entities_mentioned[entity_type] = []
                ctx.entities_mentioned[entity_type].extend(values)
        
        if goal and goal not in ctx.stated_goals:
            ctx.stated_goals.append(goal)
        
        # Track time patterns
        hour = datetime.now().hour
        time_bucket = f"{hour:02d}:00"
        ctx.time_patterns[time_bucket] = ctx.time_patterns.get(time_bucket, 0) + 1
    
    def get_suggestions(
        self,
        session_id: str,
        last_action: Optional[str] = None,
        last_result: Optional[Dict[str, Any]] = None,
        current_message: Optional[str] = None,
        max_suggestions: int = 3
    ) -> List[ProactiveSuggestion]:
        """
        Generate proactive suggestions based on context.
        
        Args:
            session_id: Current session
            last_action: Last tool/action executed
            last_result: Result from last action
            current_message: User's current message
            max_suggestions: Max number of suggestions
            
        Returns:
            List of prioritized suggestions
        """
        suggestions = []
        ctx = self._get_or_create_context(session_id)
        
        # 1. Follow-up suggestions based on last action
        if last_action:
            suggestions.extend(self._get_follow_up_suggestions(last_action, last_result, ctx))
        
        # 2. Workflow continuation suggestions
        if ctx.tools_used:
            suggestions.extend(self._get_workflow_suggestions(ctx))
        
        # 3. Goal-based suggestions
        if ctx.stated_goals:
            suggestions.extend(self._get_goal_suggestions(ctx))
        
        # 4. Error prevention suggestions
        if current_message:
            suggestions.extend(self._get_prevention_suggestions(current_message, ctx))
        
        # 5. Timing-based suggestions
        suggestions.extend(self._get_timing_suggestions(ctx))
        
        # Sort by priority and confidence
        suggestions.sort(key=lambda s: (s.priority, s.confidence), reverse=True)
        
        return suggestions[:max_suggestions]
    
    def _get_follow_up_suggestions(
        self,
        last_action: str,
        last_result: Optional[Dict[str, Any]],
        ctx: UserContext
    ) -> List[ProactiveSuggestion]:
        """Get suggestions based on what was just done."""
        suggestions = []
        
        # Check if we have templates for this action
        if last_action in self.follow_up_templates:
            for text, confidence in self.follow_up_templates[last_action]:
                suggestions.append(ProactiveSuggestion(
                    suggestion_type=SuggestionType.FOLLOW_UP_ACTION,
                    text=text,
                    reasoning=f"Common follow-up after {last_action}",
                    confidence=confidence,
                    priority=4,
                    metadata={"trigger_action": last_action}
                ))
        
        # Check workflow patterns
        if last_action in self.workflow_patterns:
            next_steps = self.workflow_patterns[last_action]
            for next_step in next_steps[:2]:
                suggestions.append(ProactiveSuggestion(
                    suggestion_type=SuggestionType.WORKFLOW_SUGGESTION,
                    text=f"Would you like me to {next_step.replace('_', ' ')} next?",
                    reasoning=f"Typical workflow: {last_action} → {next_step}",
                    confidence=0.75,
                    priority=3,
                    metadata={"suggested_action": next_step}
                ))
        
        return suggestions
    
    def _get_workflow_suggestions(self, ctx: UserContext) -> List[ProactiveSuggestion]:
        """Suggest based on detected workflow patterns."""
        suggestions = []
        
        # If multiple related tools used, suggest combining
        if len(ctx.tools_used) >= 2:
            recent_tools = ctx.tools_used[-3:]
            
            # Check for incomplete workflows
            for pattern_start, pattern_ends in self.workflow_patterns.items():
                if pattern_start in recent_tools:
                    for end_action in pattern_ends:
                        if end_action not in recent_tools:
                            suggestions.append(ProactiveSuggestion(
                                suggestion_type=SuggestionType.WORKFLOW_SUGGESTION,
                                text=f"You started a workflow with {pattern_start.replace('_', ' ')}. Want me to complete it with {end_action.replace('_', ' ')}?",
                                reasoning="Detected incomplete workflow pattern",
                                confidence=0.7,
                                priority=3
                            ))
                            break
        
        return suggestions
    
    def _get_goal_suggestions(self, ctx: UserContext) -> List[ProactiveSuggestion]:
        """Suggest actions aligned with stated goals."""
        suggestions = []
        
        for goal in ctx.stated_goals[-2:]:  # Last 2 goals
            # Check if goal-related actions have been taken
            goal_keywords = goal.lower().split()
            related_actions = [
                tool for tool in ctx.preferred_tools
                if any(kw in tool.lower() for kw in goal_keywords)
            ]
            
            if not related_actions:
                suggestions.append(ProactiveSuggestion(
                    suggestion_type=SuggestionType.REMINDER,
                    text=f"You mentioned wanting to '{goal}'. Should we work on that?",
                    reasoning="Reminder about stated goal",
                    confidence=0.8,
                    priority=4,
                    metadata={"goal": goal}
                ))
        
        return suggestions
    
    def _get_prevention_suggestions(
        self,
        current_message: str,
        ctx: UserContext
    ) -> List[ProactiveSuggestion]:
        """Suggest to prevent common mistakes."""
        suggestions = []
        message_lower = current_message.lower()
        
        # Check for potential issues
        if "delete" in message_lower or "remove" in message_lower:
            suggestions.append(ProactiveSuggestion(
                suggestion_type=SuggestionType.ERROR_PREVENTION,
                text="⚠️ This is a destructive action. Would you like me to create a backup first?",
                reasoning="Destructive action detected",
                confidence=0.9,
                priority=5
            ))
        
        if "all" in message_lower and any(w in message_lower for w in ["products", "posts", "emails"]):
            suggestions.append(ProactiveSuggestion(
                suggestion_type=SuggestionType.ERROR_PREVENTION,
                text="This will affect many items. Should I show you a preview first?",
                reasoning="Bulk action detected",
                confidence=0.85,
                priority=5
            ))
        
        # Check for missing context
        if any(w in message_lower for w in ["publish", "post", "send"]) and not ctx.entities_mentioned.get("products"):
            suggestions.append(ProactiveSuggestion(
                suggestion_type=SuggestionType.ERROR_PREVENTION,
                text="I don't see any content ready to publish. Want me to help create something first?",
                reasoning="Publish without content",
                confidence=0.75,
                priority=4
            ))
        
        return suggestions
    
    def _get_timing_suggestions(self, ctx: UserContext) -> List[ProactiveSuggestion]:
        """Time-aware suggestions."""
        suggestions = []
        hour = datetime.now().hour
        
        # Morning suggestions
        if 6 <= hour <= 9:
            if ctx.preferred_tools.get("get_shopify_orders"):
                suggestions.append(ProactiveSuggestion(
                    suggestion_type=SuggestionType.WORKFLOW_SUGGESTION,
                    text="Good morning! Want me to check overnight orders and summarize?",
                    reasoning="Morning routine suggestion",
                    confidence=0.7,
                    priority=2
                ))
        
        # End of day suggestions
        if 16 <= hour <= 18:
            if len(ctx.incomplete_tasks) > 0:
                suggestions.append(ProactiveSuggestion(
                    suggestion_type=SuggestionType.REMINDER,
                    text=f"End of day check: You have {len(ctx.incomplete_tasks)} tasks in progress. Want a status update?",
                    reasoning="End of day review",
                    confidence=0.75,
                    priority=3
                ))
        
        return suggestions
    
    async def analyze_opportunity(
        self,
        session_id: str,
        conversation_history: List[Dict[str, str]]
    ) -> Optional[ProactiveSuggestion]:
        """
        Use AI to find proactive opportunities in conversation.
        
        This is a deeper analysis than rule-based suggestions.
        """
        if len(conversation_history) < 2:
            return None
        
        system = """You are Otto's proactive intelligence. Analyze this conversation and identify ONE high-value proactive suggestion.

Look for:
1. Implicit needs the user hasn't explicitly asked for
2. Optimizations to their current approach
3. Related valuable actions they might not have considered
4. Potential issues to prevent

Respond in JSON:
{
    "suggestion": "Your proactive suggestion text",
    "reasoning": "Why this would be valuable",
    "type": "follow_up|improvement|reminder|optimization|error_prevention|insight|workflow",
    "confidence": 0.0-1.0,
    "priority": 1-5
}

If no good suggestion, respond with: {"suggestion": null}"""
        
        # Format conversation for analysis
        convo_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in conversation_history[-6:]  # Last 6 messages
        ])
        
        response = self.anthropic.messages.create(
            model=self.model,
            max_tokens=512,
            system=system,
            messages=[{"role": "user", "content": convo_text}]
        )
        
        try:
            result = json.loads(response.content[0].text)
            if result.get("suggestion"):
                return ProactiveSuggestion(
                    suggestion_type=SuggestionType(result.get("type", "insight")),
                    text=result["suggestion"],
                    reasoning=result.get("reasoning", "AI analysis"),
                    confidence=result.get("confidence", 0.7),
                    priority=result.get("priority", 3)
                )
        except (json.JSONDecodeError, KeyError):
            pass
        
        return None


class SmartSuggestionRenderer:
    """Renders suggestions in a user-friendly way."""
    
    @staticmethod
    def format_suggestions(suggestions: List[ProactiveSuggestion]) -> str:
        """Format suggestions for display."""
        if not suggestions:
            return ""
        
        lines = ["\n💡 **Suggestions:**"]
        
        for i, s in enumerate(suggestions, 1):
            emoji = {
                SuggestionType.FOLLOW_UP_ACTION: "➡️",
                SuggestionType.IMPROVEMENT: "✨",
                SuggestionType.REMINDER: "🔔",
                SuggestionType.OPTIMIZATION: "⚡",
                SuggestionType.ERROR_PREVENTION: "⚠️",
                SuggestionType.RELATED_INSIGHT: "💭",
                SuggestionType.WORKFLOW_SUGGESTION: "🔄",
            }.get(s.suggestion_type, "💡")
            
            lines.append(f"  {emoji} {s.text}")
        
        return "\n".join(lines)


def get_proactive_intelligence(anthropic_client: Anthropic) -> ProactiveIntelligence:
    """Factory function."""
    return ProactiveIntelligence(anthropic_client)
