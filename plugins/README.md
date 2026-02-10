# Otto Plugin Development Guide

Create custom plugins to extend Otto's capabilities with new tools, integrations, agents, and workflows.

## Quick Start

### 1. Create Plugin Directory

```bash
mkdir plugins/my_plugin
cd plugins/my_plugin
```

### 2. Create manifest.yaml

```yaml
name: my_plugin
version: 1.0.0
description: My awesome plugin
author: Your Name
type: tool  # tool, integration, agent, workflow

entry_point: main

provides_tools:
  - my_tool_name

settings_schema:
  api_key:
    type: string
    description: API key for the service
    required: false

default_settings:
  api_key: ""

tags:
  - utility
  - custom
```

### 3. Create main.py

```python
"""My Plugin - Does awesome things."""

from src.core.plugin_system import ToolPlugin

class MyPlugin(ToolPlugin):
    """Main plugin class."""
    
    async def initialize(self) -> None:
        """Register tools when plugin loads."""
        self.register_tool(
            name="my_tool",
            func=self.my_tool,
            description="Does something amazing",
            parameters={
                "input": {
                    "type": "string",
                    "required": True,
                    "description": "Input to process"
                },
                "option": {
                    "type": "string",
                    "required": False,
                    "description": "Optional setting"
                }
            }
        )
    
    async def my_tool(self, input: str, option: str = "default") -> dict:
        """Tool implementation."""
        # Access settings via self.settings
        api_key = self.settings.get("api_key", "")
        
        # Your logic here
        result = f"Processed: {input} with {option}"
        
        return {
            "success": True,
            "result": result
        }
```

## Plugin Types

### Tool Plugin
Add new tools/functions that Otto can use.

```python
from src.core.plugin_system import ToolPlugin

class MyToolPlugin(ToolPlugin):
    async def initialize(self) -> None:
        self.register_tool(
            name="analyze_data",
            func=self.analyze,
            description="Analyze data and return insights",
            parameters={
                "data": {"type": "string", "required": True}
            }
        )
    
    async def analyze(self, data: str) -> dict:
        return {"insights": [...]}
```

### Integration Plugin
Connect to external services.

```python
from src.core.plugin_system import IntegrationPlugin

class SlackPlugin(IntegrationPlugin):
    async def initialize(self) -> None:
        self.api_token = self.settings.get("token")
    
    async def connect(self) -> bool:
        # Connect to Slack API
        self._connected = True
        return True
    
    async def disconnect(self) -> None:
        self._connected = False
    
    def get_tools(self):
        return [{
            "name": "send_slack_message",
            "description": "Send a message to Slack",
            "parameters": {...}
        }]
```

### Workflow Plugin
Add reusable workflow templates.

```python
from src.core.plugin_system import PluginBase

class ContentWorkflowPlugin(PluginBase):
    async def initialize(self) -> None:
        pass
    
    def get_workflows(self):
        return [{
            "name": "Blog Post Pipeline",
            "description": "Research → Write → Edit → Publish",
            "steps": [
                {"action": "research", "params": {"topic": "$input"}},
                {"action": "write_content", "params": {"research": "$previous"}},
                {"action": "edit", "params": {"content": "$previous"}},
                {"action": "publish", "params": {"content": "$previous"}}
            ]
        }]
```

## Settings & Configuration

### Accessing Settings
```python
# In your plugin
api_key = self.settings.get("api_key", "default_value")
```

### Settings Schema (manifest.yaml)
```yaml
settings_schema:
  api_key:
    type: string
    description: API authentication key
    required: true
  
  max_retries:
    type: integer
    description: Maximum retry attempts
    default: 3
  
  enable_cache:
    type: boolean
    description: Enable response caching
    default: true
```

## Async Support

All plugin methods support async/await:

```python
async def my_tool(self, query: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.example.com?q={query}") as resp:
            data = await resp.json()
    return data
```

## Error Handling

```python
async def my_tool(self, input: str) -> dict:
    try:
        result = await self.process(input)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

## Plugin Lifecycle

1. **Discovery**: Plugin directory scanned for manifest.yaml
2. **Loading**: manifest.yaml parsed, plugin class instantiated
3. **Initialization**: `initialize()` called, tools registered
4. **Active**: Plugin tools available to Otto
5. **Cleanup**: `cleanup()` called on shutdown/disable

## Directory Structure

```
plugins/
├── my_plugin/
│   ├── manifest.yaml      # Required: Plugin metadata
│   ├── main.py            # Required: Plugin entry point
│   ├── utils.py           # Optional: Helper modules
│   ├── templates/         # Optional: Template files
│   └── README.md          # Optional: Documentation
```

## API Endpoints

```
GET  /api/plugins                 # List all plugins
GET  /api/plugins/{id}            # Get plugin details
POST /api/plugins/{id}/enable     # Enable plugin
POST /api/plugins/{id}/disable    # Disable plugin
POST /api/plugins/{id}/settings   # Update settings
POST /api/plugins/create          # Create new plugin
```

## Tips

1. **Keep it simple**: One plugin = one focused capability
2. **Document well**: Add descriptions to all tools and parameters
3. **Handle errors**: Return structured error responses
4. **Use settings**: Make configurable via settings_schema
5. **Test locally**: Test your plugin before sharing

## Need Help?

See example plugins in `src/plugins/` for working examples.
