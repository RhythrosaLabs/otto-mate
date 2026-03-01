# Getting Started

This guide walks you through installing, configuring, and running Otto Chat for the first time.

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| **Python** | 3.11+ | Required |
| **pip** | Latest | Comes with Python |
| **Anthropic API Key** | — | [Get one here](https://console.anthropic.com/settings/keys) |
| **Git** | Any | For cloning the repo |

### Optional Dependencies

| Dependency | Purpose |
|------------|---------|
| **Node.js** | For alternative vanilla-js frontend |
| **Docker** | For containerized deployment |
| **Playwright** | For browser automation (`playwright install`) |
| **Ollama** | For local AI models |

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/RhythrosaLabs/otto-chat.git
cd otto-chat
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate    # macOS / Linux
# venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
# Full installation (all features)
pip install -r requirements.txt

# Minimal installation (core chat only)
pip install -r requirements-minimal.txt
```

### 4. Configure Environment

```bash
# Copy the template
cp config/.env.example .env

# Edit with your API keys
nano .env   # or open in any editor
```

At minimum, set:
```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 5. Install Browser Binaries (Optional)

Required only if you want browser automation features:
```bash
playwright install
```

---

## Running Otto

### Standard Launch

```bash
python run.py
```

This starts the server on **http://localhost:8000**.

### Development Mode (Auto-Reload)

```bash
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Using the Shell Script

```bash
chmod +x run_v2.sh
./run_v2.sh --dev       # Development mode
./run_v2.sh --prod      # Production mode (4 workers)
./run_v2.sh --port 3000 # Custom port
```

### Using Docker

```bash
docker-compose up -d
```

---

## First Run — Onboarding

When you first visit **http://localhost:8000**, Otto automatically redirects you to the **onboarding wizard** at `/onboarding`. This walks you through:

1. **API Key Setup** — Enter your Anthropic and optional API keys
2. **Connection Testing** — Verify each integration works
3. **Feature Selection** — Enable/disable features based on your needs
4. **Quick Tour** — Overview of the interface

After completing onboarding, you'll land at the main chat interface.

---

## Verifying the Installation

### Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "anthropic": true,
    "replicate": false,
    "printify": false
  }
}
```

### List Available Tools

```bash
curl http://localhost:8000/tools
```

### Send a Test Message

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello! What can you do?"}'
```

---

## Project Structure Overview

```
otto-chat/
├── run.py              # Main entry point
├── .env                # Your configuration (not committed)
├── config/
│   └── .env.example    # Configuration template
├── src/
│   ├── api/            # 34 API route modules
│   ├── core/           # 65 business logic modules
│   ├── tools/          # 40 tool implementations
│   ├── web/            # Built-in web UI (HTML/CSS/JS)
│   ├── channels/       # Multi-channel messaging
│   ├── database/       # SQLAlchemy ORM
│   ├── voice/          # Voice I/O pipeline
│   ├── storage/        # File storage backend
│   └── utils/          # Configuration & logging
├── plugins/            # 8 built-in plugins
├── skills/             # 17 skill packages
├── data/               # Runtime data (generated files, DB, etc.)
├── scripts/            # CLI & setup scripts
├── frontends/          # Alternative frontend implementations
└── docs/               # Documentation
```

---

## Next Steps

- **[Configuration](Configuration)** — Set up additional integrations (Replicate, Printify, Shopify, etc.)
- **[Features](Features)** — Explore what Otto can do
- **[API Reference](API-Reference)** — Build integrations with the REST API
- **[Plugin Development](Plugin-Development)** — Extend Otto with custom plugins
