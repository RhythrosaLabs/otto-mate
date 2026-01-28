"""
Autonomous Code Execution Tools
===============================

Tools for writing, executing, and managing code dynamically.
Enables the AI to solve problems by writing and running code.
"""

import logging
import asyncio
import subprocess
import tempfile
import os
import sys
import json
import traceback
from typing import Optional, Dict, Any, List
from pathlib import Path
from .core import tool, ToolBase

logger = logging.getLogger(__name__)


class CodeExecutionTools(ToolBase):
    """
    Autonomous code execution - write and run code to solve problems.
    
    This enables:
    - Writing Python scripts dynamically
    - Executing code in sandboxed environments
    - Installing packages on demand
    - Running shell commands
    - Creating and managing files
    """
    
    def __init__(self, workspace_dir: str = "./workspace"):
        self.workspace = Path(workspace_dir)
        self.workspace.mkdir(parents=True, exist_ok=True)
        
        # Track created files
        self.created_files: List[str] = []
        
        # Safe execution timeout
        self.timeout = 60  # seconds
    
    @tool(
        name="execute_python",
        description="Execute Python code and return the result. Use this to solve problems programmatically, process data, make calculations, or generate content.",
        category="code"
    )
    async def execute_python(
        self,
        code: str,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Execute Python code.
        
        Args:
            code: Python code to execute
            timeout: Maximum execution time in seconds
        """
        # Create temp file
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.py', 
            delete=False,
            dir=str(self.workspace)
        ) as f:
            f.write(code)
            script_path = f.name
        
        try:
            # Run the code
            process = await asyncio.create_subprocess_exec(
                sys.executable, script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace)
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "success": False,
                    "error": f"Execution timed out after {timeout}s",
                    "code": code
                }
            
            stdout_text = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "return_code": process.returncode,
                "code": code
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "code": code
            }
        finally:
            # Cleanup
            try:
                os.unlink(script_path)
            except:
                pass
    
    @tool(
        name="execute_shell",
        description="Execute a shell command. Use for system operations, file management, or running external tools.",
        category="code"
    )
    async def execute_shell(
        self,
        command: str,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Execute a shell command.
        
        Args:
            command: Shell command to execute
            timeout: Maximum execution time
        """
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace)
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "success": False,
                    "error": f"Command timed out after {timeout}s"
                }
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode('utf-8', errors='replace'),
                "stderr": stderr.decode('utf-8', errors='replace'),
                "return_code": process.returncode,
                "command": command
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @tool(
        name="install_package",
        description="Install a Python package using pip. Use when code requires a package that isn't installed.",
        category="code"
    )
    async def install_package(
        self,
        package: str
    ) -> Dict[str, Any]:
        """
        Install a Python package.
        
        Args:
            package: Package name (e.g., "requests", "pillow>=9.0")
        """
        result = await self.execute_shell(
            f"{sys.executable} -m pip install {package} --quiet"
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": f"Successfully installed {package}"
            }
        else:
            return {
                "success": False,
                "error": f"Failed to install {package}",
                "details": result.get("stderr", "")
            }
    
    @tool(
        name="create_file",
        description="Create a file with specified content. Use for generating scripts, configs, data files, or any other file type.",
        category="code"
    )
    async def create_file(
        self,
        filename: str,
        content: str,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Create a file.
        
        Args:
            filename: Name or path of file to create
            content: File content
            overwrite: Whether to overwrite if exists
        """
        try:
            # Resolve path
            if os.path.isabs(filename):
                filepath = Path(filename)
            else:
                filepath = self.workspace / filename
            
            # Create parent dirs
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if exists
            if filepath.exists() and not overwrite:
                return {
                    "success": False,
                    "error": f"File already exists: {filepath}. Set overwrite=True to replace."
                }
            
            # Write file
            filepath.write_text(content)
            self.created_files.append(str(filepath))
            
            return {
                "success": True,
                "path": str(filepath),
                "size": len(content),
                "message": f"Created file: {filepath}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @tool(
        name="read_file",
        description="Read the contents of a file.",
        category="code"
    )
    async def read_file(
        self,
        filename: str
    ) -> Dict[str, Any]:
        """
        Read a file.
        
        Args:
            filename: Name or path of file to read
        """
        try:
            if os.path.isabs(filename):
                filepath = Path(filename)
            else:
                filepath = self.workspace / filename
            
            if not filepath.exists():
                return {
                    "success": False,
                    "error": f"File not found: {filepath}"
                }
            
            content = filepath.read_text()
            
            return {
                "success": True,
                "path": str(filepath),
                "content": content,
                "size": len(content)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @tool(
        name="list_workspace_files",
        description="List files in the workspace directory.",
        category="code"
    )
    async def list_files(
        self,
        pattern: str = "*"
    ) -> Dict[str, Any]:
        """
        List files in workspace.
        
        Args:
            pattern: Glob pattern to match (e.g., "*.py", "**/*.json")
        """
        try:
            files = list(self.workspace.glob(pattern))
            
            file_list = []
            for f in files:
                if f.is_file():
                    file_list.append({
                        "name": f.name,
                        "path": str(f),
                        "size": f.stat().st_size,
                        "modified": f.stat().st_mtime
                    })
            
            return {
                "success": True,
                "workspace": str(self.workspace),
                "files": file_list,
                "count": len(file_list)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @tool(
        name="solve_with_code",
        description="Solve a problem by writing and executing Python code. Describe what you need and this will generate and run appropriate code.",
        category="code"
    )
    async def solve_with_code(
        self,
        problem: str,
        expected_output: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate and execute code to solve a problem.
        
        Args:
            problem: Description of the problem to solve
            expected_output: Optional description of expected output format
        """
        # This is a meta-tool - the orchestrator should use this as a hint
        # to generate appropriate code. The actual code generation happens
        # in the orchestrator's planning phase.
        
        return {
            "success": True,
            "message": "Code generation requested",
            "problem": problem,
            "expected_output": expected_output,
            "hint": "The orchestrator should generate Python code to solve this problem"
        }


class DataProcessingTools(ToolBase):
    """Tools for processing and transforming data."""
    
    def __init__(self, workspace_dir: str = "./workspace"):
        self.workspace = Path(workspace_dir)
        self.workspace.mkdir(parents=True, exist_ok=True)
    
    @tool(
        name="process_json",
        description="Process and transform JSON data. Extract fields, filter, transform, or aggregate.",
        category="data"
    )
    async def process_json(
        self,
        data: Any,
        operation: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process JSON data.
        
        Args:
            data: JSON data (string or dict/list)
            operation: Operation (extract, filter, transform, aggregate)
            params: Operation parameters
        """
        params = params or {}
        
        try:
            # Parse if string
            if isinstance(data, str):
                data = json.loads(data)
            
            if operation == "extract":
                # Extract specific fields
                path = params.get("path", "").split(".")
                result = data
                for key in path:
                    if key:
                        if isinstance(result, dict):
                            result = result.get(key)
                        elif isinstance(result, list) and key.isdigit():
                            result = result[int(key)]
                return {"success": True, "result": result}
            
            elif operation == "filter":
                # Filter list by condition
                if not isinstance(data, list):
                    return {"success": False, "error": "Filter requires a list"}
                
                field = params.get("field")
                value = params.get("value")
                op = params.get("operator", "equals")
                
                filtered = []
                for item in data:
                    if isinstance(item, dict) and field:
                        item_val = item.get(field)
                        if op == "equals" and item_val == value:
                            filtered.append(item)
                        elif op == "contains" and value in str(item_val):
                            filtered.append(item)
                        elif op == "gt" and item_val > value:
                            filtered.append(item)
                        elif op == "lt" and item_val < value:
                            filtered.append(item)
                
                return {"success": True, "result": filtered, "count": len(filtered)}
            
            elif operation == "aggregate":
                # Aggregate list
                if not isinstance(data, list):
                    return {"success": False, "error": "Aggregate requires a list"}
                
                field = params.get("field")
                agg_type = params.get("type", "count")
                
                if agg_type == "count":
                    return {"success": True, "result": len(data)}
                
                values = [item.get(field) for item in data if isinstance(item, dict) and field in item]
                numeric_values = [v for v in values if isinstance(v, (int, float))]
                
                if agg_type == "sum":
                    return {"success": True, "result": sum(numeric_values)}
                elif agg_type == "avg":
                    return {"success": True, "result": sum(numeric_values) / len(numeric_values) if numeric_values else 0}
                elif agg_type == "min":
                    return {"success": True, "result": min(numeric_values) if numeric_values else None}
                elif agg_type == "max":
                    return {"success": True, "result": max(numeric_values) if numeric_values else None}
            
            elif operation == "transform":
                # Transform using template
                template = params.get("template", "{}")
                if isinstance(data, list):
                    results = []
                    for item in data:
                        if isinstance(item, dict):
                            try:
                                results.append(template.format(**item))
                            except:
                                results.append(item)
                    return {"success": True, "result": results}
                elif isinstance(data, dict):
                    return {"success": True, "result": template.format(**data)}
            
            return {"success": False, "error": f"Unknown operation: {operation}"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="convert_format",
        description="Convert data between formats (JSON, CSV, YAML, etc.)",
        category="data"
    )
    async def convert_format(
        self,
        data: str,
        from_format: str,
        to_format: str
    ) -> Dict[str, Any]:
        """
        Convert data between formats.
        
        Args:
            data: Input data as string
            from_format: Source format (json, csv, yaml)
            to_format: Target format (json, csv, yaml)
        """
        try:
            # Parse input
            if from_format == "json":
                parsed = json.loads(data)
            elif from_format == "csv":
                import csv
                from io import StringIO
                reader = csv.DictReader(StringIO(data))
                parsed = list(reader)
            elif from_format == "yaml":
                try:
                    import yaml
                    parsed = yaml.safe_load(data)
                except ImportError:
                    return {"success": False, "error": "PyYAML not installed"}
            else:
                return {"success": False, "error": f"Unknown format: {from_format}"}
            
            # Convert to output
            if to_format == "json":
                result = json.dumps(parsed, indent=2)
            elif to_format == "csv":
                import csv
                from io import StringIO
                if not isinstance(parsed, list):
                    parsed = [parsed]
                if parsed and isinstance(parsed[0], dict):
                    output = StringIO()
                    writer = csv.DictWriter(output, fieldnames=parsed[0].keys())
                    writer.writeheader()
                    writer.writerows(parsed)
                    result = output.getvalue()
                else:
                    return {"success": False, "error": "Cannot convert to CSV"}
            elif to_format == "yaml":
                try:
                    import yaml
                    result = yaml.dump(parsed, default_flow_style=False)
                except ImportError:
                    return {"success": False, "error": "PyYAML not installed"}
            else:
                return {"success": False, "error": f"Unknown format: {to_format}"}
            
            return {
                "success": True,
                "result": result,
                "from_format": from_format,
                "to_format": to_format
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
