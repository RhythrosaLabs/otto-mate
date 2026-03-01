# Multi-Channel Setup

Otto supports multiple communication channels beyond the web UI, allowing you to interact through messaging platforms.

---

## Supported Channels

| Channel | Status | Protocol |
|---------|--------|----------|
| Web UI | ✅ Built-in | HTTP / WebSocket |
| Telegram | ✅ Supported | Telegram Bot API |
| Discord | ✅ Supported | Discord.py |
| Slack | ✅ Supported | Slack Bolt |
| WhatsApp | ✅ Supported | Twilio API |
| Email | ✅ Supported | SMTP / IMAP |

---

## Telegram Setup

### 1. Create a Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot`
3. Follow the prompts to name your bot
4. Copy the bot token

### 2. Configure Otto

```env
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_ENABLED=true
```

### 3. Features

- Text conversations
- Image generation and sending
- File uploads/downloads
- Slash commands via `/` prefix
- Group chat support

---

## Discord Setup

### 1. Create a Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Go to Bot → Add Bot
4. Copy the token
5. Enable Message Content Intent under Privileged Gateway Intents

### 2. Invite the Bot

Generate an invite URL with these permissions:
- Send Messages
- Read Message History
- Attach Files
- Embed Links
- Use Slash Commands

### 3. Configure Otto

```env
DISCORD_BOT_TOKEN=your-bot-token
DISCORD_ENABLED=true
```

### 4. Features

- Text conversations
- Embed-formatted responses
- Image/file attachments
- Server and DM support
- Thread support

---

## Slack Setup

### 1. Create a Slack App

1. Go to [Slack API](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Add Bot Token Scopes:
   - `chat:write`
   - `app_mentions:read`
   - `channels:history`
   - `files:write`
   - `im:read`
   - `im:write`
   - `im:history`

### 2. Configure Otto

```env
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_ENABLED=true
```

### 3. Features

- Direct messages
- Channel mentions
- Rich message formatting
- File sharing
- Thread conversations

---

## WhatsApp Setup

### 1. Twilio Account

1. Sign up at [Twilio](https://www.twilio.com)
2. Set up a WhatsApp Sandbox (or production number)
3. Get your Account SID, Auth Token, and WhatsApp number

### 2. Configure Otto

```env
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
WHATSAPP_ENABLED=true
```

### 3. Set Webhook

Point the Twilio webhook to:
```
https://your-domain.com/api/webhooks/whatsapp
```

### 4. Features

- Text conversations
- Image sending/receiving
- Location sharing
- Quick replies

---

## Email Channel

### Configure

```env
# Incoming email (IMAP)
EMAIL_IMAP_SERVER=imap.gmail.com
EMAIL_IMAP_PORT=993
EMAIL_ADDRESS=otto@yourdomain.com
EMAIL_PASSWORD=your-app-password

# Outgoing email (SMTP)
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USERNAME=otto@yourdomain.com
EMAIL_SMTP_PASSWORD=your-app-password

EMAIL_ENABLED=true
EMAIL_CHECK_INTERVAL=60
```

### Features

- Auto-respond to emails
- Process attachments
- HTML-formatted responses
- Thread tracking

---

## Channel Configuration File

All channel settings can be consolidated in a single env file:

```bash
cp config/channels.example.env .env
```

The example file includes all channel configurations with documentation.

---

## Multi-Channel Architecture

```
                    ┌─────────────┐
                    │   Web UI    │
                    └──────┬──────┘
                           │
┌──────────┐    ┌──────────┴──────────┐    ┌──────────┐
│ Telegram │────│   Gateway Router    │────│ Discord  │
└──────────┘    │                     │    └──────────┘
                │  Channel Adapter    │
┌──────────┐    │  Message Queue      │    ┌──────────┐
│  Slack   │────│  Response Router    │────│ WhatsApp │
└──────────┘    └──────────┬──────────┘    └──────────┘
                           │
                    ┌──────┴──────┐
                    │  Otto Core  │
                    └─────────────┘
```

Each channel uses an adapter that normalizes messages into Otto's internal format, allowing the AI core to be channel-agnostic.

---

## Best Practices

1. **Use different bot names** — Set distinct names per channel for clarity
2. **Rate limiting** — Configure per-channel rate limits to avoid API throttling
3. **Response formatting** — Each channel adapter handles format conversion (Markdown → HTML, embeds, etc.)
4. **Error isolation** — A failure in one channel won't affect others
5. **Logging** — Enable per-channel logging for debugging
