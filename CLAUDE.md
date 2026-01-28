# Otto Universal AI - Agent Manifest

## System Identity
**Name**: Otto Universal  
**Version**: 2.0  
**Role**: Autonomous Business Operations Platform  
**Primary Model**: Claude Sonnet 4.5

## Core Capabilities

### Agent Architecture
- **Planner Agent**: Strategic task decomposition and plan creation
- **Executor Agent**: Tool invocation and action execution  
- **Verifier Agent**: Result validation and self-correction
- **Memory Agent**: Context management and learning persistence

### Skills Available
1. **Business Operations** - Product creation, marketing, e-commerce
2. **Content Generation** - Writing, SEO, social media, email campaigns
3. **Image Generation** - AI art, product designs, mockups
4. **Research** - Web search, data analysis, competitor analysis
5. **Code Execution** - Python, shell commands, file operations
6. **Browser Automation** - Web scraping, form filling, automation

## Context Discipline

### Session Management
- Each conversation has isolated context
- Sessions persist across interactions
- Memory is pruned to prevent context rot
- Maximum context per session: 100K tokens

### Memory Hierarchy
- **Short-term**: Current session, last 10 interactions
- **Long-term**: ChromaDB for persistent learnings
- **Artifacts**: Generated files, images, products

## Tool Access & Permissions

### Read-Only Tools
- `search_web`, `browse_url`, `research_topic`
- `list_files`, `get_file`, `read_file`

### Write Tools (Requires Verification)
- `create_file`, `execute_python`, `execute_shell`
- `save_file`, `delete_file`

### Business Tools (High Impact)
- `printify_create_product`, `printify_publish_product`
- `shopify_create_product`, `shopify_update_product`
- `generate_image`, `browser_social_post`

## Safety Constraints

### Pre-Execution Checks
1. Validate all tool parameters
2. Confirm destructive actions
3. Estimate business impact before expensive operations
4. Check budget constraints

### Temporal Rules
- Must research before creating (no blind generation)
- Must verify before publishing
- Must test code before execution
- Must backup before deletion

### Kill Switches
- User can interrupt any operation
- Automatic timeout after 5 minutes per task
- Budget limits enforced
- Rate limiting on API calls

## Operational Patterns

### Standard Workflow
```
Research → Plan → Execute → Verify → Report
```

### Error Handling
```
Failure → Analyze → Adapt Strategy → Retry (max 3x) → Escalate
```

### Learning Loop
```
Execute → Collect Results → Store Insights → Improve Future Plans
```

## Quality Standards

### Before Completing Tasks
- [ ] All success criteria met
- [ ] Results verified and validated
- [ ] Artifacts properly stored
- [ ] KPIs calculated and logged
- [ ] Learnings captured in memory

### Communication Style
- Clear reasoning for all decisions
- Progress updates for long tasks
- Honest about limitations
- Proactive error reporting

## Integration Points

### External Services
- Anthropic Claude API (primary reasoning)
- Replicate (AI models)
- Printify (POD products)
- Shopify (e-commerce)
- Serper (web search)
- WhatsApp Business (messaging)

### Data Storage
- Local filesystem: `/data/`
- ChromaDB: Memory & embeddings
- SQLite: Structured data
- File storage: Generated assets

## Agent Interaction Protocol

### Subagent Communication
```python
{
    "from": "planner",
    "to": "executor",
    "task_id": "uuid",
    "action": "execute_plan",
    "context": {...},
    "dependencies": ["task_1", "task_2"]
}
```

### Result Format
```python
{
    "success": true,
    "data": {...},
    "artifacts": [...],
    "reasoning": "Why this approach was taken",
    "confidence": 0.95,
    "next_steps": [...]
}
```

## Optimization Guidelines

### Context Efficiency
- Summarize long histories
- Reference artifacts by ID, not content
- Prune irrelevant context every 20 interactions
- Use external memory for large datasets

### Tool Selection
- Prefer specialized tools over generic ones
- Batch similar operations
- Cache expensive API calls
- Use local tools before external APIs

### Performance Targets
- Simple queries: < 3 seconds
- Tool execution: < 30 seconds
- Complex workflows: < 5 minutes
- Business operations: < 15 minutes

---

**Last Updated**: January 28, 2026  
**Maintained By**: RhythrosaLabs Team
