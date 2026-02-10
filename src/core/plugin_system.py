"""
Plugin System
=============

A modular plugin architecture for extending Otto with:
- Custom tools
- New integrations
- Specialized agents
- UI extensions

Plugins can be loaded from:
- Built-in plugins (./plugins/)
- User plugins (~/.otto/plugins/)
- Remote plugins (pip packages)
"""

import asyncio
import importlib
import importlib.util
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import yaml
import json

logger = logging.getLogger(__name__)


class PluginType(Enum):
    """Types of plugins."""
    TOOL = "tool"  # Adds new tools
    INTEGRATION = "integration"  # External service integration
    AGENT = "agent"  # Specialized agent
    PROCESSOR = "processor"  # Message/data processor
    UI = "ui"  # UI extension
    WORKFLOW = "workflow"  # Workflow templates


class PluginStatus(Enum):
    """Plugin lifecycle status."""
    DISCOVERED = "discovered"
    LOADING = "loading"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class PluginMetadata:
    """Plugin metadata from manifest."""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    
    # Dependencies
    requires: List[str] = field(default_factory=list)
    python_requires: str = ">=3.10"
    
    # Entry point
    entry_point: str = "main"
    
    # Capabilities
    provides_tools: List[str] = field(default_factory=list)
    provides_integrations: List[str] = field(default_factory=list)
    
    # Settings
    settings_schema: Dict[str, Any] = field(default_factory=dict)
    default_settings: Dict[str, Any] = field(default_factory=dict)
    
    # Optional
    homepage: Optional[str] = None
    license: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class Plugin:
    """A loaded plugin instance."""
    metadata: PluginMetadata
    path: Path
    status: PluginStatus = PluginStatus.DISCOVERED
    instance: Optional[Any] = None
    error: Optional[str] = None
    loaded_at: Optional[datetime] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    
    @property 
    def id(self) -> str:
        """Unique plugin identifier."""
        return f"{self.metadata.name}@{self.metadata.version}"


class PluginBase(ABC):
    """Base class for all plugins."""
    
    def __init__(self, settings: Dict[str, Any] = None):
        self.settings = settings or {}
        self._enabled = True
        
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the plugin. Called once when loaded."""
        pass
    
    async def cleanup(self) -> None:
        """Cleanup resources. Called when unloading."""
        pass
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Return tools provided by this plugin."""
        return []
    
    def get_integrations(self) -> List[Dict[str, Any]]:
        """Return integrations provided by this plugin."""
        return []
    
    def get_workflows(self) -> List[Dict[str, Any]]:
        """Return workflow templates provided by this plugin."""
        return []
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    def enable(self) -> None:
        self._enabled = True
        
    def disable(self) -> None:
        self._enabled = False


class ToolPlugin(PluginBase):
    """Base class for tool plugins."""
    
    def __init__(self, settings: Dict[str, Any] = None):
        super().__init__(settings)
        self._tools: Dict[str, Callable] = {}
    
    def register_tool(
        self,
        name: str,
        func: Callable,
        description: str = "",
        parameters: Dict[str, Any] = None
    ) -> None:
        """Register a tool function."""
        self._tools[name] = {
            "func": func,
            "description": description,
            "parameters": parameters or {}
        }
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get all registered tools."""
        return [
            {
                "name": name,
                "description": info["description"],
                "parameters": info["parameters"],
                "category": "plugin"
            }
            for name, info in self._tools.items()
        ]
    
    async def execute_tool(self, name: str, **kwargs) -> Any:
        """Execute a registered tool."""
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not found in plugin")
        
        func = self._tools[name]["func"]
        if asyncio.iscoroutinefunction(func):
            return await func(**kwargs)
        return func(**kwargs)


class IntegrationPlugin(PluginBase):
    """Base class for integration plugins."""
    
    def __init__(self, settings: Dict[str, Any] = None):
        super().__init__(settings)
        self._connected = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the external service."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the service."""
        pass
    
    @property
    def connected(self) -> bool:
        return self._connected
    
    async def health_check(self) -> Dict[str, Any]:
        """Check integration health."""
        return {
            "connected": self._connected,
            "status": "healthy" if self._connected else "disconnected"
        }


class PluginManager:
    """
    Manages plugin discovery, loading, and lifecycle.
    """
    
    # Default plugin directories
    BUILTIN_PLUGINS_DIR = Path(__file__).parent.parent / "plugins"
    USER_PLUGINS_DIR = Path.home() / ".otto" / "plugins"
    
    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}
        self._tools: Dict[str, Callable] = {}
        self._integrations: Dict[str, Any] = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the plugin manager."""
        if self._initialized:
            return
        
        # Create plugin directories
        self.BUILTIN_PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
        self.USER_PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Discover plugins
        await self.discover_plugins()
        
        # Load enabled plugins
        await self.load_enabled_plugins()
        
        self._initialized = True
        logger.info(f"Plugin manager initialized with {len(self._plugins)} plugins")
    
    async def discover_plugins(self) -> List[Plugin]:
        """Discover available plugins in all plugin directories."""
        discovered = []
        
        for plugin_dir in [self.BUILTIN_PLUGINS_DIR, self.USER_PLUGINS_DIR]:
            if not plugin_dir.exists():
                continue
            
            for item in plugin_dir.iterdir():
                if item.is_dir() and (item / "manifest.yaml").exists():
                    plugin = await self._load_manifest(item)
                    if plugin:
                        discovered.append(plugin)
                        self._plugins[plugin.id] = plugin
        
        logger.info(f"Discovered {len(discovered)} plugins")
        return discovered
    
    async def _load_manifest(self, plugin_path: Path) -> Optional[Plugin]:
        """Load plugin manifest from directory."""
        manifest_path = plugin_path / "manifest.yaml"
        
        try:
            with open(manifest_path) as f:
                data = yaml.safe_load(f)
            
            metadata = PluginMetadata(
                name=data.get("name", plugin_path.name),
                version=data.get("version", "1.0.0"),
                description=data.get("description", ""),
                author=data.get("author", "Unknown"),
                plugin_type=PluginType(data.get("type", "tool")),
                requires=data.get("requires", []),
                entry_point=data.get("entry_point", "main"),
                provides_tools=data.get("provides_tools", []),
                provides_integrations=data.get("provides_integrations", []),
                settings_schema=data.get("settings_schema", {}),
                default_settings=data.get("default_settings", {}),
                homepage=data.get("homepage"),
                license=data.get("license"),
                tags=data.get("tags", [])
            )
            
            return Plugin(metadata=metadata, path=plugin_path)
            
        except Exception as e:
            logger.error(f"Failed to load manifest from {plugin_path}: {e}")
            return None
    
    async def load_plugin(self, plugin_id: str) -> bool:
        """Load and initialize a plugin."""
        if plugin_id not in self._plugins:
            logger.error(f"Plugin '{plugin_id}' not found")
            return False
        
        plugin = self._plugins[plugin_id]
        
        if plugin.status == PluginStatus.ACTIVE:
            return True
        
        plugin.status = PluginStatus.LOADING
        
        try:
            # Import the plugin module
            module_path = plugin.path / f"{plugin.metadata.entry_point}.py"
            
            if not module_path.exists():
                raise FileNotFoundError(f"Entry point not found: {module_path}")
            
            spec = importlib.util.spec_from_file_location(
                f"otto_plugin_{plugin.metadata.name}",
                module_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find and instantiate the plugin class
            plugin_class = None
            for name in dir(module):
                obj = getattr(module, name)
                if isinstance(obj, type) and issubclass(obj, PluginBase) and obj != PluginBase:
                    plugin_class = obj
                    break
            
            if plugin_class is None:
                raise ValueError("No PluginBase subclass found in module")
            
            # Instantiate and initialize
            settings = {**plugin.metadata.default_settings, **plugin.settings}
            instance = plugin_class(settings)
            await instance.initialize()
            
            plugin.instance = instance
            plugin.status = PluginStatus.ACTIVE
            plugin.loaded_at = datetime.now()
            
            # Register tools
            for tool in instance.get_tools():
                tool_name = f"{plugin.metadata.name}.{tool['name']}"
                self._tools[tool_name] = {
                    "plugin": plugin_id,
                    **tool
                }
            
            logger.info(f"Loaded plugin: {plugin_id}")
            return True
            
        except Exception as e:
            plugin.status = PluginStatus.ERROR
            plugin.error = str(e)
            logger.error(f"Failed to load plugin '{plugin_id}': {e}")
            return False
    
    async def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a plugin."""
        if plugin_id not in self._plugins:
            return False
        
        plugin = self._plugins[plugin_id]
        
        if plugin.status != PluginStatus.ACTIVE:
            return True
        
        try:
            if plugin.instance:
                await plugin.instance.cleanup()
            
            # Remove registered tools
            self._tools = {
                k: v for k, v in self._tools.items()
                if v.get("plugin") != plugin_id
            }
            
            plugin.instance = None
            plugin.status = PluginStatus.DISABLED
            
            logger.info(f"Unloaded plugin: {plugin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error unloading plugin '{plugin_id}': {e}")
            return False
    
    async def load_enabled_plugins(self) -> None:
        """Load all plugins that should be enabled."""
        # Load settings to see which plugins are enabled
        settings_path = self.USER_PLUGINS_DIR / "settings.json"
        enabled_plugins = set()
        
        if settings_path.exists():
            try:
                with open(settings_path) as f:
                    settings = json.load(f)
                    enabled_plugins = set(settings.get("enabled", []))
            except Exception as e:
                logger.warning(f"Could not load plugin settings: {e}")
        
        # Load enabled plugins, or all if no settings
        for plugin_id, plugin in self._plugins.items():
            if not enabled_plugins or plugin_id in enabled_plugins:
                await self.load_plugin(plugin_id)
    
    def get_plugins(self) -> List[Plugin]:
        """Get all discovered plugins."""
        return list(self._plugins.values())
    
    def get_active_plugins(self) -> List[Plugin]:
        """Get all active plugins."""
        return [p for p in self._plugins.values() if p.status == PluginStatus.ACTIVE]
    
    def get_all_tools(self) -> Dict[str, Any]:
        """Get all tools from all active plugins."""
        return self._tools.copy()
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a plugin tool by name."""
        if tool_name not in self._tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        tool_info = self._tools[tool_name]
        plugin_id = tool_info["plugin"]
        plugin = self._plugins.get(plugin_id)
        
        if not plugin or plugin.status != PluginStatus.ACTIVE:
            raise RuntimeError(f"Plugin '{plugin_id}' is not active")
        
        # Extract the original tool name (without plugin prefix)
        original_name = tool_name.split(".", 1)[1] if "." in tool_name else tool_name
        
        return await plugin.instance.execute_tool(original_name, **kwargs)
    
    async def create_plugin(
        self,
        name: str,
        description: str,
        plugin_type: PluginType = PluginType.TOOL
    ) -> Path:
        """Create a new plugin scaffold."""
        plugin_dir = self.USER_PLUGINS_DIR / name
        plugin_dir.mkdir(parents=True, exist_ok=True)
        
        # Create manifest
        manifest = {
            "name": name,
            "version": "1.0.0",
            "description": description,
            "author": "User",
            "type": plugin_type.value,
            "entry_point": "main",
            "provides_tools": [],
            "settings_schema": {},
            "default_settings": {}
        }
        
        with open(plugin_dir / "manifest.yaml", "w") as f:
            yaml.dump(manifest, f, default_flow_style=False)
        
        # Create main.py scaffold
        main_content = f'''"""
{name} Plugin
{'=' * len(name + ' Plugin')}

{description}
"""

from src.core.plugin_system import ToolPlugin


class {name.title().replace('_', '')}Plugin(ToolPlugin):
    """Main plugin class."""
    
    async def initialize(self) -> None:
        """Initialize the plugin and register tools."""
        # Register your tools here
        self.register_tool(
            name="example_tool",
            func=self.example_tool,
            description="An example tool",
            parameters={{
                "input": {{"type": "string", "required": True}}
            }}
        )
    
    async def example_tool(self, input: str) -> dict:
        """Example tool implementation."""
        return {{
            "success": True,
            "result": f"Processed: {{input}}"
        }}
'''
        
        with open(plugin_dir / "main.py", "w") as f:
            f.write(main_content)
        
        logger.info(f"Created plugin scaffold at {plugin_dir}")
        return plugin_dir


# Singleton instance
_plugin_manager: Optional[PluginManager] = None

def get_plugin_manager() -> PluginManager:
    """Get the singleton plugin manager."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


async def init_plugins() -> PluginManager:
    """Initialize the plugin system."""
    manager = get_plugin_manager()
    await manager.initialize()
    return manager
