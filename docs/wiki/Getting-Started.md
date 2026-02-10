# Getting Started

Get Otto Chat up and running in 5 minutes.

## Prerequisites

- **Python 3.11+** - [Download Python](https://python.org/downloads)
- **Anthropic API Key** - [Get API Key](https://console.anthropic.com/settings/keys)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/RhythrosaLabs/otto-chat.git
cd otto-chat
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```env
# Required - Core AI
ANTHROPIC_API_KEY=sk-ant-...

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

### 5. Start the Server

```bash
python run.py
```

Visit **http://localhost:8000** to start chatting!

## First-Time Setup

1. Open http://localhost:8000
2. You'll be redirected to the onboarding wizard
3. Enter your API keys
4. Test connections
5. Start chatting!

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `⌘/Ctrl + Enter` | Send message |
| `⌘/Ctrl + ,` | Open settings |
| `⌘/Ctrl + Q` | Open task queue |
| `⌘/Ctrl + J` | Toggle jobs panel |
| `?` | Show keyboard shortcuts |

## Your First Commands

Try these to get started:

```
💬 "Generate an image of a sunset over mountains"

💬 "Create a t-shirt design with a space cat"

💬 "Research the top AI tools of 2026"

💬 "Create a promo video for my coffee brand"
```

## Docker Deployment

```bash
docker-compose up -d
```

See [[Docker Deployment]] for more options.

## Next Steps

- [[Features]] - Explore all capabilities
- [[Plugin Development]] - Add custom tools
- [[Themes]] - Customize the interface
- [[API Reference]] - Build integrations
