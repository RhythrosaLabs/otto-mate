# Configuration

Complete guide to configuring Otto Chat.

---

## Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-...` |

### AI Provider Keys

```env
# Primary AI (at least one required)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx

# Image/Video Generation
REPLICATE_API_TOKEN=r8_xxxxxxxxxxxxxxxxxxxxxxxx
FAL_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
STABILITY_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
IDEOGRAM_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx

# Search
GOOGLE_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx
GOOGLE_CSE_ID=xxxxxxxxxxxxxxxx
SERPER_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx
```

### E-Commerce Integration

```env
# Printify
PRINTIFY_API_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxx
PRINTIFY_SHOP_ID=xxxxxxxx

# Shopify
SHOPIFY_STORE_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxx

# Stripe (optional)
STRIPE_API_KEY=sk_live_xxxxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxx
```

### Server Configuration

```env
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# Security
SECRET_KEY=your-secret-key-at-least-32-characters
CORS_ORIGINS=http://localhost:3000,https://your-domain.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_PERIOD=60
```

### Storage Configuration

```env
# File Storage
STORAGE_PATH=./data
MAX_FILE_SIZE=104857600
ALLOWED_EXTENSIONS=png,jpg,jpeg,gif,webp,mp4,mp3,wav,pdf

# Database
DATABASE_URL=sqlite:///./data/otto.db
CHROMA_PERSIST_DIRECTORY=./data/chroma
```

---

## Configuration Files

### config/settings.yaml

Main application settings:

```yaml
# AI Settings
ai:
  default_model: claude-3-5-sonnet-20241022
  fallback_model: gpt-4o
  max_tokens: 8192
  temperature: 0.7
  streaming: true

# Memory
memory:
  max_context_messages: 50
  enable_long_term: true
  embedding_model: text-embedding-3-small

# Tools
tools:
  enabled: true
  auto_execute: true
  confirmation_required:
    - delete_file
    - publish_product
    - send_email

# Task Queue
task_queue:
  enabled: true
  max_concurrent: 3
  default_priority: normal
  retry_attempts: 3

# Plugins
plugins:
  enabled: true
  auto_load: true
  directory: ./plugins

# UI
ui:
  default_theme: default-dark
  show_thinking: true
  enable_sounds: false
```

### config/tools.yaml

Tool-specific configuration:

```yaml
# Image Generation
image_generation:
  default_model: flux-pro-1.1
  default_aspect_ratio: "1:1"
  auto_save: true
  max_batch_size: 4

# Video Generation
video_generation:
  default_model: runway
  default_duration: 5
  max_duration: 30

# Browser
browser:
  headless: true
  timeout: 30000
  viewport:
    width: 1920
    height: 1080

# Printify
printify:
  auto_publish: false
  default_print_provider: auto
  sync_interval: 3600
```

### config/agents.yaml

Agent configuration:

```yaml
agents:
  researcher:
    model: claude-3-5-sonnet-20241022
    skills:
      - web_search
      - scrape_webpage
      - summarize
    max_iterations: 10

  designer:
    model: claude-3-5-sonnet-20241022
    skills:
      - generate_image
      - edit_image
      - create_logo
    max_iterations: 5

  developer:
    model: claude-3-5-sonnet-20241022
    skills:
      - code_analysis
      - code_generation
      - testing

delegation:
  enabled: true
  auto_delegate: true
  max_delegation_depth: 3
```

---

## Settings API

### Get All Settings

```bash
GET /api/settings
```

### Update Settings

```bash
PUT /api/settings
Content-Type: application/json

{
  "theme": "cyberpunk",
  "default_model": "gpt-4o",
  "temperature": 0.8
}
```

### Reset to Defaults

```bash
POST /api/settings/reset
```

---

## Model Configuration

### Supported Models

| Provider | Models |
|----------|--------|
| Anthropic | claude-3-5-sonnet-20241022, claude-3-opus-20240229, claude-3-haiku-20240307 |
| OpenAI | gpt-4o, gpt-4-turbo, gpt-4, gpt-3.5-turbo |
| Local | ollama/llama2, ollama/mistral, ollama/codellama |

### Model Selection Priority

```yaml
models:
  # Primary model for main tasks
  primary: claude-3-5-sonnet-20241022
  
  # Fallback if primary unavailable
  fallback: gpt-4o
  
  # Specialized models
  coding: claude-3-5-sonnet-20241022
  creative: gpt-4o
  fast: claude-3-haiku-20240307
  
  # Local models (Ollama)
  local_enabled: true
  local_models:
    - ollama/llama2
    - ollama/codellama
```

### Temperature Settings

| Use Case | Temperature |
|----------|------------|
| Code generation | 0.2 |
| Analysis | 0.3 |
| General chat | 0.7 |
| Creative writing | 0.9 |
| Brainstorming | 1.0 |

---

## Security Configuration

### Authentication

```yaml
auth:
  enabled: false  # Set true for production
  method: api_key  # or jwt, oauth
  api_keys:
    - name: admin
      key: your-api-key-here
      permissions: ["*"]
    - name: readonly
      key: readonly-key
      permissions: ["read"]
```

### CORS Configuration

```yaml
cors:
  enabled: true
  origins:
    - http://localhost:3000
    - https://your-domain.com
  methods: ["GET", "POST", "PUT", "DELETE"]
  allow_credentials: true
```

### Rate Limiting

```yaml
rate_limiting:
  enabled: true
  
  # Global limits
  requests_per_minute: 60
  requests_per_hour: 1000
  
  # Endpoint-specific
  endpoints:
    /api/chat:
      requests_per_minute: 30
    /api/generate:
      requests_per_minute: 10
```

---

## Storage Configuration

### File Storage

```yaml
storage:
  # Local storage path
  path: ./data
  
  # File limits
  max_file_size: 100MB
  max_total_storage: 10GB
  
  # Cleanup
  auto_cleanup: true
  cleanup_after_days: 30
  
  # Cloud storage (optional)
  cloud:
    enabled: false
    provider: s3  # or gcs, azure
    bucket: otto-files
    region: us-east-1
```

### Database

```yaml
database:
  # SQLite (default)
  url: sqlite:///./data/otto.db
  
  # PostgreSQL
  # url: postgresql://user:pass@localhost/otto
  
  # MySQL
  # url: mysql://user:pass@localhost/otto
  
  # Connection pool
  pool_size: 5
  max_overflow: 10
```

### Vector Database (ChromaDB)

```yaml
chroma:
  persist_directory: ./data/chroma
  collection_name: otto_memory
  
  # Embedding settings
  embedding_function: openai  # or sentence_transformers
  embedding_model: text-embedding-3-small
  
  # Performance
  anonymized_telemetry: false
```

---

## Logging Configuration

### Log Levels

| Level | When to Use |
|-------|-------------|
| DEBUG | Development, troubleshooting |
| INFO | Production monitoring |
| WARNING | Potential issues |
| ERROR | Errors requiring attention |
| CRITICAL | System failures |

### Configuration

```yaml
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
  # File logging
  file:
    enabled: true
    path: ./logs/otto.log
    max_size: 10MB
    backup_count: 5
    
  # Console logging
  console:
    enabled: true
    colorize: true
    
  # External logging (optional)
  sentry:
    enabled: false
    dsn: your-sentry-dsn
```

---

## Docker Configuration

### docker-compose.yml

```yaml
version: '3.8'

services:
  otto:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./.env:/app/.env
    environment:
      - HOST=0.0.0.0
      - PORT=8000
    restart: unless-stopped
    
  # Optional: Redis for caching
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

volumes:
  redis-data:
```

### Environment Variables in Docker

```bash
# Run with env file
docker run --env-file .env otto-chat

# Or pass directly
docker run \
  -e OPENAI_API_KEY=sk-xxx \
  -e ANTHROPIC_API_KEY=sk-ant-xxx \
  otto-chat
```

---

## Production Configuration

### Recommended Settings

```env
# Production .env
DEBUG=false
LOG_LEVEL=WARNING

# Security
SECRET_KEY=<generate-strong-key>
CORS_ORIGINS=https://your-domain.com

# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=30
RATE_LIMIT_PERIOD=60

# Performance
MAX_CONCURRENT_TASKS=5
CHROMA_SERVER_MEMORY_LIMIT=4G
```

### Reverse Proxy (nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### SSL/TLS

```bash
# With Let's Encrypt
certbot --nginx -d your-domain.com
```
