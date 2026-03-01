"""
Sample Plugin
=============

A demonstration plugin showing how to create Otto plugins.
"""

import math
from typing import Dict, Any
from src.core.plugin_system import ToolPlugin


class SamplePlugin(ToolPlugin):
    """A sample plugin with several demo tools."""
    
    async def initialize(self) -> None:
        """Initialize the plugin and register tools."""
        prefix = self.settings.get("greeting_prefix", "Hello")
        
        # Register greeting tool
        self.register_tool(
            name="greet_user",
            func=self.greet_user,
            description=f"Greet a user with a customizable message (prefix: {prefix})",
            parameters={
                "name": {"type": "string", "required": True, "description": "Name to greet"},
                "style": {"type": "string", "required": False, "description": "Greeting style: formal, casual, enthusiastic"}
            }
        )
        
        # Register calculator tool
        self.register_tool(
            name="calculate_expression",
            func=self.calculate_expression,
            description="Safely evaluate a mathematical expression",
            parameters={
                "expression": {"type": "string", "required": True, "description": "Math expression to evaluate"}
            }
        )
        
        # Register text formatter
        self.register_tool(
            name="format_text",
            func=self.format_text,
            description="Format text in various styles",
            parameters={
                "text": {"type": "string", "required": True, "description": "Text to format"},
                "style": {"type": "string", "required": True, "description": "Style: uppercase, lowercase, title, reverse, leetspeak"}
            }
        )
    
    async def greet_user(self, name: str, style: str = "casual") -> Dict[str, Any]:
        """Generate a greeting for the user."""
        prefix = self.settings.get("greeting_prefix", "Hello")
        
        greetings = {
            "formal": f"Good day, {name}. It is a pleasure to make your acquaintance.",
            "casual": f"{prefix}, {name}! How's it going?",
            "enthusiastic": f"🎉 {prefix.upper()}, {name.upper()}!!! SO GREAT TO SEE YOU! 🎉"
        }
        
        greeting = greetings.get(style, greetings["casual"])
        
        return {
            "success": True,
            "greeting": greeting,
            "style": style,
            "name": name
        }
    
    async def calculate_expression(self, expression: str) -> Dict[str, Any]:
        """Safely evaluate a math expression."""
        # Only allow safe math operations
        allowed_chars = set("0123456789+-*/.() ")
        allowed_funcs = {"sin", "cos", "tan", "sqrt", "abs", "round", "pow", "pi", "e"}
        
        # Check for unsafe characters
        clean_expr = expression
        for func in allowed_funcs:
            clean_expr = clean_expr.replace(func, "")
        
        if not all(c in allowed_chars for c in clean_expr):
            return {
                "success": False,
                "error": "Expression contains unsafe characters"
            }
        
        try:
            # Create safe namespace with math functions
            safe_dict = {
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "sqrt": math.sqrt,
                "abs": abs,
                "round": round,
                "pow": pow,
                "pi": math.pi,
                "e": math.e
            }
            
            result = eval(expression, {"__builtins__": {}}, safe_dict)
            
            return {
                "success": True,
                "expression": expression,
                "result": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "expression": expression,
                "error": str(e)
            }
    
    async def format_text(self, text: str, style: str) -> Dict[str, Any]:
        """Format text in various styles."""
        formatters = {
            "uppercase": lambda t: t.upper(),
            "lowercase": lambda t: t.lower(),
            "title": lambda t: t.title(),
            "reverse": lambda t: t[::-1],
            "leetspeak": lambda t: t.replace('a', '4').replace('e', '3').replace('i', '1').replace('o', '0').replace('s', '5').replace('t', '7')
        }
        
        formatter = formatters.get(style.lower())
        
        if not formatter:
            return {
                "success": False,
                "error": f"Unknown style: {style}. Available: {', '.join(formatters.keys())}"
            }
        
        formatted = formatter(text)
        
        return {
            "success": True,
            "original": text,
            "formatted": formatted,
            "style": style
        }
