"""
Otto Universal - Slash Command Processor
========================================

Based on printify_clean/otto_engine.py patterns.
Provides quick access to AI models and utilities via /command syntax.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Callable, List

logger = logging.getLogger(__name__)

# ============================================================================
# AI MODEL REGISTRY
# ============================================================================
AI_MODELS = {
    # Image Generation
    "image": {
        "model": "flux-schnell",
        "type": "image",
        "desc": "Generate images (Flux Schnell - fast)"
    },
    "flux": {
        "model": "flux-schnell", 
        "type": "image",
        "desc": "Generate images with Flux"
    },
    "flux-dev": {
        "model": "flux-dev",
        "type": "image", 
        "desc": "Generate high-quality images (Flux Dev - slower)"
    },
    
    # Video Generation
    "video": {
        "model": "kling",
        "type": "video",
        "desc": "Generate video clips"
    },
    "kling": {
        "model": "kling",
        "type": "video",
        "desc": "Generate video with Kling AI"
    },
    
    # Audio/Music Generation
    "music": {
        "model": "musicgen",
        "type": "audio",
        "desc": "Generate music tracks"
    },
    "musicgen": {
        "model": "musicgen",
        "type": "audio",
        "desc": "Generate music with MusicGen"
    },
    "speak": {
        "model": "tts",
        "type": "speech",
        "desc": "Text-to-speech"
    },
    "tts": {
        "model": "tts",
        "type": "speech",
        "desc": "Text-to-speech"
    },
}

# ============================================================================
# SLASH COMMANDS REGISTRY
# ============================================================================
SLASH_COMMANDS = {
    # Help
    "help": {"type": "help", "desc": "Show available slash commands"},
    "commands": {"type": "help", "desc": "Show available slash commands"},
    
    # File Generation
    "python": {"type": "code", "ext": "py", "desc": "Generate Python script"},
    "py": {"type": "code", "ext": "py", "desc": "Generate Python script"},
    "html": {"type": "code", "ext": "html", "desc": "Generate HTML file"},
    "js": {"type": "code", "ext": "js", "desc": "Generate JavaScript file"},
    "ts": {"type": "code", "ext": "ts", "desc": "Generate TypeScript file"},
    "jsx": {"type": "code", "ext": "jsx", "desc": "Generate JSX file"},
    "tsx": {"type": "code", "ext": "tsx", "desc": "Generate TSX file"},
    "css": {"type": "code", "ext": "css", "desc": "Generate CSS stylesheet"},
    "md": {"type": "code", "ext": "md", "desc": "Generate Markdown file"},
    "json": {"type": "data", "ext": "json", "desc": "Generate JSON file"},
    "yaml": {"type": "data", "ext": "yaml", "desc": "Generate YAML file"},
    "txt": {"type": "code", "ext": "txt", "desc": "Generate text file"},
    "csv": {"type": "data", "ext": "csv", "desc": "Generate CSV file"},
    
    # Quick Actions
    "search": {"type": "search", "desc": "Search the web"},
    "browse": {"type": "browser", "desc": "Browse a URL and extract info"},
    "scrape": {"type": "scrape", "desc": "Scrape data from a webpage"},
    
    # Workflow Shortcuts
    "campaign": {"type": "workflow", "workflow": "full_campaign", "desc": "Create a full marketing campaign"},
    "blog": {"type": "workflow", "workflow": "blog_post", "desc": "Create a blog post with images"},
    "product": {"type": "workflow", "workflow": "product_creation", "desc": "Create a product with mockups"},
    
    # Chain/Multi-step
    "chain": {"type": "chain", "desc": "Execute multiple steps: /chain image:prompt | video:prompt"},
    
    # System Commands (OpenClaw-style)
    "status": {"type": "system", "action": "status", "desc": "Show system status and health"},
    "reset": {"type": "system", "action": "reset", "desc": "Reset conversation context"},
    "models": {"type": "system", "action": "models", "desc": "List available AI models"},
    "tools": {"type": "system", "action": "tools", "desc": "List available tools by category"},
    "verbose": {"type": "system", "action": "verbose", "desc": "Toggle verbose output mode"},
    "health": {"type": "system", "action": "health", "desc": "Show detailed system health"},
    "version": {"type": "system", "action": "version", "desc": "Show Otto version info"},
}


class SlashCommandProcessor:
    """
    Process slash commands and generate appropriate outputs.
    Supports file generation, media creation, model calls, and workflow chaining.
    """
    
    def __init__(self, orchestrator=None, tool_registry=None):
        """
        Initialize the slash command processor.
        
        Args:
            orchestrator: The agent orchestrator for executing complex tasks
            tool_registry: The tool registry for accessing tools
        """
        self.orchestrator = orchestrator
        self.tool_registry = tool_registry
        self.output_dir = Path("data/slash_outputs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def parse_command(self, message: str) -> Tuple[Optional[str], str]:
        """
        Parse a message to extract slash command and prompt.
        
        Args:
            message: The user's message
            
        Returns:
            Tuple of (command, prompt) where command is None if not a slash command
        """
        message = message.strip()
        if not message.startswith("/"):
            return None, message
        
        # Extract command and prompt
        parts = message[1:].split(" ", 1)
        command = parts[0].lower()
        prompt = parts[1] if len(parts) > 1 else ""
        
        return command, prompt
    
    def is_slash_command(self, message: str) -> bool:
        """Check if message is a valid slash command."""
        if not message.strip().startswith("/"):
            return False
        command, _ = self.parse_command(message)
        return command in SLASH_COMMANDS or command in AI_MODELS
    
    async def execute(self, message: str, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Execute a slash command and return results.
        
        Args:
            message: The full message with slash command
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dict with success status and results/error
        """
        command, prompt = self.parse_command(message)
        
        if not command:
            return {"success": False, "error": "No command found"}
        
        # Help command
        if command in ("help", "commands"):
            return self._show_help()
        
        # Chain command for multi-step execution
        if command == "chain":
            return await self._execute_chain(prompt, progress_callback)
        
        # Registered slash commands
        if command in SLASH_COMMANDS:
            cmd_info = SLASH_COMMANDS[command]
            cmd_type = cmd_info["type"]
            
            if cmd_type == "code":
                return await self._generate_code_file(command, prompt, cmd_info)
            elif cmd_type == "data":
                return await self._generate_data_file(command, prompt, cmd_info)
            elif cmd_type == "workflow":
                return await self._execute_workflow(command, prompt, cmd_info)
            elif cmd_type in ("browser", "search", "scrape"):
                return await self._execute_browser_task(command, prompt, cmd_info)
            elif cmd_type == "system":
                return await self._handle_system_command(command, prompt, cmd_info)
        
        # Direct AI model calls
        if command in AI_MODELS:
            return await self._call_model(command, prompt)
        
        return {"success": False, "error": f"Unknown command: /{command}"}
    
    def _show_help(self) -> Dict[str, Any]:
        """Generate help message showing all available commands."""
        help_text = """## 🚀 Otto Slash Commands

Type a command followed by your prompt, e.g., `/image a sunset over mountains`

### 🎨 Media Generation
| Command | Description |
|---------|-------------|
| `/image` | Generate AI images (Flux Schnell) |
| `/flux-dev` | High-quality images (Flux Dev) |
| `/video` | Generate video clips |
| `/music` | Generate music tracks |
| `/speak`, `/tts` | Text-to-speech |

### 📄 Code & Files
| Command | Description |
|---------|-------------|
| `/python`, `/py` | Generate Python script |
| `/html` | Generate HTML file |
| `/js`, `/ts` | Generate JavaScript/TypeScript |
| `/jsx`, `/tsx` | Generate React components |
| `/css` | Generate CSS stylesheet |
| `/md` | Generate Markdown file |
| `/json`, `/yaml` | Generate data files |

### 🔧 Quick Actions
| Command | Description |
|---------|-------------|
| `/search` | Search the web |
| `/browse` | Browse a URL |
| `/scrape` | Scrape webpage data |

### 🎯 Workflows
| Command | Description |
|---------|-------------|
| `/campaign` | Create a marketing campaign |
| `/blog` | Create a blog post with images |
| `/product` | Create a product with mockups |

### 🔗 Advanced
| Command | Description |
|---------|-------------|
| `/chain` | Multi-step execution |

### ⚙️ System Commands
| Command | Description |
|---------|-------------|
| `/status` | Show system status and health |
| `/health` | Detailed health check |
| `/models` | List available AI models |
| `/tools` | List available tools by category |
| `/reset` | Reset conversation context |
| `/verbose` | Toggle verbose output |
| `/version` | Show Otto version info |

**Example:** `/chain image:cyberpunk city | video:animate the city`
"""
        return {
            "success": True,
            "type": "help",
            "message": help_text
        }
    
    async def _handle_system_command(
        self, 
        command: str, 
        prompt: str, 
        cmd_info: Dict
    ) -> Dict[str, Any]:
        """Handle system-level commands like /status, /reset, /models, /tools."""
        action = cmd_info.get("action", "")
        
        if action == "status":
            return await self._get_system_status()
        elif action == "reset":
            return self._reset_context()
        elif action == "models":
            return self._list_models()
        elif action == "tools":
            return self._list_tools(prompt)
        elif action == "verbose":
            return self._toggle_verbose()
        elif action == "health":
            return await self._get_detailed_health()
        elif action == "version":
            return self._get_version()
        
        return {"success": False, "error": f"Unknown system action: {action}"}
    
    async def _get_system_status(self) -> Dict[str, Any]:
        """Get system status including uptime, memory, and service health."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_str = f"{cpu_percent:.1f}%"
            mem_str = f"{memory.percent:.1f}% ({memory.used // (1024**3):.1f} GB / {memory.total // (1024**3):.1f} GB)"
            avail_str = f"{memory.available // (1024**3):.1f} GB"
            mem_percent = memory.percent
        except ImportError:
            cpu_str = "N/A (psutil not installed)"
            mem_str = "N/A"
            avail_str = "N/A"
            cpu_percent = 0
            mem_percent = 0
        
        # Check services
        services = {
            "orchestrator": self.orchestrator is not None,
            "tool_registry": self.tool_registry is not None,
        }
        
        # Count tools
        tool_count = 0
        if self.tool_registry:
            try:
                tools = self.tool_registry.list_tools()
                tool_count = len(tools) if tools else 0
            except:
                pass
        
        status_text = f"""## 📊 Otto System Status

### 🖥️ System Resources
| Metric | Value |
|--------|-------|
| CPU Usage | {cpu_str} |
| Memory Used | {mem_str} |
| Available Memory | {avail_str} |

### 🔧 Services
| Service | Status |
|---------|--------|
| Orchestrator | {'✅ Active' if services['orchestrator'] else '❌ Inactive'} |
| Tool Registry | {'✅ Active' if services['tool_registry'] else '❌ Inactive'} |
| Tools Available | {tool_count} |

### 🎯 Capabilities
- **Slash Commands**: {len(SLASH_COMMANDS)} commands available
- **AI Models**: {len(AI_MODELS)} models registered
"""
        return {
            "success": True,
            "type": "status",
            "message": status_text,
            "data": {
                "cpu_percent": cpu_percent,
                "memory_percent": mem_percent,
                "services": services,
                "tool_count": tool_count
            }
        }
    
    def _reset_context(self) -> Dict[str, Any]:
        """Reset the conversation context."""
        # This would typically clear conversation history
        # The actual reset happens at the API level
        return {
            "success": True,
            "type": "reset",
            "message": "✅ **Conversation Reset**\n\nYour conversation context has been cleared. Start fresh!",
            "action": "clear_context"  # Signal to chat endpoint to clear history
        }
    
    def _list_models(self) -> Dict[str, Any]:
        """List all available AI models."""
        model_list = []
        
        for name, info in AI_MODELS.items():
            model_list.append(f"| `/{name}` | {info.get('desc', 'No description')} | {info.get('type', 'unknown')} |")
        
        models_text = f"""## 🤖 Available AI Models

| Command | Description | Type |
|---------|-------------|------|
{chr(10).join(model_list)}

### Quick Examples
- `/image a futuristic cityscape` - Generate an image
- `/video a timelapse of clouds` - Generate a video
- `/music upbeat electronic track` - Generate music
- `/speak Hello world` - Text-to-speech
"""
        return {
            "success": True,
            "type": "models",
            "message": models_text,
            "models": list(AI_MODELS.keys())
        }
    
    def _list_tools(self, category_filter: str = "") -> Dict[str, Any]:
        """List available tools, optionally filtered by category."""
        if not self.tool_registry:
            return {
                "success": False,
                "error": "Tool registry not available"
            }
        
        try:
            all_tools = self.tool_registry.list_tools()
            categories = self.tool_registry.get_categories() if hasattr(self.tool_registry, 'get_categories') else []
            
            # Build tool list
            tool_sections = []
            
            if category_filter:
                # Filter by category
                filtered = [t for t in all_tools if t.get('category', '').lower() == category_filter.lower()]
                tool_sections.append(f"### {category_filter.title()} Tools")
                for tool in filtered[:20]:  # Limit display
                    tool_sections.append(f"- **{tool.get('name', 'Unknown')}**: {tool.get('description', 'No description')[:60]}")
            else:
                # Group by category
                by_category = {}
                for tool in all_tools:
                    cat = tool.get('category', 'Other')
                    if cat not in by_category:
                        by_category[cat] = []
                    by_category[cat].append(tool)
                
                for cat, tools in sorted(by_category.items()):
                    tool_sections.append(f"\n### {cat} ({len(tools)} tools)")
                    for tool in tools[:5]:  # Show first 5 per category
                        tool_sections.append(f"- **{tool.get('name', 'Unknown')}**")
                    if len(tools) > 5:
                        tool_sections.append(f"  *...and {len(tools) - 5} more*")
            
            tools_text = f"""## 🛠️ Available Tools

**Total Tools:** {len(all_tools)}
**Categories:** {', '.join(categories) if categories else 'N/A'}

{chr(10).join(tool_sections)}

💡 **Tip:** Use `/tools <category>` to see tools in a specific category.
"""
            return {
                "success": True,
                "type": "tools",
                "message": tools_text,
                "tool_count": len(all_tools),
                "categories": categories
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error listing tools: {str(e)}"
            }
    
    def _toggle_verbose(self) -> Dict[str, Any]:
        """Toggle verbose output mode."""
        # This would typically be stored in a session/context
        return {
            "success": True,
            "type": "verbose",
            "message": "🔊 **Verbose Mode Toggled**\n\nVerbose output has been toggled. (Note: Implement session-based toggle for persistence)",
            "action": "toggle_verbose"
        }
    
    async def _get_detailed_health(self) -> Dict[str, Any]:
        """Get detailed health check information."""
        from datetime import datetime
        
        checks = {
            "api": {"status": "healthy", "latency_ms": 0},
            "memory": {"status": "unknown", "usage_percent": 0},
            "disk": {"status": "unknown", "usage_percent": 0},
            "orchestrator": {"status": "unknown"},
            "tools": {"status": "unknown", "count": 0}
        }
        
        try:
            import psutil
            # Memory check
            mem = psutil.virtual_memory()
            checks["memory"]["usage_percent"] = mem.percent
            checks["memory"]["status"] = "healthy" if mem.percent < 80 else "warning" if mem.percent < 95 else "critical"
            
            # Disk check
            disk = psutil.disk_usage('/')
            checks["disk"]["usage_percent"] = disk.percent
            checks["disk"]["status"] = "healthy" if disk.percent < 80 else "warning" if disk.percent < 95 else "critical"
        except ImportError:
            checks["memory"]["status"] = "unavailable"
            checks["disk"]["status"] = "unavailable"
        
        # Orchestrator check
        checks["orchestrator"]["status"] = "healthy" if self.orchestrator else "unavailable"
        
        # Tools check
        if self.tool_registry:
            try:
                tools = self.tool_registry.list_tools()
                checks["tools"]["count"] = len(tools) if tools else 0
                checks["tools"]["status"] = "healthy" if tools else "empty"
            except:
                checks["tools"]["status"] = "error"
        
        # Overall health
        statuses = [c["status"] for c in checks.values() if "status" in c]
        overall = "healthy"
        if "critical" in statuses:
            overall = "critical"
        elif "error" in statuses or "unavailable" in statuses:
            overall = "degraded" 
        elif "warning" in statuses:
            overall = "warning"
        
        status_emoji = {"healthy": "✅", "warning": "⚠️", "degraded": "🟡", "critical": "❌"}
        
        health_text = f"""## 🏥 Otto Health Check

**Overall Status:** {status_emoji.get(overall, '❓')} {overall.upper()}
**Timestamp:** {datetime.now().isoformat()}

### Component Health
| Component | Status | Details |
|-----------|--------|---------|
| API | {status_emoji.get(checks['api']['status'], '❓')} {checks['api']['status']} | Response OK |
| Memory | {status_emoji.get(checks['memory']['status'], '❓')} {checks['memory']['status']} | {checks['memory']['usage_percent']:.1f}% used |
| Disk | {status_emoji.get(checks['disk']['status'], '❓')} {checks['disk']['status']} | {checks['disk']['usage_percent']:.1f}% used |
| Orchestrator | {status_emoji.get(checks['orchestrator']['status'], '❓')} {checks['orchestrator']['status']} | AI Processing |
| Tool Registry | {status_emoji.get(checks['tools']['status'], '❓')} {checks['tools']['status']} | {checks['tools']['count']} tools |

### Thresholds
- **Healthy**: < 80% resource usage
- **Warning**: 80-95% resource usage  
- **Critical**: > 95% resource usage
"""
        return {
            "success": True,
            "type": "health",
            "message": health_text,
            "overall": overall,
            "checks": checks
        }
    
    def _get_version(self) -> Dict[str, Any]:
        """Get Otto version information."""
        version_text = """## 📦 Otto Version Info

| Property | Value |
|----------|-------|
| Version | 2.0.0 |
| Codename | Universal |
| Framework | FastAPI |
| Python | 3.11+ |

### Features
- 🤖 Multi-agent orchestration
- 🎨 AI media generation (images, video, audio)
- 🛒 E-commerce integrations (Printify, Shopify)
- 🌐 Browser automation
- 💬 Slash commands
- 📊 Analytics & workflows

### Links
- GitHub: otto-universal
- Docs: /docs folder
"""
        return {
            "success": True,
            "type": "version",
            "message": version_text,
            "version": "2.0.0",
            "codename": "Universal"
        }
    
    async def _generate_code_file(
        self, 
        command: str, 
        prompt: str, 
        cmd_info: Dict
    ) -> Dict[str, Any]:
        """Generate a code file based on the prompt."""
        ext = cmd_info.get("ext", "txt")
        
        if not prompt:
            return {
                "success": False,
                "error": f"Please provide a description. Example: `/{command} a function to sort numbers`"
            }
        
        # Use the orchestrator to generate code
        if self.orchestrator:
            try:
                result = await self.orchestrator.process(
                    message=f"Generate {ext} code: {prompt}. Return ONLY the code, no explanations.",
                    context={"slash_command": command, "code_generation": True}
                )
                content = result.get("response", "")
                
                # Clean up the response - extract code from markdown if present
                if f"```{ext}" in content:
                    start = content.find(f"```{ext}") + len(f"```{ext}")
                    end = content.find("```", start)
                    content = content[start:end].strip()
                elif "```" in content:
                    start = content.find("```") + 3
                    # Skip language indicator if present
                    if content[start:].startswith(ext):
                        start += len(ext)
                    end = content.find("```", start)
                    content = content[start:end].strip()
                
                # Generate filename
                filename = self._generate_filename(prompt, ext)
                filepath = self.output_dir / filename
                
                # Save the file
                with open(filepath, "w") as f:
                    f.write(content)
                
                return {
                    "success": True,
                    "type": "file",
                    "file_type": ext,
                    "filename": filename,
                    "filepath": str(filepath),
                    "content": content
                }
            except Exception as e:
                logger.error(f"Code generation error: {e}")
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Orchestrator not available"}
    
    async def _generate_data_file(
        self,
        command: str,
        prompt: str,
        cmd_info: Dict
    ) -> Dict[str, Any]:
        """Generate a data file (JSON, YAML, CSV, etc.)."""
        ext = cmd_info.get("ext", "json")
        
        if not prompt:
            return {
                "success": False,
                "error": f"Please provide a description. Example: `/{command} list of countries with capitals`"
            }
        
        # Use orchestrator to generate data
        if self.orchestrator:
            try:
                result = await self.orchestrator.process(
                    message=f"Generate {ext.upper()} data: {prompt}. Return ONLY the {ext.upper()} data, no explanations.",
                    context={"slash_command": command, "data_generation": True}
                )
                content = result.get("response", "")
                
                # Clean up - extract from markdown if present
                if f"```{ext}" in content:
                    start = content.find(f"```{ext}") + len(f"```{ext}")
                    end = content.find("```", start)
                    content = content[start:end].strip()
                elif "```" in content:
                    start = content.find("```") + 3
                    end = content.find("```", start)
                    content = content[start:end].strip()
                
                # Generate filename
                filename = self._generate_filename(prompt, ext)
                filepath = self.output_dir / filename
                
                # Save the file
                with open(filepath, "w") as f:
                    f.write(content)
                
                return {
                    "success": True,
                    "type": "file",
                    "file_type": ext,
                    "filename": filename,
                    "filepath": str(filepath),
                    "content": content
                }
            except Exception as e:
                logger.error(f"Data generation error: {e}")
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Orchestrator not available"}
    
    async def _call_model(self, command: str, prompt: str) -> Dict[str, Any]:
        """Call an AI model directly."""
        model_info = AI_MODELS.get(command)
        if not model_info:
            return {"success": False, "error": f"Unknown model: {command}"}
        
        if not prompt:
            return {
                "success": False,
                "error": f"Please provide a prompt. Example: `/{command} a beautiful sunset`"
            }
        
        model_type = model_info.get("type", "image")
        
        # Use orchestrator to execute the appropriate tool
        if self.orchestrator:
            try:
                # Map model type to tool call
                if model_type == "image":
                    result = await self.orchestrator.process(
                        message=f"Generate an image: {prompt}",
                        context={"slash_command": command, "model": model_info["model"]}
                    )
                elif model_type == "video":
                    result = await self.orchestrator.process(
                        message=f"Generate a video: {prompt}",
                        context={"slash_command": command, "model": model_info["model"]}
                    )
                elif model_type == "audio":
                    result = await self.orchestrator.process(
                        message=f"Generate music: {prompt}",
                        context={"slash_command": command, "model": model_info["model"]}
                    )
                elif model_type == "speech":
                    result = await self.orchestrator.process(
                        message=f"Convert to speech: {prompt}",
                        context={"slash_command": command}
                    )
                else:
                    result = await self.orchestrator.process(
                        message=prompt,
                        context={"slash_command": command}
                    )
                
                return {
                    "success": True,
                    "type": "media",
                    "media_type": model_type,
                    "message": result.get("response", ""),
                    "artifacts": result.get("artifacts", [])
                }
            except Exception as e:
                logger.error(f"Model call error: {e}")
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Orchestrator not available"}
    
    async def _execute_workflow(
        self,
        command: str,
        prompt: str,
        cmd_info: Dict
    ) -> Dict[str, Any]:
        """Execute a predefined workflow."""
        workflow = cmd_info.get("workflow", "")
        
        if not prompt:
            return {
                "success": False,
                "error": f"Please provide a topic/description. Example: `/{command} eco-friendly products`"
            }
        
        # Use orchestrator to execute workflow
        if self.orchestrator:
            try:
                # Map workflow to detailed request
                if workflow == "full_campaign":
                    message = f"Create a complete marketing campaign for: {prompt}. Include social media posts, images, and a content calendar."
                elif workflow == "blog_post":
                    message = f"Write a blog post about: {prompt}. Include an image for the header."
                elif workflow == "product_creation":
                    message = f"Create a product design for: {prompt}. Generate mockups and product descriptions."
                else:
                    message = prompt
                
                result = await self.orchestrator.process(
                    message=message,
                    context={"slash_command": command, "workflow": workflow}
                )
                
                return {
                    "success": True,
                    "type": "workflow",
                    "workflow": workflow,
                    "message": result.get("response", ""),
                    "artifacts": result.get("artifacts", [])
                }
            except Exception as e:
                logger.error(f"Workflow error: {e}")
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Orchestrator not available"}
    
    async def _execute_browser_task(
        self,
        command: str,
        prompt: str,
        cmd_info: Dict
    ) -> Dict[str, Any]:
        """Execute a browser-based task."""
        if not prompt:
            return {
                "success": False,
                "error": f"Please provide a URL or search query. Example: `/{command} https://example.com`"
            }
        
        if self.orchestrator:
            try:
                if command == "search":
                    message = f"Search the web for: {prompt}"
                elif command == "scrape":
                    message = f"Scrape data from: {prompt}"
                else:  # browse
                    message = f"Browse and summarize: {prompt}"
                
                result = await self.orchestrator.process(
                    message=message,
                    context={"slash_command": command, "browser_task": True}
                )
                
                return {
                    "success": True,
                    "type": "browser",
                    "message": result.get("response", "")
                }
            except Exception as e:
                logger.error(f"Browser task error: {e}")
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Orchestrator not available"}
    
    async def _execute_chain(
        self,
        prompt: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Execute a chain of commands.
        
        Format: /chain command1:prompt1 | command2:prompt2 | ...
        """
        if not prompt:
            return {
                "success": False,
                "error": "Please provide chain steps. Example: `/chain image:a cat | video:animate the cat`"
            }
        
        # Parse the chain
        steps = [s.strip() for s in prompt.split("|")]
        results = []
        artifacts = []
        
        for i, step in enumerate(steps):
            step = step.strip()
            if ":" not in step:
                results.append({
                    "step": i + 1,
                    "success": False,
                    "error": f"Invalid step format: {step}. Use command:prompt"
                })
                continue
            
            cmd, step_prompt = step.split(":", 1)
            cmd = cmd.strip().lower()
            step_prompt = step_prompt.strip()
            
            # Progress callback
            if progress_callback:
                progress_callback({
                    "step": i + 1,
                    "total": len(steps),
                    "name": f"/{cmd}",
                    "status": "running"
                })
            
            # Execute the step
            step_result = await self.execute(f"/{cmd} {step_prompt}")
            
            results.append({
                "step": i + 1,
                "command": cmd,
                "success": step_result.get("success", False),
                "message": step_result.get("message", ""),
                "error": step_result.get("error", "")
            })
            
            # Collect artifacts
            if step_result.get("artifacts"):
                artifacts.extend(step_result["artifacts"])
            
            # Progress callback - completed
            if progress_callback:
                progress_callback({
                    "step": i + 1,
                    "total": len(steps),
                    "name": f"/{cmd}",
                    "status": "completed" if step_result.get("success") else "failed",
                    "result": step_result
                })
        
        successful = sum(1 for r in results if r.get("success"))
        
        return {
            "success": successful == len(results),
            "type": "chain",
            "steps_completed": successful,
            "steps_total": len(results),
            "results": results,
            "artifacts": artifacts
        }
    
    def _generate_filename(self, prompt: str, ext: str) -> str:
        """Generate a filename from a prompt."""
        import re
        from datetime import datetime
        
        # Clean prompt for filename
        clean = re.sub(r'[^\w\s-]', '', prompt.lower())
        clean = re.sub(r'[-\s]+', '_', clean)
        clean = clean[:30]  # Limit length
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{clean}_{timestamp}.{ext}"


# ============================================================================
# SINGLETON
# ============================================================================
_slash_processor: Optional[SlashCommandProcessor] = None


def get_slash_processor(orchestrator=None, tool_registry=None) -> SlashCommandProcessor:
    """Get or create the slash command processor singleton."""
    global _slash_processor
    if _slash_processor is None:
        _slash_processor = SlashCommandProcessor(orchestrator, tool_registry)
    elif orchestrator is not None:
        _slash_processor.orchestrator = orchestrator
    return _slash_processor
