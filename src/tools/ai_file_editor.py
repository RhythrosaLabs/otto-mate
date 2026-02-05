"""
AI File Editor
==============

AI-powered file editing using Replicate's code models.
Enables intelligent code refactoring, bug fixing, and feature implementation.
"""

import asyncio
import logging
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    import aiohttp
except ImportError:
    aiohttp = None

from .core import tool, ToolBase

logger = logging.getLogger(__name__)


class AIFileEditor(ToolBase):
    """AI-powered file editing capabilities."""
    
    # Code-capable models on Replicate
    CODE_MODELS = {
        "qwen": "qwen/qwen2.5-coder-32b-instruct",
        "deepseek": "deepseek-ai/deepseek-coder-33b-instruct",
        "codellama": "meta/codellama-70b-instruct",
        "llama": "meta/llama-3.1-405b-instruct"
    }
    
    def __init__(self, replicate_token: Optional[str] = None, project_root: Optional[str] = None):
        self.api_token = replicate_token or os.getenv("REPLICATE_API_TOKEN")
        self.project_root = Path(project_root or Path(__file__).parent.parent.parent)
        self.backup_dir = self.project_root / "data" / "file_backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    async def _call_code_model(
        self,
        prompt: str,
        model: str = "qwen",
        max_tokens: int = 4096
    ) -> str:
        """Call a code-capable model on Replicate."""
        if aiohttp is None:
            raise ImportError("aiohttp is required for AI file editing. Install with: pip install aiohttp")
        
        if not self.api_token:
            raise ValueError("REPLICATE_API_TOKEN not set")
        
        model_id = self.CODE_MODELS.get(model, self.CODE_MODELS["qwen"])
        
        headers = {
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:  # type: ignore
            # Create prediction
            async with session.post(
                f"https://api.replicate.com/v1/models/{model_id}/predictions",
                headers=headers,
                json={
                    "input": {
                        "prompt": prompt,
                        "max_tokens": max_tokens,
                        "temperature": 0.2  # Low temp for code
                    }
                }
            ) as response:
                if response.status >= 400:
                    error = await response.text()
                    raise Exception(f"Model call failed: {error}")
                result = await response.json()
            
            # Poll for completion
            prediction_url = result.get("urls", {}).get("get")
            
            while result.get("status") in ["starting", "processing"]:
                await asyncio.sleep(1)
                async with session.get(prediction_url, headers=headers) as response:
                    result = await response.json()
            
            if result.get("status") == "failed":
                raise Exception(f"Model failed: {result.get('error')}")
            
            output = result.get("output", "")
            if isinstance(output, list):
                output = "".join(output)
            
            return output
    
    def _create_backup(self, file_path: Path) -> Path:
        """Create a backup of a file before editing."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = self.backup_dir / backup_name
        
        if file_path.exists():
            import shutil
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
        
        return backup_path
    
    def _extract_code_block(self, text: str, language: Optional[str] = None) -> str:
        """Extract code from markdown code blocks."""
        # Try to find code blocks
        if language:
            pattern = rf"```{language}\n(.*?)```"
        else:
            pattern = r"```(?:\w+)?\n(.*?)```"
        
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return matches[0].strip()
        
        # If no code blocks, return the text as-is (might already be code)
        return text.strip()
    
    @tool(
        name="ai_edit_file",
        description="Use AI to intelligently edit a file based on instructions. The AI will understand the code and make appropriate changes.",
        category="file_editing"
    )
    async def ai_edit_file(
        self,
        file_path: str,
        instruction: str,
        model: str = "qwen",
        create_backup: bool = True
    ) -> Dict[str, Any]:
        """
        Use AI to edit a file based on natural language instructions.
        
        Args:
            file_path: Path to the file to edit (relative to project root)
            instruction: Natural language description of changes to make
            model: Code model to use (qwen, deepseek, codellama, llama)
            create_backup: Whether to backup the original file
        
        Returns:
            Result with original content, new content, and diff info
        """
        full_path = self.project_root / file_path
        
        # Validate file exists
        if not full_path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}
        
        # Security check
        try:
            full_path.resolve().relative_to(self.project_root.resolve())
        except ValueError:
            return {"success": False, "error": "Access denied - path outside project"}
        
        # Read current content
        try:
            with open(full_path, 'r') as f:
                original_content = f.read()
        except Exception as e:
            return {"success": False, "error": f"Failed to read file: {e}"}
        
        # Detect language from extension
        ext_to_lang = {
            ".py": "python", ".js": "javascript", ".ts": "typescript",
            ".html": "html", ".css": "css", ".json": "json",
            ".md": "markdown", ".yaml": "yaml", ".yml": "yaml",
            ".sh": "bash", ".sql": "sql"
        }
        language = ext_to_lang.get(full_path.suffix, "text")
        
        # Create prompt for the AI
        prompt = f"""You are an expert programmer. Edit the following {language} code according to the instruction.

INSTRUCTION: {instruction}

ORIGINAL CODE:
```{language}
{original_content}
```

OUTPUT ONLY the complete modified code, wrapped in ```{language} code blocks. Do not include explanations, just the code."""

        try:
            # Call code model
            response = await self._call_code_model(prompt, model=model)
            
            # Extract the code from response
            new_content = self._extract_code_block(response, language)
            
            if not new_content or new_content == original_content:
                return {
                    "success": False,
                    "error": "AI returned empty or unchanged content",
                    "raw_response": response[:500]
                }
            
            # Create backup if requested
            backup_path = None
            if create_backup:
                backup_path = self._create_backup(full_path)
            
            # Write new content
            with open(full_path, 'w') as f:
                f.write(new_content)
            
            # Calculate diff stats
            original_lines = len(original_content.splitlines())
            new_lines = len(new_content.splitlines())
            
            return {
                "success": True,
                "file_path": file_path,
                "instruction": instruction,
                "original_lines": original_lines,
                "new_lines": new_lines,
                "lines_changed": abs(new_lines - original_lines),
                "backup_path": str(backup_path) if backup_path else None,
                "model_used": model
            }
            
        except Exception as e:
            logger.error(f"AI edit failed: {e}")
            return {"success": False, "error": str(e)}
    
    @tool(
        name="ai_fix_code",
        description="Use AI to fix bugs or errors in a code file",
        category="file_editing"
    )
    async def ai_fix_code(
        self,
        file_path: str,
        error_message: Optional[str] = None,
        bug_description: Optional[str] = None,
        model: str = "qwen"
    ) -> Dict[str, Any]:
        """
        Use AI to fix bugs in code.
        
        Args:
            file_path: Path to the file with bugs
            error_message: The error message received (if any)
            bug_description: Description of the bug behavior
            model: Code model to use
        """
        context = []
        if error_message:
            context.append(f"Error message: {error_message}")
        if bug_description:
            context.append(f"Bug description: {bug_description}")
        
        instruction = "Fix the bugs in this code. " + " ".join(context)
        
        return await self.ai_edit_file(file_path, instruction, model=model)
    
    @tool(
        name="ai_refactor_code",
        description="Use AI to refactor and improve code quality",
        category="file_editing"
    )
    async def ai_refactor_code(
        self,
        file_path: str,
        refactor_type: str = "general",
        model: str = "qwen"
    ) -> Dict[str, Any]:
        """
        Use AI to refactor code.
        
        Args:
            file_path: Path to the file to refactor
            refactor_type: Type of refactoring (general, performance, readability, modular)
            model: Code model to use
        """
        instructions = {
            "general": "Refactor this code to improve quality, fix any issues, and follow best practices.",
            "performance": "Optimize this code for better performance. Reduce complexity and improve efficiency.",
            "readability": "Refactor for better readability. Add docstrings, improve naming, simplify logic.",
            "modular": "Refactor to be more modular. Extract functions, reduce duplication, improve structure."
        }
        
        instruction = instructions.get(refactor_type, instructions["general"])
        return await self.ai_edit_file(file_path, instruction, model=model)
    
    @tool(
        name="ai_add_feature",
        description="Use AI to add a new feature to existing code",
        category="file_editing"
    )
    async def ai_add_feature(
        self,
        file_path: str,
        feature_description: str,
        model: str = "qwen"
    ) -> Dict[str, Any]:
        """
        Use AI to add a feature to code.
        
        Args:
            file_path: Path to the file to modify
            feature_description: Description of the feature to add
            model: Code model to use
        """
        instruction = f"Add the following feature to this code while maintaining existing functionality: {feature_description}"
        return await self.ai_edit_file(file_path, instruction, model=model)
    
    @tool(
        name="ai_explain_code",
        description="Use AI to explain what code does",
        category="file_editing"
    )
    async def ai_explain_code(
        self,
        file_path: str,
        section: Optional[str] = None,
        model: str = "qwen"
    ) -> Dict[str, Any]:
        """
        Use AI to explain code.
        
        Args:
            file_path: Path to the file to explain
            section: Specific section or function to explain (optional)
            model: Code model to use
        """
        full_path = self.project_root / file_path
        
        if not full_path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}
        
        with open(full_path, 'r') as f:
            content = f.read()
        
        focus = f"Focus on: {section}" if section else "Explain the entire file"
        
        prompt = f"""Explain the following code. {focus}

```
{content[:8000]}  
```

Provide:
1. Overall purpose
2. Key functions/classes and what they do
3. Important logic flows
4. Any notable patterns or techniques used"""

        try:
            explanation = await self._call_code_model(prompt, model=model, max_tokens=2048)
            
            return {
                "success": True,
                "file_path": file_path,
                "explanation": explanation,
                "code_length": len(content),
                "model_used": model
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="ai_generate_code",
        description="Use AI to generate new code based on requirements",
        category="file_editing"
    )
    async def ai_generate_code(
        self,
        file_path: str,
        requirements: str,
        language: Optional[str] = None,
        model: str = "qwen"
    ) -> Dict[str, Any]:
        """
        Use AI to generate new code.
        
        Args:
            file_path: Path where to save the generated code
            requirements: Description of what the code should do
            language: Programming language (auto-detected from extension if not provided)
            model: Code model to use
        """
        full_path = self.project_root / file_path
        
        # Detect language
        if not language:
            ext_to_lang = {
                ".py": "python", ".js": "javascript", ".ts": "typescript",
                ".html": "html", ".css": "css", ".sh": "bash"
            }
            language = ext_to_lang.get(full_path.suffix, "python")
        
        prompt = f"""Generate {language} code for the following requirements:

{requirements}

Output ONLY the complete code, wrapped in ```{language} code blocks. Include:
- Proper imports
- Type hints (if applicable)
- Docstrings
- Error handling
- Follow best practices for {language}"""

        try:
            response = await self._call_code_model(prompt, model=model, max_tokens=4096)
            code = self._extract_code_block(response, language)
            
            if not code:
                return {"success": False, "error": "Failed to generate code"}
            
            # Create parent directories
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write code
            with open(full_path, 'w') as f:
                f.write(code)
            
            return {
                "success": True,
                "file_path": file_path,
                "requirements": requirements,
                "lines_generated": len(code.splitlines()),
                "model_used": model
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="ai_code_review",
        description="Use AI to review code and suggest improvements",
        category="file_editing"
    )
    async def ai_code_review(
        self,
        file_path: str,
        model: str = "qwen"
    ) -> Dict[str, Any]:
        """
        Use AI to review code.
        
        Args:
            file_path: Path to the file to review
            model: Code model to use
        """
        full_path = self.project_root / file_path
        
        if not full_path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}
        
        with open(full_path, 'r') as f:
            content = f.read()
        
        prompt = f"""Review the following code and provide detailed feedback:

```
{content[:8000]}
```

Provide:
1. Code Quality Score (1-10)
2. Bugs or potential issues found
3. Security concerns
4. Performance issues
5. Style/best practice violations
6. Specific improvement suggestions with code examples"""

        try:
            review = await self._call_code_model(prompt, model=model, max_tokens=2048)
            
            return {
                "success": True,
                "file_path": file_path,
                "review": review,
                "code_length": len(content),
                "lines": len(content.splitlines()),
                "model_used": model
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="restore_file_backup",
        description="Restore a file from its backup",
        category="file_editing"
    )
    async def restore_backup(
        self,
        original_path: str,
        backup_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Restore a file from backup.
        
        Args:
            original_path: Path to the file to restore
            backup_path: Specific backup to restore (uses latest if not specified)
        """
        full_path = self.project_root / original_path
        
        if backup_path:
            backup = Path(backup_path)
        else:
            # Find latest backup
            stem = full_path.stem
            suffix = full_path.suffix
            pattern = f"{stem}_*{suffix}"
            backups = list(self.backup_dir.glob(pattern))
            
            if not backups:
                return {"success": False, "error": "No backups found"}
            
            backup = max(backups, key=lambda p: p.stat().st_mtime)
        
        if not backup.exists():
            return {"success": False, "error": f"Backup not found: {backup}"}
        
        try:
            import shutil
            shutil.copy2(backup, full_path)
            
            return {
                "success": True,
                "restored_from": str(backup),
                "restored_to": original_path
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


def get_ai_file_editor() -> AIFileEditor:
    """Get the AI file editor instance."""
    return AIFileEditor()
