# 🏗️ Otto Universal - Modular Architecture Proposal

## Executive Summary

This document outlines a comprehensive refactoring to create a **UI-agnostic, modular architecture** that allows Otto to swap UI/UX libraries (React, Vue, Svelte, vanilla JS, etc.) without affecting core functionality.

## Problems with Current Architecture

### 1. **Tight Coupling**
- HTML/CSS/JS directly embedded in `src/web/` directory
- Backend serves HTML files directly via FastAPI
- No clear separation between presentation and business logic
- UI state management mixed with API calls

### 2. **Monolithic Frontend**
- Single large HTML files with inline JavaScript
- No component isolation
- Hard to test UI independently
- Difficult to reuse components

### 3. **API Design Issues**
- Some routes return HTML (`HTMLResponse`)
- Mixing of UI serving and API endpoints
- No clear API versioning
- Frontend and backend deployed together

## Proposed Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer (Swappable)                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  React   │  │   Vue    │  │  Svelte  │  │ Vanilla  │   │
│  │    UI    │  │    UI    │  │    UI    │  │    JS    │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       └──────────────┴──────────────┴──────────────┘         │
│                            │                                  │
└────────────────────────────┼─────────────────────────────────┘
                             │
                   ┌─────────▼──────────┐
                   │   API Gateway      │
                   │   (REST/WebSocket) │
                   └─────────┬──────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                    Backend Core (Stable)                      │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   API Layer  │  │  Business    │  │ Integration  │      │
│  │   (FastAPI)  │  │    Logic     │  │    Layer     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │               │
│  ┌──────▼──────────────────▼──────────────────▼───────┐     │
│  │         Agent Orchestration Layer                   │     │
│  │  (Planning, Execution, Memory, Tool Registry)      │     │
│  └─────────────────────────┬──────────────────────────┘     │
│                            │                                  │
│  ┌─────────────────────────▼──────────────────────────┐     │
│  │              Data & Infrastructure                   │     │
│  │  (ChromaDB, Redis, PostgreSQL, File Storage)       │     │
│  └──────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────┘
```

## New Directory Structure

```
otto-universal/
│
├── backend/                          # Pure backend API (no UI)
│   ├── src/
│   │   ├── api/                      # API layer (REST endpoints)
│   │   │   ├── v1/                   # API v1
│   │   │   │   ├── chat.py
│   │   │   │   ├── agents.py
│   │   │   │   ├── files.py
│   │   │   │   ├── settings.py
│   │   │   │   └── health.py
│   │   │   ├── websockets/           # WebSocket handlers
│   │   │   │   └── chat_ws.py
│   │   │   ├── middleware/
│   │   │   │   ├── cors.py
│   │   │   │   ├── auth.py
│   │   │   │   └── rate_limit.py
│   │   │   └── main.py              # FastAPI app
│   │   │
│   │   ├── core/                     # Business logic (UI-agnostic)
│   │   │   ├── agents/
│   │   │   │   ├── orchestrator.py
│   │   │   │   ├── planning.py
│   │   │   │   ├── execution.py
│   │   │   │   └── memory.py
│   │   │   ├── tools/
│   │   │   │   ├── registry.py
│   │   │   │   ├── base.py
│   │   │   │   └── categories/
│   │   │   ├── services/              # Business services
│   │   │   │   ├── chat_service.py
│   │   │   │   ├── file_service.py
│   │   │   │   └── workflow_service.py
│   │   │   └── models/                # Domain models
│   │   │       ├── chat.py
│   │   │       ├── agent.py
│   │   │       └── workflow.py
│   │   │
│   │   ├── integrations/             # External service integrations
│   │   │   ├── printify/
│   │   │   ├── shopify/
│   │   │   ├── replicate/
│   │   │   └── openai/
│   │   │
│   │   ├── storage/                  # Data persistence
│   │   │   ├── repositories/         # Data access layer
│   │   │   ├── file_storage.py
│   │   │   └── vector_db.py
│   │   │
│   │   └── utils/
│   │       ├── config.py
│   │       ├── logger.py
│   │       └── validators.py
│   │
│   ├── tests/
│   ├── pyproject.toml
│   └── README.md
│
├── frontends/                        # Multiple UI implementations
│   │
│   ├── vanilla-js/                   # Current vanilla JS UI
│   │   ├── public/
│   │   │   ├── index.html
│   │   │   ├── chat.html
│   │   │   ├── settings.html
│   │   │   └── assets/
│   │   │       ├── css/
│   │   │       ├── js/
│   │   │       └── images/
│   │   ├── src/
│   │   │   ├── api/                  # API client
│   │   │   │   └── client.js
│   │   │   ├── components/           # Vanilla components
│   │   │   └── utils/
│   │   ├── package.json
│   │   └── README.md
│   │
│   ├── react/                        # React implementation (future)
│   │   ├── src/
│   │   │   ├── api/
│   │   │   │   └── client.ts
│   │   │   ├── components/
│   │   │   │   ├── Chat/
│   │   │   │   ├── Sidebar/
│   │   │   │   └── Settings/
│   │   │   ├── hooks/
│   │   │   ├── store/               # State management
│   │   │   └── App.tsx
│   │   ├── package.json
│   │   └── README.md
│   │
│   └── shared/                       # Shared frontend utilities
│       ├── types/                    # TypeScript types
│       ├── api-client/               # Shared API client
│       └── constants/
│
├── packages/                         # Shared packages
│   ├── api-client/                   # TypeScript API client
│   │   ├── src/
│   │   │   ├── client.ts
│   │   │   ├── types.ts
│   │   │   └── websocket.ts
│   │   ├── package.json
│   │   └── README.md
│   │
│   └── types/                        # Shared TypeScript types
│       ├── chat.ts
│       ├── agent.ts
│       └── workflow.ts
│
├── docs/                             # All documentation here
│   ├── architecture/
│   ├── api/
│   ├── deployment/
│   └── guides/
│
├── docker/                           # Docker configs
│   ├── backend.Dockerfile
│   ├── frontend.Dockerfile
│   └── docker-compose.yml
│
└── scripts/                          # Build/deploy scripts
    ├── setup-backend.sh
    ├── setup-frontend.sh
    └── deploy.sh
```

## Key Principles

### 1. **Backend: Pure API**
- **No HTML serving** - Backend only returns JSON/data
- **RESTful design** - Clear resource-based endpoints
- **WebSocket support** - Real-time communication
- **API versioning** - `/api/v1/`, `/api/v2/`
- **Stateless** - No session state on server

### 2. **Frontend: Pluggable**
- **Separate deployments** - Frontend can be deployed independently
- **API-first** - All frontends consume the same API
- **Framework agnostic** - Use React, Vue, Svelte, or vanilla JS
- **Shared types** - TypeScript types shared across frontends

### 3. **Core: Business Logic**
- **No UI dependencies** - Core has no knowledge of presentation layer
- **Service layer** - Clean service interfaces
- **Domain models** - Rich domain objects
- **Repository pattern** - Abstract data access

## Implementation Plan

### Phase 1: Backend Refactoring (Week 1-2)

#### 1.1 Extract Business Logic
```python
# OLD (src/api/main.py)
@app.post("/chat")
async def chat(request: ChatRequest):
    # Business logic mixed with API handling
    result = await otto.process(message=request.message)
    return ChatResponse(**result)

# NEW (src/core/services/chat_service.py)
class ChatService:
    def __init__(self, orchestrator: AgentOrchestrator):
        self.orchestrator = orchestrator
    
    async def process_message(
        self, 
        message: str, 
        session_id: str
    ) -> ChatResult:
        # Pure business logic
        return await self.orchestrator.process(message, session_id)

# NEW (src/api/v1/chat.py)
@router.post("/chat")
async def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    # API layer only handles HTTP concerns
    result = await chat_service.process_message(
        message=request.message,
        session_id=request.session_id
    )
    return ChatResponse.from_domain(result)
```

#### 1.2 Create Service Layer
- `ChatService` - Chat operations
- `FileService` - File management
- `WorkflowService` - Workflow execution
- `AgentService` - Agent management
- `SettingsService` - Settings management

#### 1.3 Define Domain Models
```python
# src/core/models/chat.py
@dataclass
class ChatMessage:
    id: str
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class ChatSession:
    id: str
    user_id: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime
```

#### 1.4 API Versioning
```python
# src/api/main.py
app = FastAPI(title="Otto API", version="1.0.0")

# Register versioned routers
app.include_router(
    v1_router,
    prefix="/api/v1",
    tags=["v1"]
)
```

### Phase 2: Frontend Extraction (Week 2-3)

#### 2.1 Create API Client Library
```typescript
// packages/api-client/src/client.ts
export class OttoApiClient {
    constructor(private baseUrl: string) {}
    
    async sendMessage(message: string, sessionId: string): Promise<ChatResponse> {
        const response = await fetch(`${this.baseUrl}/api/v1/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, session_id: sessionId })
        });
        return response.json();
    }
    
    streamChat(message: string): AsyncIterableIterator<ChatChunk> {
        // WebSocket/SSE streaming
    }
}
```

#### 2.2 Migrate Current UI to `frontends/vanilla-js/`
- Move HTML files to `public/`
- Extract inline JS to modules in `src/`
- Use API client for all requests
- Implement proper component structure

#### 2.3 Create Shared Types
```typescript
// packages/types/chat.ts
export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    metadata?: Record<string, any>;
}

export interface ChatSession {
    id: string;
    userId: string;
    messages: ChatMessage[];
    createdAt: string;
    updatedAt: string;
}
```

### Phase 3: React Frontend (Week 4)

#### 3.1 Create React App
```bash
cd frontends/react
npm create vite@latest . -- --template react-ts
npm install @otto/api-client @otto/types
```

#### 3.2 Implement Components
```tsx
// frontends/react/src/components/Chat/ChatWindow.tsx
import { useState } from 'react';
import { OttoApiClient } from '@otto/api-client';
import { ChatMessage } from '@otto/types';

export function ChatWindow() {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const client = new OttoApiClient(import.meta.env.VITE_API_URL);
    
    const sendMessage = async (content: string) => {
        const response = await client.sendMessage(content, sessionId);
        setMessages([...messages, response.message]);
    };
    
    return (
        <div className="chat-window">
            {messages.map(msg => (
                <MessageBubble key={msg.id} message={msg} />
            ))}
            <MessageInput onSend={sendMessage} />
        </div>
    );
}
```

### Phase 4: Testing & Documentation (Week 5)

#### 4.1 Backend Tests
```python
# tests/core/services/test_chat_service.py
async def test_chat_service_processes_message():
    service = ChatService(orchestrator=mock_orchestrator)
    result = await service.process_message("Hello", "session-123")
    assert result.message.content == "Hi there!"
```

#### 4.2 Frontend Tests
```typescript
// frontends/react/src/components/Chat/__tests__/ChatWindow.test.tsx
test('sends message when user submits', async () => {
    render(<ChatWindow />);
    await userEvent.type(screen.getByRole('textbox'), 'Hello');
    await userEvent.click(screen.getByRole('button', { name: /send/i }));
    expect(await screen.findByText(/Hi there!/)).toBeInTheDocument();
});
```

#### 4.3 API Documentation
- OpenAPI/Swagger docs auto-generated
- WebSocket protocol documentation
- Client SDK documentation

## Benefits

### 1. **Flexibility**
- Swap UI frameworks without touching backend
- A/B test different frontends
- Support multiple clients (web, mobile, desktop)

### 2. **Scalability**
- Frontend and backend scale independently
- Deploy frontends to CDN
- Backend can be containerized and scaled horizontally

### 3. **Maintainability**
- Clear separation of concerns
- Easier to test each layer
- Better code organization

### 4. **Developer Experience**
- Frontend devs work independently from backend devs
- Use modern frontend tooling (Vite, TypeScript, etc.)
- Shared types ensure API contract compliance

### 5. **Performance**
- Static frontend assets served from CDN
- Backend optimized for API performance
- Caching strategies at each layer

## Migration Strategy

### Stage 1: Backward Compatible (Weeks 1-2)
- Keep existing UI working
- Create new API endpoints under `/api/v1/`
- Backend serves both old UI and new API

### Stage 2: Parallel Implementation (Weeks 2-4)
- New vanilla JS UI uses new API
- Old UI still available at `/legacy/`
- Both work side-by-side

### Stage 3: Deprecation (Week 5)
- Mark old endpoints as deprecated
- Document migration path
- Set sunset date for old UI

### Stage 4: Cleanup (Week 6)
- Remove old HTML-serving endpoints
- Pure API backend
- All clients use new API

## Example: Chat Flow

### Old Architecture
```
User Browser → FastAPI (serves chat.html)
              ↓
User types message → Inline JS → POST /chat
                                   ↓
                            AgentOrchestrator.process()
                                   ↓
                            Returns HTML snippet
                                   ↓
                            jQuery updates DOM
```

### New Architecture
```
User Browser → Nginx/CDN (serves static React app)
              ↓
React App initialized → ApiClient connects to ws://api.otto.com/chat
                                   ↓
User types message → React state update → WebSocket message
                                              ↓
                                        FastAPI WebSocket
                                              ↓
                                        ChatService.process_message()
                                              ↓
                                        AgentOrchestrator.process()
                                              ↓
                                        Stream results via WebSocket
                                              ↓
                                        React updates UI in real-time
```

## Insights from Useful Repos

### Browser-Use
- **Lesson**: Clean agent/tool abstraction
- **Apply**: Similar tool registry pattern but UI-agnostic
- **Code**: Their `Agent` class is decoupled from UI

### CrewAI
- **Lesson**: Multi-agent orchestration patterns
- **Apply**: Improve our agent orchestration layer
- **Code**: Their crew/agent/task structure

### AutoGPT
- **Lesson**: Modular plugin system
- **Apply**: Plugin-based tool loading
- **Code**: Their plugin architecture

### Quivr
- **Lesson**: Clean API design for AI features
- **Apply**: RESTful patterns for our endpoints
- **Code**: Their FastAPI structure

## Next Steps

1. **Review & Approve** this proposal
2. **Create feature branches** for each phase
3. **Set up CI/CD** for new structure
4. **Begin Phase 1** - Backend refactoring
5. **Weekly sync** to track progress

## Questions & Discussion

- Should we support multiple API versions simultaneously?
- Which frontend framework to prioritize after vanilla JS?
- How to handle WebSocket reconnection in new architecture?
- Authentication strategy for API-first approach?

---

**Goal**: Make Otto's backend a rock-solid, UI-agnostic API that can power any frontend, mobile app, CLI tool, or integration. The UI should be a thin client that just displays data and handles user interactions.
