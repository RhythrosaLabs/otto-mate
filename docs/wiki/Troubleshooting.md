# Troubleshooting

Solutions for common issues with Otto Chat.

---

## Quick Diagnostics

Run the diagnostic command:

```bash
python -c "from src.utils.diagnostics import run_diagnostics; run_diagnostics()"
```

Or via API:

```bash
curl http://localhost:8000/api/health/detailed
```

---

## Installation Issues

### Python Version Errors

**Problem:** `Python 3.11+ required`

**Solution:**
```bash
# Check Python version
python --version

# Install Python 3.11+
# macOS
brew install python@3.11

# Ubuntu/Debian
sudo apt install python3.11

# Use specific version
python3.11 -m venv venv
```

### Dependency Installation Fails

**Problem:** `pip install` errors

**Solutions:**

```bash
# Upgrade pip
pip install --upgrade pip

# Install with legacy resolver
pip install -r requirements.txt --use-deprecated=legacy-resolver

# Missing system dependencies (Ubuntu)
sudo apt install python3-dev build-essential libffi-dev

# macOS
xcode-select --install
brew install openssl
```

### Node.js/npm Errors

**Problem:** Frontend build fails

**Solution:**
```bash
# Check Node version (16+ required)
node --version

# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

---

## Server Issues

### Port Already in Use

**Problem:** `Address already in use: 8000`

**Solution:**
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
python run.py --port 8001
```

### Server Won't Start

**Problem:** Server crashes on startup

**Checklist:**
1. Check logs: `tail -f logs/otto.log`
2. Verify `.env` file exists and has required keys
3. Check database connection
4. Verify ChromaDB data isn't corrupted

```bash
# Reset ChromaDB
rm -rf data/chroma
python run.py  # Will recreate
```

### Memory Issues

**Problem:** `MemoryError` or slow performance

**Solutions:**
```bash
# Check memory usage
ps aux | grep python

# Limit ChromaDB memory
export CHROMA_SERVER_NOFILE_LIMIT=65535
export CHROMA_SERVER_MEMORY_LIMIT=2G

# Use minimal requirements
pip install -r requirements-minimal.txt
```

---

## API Key Issues

### Invalid API Key

**Problem:** `AuthenticationError: Invalid API Key`

**Solutions:**

1. **Check .env file format:**
```env
# Correct
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx

# Wrong (no quotes needed)
OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxx"
```

2. **Verify key is active:**
```bash
# OpenAI
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Anthropic
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01"
```

3. **Check for billing issues** on provider dashboard

### Rate Limiting

**Problem:** `429 Too Many Requests`

**Solutions:**
```env
# Add to .env to enable rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_PERIOD=60
```

Or wait and retry - most limits reset within a minute.

### Key Not Being Read

**Problem:** API key in `.env` but not working

**Solutions:**
```bash
# Ensure .env is in project root
ls -la .env

# Restart server (keys read at startup)
# Ctrl+C then:
python run.py

# Verify key is loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('OPENAI_API_KEY', 'NOT FOUND')[:10])"
```

---

## AI Generation Issues

### Image Generation Fails

**Problem:** Image tools return errors

| Error | Solution |
|-------|----------|
| `NSFW content detected` | Modify prompt to be SFW |
| `Invalid dimensions` | Use supported aspect ratio |
| `Timeout` | Image is processing, wait longer |
| `Credit limit` | Check Replicate/API credits |

```bash
# Check Replicate status
curl https://api.replicate.com/v1/predictions \
  -H "Authorization: Token $REPLICATE_API_TOKEN"
```

### Video Generation Times Out

**Problem:** Video generation never completes

**Solutions:**
1. Videos can take 2-5 minutes - be patient
2. Check generation status via API
3. Simplify prompt (fewer motion elements)
4. Use shorter duration

```bash
# Check video status
curl http://localhost:8000/api/generations/{generation_id}
```

### Wrong Model Being Used

**Problem:** Response quality not as expected

**Solution:** Specify model in settings:
```json
{
  "default_model": "claude-3-5-sonnet-20241022",
  "fallback_model": "gpt-4o"
}
```

---

## Printify Issues

### Connection Failed

**Problem:** Can't connect to Printify

**Checklist:**
1. Verify API token is correct
2. Check token has correct scopes
3. Token not expired

```bash
# Test Printify connection
curl https://api.printify.com/v1/shops.json \
  -H "Authorization: Bearer $PRINTIFY_API_TOKEN"
```

### Image Upload Fails

**Problem:** Images won't upload to Printify

**Solutions:**
1. Image must be accessible URL (not localhost)
2. Check image dimensions meet requirements
3. Format must be PNG, JPG, or SVG
4. File size under 50MB

```bash
# Upload test
curl -X POST https://api.printify.com/v1/uploads/images.json \
  -H "Authorization: Bearer $PRINTIFY_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"file_name": "test.png", "url": "https://example.com/image.png"}'
```

### Product Creation Fails

**Problem:** Can't create products

**Common causes:**
- Invalid blueprint ID
- Missing required print areas
- Invalid variant selections

```bash
# Get valid blueprints
curl https://api.printify.com/v1/catalog/blueprints.json \
  -H "Authorization: Bearer $PRINTIFY_API_TOKEN"
```

---

## Shopify Issues

### Authentication Failed

**Problem:** Shopify API returns 401

**Solutions:**
1. Verify Access Token is correct
2. Check app has required scopes
3. Store URL is correct format

```env
# Correct format
SHOPIFY_STORE_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxx
```

### Product Sync Issues

**Problem:** Products not syncing correctly

**Checklist:**
- Check product status is `active`
- Verify inventory tracking settings
- Check for duplicate SKUs

---

## Plugin Issues

### Plugin Not Loading

**Problem:** Installed plugin doesn't appear

**Checklist:**
1. Check plugin directory structure:
   ```
   plugins/my-plugin/
   ├── manifest.json
   └── main.py
   ```
2. Verify manifest.json is valid JSON
3. Check for Python syntax errors in main.py
4. Restart server after installing

```bash
# Check plugin logs
grep "plugin" logs/otto.log | tail -50
```

### Plugin Dependency Missing

**Problem:** `ModuleNotFoundError` in plugin

**Solution:**
```bash
# Install plugin dependencies
pip install -r plugins/plugin-name/requirements.txt

# Or install specific package
pip install package-name
```

### Plugin Conflicts

**Problem:** Multiple plugins conflict

**Solutions:**
1. Check for duplicate tool names
2. Disable conflicting plugin in settings
3. Check plugin load order

---

## UI Issues

### UI Not Loading

**Problem:** Blank page or JavaScript errors

**Solutions:**
```bash
# Check browser console for errors
# Chrome: F12 → Console

# Hard refresh
# Chrome: Ctrl+Shift+R
# Safari: Cmd+Shift+R

# Clear cache
rm -rf frontends/vanilla-js/dist
```

### Theme Not Applying

**Problem:** Theme changes don't take effect

**Solutions:**
1. Hard refresh browser
2. Check for CSS caching
3. Verify theme name in settings

```javascript
// Browser console
localStorage.setItem('otto-theme', 'cyberpunk');
location.reload();
```

### WebSocket Disconnections

**Problem:** Real-time updates stop working

**Solutions:**
1. Check network connectivity
2. Verify WebSocket URL is correct
3. Check for proxy/firewall blocking WS

```javascript
// Test WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onopen = () => console.log('Connected');
ws.onerror = (e) => console.log('Error:', e);
```

---

## Database Issues

### ChromaDB Errors

**Problem:** Vector database errors

**Solutions:**
```bash
# Reset ChromaDB
rm -rf data/chroma

# Or repair
python -c "from src.memory.chroma_manager import ChromaManager; ChromaManager().repair()"
```

### Data Corruption

**Problem:** Corrupted conversation data

**Solutions:**
```bash
# Backup current data
cp -r data data.backup

# Reset specific data
rm -rf data/conversations
rm -rf data/chroma

# Restart server
python run.py
```

---

## Performance Issues

### Slow Responses

**Checklist:**
1. Check API latency:
   ```bash
   curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/health
   ```
2. Monitor memory: `htop` or Activity Monitor
3. Check task queue - too many pending tasks
4. Reduce context length in settings

### High CPU Usage

**Solutions:**
```bash
# Check worker processes
ps aux | grep python

# Limit concurrent tasks
export MAX_CONCURRENT_TASKS=2

# Reduce embedding operations
export EMBEDDING_BATCH_SIZE=100
```

### High Memory Usage

**Solutions:**
```bash
# Limit conversation history length
curl -X PUT http://localhost:8000/api/settings \
  -d '{"max_context_messages": 20}'

# Clear old data
python -c "from src.utils.cleanup import cleanup_old_data; cleanup_old_data(days=30)"
```

---

## Error Messages Reference

| Error | Meaning | Solution |
|-------|---------|----------|
| `ECONNREFUSED` | Server not running | Start server |
| `ETIMEDOUT` | Network timeout | Check connectivity |
| `ENOMEM` | Out of memory | Increase RAM or reduce load |
| `ENOENT` | File not found | Check file paths |
| `EPERM` | Permission denied | Check file permissions |
| `SQLITE_CORRUPT` | DB corruption | Reset database |

---

## Getting Help

### Logs

```bash
# View recent logs
tail -100 logs/otto.log

# Search for errors
grep -i error logs/otto.log

# Watch logs in real-time
tail -f logs/otto.log
```

### Debug Mode

```bash
# Run with debug output
DEBUG=true python run.py

# Or set in .env
DEBUG=true
LOG_LEVEL=DEBUG
```

### Community Support

- GitHub Issues: [Report bugs](https://github.com/RhythrosaLabs/otto-chat/issues)
- Discussions: [Ask questions](https://github.com/RhythrosaLabs/otto-chat/discussions)
- Wiki: [Documentation](https://github.com/RhythrosaLabs/otto-chat/wiki)
