# Otto Chat Wiki

Welcome to the Otto Chat documentation! Otto Chat is a universal AI business platform that automates everything through conversation.

## Quick Links

- [[Getting Started]] - Set up Otto Chat in minutes
- [[Features]] - Full feature overview
- [[Plugin Development]] - Create custom plugins
- [[API Reference]] - REST API documentation
- [[Themes]] - Customize the look and feel
- [[Task Queue]] - Schedule and manage tasks
- [[Troubleshooting]] - Common issues and solutions

## What is Otto Chat?

Otto Chat is a sophisticated autonomous AI platform that combines Claude's intelligence with 100+ integrated tools. It enables you to:

- 🎨 **Generate Images & Videos** - 15+ AI models including Flux Pro, SDXL, Runway, Luma
- 🛍️ **Manage E-Commerce** - Printify and Shopify integration
- 📧 **Send Marketing Emails** - HTML email campaigns
- 🔍 **Research & Analyze** - Web search, scraping, competitive intelligence
- 🎵 **Create Audio** - Music, voiceovers, sound effects
- 🔌 **Extend with Plugins** - Easy third-party plugin system

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Otto Chat Interface                      │
├─────────────────────────────────────────────────────────────┤
│                    Super Planning Agent                      │
│            (Claude Opus 4 + Task Decomposition)             │
├─────────────────────────────────────────────────────────────┤
│    Specialized Agents    │    Plugin System    │   Tools    │
│  ├── Content Agent       │  ├── Web Scraper    │  100+      │
│  ├── Image Agent         │  ├── Notifications  │  Built-in  │
│  ├── Video Agent         │  └── Database       │  Tools     │
│  └── Research Agent      │                     │            │
├─────────────────────────────────────────────────────────────┤
│            Integrations: Printify • Shopify • Replicate     │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

| Feature | Description |
|---------|-------------|
| **100+ Tools** | Image, video, audio, e-commerce, research, and more |
| **Plugin System** | Extend with custom tools and integrations |
| **14 Themes** | Customize appearance with built-in themes |
| **Task Queue** | Schedule and track multi-step operations |
| **Agent Delegation** | Specialized agents for different task types |
| **Calendar Integration** | Schedule tasks for specific dates |

## Getting Help

- Check the [[Troubleshooting]] page for common issues
- Review the [[API Reference]] for integration details
- See [[Plugin Development]] to extend Otto

---

**Version:** 2.0.0  
**Last Updated:** February 2026
