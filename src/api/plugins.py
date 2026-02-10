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
