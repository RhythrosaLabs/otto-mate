"""
Intelligent Retry System - Otto Universal
==========================================

Autonomous retry system that:
1. Analyzes failure reasons
2. Determines if retry is worthwhile
3. Adjusts parameters automatically
4. Tries alternative models/approaches
5. Minimizes human intervention

Key Features:
- Failure pattern analysis
- Smart backoff strategies
- Alternative model selection
- Parameter adjustment
- Success prediction
"""

import logging
import asyncio
import time
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class FailureType(str, Enum):
    """Types of failures we can encounter."""
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    INVALID_PARAMS = "invalid_params"
    MODEL_ERROR = "model_error"
    API_ERROR = "api_error"
    AUTH_ERROR = "auth_error"
    QUOTA_EXCEEDED = "quota_exceeded"
    MODEL_UNAVAILABLE = "model_unavailable"
    INVALID_INPUT = "invalid_input"
    SERVER_ERROR = "server_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"


class RetryStrategy(str, Enum):
    """Retry strategies based on failure type."""
    IMMEDIATE = "immediate"  # Try again immediately
    BACKOFF = "backoff"  # Exponential backoff
    ADJUST_PARAMS = "adjust_params"  # Try with different params
    ALTERNATIVE_MODEL = "alternative_model"  # Try different model
    GIVE_UP = "give_up"  # No point retrying


@dataclass
class FailureAnalysis:
    """Analysis of a failure."""
    failure_type: FailureType
    reason: str
    is_retriable: bool
    retry_strategy: RetryStrategy
    suggested_adjustments: Dict[str, Any] = field(default_factory=dict)
    alternative_models: List[str] = field(default_factory=list)
    wait_seconds: float = 0.0
    confidence: float = 0.8


@dataclass
class RetryAttempt:
    """Record of a retry attempt."""
    attempt_number: int
    strategy: RetryStrategy
    adjustments: Dict[str, Any]
    model_used: str
    timestamp: datetime
    success: bool
    error: Optional[str] = None
    duration: float = 0.0


@dataclass
class RetryResult:
    """Result from retry system."""
    success: bool
    final_output: Any
    attempts: List[RetryAttempt]
    total_duration: float
    final_model_used: str
    gave_up_reason: Optional[str] = None


class IntelligentRetrySystem:
    """
    Autonomous retry system with failure analysis and smart recovery.
    
    Features:
    - Analyzes why failures happen
    - Determines best retry strategy
    - Adjusts parameters automatically
    - Tries alternative models
    - Learns from patterns
    """
    
    def __init__(
        self,
        max_retries: int = 5,
        max_total_duration: float = 300.0,  # 5 minutes max
        enable_learning: bool = True
    ):
        self.max_retries = max_retries
        self.max_total_duration = max_total_duration
        self.enable_learning = enable_learning
        
        # Track failure patterns for learning
        self.failure_history: List[Dict[str, Any]] = []
        self.success_patterns: Dict[str, List[Dict]] = {}
        
        # Failure pattern matchers
        self.failure_patterns = {
            FailureType.RATE_LIMIT: [
                "rate limit", "too many requests", "429", "quota", "throttle"
            ],
            FailureType.TIMEOUT: [
                "timeout", "timed out", "time limit", "deadline exceeded"
            ],
            FailureType.INVALID_PARAMS: [
                "invalid parameter", "bad request", "validation error", 
                "missing required", "400"
            ],
            FailureType.MODEL_ERROR: [
                "model error", "model failed", "generation failed",
                "model unavailable", "model overloaded"
            ],
            FailureType.API_ERROR: [
                "api error", "service error", "internal error", "500", "503"
            ],
            FailureType.AUTH_ERROR: [
                "unauthorized", "invalid api key", "authentication", "401", "403"
            ],
            FailureType.QUOTA_EXCEEDED: [
                "quota exceeded", "credit", "insufficient funds", "limit reached"
            ],
            FailureType.MODEL_UNAVAILABLE: [
                "model not found", "model unavailable", "404"
            ],
            FailureType.INVALID_INPUT: [
                "invalid input", "prompt too long", "content filter",
                "nsfw", "safety"
            ],
            FailureType.NETWORK_ERROR: [
                "network", "connection", "dns", "unreachable"
            ],
        }
    
    async def execute_with_retry(
        self,
        operation: Callable,
        operation_args: Dict[str, Any],
        modality: str,
        original_model: str,
        alternative_models: Optional[List[str]] = None,
        model_selector: Optional[Callable] = None
    ) -> RetryResult:
        """
        Execute operation with intelligent retry on failure.
        
        Args:
            operation: Async function to execute
            operation_args: Arguments for the operation
            modality: Modality type (IMAGE, TEXT, etc.)
            original_model: Original model to use
            alternative_models: List of alternative models to try
            model_selector: Function to select alternative models
            
        Returns:
            RetryResult with success status and output
        """
        start_time = time.time()
        attempts: List[RetryAttempt] = []
        current_model = original_model
        current_args = operation_args.copy()
        alternative_models = alternative_models or []
        
        logger.info(f"Starting intelligent retry execution with {current_model}")
        
        for attempt_num in range(1, self.max_retries + 1):
            attempt_start = time.time()
            
            # Check if we've exceeded max duration
            if time.time() - start_time > self.max_total_duration:
                logger.warning("Exceeded maximum retry duration")
                return RetryResult(
                    success=False,
                    final_output=None,
                    attempts=attempts,
                    total_duration=time.time() - start_time,
                    final_model_used=current_model,
                    gave_up_reason="Maximum duration exceeded"
                )
            
            try:
                logger.info(f"Attempt {attempt_num}/{self.max_retries} with {current_model}")
                
                # Execute operation
                result = await operation(**current_args, model=current_model)
                
                # Success!
                duration = time.time() - attempt_start
                logger.info(f"✅ Success on attempt {attempt_num} ({duration:.1f}s)")
                
                attempts.append(RetryAttempt(
                    attempt_number=attempt_num,
                    strategy=RetryStrategy.IMMEDIATE if attempt_num == 1 else RetryStrategy.ALTERNATIVE_MODEL,
                    adjustments=self._get_args_diff(operation_args, current_args),
                    model_used=current_model,
                    timestamp=datetime.now(),
                    success=True,
                    duration=duration
                ))
                
                # Learn from success
                if self.enable_learning and attempt_num > 1:
                    self._record_success_pattern(
                        modality, original_model, current_model, 
                        attempts[-1].strategy, current_args
                    )
                
                return RetryResult(
                    success=True,
                    final_output=result,
                    attempts=attempts,
                    total_duration=time.time() - start_time,
                    final_model_used=current_model
                )
                
            except Exception as e:
                duration = time.time() - attempt_start
                error_msg = str(e)
                
                logger.warning(f"❌ Attempt {attempt_num} failed: {error_msg[:100]}")
                
                # Analyze the failure
                analysis = self._analyze_failure(error_msg, attempt_num, modality)
                
                attempts.append(RetryAttempt(
                    attempt_number=attempt_num,
                    strategy=analysis.retry_strategy,
                    adjustments=self._get_args_diff(operation_args, current_args),
                    model_used=current_model,
                    timestamp=datetime.now(),
                    success=False,
                    error=error_msg,
                    duration=duration
                ))
                
                # Record failure for learning
                self._record_failure(modality, current_model, analysis, error_msg)
                
                # Check if we should give up
                if not analysis.is_retriable or analysis.retry_strategy == RetryStrategy.GIVE_UP:
                    logger.error(f"Giving up: {analysis.reason}")
                    return RetryResult(
                        success=False,
                        final_output=None,
                        attempts=attempts,
                        total_duration=time.time() - start_time,
                        final_model_used=current_model,
                        gave_up_reason=analysis.reason
                    )
                
                # Last attempt?
                if attempt_num >= self.max_retries:
                    logger.error("Max retries reached")
                    return RetryResult(
                        success=False,
                        final_output=None,
                        attempts=attempts,
                        total_duration=time.time() - start_time,
                        final_model_used=current_model,
                        gave_up_reason="Maximum retries exceeded"
                    )
                
                # Apply retry strategy
                logger.info(f"Applying strategy: {analysis.retry_strategy.value}")
                
                if analysis.retry_strategy == RetryStrategy.BACKOFF:
                    # Wait before retrying
                    wait_time = analysis.wait_seconds or (2 ** attempt_num)
                    logger.info(f"Waiting {wait_time:.1f}s before retry...")
                    await asyncio.sleep(wait_time)
                
                elif analysis.retry_strategy == RetryStrategy.ADJUST_PARAMS:
                    # Adjust parameters
                    current_args.update(analysis.suggested_adjustments)
                    logger.info(f"Adjusted parameters: {analysis.suggested_adjustments}")
                
                elif analysis.retry_strategy == RetryStrategy.ALTERNATIVE_MODEL:
                    # Try alternative model
                    new_model = self._select_alternative_model(
                        modality, current_model, alternative_models,
                        analysis, model_selector
                    )
                    
                    if new_model and new_model != current_model:
                        logger.info(f"Switching to alternative model: {new_model}")
                        current_model = new_model
                        # Reset args for new model
                        current_args = operation_args.copy()
                    else:
                        logger.warning("No alternative model available, using backoff")
                        await asyncio.sleep(2 ** attempt_num)
                
                # Continue to next attempt
                continue
        
        # Should not reach here, but just in case
        return RetryResult(
            success=False,
            final_output=None,
            attempts=attempts,
            total_duration=time.time() - start_time,
            final_model_used=current_model,
            gave_up_reason="Unexpected exit from retry loop"
        )
    
    def _analyze_failure(
        self, 
        error_msg: str, 
        attempt_num: int,
        modality: str
    ) -> FailureAnalysis:
        """
        Analyze failure and determine retry strategy.
        
        Uses pattern matching and historical data to understand
        why the failure occurred and how to fix it.
        """
        error_lower = error_msg.lower()
        
        # Detect failure type
        failure_type = FailureType.UNKNOWN
        for ftype, patterns in self.failure_patterns.items():
            if any(pattern in error_lower for pattern in patterns):
                failure_type = ftype
                break
        
        logger.info(f"Detected failure type: {failure_type.value}")
        
        # Determine retry strategy based on failure type
        if failure_type == FailureType.RATE_LIMIT:
            wait_time = min(2 ** (attempt_num + 2), 60)  # Max 60s
            return FailureAnalysis(
                failure_type=failure_type,
                reason="Rate limit hit, will retry with backoff",
                is_retriable=True,
                retry_strategy=RetryStrategy.BACKOFF,
                wait_seconds=wait_time,
                confidence=0.95
            )
        
        elif failure_type == FailureType.TIMEOUT:
            return FailureAnalysis(
                failure_type=failure_type,
                reason="Request timed out, will retry with adjusted timeout",
                is_retriable=True,
                retry_strategy=RetryStrategy.ADJUST_PARAMS,
                suggested_adjustments={"timeout": 120, "max_wait": 180},
                confidence=0.85
            )
        
        elif failure_type == FailureType.INVALID_PARAMS:
            # Try to extract what parameter was invalid
            adjustments = {}
            
            if "prompt too long" in error_lower or "max tokens" in error_lower:
                adjustments["max_tokens"] = 4000
                adjustments["truncate_prompt"] = True
            
            if "negative_prompt" in error_lower:
                adjustments.pop("negative_prompt", None)
            
            return FailureAnalysis(
                failure_type=failure_type,
                reason="Invalid parameters, will adjust and retry",
                is_retriable=True,
                retry_strategy=RetryStrategy.ADJUST_PARAMS,
                suggested_adjustments=adjustments,
                confidence=0.7
            )
        
        elif failure_type == FailureType.MODEL_ERROR:
            return FailureAnalysis(
                failure_type=failure_type,
                reason="Model error, will try alternative model",
                is_retriable=True,
                retry_strategy=RetryStrategy.ALTERNATIVE_MODEL,
                confidence=0.8
            )
        
        elif failure_type == FailureType.MODEL_UNAVAILABLE:
            return FailureAnalysis(
                failure_type=failure_type,
                reason="Model unavailable, trying alternative",
                is_retriable=True,
                retry_strategy=RetryStrategy.ALTERNATIVE_MODEL,
                confidence=0.9
            )
        
        elif failure_type == FailureType.AUTH_ERROR:
            return FailureAnalysis(
                failure_type=failure_type,
                reason="Authentication failed - check API keys",
                is_retriable=False,
                retry_strategy=RetryStrategy.GIVE_UP,
                confidence=1.0
            )
        
        elif failure_type == FailureType.QUOTA_EXCEEDED:
            return FailureAnalysis(
                failure_type=failure_type,
                reason="Quota exceeded, trying alternative model",
                is_retriable=True,
                retry_strategy=RetryStrategy.ALTERNATIVE_MODEL,
                confidence=0.9
            )
        
        elif failure_type == FailureType.INVALID_INPUT:
            # Content filter or safety issues
            adjustments = {
                "prompt_filter": True,
                "safety_level": "high"
            }
            return FailureAnalysis(
                failure_type=failure_type,
                reason="Input triggered safety filter, adjusting",
                is_retriable=True,
                retry_strategy=RetryStrategy.ADJUST_PARAMS,
                suggested_adjustments=adjustments,
                confidence=0.6
            )
        
        elif failure_type == FailureType.SERVER_ERROR or failure_type == FailureType.API_ERROR:
            return FailureAnalysis(
                failure_type=failure_type,
                reason="Server error, will retry with backoff",
                is_retriable=True,
                retry_strategy=RetryStrategy.BACKOFF,
                wait_seconds=min(2 ** attempt_num, 30),
                confidence=0.7
            )
        
        elif failure_type == FailureType.NETWORK_ERROR:
            return FailureAnalysis(
                failure_type=failure_type,
                reason="Network error, will retry immediately",
                is_retriable=True,
                retry_strategy=RetryStrategy.IMMEDIATE,
                confidence=0.8
            )
        
        else:
            # Unknown error - be conservative
            return FailureAnalysis(
                failure_type=FailureType.UNKNOWN,
                reason="Unknown error, trying alternative approach",
                is_retriable=True,
                retry_strategy=RetryStrategy.ALTERNATIVE_MODEL if attempt_num <= 2 else RetryStrategy.BACKOFF,
                wait_seconds=2 ** attempt_num,
                confidence=0.5
            )
    
    def _select_alternative_model(
        self,
        modality: str,
        current_model: str,
        alternative_models: List[str],
        analysis: FailureAnalysis,
        model_selector: Optional[Callable]
    ) -> Optional[str]:
        """
        Select an alternative model to try.
        
        Considers:
        - Available alternatives
        - Historical success patterns
        - Failure type
        """
        # Remove current model from alternatives
        alternatives = [m for m in alternative_models if m != current_model]
        
        if not alternatives and model_selector:
            # Try to get alternatives from model selector
            try:
                alternatives = model_selector(modality, exclude=[current_model])
            except Exception as e:
                logger.warning(f"Model selector failed: {e}")
                return None
        
        if not alternatives:
            logger.warning("No alternative models available")
            return None
        
        # Check historical success patterns
        if self.enable_learning and modality in self.success_patterns:
            patterns = self.success_patterns[modality]
            
            # Find models that succeeded after similar failures
            successful_alternatives = [
                p["successful_model"] 
                for p in patterns 
                if p["failed_model"] == current_model 
                and p["successful_model"] in alternatives
            ]
            
            if successful_alternatives:
                # Use most common successful alternative
                from collections import Counter
                most_common = Counter(successful_alternatives).most_common(1)[0][0]
                logger.info(f"Using historically successful alternative: {most_common}")
                return most_common
        
        # Default to first alternative
        logger.info(f"Trying first alternative: {alternatives[0]}")
        return alternatives[0]
    
    def _record_failure(
        self,
        modality: str,
        model: str,
        analysis: FailureAnalysis,
        error_msg: str
    ):
        """Record failure for learning."""
        if not self.enable_learning:
            return
        
        self.failure_history.append({
            "timestamp": datetime.now(),
            "modality": modality,
            "model": model,
            "failure_type": analysis.failure_type.value,
            "error_msg": error_msg[:200],
            "strategy": analysis.retry_strategy.value
        })
        
        # Keep only recent history
        if len(self.failure_history) > 1000:
            self.failure_history = self.failure_history[-1000:]
    
    def _record_success_pattern(
        self,
        modality: str,
        failed_model: str,
        successful_model: str,
        strategy: RetryStrategy,
        args: Dict[str, Any]
    ):
        """Record successful retry pattern for learning."""
        if not self.enable_learning:
            return
        
        if modality not in self.success_patterns:
            self.success_patterns[modality] = []
        
        self.success_patterns[modality].append({
            "timestamp": datetime.now(),
            "failed_model": failed_model,
            "successful_model": successful_model,
            "strategy": strategy.value,
            "args": str(args)[:200]
        })
        
        # Keep only recent patterns
        if len(self.success_patterns[modality]) > 100:
            self.success_patterns[modality] = self.success_patterns[modality][-100:]
    
    def _get_args_diff(self, original: Dict, current: Dict) -> Dict:
        """Get differences between original and current args."""
        diff = {}
        for key, value in current.items():
            if key not in original or original[key] != value:
                diff[key] = value
        return diff
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retry system statistics."""
        if not self.failure_history:
            return {"total_failures": 0}
        
        from collections import Counter
        
        failure_types = Counter(f["failure_type"] for f in self.failure_history)
        models_failed = Counter(f["model"] for f in self.failure_history)
        
        total_successes = sum(
            len(patterns) for patterns in self.success_patterns.values()
        )
        
        return {
            "total_failures": len(self.failure_history),
            "total_successes_after_retry": total_successes,
            "failure_types": dict(failure_types),
            "models_failed": dict(models_failed),
            "success_patterns": {
                k: len(v) for k, v in self.success_patterns.items()
            }
        }


# =============================================================================
# Singleton Access
# =============================================================================

_retry_system: Optional[IntelligentRetrySystem] = None


def get_retry_system(
    max_retries: int = 5,
    max_total_duration: float = 300.0,
    enable_learning: bool = True
) -> IntelligentRetrySystem:
    """Get or create the intelligent retry system singleton."""
    global _retry_system
    if _retry_system is None:
        _retry_system = IntelligentRetrySystem(
            max_retries=max_retries,
            max_total_duration=max_total_duration,
            enable_learning=enable_learning
        )
    return _retry_system
