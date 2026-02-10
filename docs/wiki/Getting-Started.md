# Getting Started

This guide will walk you through setting up Otto Chat from scratch.

---

## Prerequisites

Before installing Otto Chat, ensure you have:

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **Python** | 3.11 | 3.12 |
| **RAM** | 4 GB | 8 GB |
| **Disk Space** | 2 GB | 10 GB |
| **OS** | macOS, Linux, Windows | macOS, Linux |

### Required API Keys

| Service | Purpose | Required? | Get Key |
|---------|---------|-----------|---------|
| **Anthropic** | Claude AI (core) | ✅ Required | [console.anthropic.com](https://console.anthropic.com/settings/keys) |
| **Replicate** | Image/Video AI | Recommended | [replicate.com](https://replicate.com/account/api-tokens) |
| **Printify** | Print-on-Demand | Optional | [printify.com/app/settings/api](https://printify.com/app/settings/api) |
| **Shopify** | E-Commerce | Optional | [shopify.dev](https://shopify.dev/docs/apps/auth/admin-app-access-tokens) |
| **Serper** | Web Search | Optional | [serper.dev](https://serper.dev) |
| **OpenAI** | Voice (Whisper) | Optional | [platform.openai.com](https://platform.openai.com/api-keys) |
| **SendGrid** | Email | Optional | [sendgrid.com](https://app.sendgrid.com/settings/api_keys) |

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/RhythrosaLabs/otto-chat.git
cd otto-chat
```

### Step 2: Create Virtual Environment

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs approximately 50+ packages including:
- `fastapi` - Web framework
- `anthropic` - Claude API client
- `replicate` - AI model access
- `httpx` - Async HTTP client
- `pydantic` - Data validation
- `uvicorn` - ASGI server

### Step 4: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your text editor:

```bash
nano .env
# or
code .env
# or
vim .env
```

### Step 5: Add API Keys

Edit your `.env` file:

```env
# ═══════════════════════════════════════════════════════════════
# REQUIRED - Core AI (at minimum, you need this)
# ═══════════════════════════════════════════════════════════════
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxx

# ═══════════════════════════════════════════════════════════════
# RECOMMENDED - Image & Video Generation
# ═══════════════════════════════════════════════════════════════
REPLICATE_API_TOKEN=r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ═══════════════════════════════════════════════════════════════
# OPTIONAL - Print-on-Demand (Printify)
# ═══════════════════════════════════════════════════════════════
PRINTIFY_API_TOKEN=your_printify_token
PRINTIFY_SHOP_ID=12345678

# ═══════════════════════════════════════════════════════════════
# OPTIONAL - E-Commerce (Shopify)
# ═══════════════════════════════════════════════════════════════
SHOPIFY_SHOP_NAME=your-store-name
SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxx

# ═══════════════════════════════════════════════════════════════
# OPTIONAL - Web Search
# ═══════════════════════════════════════════════════════════════
SERPER_API_KEY=your_serper_key

# ═══════════════════════════════════════════════════════════════
# OPTIONAL - Voice Features
# ═══════════════════════════════════════════════════════════════
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx

# ═══════════════════════════════════════════════════════════════
# OPTIONAL - Email (SendGrid or SMTP)
# ═══════════════════════════════════════════════════════════════
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxx
# Or for SMTP:
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Step 6: Start the Server

```bash
python run.py
```

You should see:
```
🚀 Otto Chat starting...
✅ Anthropic API connected
✅ Replicate API connected
✅ Printify API connected
📡 Server running at http://localhost:8000
```

### Step 7: Open in Browser

Navigate to: **http://localhost:8000**

---

## First-Time Setup (Onboarding)

When you first visit Otto, the onboarding wizard will guide you through:

### 1. API Keys Configuration
Enter your API keys. The wizard will test each connection.

### 2. Connection Testing
Otto verifies each service is accessible:
- ✅ Green checkmark = Connected
- ❌ Red X = Failed (check key)
- ⚪ Gray circle = Not configured

### 3. Preferences
Set your defaults:
- **Default AI Model**: Claude Opus 4 recommended
- **Default Image Model**: Flux Pro 1.1 recommended
- **Theme**: Choose from 14 options

### 4. Complete!
You're ready to start chatting.

---

## Your First Commands

Try these to get familiar with Otto:

### Basic Chat
```
"Hello! What can you help me with?"
```

### Generate an Image
```
"Generate a beautiful sunset over mountains in a photorealistic style"
```

### Create Content
```
"Write a blog post about the benefits of AI in small business"
```

### Research
```
"Research the top 5 AI tools launched in 2025"
```

### E-Commerce (if configured)
```
"Create a t-shirt design with an astronaut cat and upload it to Printify"
```

### Multi-Step Workflow
```
"Generate 3 different logo options for a coffee shop called 'Bean There', 
then create t-shirt products with each design and publish them to my store"
```

---

## Keyboard Shortcuts

Master these for power-user productivity:

| Shortcut | Action |
|----------|--------|
| `⌘/Ctrl + Enter` | Send message |
| `⌘/Ctrl + ,` | Open settings |
| `⌘/Ctrl + Q` | Open task queue |
| `⌘/Ctrl + J` | Toggle jobs panel |
| `⌘/Ctrl + K` | Quick search |
| `Escape` | Close sidebars |
| `↑` | Previous message (when input empty) |
| `?` | Show all shortcuts |

---

## Directory Structure

After setup, your directory looks like:

```
otto-chat/
├── .env                    # Your API keys (DO NOT COMMIT)
├── run.py                  # Start script
├── requirements.txt        # Python dependencies
│
├── src/                    # Source code
│   ├── api/               # FastAPI routes
│   ├── core/              # Core agents
│   ├── tools/             # 100+ tool implementations
│   └── web/               # Frontend HTML/CSS/JS
│
├── plugins/                # Third-party plugins
│   ├── web_scraper/
│   ├── notification_sender/
│   └── database_connector/
│
├── data/                   # Runtime data
│   ├── files/             # Generated content
│   ├── conversations/     # Chat history
│   ├── task_queue/        # Scheduled tasks
│   └── brand_brain/       # Brand intelligence
│
├── logs/                   # Log files
│   └── otto.log
│
└── docs/                   # Documentation
    └── wiki/              # Wiki source
```

---

## Verifying Your Installation

### Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "services": {
    "anthropic": "connected",
    "replicate": "connected"
  }
}
```

### List Available Tools

```bash
curl http://localhost:8000/tools | jq '.tools | length'
```

Should return: `100+`

### Test Chat API

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, what tools do you have?"}'
```

---

## Updating Otto

```bash
# Stop the running server (Ctrl+C)

# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart
python run.py
```

---

## Next Steps

- [[Features]] - Explore all capabilities
- [[Configuration]] - Advanced configuration options
- [[Docker Deployment]] - Production deployment
- [[Plugin Development]] - Extend with custom tools
- [[Troubleshooting]] - If something goes wrong
