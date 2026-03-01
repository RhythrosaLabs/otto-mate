# FAQ

Frequently asked questions about Otto.

---

## General

### What is Otto?

Otto is an AI-powered universal platform that combines conversational AI, creative content generation, e-commerce management, web research, and task automation into a single application. It uses a multi-agent architecture powered by Claude, GPT, and other AI models.

### Is Otto free to use?

Otto itself is open source and free. However, it requires API keys from AI providers (Anthropic, OpenAI, Replicate) which have their own pricing. You can start with just an Anthropic API key.

### What models does Otto use?

- **Text**: Claude Opus 4 / Sonnet 4 (Anthropic), GPT-4 Turbo (OpenAI), local models via Ollama
- **Images**: Flux Pro, SDXL, Recraft V3 (via Replicate)
- **Video**: Runway Gen-3, Luma, Minimax, Kling (via Replicate)
- **Audio**: MusicGen, and other audio models (via Replicate)

### Can I run Otto locally without cloud APIs?

Partially. You can use Ollama for local text generation, but image/video/audio generation requires cloud APIs (Replicate). The web UI and task management features work without any API keys.

---

## Setup

### What are the minimum requirements?

- Python 3.11+
- 2 GB RAM (4 GB recommended)
- At least one AI API key (Anthropic recommended)

### How do I install Otto?

```bash
git clone https://github.com/RhythrosaLabs/otto-chat.git
cd otto-chat
pip install -r requirements.txt
python run.py
```

See the [Getting Started](Getting-Started.md) guide for detailed instructions.

### Which API key should I get first?

Start with **Anthropic** (`ANTHROPIC_API_KEY`). This gives you access to Claude for all text/code/reasoning tasks. Add Replicate next for image/video generation.

### How do I update Otto?

```bash
git pull origin main
pip install -r requirements.txt
python run.py
```

---

## Features

### Can Otto generate images?

Yes. With a Replicate API token, Otto can generate images using Flux Pro, SDXL, Recraft V3, and many other models. Just ask: "Generate an image of a sunset over mountains."

### Can Otto create videos?

Yes. Video generation is supported through Replicate using models like Runway Gen-3, Luma, Minimax, and Kling.

### Can Otto browse the web?

Yes. Otto uses Playwright for browser automation and can navigate websites, extract content, take screenshots, and perform research across multiple sources.

### Does Otto have memory?

Yes. Otto maintains conversation history per session and can store long-term knowledge in its Brand Brain (ChromaDB vector store). It remembers context within a conversation and can recall stored information across sessions.

### Can Otto manage my Printify store?

Yes. With a Printify API token, Otto can list products, create new products, upload designs, manage inventory, and more. See the [API Reference](API-Reference.md) for e-commerce endpoints.

### Can I use Otto with Telegram/Discord/Slack?

Yes. Otto supports multiple channels. See [Multi-Channel Setup](Multi-Channel-Setup.md) for configuration instructions.

---

## Technical

### What port does Otto run on?

Port 8000 by default. Change it with the `PORT` environment variable.

### How do I reset Otto?

```bash
# Reset conversations
rm -rf data/conversations/*

# Reset all data
rm -rf data/*

# Reset database
rm -f data/otto.db
```

### Can I run multiple instances?

Yes, use different ports:
```bash
PORT=8000 python run.py  # Instance 1
PORT=8001 python run.py  # Instance 2
```

### Where are generated files stored?

| Content | Location |
|---------|----------|
| Images | `data/replicate_results/` |
| Videos | `data/replicate_results/` |
| Browser results | `data/browser_use_results/` |
| Screenshots | `data/screenshots/` |
| Uploads | `data/uploads/` |
| Conversations | `data/conversations/` |
| Database | `data/otto.db` |

### How do I enable debug logging?

```env
LOG_LEVEL=DEBUG
```

### Can I use Otto behind a reverse proxy?

Yes. See [Docker Deployment](Docker-Deployment.md) for Nginx configuration examples.

---

## Troubleshooting

### Otto won't start

1. Check Python version: `python --version` (need 3.11+)
2. Install dependencies: `pip install -r requirements.txt`
3. Check for port conflicts: `lsof -i :8000`
4. Check logs for errors

### API calls are failing

1. Verify your API keys in `.env`
2. Check your API key quotas/billing
3. Try a different model
4. Check network connectivity

### Images aren't generating

1. Ensure `REPLICATE_API_TOKEN` is set
2. Check Replicate account has credits
3. Try a simpler prompt first
4. Check the model-specific parameters

### Browser automation fails

1. Install Playwright browsers: `playwright install chromium`
2. On Linux, install system deps: `playwright install-deps`
3. Check for firewall blocking

For more detailed troubleshooting, see the [Troubleshooting](Troubleshooting.md) guide.

---

## Contributing

### How can I contribute?

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

### How do I create a plugin?

See the [Plugin Development](Plugin-Development.md) guide.

### How do I create a skill?

See the [Skill Development](Skill-Development.md) guide.
