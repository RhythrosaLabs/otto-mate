# 🚀 Otto Universal - Modularization Implementation Plan

## Overview

This document provides a **step-by-step implementation plan** to transform Otto from a monolithic application into a modular, UI-agnostic platform. This will enable:
- Swapping UI frameworks without touching backend
- Independent scaling of frontend and backend
- Clean separation of concerns
- Easier testing and maintenance
- Multiple client applications (web, mobile, CLI, etc.)

## Current State Assessment

### ✅ Strengths
- Working FastAPI backend with comprehensive tooling
- Multi-agent architecture (Planning, Execution, Memory)
- Extensive tool ecosystem (100+ tools)
- Real-time streaming via SSE
- ChromaDB vector memory

### ⚠️ Pain Points
- HTML served directly from backend
- Frontend logic mixed with API routes
- No clear API versioning
- Tight coupling between UI and business logic
- Hard to test components independently
- Difficult to create alternative UIs

## Target Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Frontend Layer (Swappable)                 │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Vanilla JS  │  │    React     │  │     Vue      │      │
│  │     SPA      │  │     SPA      │  │     SPA      │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         └──────────────────┴──────────────────┘              │
└────────────────────────────┼────────────────────────────────┘
                             │ (HTTP/WebSocket)
┌────────────────────────────▼────────────────────────────────┐
│                      API Gateway                              │
│              (FastAPI - Pure JSON API)                        │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                  API Endpoints (v1)                     │ │
│  │  /api/v1/chat  /api/v1/files  /api/v1/agents          │ │
│  │  /api/v1/settings  /api/v1/workflows                   │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────────┼────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                    Service Layer                              │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ChatService  │  │FileService  │  │AgentService │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                               │
│  Pure business logic - No HTTP/UI concerns                   │
└────────────────────────────┼────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│               Agent Orchestration Layer                       │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Planning Agent  │  Execution Agent  │  Memory Agent │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │             Tool Registry & Execution                 │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────────┼────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│              Data & Infrastructure Layer                      │
│                                                               │
│  ChromaDB  │  File Storage  │  Redis  │  PostgreSQL         │
└───────────────────────────────────────────────────────────────┘
```

## Implementation Phases

### Phase 0: Preparation (Day 1)
**Goal**: Set up new structure without breaking current system

**Tasks**:
1. Create new directory structure
2. Set up branch strategy
3. Document current API endpoints
4. Set up testing infrastructure

**Commands**:
```bash
# Create new structure
mkdir -p backend/src/{api/v1,core/{services,models,agents},integrations}
mkdir -p frontends/{vanilla-js/{src,public},shared}
mkdir -p packages/{api-client,types}

# Create git branches
git checkout -b refactor/modular-architecture
git checkout -b refactor/service-layer
git checkout -b refactor/frontend-extraction
```

**Deliverables**:
- [ ] New directory structure created
- [ ] Branches set up
- [ ] API documentation generated
- [ ] Test infrastructure configured

---

### Phase 1: Service Layer Extraction (Days 2-5)
**Goal**: Extract business logic from API routes into dedicated services

#### 1.1 Create Domain Models (Day 2)

**Create**: `backend/src/core/models/`

```python
# backend/src/core/models/chat.py
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Literal

@dataclass
class ChatMessage:
    """Domain model for chat message"""
    id: str
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ChatMessage':
        return cls(**data)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {}
        }

@dataclass
class ChatSession:
    """Domain model for chat session"""
    id: str
    user_id: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = None

@dataclass
class StreamingChunk:
    """Domain model for streaming response chunk"""
    type: Literal["thinking", "text", "tool_start", "tool_end", "artifact", "complete", "error"]
    content: str
    metadata: Dict[str, Any] = None
```

**Also create**:
- `models/agent.py` - Agent, Tool, Workflow models
- `models/file.py` - File, FileMetadata models
- `models/settings.py` - Settings models

**Deliverables**:
- [ ] Domain models created
- [ ] Type hints on all models
- [ ] to_dict/from_dict methods
- [ ] Unit tests for models

#### 1.2 Create Service Layer (Days 3-4)

**Create**: `backend/src/core/services/`

```python
# backend/src/core/services/chat_service.py
from typing import AsyncIterator
from ..models.chat import ChatMessage, ChatSession, StreamingChunk
from ..agents.orchestrator import AgentOrchestrator

class ChatService:
    """
    Business logic for chat operations.
    
    This service has NO knowledge of HTTP, WebSockets, or any transport layer.
    It only works with domain models.
    """
    
    def __init__(self, orchestrator: AgentOrchestrator):
        self.orchestrator = orchestrator
    
    async def process_message(
        self,
        message: str,
        session_id: str,
        user_id: str = "default"
    ) -> ChatMessage:
        """
        Process a chat message and return the response.
        
        Pure business logic - no HTTP concerns.
        """
        # Validate input
        if not message.strip():
            raise ValueError("Message cannot be empty")
        
        # Process through orchestrator
        result = await self.orchestrator.process(
            message=message,
            session_id=session_id,
            user_id=user_id
        )
        
        # Convert to domain model
        return ChatMessage(
            id=result["message_id"],
            role="assistant",
            content=result["response"],
            timestamp=datetime.now(),
            metadata=result.get("metadata", {})
        )
    
    async def process_streaming(
        self,
        message: str,
        session_id: str,
        user_id: str = "default"
    ) -> AsyncIterator[StreamingChunk]:
        """
        Process message with streaming responses.
        
        Yields domain model chunks, not HTTP/WebSocket frames.
        """
        async for chunk in self.orchestrator.process_streaming(
            message=message,
            session_id=session_id,
            user_id=user_id
        ):
            yield StreamingChunk(
                type=chunk["type"],
                content=chunk.get("content", ""),
                metadata=chunk.get("metadata", {})
            )
    
    async def get_session_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> ChatSession:
        """Get chat history for a session"""
        history = await self.orchestrator.memory_agent.get_session_history(
            session_id=session_id,
            limit=limit
        )
        
        messages = [
            ChatMessage.from_dict(msg) 
            for msg in history
        ]
        
        return ChatSession(
            id=session_id,
            user_id=history[0].get("user_id", "default") if history else "default",
            messages=messages,
            created_at=messages[0].timestamp if messages else datetime.now(),
            updated_at=messages[-1].timestamp if messages else datetime.now()
        )
```

**Also create**:
- `services/file_service.py` - File operations
- `services/agent_service.py` - Agent management
- `services/workflow_service.py` - Workflow execution
- `services/settings_service.py` - Settings management

**Deliverables**:
- [ ] All service classes created
- [ ] Services use only domain models
- [ ] No HTTP/transport layer code in services
- [ ] Unit tests for all services (80%+ coverage)

#### 1.3 Update API Routes to Use Services (Day 5)

**Update**: `backend/src/api/v1/chat.py` (NEW FILE)

```python
# backend/src/api/v1/chat.py
from fastapi import APIRouter, Depends, HTTPException
from typing import AsyncIterator
import json

from ...core.services.chat_service import ChatService
from ...core.models.chat import StreamingChunk
from .dependencies import get_chat_service
from .schemas import ChatRequest, ChatResponse, StreamChunk

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Send a chat message.
    
    API layer only handles:
    - HTTP request/response
    - Validation
    - Error handling
    - Response formatting
    
    Business logic is in ChatService.
    """
    try:
        # Call service (pure business logic)
        message = await chat_service.process_message(
            message=request.message,
            session_id=request.session_id,
            user_id=request.user_id
        )
        
        # Convert domain model to API response
        return ChatResponse(
            message_id=message.id,
            role=message.role,
            content=message.content,
            timestamp=message.timestamp,
            metadata=message.metadata
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/stream")
async def send_message_streaming(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Send message with streaming response.
    
    API layer converts domain StreamingChunk to SSE format.
    """
    async def generate_sse():
        try:
            async for chunk in chat_service.process_streaming(
                message=request.message,
                session_id=request.session_id,
                user_id=request.user_id
            ):
                # Convert domain chunk to SSE format
                sse_data = StreamChunk(
                    type=chunk.type,
                    content=chunk.content,
                    metadata=chunk.metadata
                ).dict()
                
                yield f"data: {json.dumps(sse_data)}\n\n"
        
        except Exception as e:
            error_data = {"type": "error", "content": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"
    
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream"
    )

@router.get("/{session_id}/history")
async def get_history(
    session_id: str,
    limit: int = 50,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get chat history for session"""
    try:
        session = await chat_service.get_session_history(session_id, limit)
        return {
            "session_id": session.id,
            "messages": [msg.to_dict() for msg in session.messages]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Also create**:
- `api/v1/files.py`
- `api/v1/agents.py`
- `api/v1/settings.py`
- `api/v1/workflows.py`

**Create**: `backend/src/api/v1/dependencies.py`

```python
# backend/src/api/v1/dependencies.py
from functools import lru_cache
from ...core.services.chat_service import ChatService
from ...core.agents.orchestrator import AgentOrchestrator

# Cache services (singleton pattern)
_chat_service: ChatService = None

def get_chat_service() -> ChatService:
    """Dependency injection for ChatService"""
    global _chat_service
    if _chat_service is None:
        orchestrator = AgentOrchestrator()  # Or from config
        _chat_service = ChatService(orchestrator)
    return _chat_service
```

**Deliverables**:
- [ ] All API routes refactored
- [ ] Routes use services via dependency injection
- [ ] No business logic in routes
- [ ] Integration tests for all endpoints

---

### Phase 2: Frontend Extraction (Days 6-10)
**Goal**: Move frontend to `frontends/vanilla-js/` and create API client

#### 2.1 Create API Client Library (Day 6)

**Create**: `frontends/shared/api-client.js`

```javascript
// frontends/shared/api-client.js
/**
 * Otto API Client
 * 
 * Pure JavaScript client for Otto Universal API.
 * Works with any frontend framework.
 */
class OttoApiClient {
    constructor(config = {}) {
        this.baseUrl = config.baseUrl || 'http://localhost:8000';
        this.apiVersion = config.apiVersion || 'v1';
        this.timeout = config.timeout || 30000;
    }
    
    /**
     * Send a chat message
     */
    async sendMessage(message, sessionId, userId = 'default') {
        const response = await this._fetch('/chat', {
            method: 'POST',
            body: JSON.stringify({
                message,
                session_id: sessionId,
                user_id: userId
            })
        });
        return response.json();
    }
    
    /**
     * Stream chat responses
     */
    async* streamMessage(message, sessionId, userId = 'default') {
        const response = await this._fetch('/chat/stream', {
            method: 'POST',
            body: JSON.stringify({
                message,
                session_id: sessionId,
                user_id: userId
            })
        });
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        while (true) {
            const {done, value} = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, {stream: true});
            const lines = buffer.split('\n\n');
            buffer = lines.pop(); // Keep incomplete line in buffer
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.substring(6));
                    yield data;
                }
            }
        }
    }
    
    /**
     * Get chat history
     */
    async getHistory(sessionId, limit = 50) {
        const response = await this._fetch(`/chat/${sessionId}/history?limit=${limit}`);
        return response.json();
    }
    
    /**
     * Upload file
     */
    async uploadFile(file, category = 'documents', tags = []) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('category', category);
        formData.append('tags', JSON.stringify(tags));
        
        const response = await this._fetch('/files/upload', {
            method: 'POST',
            body: formData
        });
        return response.json();
    }
    
    /**
     * Internal fetch wrapper
     */
    async _fetch(endpoint, options = {}) {
        const url = `${this.baseUrl}/api/${this.apiVersion}${endpoint}`;
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        };
        
        // Remove Content-Type for FormData
        if (options.body instanceof FormData) {
            delete defaultOptions.headers['Content-Type'];
        }
        
        const response = await fetch(url, {
            ...defaultOptions,
            ...options
        });
        
        if (!response.ok) {
            const error = await response.json().catch(() => ({detail: 'Unknown error'}));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }
        
        return response;
    }
}

// Export for use in different module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OttoApiClient;
}
```

**Deliverables**:
- [ ] API client created
- [ ] All current endpoints covered
- [ ] Error handling
- [ ] TypeScript types (`.d.ts` file)

#### 2.2 Move Frontend Files (Days 7-8)

**Structure**:
```
frontends/vanilla-js/
├── public/
│   ├── index.html
│   ├── chat.html
│   ├── settings.html
│   ├── files.html
│   └── assets/
│       ├── css/
│       ├── js/
│       └── images/
├── src/
│   ├── api/
│   │   └── client.js (symlink to shared)
│   ├── components/
│   │   ├── chat.js
│   │   ├── sidebar.js
│   │   └── artifacts.js
│   ├── utils/
│   └── app.js
├── package.json
└── README.md
```

**Update HTML files** to use API client:

```html
<!-- frontends/vanilla-js/public/chat.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Otto Chat</title>
    <link rel="stylesheet" href="/assets/css/chat.css">
</head>
<body>
    <div id="app"></div>
    
    <script type="module">
        import { OttoApiClient } from '../src/api/client.js';
        import { ChatComponent } from '../src/components/chat.js';
        
        const client = new OttoApiClient({
            baseUrl: window.location.origin
        });
        
        const chat = new ChatComponent(client);
        chat.mount('#app');
    </script>
</body>
</html>
```

**Deliverables**:
- [ ] All HTML files moved
- [ ] Inline JS extracted to modules
- [ ] CSS organized
- [ ] Uses API client for all requests

#### 2.3 Update Backend (Days 9-10)

**Update**: `backend/src/api/main.py`

```python
# backend/src/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .v1 import chat, files, agents, settings, workflows

app = FastAPI(
    title="Otto Universal API",
    description="AI Assistant API",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Vite dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes (v1)
app.include_router(chat.router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(settings.router, prefix="/api/v1")
app.include_router(workflows.router, prefix="/api/v1")

# Static files (for production)
# In dev, frontend runs on separate server
app.mount("/", StaticFiles(directory="../../frontends/vanilla-js/public", html=True), name="static")

@app.get("/api/health")
async def health():
    return {"status": "healthy"}
```

**Deliverables**:
- [ ] Backend only serves JSON API
- [ ] Static file serving for production
- [ ] CORS configured
- [ ] No HTML-specific routes

---

### Phase 3: Tool System Enhancement (Days 11-12)
**Goal**: Decorator-based tool registration

**Create**: `backend/src/core/decorators.py`

```python
# backend/src/core/decorators.py
from typing import Callable, Dict, Any
from functools import wraps

_registered_tools = []

def otto_tool(
    name: str,
    description: str,
    category: str,
    parameters: Dict[str, Any]
):
    """
    Decorator for registering Otto tools.
    
    Usage:
        @otto_tool(
            name="generate_design",
            description="Generate a design using AI",
            category="ai_models",
            parameters={
                "prompt": {"type": "string", "required": True}
            }
        )
        async def generate_design(prompt: str):
            # Tool implementation
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        # Attach metadata
        wrapper._is_otto_tool = True
        wrapper._tool_metadata = {
            "name": name,
            "description": description,
            "category": category,
            "parameters": parameters,
            "function": wrapper
        }
        
        # Auto-register
        _registered_tools.append(wrapper)
        
        return wrapper
    
    return decorator

def get_registered_tools():
    """Get all registered tools"""
    return [
        {
            "name": tool._tool_metadata["name"],
            "description": tool._tool_metadata["description"],
            "category": tool._tool_metadata["category"],
            "parameters": tool._tool_metadata["parameters"],
            "function": tool
        }
        for tool in _registered_tools
    ]
```

**Migrate existing tools**:

```python
# backend/src/integrations/replicate/tools.py
from ...core.decorators import otto_tool

@otto_tool(
    name="generate_image",
    description="Generate an image using AI",
    category="ai_models",
    parameters={
        "prompt": {"type": "string", "required": True},
        "model": {"type": "string", "required": False, "default": "flux-schnell"}
    }
)
async def generate_image(prompt: str, model: str = "flux-schnell"):
    """Generate image - automatically registered!"""
    # Implementation
    pass
```

**Deliverables**:
- [ ] Decorator system created
- [ ] Auto-registration working
- [ ] All tools migrated
- [ ] Tool discovery system

---

### Phase 4: Documentation & Testing (Days 13-14)
**Goal**: Comprehensive docs and tests

**Create**:
- API documentation (OpenAPI/Swagger)
- Frontend component documentation
- Integration guide
- Migration guide
- Testing guide

**Write tests**:
- Unit tests for all services (80%+ coverage)
- Integration tests for API endpoints
- E2E tests for critical flows
- Frontend component tests

**Deliverables**:
- [ ] Complete API docs
- [ ] Component docs
- [ ] Integration guide
- [ ] 80%+ test coverage

---

## Success Criteria

### Technical
- [ ] Backend is pure JSON API (no HTML serving)
- [ ] Frontend runs independently
- [ ] Services have no HTTP/transport dependencies
- [ ] 80%+ test coverage on business logic
- [ ] API versioning in place
- [ ] Type hints on all public functions

### Functional
- [ ] All existing features work
- [ ] No regression in functionality
- [ ] Performance maintained or improved
- [ ] Real-time streaming still works

### Developer Experience
- [ ] Frontend can be developed independently
- [ ] Backend changes don't break frontend contract
- [ ] Easy to add new tools (decorator pattern)
- [ ] Easy to add new services
- [ ] Clear separation of concerns

## Rollout Strategy

### Week 1-2: Parallel Development
- New structure alongside old code
- Both systems functional
- Feature parity maintained

### Week 3: Migration
- Migrate one feature at a time
- Test thoroughly
- Keep old code as fallback

### Week 4: Cleanup
- Remove old code
- Update documentation
- Deploy to production

## Next Steps

1. **Review this plan** - Approve or suggest changes
2. **Create branches** - Set up git workflow
3. **Start Phase 0** - Preparation work
4. **Weekly sync** - Track progress

---

**Remember**: The goal is not perfection, but **continuous improvement**. Start small, test thoroughly, iterate quickly.
