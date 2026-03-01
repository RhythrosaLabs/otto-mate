# Plugin Development

This guide explains how to create custom plugins for Otto Chat.

---

## Overview

The plugin system supports 6 plugin types:
- **Tool** — Add new AI tools
- **Integration** — Connect external services
- **Agent** — Custom agent behaviors
- **Processor** — Data processing pipelines
- **UI** — Custom UI components
- **Workflow** — Workflow templates

Plugins are discovered from three locations (in priority order):
1. `./plugins/` — Project-level
2. `~/.otto/plugins/` — User-level
3. Python packages with `otto.plugins` entry points — System-level

---

## Quick Start

### 1. Create the Plugin Directory

```bash
mkdir -p plugins/my_plugin
```

### 2. Create `plugin.json`

```json
{
  "name": "my_plugin",
  "version": "1.0.0",
  "description": "A description of what my plugin does",
  "author": "Your Name",
  "type": "tool",
  "entry_point": "main.py",
  "enabled": true,
  "settings": {
    "api_key": {
      "type": "string",
      "required": true,
      "description": "API key for the service"
    },
    "max_results": {
      "type": "integer",
      "required": false,
      "default": 10,
      "description": "Maximum results to return"
    }
  },
  "dependencies": []
}
```

### 3. Create `main.py`

```python
"""My Custom Plugin for Otto Chat."""

class MyPlugin:
    """Plugin that adds a custom tool to Otto."""

    def __init__(self, settings: dict = None):
        self.settings = settings or {}
        self.api_key = self.settings.get("api_key", "")

    def get_tools(self) -> list:
        """Return the tools this plugin provides."""
        return [
            {
                "name": "my_custom_tool",
                "description": "Does something useful",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input_text": {
                            "type": "string",
                            "description": "The input text to process"
                        },
                        "option": {
                            "type": "string",
                            "enum": ["a", "b", "c"],
                            "description": "Processing option"
                        }
                    },
                    "required": ["input_text"]
                },
                "handler": self.my_custom_tool
            }
        ]

    async def my_custom_tool(self, input_text: str, option: str = "a") -> dict:
        """Execute the custom tool."""
        # Your logic here
        result = f"Processed: {input_text} with option {option}"
        return {
            "success": True,
            "result": result
        }

    def cleanup(self):
        """Called when the plugin is disabled or unloaded."""
        pass
```

### 4. (Optional) Create `requirements.txt`

```
requests>=2.28.0
some-library>=1.0.0
```

---

## Plugin Structure

```
plugins/my_plugin/
├── plugin.json        # Metadata, settings schema, dependencies
├── main.py            # Plugin entry point (class with get_tools())
├── requirements.txt   # Python dependencies (optional)
├── README.md          # Plugin documentation (optional)
└── tests/             # Plugin tests (optional)
    └── test_plugin.py
```

---

## plugin.json Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique plugin identifier |
| `version` | string | Yes | Semantic version (e.g., "1.0.0") |
| `description` | string | Yes | Human-readable description |
| `author` | string | No | Plugin author |
| `type` | string | Yes | Plugin type (tool, integration, agent, processor, ui, workflow) |
| `entry_point` | string | Yes | Python file to load (relative to plugin dir) |
| `enabled` | boolean | No | Whether plugin is enabled by default (true) |
| `settings` | object | No | Settings schema for configuration |
| `dependencies` | array | No | Other plugins this depends on |

### Settings Schema

Each setting supports:

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Data type: string, integer, float, boolean, array, object |
| `required` | boolean | Whether the setting is required |
| `default` | any | Default value |
| `description` | string | Human-readable description |
| `enum` | array | Allowed values (for string type) |
| `min` / `max` | number | Range constraints (for numeric types) |

---

## Plugin Types

### Tool Plugin

Adds new tools that Otto can use in conversations:

```python
class MyToolPlugin:
    def get_tools(self):
        return [{
            "name": "tool_name",
            "description": "What this tool does",
            "parameters": {...},
            "handler": self.handler_method
        }]

    async def handler_method(self, **kwargs):
        return {"success": True, "result": "..."}
```

### Integration Plugin

Connects to external services:

```python
class MyIntegration:
    def __init__(self, settings):
        self.client = ExternalAPI(settings["api_key"])

    def get_tools(self):
        return [
            {"name": "fetch_data", ..., "handler": self.fetch},
            {"name": "push_data", ..., "handler": self.push}
        ]

    async def fetch(self, query):
        return await self.client.search(query)

    async def push(self, data):
        return await self.client.create(data)
```

### Workflow Plugin

Defines reusable workflow templates:

```python
class MyWorkflow:
    def get_workflows(self):
        return [{
            "name": "my_workflow",
            "description": "Automated workflow",
            "steps": [
                {"action": "research_topic", "params": {"topic": "${input.topic}"}},
                {"action": "generate_blog_post", "params": {"content": "${step_1.output}"}},
                {"action": "generate_image", "params": {"prompt": "${input.topic}"}},
            ]
        }]
```

---

## Built-in Plugin Examples

### Web Scraper

```
plugins/web_scraper/
├── plugin.json
└── main.py
```

Tools provided:
- `scrape_page` — Extract content from a URL
- `extract_links` — Get all links from a page
- `extract_tables` — Extract HTML tables
- `search_content` — Search within page content

### Notification Sender

Tools provided:
- `send_email_notification` — Send via SMTP
- `send_slack_notification` — Post to Slack
- `send_discord_notification` — Post to Discord
- `send_webhook_notification` — Call webhook URL

### Database Connector

Tools provided:
- `query_database` — Run SQL queries
- `list_tables` — List database tables
- `describe_table` — Get table schema

---

## Plugin Management

### Via Web UI

Navigate to **Settings → Plugins** to:
- View installed plugins
- Enable/disable plugins
- Configure plugin settings
- Reload plugins

### Via REST API

```bash
# List plugins
curl http://localhost:8000/api/plugins

# Get plugin details
curl http://localhost:8000/api/plugins/web_scraper

# Enable a plugin
curl -X POST http://localhost:8000/api/plugins/web_scraper/enable

# Disable a plugin
curl -X POST http://localhost:8000/api/plugins/web_scraper/disable

# Update settings
curl -X PUT http://localhost:8000/api/plugins/web_scraper/settings \
  -H "Content-Type: application/json" \
  -d '{"timeout": 30}'

# Reload all plugins
curl -X POST http://localhost:8000/api/plugins/reload
```

---

## Best Practices

1. **Handle errors gracefully** — Always return `{"success": false, "error": "..."}` on failure
2. **Use async** — All tool handlers should be `async` for performance
3. **Validate settings** — Check required settings in `__init__`
4. **Clean up resources** — Implement `cleanup()` for proper resource management
5. **Version your plugin** — Follow semantic versioning
6. **Document your tools** — Clear descriptions and parameter docs help Otto use tools correctly
7. **Test independently** — Write tests for your plugin's logic
8. **Keep dependencies minimal** — List only what you actually need

---

## Distributing Plugins

### As a Directory
Share the entire plugin directory — users drop it into their `plugins/` folder.

### As a Python Package
Create a `setup.py` or `pyproject.toml` with entry points:

```python
# setup.py
setup(
    name="otto-plugin-example",
    entry_points={
        "otto.plugins": [
            "example = otto_plugin_example:ExamplePlugin"
        ]
    }
)
```

Users install with: `pip install otto-plugin-example`
