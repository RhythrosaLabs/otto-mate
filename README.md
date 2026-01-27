# 🤖 Otto Chat

> **Universal AI Assistant** — Control everything through conversation

Otto Chat is a powerful, extensible AI assistant that combines Claude's intelligence with real-world integrations. Create products, generate images, research topics, browse the web, manage files, and automate your business — all through natural conversation.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?logo=fastapi)
![Claude](https://img.shields.io/badge/Claude-Opus%204-purple?logo=anthropic)
![License](https://img.shields.io/badge/License-Private-red)

<p align="center">
  <img src="https://img.shields.io/badge/Tools-63+-orange" alt="63+ Tools">
  <img src="https://img.shields.io/badge/Integrations-6-blue" alt="6 Integrations">
  <img src="https://img.shields.io/badge/Status-Active-success" alt="Active">
</p>

---

## ✨ Features

### 🧠 AI-Powered Conversation
- **Claude Integration** — Powered by Anthropic's Claude for intelligent, context-aware responses
- **Multi-Step Planning** — Automatically breaks down complex tasks into executable steps
- **Tool Selection** — Intelligently chooses the right tools for each task
- **Context Memory** — Maintains conversation history across sessions

### 🎨 Image Generation
- **Multiple Models** — Flux Pro, Flux Dev, SDXL, Recraft V3 via Replicate
- **Style Control** — Specify artistic styles, aspect ratios, and quality settings
- **Logo Generation** — Professional logos and icons with Recraft
- **Automatic Storage** — Generated images saved to file storage with metadata

### 🛍️ E-Commerce Integration
- **Printify** — Create print-on-demand products, manage shops, publish listings
- **Shopify** — Manage products, orders, customers, and inventory
- **Product Creation** — Generate designs and push directly to your stores
- **Catalog Management** — Full CRUD operations on your product catalog

### 🔍 Research & Web
- **Web Search** — Google search via Serper API
- **Web Scraping** — Extract content from any webpage
- **News Search** — Stay updated with latest news
- **Browser Automation** — Full browser control for complex web tasks

### 📁 File Management
- **Local Storage** — Organize files by category (images, documents, audio, video)
- **Cloud Ready** — Architecture supports S3, Google Cloud Storage
- **Metadata Tracking** — Full file history with tags and descriptions
- **Web Interface** — Browse, upload, and manage files visually

### 🎙️ Voice Capabilities
- **Speech-to-Text** — OpenAI Whisper integration
- **Text-to-Speech** — Natural voice responses
- **Voice Commands** — Control Otto hands-free

### ⚙️ Easy Setup
- **Onboarding Wizard** — Step-by-step setup for first-time users
- **Settings Page** — Configure all integrations in one place
- **Connection Testing** — Verify API keys work before saving

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- [Anthropic API Key](https://console.anthropic.com/settings/keys) (required)

### Installation

```bash
# Clone the repository
git clone https://github.com/RhythrosaLabs/otto-chat.git
cd otto-chat

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### Configuration

Edit `.env` with your API keys:

```env
# Required - Core AI
ANTHROPIC_API_KEY=sk-ant-...

# Optional - Voice Features
OPENAI_API_KEY=sk-...

# Optional - Image Generation
REPLICATE_API_TOKEN=r8_...

# Optional - Print-on-Demand
PRINTIFY_API_TOKEN=...
PRINTIFY_SHOP_ID=...

# Optional - E-commerce
SHOPIFY_SHOP_NAME=your-store
SHOPIFY_ACCESS_TOKEN=shpat_...

# Optional - Web Search
SERPER_API_KEY=...
```

### Run

```bash
# Start the server
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Or with auto-reload for development
python -m uvicorn src.api.main:app --reload
```

Visit **http://localhost:8000** to start chatting!

> 💡 First-time users are automatically redirected to the onboarding wizard

---

## 🎯 Usage Examples

### Natural Language Commands

```
💬 "Create a mountain landscape design for a t-shirt"
   → Generates image with Flux, creates Printify product

💬 "Research the top 10 AI startups in 2024"
   → Searches web, compiles comprehensive report

💬 "Take a screenshot of tesla.com"
   → Opens browser, captures screenshot, saves to files

💬 "Generate a logo for a coffee shop called 'Bean There'"
   → Creates professional logo with Recraft V3

💬 "List all my Printify products"
   → Fetches and displays your product catalog

💬 "Create a product description for wireless earbuds"
   → Generates compelling e-commerce copy

💬 "What's the latest news about SpaceX?"
   → Searches news, summarizes key stories
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web chat interface |
| `/onboarding` | GET | Setup wizard for new users |
| `/settings-page` | GET | Settings management |
| `/files-page` | GET | File browser |
| `/chat` | POST | Send chat message |
| `/voice` | POST | Voice input (audio) |
| `/tools` | GET | List all available tools |
| `/health` | GET | Health check |
| `/api/settings` | GET/PUT | Settings API |
| `/api/files/*` | * | File management API |
| `/api/connections/*` | * | Service connections API |

### REST API Example

```bash
# Send a chat message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Generate a sunset beach image"}'

# Check available tools
curl http://localhost:8000/tools

# Get connection status
curl http://localhost:8000/api/connections/status

# Upload a file
curl -X POST http://localhost:8000/api/files/upload \
  -F "file=@image.png" \
  -F "category=images"
```

---

## 🛠️ Architecture

```
otto-chat/
├── src/
│   ├── api/
│   │   ├── main.py              # FastAPI application & routes
│   │   ├── settings.py          # Settings API endpoints
│   │   ├── files.py             # File management API
│   │   └── connections.py       # Service connections API
│   │
│   ├── core/
│   │   └── agent_orchestrator.py # AI orchestration & tool dispatch
│   │
│   ├── tools/
│   │   ├── __init__.py          # Tool registry
│   │   ├── printify.py          # Printify integration (13 tools)
│   │   ├── shopify.py           # Shopify integration (12 tools)
│   │   ├── image_generation.py  # AI image generation (8 tools)
│   │   ├── research.py          # Web search & scraping (8 tools)
│   │   ├── browser.py           # Browser automation (8 tools)
│   │   ├── content.py           # Content generation (7 tools)
│   │   └── file_storage.py      # File management (7 tools)
│   │
│   ├── storage/
│   │   └── file_storage.py      # File storage backend
│   │
│   ├── utils/
│   │   ├── config.py            # Pydantic settings
│   │   └── logger.py            # Logging configuration
│   │
│   └── web/
│       ├── index.html           # Main chat interface
│       ├── settings.html        # Settings page
│       ├── files.html           # File browser
│       └── onboarding.html      # Setup wizard
│
├── data/
│   ├── files/                   # File storage directory
│   │   ├── images/
│   │   ├── documents/
│   │   ├── audio/
│   │   └── video/
│   └── settings.json            # User settings
│
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env
```

---

## 🔧 Available Tools (63 Total)

### 🖨️ Printify Tools (13)
| Tool | Description |
|------|-------------|
| `get_printify_shops` | List all connected shops |
| `get_printify_products` | Get products from a shop |
| `get_printify_product` | Get single product details |
| `create_printify_product` | Create new product |
| `update_printify_product` | Update existing product |
| `delete_printify_product` | Delete a product |
| `upload_printify_image` | Upload design image |
| `publish_printify_product` | Publish to sales channel |
| `unpublish_printify_product` | Remove from sales channel |
| `get_print_providers` | List print providers |
| `get_blueprints` | Get product templates |
| `get_blueprint_variants` | Get variant options |
| `calculate_shipping` | Get shipping costs |

### 🛒 Shopify Tools (12)
| Tool | Description |
|------|-------------|
| `get_shopify_products` | List store products |
| `get_shopify_product` | Get product details |
| `create_shopify_product` | Create new product |
| `update_shopify_product` | Update existing product |
| `delete_shopify_product` | Delete a product |
| `get_shopify_orders` | View orders |
| `get_shopify_order` | Order details |
| `update_shopify_order` | Update order |
| `get_shopify_customers` | List customers |
| `get_shopify_customer` | Customer details |
| `get_shopify_inventory` | Inventory levels |
| `update_shopify_inventory` | Adjust inventory |

### 🎨 Image Generation Tools (8)
| Tool | Description |
|------|-------------|
| `generate_image_flux_pro` | Flux Pro (highest quality) |
| `generate_image_flux_dev` | Flux Dev (fast) |
| `generate_image_sdxl` | Stable Diffusion XL |
| `generate_image_recraft` | Recraft V3 (logos, icons) |
| `generate_logo` | Professional logo creation |
| `generate_icon` | App/web icons |
| `upscale_image` | AI image upscaling |
| `remove_background` | Background removal |

### 🔍 Research Tools (8)
| Tool | Description |
|------|-------------|
| `web_search` | Google search via Serper |
| `search_news` | News article search |
| `search_images` | Image search |
| `search_videos` | Video search |
| `scrape_webpage` | Extract page content |
| `scrape_structured` | Extract structured data |
| `get_page_links` | Extract all links |
| `summarize_url` | Summarize webpage |

### 🌐 Browser Tools (8)
| Tool | Description |
|------|-------------|
| `browser_navigate` | Open URL in browser |
| `browser_screenshot` | Capture page screenshot |
| `browser_click` | Click elements |
| `browser_type` | Enter text in fields |
| `browser_scroll` | Scroll page |
| `browser_extract` | Extract data from page |
| `browser_wait` | Wait for element |
| `browser_close` | Close browser |

### 📁 File Storage Tools (7)
| Tool | Description |
|------|-------------|
| `save_file` | Store file with metadata |
| `save_image_from_url` | Download and save image |
| `save_generated_image` | Save AI-generated image |
| `get_file` | Retrieve file by ID |
| `list_files` | Browse files by category |
| `delete_file` | Remove file |
| `get_storage_stats` | Storage statistics |

### ✍️ Content Tools (7)
| Tool | Description |
|------|-------------|
| `generate_blog_post` | AI blog writing |
| `generate_product_description` | E-commerce copy |
| `generate_social_post` | Social media content |
| `generate_email` | Email drafting |
| `summarize_text` | Text summarization |
| `rewrite_text` | Content rewriting |
| `generate_ideas` | Brainstorming |

---

## 🐳 Docker Deployment

### Quick Start with Docker

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f otto

# Stop
docker-compose down
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  otto:
    build: .
    container_name: otto-chat
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directories
RUN mkdir -p data/files/images data/files/documents data/files/audio data/files/video

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🔐 Security

- **Environment Variables** — API keys stored in `.env` (never committed)
- **CORS Configuration** — Configurable for production
- **Rate Limiting** — Built-in request throttling
- **Input Validation** — Pydantic models for all inputs
- **JWT Ready** — Authentication infrastructure in place

### Security Best Practices

```bash
# Never commit .env files
echo ".env" >> .gitignore

# Use secrets manager in production
# AWS Secrets Manager, HashiCorp Vault, etc.

# Restrict CORS in production
# Edit src/api/main.py allow_origins
```

---

## 📊 API Response Format

### Chat Response

```json
{
  "response": "I've generated your mountain landscape image...",
  "type": "success",
  "session_id": "abc123",
  "plan": {
    "steps": ["Generate image", "Save to storage", "Return result"],
    "current_step": 3,
    "completed": true
  },
  "results": [
    {
      "tool": "generate_image_flux_pro",
      "success": true,
      "data": {
        "url": "https://...",
        "file_id": "img_123"
      }
    }
  ]
}
```

### Error Response

```json
{
  "detail": "Error message here",
  "error_code": "TOOL_EXECUTION_FAILED",
  "tool": "generate_image_flux_pro"
}
```

---

## 🗺️ Roadmap

### Coming Soon
- [ ] Multi-user authentication
- [ ] Workflow automation builder
- [ ] Scheduled tasks / cron jobs
- [ ] Plugin system for custom tools
- [ ] Webhook integrations

### Future
- [ ] Mobile app companion
- [ ] Voice-first mode
- [ ] Team collaboration
- [ ] Analytics dashboard
- [ ] Custom AI model support

---

## 🐛 Troubleshooting

### Common Issues

**Server won't start**
```bash
# Check Python version
python --version  # Should be 3.11+

# Check dependencies
pip install -r requirements.txt

# Check .env file exists
cat .env
```

**"Anthropic API key required"**
```bash
# Add to .env file
echo 'ANTHROPIC_API_KEY=sk-ant-...' >> .env
```

**Port 8000 already in use**
```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn src.api.main:app --port 8001
```

**Image generation failing**
```bash
# Check Replicate token
curl -H "Authorization: Token $REPLICATE_API_TOKEN" \
  https://api.replicate.com/v1/account
```

---

## 📚 Documentation

- [API Reference](docs/api.md)
- [Tool Development Guide](docs/tools.md)
- [Deployment Guide](docs/deployment.md)
- [Contributing](docs/contributing.md)

---

## 🤝 Contributing

This is a private repository. Contact the owner for contribution access.

---

## 📄 License

**Private** — All Rights Reserved

© 2024-2026 RhythrosaLabs

---

## 🙏 Acknowledgments

Built with amazing open-source projects and APIs:

- [Anthropic Claude](https://anthropic.com) — AI language model
- [FastAPI](https://fastapi.tiangolo.com) — Web framework
- [Replicate](https://replicate.com) — Image generation
- [Printify](https://printify.com) — Print-on-demand
- [Shopify](https://shopify.com) — E-commerce
- [Serper](https://serper.dev) — Search API
- [Pydantic](https://pydantic.dev) — Data validation

---

<p align="center">
  <strong>Built with ❤️ by <a href="https://github.com/RhythrosaLabs">RhythrosaLabs</a></strong>
</p>

<p align="center">
  <sub>Otto Chat — Your AI Business Partner</sub>
</p>
