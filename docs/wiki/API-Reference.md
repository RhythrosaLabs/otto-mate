# API Reference

Complete REST API documentation for Otto Chat.

---

## Overview

| Base URL | `http://localhost:8000` |
|----------|-------------------------|
| **Format** | JSON |
| **Authentication** | Session-based (API keys coming soon) |
| **Rate Limits** | 60 req/min (chat), 100 req/min (files) |

### Response Format

All responses follow this structure:

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

Error responses:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { ... }
  }
}
```

---

## Chat API

### Send Message

Send a message to Otto and receive an AI response.

```http
POST /chat
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "Generate an image of a sunset over mountains",
  "session_id": "optional-session-id",
  "stream": false,
  "context": {
    "previous_messages": [],
    "preferences": {
      "image_model": "flux-pro-1.1",
      "aspect_ratio": "landscape"
    }
  }
}
```

**Response:**
```json
{
  "response": "I've generated a beautiful sunset image over mountains...",
  "type": "success",
  "session_id": "sess_abc123",
  "plan": {
    "id": "plan_xyz789",
    "steps": [
      {
        "id": 1,
        "name": "Generate image",
        "tool": "generate_image_flux_pro",
        "status": "completed"
      },
      {
        "id": 2,
        "name": "Save to storage",
        "tool": "save_generated_image",
        "status": "completed"
      }
    ],
    "current_step": 2,
    "completed": true,
    "started_at": "2026-02-09T12:00:00Z",
    "completed_at": "2026-02-09T12:00:15Z"
  },
  "results": [
    {
      "step_id": 1,
      "tool": "generate_image_flux_pro",
      "success": true,
      "data": {
        "url": "https://replicate.delivery/...",
        "width": 1216,
        "height": 832,
        "model": "flux-pro-1.1"
      }
    },
    {
      "step_id": 2,
      "tool": "save_generated_image",
      "success": true,
      "data": {
        "file_id": "file_img123",
        "local_url": "/files/file_img123"
      }
    }
  ],
  "attachments": [
    {
      "type": "image",
      "url": "/files/file_img123",
      "thumbnail": "/files/file_img123?size=thumb"
    }
  ]
}
```

### Stream Chat (SSE)

Stream responses in real-time using Server-Sent Events.

```http
POST /chat/stream
Content-Type: application/json
Accept: text/event-stream
```

**Request Body:**
```json
{
  "message": "Write a long blog post about AI",
  "session_id": "optional"
}
```

**Event Stream:**
```
event: start
data: {"session_id": "sess_abc123", "plan_id": "plan_xyz789"}

event: step_start
data: {"step_id": 1, "name": "Generate content", "tool": "generate_text"}

event: token
data: {"content": "Artificial "}

event: token
data: {"content": "Intelligence "}

event: token
data: {"content": "is transforming..."}

event: step_complete
data: {"step_id": 1, "success": true}

event: complete
data: {"response": "...", "results": [...]}
```

### Voice Input

Send audio for transcription and processing.

```http
POST /voice
Content-Type: multipart/form-data
```

**Form Data:**
| Field | Type | Description |
|-------|------|-------------|
| `audio` | file | Audio file (WAV, MP3, M4A) |
| `session_id` | string | Optional session ID |
| `language` | string | Language code (default: "en") |

**Response:**
```json
{
  "transcription": "Generate an image of a cat",
  "confidence": 0.95,
  "response": "I'll generate a cat image...",
  "results": [...]
}
```

---

## Files API

### List Files

```http
GET /api/files
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `category` | string | all | Filter by category |
| `limit` | int | 50 | Max results |
| `offset` | int | 0 | Pagination offset |
| `sort` | string | created_desc | Sort order |
| `search` | string | | Search in filename |

**Categories:** `images`, `videos`, `audio`, `documents`, `3d`, `other`

**Response:**
```json
{
  "files": [
    {
      "id": "file_abc123",
      "filename": "sunset_mountains.png",
      "original_filename": "sunset_mountains.png",
      "category": "images",
      "mime_type": "image/png",
      "size": 2456789,
      "width": 1216,
      "height": 832,
      "url": "/files/file_abc123",
      "thumbnail_url": "/files/file_abc123?size=thumb",
      "created_at": "2026-02-09T12:00:00Z",
      "metadata": {
        "model": "flux-pro-1.1",
        "prompt": "sunset over mountains",
        "aspect_ratio": "landscape"
      },
      "tags": ["sunset", "mountains", "landscape"]
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

### Upload File

```http
POST /api/files/upload
Content-Type: multipart/form-data
```

**Form Data:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | File to upload |
| `category` | string | No | Override auto-detection |
| `tags` | string | No | Comma-separated tags |
| `description` | string | No | File description |

**Response:**
```json
{
  "success": true,
  "file": {
    "id": "file_xyz789",
    "filename": "logo.png",
    "url": "/files/file_xyz789",
    "size": 45678,
    "category": "images"
  }
}
```

### Get File

```http
GET /files/{file_id}
```

Returns the actual file content with appropriate Content-Type header.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `size` | string | `thumb` (256px), `medium` (512px), `large` (1024px) |
| `download` | bool | Force download (Content-Disposition: attachment) |

### Get File Info

```http
GET /api/files/{file_id}
```

**Response:**
```json
{
  "id": "file_abc123",
  "filename": "sunset_mountains.png",
  "category": "images",
  "size": 2456789,
  "url": "/files/file_abc123",
  "created_at": "2026-02-09T12:00:00Z",
  "metadata": {...},
  "tags": ["sunset", "mountains"]
}
```

### Update File

```http
PATCH /api/files/{file_id}
Content-Type: application/json
```

**Request Body:**
```json
{
  "filename": "new_name.png",
  "tags": ["updated", "tags"],
  "description": "Updated description"
}
```

### Delete File

```http
DELETE /api/files/{file_id}
```

### Download All Files

Download all files as a ZIP archive.

```http
GET /api/files/download-all
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `category` | string | Filter by category |
| `format` | string | `zip` (default) |

Returns a ZIP file organized by category.

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
      "description": "Scrape web pages and extract content",
      "type": "tool",
      "enabled": true,
      "author": "Otto Team",
      "tools": [
        {
          "name": "scrape_page",
          "description": "Scrape a webpage"
        },
        {
          "name": "extract_links",
          "description": "Extract all links"
        }
      ],
      "settings_schema": [
        {
          "name": "timeout",
          "type": "number",
          "default": 30
        }
      ]
    }
  ],
  "total": 3
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

**Response:**
```json
{
  "success": true,
  "plugin": {
    "id": "web_scraper",
    "enabled": true
  }
}
```

### Disable Plugin

```http
POST /api/plugins/{plugin_id}/disable
```

### Update Plugin Settings

```http
POST /api/plugins/{plugin_id}/settings
Content-Type: application/json
```

**Request Body:**
```json
{
  "api_key": "sk-...",
  "timeout": 60,
  "mode": "quality"
}
```

### Discover New Plugins

Scan the plugins directory for new plugins.

```http
POST /api/plugins/discover
```

**Response:**
```json
{
  "success": true,
  "discovered": ["new_plugin_1", "new_plugin_2"],
  "total": 5
}
```

### Reload All Plugins

```http
POST /api/plugins/reload
```

### Get All Plugin Tools

```http
GET /api/plugins/tools/all
```

**Response:**
```json
{
  "tools": [
    {
      "plugin_id": "web_scraper",
      "name": "scrape_page",
      "description": "Scrape a webpage",
      "parameters": [
        {
          "name": "url",
          "type": "string",
          "required": true
        }
      ]
    }
  ]
}
```

---

## Task Queue API

### List Tasks

```http
GET /api/tasks
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | all | Filter: pending, running, completed, failed |
| `priority` | string | all | Filter: low, normal, high, urgent |
| `limit` | int | 50 | Max results |

**Response:**
```json
{
  "tasks": [
    {
      "id": "task_abc123",
      "title": "Generate product images",
      "status": "running",
      "progress": 45,
      "progress_message": "Generating image 2 of 5...",
      "priority": "normal",
      "created_at": "2026-02-09T12:00:00Z",
      "started_at": "2026-02-09T12:00:05Z",
      "estimated_completion": "2026-02-09T12:01:00Z"
    }
  ],
  "total": 15,
  "by_status": {
    "pending": 3,
    "running": 1,
    "completed": 10,
    "failed": 1
  }
}
```

### Get Task

```http
GET /api/tasks/{task_id}
```

**Response:**
```json
{
  "id": "task_abc123",
  "title": "Generate product images",
  "description": "Create 5 beach-themed product images",
  "status": "running",
  "progress": 45,
  "steps": [
    {"name": "Generate image 1", "status": "completed"},
    {"name": "Generate image 2", "status": "running"},
    {"name": "Generate image 3", "status": "pending"}
  ],
  "result": null,
  "error": null,
  "created_at": "2026-02-09T12:00:00Z",
  "started_at": "2026-02-09T12:00:05Z"
}
```

### Create Task

```http
POST /api/tasks
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "Generate 5 product images",
  "priority": "high"
}
```

### Schedule Task

```http
POST /api/tasks/schedule
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "Generate weekly sales report",
  "scheduled_for": "2026-02-10T09:00:00Z",
  "priority": "normal",
  "recurring": "weekly",
  "recurring_options": {
    "day_of_week": "monday",
    "time": "09:00",
    "timezone": "America/New_York"
  }
}
```

### Cancel Task

```http
POST /api/tasks/{task_id}/cancel
```

### Retry Task

```http
POST /api/tasks/{task_id}/retry
```

### Clear Completed Tasks

```http
DELETE /api/tasks/completed
```

---

## Settings API

### Get Settings

```http
GET /api/settings
```

**Response:**
```json
{
  "defaultModel": "claude-opus-4",
  "imageModel": "flux-pro-1.1",
  "videoModel": "runway-gen3",
  "theme": "classic",
  "autoSave": true,
  "showToolCalls": false,
  "voiceEnabled": true,
  "notifications": true
}
```

### Update Settings

```http
POST /api/settings
Content-Type: application/json
```

**Request Body:**
```json
{
  "theme": "midnight",
  "imageModel": "sdxl",
  "autoSave": false
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
  "anthropic": {
    "connected": true,
    "model": "claude-opus-4-20260101",
    "last_checked": "2026-02-09T12:00:00Z"
  },
  "replicate": {
    "connected": true,
    "credits_remaining": 500.00
  },
  "printify": {
    "connected": true,
    "shop_id": "12345678",
    "shop_name": "My Store"
  },
  "shopify": {
    "connected": false,
    "error": "Access token expired"
  },
  "serper": {
    "connected": true,
    "credits_remaining": 2500
  }
}
```

### Test Connection

```http
POST /api/connections/{service}/test
Content-Type: application/json
```

**Request Body:**
```json
{
  "api_key": "new-api-key"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Connection successful",
  "details": {
    "account": "user@example.com",
    "plan": "pro"
  }
}
```

### Update Connection

```http
PUT /api/connections/{service}
Content-Type: application/json
```

**Request Body:**
```json
{
  "api_key": "new-api-key",
  "shop_id": "12345678"
}
```

---

## Tools API

### List All Tools

```http
GET /tools
```

**Response:**
```json
{
  "tools": [
    {
      "name": "generate_image_flux_pro",
      "description": "Generate high-quality images using Flux Pro 1.1",
      "category": "image_generation",
      "parameters": [
        {
          "name": "prompt",
          "type": "string",
          "required": true,
          "description": "The image generation prompt"
        },
        {
          "name": "aspect_ratio",
          "type": "string",
          "required": false,
          "default": "1:1",
          "options": ["1:1", "16:9", "9:16", "4:3", "3:4"]
        }
      ]
    }
  ],
  "total": 100,
  "by_category": {
    "image_generation": 15,
    "video_generation": 10,
    "audio": 8,
    "printify": 15,
    "shopify": 12,
    "research": 8,
    "browser": 8,
    "content": 7,
    "file_storage": 7,
    "plugin": 10
  }
}
```

### Execute Tool Directly

```http
POST /api/tools/{tool_name}
Content-Type: application/json
```

**Request Body:**
```json
{
  "prompt": "A sunset over mountains",
  "aspect_ratio": "16:9"
}
```

**Response:**
```json
{
  "success": true,
  "tool": "generate_image_flux_pro",
  "execution_time": 12.5,
  "result": {
    "url": "https://...",
    "file_id": "file_abc123"
  }
}
```

---

## Health & System

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "uptime": 86400,
  "memory_usage": {
    "used_mb": 512,
    "total_mb": 8192
  },
  "services": {
    "anthropic": "connected",
    "replicate": "connected",
    "database": "connected"
  }
}
```

### System Info

```http
GET /api/system/info
```

**Response:**
```json
{
  "version": "2.0.0",
  "python_version": "3.11.5",
  "platform": "darwin",
  "tools_count": 100,
  "plugins_count": 3,
  "files_count": 1500,
  "storage_used_mb": 2500
}
```

---

## Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `AUTHENTICATION_REQUIRED` | 401 | Authentication needed |
| `FORBIDDEN` | 403 | Access denied |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMITED` | 429 | Too many requests |
| `TOOL_EXECUTION_FAILED` | 500 | Tool encountered error |
| `SERVICE_UNAVAILABLE` | 503 | External service down |
| `TIMEOUT` | 504 | Request timed out |

### Error Response Example

```json
{
  "success": false,
  "error": {
    "code": "TOOL_EXECUTION_FAILED",
    "message": "Failed to generate image: Rate limit exceeded",
    "details": {
      "tool": "generate_image_flux_pro",
      "retry_after": 60
    }
  }
}
```

---

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/chat` | 60 | 1 minute |
| `/voice` | 30 | 1 minute |
| `/api/files/*` | 100 | 1 minute |
| `/api/tools/*` | 30 | 1 minute |
| `/api/plugins/*` | 60 | 1 minute |

### Rate Limit Headers

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1707480000
```

---

## WebSocket Events

### Connect

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

### Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `connected` | server → client | Connection established |
| `task_started` | server → client | Task execution started |
| `task_progress` | server → client | Progress update |
| `task_completed` | server → client | Task finished |
| `task_failed` | server → client | Task error |

### Event Format

```json
{
  "event": "task_progress",
  "data": {
    "task_id": "task_abc123",
    "progress": 45,
    "message": "Generating image 2 of 5..."
  },
  "timestamp": "2026-02-09T12:00:30Z"
}
```
