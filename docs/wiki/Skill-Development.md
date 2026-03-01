# Skill Development

Skills are modular capability packages that extend Otto's functionality.

---

## Overview

A skill is a self-contained directory containing:
- Python code implementing one or more capabilities
- A manifest file describing the skill
- Optional assets (templates, data, configs)

```
skills/
├── my_skill/
│   ├── manifest.json
│   ├── __init__.py
│   ├── main.py
│   └── assets/
│       └── template.txt
```

---

## Quick Start

### 1. Create the Skill Directory

```bash
mkdir -p skills/hello_world
```

### 2. Create manifest.json

```json
{
  "name": "hello_world",
  "version": "1.0.0",
  "description": "A simple greeting skill",
  "author": "Your Name",
  "capabilities": ["greeting"],
  "tools": [
    {
      "name": "say_hello",
      "description": "Greet someone by name",
      "parameters": {
        "name": {
          "type": "string",
          "description": "Name to greet",
          "required": true
        },
        "language": {
          "type": "string",
          "description": "Language for greeting",
          "default": "english"
        }
      }
    }
  ]
}
```

### 3. Create main.py

```python
"""Hello World skill for Otto."""

GREETINGS = {
    "english": "Hello",
    "spanish": "Hola",
    "french": "Bonjour",
    "japanese": "こんにちは"
}

async def say_hello(name: str, language: str = "english") -> dict:
    """Greet someone in their preferred language."""
    greeting = GREETINGS.get(language, GREETINGS["english"])
    return {
        "message": f"{greeting}, {name}!",
        "language": language
    }
```

### 4. Load the Skill

Skills in the `skills/` directory are discovered and loaded automatically at startup.

---

## Skill Manifest Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Unique skill identifier |
| `version` | string | ✅ | Semantic version |
| `description` | string | ✅ | What the skill does |
| `author` | string | No | Creator name |
| `capabilities` | string[] | No | List of capability tags |
| `dependencies` | string[] | No | Python packages needed |
| `tools` | object[] | ✅ | Tools provided by this skill |
| `slash_commands` | object[] | No | Slash commands to register |
| `config` | object | No | Default configuration values |
| `min_version` | string | No | Minimum Otto version required |

---

## Tool Definition

Each tool in the manifest `tools` array:

```json
{
  "name": "tool_name",
  "description": "What this tool does (shown to the AI)",
  "parameters": {
    "param1": {
      "type": "string",
      "description": "Parameter description",
      "required": true
    },
    "param2": {
      "type": "integer",
      "description": "Optional parameter",
      "default": 10
    }
  }
}
```

The corresponding Python function **must** match the tool name:

```python
async def tool_name(param1: str, param2: int = 10) -> dict:
    """Implementation of the tool."""
    return {"result": "..."}
```

---

## Built-in Skills

Otto ships with 14+ skills:

| Skill | Description |
|-------|-------------|
| `printify` | E-commerce product management |
| `web_search` | Web search and research |
| `browser` | Browser automation |
| `image_gen` | Image generation |
| `video_gen` | Video generation |
| `audio_gen` | Audio and music generation |
| `code_gen` | Code generation and execution |
| `data_analysis` | Data processing and visualization |
| `social_media` | Social media management |
| `email` | Email operations |
| `file_ops` | File operations |
| `project_mgmt` | Project management |
| `content` | Content creation |
| `analytics` | Analytics and reporting |

---

## Advanced Patterns

### Skill with State

```python
class MySkill:
    def __init__(self):
        self.state = {}
    
    async def process(self, input_data: str) -> dict:
        # Access and modify state
        self.state["last_input"] = input_data
        return {"processed": True}
```

### Skill with External API

```python
import httpx

async def fetch_data(query: str) -> dict:
    """Fetch data from external API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.example.com/data",
            params={"q": query}
        )
        return response.json()
```

### Skill with File Output

```python
from pathlib import Path

async def generate_report(topic: str) -> dict:
    """Generate and save a report."""
    content = f"Report on {topic}\n..."
    
    output_path = Path("data/slash_outputs") / f"report_{topic}.md"
    output_path.write_text(content)
    
    return {
        "message": f"Report saved to {output_path}",
        "file_path": str(output_path)
    }
```

---

## Best Practices

1. **Keep skills focused** — One domain per skill
2. **Use async** — All tool functions should be `async`
3. **Return dicts** — Always return structured data
4. **Handle errors** — Catch exceptions and return useful error messages
5. **Document tools** — Clear descriptions help the AI use tools correctly
6. **Version your skills** — Use semantic versioning
7. **Minimize dependencies** — Only require what you need
