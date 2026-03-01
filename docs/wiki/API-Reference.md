# API Reference

Complete reference for all REST and WebSocket endpoints in Otto Chat.

**Base URL:** `http://localhost:8000`

---

## Authentication

Otto supports JWT token authentication:

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "..."}'

# Use token
curl http://localhost:8000/api/settings \
  -H "Authorization: Bearer <token>"
```

API key authentication is also supported via the `X-API-Key` header (configurable).

---

## Core Endpoints

### Chat

#### `POST /chat`
Send a chat message and receive a response.

**Request:**
```json
{
  "message": "Generate a sunset beach image",
  "session_id": "optional-session-id",
  "images": [],
  "stream": false
}
```

**Response:**
```json
{
  "response": "I've generated your sunset beach image...",
  "type": "success",
  "session_id": "abc123",
  "plan": {
    "steps": ["Generate image", "Save to storage"],
    "current_step": 2,
    "completed": true
  },
  "results": [
    {
      "tool": "generate_image",
      "success": true,
      "data": {
        "url": "https://...",
        "file_id": "img_123"
      }
    }
  ]
}
```

#### `POST /chat/stream`
Stream a chat response via Server-Sent Events (SSE).

**Request:** Same as `/chat` with `"stream": true`

**Response:** SSE stream with `data: {...}` events.

#### `GET /api/chat/history/{session_id}`
Retrieve chat history for a session.

#### `DELETE /api/chat/history/{session_id}`
Clear chat history for a session.

---

### Voice

#### `POST /voice`
Full voice pipeline: Speech → Text → AI → Text → Speech.

**Request:** `multipart/form-data` with `audio` file.

**Response:**
```json
{
  "transcription": "What's the weather like?",
  "response": "...",
  "audio_url": "/api/files/audio_response.mp3"
}
```

#### `POST /transcribe`
Speech-to-text only.

**Request:** `multipart/form-data` with `audio` file.

---

### Tools & Capabilities

#### `GET /tools`
List all available tools.

**Response:**
```json
{
  "tools": [
    {
      "name": "generate_image",
      "category": "image",
      "description": "Generate an AI image",
      "parameters": {...}
    }
  ],
  "count": 100
}
```

#### `GET /capabilities`
Get Otto's current capabilities and enabled features.

---

### Health

#### `GET /health`
Basic health check.

```json
{
  "status": "healthy",
  "timestamp": "2026-03-01T12:00:00",
  "version": "1.0.0",
  "uptime": "2h 15m",
  "services": {
    "anthropic": true,
    "replicate": true,
    "printify": true
  }
}
```

#### `GET /health/detailed`
Comprehensive health check with all component statuses, resource usage, and diagnostics.

---

### File Upload

#### `POST /upload`
Upload a file (convenience alias for `/api/files/upload`).

**Request:** `multipart/form-data` with `file` and optional `category`.

---

### Workflow Execution

#### `POST /workflow`
Execute a workflow by name or definition.

```json
{
  "workflow": "product_launch",
  "params": {
    "product_name": "Sunset Collection",
    "designs": 5
  }
}
```

---

## WebSocket

### `WS /ws`
Real-time bidirectional communication.

**Client → Server Messages:**
```json
{"type": "chat", "message": "Hello"}
{"type": "voice", "audio": "<base64>"}
{"type": "command", "command": "/help"}
{"type": "ping"}
```

**Server → Client Messages:**
```json
{"type": "response", "message": "..."}
{"type": "progress", "step": 1, "total": 3, "message": "Generating image..."}
{"type": "typing", "active": true}
{"type": "error", "message": "..."}
{"type": "pong"}
```

---

## Resource APIs

### Settings — `/api/settings`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/settings` | Get all settings |
| PUT | `/api/settings` | Update settings |
| GET | `/api/settings/{key}` | Get specific setting |

### Files — `/api/files`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/files` | List files (with filters) |
| POST | `/api/files/upload` | Upload file |
| GET | `/api/files/{id}` | Get file by ID |
| DELETE | `/api/files/{id}` | Delete file |
| GET | `/api/files/download/{id}` | Download file |
| GET | `/api/files/tree` | Project file tree |
| GET | `/api/files/content` | Read file content |
| GET | `/api/files/stats` | Storage statistics |

### Connections — `/api/connections`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/connections/status` | Check all connections |
| GET | `/api/connections/test/{service}` | Test specific service |

### Agents — `/api/agents`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/agents` | List all agents |
| GET | `/api/agents/{id}` | Get agent details |
| POST | `/api/agents` | Create agent |
| PUT | `/api/agents/{id}` | Update agent |
| DELETE | `/api/agents/{id}` | Delete agent |

### Models — `/api/models`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/models` | List available AI models |
| GET | `/api/models/{id}` | Get model details |
| POST | `/api/models/select` | Select active model |

### Workflows — `/api/workflows`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/workflows` | List workflows |
| POST | `/api/workflows` | Create workflow |
| GET | `/api/workflows/{id}` | Get workflow |
| PUT | `/api/workflows/{id}` | Update workflow |
| DELETE | `/api/workflows/{id}` | Delete workflow |
| POST | `/api/workflows/{id}/run` | Execute workflow |

### Business — `/api/business`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/business/status` | Business operations status |
| POST | `/api/business/execute` | Run business operation |
| GET | `/api/business/kpis` | Get business KPIs |

### Projects — `/api/projects`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/projects` | List projects |
| POST | `/api/projects` | Create project |
| GET | `/api/projects/{id}` | Get project |
| PUT | `/api/projects/{id}` | Update project |
| DELETE | `/api/projects/{id}` | Delete project |

### Skills — `/api/skills`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/skills` | List available skills |
| GET | `/api/skills/{name}` | Get skill details |

### Plugins — `/api/plugins`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/plugins` | List installed plugins |
| GET | `/api/plugins/{name}` | Get plugin details |
| POST | `/api/plugins/{name}/enable` | Enable plugin |
| POST | `/api/plugins/{name}/disable` | Disable plugin |
| PUT | `/api/plugins/{name}/settings` | Update plugin settings |
| POST | `/api/plugins/reload` | Reload all plugins |

### Tasks — `/api/tasks`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tasks` | List tasks |
| POST | `/api/tasks` | Create task |
| GET | `/api/tasks/{id}` | Get task |
| DELETE | `/api/tasks/{id}` | Cancel/delete task |
| GET | `/api/tasks/background` | List background tasks |

### Scheduler — `/api/scheduler`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/scheduler/jobs` | List scheduled jobs |
| POST | `/api/scheduler/jobs` | Create scheduled job |
| DELETE | `/api/scheduler/jobs/{id}` | Remove job |
| GET | `/api/scheduler/status` | Scheduler status |

### Browser — `/api/browser`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/browser/navigate` | Navigate to URL |
| POST | `/api/browser/screenshot` | Take screenshot |
| POST | `/api/browser/click` | Click element |
| POST | `/api/browser/type` | Type text |
| POST | `/api/browser/extract` | Extract data |
| GET | `/api/browser/proxy` | Iframe proxy |

### Intelligence — `/api/intelligence`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/intelligence/stats` | Intelligence metrics |
| GET | `/api/intelligence/insights` | Generated insights |

### Creative Platform — `/api/creative`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/creative/projects` | List creative projects |
| POST | `/api/creative/projects` | Create creative project |
| GET | `/api/creative/projects/{id}/status` | Project status |

### Conversations — `/api/conversations`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/conversations` | List conversations |
| GET | `/api/conversations/{id}` | Get conversation |
| DELETE | `/api/conversations/{id}` | Delete conversation |

### Profile — `/api/profile`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/profile` | Get user profile |
| PUT | `/api/profile` | Update profile |

### Brand — `/api/brand`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/brand` | Get brand settings |
| PUT | `/api/brand` | Update brand settings |

### Social — `/api/social`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/social/post` | Create social media post |
| GET | `/api/social/accounts` | List connected accounts |

### Email — `/api/email`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/email/send` | Send email |
| POST | `/api/email/campaign` | Create email campaign |

### Auth — `/api/auth`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/register` | Register |
| POST | `/api/auth/refresh` | Refresh token |
| GET | `/api/auth/me` | Current user |

### Setup — `/api/setup`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/setup/status` | Setup completion status |
| POST | `/api/setup/complete` | Mark setup complete |

### AI Editing

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ai/edit` | AI file editing |
| POST | `/api/ai/review` | AI code review |
| POST | `/api/ai/explain` | AI code explanation |
| POST | `/api/ai/refactor` | AI refactoring |
| POST | `/api/ai/fix` | AI bug fixing |
| POST | `/api/media/edit` | Universal media editing |
| GET | `/api/media/capabilities` | Media capabilities |

### Memory

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/memory/stats` | Memory usage statistics |

### Import

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/import/contacts` | Import contacts (CSV/Excel) |
| POST | `/api/import/schedule` | Import schedule (CSV/Excel) |

---

## Messaging Channel APIs

### WhatsApp — `/api/whatsapp`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/whatsapp/webhook` | Incoming message webhook |
| GET | `/api/whatsapp/webhook` | Webhook verification |
| POST | `/api/whatsapp/send` | Send message |

### Telegram — `/api/telegram`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/telegram/webhook` | Incoming update webhook |
| POST | `/api/telegram/send` | Send message |
| GET | `/api/telegram/status` | Bot status |

### Discord — `/api/discord`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/discord/send` | Send message |
| GET | `/api/discord/status` | Bot status |

### Gateway — `/gateway`

| Method | Endpoint | Description |
|--------|----------|-------------|
| WS | `/gateway/ws` | Gateway WebSocket |
| POST | `/gateway/pair` | Pair device |
| GET | `/gateway/devices` | List paired devices |

---

## Error Format

All errors follow a consistent format:

```json
{
  "detail": "Human-readable error message",
  "error_code": "TOOL_EXECUTION_FAILED",
  "tool": "generate_image",
  "timestamp": "2026-03-01T12:00:00"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|------------|-------------|
| `VALIDATION_ERROR` | 422 | Invalid input |
| `TOOL_EXECUTION_FAILED` | 500 | Tool failed to execute |
| `SERVICE_UNAVAILABLE` | 503 | External service down |
| `RATE_LIMITED` | 429 | Too many requests |
| `UNAUTHORIZED` | 401 | Missing/invalid auth |
| `NOT_FOUND` | 404 | Resource not found |
