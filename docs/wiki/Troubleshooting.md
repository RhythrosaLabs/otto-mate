# Troubleshooting

Solutions for common issues when running Otto Chat.

---

## Installation Issues

### Python Version Error

**Problem:** `SyntaxError` or `ModuleNotFoundError` on startup.

**Solution:** Otto requires Python 3.11+.
```bash
python --version  # Must be 3.11+

# If wrong version, use pyenv or update:
brew install python@3.11  # macOS
sudo apt install python3.11  # Ubuntu
```

### Dependency Installation Fails

**Problem:** `pip install -r requirements.txt` fails.

**Solution:**
```bash
# Upgrade pip first
pip install --upgrade pip

# Install with verbose output
pip install -r requirements.txt -v

# If specific packages fail, install core first:
pip install -r requirements-minimal.txt

# Common missing system deps (Ubuntu):
sudo apt install gcc g++ make libffi-dev libssl-dev

# Common missing system deps (macOS):
xcode-select --install
```

### Playwright Installation

**Problem:** Browser automation fails with `playwright` errors.

**Solution:**
```bash
pip install playwright
playwright install
playwright install-deps  # Linux only — installs system deps
```

---

## Startup Issues

### Server Won't Start

**Problem:** Server crashes immediately on startup.

**Checks:**
```bash
# 1. Check Python version
python --version

# 2. Check .env file exists
ls -la .env

# 3. Check Anthropic key is set
grep ANTHROPIC_API_KEY .env

# 4. Run with debug output
DEBUG_MODE=true python run.py

# 5. Check for port conflicts
lsof -i :8000
```

### Port Already in Use

**Problem:** `Address already in use` error.

**Solution:**
```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
PORT=8001 python run.py
```

### "Anthropic API Key Required"

**Problem:** Server starts but refuses to work.

**Solution:**
```bash
# Check .env has the key (not a placeholder)
cat .env | grep ANTHROPIC

# Should show: ANTHROPIC_API_KEY=sk-ant-api03-...
# NOT: ANTHROPIC_API_KEY=your_key_here

# Verify the key works
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "content-type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"claude-sonnet-4-20250514","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}'
```

### Module Import Errors

**Problem:** `ModuleNotFoundError: No module named 'src'`

**Solution:** Always run from the project root:
```bash
cd /path/to/otto-chat
python run.py

# Or with uvicorn
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### RuntimeWarning: coroutine was never awaited

**Problem:** Warning about `TaskScheduler.start` coroutine.

**Solution:** This is a known non-critical warning. The scheduler still works. It will be fixed in a future release.

---

## Feature Issues

### Image Generation Not Working

**Problem:** Image generation requests fail.

**Checks:**
```bash
# 1. Check Replicate token
curl -H "Authorization: Token $REPLICATE_API_TOKEN" \
  https://api.replicate.com/v1/account

# 2. Verify token in .env
grep REPLICATE .env

# 3. Check rate limits — Replicate has per-model limits

# 4. Try a specific model
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "generate a simple image of a blue circle using flux dev"}'
```

### Printify Connection Issues

**Problem:** Printify operations fail.

**Checks:**
```bash
# Both token AND shop ID are required
grep PRINTIFY .env
# Should show:
# PRINTIFY_API_TOKEN=eyJ...
# PRINTIFY_SHOP_ID=12345

# Test the connection
curl http://localhost:8000/api/connections/test/printify

# Verify token works
curl -H "Authorization: Bearer $PRINTIFY_API_TOKEN" \
  https://api.printify.com/v1/shops.json
```

### Shopify Connection Issues

**Problem:** Shopify operations fail.

**Checks:**
```bash
grep SHOPIFY .env
# Should show:
# SHOPIFY_SHOP_NAME=your-store
# SHOPIFY_ACCESS_TOKEN=shpat_...

# Test API
curl -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  "https://$SHOPIFY_SHOP_NAME.myshopify.com/admin/api/2024-01/shop.json"
```

### Web Search Not Working

**Problem:** Research and search features return empty results.

**Solution:**
```bash
# Check Serper API key
grep SERPER .env

# Test directly
curl -X POST https://google.serper.dev/search \
  -H "X-API-KEY: $SERPER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"q": "test search"}'
```

### Browser Automation Fails

**Problem:** Browser tools error out.

**Solution:**
```bash
# Install browser binaries
playwright install chromium

# Check if running headless
grep PLAYWRIGHT_HEADLESS .env  # Should be true for servers

# Increase timeout if pages load slowly
# Set BROWSER_TIMEOUT=60000 in .env
```

### Voice Features Not Working

**Problem:** Voice input/output fails.

**Solution:**
```bash
# For Speech-to-Text: needs OpenAI key
grep OPENAI_API_KEY .env

# For Text-to-Speech: needs ElevenLabs
grep ELEVENLABS_API_KEY .env

# Optional — install whisper locally
pip install openai-whisper
```

### ChromaDB Errors

**Problem:** Memory/vector store errors.

**Solution:**
```bash
# Create the data directory
mkdir -p data/chroma

# Check permissions
chmod 755 data/chroma

# Or use a remote ChromaDB instance
# CHROMA_HOST=localhost
# CHROMA_PORT=8001
```

---

## Performance Issues

### Slow Responses

**Possible causes:**
1. **Large conversation history** — Clear history with `DELETE /api/chat/history/{session_id}`
2. **Complex tool chains** — Long multi-step plans take time
3. **API rate limits** — Replicate and other APIs may throttle
4. **Memory pressure** — Check system resources

**Solutions:**
```bash
# Limit conversation history
echo "MEMORY_MAX_HISTORY=20" >> .env

# Reduce parallel tool limit
echo "PARALLEL_TOOL_LIMIT=3" >> .env

# Check system resources
top -l 1 | head -10  # macOS
free -h              # Linux
```

### High Memory Usage

**Solution:**
```bash
# Reduce ChromaDB memory
echo "CHROMA_PERSIST_DIRECTORY=./data/chroma" >> .env

# Limit WebSocket connections
echo "WS_MAX_CONNECTIONS=50" >> .env

# Use fewer workers
echo "API_WORKERS=1" >> .env
```

---

## Docker Issues

### Container Won't Start

```bash
# Check logs
docker-compose logs otto-api

# Rebuild
docker-compose up -d --build

# Check .env is mounted
docker exec otto-chat cat /app/.env
```

### Database Connection in Docker

```bash
# PostgreSQL must be ready before otto-api starts
# docker-compose.yml should have depends_on with healthcheck

# Check PostgreSQL is running
docker exec otto-postgres pg_isready
```

---

## Getting Help

If your issue isn't covered here:

1. **Check logs** — Look at terminal output or `logs/` directory
2. **Enable debug mode** — Set `DEBUG_MODE=true` and `LOG_LEVEL=DEBUG` in `.env`
3. **Check health endpoint** — `curl http://localhost:8000/health/detailed`
4. **Open an issue** — [GitHub Issues](https://github.com/RhythrosaLabs/otto-chat/issues)
