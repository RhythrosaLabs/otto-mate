# Configuration

Otto Chat is configured through environment variables in a `.env` file. Copy the template to get started:

```bash
cp config/.env.example .env
```

---

## Required Configuration

Only one variable is required to run Otto:

```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Everything else is optional and enables additional features.

---

## Complete Environment Variables Reference

### Core AI Providers

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | **Required.** Anthropic Claude API key |
| `OPENAI_API_KEY` | — | OpenAI API key for voice features and fallback models |
| `REPLICATE_API_TOKEN` | — | Replicate API token for image/video generation |
| `ELEVENLABS_API_KEY` | — | ElevenLabs API key for text-to-speech |

### AI Model Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_AI_MODEL` | `claude-sonnet-4-20250514` | Primary AI model |
| `FALLBACK_AI_MODEL` | `gpt-4-turbo` | Fallback when primary fails |
| `MAX_TOKENS` | `8192` | Maximum response tokens |
| `TEMPERATURE` | `0.7` | Response creativity (0.0–1.0) |

### Server Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |
| `API_WORKERS` | `1` | Number of uvicorn workers |
| `API_RELOAD` | `true` | Auto-reload on code changes |
| `DEBUG_MODE` | `false` | Enable debug output |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_FILE` | — | Path to log file (optional) |

### E-Commerce — Printify

| Variable | Default | Description |
|----------|---------|-------------|
| `PRINTIFY_API_TOKEN` | — | Printify API token |
| `PRINTIFY_SHOP_ID` | — | Printify shop ID |

### E-Commerce — Shopify

| Variable | Default | Description |
|----------|---------|-------------|
| `SHOPIFY_SHOP_NAME` | — | Your Shopify store name (e.g., `my-store`) |
| `SHOPIFY_ACCESS_TOKEN` | — | Shopify Admin API access token |
| `SHOPIFY_API_KEY` | — | Shopify API key |
| `SHOPIFY_API_SECRET` | — | Shopify API secret |

### Search & Research

| Variable | Default | Description |
|----------|---------|-------------|
| `SERPER_API_KEY` | — | Serper.dev Google search API key |

### Email

| Variable | Default | Description |
|----------|---------|-------------|
| `SENDGRID_API_KEY` | — | SendGrid API key for email campaigns |
| `SMTP_HOST` | — | SMTP server hostname |
| `SMTP_PORT` | `587` | SMTP server port |
| `SMTP_USER` | — | SMTP username |
| `SMTP_PASSWORD` | — | SMTP password |
| `EMAIL_FROM` | — | Default sender email address |

### Messaging — WhatsApp

| Variable | Default | Description |
|----------|---------|-------------|
| `WHATSAPP_PHONE_ID` | — | WhatsApp Business phone number ID |
| `WHATSAPP_ACCESS_TOKEN` | — | WhatsApp Cloud API access token |
| `WHATSAPP_VERIFY_TOKEN` | — | Webhook verification token |

### Messaging — Telegram

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | — | Telegram Bot API token |

### Messaging — Discord

| Variable | Default | Description |
|----------|---------|-------------|
| `DISCORD_BOT_TOKEN` | — | Discord bot token |

### Messaging — Slack

| Variable | Default | Description |
|----------|---------|-------------|
| `SLACK_BOT_TOKEN` | — | Slack bot token |
| `SLACK_APP_TOKEN` | — | Slack app-level token |

### Messaging — Twilio

| Variable | Default | Description |
|----------|---------|-------------|
| `TWILIO_ACCOUNT_SID` | — | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | — | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | — | Twilio phone number |

### YouTube

| Variable | Default | Description |
|----------|---------|-------------|
| `YOUTUBE_API_KEY` | — | YouTube Data API key |
| `YOUTUBE_CLIENT_ID` | — | OAuth2 client ID |
| `YOUTUBE_CLIENT_SECRET` | — | OAuth2 client secret |

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./data/otto.db` | Database connection string |

Supported databases:
- SQLite: `sqlite:///./data/otto.db` (default)
- PostgreSQL: `postgresql://user:pass@localhost:5432/otto`
- MySQL: `mysql://user:pass@localhost:3306/otto`

### Cache

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | — | Redis connection URL (e.g., `redis://localhost:6379`) |

### Vector Store (ChromaDB)

| Variable | Default | Description |
|----------|---------|-------------|
| `CHROMA_HOST` | `localhost` | ChromaDB host |
| `CHROMA_PORT` | `8001` | ChromaDB port |
| `CHROMA_PERSIST_DIRECTORY` | `./data/chroma` | Local persistence directory |

### Security

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET_KEY` | — | Secret key for JWT token signing |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_EXPIRE_MINUTES` | `1440` | Token expiry (minutes) |
| `API_KEY_HEADER` | `X-API-Key` | API key header name |

### Rate Limiting

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_PER_MINUTE` | `60` | Max requests per minute |
| `RATE_LIMIT_PER_HOUR` | `1000` | Max requests per hour |

### Voice

| Variable | Default | Description |
|----------|---------|-------------|
| `VOICE_MODEL` | `whisper-1` | Speech-to-text model |
| `TTS_MODEL` | `tts-1` | Text-to-speech model |
| `TTS_VOICE_ID` | `alloy` | Default TTS voice |
| `SAMPLE_RATE` | `16000` | Audio sample rate |

### WebSocket

| Variable | Default | Description |
|----------|---------|-------------|
| `WS_HEARTBEAT_INTERVAL` | `30` | WebSocket heartbeat (seconds) |
| `WS_MAX_CONNECTIONS` | `100` | Max concurrent WebSocket connections |

### Tool Execution

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_TOOL_RETRIES` | `3` | Max retry attempts for failed tools |
| `TOOL_TIMEOUT_SECONDS` | `300` | Tool execution timeout |
| `PARALLEL_TOOL_LIMIT` | `5` | Max parallel tool executions |

### Memory

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMORY_MAX_HISTORY` | `50` | Max conversation history entries |
| `MEMORY_SIMILARITY_THRESHOLD` | `0.7` | Minimum similarity for memory recall |
| `MEMORY_TOP_K` | `5` | Number of memories to retrieve |

### Browser Automation

| Variable | Default | Description |
|----------|---------|-------------|
| `PLAYWRIGHT_HEADLESS` | `true` | Run browser in headless mode |
| `BROWSER_TIMEOUT` | `30000` | Browser operation timeout (ms) |
| `SCREENSHOT_PATH` | `./data/screenshots` | Screenshot storage path |

### File Storage

| Variable | Default | Description |
|----------|---------|-------------|
| `UPLOAD_DIR` | `./data/uploads` | File upload directory |
| `MAX_UPLOAD_SIZE` | `52428800` | Max upload size in bytes (50MB) |
| `ALLOWED_EXTENSIONS` | `*` | Allowed file extensions |

### Monitoring

| Variable | Default | Description |
|----------|---------|-------------|
| `PROMETHEUS_PORT` | `9090` | Prometheus metrics port |
| `SENTRY_DSN` | — | Sentry error tracking DSN |

---

## Configuration Tips

### Minimal Setup (Chat Only)
```env
ANTHROPIC_API_KEY=sk-ant-...
```

### Creative Production Setup
```env
ANTHROPIC_API_KEY=sk-ant-...
REPLICATE_API_TOKEN=r8_...
OPENAI_API_KEY=sk-...
```

### Full E-Commerce Setup
```env
ANTHROPIC_API_KEY=sk-ant-...
REPLICATE_API_TOKEN=r8_...
PRINTIFY_API_TOKEN=...
PRINTIFY_SHOP_ID=...
SHOPIFY_SHOP_NAME=my-store
SHOPIFY_ACCESS_TOKEN=shpat_...
SERPER_API_KEY=...
```

### Full Production Setup
```env
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
REPLICATE_API_TOKEN=r8_...
ELEVENLABS_API_KEY=...
SERPER_API_KEY=...
PRINTIFY_API_TOKEN=...
PRINTIFY_SHOP_ID=...
DATABASE_URL=postgresql://otto:pass@localhost:5432/otto
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=your-secure-random-key
LOG_LEVEL=WARNING
API_WORKERS=4
```

---

## Settings Management

### Via Web UI

Navigate to **Settings** (⌘+, or sidebar) to configure:
- API keys for all integrations
- Connection testing (verify keys work)
- Feature toggles
- Theme selection

### Via REST API

```bash
# Get current settings
curl http://localhost:8000/api/settings

# Update settings
curl -X PUT http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{"anthropic_api_key": "sk-ant-..."}'

# Test a connection
curl http://localhost:8000/api/connections/test/anthropic
```

### Via CLI

```bash
python scripts/otto_cli.py config set ANTHROPIC_API_KEY sk-ant-...
python scripts/otto_cli.py config show
```
