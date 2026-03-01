"""
Plugin Management API
=====================

REST API endpoints for managing Otto plugins.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging

from ..core.plugin_system import get_plugin_manager, PluginStatus, PluginType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/plugins", tags=["plugins"])


class PluginSettingsUpdate(BaseModel):
    """Request body for updating plugin settings."""
    settings: Dict[str, Any]


class PluginCreateRequest(BaseModel):
    """Request body for creating a new plugin."""
    name: str
    description: str
    plugin_type: str = "tool"


class PluginInfo(BaseModel):
    """Plugin information response."""
    id: str
    name: str
    version: str
    description: str
    author: str
    plugin_type: str
    status: str
    tags: List[str] = []
    provides_tools: List[str] = []
    provides_integrations: List[str] = []
    error: Optional[str] = None


@router.get("")
async def list_plugins() -> Dict[str, Any]:
    """List all available plugins."""
    manager = get_plugin_manager()
    
    plugins = []
    for plugin in manager.get_plugins():
        plugins.append({
            "id": plugin.id,
            "name": plugin.metadata.name,
            "version": plugin.metadata.version,
            "description": plugin.metadata.description,
            "author": plugin.metadata.author,
            "type": plugin.metadata.plugin_type.value,
            "status": plugin.status.value,
            "tags": plugin.metadata.tags,
            "provides_tools": plugin.metadata.provides_tools,
            "error": plugin.error
        })
    
    return {
        "total": len(plugins),
        "active": len([p for p in plugins if p["status"] == "active"]),
        "plugins": plugins
    }


@router.get("/{plugin_id}")
async def get_plugin(plugin_id: str) -> Dict[str, Any]:
    """Get detailed information about a plugin."""
    manager = get_plugin_manager()
    
    # Find plugin by ID or name
    for plugin in manager.get_plugins():
        if plugin.id == plugin_id or plugin.metadata.name == plugin_id:
            result = {
                "id": plugin.id,
                "name": plugin.metadata.name,
                "version": plugin.metadata.version,
                "description": plugin.metadata.description,
                "author": plugin.metadata.author,
                "type": plugin.metadata.plugin_type.value,
                "status": plugin.status.value,
                "tags": plugin.metadata.tags,
                "provides_tools": plugin.metadata.provides_tools,
                "provides_integrations": plugin.metadata.provides_integrations,
                "settings_schema": plugin.metadata.settings_schema,
                "settings": plugin.settings,
                "path": str(plugin.path),
                "error": plugin.error
            }
            
            # Include tools if active
            if plugin.instance and plugin.status == PluginStatus.ACTIVE:
                result["tools"] = plugin.instance.get_tools()
            
            return result
    
    raise HTTPException(status_code=404, detail="Plugin not found")


@router.post("/{plugin_id}/enable")
async def enable_plugin(plugin_id: str) -> Dict[str, Any]:
    """Enable and load a plugin."""
    manager = get_plugin_manager()
    
    # Find plugin
    target = None
    for plugin in manager.get_plugins():
        if plugin.id == plugin_id or plugin.metadata.name == plugin_id:
            target = plugin
            break
    
    if not target:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    success = await manager.load_plugin(target.id)
    
    if success:
        return {
            "success": True,
            "message": f"Plugin '{target.metadata.name}' enabled",
            "status": target.status.value
        }
    else:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to enable plugin: {target.error}"
        )


@router.post("/{plugin_id}/disable")
async def disable_plugin(plugin_id: str) -> Dict[str, Any]:
    """Disable and unload a plugin."""
    manager = get_plugin_manager()
    
    # Find plugin
    target = None
    for plugin in manager.get_plugins():
        if plugin.id == plugin_id or plugin.metadata.name == plugin_id:
            target = plugin
            break
    
    if not target:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    success = await manager.unload_plugin(target.id)
    
    return {
        "success": success,
        "message": f"Plugin '{target.metadata.name}' disabled" if success else "Failed to disable",
        "status": target.status.value
    }


@router.post("/{plugin_id}/settings")
async def update_plugin_settings(
    plugin_id: str, 
    request: PluginSettingsUpdate
) -> Dict[str, Any]:
    """Update plugin settings."""
    manager = get_plugin_manager()
    
    # Find plugin
    target = None
    for plugin in manager.get_plugins():
        if plugin.id == plugin_id or plugin.metadata.name == plugin_id:
            target = plugin
            break
    
    if not target:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    # Update settings
    target.settings.update(request.settings)
    
    # Reload if active
    if target.status == PluginStatus.ACTIVE:
        await manager.unload_plugin(target.id)
        await manager.load_plugin(target.id)
    
    return {
        "success": True,
        "message": "Settings updated",
        "settings": target.settings
    }


@router.post("/create")
async def create_plugin(request: PluginCreateRequest) -> Dict[str, Any]:
    """Create a new plugin scaffold."""
    manager = get_plugin_manager()
    
    try:
        plugin_type = PluginType(request.plugin_type)
    except ValueError:
        plugin_type = PluginType.TOOL
    
    try:
        path = await manager.create_plugin(
            name=request.name,
            description=request.description,
            plugin_type=plugin_type
        )
        
        return {
            "success": True,
            "message": f"Plugin created at {path}",
            "path": str(path),
            "name": request.name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/all")
async def get_all_plugin_tools() -> Dict[str, Any]:
    """Get all tools from all active plugins."""
    manager = get_plugin_manager()
    tools = manager.get_all_tools()
    
    return {
        "total": len(tools),
        "tools": list(tools.values())
    }


@router.post("/discover")
async def discover_plugins() -> Dict[str, Any]:
    """Rescan plugin directories for new plugins."""
    manager = get_plugin_manager()
    
    plugins = await manager.discover_plugins()
    
    return {
        "success": True,
        "discovered": len(plugins),
        "plugins": [
            {
                "id": p.id,
                "name": p.metadata.name,
                "version": p.metadata.version,
                "status": p.status.value
            }
            for p in plugins
        ]
    }


@router.post("/reload")
async def reload_all_plugins() -> Dict[str, Any]:
    """Reload all plugins."""
    manager = get_plugin_manager()
    
    # Unload all
    for plugin in manager.get_active_plugins():
        await manager.unload_plugin(plugin.id)
    
    # Rediscover
    await manager.discover_plugins()
    
    # Reload enabled
    await manager.load_enabled_plugins()
    
    active = manager.get_active_plugins()
    
    return {
        "success": True,
        "message": f"Reloaded {len(active)} plugins",
        "active_plugins": [p.metadata.name for p in active]
    }


class PluginInstallRequest(BaseModel):
    """Request body for installing a plugin from URL."""
    source: str  # GitHub URL or plugin name
    type: Optional[str] = None  # 'featured' for built-in extensions
    pip_packages: Optional[str] = None  # Space-separated pip packages
    api_keys: Optional[Dict[str, str]] = None  # API keys to configure
    tools: Optional[List[str]] = None  # Tools this plugin provides


@router.post("/install")
async def install_plugin(request: PluginInstallRequest) -> Dict[str, Any]:
    """Install a plugin from a GitHub URL, plugin registry, or featured extensions."""
    import subprocess
    import os
    import shutil
    import json
    from pathlib import Path
    
    source = request.source.strip()
    plugins_dir = Path("plugins")
    plugins_dir.mkdir(exist_ok=True)
    
    # Handle featured plugins (built-in third-party extensions)
    if request.type == "featured":
        plugin_name = source
        plugin_path = plugins_dir / plugin_name
        
        # Install pip packages
        if request.pip_packages:
            packages = request.pip_packages.split()
            logger.info(f"Installing pip packages for {plugin_name}: {packages}")
            
            try:
                for package in packages:
                    result = subprocess.run(
                        ["pip", "install", package, "-q"],
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    if result.returncode != 0:
                        logger.warning(f"pip install {package} stderr: {result.stderr}")
            except Exception as e:
                logger.error(f"Failed to install pip packages: {e}")
        
        # Store API keys in .env or plugin config
        if request.api_keys:
            env_path = Path(".env")
            existing_env = {}
            if env_path.exists():
                with open(env_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if "=" in line and not line.startswith("#"):
                            key, val = line.split("=", 1)
                            existing_env[key] = val
            
            # Add new API keys
            for key, value in request.api_keys.items():
                if value:  # Only add if value provided
                    existing_env[key] = value
                    os.environ[key] = value  # Set in current process too
            
            # Write back
            with open(env_path, "w") as f:
                for key, value in existing_env.items():
                    f.write(f"{key}={value}\n")
            
            logger.info(f"Stored API keys for {plugin_name}")
        
        # Create plugin manifest
        plugin_path.mkdir(exist_ok=True)
        manifest = {
            "name": plugin_name,
            "version": "1.0.0",
            "description": f"{plugin_name.title()} integration plugin",
            "author": "Otto Universal",
            "plugin_type": "tool",
            "provides_tools": request.tools or [],
            "pip_packages": request.pip_packages,
            "api_keys_configured": list(request.api_keys.keys()) if request.api_keys else []
        }
        
        with open(plugin_path / "manifest.json", "w") as f:
            json.dump(manifest, f, indent=2)
        
        # Create plugin Python file
        plugin_code = f'''"""
{plugin_name.title()} Plugin
=========================

Auto-installed third-party extension plugin.
"""

from typing import Any, Dict, List
import os

class {plugin_name.title().replace("-", "")}Plugin:
    """Plugin wrapper for {plugin_name.title()} integration."""
    
    def __init__(self):
        self.name = "{plugin_name}"
        self.tools = {request.tools or []}
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Return available tools from this plugin."""
        return [
            {{
                "name": tool,
                "description": f"{plugin_name.title()} {{tool}} function",
                "parameters": {{"type": "object", "properties": {{}}}}
            }}
            for tool in self.tools
        ]
    
    async def execute(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool from this plugin."""
        # Import the actual library dynamically
        try:
            if "{plugin_name}" == "langchain":
                from langchain_openai import ChatOpenAI
                return {{"status": "langchain ready", "tools": self.tools}}
            elif "{plugin_name}" == "crewai":
                from crewai import Agent, Task, Crew
                return {{"status": "crewai ready", "tools": self.tools}}
            elif "{plugin_name}" == "serper":
                import requests
                api_key = os.getenv("SERPER_API_KEY")
                return {{"status": "serper ready", "has_key": bool(api_key)}}
            elif "{plugin_name}" == "elevenlabs":
                from elevenlabs import ElevenLabs
                return {{"status": "elevenlabs ready"}}
            elif "{plugin_name}" == "firecrawl":
                from firecrawl import FirecrawlApp
                return {{"status": "firecrawl ready"}}
            elif "{plugin_name}" == "e2b":
                from e2b_code_interpreter import CodeInterpreter
                return {{"status": "e2b ready"}}
            elif "{plugin_name}" == "supabase":
                from supabase import create_client
                return {{"status": "supabase ready"}}
            else:
                return {{"status": "unknown plugin", "name": "{plugin_name}"}}
        except ImportError as e:
            return {{"error": f"Module not installed: {{e}}"}}


def get_plugin():
    """Plugin entry point."""
    return {plugin_name.title().replace("-", "")}Plugin()
'''
        
        with open(plugin_path / "plugin.py", "w") as f:
            f.write(plugin_code)
        
        # Rediscover plugins
        manager = get_plugin_manager()
        await manager.discover_plugins()
        
        return {
            "success": True,
            "name": plugin_name,
            "version": "1.0.0",
            "tools": request.tools or [],
            "message": f"Installed {plugin_name} with tools: {', '.join(request.tools or [])}"
        }
    
    # Determine if it's a GitHub URL
    if source.startswith(("https://github.com/", "git@github.com:", "github.com/")):
        # Normalize GitHub URL
        if source.startswith("github.com/"):
            source = "https://" + source
        
        # Extract repo name for plugin folder
        repo_name = source.rstrip("/").split("/")[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
        
        plugin_path = plugins_dir / repo_name
        
        # Check if already exists
        if plugin_path.exists():
            raise HTTPException(status_code=400, detail=f"Plugin '{repo_name}' already exists")
        
        try:
            # Clone the repository
            result = subprocess.run(
                ["git", "clone", "--depth", "1", source, str(plugin_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to clone repository: {result.stderr}"
                )
            
            # Remove .git folder to save space
            git_folder = plugin_path / ".git"
            if git_folder.exists():
                shutil.rmtree(git_folder)
            
            # Rediscover plugins
            manager = get_plugin_manager()
            await manager.discover_plugins()
            
            # Try to find and load the new plugin
            for plugin in manager.get_plugins():
                if plugin.path and plugin_path in Path(plugin.path).parents or Path(plugin.path) == plugin_path:
                    await manager.load_plugin(plugin.id)
                    return {
                        "success": True,
                        "name": plugin.metadata.name,
                        "version": plugin.metadata.version,
                        "message": f"Installed and loaded {plugin.metadata.name}"
                    }
            
            return {
                "success": True,
                "name": repo_name,
                "message": f"Cloned {repo_name}. Run 'Discover' to detect plugin."
            }
            
        except subprocess.TimeoutExpired:
            # Clean up partial clone
            if plugin_path.exists():
                shutil.rmtree(plugin_path)
            raise HTTPException(status_code=500, detail="Clone timed out")
            
        except Exception as e:
            # Clean up on error
            if plugin_path.exists():
                shutil.rmtree(plugin_path)
            raise HTTPException(status_code=500, detail=str(e))
    
    else:
        # Treat as a plugin name - check official registry (placeholder)
        raise HTTPException(
            status_code=400, 
            detail="Plugin registry not implemented yet. Please provide a GitHub URL."
        )

