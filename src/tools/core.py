"""
Core Tool Definitions
====================

Base classes and decorators for tool registration.
"""

from typing import Callable, Dict, Any, Optional, List
from functools import wraps
import inspect
import logging

logger = logging.getLogger(__name__)


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    category: str = "general",
    parameters: Optional[Dict[str, Any]] = None
):
    """
    Decorator to register a function as a tool.
    
    Usage:
        @tool(
            name="generate_image",
            description="Generate an image using AI",
            category="ai_models"
        )
        async def generate_image(prompt: str, style: str = "realistic"):
            ...
    """
    def decorator(func: Callable):
        # Extract function info
        func_name = name or func.__name__
        func_desc = description or func.__doc__ or "No description"
        
        # Extract parameters from type hints
        sig = inspect.signature(func)
        func_params = parameters or {}
        
        if not func_params:
            for param_name, param in sig.parameters.items():
                if param_name in ['self', 'cls']:
                    continue
                    
                param_info = {
                    "type": "string",  # default
                    "required": param.default == inspect.Parameter.empty
                }
                
                # Try to get type from annotation
                if param.annotation != inspect.Parameter.empty:
                    if param.annotation == str:
                        param_info["type"] = "string"
                    elif param.annotation == int:
                        param_info["type"] = "integer"
                    elif param.annotation == float:
                        param_info["type"] = "number"
                    elif param.annotation == bool:
                        param_info["type"] = "boolean"
                    elif param.annotation == list or param.annotation == List:
                        param_info["type"] = "array"
                    elif param.annotation == dict or param.annotation == Dict:
                        param_info["type"] = "object"
                
                if param.default != inspect.Parameter.empty:
                    param_info["default"] = param.default
                    
                func_params[param_name] = param_info
        
        # Attach metadata
        func._tool_metadata = {
            "name": func_name,
            "description": func_desc.strip(),
            "category": category,
            "parameters": func_params,
            "is_async": inspect.iscoroutinefunction(func)
        }
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logger.info(f"Executing tool: {func_name}")
            try:
                if inspect.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                logger.info(f"Tool {func_name} completed successfully")
                return result
            except Exception as e:
                logger.error(f"Tool {func_name} failed: {e}", exc_info=True)
                raise
        
        wrapper._tool_metadata = func._tool_metadata
        wrapper._is_tool = True
        wrapper._tool_info = {
            "name": func_name,
            "description": func_desc.strip(),
            "category": category,
            "parameters": func_params,
            "is_async": inspect.iscoroutinefunction(func)
        }
        return wrapper
    
    return decorator


class ToolBase:
    """Base class for tool collections."""
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get all tools defined in this class."""
        tools = []
        for name in dir(self):
            method = getattr(self, name)
            if hasattr(method, '_tool_metadata'):
                tools.append(method._tool_metadata)
        return tools
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """Get a specific tool by name."""
        for attr_name in dir(self):
            method = getattr(self, attr_name)
            if hasattr(method, '_tool_metadata'):
                if method._tool_metadata['name'] == name:
                    return method
        return None
