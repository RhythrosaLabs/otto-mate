# API Reference

Otto Chat provides a REST API for integration with external systems.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently uses session-based authentication. API key authentication coming soon.

---

## Chat API

### Send Message

Send a message to Otto and receive AI response.

```http
POST /chat
Content-Type: application/json

{
  "message": "Generate an image of a sunset",
  "session_id": "optional-session-id"
}
```

**Response:**

```json
{
  "response": "I've generated your sunset image...",
  "type": "success",
  "session_id": "abc123",
  "plan": {
    "steps": ["Generate image", "Save to storage"],
    "current_step": 2,
    "completed": true
  },
  "results": [
    {
      "tool": "generate_image_flux_pro",
      "success": true,
      "data": {
        "url": "https://...",
        "file_id": "img_123"
      }
    }
  ]
}
```

### Voice Input

Send audio for transcription and processing.

```http
POST /voice
Content-Type: multipart/form-data

audio: <audio file>
```

---

## Files API

### List Files

```http
GET /api/files?category=images&limit=50
```

**Response:**

```json
{
  "files": [
    {
      "id": "file_123",
      "filename": "sunset.png",
      "category": "images",
      "size": 245678,
      "created_at": "2026-02-09T12:00:00Z",
      "url": "/files/file_123"
    }
  ],
  "total": 150
}
```

### Upload File

```http
POST /api/files/upload
Content-Type: multipart/form-data

file: <file>
category: images
```

### Get File

```http
GET /files/{file_id}
```

### Delete File

```http
DELETE /api/files/{file_id}
```

### Download All as ZIP

```http
GET /api/files/download-all
```

---

## Plugins API

### List Plugins

```http
GET /api/plugins
```

**Response:**

```json
{
  "plugins": [
    {
      "id": "web_scraper",
      "name": "Web Scraper",
      "version": "1.0.0",
      "enabled": true,
      "type": "tool"
    }
  ]
}
```

### Get Plugin Details

```http
GET /api/plugins/{plugin_id}
```

### Enable Plugin

```http
POST /api/plugins/{plugin_id}/enable
```

### Disable Plugin

```http
POST /api/plugins/{plugin_id}/disable
```

### Update Plugin Settings

```http
POST /api/plugins/{plugin_id}/settings
Content-Type: application/json

{
  "api_key": "...",
  "other_setting": "value"
}
```

### Discover New Plugins

```http
POST /api/plugins/discover
```

### Reload All Plugins

```http
POST /api/plugins/reload
```

---

## Task Queue API

### List Tasks

```http
GET /api/tasks
```

**Response:**

```json
{
  "tasks": [
    {
      "id": "task_123",
      "title": "Generate product images",
      "status": "running",
      "progress": 45,
      "created_at": "2026-02-09T12:00:00Z"
    }
  ]
}
```

### Get Task Status

```http
GET /api/tasks/{task_id}
```

### Cancel Task

```http
POST /api/tasks/{task_id}/cancel
```

### Schedule Task

```http
POST /api/tasks/schedule
Content-Type: application/json

{
  "message": "Create weekly report",
  "scheduled_for": "2026-02-10T09:00:00Z",
  "priority": "high",
  "recurring": "weekly"
}
```

---

## Settings API

### Get Settings

```http
GET /api/settings
```

### Update Settings

```http
POST /api/settings
Content-Type: application/json

{
  "defaultModel": "claude-opus-4",
  "imageModel": "flux-pro-1.1",
  "autoSave": true
}
```

---

## Connections API

### Get Connection Status

```http
GET /api/connections/status
```

**Response:**

```json
{
  "anthropic": { "connected": true },
  "replicate": { "connected": true },
  "printify": { "connected": false, "error": "No API key" },
  "shopify": { "connected": false }
}
```

### Test Connection

```http
POST /api/connections/{service}/test
Content-Type: application/json

{
  "api_key": "..."
}
```

---

## Tools API

### List Available Tools

```http
GET /tools
```

**Response:**

```json
{
  "tools": [
    {
      "name": "generate_image_flux_pro",
      "description": "Generate image using Flux Pro 1.1",
      "parameters": [
        {
          "name": "prompt",
          "type": "string",
          "required": true
        }
      ]
    }
  ]
}
```

---

## Health Check

### Server Health

```http
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "version": "2.0.0",
  "uptime": 3600
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message here",
  "error_code": "ERROR_CODE",
  "tool": "tool_name_if_applicable"
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Invalid request parameters |
| `TOOL_EXECUTION_FAILED` | Tool encountered an error |
| `RATE_LIMITED` | Too many requests |
| `NOT_FOUND` | Resource not found |
| `UNAUTHORIZED` | Authentication required |
| `SERVICE_UNAVAILABLE` | External service down |

---

## Rate Limits

- **Chat:** 60 requests/minute
- **Files:** 100 requests/minute
- **Tools:** 30 requests/minute

Rate limit headers:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1707480000
```

---

## Webhooks (Coming Soon)

Register webhooks to receive real-time updates:

```http
POST /api/webhooks
Content-Type: application/json

{
  "url": "https://your-server.com/webhook",
  "events": ["task.completed", "file.created"]
}
```
