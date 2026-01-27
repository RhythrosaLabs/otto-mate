# 🚀 Getting Started with Otto Universal

This guide will help you get Otto Universal up and running in minutes.

## Prerequisites

- **Python 3.11+** installed
- **API Keys** for:
  - Anthropic Claude (required)
  - OpenAI (required)
  - Other services (optional)

## Installation

### 1. Clone or Create the Repository

```bash
cd /path/to/your/workspace
# Repository already created at /Users/sheils/repos/otto-universal
```

### 2. Set Up Python Environment

```bash
cd /Users/sheils/repos/otto-universal

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# Or on Windows:
# venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy example env file
cp config/.env.example .env

# Edit .env with your API keys
nano .env  # or use your preferred editor
```

**Minimum required keys:**
```env
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here
```

### 5. Create Data Directories

```bash
mkdir -p data/chroma data/uploads data/screenshots logs
```

## Running Otto

### Option 1: Development Server

```bash
# Run with auto-reload
python -m src.api.main

# Or use uvicorn directly
uvicorn src.api.main:app --reload --port 8000
```

### Option 2: Production Server

```bash
# Run with multiple workers
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Option 3: Docker (Recommended for Production)

```bash
# Build image
docker build -t otto-universal .

# Run container
docker run -p 8000:8000 --env-file .env otto-universal
```

## Testing the API

### Health Check

```bash
curl http://localhost:8000/health
```

### Simple Chat

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello Otto! What can you do?",
    "session_id": "test-session"
  }'
```

### Generate an Image

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Generate a t-shirt design with mountains",
    "session_id": "test-session"
  }'
```

### Execute Workflow

```bash
curl -X POST http://localhost:8000/workflow \
  -H "Content-Type: application/json" \
  -d '{
    "workflow": [
      {
        "tool": "generate_image",
        "params": {
          "prompt": "mountain landscape"
        }
      },
      {
        "tool": "generate_text",
        "params": {
          "prompt": "description for mountain image",
          "type": "caption"
        }
      }
    ]
  }'
```

## WebSocket Connection

### Using JavaScript

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('Connected to Otto');
  
  // Send message
  ws.send(JSON.stringify({
    type: 'chat',
    message: 'Hello Otto!',
    session_id: 'my-session'
  }));
};

ws.onmessage = (event) => {
  const response = JSON.parse(event.data);
  console.log('Otto says:', response);
};
```

### Using Python

```python
import asyncio
import websockets
import json

async def chat_with_otto():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        # Send message
        await websocket.send(json.dumps({
            "type": "chat",
            "message": "Hello Otto!",
            "session_id": "my-session"
        }))
        
        # Receive response
        response = await websocket.recv()
        print(json.loads(response))

asyncio.run(chat_with_otto())
```

## Adding Custom Tools

### 1. Create Tool File

Create `src/tools/my_tools/__init__.py`:

```python
from ..core.tool_registry import tool

@tool(
    name="my_awesome_tool",
    description="Does something awesome",
    parameters={
        "input": {
            "type": "string",
            "description": "Input parameter",
            "required": True
        }
    },
    category="custom",
    tags=["awesome", "custom"]
)
async def my_awesome_tool(input: str):
    # Your implementation
    result = f"Processed: {input}"
    return {"result": result}
```

### 2. Tools Auto-Discovered

Otto automatically discovers tools decorated with `@tool` in the `src/tools/` directory.

### 3. Use Your Tool

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Use my awesome tool on test data"
  }'
```

## Integrating with Otto Platform

To leverage existing Otto Platform capabilities:

### Option 1: API Calls

```python
@tool(
    name="create_printify_product",
    description="Create product on Printify",
    parameters={...},
    category="business"
)
async def create_printify_product(design_url: str, product_type: str):
    # Call Otto Platform API
    response = await httpx.post(
        "http://otto-platform-api/products/create",
        json={"design": design_url, "type": product_type}
    )
    return response.json()
```

### Option 2: Direct Import

```python
# Add Otto Platform to Python path
import sys
sys.path.append("/Users/sheils/repos/printify")

from campaign_generator_service import generate_campaign

@tool(
    name="create_campaign",
    description="Create marketing campaign",
    parameters={...},
    category="business"
)
async def create_campaign(product_name: str):
    result = await generate_campaign(product_name)
    return result
```

## Next Steps

1. **Add More Tools** - Create tools for your specific use cases
2. **Voice Integration** - Set up Whisper and ElevenLabs for voice
3. **WhatsApp Integration** - Configure WhatsApp Business API
4. **Deploy to Production** - Use Docker and cloud hosting
5. **Monitor and Scale** - Set up logging, metrics, and scaling

## Common Issues

### Port Already in Use

```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9
```

### Import Errors

```bash
# Make sure you're in the venv
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### ChromaDB Issues

```bash
# Clear ChromaDB data
rm -rf data/chroma
mkdir -p data/chroma
```

## Documentation

- [Architecture](../ARCHITECTURE.md) - System design
- [API Reference](API.md) - API endpoints
- [Tools Guide](TOOLS.md) - Creating tools
- [Deployment](DEPLOYMENT.md) - Production deployment

## Support

- Issues: GitHub Issues
- Discussions: GitHub Discussions
- Email: support@otto-ai.com

---

**You're now ready to build the most powerful AI assistant ever! 🚀**
