# Docker Deployment

Deploy Otto using Docker for consistent, reproducible environments.

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/RhythrosaLabs/otto-chat.git
cd otto-chat

# Set up environment
cp config/channels.example.env .env
# Edit .env with your API keys

# Build and run
docker-compose up -d
```

---

## Docker Compose

The included `docker-compose.yml` provides a complete deployment:

```yaml
version: "3.8"
services:
  otto:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./skills:/app/skills
      - ./plugins:/app/plugins
    restart: unless-stopped
    environment:
      - HOST=0.0.0.0
      - PORT=8000
```

### Services

| Service | Purpose | Port |
|---------|---------|------|
| `otto` | Main application | 8000 |

---

## Dockerfile

The Dockerfile uses a multi-stage approach:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps chromium

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run
CMD ["python", "run.py"]
```

---

## Environment Configuration

### Required Variables

```env
# At minimum, set one AI provider
ANTHROPIC_API_KEY=sk-ant-...

# For full functionality
OPENAI_API_KEY=sk-...
REPLICATE_API_TOKEN=r8_...
```

### Volume Mounts

| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| `./data` | `/app/data` | Persistent data (conversations, files, DB) |
| `./skills` | `/app/skills` | Custom skills |
| `./plugins` | `/app/plugins` | Custom plugins |
| `./.env` | `/app/.env` | Environment configuration |

---

## Production Deployment

### With Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name otto.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
}
```

### With SSL (Let's Encrypt)

```bash
# Install certbot
apt install certbot python3-certbot-nginx

# Get certificate
certbot --nginx -d otto.example.com

# Auto-renew
crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Docker Compose Production

```yaml
version: "3.8"
services:
  otto:
    build: .
    ports:
      - "127.0.0.1:8000:8000"
    env_file:
      - .env
    volumes:
      - otto-data:/app/data
      - ./skills:/app/skills
      - ./plugins:/app/plugins
    restart: always
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  otto-data:
    driver: local
```

---

## Resource Requirements

### Minimum

| Resource | Value |
|----------|-------|
| CPU | 1 core |
| RAM | 2 GB |
| Disk | 5 GB |

### Recommended

| Resource | Value |
|----------|-------|
| CPU | 2+ cores |
| RAM | 4+ GB |
| Disk | 20+ GB |
| Network | Stable internet (for AI APIs) |

---

## Maintenance

### Updating

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Backup

```bash
# Backup data directory
tar -czf otto-backup-$(date +%Y%m%d).tar.gz data/

# Backup with docker volumes
docker run --rm \
  -v otto-data:/data \
  -v $(pwd):/backup \
  alpine tar -czf /backup/otto-data-backup.tar.gz /data
```

### Logs

```bash
# View logs
docker-compose logs -f otto

# View last 100 lines
docker-compose logs --tail=100 otto
```

### Health Check

```bash
curl http://localhost:8000/health
```

---

## Troubleshooting Docker

| Issue | Solution |
|-------|----------|
| Port already in use | Change port mapping in docker-compose.yml |
| Container exits immediately | Check logs: `docker-compose logs otto` |
| Playwright failures | Ensure chromium is installed in container |
| Permission errors | Check volume mount permissions |
| Out of memory | Increase Docker memory limit or use resource constraints |
| Slow builds | Use `.dockerignore` to exclude unnecessary files |
