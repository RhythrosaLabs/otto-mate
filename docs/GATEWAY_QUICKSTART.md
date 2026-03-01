# Otto Gateway & Channels - Quick Start Guide

## Overview

Otto now has OpenClaw-inspired architecture with:
- **Gateway WebSocket**: Single control plane for all messaging
- **Messaging Channels**: Telegram, Discord, Slack integrations
- **Voice Capabilities**: Wake word detection & Talk Mode
- **Skills/Plugin Ecosystem**: Extend Otto with custom capabilities
- **Device Pairing**: Secure approval flow for new devices

## Quick Setup

### 1. Install Dependencies

```bash
# Messaging channels
pip install python-telegram-bot discord.py slack-bolt

# Voice capabilities (optional)
pip install pvporcupine openai-whisper elevenlabs pyaudio

# Skills examples
pip install aiosmtplib google-api-python-client
```

### 2. Configure Channels

Copy example config:
```bash
cp config/channels.example.env .env
```

Edit `.env` with your tokens:
```bash
# Telegram
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Discord
DISCORD_BOT_TOKEN=MTIzNDU2Nzg5MDEyMzQ1Njc4OQ.Xy_abc.def123

# Slack
SLACK_BOT_TOKEN=xoxb-123456789-abcdefghijkl
SLACK_APP_TOKEN=xapp-1-A123-789-abc
```

### 3. Start Otto

```bash
./run_v2.sh
```

Gateway will start automatically if channels are configured!

## Using Channels

### Telegram

1. Create bot with @BotFather
2. Get token and add to `.env`
3. Message your bot!

Commands:
- `/start` - Introduce Otto
- `/status` - Check gateway status
- Send any message to chat with Otto

### Discord

1. Create app at Discord Developer Portal
2. Enable Message Content Intent
3. Get bot token and add to `.env`
4. Invite bot to your server
5. Message or mention Otto!

Commands:
- `!status` - Check gateway status  
- `!help` - Show help
- Mention `@Otto` to chat

### Slack

1. Create Slack app
2. Enable Socket Mode
3. Get bot token and app token
4. Add to `.env`
5. Install app to workspace
6. Message Otto in any channel!

Commands:
- `/otto` - Introduce Otto
- `/status` - Check gateway status
- Mention `@Otto` to chat

## Voice Capabilities

### Voice Wake (Hey Otto)

Passive listening for wake word:

```python
# In .env
ENABLE_VOICE_WAKE=true
WAKE_WORD="hey otto"
```

Say "Hey Otto" and it will activate Talk Mode!

### Talk Mode

Active voice conversation:

```python
# In .env
ENABLE_TALK_MODE=true
STT_PROVIDER=whisper
TTS_PROVIDER=elevenlabs
ELEVENLABS_API_KEY=your_key
```

Otto listens, transcribes, thinks, and responds with voice!

## Device Pairing

For clients/apps connecting to Gateway:

1. Client connects to `ws://localhost:18789/gateway/ws`
2. Sends connect handshake with device info
3. Gateway responds with pairing code (e.g., "A3F9B2")
4. Admin approves via UI or API:
   ```bash
   curl -X POST http://localhost:8000/gateway/pairing/approve \
     -H "Content-Type: application/json" \
     -d '{"pairing_code": "A3F9B2"}'
   ```
5. Client receives device token
6. Future connections use device token (no re-approval needed)

## Skills/Plugins

### Installing Skills

```bash
# From Git repository
otto skills install email https://github.com/otto/skills-email

# Or manually
mkdir skills/email
cd skills/email
# Create __init__.py with BaseSkill subclass
```

### Creating Custom Skills

```python
from src.core.skills import BaseSkill, SkillMetadata, SkillCategory

class MySkill(BaseSkill):
    @property
    def metadata(self):
        return SkillMetadata(
            id="my_skill",
            name="My Custom Skill",
            version="1.0.0",
            description="Does something cool",
            author="You",
            category=SkillCategory.CUSTOM
        )
    
    async def initialize(self, config):
        # Setup code
        pass
    
    async def shutdown(self):
        # Cleanup code
        pass
    
    def get_tools(self):
        return {
            "my_action": self.my_action
        }
    
    async def my_action(self, param: str):
        # Your logic here
        return f"Executed with: {param}"
```

Skills are auto-discovered from `skills/` directory on startup!

## Gateway WebSocket Protocol

### Connect Handshake (First Frame)

```json
{
  "type": "connect",
  "version": "1.0.0",
  "device": {
    "device_id": "iphone_12_abc123",
    "device_name": "John's iPhone 12",
    "platform": "ios"
  },
  "challenge": "random_challenge_string",
  "device_token": null
}
```

### Request Format

```json
{
  "type": "req",
  "id": "unique_request_id",
  "method": "agent.chat",
  "params": {
    "message": "Hello Otto!",
    "session_id": "session_123"
  }
}
```

### Response Format

```json
{
  "type": "res",
  "id": "unique_request_id",
  "ok": true,
  "payload": {
    "message": "Hi! How can I help you?",
    "usage": {...}
  }
}
```

### Server Events

```json
{
  "type": "event",
  "seq": 42,
  "event": "agent.message",
  "payload": {
    "session_id": "session_123",
    "message": "Processing your request..."
  }
}
```

## API Endpoints

### Gateway Stats
```
GET /gateway/stats
```

### List Clients
```
GET /gateway/clients
```

### List Pending Pairings
```
GET /gateway/pairing/pending
```

### Approve Pairing
```
POST /gateway/pairing/approve
{
  "pairing_code": "A3F9B2"
}
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Otto Gateway                         │
│                  (WebSocket Control Plane)              │
└────────┬────────┬────────┬───────────┬─────────────────┘
         │        │        │           │
    ┌────▼───┐ ┌─▼────┐ ┌─▼──────┐ ┌──▼─────┐
    │Telegram│ │Discord│ │ Slack  │ │Devices │
    │Channel │ │Channel│ │Channel │ │(Mobile)│
    └────────┘ └───────┘ └────────┘ └────────┘
         │        │         │           │
         └────────┴─────────┴───────────┘
                      │
            ┌─────────▼─────────┐
            │ Agent Orchestrator│
            └───────────────────┘
```

All messaging surfaces connect through Gateway, which routes to Otto's agent system.

## Troubleshooting

### Channels not starting
- Check tokens in `.env`
- Ensure dependencies installed: `pip install python-telegram-bot discord.py slack-bolt`
- Check logs for specific errors

### Voice not working
- Install dependencies: `pip install pvporcupine openai-whisper elevenlabs pyaudio`
- Check microphone permissions
- Verify API keys (ElevenLabs for TTS)

### Skills not loading
- Check `skills/` directory structure
- Ensure `__init__.py` exists in skill folder
- Check for missing dependencies in skill's `requirements.txt`

## What's Next?

- WhatsApp integration (via baileys-python or whatsapp-web.py)
- iMessage integration (macOS only, via AppleScript bridge)
- Signal integration (via signal-cli)
- Mobile apps (iOS/Android with Gateway client)
- ClawHub-style marketplace for skills
- Multi-instance Gateway clustering
- Voice wake word training (custom "Otto" wake word)

## Resources

- OpenClaw: https://github.com/openclawai/openclaw
- Gateway Protocol: See `src/core/gateway.py`
- Channel Base: See `src/channels/base.py`
- Skills System: See `src/core/skills.py`
- Voice System: See `src/core/voice.py`
