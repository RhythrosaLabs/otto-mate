# Otto Universal - Implementation Status & Next Steps

## What Was Done ✅

### 1. Streaming Support Added
- ✅ `StreamingResponse` import added to API  
- ✅ `/chat/stream` endpoint implemented
- ✅ `process_streaming()` method added to `AgentOrchestrator`
- ✅ Yields: thinking, tool_start, tool_end, text, artifact, complete, error
- ✅ Word-by-word streaming with typing delay

**File:** `src/core/agent_orchestrator.py`  
**Method:** `async def process_streaming(...) -> AsyncGenerator`

### 2. Research Complete
- ✅ Claude Agents SDK patterns analyzed
- ✅ Gemini UI patterns documented
- ✅ Anthropic Cookbook reviewed
- ✅ Best practices identified

## What Needs to Be Done 🚧

### Priority 1: Critical Functionality

#### A. Fix Printify Integration (CRITICAL)
**Problem:** Image upload consistently fails with error 10300

**Root Cause:** Replicate webp URLs not compatible with Printify API

**Solution:**
1. Always save generated images to local file storage first
2. Upload from local files, not URLs
3. Already partially implemented in `business_workflows.py` (save_design step)

**Files to Fix:**
- `src/tools/printify.py` - `upload_image()` method
- `src/core/business_workflows.py` - Verify save_design step works

**Code Fix Needed:**
```python
# In printify.py upload_image method
async def upload_image(self, image_url: str, ...):
    # Step 1: Download image first
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as resp:
            image_data = await resp.read()
    
    # Step 2: Save to local storage
    from ..storage.file_storage import FileStorage
    storage = FileStorage()
    local_path = await storage.save_file(
        file_data=image_data,
        filename=filename,
        category="temp"
    )
    
    # Step 3: Read and base64 encode
    with open(local_path, 'rb') as f:
        encoded = base64.b64encode(f.read()).decode('utf-8')
    
    # Step 4: Upload to Printify
    data = {
        "file_name": filename,
        "contents": encoded  # Use contents, not url
    }
    return await self._request("POST", endpoint, data)
```

#### B. Update Chat UI for Streaming
**Problem:** UI doesn't consume SSE stream yet

**Solution:** Replace WebSocket with EventSource for streaming

**File:** `src/web/chat.html`

**Code to Add:**
```javascript
// Replace sendMessage() function
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    if (!message) return;
    
    // Add user message
    addMessage('user', message);
    input.value = '';
    
    // Create assistant message container
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message assistant';
    msgDiv.innerHTML = `
        <div class="message-content">
            <div class="thinking" id="thinking"></div>
            <div class="message-bubble" id="response"></div>
            <div class="artifacts" id="artifacts"></div>
        </div>
    `;
    document.getElementById('messages').appendChild(msgDiv);
    
    // Connect to streaming endpoint
    const eventSource = new EventSource(`/chat/stream?message=${encodeURIComponent(message)}&session_id=${sessionId}`);
    
    let responseText = '';
    const responseDiv = document.getElementById('response');
    const thinkingDiv = document.getElementById('thinking');
    const artifactsDiv = document.getElementById('artifacts');
    
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        switch(data.type) {
            case 'thinking':
                thinkingDiv.textContent = data.content;
                break;
                
            case 'tool_start':
                thinkingDiv.innerHTML += `<div class="tool-exec">⚡ ${data.content}...</div>`;
                break;
                
            case 'tool_end':
                if (data.metadata.success) {
                    thinkingDiv.innerHTML += `<div class="tool-done">✓ ${data.content}</div>`;
                } else {
                    thinkingDiv.innerHTML += `<div class="tool-error">✗ ${data.content}</div>`;
                }
                break;
                
            case 'text':
                responseText += data.content;
                responseDiv.textContent = responseText;
                break;
                
            case 'artifact':
                if (data.content.type === 'image') {
                    artifactsDiv.innerHTML += `<img src="${data.content.url}" class="artifact-image">`;
                }
                break;
                
            case 'complete':
                thinkingDiv.style.display = 'none';
                eventSource.close();
                break;
                
            case 'error':
                responseDiv.innerHTML = `<div class="error">Error: ${data.content}</div>`;
                eventSource.close();
                break;
        }
        
        // Auto-scroll
        msgDiv.scrollIntoView({ behavior: 'smooth' });
    };
    
    eventSource.onerror = (error) => {
        console.error('EventSource error:', error);
        eventSource.close();
    };
}
```

#### C. Make Otto More Autonomous
**Problem:** Too many "Should I..." questions in prompts

**Solution:** Change all planning prompts to be decisive

**File:** `src/core/super_planning_agent.py`

**Changes Needed:**
```python
# Line ~45 - Change system prompt from:
"Should I create a product?"
"Do you want me to...?"

# To:
"Creating product..."
"Executing plan..."
"Generating images..."
```

**Specific Prompt Updates:**
```python
system = f"""You are Otto, an AUTONOMOUS AI assistant. You make decisions and execute them without asking permission.

NEVER ask "Should I...?" or "Do you want me to...?"  
ALWAYS execute your plan directly.

When given a task:
1. Analyze what needs to be done
2. Create an execution plan
3. EXECUTE IT (don't ask first)
4. Report results

Only check-in if there are multiple valid approaches and you need clarification.

Example GOOD response:
"I'll create a t-shirt design, upload it to Printify, and generate social media content."

Example BAD response:
"Should I create a t-shirt design? Would you like me to upload it to Printify?"
"""
```

### Priority 2: UI Improvements

#### D. Gemini-Style CSS
**File:** `src/web/chat.html` (in `<style>` section)

**Key Changes:**
```css
/* Import Google Sans font */
@import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&display=swap');

:root {
    /* Gemini color palette */
    --bg-primary: #ffffff;
    --bg-secondary: #f8f9fa;
    --bg-tertiary: #e8eaed;
    --text-primary: #202124;
    --text-secondary: #5f6368;
    --accent-blue: #1a73e8;
    --accent-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --border: #dadce0;
}

body {
    font-family: 'Google Sans', 'Helvetica Neue', Arial, sans-serif;
    background: var(--bg-secondary);
}

/* Metallic sheen effect */
.button, .send-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    position: relative;
    overflow: hidden;
}

.button::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: linear-gradient(
        45deg,
        transparent 30%,
        rgba(255, 255, 255, 0.3) 50%,
        transparent 70%
    );
    animation: shine 3s infinite;
}

@keyframes shine {
    0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
    100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
}

/* Smooth message animations */
.message {
    animation: fadeSlideIn 0.3s ease-out;
}

@keyframes fadeSlideIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Thinking indicator */
.thinking {
    padding: 12px;
    background: var(--bg-tertiary);
    border-radius: 8px;
    margin-bottom: 8px;
    font-size: 13px;
    color: var(--text-secondary);
    font-style: italic;
}

/* Tool execution styles */
.tool-exec {
    color: var(--accent-blue);
    margin: 4px 0;
}

.tool-done {
    color: #1e8e3e;
    margin: 4px 0;
}

.tool-error {
    color: #d93025;
    margin: 4px 0;
}
```

### Priority 3: Architecture

#### E. Unify Agents/Skills/Workflows
**Goal:** Single "Agents" concept replacing all three

**New File:** `src/core/unified_agents.py`
```python
class UnifiedAgent:
    """
    Single concept replacing Skills, Workflows, and Agents.
    Each agent has:
    - Capabilities (what it can do)
    - Workflows (how to do things)
    - Personality (system prompt)
    """
    id: str
    name: str
    icon: str
    description: str
    capabilities: List[str]
    workflows: List[Workflow]
    system_prompt: str
    knowledge_base: Optional[KnowledgeBase]
    
# Migration path:
# 1. Convert each Skill to a UnifiedAgent
# 2. Move workflows from business_workflows.py into agents
# 3. Keep MasterOrchestrator but simplify
# 4. Update UI to show only "Agents" (not Skills/Workflows separately)
```

#### F. Project Knowledge Base
**File:** `src/core/project_manager.py`

**Add to Project class:**
```python
@dataclass
class KnowledgeBase:
    files: List[str]  # File IDs
    instructions: str  # User-provided context
    embeddings: Optional[List] = None  # For semantic search

@dataclass
class Project:
    id: str
    name: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    chats: List[str] = field(default_factory=list)
    knowledge_base: KnowledgeBase = field(default_factory=lambda: KnowledgeBase([], ""))
    
    def add_knowledge_file(self, file_id: str):
        """Add file to project knowledge base"""
        if file_id not in self.knowledge_base.files:
            self.knowledge_base.files.append(file_id)
    
    def set_instructions(self, instructions: str):
        """Set project-specific instructions"""
        self.knowledge_base.instructions = instructions
    
    def move_chat(self, chat_id: str, from_project: Optional[str] = None):
        """Move chat from another project or add new"""
        if chat_id not in self.chats:
            self.chats.append(chat_id)
    
    def duplicate_chat_to(self, chat_id: str, target_project: 'Project'):
        """Duplicate chat to another project"""
        if chat_id in self.chats:
            target_project.chats.append(chat_id)
```

### Priority 4: Code Quality

#### G. Remove Duplicates
**Files with Redundancy:**
- `src/core/skills_system.py` + `src/core/business_workflows.py` + `src/core/master_agent.py`
  → Consolidate into unified_agents.py

- `src/tools/core.py` decorator duplication
  → Single @tool decorator

#### H. Better Error Handling
**Pattern to Apply Everywhere:**
```python
try:
    result = await execute_tool(...)
except SpecificError as e:
    logger.error(f"Tool failed: {e}")
    # Try fallback
    result = await fallback_strategy()
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise
```

## Testing Checklist

Before considering modernization complete:

- [ ] Streaming works in UI (see typing effect)
- [ ] Printify creates products successfully
- [ ] Otto doesn't ask permission unnecessarily
- [ ] UI looks like Gemini (fonts, colors, animations)
- [ ] Projects have knowledge base
- [ ] Chats can move between projects
- [ ] All integrations work reliably
- [ ] No duplicate code
- [ ] Proper error handling everywhere

## Estimated Time Remaining

- Fix Printify: 1-2 hours
- Update UI for streaming: 2-3 hours
- Make autonomous: 1 hour
- Gemini styling: 2-3 hours
- Unify architecture: 4-5 hours
- Project knowledge base: 2 hours
- Code cleanup: 2-3 hours

**Total:** ~15-20 hours of focused work

## Recommendation

**Do in this order:**
1. Fix Printify (makes integration actually work)
2. Update UI for streaming (dramatic UX improvement)
3. Make Otto autonomous (better behavior)
4. Apply Gemini styling (professional look)
5. Then tackle architecture if time permits

This gets you from "broken and confusing" to "polished and functional" in ~8-10 hours.

## Current Status

✅ Streaming backend implemented
✅ Research complete
✅ Comprehensive plan documented
🚧 UI needs streaming consumer
🚧 Printify needs fixing
🚧 Prompts need autonomy update
🚧 CSS needs Gemini styling

**You're about 40% done with the full modernization.**
