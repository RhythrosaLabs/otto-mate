# Security

Security configuration and best practices for Otto.

---

## Authentication

### API Key Authentication

Otto supports API key-based authentication for API endpoints:

```env
API_KEY=your-secret-api-key
REQUIRE_AUTH=true
```

When enabled, all API requests must include the key:

```bash
curl -H "Authorization: Bearer your-secret-api-key" \
  http://localhost:8000/api/chat
```

### Session Management

- Sessions are stored server-side with unique IDs
- Session data includes conversation history, preferences, and state
- Sessions expire after configurable timeout

```env
SESSION_TIMEOUT=3600  # seconds
```

---

## CORS (Cross-Origin Resource Sharing)

Configure which origins can access the API:

```env
CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["*"]
CORS_ALLOW_HEADERS=["*"]
```

For development:

```env
CORS_ORIGINS=["*"]  # Allow all origins (NOT for production)
```

---

## Rate Limiting

Protect against abuse with rate limiting:

```env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60  # seconds
```

This limits each client to 100 requests per 60-second window.

### Per-Endpoint Limits

Some endpoints have stricter limits:
- `/api/chat` — Standard rate limit
- `/api/generate/*` — Lower limit (expensive operations)
- `/health` — No rate limit

---

## API Key Management

### Required API Keys

| Key | Purpose | Required |
|-----|---------|----------|
| `ANTHROPIC_API_KEY` | Claude AI models | Yes (primary AI) |
| `OPENAI_API_KEY` | GPT models, embeddings | Recommended |
| `REPLICATE_API_TOKEN` | Image/video/audio generation | Recommended |

### Optional API Keys

| Key | Purpose |
|-----|---------|
| `PRINTIFY_API_TOKEN` | E-commerce integration |
| `SERP_API_KEY` | Web search |
| `TAVILY_API_KEY` | Research search |
| `TELEGRAM_BOT_TOKEN` | Telegram channel |
| `DISCORD_BOT_TOKEN` | Discord channel |
| `SLACK_BOT_TOKEN` | Slack channel |
| `TWILIO_ACCOUNT_SID` | WhatsApp channel |
| `SENDGRID_API_KEY` | Email sending |

### Key Storage Best Practices

1. **Never commit keys** — Use `.env` files (included in `.gitignore`)
2. **Use environment variables** — Set via shell or Docker
3. **Rotate regularly** — Change keys periodically
4. **Minimum privilege** — Use keys with only necessary permissions
5. **Separate environments** — Different keys for dev/staging/production

---

## File Security

### Upload Restrictions

```env
MAX_UPLOAD_SIZE=104857600  # 100MB in bytes
ALLOWED_FILE_TYPES=["image/*", "text/*", "application/pdf"]
```

### File Storage

- Uploaded files are stored in `data/uploads/`
- Generated files are stored in `data/` subdirectories
- Files are served through authenticated endpoints

---

## Network Security

### Production Checklist

- [ ] **Use HTTPS** — Configure SSL/TLS via reverse proxy
- [ ] **Bind to localhost** — Don't expose directly to the internet
- [ ] **Use a reverse proxy** — Nginx or Caddy in front of Otto
- [ ] **Enable CORS restrictions** — Whitelist specific origins
- [ ] **Enable rate limiting** — Prevent API abuse
- [ ] **Set strong API key** — Long, random string
- [ ] **Firewall rules** — Only allow necessary ports
- [ ] **Keep updated** — Regularly pull security updates

### Recommended Architecture

```
Internet → Cloudflare/CDN → Nginx (SSL) → Otto (localhost:8000)
```

### Example Nginx with SSL

```nginx
server {
    listen 443 ssl;
    server_name otto.example.com;

    ssl_certificate /etc/letsencrypt/live/otto.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/otto.example.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Data Privacy

### Conversation Data

- Conversations are stored locally in `data/conversations/`
- No data is sent to third parties except AI API providers
- You control all data retention

### AI Provider Data

- **Anthropic (Claude)** — Check [Anthropic's data policy](https://anthropic.com/privacy)
- **OpenAI** — Check [OpenAI's data policy](https://openai.com/policies/privacy-policy)
- **Replicate** — Check [Replicate's privacy policy](https://replicate.com/privacy)

### Data Cleanup

```bash
# Clear conversation history
rm -rf data/conversations/*

# Clear generated files
rm -rf data/replicate_results/*
rm -rf data/browser_downloads/*

# Clear session data
rm -rf data/sessions/*
```

---

## Security Monitoring

### Logging

Otto logs all API requests and important events:

```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

Logs are stored in `logs/` and include:
- Request timestamps and methods
- Client IP addresses
- Error details
- Tool execution results

### Health Monitoring

```bash
# Check if Otto is running
curl http://localhost:8000/health

# Check system status
curl http://localhost:8000/api/status
```
