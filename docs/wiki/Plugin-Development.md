# Plugin Development

Create custom plugins to extend Otto Chat with new tools and integrations.

## Quick Start

### 1. Create Plugin Directory

```bash
mkdir -p plugins/my_plugin
```

### 2. Create Manifest

Create `plugins/my_plugin/manifest.yaml`:

```yaml
name: "My Plugin"
version: "1.0.0"
description: "A custom plugin for Otto Chat"
author: "Your Name"
type: "tool"  # or "integration"
entry_point: "main.py"
class_name: "MyPlugin"

provides:
  - name: my_tool
    description: "Does something useful"
    parameters:
      - name: input_text
        type: string
        required: true
        description: "The text to process"

settings:
  - name: api_key
    type: string
    required: false
    description: "Optional API key"
    secret: true
```

### 3. Create Plugin Class

Create `plugins/my_plugin/main.py`:

```python
from src.core.plugin_system import ToolPlugin

class MyPlugin(ToolPlugin):
    """Custom tool plugin."""
    
    def __init__(self, manifest: dict, settings: dict = None):
        super().__init__(manifest, settings)
        self.api_key = settings.get('api_key') if settings else None
    
    async def initialize(self) -> bool:
        """Initialize plugin resources."""
        # Setup connections, load data, etc.
        return True
    
    async def cleanup(self):
        """Cleanup when plugin is disabled."""
        pass
    
    async def my_tool(self, input_text: str) -> dict:
        """Process the input text."""
        result = input_text.upper()  # Example transformation
        
        return {
            "success": True,
            "result": result
        }
```

### 4. Enable Plugin

1. Open Settings in Otto Chat
2. Go to Plugins section
3. Click "Discover" to find new plugins
4. Enable your plugin

---

## Plugin Types

### Tool Plugin

Adds new AI tools that can be called via natural language.

```python
from src.core.plugin_system import ToolPlugin

class MyToolPlugin(ToolPlugin):
    async def my_tool(self, param: str) -> dict:
        return {"result": "done"}
```

### Integration Plugin

Connects to external services and APIs.

```python
from src.core.plugin_system import IntegrationPlugin

class MyIntegration(IntegrationPlugin):
    async def connect(self):
        """Connect to external service."""
        self.client = await create_connection()
    
    async def disconnect(self):
        """Disconnect from service."""
        await self.client.close()
```

---

## Manifest Reference

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Display name |
| `version` | string | Semantic version |
| `description` | string | Plugin description |
| `type` | string | "tool" or "integration" |
| `entry_point` | string | Python file name |
| `class_name` | string | Main class name |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `author` | string | Plugin author |
| `homepage` | string | Documentation URL |
| `license` | string | License type |
| `provides` | array | Tools provided |
| `settings` | array | Configuration options |
| `dependencies` | array | Required packages |

### Tool Definition

```yaml
provides:
  - name: tool_name
    description: "What the tool does"
    parameters:
      - name: param_name
        type: string|number|boolean|array|object
        required: true|false
        description: "Parameter description"
        default: "optional default"
```

### Settings Schema

```yaml
settings:
  - name: setting_name
    type: string|number|boolean
    required: true|false
    description: "Setting description"
    default: "default value"
    secret: true|false  # Hide in UI
    options:  # For enum types
      - value1
      - value2
```

---

## API Reference

### PluginBase Methods

```python
class PluginBase:
    async def initialize(self) -> bool:
        """Called when plugin is enabled."""
        pass
    
    async def cleanup(self):
        """Called when plugin is disabled."""
        pass
    
    def get_info(self) -> dict:
        """Return plugin metadata."""
        return self.manifest
    
    def get_settings_schema(self) -> list:
        """Return settings configuration."""
        return self.manifest.get('settings', [])
```

### ToolPlugin Methods

```python
class ToolPlugin(PluginBase):
    def get_tools(self) -> list:
        """Return list of tool definitions."""
        return self.manifest.get('provides', [])
    
    async def execute_tool(self, name: str, **kwargs) -> dict:
        """Execute a tool by name."""
        method = getattr(self, name)
        return await method(**kwargs)
```

### IntegrationPlugin Methods

```python
class IntegrationPlugin(PluginBase):
    async def connect(self):
        """Establish connection to service."""
        pass
    
    async def disconnect(self):
        """Close connection."""
        pass
    
    async def health_check(self) -> bool:
        """Check if connection is healthy."""
        return True
```

---

## Example Plugins

### Web Scraper

Scrapes web pages and extracts content:

```yaml
# manifest.yaml
name: "Web Scraper"
version: "1.0.0"
type: "tool"
provides:
  - name: scrape_page
    description: "Extract content from a webpage"
  - name: extract_links
    description: "Get all links from a page"
```

### Notification Sender

Sends notifications via multiple channels:

```yaml
# manifest.yaml
name: "Notification Sender"
version: "1.0.0"
type: "integration"
settings:
  - name: slack_webhook
    type: string
    secret: true
  - name: discord_webhook
    type: string
    secret: true
```

### Database Connector

Queries SQL databases:

```yaml
# manifest.yaml
name: "Database Connector"
version: "1.0.0"
type: "integration"
settings:
  - name: connection_string
    type: string
    required: true
    secret: true
```

---

## Plugin API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/plugins` | GET | List all plugins |
| `/api/plugins/{id}` | GET | Get plugin details |
| `/api/plugins/{id}/enable` | POST | Enable plugin |
| `/api/plugins/{id}/disable` | POST | Disable plugin |
| `/api/plugins/{id}/settings` | POST | Update settings |
| `/api/plugins/discover` | POST | Scan for new plugins |
| `/api/plugins/reload` | POST | Reload all plugins |

---

## Best Practices

1. **Handle Errors Gracefully** - Return informative error messages
2. **Validate Input** - Check parameters before processing
3. **Async by Default** - Use async/await for I/O operations
4. **Document Everything** - Clear descriptions in manifest
5. **Version Semantically** - Follow semver for updates
6. **Secure Secrets** - Mark sensitive settings as `secret: true`
7. **Clean Up Resources** - Implement cleanup() properly
