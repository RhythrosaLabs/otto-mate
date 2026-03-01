"""
Code Formatter Plugin
=====================

Format, beautify, and lint code in various programming languages.

Example usage:
    >>> result = await plugin.format_code("def foo():pass", language="python")
    >>> result = await plugin.minify_code(css_content, language="css")
"""

import json
import re
from typing import Dict, Any, Optional

try:
    import black
    HAS_BLACK = True
except ImportError:
    HAS_BLACK = False

try:
    import autopep8
    HAS_AUTOPEP8 = True
except ImportError:
    HAS_AUTOPEP8 = False

from src.core.plugin_system import ToolPlugin


class CodeFormatterPlugin(ToolPlugin):
    """Plugin for code formatting and beautification."""
    
    SUPPORTED_LANGUAGES = {
        "python": {"extensions": [".py"], "formatters": ["black", "autopep8"]},
        "javascript": {"extensions": [".js", ".jsx"], "formatters": ["builtin"]},
        "json": {"extensions": [".json"], "formatters": ["builtin"]},
        "html": {"extensions": [".html", ".htm"], "formatters": ["builtin"]},
        "css": {"extensions": [".css"], "formatters": ["builtin"]},
        "sql": {"extensions": [".sql"], "formatters": ["builtin"]},
        "xml": {"extensions": [".xml"], "formatters": ["builtin"]},
        "yaml": {"extensions": [".yaml", ".yml"], "formatters": ["builtin"]},
    }
    
    async def initialize(self) -> None:
        """Initialize the plugin and register tools."""
        
        self.python_style = self.settings.get("python_style", "black")
        self.indent_size = self.settings.get("indent_size", 4)
        self.use_tabs = self.settings.get("use_tabs", False)
        self.line_length = self.settings.get("line_length", 88)
        
        self.register_tool(
            name="format_code",
            func=self.format_code,
            description="Format and beautify code in various languages",
            parameters={
                "code": {"type": "string", "required": True, "description": "Code to format"},
                "language": {"type": "string", "required": True, "description": "Programming language"},
                "indent_size": {"type": "integer", "required": False, "description": "Indentation size"}
            }
        )
        
        self.register_tool(
            name="minify_code",
            func=self.minify_code,
            description="Minify code by removing whitespace and comments",
            parameters={
                "code": {"type": "string", "required": True},
                "language": {"type": "string", "required": True, "description": "Language (js, css, html)"}
            }
        )
        
        self.register_tool(
            name="lint_code",
            func=self.lint_code,
            description="Check code for common issues and style problems",
            parameters={
                "code": {"type": "string", "required": True},
                "language": {"type": "string", "required": True}
            }
        )
        
        self.register_tool(
            name="convert_tabs_spaces",
            func=self.convert_tabs_spaces,
            description="Convert between tabs and spaces",
            parameters={
                "code": {"type": "string", "required": True},
                "to_tabs": {"type": "boolean", "required": False, "description": "Convert to tabs (default: to spaces)"},
                "tab_width": {"type": "integer", "required": False, "description": "Tab width in spaces"}
            }
        )
        
        self.register_tool(
            name="get_supported_formats",
            func=self.get_supported_formats,
            description="Get list of supported programming languages",
            parameters={}
        )
    
    async def format_code(self, code: str, language: str, 
                         indent_size: Optional[int] = None) -> Dict[str, Any]:
        """Format code in the specified language."""
        try:
            language = language.lower()
            indent = indent_size or self.indent_size
            
            if language not in self.SUPPORTED_LANGUAGES:
                return {
                    "error": f"Unsupported language: {language}",
                    "supported": list(self.SUPPORTED_LANGUAGES.keys()),
                    "success": False
                }
            
            formatted = code
            formatter_used = "none"
            
            if language == "python":
                formatted, formatter_used = self._format_python(code)
            elif language == "json":
                formatted, formatter_used = self._format_json(code, indent)
            elif language == "javascript":
                formatted, formatter_used = self._format_javascript(code, indent)
            elif language == "html":
                formatted, formatter_used = self._format_html(code, indent)
            elif language == "css":
                formatted, formatter_used = self._format_css(code, indent)
            elif language == "sql":
                formatted, formatter_used = self._format_sql(code)
            elif language == "xml":
                formatted, formatter_used = self._format_xml(code, indent)
            else:
                formatted = code
            
            return {
                "success": True,
                "language": language,
                "formatter": formatter_used,
                "original_length": len(code),
                "formatted_length": len(formatted),
                "formatted_code": formatted
            }
            
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def _format_python(self, code: str) -> tuple:
        """Format Python code."""
        if HAS_BLACK and self.python_style == "black":
            try:
                formatted = black.format_str(code, mode=black.Mode(line_length=self.line_length))
                return formatted, "black"
            except:
                pass
        
        if HAS_AUTOPEP8:
            try:
                formatted = autopep8.fix_code(code, options={"max_line_length": self.line_length})
                return formatted, "autopep8"
            except:
                pass
        
        # Basic Python formatting
        lines = code.split("\n")
        formatted_lines = []
        indent_level = 0
        indent_str = " " * self.indent_size
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                formatted_lines.append("")
                continue
            
            # Decrease indent for these
            if stripped.startswith(("elif ", "else:", "except", "finally:", "except:")):
                indent_level = max(0, indent_level - 1)
            elif stripped.startswith(("return", "break", "continue", "pass", "raise")):
                pass
            elif stripped.endswith(":"):
                pass
            
            formatted_lines.append(indent_str * indent_level + stripped)
            
            # Increase indent after colons
            if stripped.endswith(":"):
                indent_level += 1
        
        return "\n".join(formatted_lines), "builtin"
    
    def _format_json(self, code: str, indent: int) -> tuple:
        """Format JSON code."""
        try:
            parsed = json.loads(code)
            formatted = json.dumps(parsed, indent=indent, ensure_ascii=False)
            return formatted, "builtin"
        except json.JSONDecodeError as e:
            return code, f"error: {e}"
    
    def _format_javascript(self, code: str, indent: int) -> tuple:
        """Format JavaScript code (basic)."""
        indent_str = " " * indent
        
        # Add newlines after braces
        code = re.sub(r'\{(?!\s*\n)', '{\n', code)
        code = re.sub(r'(?<!\n\s*)\}', '\n}', code)
        
        # Format
        lines = code.split("\n")
        formatted = []
        level = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            
            if stripped.startswith("}"):
                level = max(0, level - 1)
            
            formatted.append(indent_str * level + stripped)
            
            if stripped.endswith("{"):
                level += 1
        
        return "\n".join(formatted), "builtin"
    
    def _format_html(self, code: str, indent: int) -> tuple:
        """Format HTML code (basic)."""
        indent_str = " " * indent
        
        # Add newlines around tags
        code = re.sub(r'>(\s*)<', '>\n<', code)
        
        lines = code.split("\n")
        formatted = []
        level = 0
        
        void_elements = {"br", "hr", "img", "input", "meta", "link", "area", "base", "col", "embed"}
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            
            # Check for closing tag
            if stripped.startswith("</"):
                level = max(0, level - 1)
            
            formatted.append(indent_str * level + stripped)
            
            # Check for opening tag (not void or self-closing)
            if re.match(r"<[a-z]+[^>]*>$", stripped.lower()) and not stripped.endswith("/>"):
                tag_match = re.match(r"<([a-z]+)", stripped.lower())
                if tag_match and tag_match.group(1) not in void_elements:
                    level += 1
        
        return "\n".join(formatted), "builtin"
    
    def _format_css(self, code: str, indent: int) -> tuple:
        """Format CSS code."""
        indent_str = " " * indent
        
        # Add newlines
        code = re.sub(r'\{', ' {\n', code)
        code = re.sub(r'\}', '\n}\n', code)
        code = re.sub(r';', ';\n', code)
        
        lines = code.split("\n")
        formatted = []
        in_block = False
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            
            if "{" in stripped:
                in_block = True
                formatted.append(stripped)
            elif "}" in stripped:
                in_block = False
                formatted.append(stripped)
            elif in_block:
                formatted.append(indent_str + stripped)
            else:
                formatted.append(stripped)
        
        return "\n".join(formatted), "builtin"
    
    def _format_sql(self, code: str) -> tuple:
        """Format SQL code (basic)."""
        keywords = ["SELECT", "FROM", "WHERE", "AND", "OR", "JOIN", "LEFT", "RIGHT", 
                   "INNER", "OUTER", "ON", "ORDER BY", "GROUP BY", "HAVING", "LIMIT",
                   "INSERT", "INTO", "VALUES", "UPDATE", "SET", "DELETE", "CREATE", "DROP"]
        
        formatted = code.upper()
        for kw in keywords:
            formatted = re.sub(rf'\b{kw}\b', f'\n{kw}', formatted, flags=re.IGNORECASE)
        
        # Clean up multiple newlines
        formatted = re.sub(r'\n\s*\n', '\n', formatted)
        formatted = formatted.strip()
        
        return formatted, "builtin"
    
    def _format_xml(self, code: str, indent: int) -> tuple:
        """Format XML code."""
        return self._format_html(code, indent)  # Reuse HTML formatter
    
    async def minify_code(self, code: str, language: str) -> Dict[str, Any]:
        """Minify code by removing unnecessary whitespace."""
        try:
            language = language.lower()
            original_size = len(code)
            
            if language in ["js", "javascript"]:
                # Remove comments
                minified = re.sub(r'//.*?\n', '', code)
                minified = re.sub(r'/\*.*?\*/', '', minified, flags=re.DOTALL)
                # Remove whitespace
                minified = re.sub(r'\s+', ' ', minified)
                minified = re.sub(r'\s*([{}();,:])\s*', r'\1', minified)
                
            elif language == "css":
                # Remove comments
                minified = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
                # Remove whitespace
                minified = re.sub(r'\s+', ' ', minified)
                minified = re.sub(r'\s*([{}:;,])\s*', r'\1', minified)
                
            elif language == "html":
                # Remove comments
                minified = re.sub(r'<!--.*?-->', '', code, flags=re.DOTALL)
                # Remove whitespace between tags
                minified = re.sub(r'>\s+<', '><', minified)
                minified = re.sub(r'\s+', ' ', minified)
                
            elif language == "json":
                minified = json.dumps(json.loads(code), separators=(',', ':'))
                
            else:
                minified = re.sub(r'\s+', ' ', code).strip()
            
            minified = minified.strip()
            new_size = len(minified)
            
            return {
                "success": True,
                "language": language,
                "original_size": original_size,
                "minified_size": new_size,
                "reduction_percent": round((1 - new_size / original_size) * 100, 1) if original_size > 0 else 0,
                "minified_code": minified
            }
            
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def lint_code(self, code: str, language: str) -> Dict[str, Any]:
        """Check code for common issues."""
        try:
            issues = []
            language = language.lower()
            
            lines = code.split("\n")
            
            for i, line in enumerate(lines, 1):
                # Check line length
                if len(line) > self.line_length:
                    issues.append({
                        "line": i,
                        "type": "warning",
                        "message": f"Line too long ({len(line)} > {self.line_length})"
                    })
                
                # Trailing whitespace
                if line.rstrip() != line:
                    issues.append({
                        "line": i,
                        "type": "style",
                        "message": "Trailing whitespace"
                    })
                
                # Mixed tabs and spaces
                if "\t" in line and "    " in line:
                    issues.append({
                        "line": i,
                        "type": "style",
                        "message": "Mixed tabs and spaces"
                    })
            
            # Language-specific checks
            if language == "python":
                if "import *" in code:
                    issues.append({"line": 0, "type": "warning", "message": "Avoid wildcard imports"})
                if "except:" in code and "except Exception" not in code:
                    issues.append({"line": 0, "type": "warning", "message": "Avoid bare except clauses"})
            
            elif language in ["javascript", "js"]:
                if "var " in code:
                    issues.append({"line": 0, "type": "suggestion", "message": "Consider using 'let' or 'const' instead of 'var'"})
                if "==" in code and "===" not in code:
                    issues.append({"line": 0, "type": "suggestion", "message": "Consider using strict equality (===)"})
            
            return {
                "success": True,
                "language": language,
                "issues_count": len(issues),
                "issues": issues,
                "summary": "No issues found" if not issues else f"Found {len(issues)} issue(s)"
            }
            
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def convert_tabs_spaces(self, code: str, to_tabs: bool = False, 
                                  tab_width: Optional[int] = None) -> Dict[str, Any]:
        """Convert between tabs and spaces."""
        try:
            width = tab_width or self.indent_size
            
            if to_tabs:
                # Spaces to tabs
                converted = code.replace(" " * width, "\t")
            else:
                # Tabs to spaces
                converted = code.replace("\t", " " * width)
            
            return {
                "success": True,
                "conversion": "spaces_to_tabs" if to_tabs else "tabs_to_spaces",
                "tab_width": width,
                "converted_code": converted
            }
            
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def get_supported_formats(self) -> Dict[str, Any]:
        """Get list of supported languages."""
        return {
            "success": True,
            "languages": self.SUPPORTED_LANGUAGES,
            "count": len(self.SUPPORTED_LANGUAGES),
            "python_formatters_available": {
                "black": HAS_BLACK,
                "autopep8": HAS_AUTOPEP8
            }
        }
