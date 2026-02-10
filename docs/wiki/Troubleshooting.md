# Troubleshooting

Common issues and their solutions.

## Server Issues

### Server Won't Start

**Symptoms:** Error when running `python run.py`

**Solutions:**

1. **Check Python version**
   ```bash
   python --version
   # Should be 3.11+
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Check .env file**
   ```bash
   cat .env
   # Ensure ANTHROPIC_API_KEY is set
   ```

4. **Check port availability**
   ```bash
   lsof -i :8000
   # Kill existing process if needed:
   lsof -ti:8000 | xargs kill -9
   ```

### Port Already in Use

```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
python -m uvicorn src.api.main:app --port 8001
```

### "Module Not Found" Errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

## API Key Issues

### "Anthropic API Key Required"

1. Get key from [Anthropic Console](https://console.anthropic.com/settings/keys)
2. Add to `.env`:
   ```env
   ANTHROPIC_API_KEY=sk-ant-...
   ```
3. Restart server

### "Invalid API Key"

- Check for extra spaces or quotes
- Verify key hasn't expired
- Test directly:
  ```bash
  curl https://api.anthropic.com/v1/messages \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01"
  ```

### Replicate Token Issues

Test token:
```bash
curl -H "Authorization: Token $REPLICATE_API_TOKEN" \
  https://api.replicate.com/v1/account
```

---

## Image Generation Issues

### Images Not Generating

1. **Check Replicate token**
   - Verify `REPLICATE_API_TOKEN` in `.env`
   - Check token balance at [replicate.com](https://replicate.com)

2. **Check model availability**
   - Some models may be temporarily unavailable
   - Try a different model (e.g., switch from Flux Pro to SDXL)

3. **Check error messages**
   - Look at server logs for detailed errors
   - API rate limits may apply

### Wrong Image Size/Aspect Ratio

Specify explicitly:
```
"Generate a portrait image (2:3) of a sunset"
"Create a landscape banner at 1920x1080"
```

### Image Quality Issues

- Use Flux Pro 1.1 for highest quality
- Enable upscaling for larger images
- Add style keywords like "high quality, detailed, professional"

---

## Printify Issues

### "Cannot Connect to Printify"

1. Verify API token at [Printify](https://printify.com/app/settings/api)
2. Check shop ID is correct
3. Test connection in Settings

### "Product Not Found"

- Blueprints change - run `get_blueprints` to get current options
- Some products are region-specific
- Check product is available for your shop

### Image Upload Fails

- Ensure image URL is publicly accessible
- Image must be PNG or JPEG
- Minimum resolution varies by product (usually 150 DPI)

---

## Plugin Issues

### Plugin Not Discovered

1. Check plugin directory structure:
   ```
   plugins/
   └── my_plugin/
       ├── manifest.yaml
       └── main.py
   ```

2. Validate manifest.yaml syntax
3. Click "Discover" in Settings → Plugins

### Plugin Won't Enable

1. Check for import errors in main.py
2. Verify all dependencies are installed
3. Check server logs for error details

### Plugin Tools Not Working

1. Verify tool is listed in manifest `provides`
2. Check method signature matches manifest
3. Ensure async/await is used correctly

---

## UI Issues

### Interface Not Loading

1. Clear browser cache
2. Check browser console for errors (F12)
3. Verify server is running
4. Try incognito/private window

### Theme Not Applying

1. Clear browser cache
2. Check localStorage:
   ```javascript
   localStorage.getItem('otto-theme')
   ```
3. Reset to default:
   ```javascript
   localStorage.removeItem('otto-theme')
   ```

### Keyboard Shortcuts Not Working

- Ensure focus is on the chat area
- Check for conflicting browser extensions
- Some shortcuts may conflict with OS shortcuts

---

## Performance Issues

### Slow Responses

1. Check network connection
2. Reduce concurrent tasks
3. Use simpler prompts for faster processing
4. Check API rate limits

### High Memory Usage

1. Clear completed tasks from queue
2. Close unused browser tabs
3. Restart server periodically for long-running instances

### File Storage Full

```bash
# Check storage usage
du -sh data/files/

# Clean up old files
find data/files/ -type f -mtime +30 -delete
```

---

## Docker Issues

### Container Won't Start

```bash
# Check logs
docker-compose logs otto

# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

### Volume Permissions

```bash
# Fix permissions
chmod -R 755 data/
```

---

## Getting Help

### Collect Debug Information

```bash
# System info
python --version
pip list | grep -E "fastapi|anthropic|pydantic"

# Server logs
tail -100 logs/otto.log

# Check config
cat .env | grep -v KEY | grep -v TOKEN
```

### Contact Support

1. Check existing [GitHub Issues](https://github.com/RhythrosaLabs/otto-chat/issues)
2. Create new issue with:
   - Otto version
   - Python version
   - OS
   - Error messages
   - Steps to reproduce

---

## Common Error Codes

| Error | Meaning | Solution |
|-------|---------|----------|
| `ANTHROPIC_ERROR` | Claude API issue | Check API key, quota |
| `REPLICATE_ERROR` | Image gen failed | Check token, try different model |
| `PRINTIFY_401` | Auth failed | Refresh Printify token |
| `RATE_LIMITED` | Too many requests | Wait and retry |
| `TIMEOUT` | Request took too long | Retry with simpler task |
| `FILE_NOT_FOUND` | Missing file | Check file path |
| `VALIDATION_ERROR` | Bad input | Check request format |
