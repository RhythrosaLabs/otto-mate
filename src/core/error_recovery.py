"""
Enhanced Error Recovery System
===============================

Provides intelligent error recovery patterns and retry strategies for agents.

Features:
- Circuit breaker pattern for failing services
- Exponential backoff with jitter
- Fallback strategies
- Error classification and handling
- Automatic parameter fixing
- Context-aware recovery
"""

import logging
import asyncio
import random
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    TRANSIENT = "transient"  # Temporary, retry immediately
    RATE_LIMIT = "rate_limit"  # Rate limited, back off
    CLIENT_ERROR = "client_error"  # Bad request, fix parameters
    SERVER_ERROR = "server_error"  # Server issue, retry with backoff
    FATAL = "fatal"  # Unrecoverable, don't retry


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class ErrorPattern:
    """Pattern for matching and handling errors."""
    pattern: str  # Error message pattern
    severity: ErrorSeverity
    retry_strategy: str  # "immediate", "backoff", "none"
    max_retries: int = 3
    backoff_base: float = 1.0  # Base delay in seconds
    backoff_max: float = 60.0  # Max delay in seconds
    fix_hint: Optional[str] = None  # Hint for fixing the error


# Predefined error patterns
ERROR_PATTERNS = [
    # Transient errors - retry immediately
    ErrorPattern(
        pattern="connection timeout|timeout error|connection reset",
        severity=ErrorSeverity.TRANSIENT,
        retry_strategy="immediate",
        max_retries=3
    ),
    
    # Rate limiting - exponential backoff
    ErrorPattern(
        pattern="rate limit|too many requests|429",
        severity=ErrorSeverity.RATE_LIMIT,
        retry_strategy="backoff",
        max_retries=5,
        backoff_base=2.0,
        backoff_max=120.0
    ),
    
    # Printify specific errors
    ErrorPattern(
        pattern="10300|invalid blueprint_id",
        severity=ErrorSeverity.CLIENT_ERROR,
        retry_strategy="none",
        fix_hint="Use blueprint_id: 6 for t-shirts or 11 for mugs"
    ),
    
    # Parameter errors - fix and retry
    ErrorPattern(
        pattern="missing required|invalid parameter|parameter .* is required",
        severity=ErrorSeverity.CLIENT_ERROR,
        retry_strategy="none",
        fix_hint="Check parameter requirements and provide defaults"
    ),
    
    # Server errors - retry with backoff
    ErrorPattern(
        pattern="500|502|503|504|internal server error|service unavailable",
        severity=ErrorSeverity.SERVER_ERROR,
        retry_strategy="backoff",
        max_retries=4,
        backoff_base=1.5
    ),
    
    # Authentication errors - fatal
    ErrorPattern(
        pattern="unauthorized|invalid api key|authentication failed",
        severity=ErrorSeverity.FATAL,
        retry_strategy="none",
        fix_hint="Check API key configuration"
    ),
]


@dataclass
class CircuitBreaker:
    """Circuit breaker for failing services."""
    service_name: str
    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes to close from half-open
    timeout_seconds: float = 60.0  # Time before trying half-open
    
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_state_change: datetime = field(default_factory=datetime.now)
    
    def record_success(self):
        """Record a successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self._close_circuit()
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    def record_failure(self):
        """Record a failed call."""
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            self._open_circuit()
        elif self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self._open_circuit()
    
    def can_execute(self) -> bool:
        """Check if execution is allowed."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if self.last_failure_time:
                time_since_failure = (datetime.now() - self.last_failure_time).total_seconds()
                if time_since_failure >= self.timeout_seconds:
                    self._half_open_circuit()
                    return True
            return False
        
        # HALF_OPEN - allow limited requests
        return True
    
    def _open_circuit(self):
        """Open the circuit (stop requests)."""
        logger.warning(f"Circuit breaker opened for {self.service_name}")
        self.state = CircuitState.OPEN
        self.last_state_change = datetime.now()
        self.success_count = 0
    
    def _half_open_circuit(self):
        """Half-open the circuit (test recovery)."""
        logger.info(f"Circuit breaker half-open for {self.service_name}")
        self.state = CircuitState.HALF_OPEN
        self.last_state_change = datetime.now()
        self.success_count = 0
    
    def _close_circuit(self):
        """Close the circuit (resume normal operation)."""
        logger.info(f"Circuit breaker closed for {self.service_name}")
        self.state = CircuitState.CLOSED
        self.last_state_change = datetime.now()
        self.failure_count = 0
        self.success_count = 0


class ErrorRecoveryManager:
    """
    Manages error recovery strategies for agents.
    
    Features:
    - Error pattern matching and classification
    - Intelligent retry strategies
    - Circuit breaker pattern
    - Automatic parameter fixing
    - Fallback strategy selection
    """
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_history: List[Dict[str, Any]] = []
        self.recovery_strategies: Dict[str, Callable] = {}
        
        # Register default recovery strategies
        self._register_default_strategies()
        
        logger.info("Error Recovery Manager initialized")
    
    def _register_default_strategies(self):
        """Register default recovery strategies."""
        self.recovery_strategies["printify_blueprint_fix"] = self._fix_printify_blueprint
        self.recovery_strategies["parameter_defaults"] = self._add_parameter_defaults
        self.recovery_strategies["image_format_conversion"] = self._convert_image_format
    
    def classify_error(self, error_message: str) -> Tuple[ErrorSeverity, Optional[ErrorPattern]]:
        """Classify an error and determine severity."""
        error_lower = error_message.lower()
        
        for pattern in ERROR_PATTERNS:
            import re
            if re.search(pattern.pattern, error_lower):
                return pattern.severity, pattern
        
        # Default to server error if unknown
        return ErrorSeverity.SERVER_ERROR, None
    
    def should_retry(
        self,
        error_message: str,
        attempt: int,
        service_name: str
    ) -> Tuple[bool, float]:
        """
        Determine if an error should be retried and calculate delay.
        
        Returns:
            (should_retry, delay_seconds)
        """
        severity, pattern = self.classify_error(error_message)
        
        # Check circuit breaker
        circuit = self._get_circuit_breaker(service_name)
        if not circuit.can_execute():
            logger.warning(f"Circuit breaker open for {service_name}, not retrying")
            return False, 0.0
        
        # Fatal errors - don't retry
        if severity == ErrorSeverity.FATAL:
            return False, 0.0
        
        # Check retry limit
        if pattern and attempt >= pattern.max_retries:
            return False, 0.0
        
        # Calculate delay based on strategy
        delay = 0.0
        if pattern:
            if pattern.retry_strategy == "immediate":
                delay = 0.1
            elif pattern.retry_strategy == "backoff":
                delay = self._calculate_backoff(
                    attempt,
                    pattern.backoff_base,
                    pattern.backoff_max
                )
            elif pattern.retry_strategy == "none":
                return False, 0.0
        else:
            # Default backoff for unknown errors
            delay = self._calculate_backoff(attempt, 1.0, 30.0)
        
        return True, delay
    
    def _calculate_backoff(
        self,
        attempt: int,
        base: float,
        max_delay: float
    ) -> float:
        """Calculate exponential backoff with jitter."""
        delay = min(base * (2 ** attempt), max_delay)
        # Add jitter (±25%)
        jitter = delay * 0.25 * (2 * random.random() - 1)
        return max(0.1, delay + jitter)
    
    def _get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for a service."""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker(service_name)
        return self.circuit_breakers[service_name]
    
    def record_execution(
        self,
        service_name: str,
        success: bool,
        error_message: Optional[str] = None
    ):
        """Record an execution result for circuit breaker."""
        circuit = self._get_circuit_breaker(service_name)
        
        if success:
            circuit.record_success()
        else:
            circuit.record_failure()
            
            # Record in history
            self.error_history.append({
                "service": service_name,
                "error": error_message,
                "timestamp": datetime.now().isoformat(),
                "circuit_state": circuit.state.value
            })
            
            # Keep only recent history
            if len(self.error_history) > 100:
                self.error_history = self.error_history[-100:]
    
    async def execute_with_recovery(
        self,
        service_name: str,
        func: Callable,
        *args,
        max_retries: int = 3,
        **kwargs
    ) -> Tuple[bool, Any, Optional[str]]:
        """
        Execute a function with automatic error recovery.
        
        Returns:
            (success, result, error_message)
        """
        circuit = self._get_circuit_breaker(service_name)
        
        if not circuit.can_execute():
            return False, None, f"Circuit breaker open for {service_name}"
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Execute function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Success
                self.record_execution(service_name, True)
                return True, result, None
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {last_error}")
                
                # Classify error
                severity, pattern = self.classify_error(last_error)
                
                # Check if should retry
                should_retry, delay = self.should_retry(last_error, attempt, service_name)
                
                if not should_retry:
                    logger.error(f"Not retrying {service_name}: {severity.value}")
                    self.record_execution(service_name, False, last_error)
                    return False, None, last_error
                
                # Try to fix parameters if client error
                if severity == ErrorSeverity.CLIENT_ERROR and pattern and pattern.fix_hint:
                    logger.info(f"Attempting to fix parameters: {pattern.fix_hint}")
                    # TODO: Implement parameter fixing
                
                # Wait before retry
                if delay > 0:
                    logger.info(f"Waiting {delay:.2f}s before retry")
                    await asyncio.sleep(delay)
        
        # All retries failed
        self.record_execution(service_name, False, last_error)
        return False, None, last_error
    
    def _fix_printify_blueprint(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Fix Printify blueprint parameters."""
        fixed = parameters.copy()
        
        # Use default blueprint if missing or invalid
        if "blueprint_id" not in fixed or fixed["blueprint_id"] is None:
            fixed["blueprint_id"] = 6  # T-shirt default
        
        return fixed
    
    def _add_parameter_defaults(self, parameters: Dict[str, Any], required: List[str]) -> Dict[str, Any]:
        """Add missing required parameters with defaults."""
        fixed = parameters.copy()
        
        defaults = {
            "size": "medium",
            "color": "black",
            "style": "professional",
            "format": "png",
            "quality": "high",
            "width": 1024,
            "height": 1024
        }
        
        for param in required:
            if param not in fixed:
                if param in defaults:
                    fixed[param] = defaults[param]
                    logger.info(f"Added default for {param}: {defaults[param]}")
        
        return fixed
    
    def _convert_image_format(self, image_url: str, target_format: str = "png") -> str:
        """Convert image format (placeholder for actual implementation)."""
        # This would integrate with an image conversion service
        logger.info(f"Would convert {image_url} to {target_format}")
        return image_url
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get recovery statistics."""
        return {
            "circuit_breakers": {
                name: {
                    "state": cb.state.value,
                    "failure_count": cb.failure_count,
                    "success_count": cb.success_count,
                    "last_state_change": cb.last_state_change.isoformat()
                }
                for name, cb in self.circuit_breakers.items()
            },
            "recent_errors": self.error_history[-10:],
            "total_errors": len(self.error_history)
        }


# Singleton instance
_recovery_manager: Optional[ErrorRecoveryManager] = None


def get_recovery_manager() -> ErrorRecoveryManager:
    """Get the global error recovery manager."""
    global _recovery_manager
    if _recovery_manager is None:
        _recovery_manager = ErrorRecoveryManager()
    return _recovery_manager
