# Architecture

Otto Chat follows a modular, service-oriented architecture built on FastAPI with multi-agent AI orchestration.

---

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENTS                               │
│  Web UI  │  Telegram  │  Discord  │  Slack  │  WhatsApp     │
│  REST    │  WebSocket │  CLI      │  Voice  │  Gateway      │
└─────────┬───────────┬──────────┬──────────┬────────────────┘
          │           │          │          │
          ▼           ▼          ▼          ▼
┌─────────────────────────────────────────────────────────────┐
│                    API LAYER (FastAPI)                        │
│  30+ Routers  │  WebSocket Gateway  │  SSE Streaming         │
│  JWT Auth     │  CORS               │  Rate Limiting         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                 ORCHESTRATION LAYER                           │
│  Agent Orchestrator  │  Super Planning Agent                 │
│  Execution Agent     │  Enhanced Intelligence                │
│  Unified Agent System (multi-agent crews)                    │
│  Autonomous Orchestrator (business operations)               │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  TOOL LAYER  │ │ MEMORY LAYER │ │ INTELLIGENCE │
│  40 modules  │ │  ChromaDB    │ │  Reasoning   │
│  100+ tools  │ │  Context     │ │  Self-Improve│
│  Tool Router │ │  Sessions    │ │  Proactive   │
└──────┬───────┘ └──────────────┘ └──────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                   EXTERNAL SERVICES                          │
│  Anthropic  │  OpenAI   │  Replicate  │  Printify           │
│  Shopify    │  Serper   │  SendGrid   │  ElevenLabs         │
│  Playwright │  Ollama   │  Telegram   │  Discord            │
└─────────────────────────────────────────────────────────────┘
```

---

## Module Map

### API Layer (`src/api/` — 34 modules)

The API layer provides REST and WebSocket endpoints. All routes are mounted via FastAPI routers in `main.py`.

| Module | Prefix | Responsibility |
|--------|--------|---------------|
| `main.py` | `/` | FastAPI app, lifespan, root routes, WebSocket |
| `settings.py` | `/api/settings` | Configuration management |
| `files.py` | `/api/files` | File upload, download, tree, content |
| `connections.py` | `/api/connections` | Service connection testing |
| `agents.py` | `/api/agents` | Agent CRUD and management |
| `models.py` | `/api/models` | AI model listing and selection |
| `workflows.py` | `/api/workflows` | Workflow CRUD and execution |
| `business.py` | `/api/business` | Autonomous business operations |
| `projects.py` | `/api/projects` | Project management |
| `skills.py` | `/api/skills` | Skill registry |
| `plugins.py` | `/api/plugins` | Plugin management |
| `extensions.py` | `/api/extensions` | Extension management |
| `conversations.py` | `/api/conversations` | Conversation CRUD |
| `tasks.py` | `/api/tasks` | Task queue management |
| `scheduler_routes.py` | `/api/scheduler` | Scheduled task management |
| `browser.py` | `/api/browser` | Browser automation |
| `intelligence.py` | `/api/intelligence` | Intelligence analytics |
| `creative_platform.py` | `/api/creative` | Creative project management |
| `integrations.py` | `/api/integrations` | Third-party integrations |
| `profile.py` | `/api/profile` | User profile |
| `brand.py` | `/api/brand` | Brand intelligence |
| `social.py` | `/api/social` | Social media management |
| `email.py` | `/api/email` | Email sending |
| `webhooks.py` | `/api/webhooks` | Webhook management |
| `auth.py` | `/api/auth` | JWT authentication |
| `setup.py` | `/api/setup` | First-run setup wizard |
| `ollama.py` | `/api/ollama` | Local Ollama models |
| `model_manager.py` | `/api/model-manager` | Model lifecycle |
| `gateway_ws.py` | `/gateway` | WebSocket gateway |
| `whatsapp.py` | `/api/whatsapp` | WhatsApp messaging |
| `telegram.py` | `/api/telegram` | Telegram bot |
| `discord.py` | `/api/discord` | Discord bot |
| `email_webhook.py` | `/api/email-webhook` | Inbound email |
| `session_manager.py` | `/api/sessions` | Session lifecycle |

### Core Layer (`src/core/` — 65 modules)

The core layer contains business logic, agent orchestration, and intelligence systems.

#### Agent Systems

| Module | Lines | Purpose |
|--------|-------|---------|
| `agent_orchestrator.py` | 1825 | Central brain — routes requests to tools or conversation, manages execution |
| `super_planning_agent.py` | — | Autonomous multi-step planning with context preservation |
| `execution_agent.py` | — | Step-by-step execution with dependency resolution |
| `unified_agent_system.py` | 793 | Multi-agent framework with roles, crews, and execution modes |
| `super_intelligent_chat.py` | 627 | Conversational interface with tool execution and memory |
| `enhanced_intelligence.py` | 354 | Advanced reasoning, proactive intelligence, self-improvement |
| `autonomous_orchestrator.py` | 723 | Fully autonomous business operations with KPI tracking |
| `enhanced_agent_delegation.py` | — | Specialized agent routing by domain |

#### Support Systems

| Module | Purpose |
|--------|---------|
| `tool_registry.py` | Dynamic tool discovery and registration |
| `memory_agent.py` | ChromaDB vector store for conversations and knowledge |
| `context_manager.py` | Conversation context management |
| `session_manager.py` | Session lifecycle management |
| `streaming_support.py` | SSE streaming for real-time responses |
| `slash_commands.py` | `/command` syntax processing |
| `voice.py` | Wake word detection and talk mode |

#### Intelligence Systems

| Module | Purpose |
|--------|---------|
| `advanced_reasoning.py` | Multi-strategy reasoning engine |
| `proactive_intelligence.py` | Anticipatory user need detection |
| `smart_tool_router.py` | Optimal tool selection and routing |
| `self_improvement_loop.py` | Learning from interaction outcomes |
| `intelligent_retry_system.py` | Smart retry with failure analysis |
| `error_recovery.py` | Graceful error recovery |
| `platform_intelligence.py` | Platform-level intelligence coordination |

#### Monitoring

| Module | Purpose |
|--------|---------|
| `agent_health_monitor.py` | Agent health tracking |
| `agent_analytics.py` | Performance analytics and metrics |
| `agent_communication.py` | Inter-agent message bus |

#### Business Systems

| Module | Purpose |
|--------|---------|
| `business_workflows.py` | Pre-built workflow templates (product launch, marketing, etc.) |
| `creative_platform.py` | Creative project management with state machine |
| `project_manager.py` | Project management with chat sessions |
| `modality_system.py` | Modality-first AI model selection |

#### Extensibility

| Module | Purpose |
|--------|---------|
| `plugin_system.py` | Plugin loading, lifecycle, and management |
| `skills.py` | Skill ecosystem with categories |
| `gateway.py` | WebSocket control plane for unified connectivity |
| `channel_manager.py` | Multi-channel lifecycle management |
| `ollama_client.py` | Local Ollama model support |

### Tool Layer (`src/tools/` — 40 modules)

Each tool module registers tools with the Tool Registry via decorators. See [Tools Reference](Tools-Reference) for details.

### Web Layer (`src/web/`)

Server-rendered HTML pages with modular CSS and JavaScript:

| Page | Purpose |
|------|---------|
| `chat.html` | Main chat interface (19K+ lines) |
| `settings.html` | Settings management |
| `files.html` | File browser |
| `agents.html` | Agent management |
| `workflows.html` | Workflow builder |
| `onboarding.html` | First-run setup wizard |

Static assets are organized in `static/`:
- **CSS**: `base.css`, `themes.css`, `layout.css`, `sidebar.css`, `chat.css`, `editor.css`, `modals.css`, `components.css`
- **JS**: `api.js`, `config.js`, `state.js`, `ui.js`, `utils.js`, `voice.js`

---

## Design Patterns

### 1. Modality-First Model Selection

Before selecting an AI model, Otto determines the **output modality** (text, image, video, audio, code, vision, 3D, data). This ensures the optimal model is always chosen:

```
User Request → Detect Modality → Select Best Model → Execute
                                    ↓
                              Priority Order:
                              1. Local models (Ollama)
                              2. Remote APIs (Anthropic, OpenAI)
                              3. Replicate (last resort)
```

### 2. Multi-Agent Pipeline

Complex tasks flow through a multi-agent pipeline:

```
User Message
    ↓
Agent Orchestrator (detect action vs question)
    ↓
Super Planning Agent (create execution plan)
    ↓
Execution Agent (run steps with dependency resolution)
    ↓
Tools (execute individual operations)
    ↓
Verification (validate results)
    ↓
Response (formatted result to user)
```

### 3. Plugin Architecture

Plugins are discovered and loaded dynamically from three locations:
1. `./plugins/` — Project-level plugins
2. `~/.otto/plugins/` — User-level plugins
3. Pip packages with entry points — System-level plugins

### 4. Gateway Architecture

The WebSocket gateway provides a unified control plane:

```
┌──────────┐  ┌──────────┐  ┌──────────┐
│  Web UI  │  │   CLI    │  │  Mobile  │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     └──────┬──────┘─────────────┘
            ▼
    ┌───────────────┐
    │   Gateway WS  │ ← Unified WebSocket
    │   /gateway    │    (device pairing,
    └───────┬───────┘     presence, routing)
            ▼
    ┌───────────────┐
    │  Orchestrator │
    └───────────────┘
```

### 5. Self-Improvement Loop

Otto learns from every interaction:

```
Interaction → Outcome Capture → Analysis → Pattern Update → Improved Future Responses
```

---

## Data Flow

### Chat Request Flow

```
1. Client sends POST /chat with {message, session_id}
2. API layer validates input (Pydantic)
3. Session manager retrieves/creates session
4. Agent Orchestrator classifies request (action vs question)
5. If action:
   a. Super Planning Agent creates execution plan
   b. Execution Agent runs steps
   c. Tools execute operations (image gen, API calls, etc.)
   d. Results collected and formatted
6. If question:
   a. Context manager assembles conversation history
   b. Memory agent retrieves relevant knowledge
   c. Claude generates response
7. Response returned to client
8. Self-improvement loop captures outcome
```

### WebSocket Flow

```
1. Client connects to /ws
2. Server authenticates and creates session
3. Bidirectional messages:
   Client → Server: chat messages, voice data, commands
   Server → Client: responses, progress updates, status
4. Server sends typing indicators during processing
5. Streaming responses via SSE or chunked WebSocket messages
```

---

## Database Schema

Otto uses SQLAlchemy ORM with support for SQLite (default) and PostgreSQL:

- **Users** — User accounts and profiles
- **Sessions** — Chat sessions with metadata
- **Messages** — Conversation message history
- **Tasks** — Scheduled and queued tasks
- **Projects** — Project management entries
- **Files** — File metadata and references

Migrations are managed via Alembic in `src/database/migrate.py`.

---

## Deployment Architecture

### Development
```
Single process → uvicorn → SQLite → Local files
```

### Production (Docker Compose)
```
nginx (reverse proxy, SSL)
  ↓
otto-api (uvicorn, 4 workers)
  ├── PostgreSQL (persistent data)
  ├── Redis (caching, sessions)
  └── ChromaDB (vector store)
```
