# 🎉 NEW: Otto Gateway & Messaging Platform

**Otto now has OpenClaw-inspired architecture!**

## What's New

### 🌐 Gateway WebSocket Architecture
- Single control plane for all messaging and clients
- WebSocket at `/gateway/ws` with req/res/event protocol
- Device pairing with approval flow
- Event streaming with sequence tracking

### 💬 Messaging Platform Integrations
- **Telegram Bot**: DM & group chat
- **Discord Bot**: Server & DM support  
- **Slack Bot**: Socket Mode integration
- Easy to add: WhatsApp, Signal, iMessage, Teams

### 🎤 Voice Capabilities
- **Voice Wake**: Passive listening for "Hey Otto"
- **Talk Mode**: Full voice conversation (STT + TTS)
- Multiple providers: Whisper, ElevenLabs, Google, Azure

### 🔌 Skills/Plugin Ecosystem
- Extend Otto with custom capabilities
- Auto-discovery from `skills/` directory
- Example skills: Email, Calendar, Weather
- Marketplace-ready architecture

## Quick Start

### 1. Install Dependencies

```bash
# Messaging (required)
pip install python-telegram-bot discord.py slack-bolt

# Voice (optional)
pip install openai-whisper elevenlabs pyaudio
```

### 2. Configure Channels

```bash
# Copy example config
cp config/channels.example.env .env

# Add your bot tokens
TELEGRAM_BOT_TOKEN=your_token
DISCORD_BOT_TOKEN=your_token
SLACK_BOT_TOKEN=your_token
SLACK_APP_TOKEN=your_token
```

### 3. Start Otto

```bash
./run_v2.sh
```

Gateway starts automatically! 🚀

### 4. Use Gateway CLI

```bash
# Check status
python scripts/gateway_cli.py status

# List clients
python scripts/gateway_cli.py clients

# Approve device pairing
python scripts/gateway_cli.py approve A3F9B2
```

## Usage

### Telegram
1. Create bot with @BotFather
2. Add token to `.env`
3. Message your bot!

### Discord
1. Create app at Discord Developer Portal
2. Enable Message Content Intent
3. Add token to `.env`
4. Invite bot and chat!

### Slack
1. Create Slack app with Socket Mode
2. Add both tokens to `.env`
3. Install to workspace
4. Message Otto!

## Documentation

- **Quick Start Guide**: [docs/GATEWAY_QUICKSTART.md](docs/GATEWAY_QUICKSTART.md)
- **Implementation Details**: [docs/GATEWAY_IMPLEMENTATION.md](docs/GATEWAY_IMPLEMENTATION.md)
- **Channel Configuration**: [config/channels.example.env](config/channels.example.env)

## Architecture

```
                    Otto Gateway
               (WebSocket Control Plane)
                        |
    ┌──────────┬────────┼────────┬──────────┐
    |          |        |        |          |
Telegram   Discord   Slack   Devices   Voice
    |          |        |        |          |
    └──────────┴────────┴────────┴──────────┘
                        |
              Agent Orchestrator
                   (Core AI)
```

All messaging surfaces → Gateway → Otto's brain

## Creating Skills

```python
from src.core.skills import BaseSkill, SkillMetadata

class MySkill(BaseSkill):
    @property
    def metadata(self):
        return SkillMetadata(
            id="my_skill",
            name="My Skill",
            version="1.0.0",
            description="Does cool stuff",
            author="You",
            category=SkillCategory.CUSTOM
        )
    
    async def initialize(self, config):
        pass
    
    def get_tools(self):
        return {
            "my_action": self.my_action
        }
    
    async def my_action(self, param: str):
        return f"Result: {param}"
```

Save to `skills/my_skill/__init__.py` - auto-discovered on startup!

## What's Next?

- WhatsApp integration
- Mobile apps (iOS/Android)
- Skills marketplace  
- Custom wake word ("Otto")
- Analytics dashboard

## Credits

Inspired by **OpenClaw** (202k ⭐) - Gateway architecture, messaging channels, device pairing

---

🚀 **Otto is now a true multi-surface AI assistant!**
