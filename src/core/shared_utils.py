"""
Otto Universal - Shared Utilities
=================================

Common patterns and utilities used across all agents and tools.
Centralizes retry logic, error handling, and other shared functionality.
"""

import asyncio
import logging
import functools
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ============================================================================
# Error Handling
# ============================================================================

class RetryableError(Exception):
    """An error that should be retried."""
    pass


class NonRetryableError(Exception):
    """An error that should NOT be retried."""
    pass


@dataclass
class ExecutionResult:
    """Standardized result from any execution."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    retryable: bool = False
    duration_ms: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "error_type": self.error_type,
            "retryable": self.retryable,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata
        }


# ============================================================================
# Retry Logic
# ============================================================================

# Errors that should be retried
RETRYABLE_ERRORS = {
    "rate_limit", "timeout", "connection", "temporary", 
    "service_unavailable", "502", "503", "504", "429"
}

# Errors that should NOT be retried
NON_RETRYABLE_ERRORS = {
    "invalid_api_key", "unauthorized", "forbidden", "not_found",
    "bad_request", "invalid_parameter", "401", "403", "404"
}


def is_retryable_error(error: Union[str, Exception]) -> bool:
    """Determine if an error should be retried."""
    error_str = str(error).lower()
    
    # Check for non-retryable first (takes precedence)
    for keyword in NON_RETRYABLE_ERRORS:
        if keyword in error_str:
            return False
    
    # Check for retryable
    for keyword in RETRYABLE_ERRORS:
        if keyword in error_str:
            return True
    
    # Default: retry on ambiguous errors
    return True


async def retry_with_backoff(
    func: Callable,
    *args,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    retryable_check: Optional[Callable[[Exception], bool]] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
    **kwargs
) -> ExecutionResult:
    """
    Execute a function with exponential backoff retry.
    
    Args:
        func: Async function to execute
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        backoff_factor: Multiplier for each retry
        retryable_check: Optional function to check if error is retryable
        on_retry: Optional callback when retry occurs
        *args, **kwargs: Arguments to pass to func
        
    Returns:
        ExecutionResult with success/failure and data
    """
    check_retryable = retryable_check or is_retryable_error
    delay = initial_delay
    last_error = None
    start_time = datetime.now()
    
    for attempt in range(max_retries + 1):
        try:
            result = await func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds() * 1000
            
            return ExecutionResult(
                success=True,
                data=result,
                duration_ms=duration,
                metadata={"attempts": attempt + 1}
            )
            
        except Exception as e:
            last_error = e
            
            # Check if we should retry
            if attempt < max_retries and check_retryable(e):
                if on_retry:
                    on_retry(attempt + 1, e)
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
                delay = min(delay * backoff_factor, max_delay)
            else:
                break
    
    duration = (datetime.now() - start_time).total_seconds() * 1000
    return ExecutionResult(
        success=False,
        error=str(last_error),
        error_type=type(last_error).__name__,
        retryable=check_retryable(last_error) if last_error else False,
        duration_ms=duration,
        metadata={"attempts": max_retries + 1}
    )


def with_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    retryable_exceptions: Optional[tuple] = None
):
    """
    Decorator to add retry logic to an async function.
    
    Usage:
        @with_retry(max_retries=3)
        async def my_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            result = await retry_with_backoff(
                func,
                *args,
                max_retries=max_retries,
                initial_delay=initial_delay,
                **kwargs
            )
            if result.success:
                return result.data
            raise Exception(result.error)
        return wrapper
    return decorator


# ============================================================================
# Fallback Strategies
# ============================================================================

class FallbackStrategy:
    """Defines a fallback strategy for when primary operations fail."""
    
    def __init__(
        self,
        name: str,
        primary_tool: str,
        fallback_tools: List[str],
        condition: Optional[Callable[[Exception], bool]] = None
    ):
        self.name = name
        self.primary_tool = primary_tool
        self.fallback_tools = fallback_tools
        self.condition = condition or (lambda e: True)
    
    def should_fallback(self, error: Exception) -> bool:
        """Check if fallback should be attempted."""
        return self.condition(error)
    
    def get_next_fallback(self, failed_tools: List[str]) -> Optional[str]:
        """Get the next fallback tool to try."""
        for tool in self.fallback_tools:
            if tool not in failed_tools:
                return tool
        return None


# Default fallback strategies
DEFAULT_FALLBACK_STRATEGIES = {
    "image_generation": FallbackStrategy(
        name="Image Generation Fallback",
        primary_tool="replicate_smart_generate",
        fallback_tools=["generate_image", "flux_schnell", "flux_pro"]
    ),
    "product_creation": FallbackStrategy(
        name="Product Creation Fallback",
        primary_tool="printify_create_product",
        fallback_tools=["printify_create_tshirt", "printify_create_mug"]
    ),
    "research": FallbackStrategy(
        name="Research Fallback",
        primary_tool="search_web",
        fallback_tools=["browse_url", "research_topic"]
    ),
    "code_execution": FallbackStrategy(
        name="Code Execution Fallback",
        primary_tool="execute_python",
        fallback_tools=["execute_shell", "run_code_snippet"]
    )
}


# ============================================================================
# Artifact Collection
# ============================================================================

class ArtifactType(Enum):
    """Types of artifacts that can be collected."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    CODE = "code"
    TEXT = "text"
    FILE = "file"
    DATA = "data"
    PRODUCT = "product"
    LINK = "link"


@dataclass
class Artifact:
    """A collected artifact from execution."""
    id: str
    type: ArtifactType
    content: Any
    title: str = ""
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "title": self.title,
            "description": self.description,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


class ArtifactCollector:
    """Collects and manages artifacts from execution."""
    
    def __init__(self):
        self.artifacts: List[Artifact] = []
    
    def add(self, artifact: Artifact):
        """Add an artifact."""
        self.artifacts.append(artifact)
    
    def add_from_result(self, result: Dict[str, Any], step_name: str = "") -> List[Artifact]:
        """Extract and add artifacts from a tool result."""
        new_artifacts = []
        
        # Check for image URLs
        for key in ["image_url", "output_url", "url", "image", "generated_image"]:
            if key in result and result[key]:
                url = result[key]
                if isinstance(url, str) and (url.startswith("http") or url.startswith("data:")):
                    artifact = Artifact(
                        id=f"img_{len(self.artifacts)}",
                        type=ArtifactType.IMAGE,
                        content=url,
                        title=step_name or "Generated Image",
                        metadata={"source_key": key}
                    )
                    self.add(artifact)
                    new_artifacts.append(artifact)
        
        # Check for video URLs
        for key in ["video_url", "video", "mp4_url"]:
            if key in result and result[key]:
                artifact = Artifact(
                    id=f"vid_{len(self.artifacts)}",
                    type=ArtifactType.VIDEO,
                    content=result[key],
                    title=step_name or "Generated Video"
                )
                self.add(artifact)
                new_artifacts.append(artifact)
        
        # Check for code
        if "code" in result and result["code"]:
            artifact = Artifact(
                id=f"code_{len(self.artifacts)}",
                type=ArtifactType.CODE,
                content=result["code"],
                title=step_name or "Generated Code",
                metadata={"language": result.get("language", "python")}
            )
            self.add(artifact)
            new_artifacts.append(artifact)
        
        # Check for product IDs
        for key in ["product_id", "printify_product_id", "shopify_product_id"]:
            if key in result and result[key]:
                artifact = Artifact(
                    id=f"product_{len(self.artifacts)}",
                    type=ArtifactType.PRODUCT,
                    content=result[key],
                    title=step_name or "Created Product",
                    metadata={"platform": "printify" if "printify" in key else "shopify"}
                )
                self.add(artifact)
                new_artifacts.append(artifact)
        
        return new_artifacts
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all artifacts as dicts."""
        return [a.to_dict() for a in self.artifacts]
    
    def get_by_type(self, artifact_type: ArtifactType) -> List[Artifact]:
        """Get artifacts filtered by type."""
        return [a for a in self.artifacts if a.type == artifact_type]
    
    def clear(self):
        """Clear all artifacts."""
        self.artifacts = []


# ============================================================================
# Context Management
# ============================================================================

@dataclass
class ExecutionContext:
    """Context passed between execution steps."""
    session_id: str
    user_message: str
    variables: Dict[str, Any] = field(default_factory=dict)
    step_results: List[Dict[str, Any]] = field(default_factory=list)
    artifacts: ArtifactCollector = field(default_factory=ArtifactCollector)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def set_variable(self, name: str, value: Any):
        """Set a context variable."""
        self.variables[name] = value
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a context variable."""
        return self.variables.get(name, default)
    
    def add_step_result(self, step_name: str, result: Dict[str, Any]):
        """Add a step result and extract artifacts."""
        self.step_results.append({"step": step_name, "result": result})
        self.artifacts.add_from_result(result, step_name)
        
        # Auto-populate common variables from results
        for key in ["image_url", "output_url", "product_id", "file_url"]:
            if key in result:
                self.set_variable(f"last_{key}", result[key])
    
    def resolve_parameter(self, value: Any) -> Any:
        """Resolve parameter value, substituting variables."""
        if not isinstance(value, str):
            return value
        
        # Check for variable references like {variable_name} or {step_0.output_url}
        import re
        pattern = r'\{([^}]+)\}'
        
        def replace_var(match):
            var_name = match.group(1)
            
            # Check for step references like "step_0.output_url"
            if var_name.startswith("step_") and "." in var_name:
                parts = var_name.split(".", 1)
                step_idx = int(parts[0].replace("step_", ""))
                key = parts[1]
                if step_idx < len(self.step_results):
                    return str(self.step_results[step_idx].get("result", {}).get(key, ""))
            
            # Check for direct variables
            if var_name in self.variables:
                return str(self.variables[var_name])
            
            return match.group(0)  # Keep original if not found
        
        return re.sub(pattern, replace_var, value)


# ============================================================================
# Logging Utilities
# ============================================================================

def log_execution(tool_name: str, params: Dict[str, Any], result: ExecutionResult):
    """Log tool execution with consistent format."""
    if result.success:
        logger.info(
            f"✅ {tool_name} succeeded in {result.duration_ms:.0f}ms "
            f"(attempts: {result.metadata.get('attempts', 1)})"
        )
    else:
        logger.warning(
            f"❌ {tool_name} failed: {result.error} "
            f"(retryable: {result.retryable})"
        )


def sanitize_for_logging(data: Any, max_length: int = 500) -> Any:
    """Sanitize data for logging (truncate long values, hide secrets)."""
    if isinstance(data, str):
        # Hide potential secrets
        if any(keyword in data.lower() for keyword in ["key", "token", "secret", "password"]):
            return "[REDACTED]"
        return data[:max_length] + "..." if len(data) > max_length else data
    
    if isinstance(data, dict):
        return {k: sanitize_for_logging(v, max_length) for k, v in data.items()}
    
    if isinstance(data, list):
        return [sanitize_for_logging(item, max_length) for item in data[:10]]
    
    return data
