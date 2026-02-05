# Otto Universal - Modernization Plan

## Research Insights

### Claude Agents SDK Best Practices
1. **Streaming First**: All responses should stream in real-time
2. **Tool Orchestration**: Agents should autonomously chain tools without asking
3. **Minimal Intervention**: Only check in when truly ambiguous
4. **Clear Reasoning**: Show thinking process but execute decisively
5. **Graceful Degradation**: Handle failures automatically with fallbacks

### Current Issues in Otto
1. **Conceptual Overlap**: Skills, Workflows, and Agents are essentially the same
2. **Too Many Check-ins**: Otto asks permission too often
3. **No Streaming**: Responses appear all at once
4. **Integration Failures**: Printify and others fail inconsistently
5. **UI/UX**: Doesn't match modern AI chat aesthetics (Gemini/Claude)

## Implementation Plan

### Phase 1: Streaming & Real-time (Priority 1)
- [ ] Implement SSE (Server-Sent Events) for streaming
- [ ] Add typing animation in UI
- [ ] Stream tool execution progress
- [ ] Show image generation progress
- [ ] Real-time artifact updates

### Phase 2: Unified Agent System (Priority 1)
- [ ] Consolidate Skills/Workflows/Agents into single "Agents" concept
- [ ] Each agent has capabilities (like skills) and workflows
- [ ] Simplified sidebar: just "Agents"
- [ ] Remove redundant systems

### Phase 3: Gemini-Style UI (Priority 2)
- [ ] Google Sans font family
- [ ] Color scheme: Blues, subtle grays, white backgrounds
- [ ] Metallic sheen on buttons and interactive elements
- [ ] Smooth animations (fade-ins, slides)
- [ ] Clean, minimal design
- [ ] Gradient backgrounds for different message types

### Phase 4: Enhanced Projects (Priority 2)
- [ ] Knowledge base per project (files + instructions)
- [ ] Move/duplicate chats across projects
- [ ] Project-specific agent settings
- [ ] Persistent context per project

### Phase 5: Autonomous Behavior (Priority 1)
- [ ] Stop asking "Should I...?" questions
- [ ] Execute plans without confirmation
- [ ] Only check-in for truly ambiguous decisions
- [ ] Better error recovery without user involvement
- [ ] Smarter fallback strategies

### Phase 6: Integration Reliability (Priority 1)
- [ ] Fix Printify workflow completely
- [ ] Better retry logic
- [ ] Validate all parameters before API calls
- [ ] Comprehensive error logging
- [ ] Test all integrations

### Phase 7: Code Quality (Ongoing)
- [ ] Remove duplicate code
- [ ] Consolidate similar functions
- [ ] Better error handling
- [ ] Comprehensive logging
- [ ] Type hints everywhere
- [ ] Documentation updates

## Technical Architecture Changes

### Streaming Implementation
```python
# New endpoint pattern
@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    async def generate():
        async for chunk in otto.process_streaming(request.message):
            yield f"data: {json.dumps(chunk)}\\n\\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
```

### Unified Agent Concept
```python
class Agent:
    id: str
    name: str
    description: str
    capabilities: List[str]  # What it can do (from old Skills)
    workflows: List[Workflow]  # How to do things (from old Workflows)
    system_prompt: str  # Personality (from old Agents)
    icon: str
    color: str
```

### Project Knowledge Base
```python
class Project:
    id: str
    name: str
    chats: List[str]  # Chat IDs
    knowledge_base: KnowledgeBase
        - files: List[File]
        - instructions: str  # User-provided context
        - settings: Dict
```

## Execution Order
1. ✅ Research (done)
2. Implement streaming responses
3. Refactor agent architecture
4. Update UI to Gemini style
5. Enhanced projects
6. Fix integrations
7. Code cleanup
8. Testing

## Success Criteria
- [ ] Responses stream in real-time like ChatGPT/Gemini
- [ ] Single "Agents" concept replaces skills/workflows/agents
- [ ] UI matches Gemini aesthetic
- [ ] Otto operates more autonomously
- [ ] All integrations work reliably
- [ ] No duplicate code or functions
- [ ] Clean, maintainable codebase
