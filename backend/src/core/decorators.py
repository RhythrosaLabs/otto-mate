"""Tool decorator system for automatic tool registration."""
from typing import Callable, Dict, Any, List, Optional
from functools import wraps
import inspect
from datetime import datetime


# Global registry
_registered_tools: List[Dict[str, Any]] = []


def otto_tool(
    name: str,
    description: str,
    category: str,
    parameters: Optional[Dict[str, Any]] = None,
    enabled: bool = True
):
    """
    Decorator for registering Otto tools.
    
    Automatically registers the function as a tool that can be discovered
    and executed by agents.
    
    Usage:
        @otto_tool(
            name="generate_design",
            description="Generate a design using AI",
            category="ai_models",
            parameters={
                "prompt": {"type": "string", "required": True, "description": "Design prompt"},
                "style": {"type": "string", "required": False, "default": "modern"}
            }
        )
        async def generate_design(prompt: str, style: str = "modern"):
            # Implementation
            return {"design_url": "..."}
    
    Args:
        name: Tool name (unique identifier)
        description: Human-readable description
        category: Tool category (ai_models, data_analysis, etc.)
        parameters: Parameter schema (optional - can be inferred)
        enabled: Whether tool is enabled
    
    Returns:
        Decorated function with tool metadata
    """
    def decorator(func: Callable):
        # Create wrapper that preserves async/sync
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            wrapper = async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            wrapper = sync_wrapper
        
        # Auto-infer parameters if not provided
        tool_parameters = parameters or _infer_parameters(func)
        
        # Attach metadata
        wrapper._is_otto_tool = True
        wrapper._tool_metadata = {
            "name": name,
            "description": description,
            "category": category,
            "parameters": tool_parameters,
            "enabled": enabled,
            "function": wrapper,
            "registered_at": datetime.now().isoformat()
        }
        
        # Auto-register
        _registered_tools.append(wrapper._tool_metadata)
        
        return wrapper
    
    return decorator


def get_registered_tools() -> List[Dict[str, Any]]:
    """
    Get all registered tools.
    
    Returns:
        List of tool metadata dictionaries
    """
    return [
        {
            "name": tool["name"],
            "description": tool["description"],
            "category": tool["category"],
            "parameters": tool["parameters"],
            "enabled": tool["enabled"],
            "function": tool["function"]
        }
        for tool in _registered_tools
    ]


def get_tool_by_name(name: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific tool by name.
    
    Args:
        name: Tool name
        
    Returns:
        Tool metadata or None if not found
    """
    for tool in _registered_tools:
        if tool["name"] == name:
            return tool
    return None


def get_tools_by_category(category: str) -> List[Dict[str, Any]]:
    """
    Get all tools in a category.
    
    Args:
        category: Tool category
        
    Returns:
        List of tool metadata dictionaries
    """
    return [
        tool for tool in _registered_tools
        if tool["category"] == category
    ]


def clear_registry():
    """Clear all registered tools (useful for testing)."""
    global _registered_tools
    _registered_tools = []


def _infer_parameters(func: Callable) -> Dict[str, Any]:
    """
    Infer parameter schema from function signature.
    
    Args:
        func: Function to inspect
        
    Returns:
        Parameter schema dictionary
    """
    sig = inspect.signature(func)
    parameters = {}
    
    for param_name, param in sig.parameters.items():
        # Skip self/cls parameters
        if param_name in ("self", "cls"):
            continue
        
        # Determine type
        param_type = "string"  # Default
        if param.annotation != inspect.Parameter.empty:
            annotation = param.annotation
            if annotation in (int, "int"):
                param_type = "integer"
            elif annotation in (float, "float"):
                param_type = "number"
            elif annotation in (bool, "bool"):
                param_type = "boolean"
            elif annotation in (list, List):
                param_type = "array"
            elif annotation in (dict, Dict):
                param_type = "object"
        
        # Determine if required
        required = param.default == inspect.Parameter.empty
        
        # Build parameter schema
        param_schema = {
            "type": param_type,
            "required": required
        }
        
        if not required:
            param_schema["default"] = param.default
        
        parameters[param_name] = param_schema
    
    return parameters


# Convenience decorators for common categories
def ai_model_tool(name: str, description: str, **kwargs):
    """Decorator for AI model tools."""
    return otto_tool(name, description, "ai_models", **kwargs)


def data_analysis_tool(name: str, description: str, **kwargs):
    """Decorator for data analysis tools."""
    return otto_tool(name, description, "data_analysis", **kwargs)


def content_creation_tool(name: str, description: str, **kwargs):
    """Decorator for content creation tools."""
    return otto_tool(name, description, "content_creation", **kwargs)


def business_tool(name: str, description: str, **kwargs):
    """Decorator for business operation tools."""
    return otto_tool(name, description, "business_operations", **kwargs)


def web_automation_tool(name: str, description: str, **kwargs):
    """Decorator for web automation tools."""
    return otto_tool(name, description, "web_automation", **kwargs)


# Example usage and testing
if __name__ == "__main__":
    # Example tool
    @otto_tool(
        name="example_tool",
        description="An example tool",
        category="examples",
        parameters={
            "text": {"type": "string", "required": True},
            "count": {"type": "integer", "required": False, "default": 1}
        }
    )
    async def example_tool(text: str, count: int = 1):
        """Example tool implementation."""
        return {"result": text * count}
    
    # Test registration
    tools = get_registered_tools()
    print(f"Registered {len(tools)} tools")
    print(f"Tool: {tools[0]['name']}")
