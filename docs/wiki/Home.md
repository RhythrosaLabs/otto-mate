# Otto Chat Wiki

Welcome to the comprehensive Otto Chat documentation! Otto Chat is a universal AI business platform that automates everything through natural conversation.

---

## 📚 Table of Contents

### Getting Started
- [[Getting Started]] - Installation and first-time setup
- [[Configuration]] - Environment variables and settings
- [[Docker Deployment]] - Container-based deployment

### Core Features
- [[Features]] - Complete feature overview
- [[AI Models]] - Available AI models and capabilities
- [[Tools Reference]] - All 100+ tools documented
- [[Agent Delegation]] - Specialized agent system

### Integrations
- [[Printify Integration]] - Print-on-demand workflows
- [[Shopify Integration]] - E-commerce management
- [[Replicate Integration]] - AI model access
- [[Email Integration]] - Marketing automation

### User Interface
- [[Themes]] - Visual customization
- [[Keyboard Shortcuts]] - Power-user navigation
- [[Task Queue]] - Task management and scheduling
- [[File Management]] - Asset organization

### Development
- [[Plugin Development]] - Create custom plugins
- [[API Reference]] - REST API documentation
- [[Webhooks]] - Event-driven integrations
- [[Contributing]] - Development guidelines

### Support
- [[Troubleshooting]] - Common issues and solutions
- [[FAQ]] - Frequently asked questions
- [[Changelog]] - Version history

---

## 🤖 What is Otto Chat?

Otto Chat is an **autonomous AI business automation platform** that combines Claude Opus 4's intelligence with 100+ integrated tools. Unlike simple chatbots, Otto can:

1. **Understand complex, multi-step requests**
2. **Create execution plans automatically**
3. **Run tasks in parallel when possible**
4. **Chain tool outputs together**
5. **Remember your preferences across sessions**
6. **Delegate to specialized agents**

### Example Workflow

When you say: *"Create a product line of 5 nature-themed framed art prints and publish them to my store"*

Otto automatically:
```
1. Generates 5 unique nature images (parallel)
   ├── Forest scene
   ├── Ocean sunset
   ├── Mountain landscape
   ├── Desert vista
   └── Aurora borealis

2. Uploads each image to Printify (parallel)

3. Creates 5 framed art products with:
   ├── Auto-generated titles
   ├── SEO-optimized descriptions
   ├── Appropriate pricing
   └── Correct product templates

4. Publishes all to your connected store

5. Returns summary with product links
```

This entire workflow runs autonomously without additional prompts.

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                                 │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────────┐ │
│  │   Chat     │ │   Queue    │ │  Calendar  │ │   File Browser     │ │
│  └────────────┘ └────────────┘ └────────────┘ └────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     SUPER PLANNING AGENT                              │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  Claude Opus 4 + Task Decomposition + Context Preservation      │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                 │
│  │  Task        │ │  Dependency  │ │  Progress    │                 │
│  │  Analyzer    │ │  Resolver    │ │  Tracker     │                 │
│  └──────────────┘ └──────────────┘ └──────────────┘                 │
└──────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    SPECIALIZED AGENTS                                 │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────────┐ │
│  │  Content   │ │   Image    │ │   Video    │ │     Research       │ │
│  │   Agent    │ │   Agent    │ │   Agent    │ │      Agent         │ │
│  └────────────┘ └────────────┘ └────────────┘ └────────────────────┘ │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────────┐ │
│  │ Analytics  │ │  E-commerce│ │   Audio    │ │     Automation     │ │
│  │   Agent    │ │   Agent    │ │   Agent    │ │      Agent         │ │
│  └────────────┘ └────────────┘ └────────────┘ └────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      TOOL LAYER (100+)                               │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────────┐ │
│  │   Image    │ │   Video    │ │   Audio    │ │     Content        │ │
│  │   Tools    │ │   Tools    │ │   Tools    │ │     Tools          │ │
│  └────────────┘ └────────────┘ └────────────┘ └────────────────────┘ │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────────┐ │
│  │  Printify  │ │  Shopify   │ │  Research  │ │     Browser        │ │
│  │   Tools    │ │   Tools    │ │   Tools    │ │     Tools          │ │
│  └────────────┘ └────────────┘ └────────────┘ └────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      PLUGIN SYSTEM                                    │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────────┐ │
│  │   Web      │ │ Notification│ │  Database  │ │   Your Custom      │ │
│  │  Scraper   │ │   Sender   │ │ Connector  │ │     Plugin         │ │
│  └────────────┘ └────────────┘ └────────────┘ └────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                                  │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────────┐ │
│  │ Anthropic  │ │ Replicate  │ │  Printify  │ │     Shopify        │ │
│  │  (Claude)  │ │ (AI Models)│ │   (POD)    │ │   (E-commerce)     │ │
│  └────────────┘ └────────────┘ └────────────┘ └────────────────────┘ │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────────┐ │
│  │  Serper    │ │  SendGrid  │ │   OpenAI   │ │      SMTP          │ │
│  │  (Search)  │ │  (Email)   │ │  (Whisper) │ │     (Email)        │ │
│  └────────────┘ └────────────┘ └────────────┘ └────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/RhythrosaLabs/otto-chat.git
cd otto-chat

# Setup environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run
python run.py
```

Visit http://localhost:8000 to start!

---

## 📊 Platform Statistics

| Metric | Value |
|--------|-------|
| **Total Tools** | 100+ |
| **AI Models** | 15+ |
| **Visual Themes** | 14 |
| **Plugin Examples** | 3 |
| **Specialized Agents** | 8 |
| **Product Templates** | 30+ |
| **Supported Languages** | Python |
| **API Style** | REST + WebSocket |

---

## 🔗 External Resources

- **GitHub Repository**: https://github.com/RhythrosaLabs/otto-chat
- **Issue Tracker**: https://github.com/RhythrosaLabs/otto-chat/issues
- **Anthropic Docs**: https://docs.anthropic.com
- **Replicate Docs**: https://replicate.com/docs
- **Printify API**: https://developers.printify.com
- **Shopify API**: https://shopify.dev/docs/api

---

## 📝 License

**Private** — All Rights Reserved  
© 2024-2026 RhythrosaLabs

---

**Version:** 2.0.0  
**Last Updated:** February 2026
