<h1 align="center">
  🤖 Otto Chat
</h1>

<p align="center">
  <strong>Universal AI Business Platform — Automate everything through conversation</strong>
</p>

<p align="center">
  Otto Chat is a full-stack autonomous AI platform that combines Claude's intelligence with 100+ integrated tools, multi-agent orchestration, and a beautiful web UI. Generate images and videos, manage e-commerce, automate research, build creative campaigns, and run your entire business — all through natural conversation.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.109+-green?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/Claude-Opus%204-purple?logo=anthropic" alt="Claude">
  <img src="https://img.shields.io/badge/Tools-100+-orange" alt="Tools">
  <img src="https://img.shields.io/badge/AI%20Models-15+-blue" alt="Models">
  <img src="https://img.shields.io/badge/Themes-14-pink" alt="Themes">
  <img src="https://img.shields.io/badge/Plugins-Extensible-green" alt="Plugins">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</p>

---

## Table of Contents

- [Screenshots](#-screenshots)
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Usage Examples](#-usage-examples)
- [Architecture](#-architecture)
- [Tools Reference](#-tools-reference)
- [Skills & Plugins](#-skills--plugins)
- [API Reference](#-api-reference)
- [Docker Deployment](#-docker-deployment)
- [Multi-Channel Support](#-multi-channel-support)
- [Security](#-security)
- [Troubleshooting](#-troubleshooting)
- [Roadmap](#-roadmap)
- [Documentation](#-documentation)
- [License](#-license)

---

## 📸 Screenshots

<p align="center">
  <img src="docs/screenshots/main-chat.png" alt="Otto Chat — Main Interface" width="100%">
  <br><em>Modern chat interface with gradient sidebars and real-time progress tracking</em>
</p>

<p align="center">
  <img src="docs/screenshots/conversation.png" alt="Otto Chat — AI Conversation" width="100%">
  <br><em>Intelligent AI responses powered by Claude Opus 4</em>
</p>

<p align="center">
  <img src="docs/screenshots/files-tab.png" alt="Otto Chat — Files Panel" width="100%">
  <br><em>File management with colorful filter chips and premium styling</em>
</p>

---

## ✨ Features

### 🧠 Multi-Agent Intelligence

| Capability | Description |
|------------|-------------|
| **Super Planning Agent** | Claude Opus 4 breaks complex tasks into parallel and sequential execution plans |
| **Agent Delegation** | Automatic routing to domain-specific agents — content, image, video, research, analytics |
| **Unified Agent System** | Multi-agent framework with Orchestrator, Planner, Executor, Researcher, Verifier roles |
| **Execution Modes** | Autonomous, Interactive, Collaborative, and Supervised operation |
| **Self-Improvement** | Learns from every interaction to improve future responses |
| **Context Preservation** | Remembers preferences (aspect ratios, styles, models) across conversations |
| **Smart Dependency Resolution** | Chains outputs between steps (e.g., generated images → products) |
| **Advanced Reasoning** | Multi-strategy reasoning engine for complex queries |
| **Proactive Intelligence** | Anticipates user needs and suggests actions |

### 🎨 Creative Generation

| Category | Models & Capabilities |
|----------|----------------------|
| **Image** (15+ models) | Flux Pro 1.1, Flux Dev, SDXL, Recraft V3, Ideogram V2 — portraits, landscapes, logos, icons, background removal, upscaling |
| **Video** (5+ models) | Runway Gen-3 Alpha, Luma Dream Machine, Minimax, Kling — cinematic, commercial, luxury, dynamic, ambient presets |
| **Audio** | AI music composition, ambient soundscapes, voice synthesis, professional voiceovers |
| **Commercial** | Apple/Nike/Tesla-quality promo scripts, multi-scene production, automatic enhancement |
| **Universal Editor** | AI-powered editing for images, video, audio, and 3D assets |

### 🛍️ E-Commerce

| Platform | Features |
|----------|----------|
| **Printify** | Full print-on-demand — design → upload → product → publish. 30+ product types (t-shirts, mugs, posters, framed art, hoodies). Multi-product batching |
| **Shopify** | Product CRUD, order management, inventory, customer management, analytics |

### 🔍 Research & Browser Automation

- **Web Search** — Google via Serper API with smart result parsing
- **Browser Automation** — Playwright-based headless browsing with stealth mode
- **Web Scraping** — Structured content extraction from any webpage
- **Competitive Intelligence** — Market trends, competitor analysis, opportunity reports
- **Deep Research** — Multi-source research with citations and summarization
- **News Aggregation** — Real-time monitoring and digest creation

### 🔌 Extensibility

- **Plugin System** — Drop plugins into `/plugins/` for instant integration. Types: Tool, Integration, Agent, Processor, UI, Workflow. Hot-reload supported
- **Skill Packages** — Modular skills in `/skills/` covering 17 business domains
- **Slash Commands** — Quick-access syntax (`/image`, `/video`, `/music`, `/help`, and more)
- **Tool Registry** — Decorator-based dynamic tool registration with category filtering

### 📋 Task Management

- **Visual Task Queue** — Pending, running, and completed tasks with real-time progress
- **Calendar View** — Schedule tasks for specific dates and times
- **Priority System** — Low, normal, high, urgent
- **Recurring Tasks** — Daily, weekly, monthly schedules
- **Task Dependencies** — Chained execution with dependency resolution
- **Business Workflows** — Pre-built templates for product launches, marketing campaigns, content pipelines, sales funnels

### 🎨 Modern UI

- **14 Visual Themes** — Aurora (default), Light, Dark, Midnight, Sunset, Ocean, Forest, Cherry, Retro, Copper, Nordic, Matrix, Lavender, Neon, Monochrome, Sakura
- **Gradient Sidebars** — Purple/pink/teal with subtle animations
- **A/B Editor Preview** — Side-by-side Original vs Result comparison
- **Keyboard Shortcuts** — ⌘+Enter (send), ⌘+, (settings), ⌘+Q (queue), ⌘+J (jobs), ? (help)
- **Real-Time Progress** — Live tracking for multi-step operations
- **Responsive** — Desktop and tablet optimized

### 📡 Multi-Channel

Otto is accessible through multiple channels simultaneously:

| Channel | Status |
|---------|--------|
| **Web UI** | Built-in chat interface |
| **Telegram** | Bot integration |
| **Discord** | Bot integration |
| **Slack** | App integration |
| **WhatsApp** | Business API |
| **WebSocket Gateway** | Unified control plane for custom clients |
| **REST API** | Full programmatic access |

### 🎙️ Voice

- **Speech-to-Text** — OpenAI Whisper
- **Text-to-Speech** — Natural voice responses with ElevenLabs
- **Voice Pipeline** — Full duplex: Speech → Text → AI → Text → Speech
- **Wake Word Detection** — Hands-free activation

### 📧 Email Marketing

- **Rich HTML Emails** — AI-generated templates via SendGrid or SMTP
- **Campaign Management** — Create and schedule email campaigns
- **Contact Import** — CSV/Excel contact importing

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Anthropic API Key** ([get one here](https://console.anthropic.com/settings/keys))

### Installation

```bash
# Clone the repository
git clone https://github.com/RhythrosaLabs/otto-chat.git
cd otto-chat

# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp config/.env.example .env
```

### Run

```bash
# Standard launch
python run.py

# Or with auto-reload for development
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Visit **http://localhost:8000** — first-time users are automatically redirected to the onboarding wizard.

---

## ⚙️ Configuration

Edit `.env` with your API keys. Only `ANTHROPIC_API_KEY` is required:

```env
# ═══════════════════ REQUIRED ═══════════════════
ANTHROPIC_API_KEY=sk-ant-...

# ═══════════════════ AI PROVIDERS (Optional) ═══════════════════
OPENAI_API_KEY=sk-...                    # Voice features, fallback models
REPLICATE_API_TOKEN=r8_...               # Image/video generation
ELEVENLABS_API_KEY=...                   # Text-to-speech

# ═══════════════════ E-COMMERCE (Optional) ═══════════════════
PRINTIFY_API_TOKEN=...                   # Print-on-demand
PRINTIFY_SHOP_ID=...
SHOPIFY_SHOP_NAME=your-store             # Shopify integration
SHOPIFY_ACCESS_TOKEN=shpat_...

# ═══════════════════ RESEARCH (Optional) ═══════════════════
SERPER_API_KEY=...                       # Google search API

# ═══════════════════ MESSAGING (Optional) ═══════════════════
TELEGRAM_BOT_TOKEN=...                   # Telegram bot
DISCORD_BOT_TOKEN=...                    # Discord bot
WHATSAPP_PHONE_ID=...                    # WhatsApp Business
WHATSAPP_ACCESS_TOKEN=...

# ═══════════════════ EMAIL (Optional) ═══════════════════
SENDGRID_API_KEY=...                     # Email campaigns
SMTP_HOST=smtp.gmail.com                 # Or SMTP provider
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...

# ═══════════════════ DATABASE (Optional) ═══════════════════
DATABASE_URL=sqlite:///./data/otto.db    # Default SQLite
# DATABASE_URL=postgresql://user:pass@localhost/otto  # PostgreSQL

# ═══════════════════ ADVANCED (Optional) ═══════════════════
DEFAULT_AI_MODEL=claude-sonnet-4-20250514
FALLBACK_AI_MODEL=gpt-4-turbo
MAX_TOKENS=8192
PORT=8000
DEBUG_MODE=false
LOG_LEVEL=INFO
JWT_SECRET_KEY=your-secret-key
REDIS_URL=redis://localhost:6379
CHROMA_PERSIST_DIRECTORY=./data/chroma
```

See [config/.env.example](config/.env.example) for all 109 configuration variables.

---

## 🎯 Usage Examples

### Natural Language Commands

```
💬 "Create a tall portrait image of a mountain landscape using Flux Pro,
    then make it into a framed art print"
   → Generates portrait image → maps to framed art → publishes to Printify

💬 "Create 3 different t-shirt designs for a sunset beach theme"
   → Generates 3 images in parallel → creates 3 products

💬 "Make me a cinematic promo video for my new coffee brand"
   → Creates premium commercial script → generates video with luxury styling

💬 "Research the top AI startups of 2025 and write a blog post about it"
   → Multi-source research → competitive analysis → formatted blog post

💬 "Generate a logo for 'Stellar Coffee' in a modern minimalist style"
   → Creates professional vector-style logo with Recraft V3

💬 "Send a promo email to hello@example.com about our new product launch"
   → Generates professional HTML email → sends via configured provider

💬 "Schedule a daily social media post at 9am about productivity tips"
   → Creates recurring task → generates fresh content daily
```

### Multi-Step Autonomous Workflows

```
User: "Launch a new product line of nature-themed wall art"

Otto automatically:
├── Generates 5 unique nature images (forest, ocean, mountain, desert, aurora)
├── Creates framed art products for each design
├── Writes compelling product descriptions
├── Sets appropriate pricing
└── Publishes all to your Printify store
```

### Slash Commands

```
/image sunset over mountains, oil painting style
/video cinematic drone shot of a coastline
/music lo-fi chill beat for a coffee shop
/research AI trends in e-commerce 2026
/help
```

---

## 🏗 Architecture

```
otto-chat/
├── run.py                        # Main entry point
│
├── src/
│   ├── api/                      # 34 REST/WebSocket route modules
│   │   ├── main.py               # FastAPI app (1500+ lines) with 30+ routers
│   │   ├── agents.py             # Agent management
│   │   ├── auth.py               # JWT authentication
│   │   ├── browser.py            # Browser automation endpoints
│   │   ├── business.py           # Autonomous business operations
│   │   ├── connections.py        # Service connection management
│   │   ├── conversations.py      # Conversation management
│   │   ├── creative_platform.py  # Creative project endpoints
│   │   ├── discord.py            # Discord bot API
│   │   ├── email.py              # Email endpoints
│   │   ├── extensions.py         # Extension management
│   │   ├── files.py              # File management & uploads
│   │   ├── gateway_ws.py         # WebSocket gateway
│   │   ├── intelligence.py       # Intelligence analytics
│   │   ├── integrations.py       # Third-party integrations
│   │   ├── models.py             # AI model listing & selection
│   │   ├── ollama.py             # Local model management
│   │   ├── plugins.py            # Plugin management
│   │   ├── profile.py            # User profile
│   │   ├── projects.py           # Project management
│   │   ├── scheduler_routes.py   # Task scheduling
│   │   ├── settings.py           # App configuration
│   │   ├── skills.py             # Skill registry
│   │   ├── social.py             # Social media management
│   │   ├── tasks.py              # Task queue management
│   │   ├── telegram.py           # Telegram bot API
│   │   ├── webhooks.py           # Webhook management
│   │   ├── whatsapp.py           # WhatsApp Business API
│   │   └── workflows.py          # Workflow creation & execution
│   │
│   ├── core/                     # 65 business logic modules
│   │   ├── agent_orchestrator.py        # Central brain (1825 lines)
│   │   ├── super_planning_agent.py      # Autonomous planning
│   │   ├── execution_agent.py           # Step execution
│   │   ├── super_intelligent_chat.py    # Conversational interface
│   │   ├── enhanced_intelligence.py     # Advanced reasoning layer
│   │   ├── unified_agent_system.py      # Multi-agent framework
│   │   ├── autonomous_orchestrator.py   # Fully autonomous operations
│   │   ├── business_workflows.py        # Pre-built workflow templates
│   │   ├── creative_platform.py         # Creative project management
│   │   ├── modality_system.py           # Modality-first model selection
│   │   ├── memory_agent.py              # ChromaDB vector memory
│   │   ├── plugin_system.py             # Plugin loading & lifecycle
│   │   ├── skills.py                    # Skill ecosystem
│   │   ├── tool_registry.py             # Dynamic tool discovery
│   │   ├── slash_commands.py            # /command syntax
│   │   ├── gateway.py                   # WebSocket control plane
│   │   ├── channel_manager.py           # Multi-channel management
│   │   ├── voice.py                     # Voice capabilities
│   │   ├── streaming_support.py         # SSE streaming
│   │   ├── session_manager.py           # Session lifecycle
│   │   ├── project_manager.py           # Project management
│   │   ├── context_manager.py           # Conversation context
│   │   ├── advanced_reasoning.py        # Multi-strategy reasoning
│   │   ├── proactive_intelligence.py    # Anticipatory suggestions
│   │   ├── smart_tool_router.py         # Intelligent tool selection
│   │   ├── self_improvement_loop.py     # Learning from outcomes
│   │   ├── intelligent_retry_system.py  # Smart retry with analysis
│   │   ├── error_recovery.py            # Graceful error handling
│   │   ├── agent_health_monitor.py      # Agent health monitoring
│   │   ├── agent_analytics.py           # Performance analytics
│   │   ├── agent_communication.py       # Inter-agent message bus
│   │   └── ollama_client.py             # Local model support
│   │
│   ├── tools/                    # 40 tool implementation modules
│   │   ├── image_generation.py   # 15+ AI image models
│   │   ├── video_generation.py   # Multi-model video
│   │   ├── promo_video.py        # Commercial production
│   │   ├── audio_processing.py   # Music & voice synthesis
│   │   ├── printify.py           # Print-on-demand
│   │   ├── shopify.py            # E-commerce
│   │   ├── research.py           # Web search & scraping
│   │   ├── browser.py            # Browser automation
│   │   ├── content.py            # Content generation
│   │   ├── email_marketing.py    # Email campaigns
│   │   ├── social_poster.py      # Social media posting
│   │   ├── universal_editor.py   # Universal media editor
│   │   ├── ai_file_editor.py     # AI code editing
│   │   ├── code_execution.py     # Code sandbox
│   │   ├── task_queue.py         # Task queue management
│   │   ├── replicate_universal.py # Replicate model hub
│   │   ├── model_chaining.py     # AI model pipelines
│   │   └── ...                   # 22 more modules
│   │
│   ├── web/                      # Built-in web UI
│   │   ├── chat.html             # Main interface (19K+ lines)
│   │   ├── settings.html         # Settings page
│   │   ├── files.html            # File browser
│   │   ├── agents.html           # Agent management
│   │   ├── workflows.html        # Workflow builder
│   │   ├── onboarding.html       # First-run setup wizard
│   │   └── static/               # CSS themes, JS modules
│   │
│   ├── channels/                 # Multi-channel messaging
│   │   ├── telegram.py
│   │   ├── discord.py
│   │   └── slack.py
│   │
│   ├── database/                 # SQLAlchemy ORM + Alembic
│   ├── voice/                    # Voice I/O pipeline
│   ├── storage/                  # File storage backend
│   └── utils/                    # Config & logging
│
├── plugins/                      # 8 built-in plugins
│   ├── web_scraper/
│   ├── notification_sender/
│   ├── database_connector/
│   ├── code_formatter/
│   ├── image_processor/
│   ├── social_poster/
│   ├── translator/
│   └── weather_fetcher/
│
├── skills/                       # 17 skill packages
│   ├── business_operations/
│   ├── content_creation/
│   ├── data_analysis/
│   ├── ecommerce_automation/
│   ├── email_marketing/
│   ├── seo_optimization/
│   ├── social_media_marketing/
│   ├── video_production/
│   ├── web_automation/
│   └── ...
│
├── scripts/                      # CLI & setup scripts
│   ├── setup.sh
│   ├── otto_cli.py
│   └── gateway_cli.py
│
├── data/                         # Runtime data (gitignored)
│   ├── chroma/                   # Vector store
│   ├── files/                    # Generated content
│   ├── conversations/            # Chat history
│   ├── projects/                 # Projects
│   └── ...
│
├── frontends/                    # Alternative frontends
│   └── vanilla-js/               # Standalone JS frontend
│
├── config/
│   └── .env.example              # Environment template (109 vars)
│
├── docker-compose.yml            # 5-service stack
├── Dockerfile
├── pyproject.toml
└── requirements.txt
```

### Core Architecture Patterns

| Pattern | Description |
|---------|-------------|
| **Modality-First Selection** | Determines output type (text, image, video, audio, code) before selecting the optimal AI model |
| **Smart Model Prioritization** | Local models → remote APIs → Replicate (cost optimization) |
| **Multi-Agent Collaboration** | Orchestrator → Planner → Executor → Verifier pipeline |
| **Self-Improvement Loop** | Analyzes outcomes to improve future responses |
| **Gateway Architecture** | Unified WebSocket control plane for all clients |
| **Channel Abstraction** | Same AI accessible through web, Telegram, Discord, Slack, WhatsApp |
| **Plugin/Skill Ecosystem** | Drop-in extensibility via `/plugins/` and `/skills/` |
| **Creative State Machine** | Project management with audit trails and stuck detection |

---

## 🔧 Tools Reference

### Image Generation (15+ models)

| Tool | Model | Best For |
|------|-------|----------|
| `generate_image` | Auto-select | General purpose |
| Flux Pro 1.1 | `black-forest-labs/flux-1.1-pro` | Highest quality |
| Flux Dev | `black-forest-labs/flux-dev` | Fast iteration |
| SDXL | `stability-ai/sdxl` | Versatile |
| Recraft V3 | `recraft-ai/recraft-v3` | Logos, icons, vector |
| Ideogram V2 | `ideogram-ai/ideogram-v2` | Text in images |
| `remove_background` | — | Background removal |
| `upscale_image` | — | AI upscaling |
| `add_text_overlay` | — | Text overlays |

### Video Generation (5+ models)

| Tool | Model | Style Presets |
|------|-------|---------------|
| `generate_ai_video` | Auto-select | Cinematic, Commercial, Luxury, Dynamic, Ambient |
| Runway Gen-3 Alpha | — | High quality |
| Luma Dream Machine | — | Creative |
| Minimax | — | Fast |
| Kling | — | Detailed |

### E-Commerce Tools

| Tool | Description |
|------|-------------|
| `create_printify_product` | Create print-on-demand products |
| `upload_printify_image` | Upload designs to Printify |
| `publish_printify_product` | Publish to sales channels |
| `get_blueprints` | Browse 30+ product templates |
| `create_shopify_product` | Create Shopify products |
| `get_shopify_orders` | View and manage orders |
| `update_shopify_inventory` | Inventory management |

### Research & Browser

| Tool | Description |
|------|-------------|
| `search_web` | Google search via Serper |
| `research_topic` | Deep multi-source research |
| `browse_url` | Navigate and extract web content |
| `analyze_competitor` | Competitive intelligence |
| `get_trending_topics` | Trend monitoring |
| `browser_navigate` | Headless browser automation |
| `browser_screenshot` | Page screenshots |
| `browser_click` / `browser_type` | Interaction automation |

### Content & Marketing

| Tool | Description |
|------|-------------|
| `generate_blog_post` | AI blog writing |
| `generate_product_description` | E-commerce copy |
| `generate_social_media_posts` | Multi-platform content |
| `generate_email_campaign` | Email marketing |
| `generate_seo_content` | SEO-optimized content |
| `generate_ad_copy` | Advertising copy |
| `improve_text` | Content enhancement |

### Code & Files

| Tool | Description |
|------|-------------|
| `ai_file_editor` | AI-powered edit, review, refactor, fix, explain |
| `code_execution` | Sandboxed code execution |
| `codebase_awareness` | Codebase understanding |
| `save_file` / `get_file` | File management |
| `save_image_from_url` | Download & save images |

### Task & Workflow

| Tool | Description |
|------|-------------|
| `task_queue` | Persistent task management |
| `scheduler` | APScheduler cron-like scheduling |
| `agent_delegation` | Inter-agent task delegation |
| `model_chaining` | AI model pipeline composition |

---

## 🧩 Skills & Plugins

### Skills (17 packages)

Skills are modular capability packages in `/skills/`:

| Skill | Domain |
|-------|--------|
| `business_operations` | Business management & analytics |
| `competitive_intelligence` | Market & competitor analysis |
| `content_creation` | Blog, social, marketing content |
| `customer_service` | Support & engagement |
| `data_analysis` | Data processing & visualization |
| `ecommerce_automation` | Store management |
| `email_marketing` | Email campaigns |
| `model_chaining` | AI model pipelines |
| `product_design` | Product design workflows |
| `research_analysis` | In-depth research |
| `seo_optimization` | Search engine optimization |
| `social_media_marketing` | Social campaigns |
| `task_queue` | Task management |
| `video_production` | Video workflows |
| `weather` | Weather data |
| `web_automation` | Browser automation |
| `workflow_automation` | Custom workflows |

### Plugins (8 built-in)

Plugins live in `/plugins/` and extend Otto with new capabilities:

| Plugin | Description |
|--------|-------------|
| `web_scraper` | Page scraping, link/table extraction, content search |
| `notification_sender` | Email, Slack, Discord, webhook notifications |
| `database_connector` | SQLite, PostgreSQL, MySQL queries |
| `code_formatter` | Code formatting & beautification |
| `image_processor` | Image manipulation & processing |
| `social_poster` | Social media posting |
| `translator` | Multi-language translation |
| `weather_fetcher` | Weather data retrieval |

### Creating a Plugin

```
plugins/my_plugin/
├── plugin.json        # Metadata and settings schema
├── main.py            # Plugin entry point
└── requirements.txt   # Dependencies (optional)
```

```json
{
  "name": "my_plugin",
  "version": "1.0.0",
  "description": "My custom plugin",
  "type": "tool",
  "entry_point": "main.py",
  "settings": {
    "api_key": { "type": "string", "required": true }
  }
}
```

---

## 📡 API Reference

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web chat interface |
| `/onboarding` | GET | First-run setup wizard |
| `/chat` | POST | Send chat message |
| `/chat/stream` | POST | SSE streaming chat |
| `/voice` | POST | Full voice pipeline (Speech→Text→AI→Text→Speech) |
| `/transcribe` | POST | Speech-to-text only |
| `/tools` | GET | List available tools |
| `/capabilities` | GET | Otto's capabilities |
| `/health` | GET | Health check with uptime and service status |
| `/health/detailed` | GET | Comprehensive component health |
| `/ws` | WebSocket | Real-time chat & voice |

### Resource APIs

| Prefix | Description |
|--------|-------------|
| `/api/settings` | App configuration |
| `/api/files` | File management, upload, download, tree |
| `/api/connections` | Service connections & status |
| `/api/agents` | Agent management |
| `/api/models` | AI model listing & selection |
| `/api/workflows` | Workflow CRUD & execution |
| `/api/business` | Autonomous business operations |
| `/api/projects` | Project management |
| `/api/skills` | Skill registry |
| `/api/plugins` | Plugin management |
| `/api/extensions` | Extension management |
| `/api/conversations` | Conversation management |
| `/api/tasks` | Task queue |
| `/api/scheduler` | Scheduled tasks |
| `/api/browser` | Browser automation |
| `/api/intelligence` | Intelligence analytics |
| `/api/creative` | Creative platform |
| `/api/integrations` | Third-party integrations |
| `/api/sessions` | Session management |
| `/api/auth` | JWT authentication |
| `/api/setup` | First-run setup |
| `/api/ollama` | Local Ollama models |
| `/api/model-manager` | Model lifecycle |
| `/api/brand` | Brand intelligence |
| `/api/social` | Social media |
| `/api/email` | Email sending |
| `/api/webhooks` | Webhook management |
| `/api/profile` | User profile |

### Messaging Channel APIs

| Prefix | Description |
|--------|-------------|
| `/api/whatsapp` | WhatsApp Business |
| `/api/telegram` | Telegram Bot |
| `/api/discord` | Discord Bot |
| `/api/email-webhook` | Inbound email |
| `/gateway` | WebSocket gateway |

### AI Editing Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ai/edit` | POST | AI file editing |
| `/api/ai/review` | POST | AI code review |
| `/api/ai/explain` | POST | AI code explanation |
| `/api/ai/refactor` | POST | AI refactoring |
| `/api/ai/fix` | POST | AI bug fixing |
| `/api/media/edit` | POST | Universal media editing |
| `/api/media/capabilities` | GET | Media editing capabilities |

### Example Requests

```bash
# Send a chat message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Generate a sunset beach image"}'

# Stream a response
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Write a blog post about AI trends"}'

# List available tools
curl http://localhost:8000/tools

# Upload a file
curl -X POST http://localhost:8000/api/files/upload \
  -F "file=@image.png" \
  -F "category=images"

# Health check
curl http://localhost:8000/health
```

### Health Response

```json
{
  "status": "healthy",
  "timestamp": "2026-03-01T12:00:00",
  "version": "1.0.0",
  "uptime": "2h 15m",
  "services": {
    "anthropic": true,
    "replicate": true,
    "printify": true,
    "chromadb": true
  }
}
```

---

## 🐳 Docker Deployment

### Quick Start

```bash
docker-compose up -d
```

### Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `otto-api` | Build from Dockerfile | 8000 | Main API server |
| `postgres` | postgres:15-alpine | 5432 | Relational database |
| `redis` | redis:7-alpine | 6379 | Caching & sessions |
| `chromadb` | chromadb/chroma:latest | 8001 | Vector store |
| `nginx` | nginx:alpine | 80, 443 | Reverse proxy |

### Docker Commands

```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f otto-api

# Stop all services
docker-compose down

# Reset data volumes
docker-compose down -v
```

### Production Deployment

```bash
# Set environment
export PORT=8000
export WORKERS=4
export LOG_LEVEL=warning

# Run with production settings
uvicorn src.api.main:app \
  --host 0.0.0.0 \
  --port $PORT \
  --workers $WORKERS \
  --log-level $LOG_LEVEL
```

---

## 🔐 Security

- **Environment Variables** — API keys stored in `.env` (never committed)
- **JWT Authentication** — Token-based auth with configurable expiry
- **CORS** — Configurable origin restrictions
- **Rate Limiting** — Per-minute and per-hour request throttling
- **Input Validation** — Pydantic models for all inputs
- **Sandboxed Execution** — Code execution in isolated environments

```bash
# Never commit secrets
echo ".env" >> .gitignore

# Generate a secure JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **Server won't start** | Check `python --version` is 3.11+, run `pip install -r requirements.txt` |
| **"Anthropic API key required"** | Add `ANTHROPIC_API_KEY=sk-ant-...` to `.env` |
| **Port 8000 in use** | `lsof -ti:8000 \| xargs kill -9` or use `--port 8001` |
| **Image generation failing** | Verify `REPLICATE_API_TOKEN` is valid |
| **Printify not connecting** | Check both `PRINTIFY_API_TOKEN` and `PRINTIFY_SHOP_ID` |
| **Browser automation errors** | Run `playwright install` for browser binaries |
| **ChromaDB errors** | Ensure `data/chroma/` directory exists and is writable |
| **Module import errors** | Run from project root: `cd otto-chat && python run.py` |

---

## 🗺️ Roadmap

### ✅ Completed

- Multi-agent orchestration with planning, execution, and verification
- 100+ tools across image, video, audio, e-commerce, research, and more
- Plugin system with 8 built-in plugins
- 17 skill packages
- 14 visual themes
- Task queue with calendar and scheduling
- Multi-channel support (Web, Telegram, Discord, Slack, WhatsApp)
- Voice pipeline (STT + TTS)
- WebSocket gateway for unified client connectivity
- Creative platform with state machine and audit trails
- Autonomous business workflows
- Self-improvement and advanced reasoning

### 🚧 In Progress

- Visual workflow automation builder
- Analytics dashboard
- Team collaboration features
- Plugin marketplace

### 🔮 Future

- Mobile app companion
- Voice-first interaction mode
- Custom fine-tuned model support
- White-label deployment toolkit
- Multi-tenant architecture

---

## 📚 Documentation

- **[GitHub Wiki](https://github.com/RhythrosaLabs/otto-chat/wiki)** — Comprehensive guides and reference
- [Getting Started](docs/GETTING_STARTED.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Plugin Development](plugins/README.md)
- [API Quick Start](docs/QUICK_START_GUIDE.md)
- [Smart Model System](docs/SMART_MODEL_SYSTEM.md)
- [Agentic Architecture](docs/AGENTIC_ARCHITECTURE.md)

---

## 📄 License

**Private** — All Rights Reserved

© 2024–2026 RhythrosaLabs

---

<p align="center">
  <strong>Built with ❤️ by <a href="https://github.com/RhythrosaLabs">RhythrosaLabs</a></strong>
  <br>
  <sub>Otto Chat — Your AI Business Partner</sub>
</p>
