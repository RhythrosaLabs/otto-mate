# Plugin Development

Complete guide to creating custom plugins for Otto Chat.

---

## Overview

The plugin system allows you to extend Otto Chat with:

- **New AI Tools** - Custom tools callable via natural language
- **External Integrations** - Connect to third-party services
- **Custom Workflows** - Specialized automation logic

### Plugin Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      PLUGIN MANAGER                          │
│  • Discovers plugins in /plugins directory                   │
│  • Loads and validates manifests                             │
│  • Manages plugin lifecycle                                  │
│  • Injects plugin tools into AI system                       │
└─────────────────────────────────────────────────────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           ▼                  ▼                  ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   ToolPlugin    │  │IntegrationPlugin│  │  Your Plugin    │
│                 │  │                 │  │                 │
│ • Provides new  │  │ • Connects to   │  │ • Custom tools  │
│   AI tools      │  │   external APIs │  │ • Custom logic  │
│ • Stateless     │  │ • Manages       │  │ • Custom data   │
│   execution     │  │   connections   │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

---

## Quick Start

### 1. Create Plugin Structure

```bash
mkdir -p plugins/my_awesome_plugin
cd plugins/my_awesome_plugin
```

### 2. Create Manifest (`manifest.yaml`)

```yaml
# Plugin metadata
name: "My Awesome Plugin"
version: "1.0.0"
description: "Does amazing things with AI"
author: "Your Name"
homepage: "https://github.com/you/my-plugin"
license: "MIT"

# Plugin type: "tool" or "integration"
type: "tool"

# Entry point configuration
entry_point: "main.py"
class_name: "MyAwesomePlugin"

# Tools this plugin provides
provides:
  - name: awesome_tool
    description: "Does something awesome with the input"
    parameters:
      - name: input_text
        type: string
        required: true
        description: "The text to process"
      - name: uppercase
        type: boolean
        required: false
        default: false
        description: "Convert to uppercase"

  - name: another_tool
    description: "Another useful tool"
    parameters:
      - name: data
        type: object
        required: true
        description: "JSON data to process"

# Settings the plugin requires
settings:
  - name: api_key
    type: string
    required: false
    description: "Optional API key for enhanced features"
    secret: true
    
  - name: mode
    type: string
    required: false
    default: "normal"
    description: "Processing mode"
    options:
      - normal
      - fast
      - quality

# Python dependencies (installed automatically)
dependencies:
  - requests>=2.28.0
  - beautifulsoup4>=4.11.0
```

### 3. Create Plugin Class (`main.py`)

```python
"""
My Awesome Plugin - Does amazing things with AI
"""

import asyncio
from typing import Any, Dict, Optional
from src.core.plugin_system import ToolPlugin


class MyAwesomePlugin(ToolPlugin):
    """
    A plugin that provides awesome text processing tools.
    """
    
    def __init__(self, manifest: dict, settings: Optional[dict] = None):
        """
        Initialize the plugin.
        
        Args:
            manifest: Parsed manifest.yaml data
            settings: User-configured settings
        """
        super().__init__(manifest, settings)
        
        # Access settings
        self.api_key = settings.get('api_key') if settings else None
        self.mode = settings.get('mode', 'normal') if settings else 'normal'
        
        # Initialize any resources
        self._cache = {}
    
    async def initialize(self) -> bool:
        """
        Called when plugin is enabled.
        Use this to set up connections, load data, etc.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Setup any required resources
            print(f"🔌 {self.manifest['name']} initializing...")
            
            # Example: Validate API key if provided
            if self.api_key:
                # await self._validate_api_key()
                pass
            
            print(f"✅ {self.manifest['name']} ready!")
            return True
            
        except Exception as e:
            print(f"❌ {self.manifest['name']} failed to initialize: {e}")
            return False
    
    async def cleanup(self):
        """
        Called when plugin is disabled.
        Clean up resources, close connections, etc.
        """
        self._cache.clear()
        print(f"👋 {self.manifest['name']} cleaned up")
    
    # ─────────────────────────────────────────────────────────
    # TOOL IMPLEMENTATIONS
    # Each method that matches a 'provides' entry becomes a tool
    # ─────────────────────────────────────────────────────────
    
    async def awesome_tool(
        self, 
        input_text: str, 
        uppercase: bool = False
    ) -> Dict[str, Any]:
        """
        Does something awesome with the input.
        
        Args:
            input_text: The text to process
            uppercase: Whether to convert to uppercase
            
        Returns:
            Dict with success status and result
        """
        try:
            # Process the input
            result = input_text.strip()
            
            if uppercase:
                result = result.upper()
            
            # Apply mode-specific processing
            if self.mode == 'fast':
                pass  # Skip extra processing
            elif self.mode == 'quality':
                # Add extra processing
                result = f"✨ {result} ✨"
            
            # Cache the result
            self._cache[input_text] = result
            
            return {
                "success": True,
                "result": result,
                "mode": self.mode,
                "cached": False
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def another_tool(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process JSON data.
        
        Args:
            data: Dictionary of data to process
            
        Returns:
            Processed data
        """
        try:
            # Process the data
            processed = {
                key: str(value).upper() 
                for key, value in data.items()
            }
            
            return {
                "success": True,
                "result": processed,
                "item_count": len(processed)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
```

### 4. Enable Your Plugin

1. Restart Otto Chat (or click "Discover" in Settings → Plugins)
2. Go to Settings → Plugins
3. Find your plugin and toggle it ON

### 5. Use Your Plugin

```
"Use awesome_tool to process 'Hello World' with uppercase"
```

Otto will call your plugin and return the result.

---

## Plugin Types

### Tool Plugin

Adds new tools that the AI can use.

```python
from src.core.plugin_system import ToolPlugin

class MyToolPlugin(ToolPlugin):
    """Provides new AI-callable tools."""
    
    async def my_tool(self, param: str) -> dict:
        """
        A tool that does something useful.
        
        This method will be available as a tool called "my_tool".
        """
        return {"result": f"Processed: {param}"}
```

**Use Cases:**
- Custom data processors
- External API wrappers
- Specialized generators
- Analysis tools

### Integration Plugin

Connects to external services with persistent connections.

```python
from src.core.plugin_system import IntegrationPlugin

class MyIntegration(IntegrationPlugin):
    """Connects to an external service."""
    
    def __init__(self, manifest, settings):
        super().__init__(manifest, settings)
        self.client = None
    
    async def connect(self):
        """Establish connection to service."""
        self.client = await create_connection(
            api_key=self.settings.get('api_key')
        )
    
    async def disconnect(self):
        """Close connection."""
        if self.client:
            await self.client.close()
    
    async def health_check(self) -> bool:
        """Check if connection is healthy."""
        try:
            await self.client.ping()
            return True
        except:
            return False
    
    async def send_message(self, message: str) -> dict:
        """Send a message via the integration."""
        response = await self.client.send(message)
        return {"success": True, "response": response}
```

**Use Cases:**
- Database connections
- Messaging services (Slack, Discord)
- Cloud services (AWS, GCP)
- Custom APIs

---

## Manifest Reference

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Human-readable plugin name |
| `version` | string | Semantic version (e.g., "1.0.0") |
| `description` | string | Brief description of plugin |
| `type` | string | "tool" or "integration" |
| `entry_point` | string | Python file name (e.g., "main.py") |
| `class_name` | string | Main class name |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `author` | string | Plugin author name |
| `homepage` | string | Documentation URL |
| `license` | string | License type (MIT, Apache, etc.) |
| `provides` | array | List of tools provided |
| `settings` | array | Configuration options |
| `dependencies` | array | Python packages required |
| `min_otto_version` | string | Minimum Otto version |

### Tool Definition

```yaml
provides:
  - name: tool_name
    description: "What the tool does"
    parameters:
      - name: param_name
        type: string | number | boolean | array | object
        required: true | false
        default: "optional default value"
        description: "What this parameter does"
```

### Settings Schema

```yaml
settings:
  - name: setting_name
    type: string | number | boolean
    required: true | false
    default: "default value"
    description: "What this setting controls"
    secret: true | false  # Hide value in UI
    options:  # For enum/dropdown
      - option1
      - option2
      - option3
```

---

## Plugin Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                     DISCOVERY                                │
│  Plugin Manager scans /plugins directory                     │
│  Parses manifests, validates structure                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      LOADING                                 │
│  Imports Python module                                       │
│  Instantiates plugin class with manifest + settings          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   INITIALIZATION                             │
│  Calls plugin.initialize()                                   │
│  Plugin sets up connections, resources                       │
│  Returns True/False for success                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      ACTIVE                                  │
│  Plugin tools are available to AI                            │
│  Tools can be called via natural language                    │
│  Settings can be updated via UI/API                          │
└─────────────────────────────────────────────────────────────┘
                              │
                    (user disables plugin)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     CLEANUP                                  │
│  Calls plugin.cleanup()                                      │
│  Plugin closes connections, frees resources                  │
│  Plugin is unloaded from memory                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Example Plugins

### 1. Web Scraper Plugin

**manifest.yaml:**
```yaml
name: "Web Scraper"
version: "1.0.0"
description: "Scrape web pages and extract content"
type: "tool"
entry_point: "main.py"
class_name: "WebScraperPlugin"

provides:
  - name: scrape_page
    description: "Scrape a webpage and extract text content"
    parameters:
      - name: url
        type: string
        required: true
        description: "URL to scrape"
      - name: selector
        type: string
        required: false
        description: "CSS selector to target"

  - name: extract_links
    description: "Extract all links from a page"
    parameters:
      - name: url
        type: string
        required: true

  - name: extract_tables
    description: "Extract tables as JSON"
    parameters:
      - name: url
        type: string
        required: true

dependencies:
  - aiohttp>=3.8.0
  - beautifulsoup4>=4.11.0
  - lxml>=4.9.0
```

**main.py:**
```python
import aiohttp
from bs4 import BeautifulSoup
from src.core.plugin_system import ToolPlugin


class WebScraperPlugin(ToolPlugin):
    
    async def initialize(self) -> bool:
        self.session = aiohttp.ClientSession()
        return True
    
    async def cleanup(self):
        await self.session.close()
    
    async def scrape_page(self, url: str, selector: str = None) -> dict:
        try:
            async with self.session.get(url) as response:
                html = await response.text()
            
            soup = BeautifulSoup(html, 'lxml')
            
            if selector:
                elements = soup.select(selector)
                content = '\n'.join(el.get_text(strip=True) for el in elements)
            else:
                # Remove scripts and styles
                for tag in soup(['script', 'style', 'nav', 'footer']):
                    tag.decompose()
                content = soup.get_text(separator='\n', strip=True)
            
            return {
                "success": True,
                "url": url,
                "content": content[:10000],  # Limit size
                "title": soup.title.string if soup.title else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def extract_links(self, url: str) -> dict:
        try:
            async with self.session.get(url) as response:
                html = await response.text()
            
            soup = BeautifulSoup(html, 'lxml')
            links = []
            
            for a in soup.find_all('a', href=True):
                href = a['href']
                text = a.get_text(strip=True)
                if href.startswith('http'):
                    links.append({"url": href, "text": text})
            
            return {
                "success": True,
                "url": url,
                "links": links[:100],  # Limit
                "count": len(links)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def extract_tables(self, url: str) -> dict:
        try:
            async with self.session.get(url) as response:
                html = await response.text()
            
            soup = BeautifulSoup(html, 'lxml')
            tables = []
            
            for table in soup.find_all('table'):
                rows = []
                for tr in table.find_all('tr'):
                    cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                    if cells:
                        rows.append(cells)
                if rows:
                    tables.append(rows)
            
            return {
                "success": True,
                "url": url,
                "tables": tables,
                "count": len(tables)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
```

### 2. Notification Sender Plugin

**manifest.yaml:**
```yaml
name: "Notification Sender"
version: "1.0.0"
description: "Send notifications via Slack, Discord, or email"
type: "integration"
entry_point: "main.py"
class_name: "NotificationSenderPlugin"

provides:
  - name: send_slack
    description: "Send a Slack message"
    parameters:
      - name: message
        type: string
        required: true
      - name: channel
        type: string
        required: false
        default: "#general"
      
  - name: send_discord
    description: "Send a Discord message"
    parameters:
      - name: message
        type: string
        required: true

  - name: send_webhook
    description: "Send to any webhook URL"
    parameters:
      - name: url
        type: string
        required: true
      - name: payload
        type: object
        required: true

settings:
  - name: slack_webhook
    type: string
    required: false
    description: "Slack incoming webhook URL"
    secret: true
    
  - name: discord_webhook
    type: string
    required: false
    description: "Discord webhook URL"
    secret: true

dependencies:
  - aiohttp>=3.8.0
```

### 3. Database Connector Plugin

**manifest.yaml:**
```yaml
name: "Database Connector"
version: "1.0.0"
description: "Query SQL databases"
type: "integration"
entry_point: "main.py"
class_name: "DatabaseConnectorPlugin"

provides:
  - name: query_database
    description: "Execute a SQL query"
    parameters:
      - name: query
        type: string
        required: true
      - name: params
        type: array
        required: false

  - name: list_tables
    description: "List all tables in the database"
    parameters: []

  - name: describe_table
    description: "Get table schema"
    parameters:
      - name: table_name
        type: string
        required: true

settings:
  - name: connection_string
    type: string
    required: true
    description: "Database connection string"
    secret: true
    
  - name: database_type
    type: string
    required: true
    options:
      - sqlite
      - postgresql
      - mysql

dependencies:
  - aiosqlite>=0.17.0
  - asyncpg>=0.27.0
  - aiomysql>=0.1.1
```

---

## API Endpoints

### List All Plugins

```http
GET /api/plugins
```

**Response:**
```json
{
  "plugins": [
    {
      "id": "web_scraper",
      "name": "Web Scraper",
      "version": "1.0.0",
      "description": "Scrape web pages and extract content",
      "type": "tool",
      "enabled": true,
      "tools": ["scrape_page", "extract_links", "extract_tables"]
    }
  ]
}
```

### Get Plugin Details

```http
GET /api/plugins/{plugin_id}
```

### Enable Plugin

```http
POST /api/plugins/{plugin_id}/enable
```

### Disable Plugin

```http
POST /api/plugins/{plugin_id}/disable
```

### Update Plugin Settings

```http
POST /api/plugins/{plugin_id}/settings
Content-Type: application/json

{
  "api_key": "...",
  "mode": "quality"
}
```

### Discover New Plugins

```http
POST /api/plugins/discover
```

### Reload All Plugins

```http
POST /api/plugins/reload
```

### Get All Plugin Tools

```http
GET /api/plugins/tools/all
```

---

## Best Practices

### 1. Error Handling

Always return structured responses:

```python
async def my_tool(self, param: str) -> dict:
    try:
        result = await do_something(param)
        return {
            "success": True,
            "result": result
        }
    except ValueError as e:
        return {
            "success": False,
            "error": f"Invalid input: {e}",
            "error_code": "INVALID_INPUT"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_code": "UNKNOWN_ERROR"
        }
```

### 2. Async by Default

Use async/await for all I/O operations:

```python
# Good ✅
async def fetch_data(self, url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# Bad ❌
def fetch_data(self, url: str) -> dict:
    response = requests.get(url)  # Blocks!
    return response.json()
```

### 3. Resource Management

Clean up resources properly:

```python
class MyPlugin(IntegrationPlugin):
    async def initialize(self) -> bool:
        self.session = aiohttp.ClientSession()
        self.db = await create_pool()
        return True
    
    async def cleanup(self):
        await self.session.close()
        await self.db.close()
```

### 4. Validate Input

Check parameters before processing:

```python
async def process_url(self, url: str) -> dict:
    # Validate URL
    if not url.startswith(('http://', 'https://')):
        return {
            "success": False,
            "error": "URL must start with http:// or https://"
        }
    
    # Continue processing...
```

### 5. Document Everything

Add clear docstrings:

```python
async def analyze_text(self, text: str, language: str = "en") -> dict:
    """
    Analyze text for sentiment and key phrases.
    
    Args:
        text: The text to analyze (max 10,000 characters)
        language: ISO language code (default: "en")
    
    Returns:
        dict with keys:
            - success: bool
            - sentiment: float (-1 to 1)
            - phrases: list of key phrases
            - language: detected language
    
    Example:
        >>> await plugin.analyze_text("I love this product!", "en")
        {"success": True, "sentiment": 0.9, "phrases": ["love", "product"], ...}
    """
```

### 6. Rate Limiting

Respect API limits:

```python
import asyncio
from collections import deque
from time import time

class RateLimiter:
    def __init__(self, calls_per_second: float = 1.0):
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0
    
    async def wait(self):
        now = time()
        elapsed = now - self.last_call
        if elapsed < self.min_interval:
            await asyncio.sleep(self.min_interval - elapsed)
        self.last_call = time()

class MyPlugin(ToolPlugin):
    def __init__(self, manifest, settings):
        super().__init__(manifest, settings)
        self.rate_limiter = RateLimiter(calls_per_second=2)
    
    async def my_tool(self, param: str) -> dict:
        await self.rate_limiter.wait()
        # Now make the API call
```

### 7. Secrets Management

Never log or expose secrets:

```python
async def initialize(self) -> bool:
    api_key = self.settings.get('api_key')
    
    # Bad ❌
    print(f"Using API key: {api_key}")
    
    # Good ✅
    print(f"API key configured: {bool(api_key)}")
```

---

## Testing Plugins

### Unit Tests

```python
import pytest
from plugins.my_plugin.main import MyPlugin

@pytest.fixture
def plugin():
    manifest = {
        'name': 'Test Plugin',
        'version': '1.0.0',
        'type': 'tool'
    }
    return MyPlugin(manifest, settings={})

@pytest.mark.asyncio
async def test_my_tool(plugin):
    await plugin.initialize()
    
    result = await plugin.my_tool("test input")
    
    assert result['success'] is True
    assert 'result' in result
    
    await plugin.cleanup()
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_plugin_with_api():
    plugin = MyPlugin(manifest, settings={'api_key': 'test_key'})
    await plugin.initialize()
    
    # Test with real API
    result = await plugin.fetch_data('https://api.example.com/data')
    
    assert result['success'] is True
    
    await plugin.cleanup()
```

---

## Publishing Plugins

### Directory Structure

```
my-plugin/
├── manifest.yaml
├── main.py
├── README.md           # Plugin documentation
├── LICENSE
├── requirements.txt    # For standalone installation
├── tests/
│   └── test_plugin.py
└── examples/
    └── usage.py
```

### Share Your Plugin

1. Create a GitHub repository
2. Document installation and usage
3. Share the repo URL

Users can then:
```bash
cd otto-chat/plugins
git clone https://github.com/you/my-plugin
# Restart Otto or click "Discover"
```
