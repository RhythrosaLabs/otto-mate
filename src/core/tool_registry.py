"""
Tool Registry - Dynamic Tool Discovery and Management
====================================================

Manages all available tools that Otto can use.
Provides discovery, validation, and execution framework.
"""

import logging
import inspect
import importlib
import pkgutil
from typing import Any, Callable, Dict, List, Optional
from functools import wraps

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Registry for all Otto tools.
    """
    
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self._tool_functions: Dict[str, Callable] = {}
        
    def register(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        category: str = "general",
        tags: Optional[List[str]] = None
    ) -> Callable:
        """
        Decorator to register a tool.
        
        Usage:
            @tool_registry.register(
                name="generate_image",
                description="Generate an image from text prompt",
                parameters={
                    "prompt": {"type": "string", "description": "Image description"},
                    "model": {"type": "string", "description": "Model to use"}
                },
                category="ai",
                tags=["image", "generation"]
            )
            async def generate_image(prompt: str, model: str = "flux-fast"):
                # Implementation
                pass
        """
        def decorator(func: Callable) -> Callable:
            self.tools[name] = {
                "name": name,
                "description": description,
                "parameters": parameters,
                "category": category,
                "tags": tags or [],
                "function": func.__name__,
                "module": func.__module__
            }
            self._tool_functions[name] = func
            logger.info(f"Registered tool: {name}")
            return func
        return decorator
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """Get tool function by name."""
        return self._tool_functions.get(name)
    
    def list_tools(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        List available tools with optional filtering.
        
        Args:
            category: Filter by category
            tags: Filter by tags (any match)
            
        Returns:
            List of tool definitions
        """
        tools = list(self.tools.values())
        
        if category:
            tools = [t for t in tools if t["category"] == category]
        
        if tags:
            tools = [
                t for t in tools
                if any(tag in t["tags"] for tag in tags)
            ]
        
        return tools
    
    def get_categories(self) -> List[str]:
        """Get all tool categories."""
        return list(set(t["category"] for t in self.tools.values()))
    
    def discover_tools(self, package_name: str = "src.tools"):
        """
        Automatically discover and register tools from package.
        
        Looks for functions decorated with @tool in all modules
        under the specified package, and also looks for ToolBase classes.
        """
        try:
            # Import the tools package
            package = importlib.import_module(package_name)
            
            # Iterate through all modules in package
            for importer, modname, ispkg in pkgutil.walk_packages(
                path=package.__path__,
                prefix=package.__name__ + ".",
                onerror=lambda x: None
            ):
                try:
                    module = importlib.import_module(modname)
                    logger.debug(f"Scanning module: {modname}")
                    
                    # Look for tool-decorated functions
                    for name, obj in inspect.getmembers(module):
                        if hasattr(obj, "_is_tool"):
                            # This is a tool!
                            tool_info = obj._tool_info
                            self.tools[tool_info["name"]] = tool_info
                            self._tool_functions[tool_info["name"]] = obj
                            logger.info(f"Discovered tool: {tool_info['name']}")
                            
                except Exception as e:
                    logger.warning(f"Failed to scan {modname}: {e}")
            
            logger.info(f"Tool discovery complete: {len(self.tools)} tools registered")
            
        except Exception as e:
            logger.error(f"Tool discovery failed: {e}")
    
    def register_tool_class(self, tool_instance: Any):
        """
        Register tools from a ToolBase instance.
        
        Scans the instance for methods decorated with @tool and registers them.
        """
        for name in dir(tool_instance):
            method = getattr(tool_instance, name)
            if hasattr(method, "_is_tool") and method._is_tool:
                tool_info = method._tool_info.copy()
                tool_info["function"] = method
                self.tools[tool_info["name"]] = tool_info
                self._tool_functions[tool_info["name"]] = method
                logger.info(f"Registered class tool: {tool_info['name']}")
    
    def validate_parameters(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Validate parameters for a tool.
        
        Returns:
            (is_valid, error_message)
        """
        if tool_name not in self.tools:
            return False, f"Tool '{tool_name}' not found"
        
        tool_def = self.tools[tool_name]
        required_params = tool_def["parameters"]
        
        # Check for required parameters
        for param_name, param_def in required_params.items():
            if param_def.get("required", True) and param_name not in parameters:
                return False, f"Missing required parameter: {param_name}"
        
        return True, None


# Decorator for easy tool registration
def tool(
    name: str,
    description: str,
    parameters: Dict[str, Any],
    category: str = "general",
    tags: Optional[List[str]] = None
):
    """
    Decorator to mark a function as an Otto tool.
    
    Example:
        @tool(
            name="search_web",
            description="Search the web for information",
            parameters={
                "query": {"type": "string", "description": "Search query", "required": True}
            },
            category="research",
            tags=["web", "search"]
        )
        async def search_web(query: str):
            # Implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        # Mark as tool and attach metadata
        wrapper._is_tool = True
        wrapper._tool_info = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "category": category,
            "tags": tags or [],
            "function": func.__name__,
            "module": func.__module__
        }
        
        return wrapper
    return decorator
