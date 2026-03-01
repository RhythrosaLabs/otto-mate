"""
Self-Improvement Loop
====================

System for learning from successes and failures to continuously improve.

Key Capabilities:
- Track outcomes of all operations
- Identify patterns in failures and successes
- Adjust parameters and strategies based on feedback
- Generate improvement recommendations
- Self-correct common mistakes
"""

import logging
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class OutcomeType(Enum):
    """Types of outcomes to track."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    ERROR = "error"
    USER_CORRECTION = "user_correction"
    ABANDONED = "abandoned"


class ImprovementArea(Enum):
    """Areas where improvements can be made."""
    INTENT_UNDERSTANDING = "intent_understanding"
    PARAMETER_INFERENCE = "parameter_inference"
    TOOL_SELECTION = "tool_selection"
    ERROR_HANDLING = "error_handling"
    RESPONSE_QUALITY = "response_quality"
    SPEED = "speed"
    CREATIVITY = "creativity"


@dataclass
class Outcome:
    """Record of an operation's outcome."""
    outcome_id: str
    timestamp: datetime
    outcome_type: OutcomeType
    
    # What was attempted
    user_request: str
    tool_used: Optional[str]
    parameters_used: Dict[str, Any]
    
    # Result
    result: Optional[Any]
    error_message: Optional[str]
    
    # Feedback
    user_feedback: Optional[str] = None
    improvement_area: Optional[ImprovementArea] = None
    
    # Analysis
    root_cause: Optional[str] = None
    suggested_fix: Optional[str] = None


@dataclass
class LearningPattern:
    """A learned pattern from outcomes."""
    pattern_id: str
    pattern_type: str
    description: str
    
    # Trigger conditions
    trigger_conditions: Dict[str, Any]
    
    # Learned behavior
    learned_action: Dict[str, Any]
    
    # Confidence and usage
    confidence: float = 0.5
    times_applied: int = 0
    success_rate: float = 0.0
    
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None


@dataclass
class ImprovementSuggestion:
    """A suggested improvement."""
    area: ImprovementArea
    description: str
    priority: int  # 1-10
    evidence: List[str]
    suggested_action: str


class SelfImprovementLoop:
    """
    Learns from every interaction to improve over time.
    
    Tracks:
    - Success/failure patterns
    - User corrections
    - Parameter effectiveness
    - Strategy outcomes
    
    Learns:
    - Better parameter defaults
    - Common user intents
    - Error recovery strategies
    - Quality improvements
    """
    
    def __init__(
        self,
        anthropic_client: Anthropic,
        data_dir: str = "data/intelligence"
    ):
        self.anthropic = anthropic_client
        self.model = "claude-sonnet-4-20250514"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory stores
        self.outcomes: List[Outcome] = []
        self.patterns: Dict[str, LearningPattern] = {}
        
        # Load persisted data
        self._load_patterns()
        
        logger.info("Self-Improvement Loop initialized")
    
    def _load_patterns(self):
        """Load learned patterns from disk."""
        patterns_file = self.data_dir / "learned_patterns.json"
        if patterns_file.exists():
            try:
                with open(patterns_file) as f:
                    data = json.load(f)
                    for p in data.get("patterns", []):
                        pattern = LearningPattern(
                            pattern_id=p["pattern_id"],
                            pattern_type=p["pattern_type"],
                            description=p["description"],
                            trigger_conditions=p["trigger_conditions"],
                            learned_action=p["learned_action"],
                            confidence=p.get("confidence", 0.5),
                            times_applied=p.get("times_applied", 0),
                            success_rate=p.get("success_rate", 0.0)
                        )
                        self.patterns[pattern.pattern_id] = pattern
                logger.info(f"Loaded {len(self.patterns)} learned patterns")
            except Exception as e:
                logger.error(f"Failed to load patterns: {e}")
    
    def _save_patterns(self):
        """Save learned patterns to disk."""
        patterns_file = self.data_dir / "learned_patterns.json"
        try:
            data = {
                "patterns": [
                    {
                        "pattern_id": p.pattern_id,
                        "pattern_type": p.pattern_type,
                        "description": p.description,
                        "trigger_conditions": p.trigger_conditions,
                        "learned_action": p.learned_action,
                        "confidence": p.confidence,
                        "times_applied": p.times_applied,
                        "success_rate": p.success_rate
                    }
                    for p in self.patterns.values()
                ]
            }
            with open(patterns_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save patterns: {e}")
    
    def record_outcome(
        self,
        user_request: str,
        outcome_type: OutcomeType,
        tool_used: Optional[str] = None,
        parameters_used: Optional[Dict[str, Any]] = None,
        result: Optional[Any] = None,
        error_message: Optional[str] = None
    ) -> Outcome:
        """Record an operation outcome."""
        outcome = Outcome(
            outcome_id=f"out_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            outcome_type=outcome_type,
            user_request=user_request,
            tool_used=tool_used,
            parameters_used=parameters_used or {},
            result=result,
            error_message=error_message
        )
        
        self.outcomes.append(outcome)
        
        # Keep only last 1000 outcomes in memory
        if len(self.outcomes) > 1000:
            self.outcomes = self.outcomes[-1000:]
        
        # Analyze for immediate learning
        if outcome_type in [OutcomeType.FAILURE, OutcomeType.ERROR]:
            self._analyze_failure(outcome)
        elif outcome_type == OutcomeType.SUCCESS:
            self._reinforce_success(outcome)
        
        return outcome
    
    def record_user_correction(
        self,
        original_request: str,
        original_response: str,
        correction: str
    ):
        """Record when user corrects the system."""
        outcome = Outcome(
            outcome_id=f"out_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            outcome_type=OutcomeType.USER_CORRECTION,
            user_request=original_request,
            tool_used=None,
            parameters_used={"original_response": original_response},
            result=None,
            error_message=None,
            user_feedback=correction
        )
        
        self.outcomes.append(outcome)
        
        # Learn from correction
        self._learn_from_correction(original_request, original_response, correction)
    
    def _analyze_failure(self, outcome: Outcome):
        """Analyze a failure to understand root cause."""
        # Check for common failure patterns
        error = outcome.error_message or ""
        
        # API-related failures
        if "api" in error.lower() or "token" in error.lower():
            outcome.root_cause = "API configuration issue"
            outcome.improvement_area = ImprovementArea.ERROR_HANDLING
            outcome.suggested_fix = "Check API keys and rate limits"
        
        # Parameter-related failures
        elif "parameter" in error.lower() or "required" in error.lower():
            outcome.root_cause = "Missing or invalid parameters"
            outcome.improvement_area = ImprovementArea.PARAMETER_INFERENCE
            outcome.suggested_fix = "Improve parameter extraction from user request"
            
            # Create learning pattern
            self._create_pattern(
                pattern_type="parameter_fix",
                description=f"Better handle missing parameters for {outcome.tool_used}",
                trigger_conditions={
                    "tool": outcome.tool_used,
                    "error_contains": "parameter"
                },
                learned_action={
                    "action": "prompt_for_missing_params",
                    "params_to_check": list(outcome.parameters_used.keys())
                }
            )
        
        # Tool selection failures
        elif "not found" in error.lower() or "unavailable" in error.lower():
            outcome.root_cause = "Wrong tool selected"
            outcome.improvement_area = ImprovementArea.TOOL_SELECTION
    
    def _reinforce_success(self, outcome: Outcome):
        """Reinforce patterns that led to success."""
        if not outcome.tool_used:
            return
        
        # Check if there's an existing pattern for this tool + request type
        for pattern in self.patterns.values():
            if pattern.trigger_conditions.get("tool") == outcome.tool_used:
                # Update success rate
                pattern.times_applied += 1
                old_rate = pattern.success_rate
                pattern.success_rate = (
                    (old_rate * (pattern.times_applied - 1) + 1.0) /
                    pattern.times_applied
                )
                pattern.confidence = min(pattern.confidence * 1.05, 1.0)
                pattern.last_used = datetime.now()
        
        # Save updated patterns
        self._save_patterns()
    
    def _learn_from_correction(
        self,
        original_request: str,
        original_response: str,
        correction: str
    ):
        """Learn from user corrections."""
        # Use AI to understand what was wrong
        system = """Analyze this user correction to understand what went wrong.

Output JSON:
{
    "improvement_area": "intent_understanding|parameter_inference|tool_selection|response_quality",
    "what_was_wrong": "brief description",
    "what_user_wanted": "brief description",
    "learned_pattern": {
        "trigger": "when this happens",
        "correct_action": "do this instead"
    }
}"""
        
        message = f"""Original request: {original_request}

System response: {original_response}

User correction: {correction}"""
        
        try:
            response = self.anthropic.messages.create(
                model=self.model,
                max_tokens=512,
                system=system,
                messages=[{"role": "user", "content": message}]
            )
            
            analysis = json.loads(response.content[0].text)
            
            # Create a learning pattern
            self._create_pattern(
                pattern_type="correction_learned",
                description=analysis.get("what_was_wrong", "Unknown issue"),
                trigger_conditions={
                    "similar_to": original_request[:100],
                    "improvement_area": analysis.get("improvement_area")
                },
                learned_action={
                    "correct_behavior": analysis.get("learned_pattern", {}).get("correct_action"),
                    "avoid": analysis.get("what_was_wrong")
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze correction: {e}")
    
    def _create_pattern(
        self,
        pattern_type: str,
        description: str,
        trigger_conditions: Dict[str, Any],
        learned_action: Dict[str, Any]
    ) -> LearningPattern:
        """Create a new learning pattern."""
        pattern = LearningPattern(
            pattern_id=f"pat_{datetime.now().timestamp()}",
            pattern_type=pattern_type,
            description=description,
            trigger_conditions=trigger_conditions,
            learned_action=learned_action
        )
        
        self.patterns[pattern.pattern_id] = pattern
        self._save_patterns()
        
        logger.info(f"Created learning pattern: {description}")
        return pattern
    
    def get_applicable_patterns(
        self,
        context: Dict[str, Any]
    ) -> List[LearningPattern]:
        """Get patterns that apply to current context."""
        applicable = []
        
        for pattern in self.patterns.values():
            if self._pattern_matches(pattern, context):
                applicable.append(pattern)
        
        # Sort by confidence
        applicable.sort(key=lambda p: p.confidence, reverse=True)
        return applicable
    
    def _pattern_matches(
        self,
        pattern: LearningPattern,
        context: Dict[str, Any]
    ) -> bool:
        """Check if a pattern matches the current context."""
        conditions = pattern.trigger_conditions
        
        # Tool match
        if "tool" in conditions:
            if context.get("tool") != conditions["tool"]:
                return False
        
        # Error contains
        if "error_contains" in conditions:
            error = context.get("error", "").lower()
            if conditions["error_contains"].lower() not in error:
                return False
        
        # Improvement area
        if "improvement_area" in conditions:
            if context.get("improvement_area") != conditions["improvement_area"]:
                return False
        
        return True
    
    def get_improvement_suggestions(self) -> List[ImprovementSuggestion]:
        """Generate improvement suggestions based on recent outcomes."""
        suggestions = []
        
        # Analyze recent failures
        recent_failures = [
            o for o in self.outcomes[-100:]
            if o.outcome_type in [OutcomeType.FAILURE, OutcomeType.ERROR]
        ]
        
        if len(recent_failures) > 10:
            # High failure rate
            failure_tools = {}
            for f in recent_failures:
                if f.tool_used:
                    failure_tools[f.tool_used] = failure_tools.get(f.tool_used, 0) + 1
            
            for tool, count in failure_tools.items():
                if count > 3:
                    suggestions.append(ImprovementSuggestion(
                        area=ImprovementArea.ERROR_HANDLING,
                        description=f"High failure rate for {tool}",
                        priority=8,
                        evidence=[f"{count} failures in recent operations"],
                        suggested_action=f"Review {tool} implementation and error handling"
                    ))
        
        # Analyze user corrections
        corrections = [
            o for o in self.outcomes[-100:]
            if o.outcome_type == OutcomeType.USER_CORRECTION
        ]
        
        if len(corrections) > 5:
            # Frequent corrections indicate misunderstanding
            suggestions.append(ImprovementSuggestion(
                area=ImprovementArea.INTENT_UNDERSTANDING,
                description="Frequent user corrections detected",
                priority=9,
                evidence=[f"{len(corrections)} corrections in recent interactions"],
                suggested_action="Improve intent parsing and ask clarifying questions"
            ))
        
        # Check for slow operations
        slow_ops = [
            o for o in self.outcomes[-100:]
            if o.outcome_type == OutcomeType.SUCCESS
            and o.parameters_used.get("duration_ms", 0) > 30000
        ]
        
        if len(slow_ops) > 5:
            suggestions.append(ImprovementSuggestion(
                area=ImprovementArea.SPEED,
                description="Many slow operations detected",
                priority=5,
                evidence=[f"{len(slow_ops)} operations took over 30 seconds"],
                suggested_action="Consider caching, parallelization, or optimization"
            ))
        
        return sorted(suggestions, key=lambda s: s.priority, reverse=True)
    
    def apply_learned_knowledge(
        self,
        user_request: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply learned knowledge to improve handling of a request."""
        adjustments = {
            "parameter_adjustments": {},
            "warnings": [],
            "suggestions": []
        }
        
        # Find applicable patterns
        patterns = self.get_applicable_patterns(context)
        
        for pattern in patterns[:3]:  # Apply top 3 matching patterns
            learned = pattern.learned_action
            
            if "correct_behavior" in learned:
                adjustments["suggestions"].append(learned["correct_behavior"])
            
            if "avoid" in learned:
                adjustments["warnings"].append(f"Avoid: {learned['avoid']}")
            
            if "params_to_check" in learned:
                adjustments["suggestions"].append(
                    f"Ensure these parameters are provided: {learned['params_to_check']}"
                )
            
            # Track pattern usage
            pattern.times_applied += 1
            pattern.last_used = datetime.now()
        
        # Get relevant historical context
        similar_requests = self._find_similar_requests(user_request)
        
        for req in similar_requests[:3]:
            if req.outcome_type == OutcomeType.SUCCESS:
                # Use successful parameters as defaults
                adjustments["parameter_adjustments"].update(req.parameters_used)
            elif req.outcome_type in [OutcomeType.FAILURE, OutcomeType.ERROR]:
                # Warn about potential issues
                if req.root_cause:
                    adjustments["warnings"].append(
                        f"Previous similar request failed: {req.root_cause}"
                    )
        
        return adjustments
    
    def _find_similar_requests(
        self,
        request: str,
        limit: int = 5
    ) -> List[Outcome]:
        """Find similar past requests."""
        # Simple keyword overlap for now
        request_words = set(request.lower().split())
        
        scored = []
        for outcome in self.outcomes[-200:]:
            outcome_words = set(outcome.user_request.lower().split())
            overlap = len(request_words & outcome_words) / max(len(request_words), 1)
            if overlap > 0.3:
                scored.append((overlap, outcome))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [o for _, o in scored[:limit]]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get improvement statistics."""
        if not self.outcomes:
            return {"message": "No data yet"}
        
        total = len(self.outcomes)
        success_count = sum(
            1 for o in self.outcomes
            if o.outcome_type == OutcomeType.SUCCESS
        )
        failure_count = sum(
            1 for o in self.outcomes
            if o.outcome_type in [OutcomeType.FAILURE, OutcomeType.ERROR]
        )
        
        return {
            "total_operations": total,
            "success_rate": success_count / total if total > 0 else 0,
            "failure_count": failure_count,
            "learned_patterns": len(self.patterns),
            "recent_corrections": sum(
                1 for o in self.outcomes[-50:]
                if o.outcome_type == OutcomeType.USER_CORRECTION
            )
        }


def get_self_improvement_loop(
    anthropic_client: Anthropic,
    data_dir: str = "data/intelligence"
) -> SelfImprovementLoop:
    """Factory function."""
    return SelfImprovementLoop(anthropic_client, data_dir)
