# 🚀 Otto Universal - Modern Agentic Architecture

## Overview

Otto Universal now implements **production-grade agentic patterns** based on Anthropic's Claude Agent SDK best practices and modern autonomous agent design.

## Architecture

### Agent Loop Pattern
```
Context → Plan → Execute → Verify → Learn
```

### Core Agents

#### 1. **Planner Agent** (`super_planning_agent.py`)
- **Role**: Strategic task decomposition
- **Capabilities**:
  - Multi-strategy problem solving
  - Adaptive plan modification
  - Failure recovery
  - Tool discovery and selection
- **Permissions**: Read-only, analysis tools
- **Output**: Executable plan with dependencies

#### 2. **Executor Agent** (`execution_agent.py`)
- **Role**: Tool invocation and action execution
- **Capabilities**:
  - Tool execution with automatic retry
  - Smart fallback strategies
  - Context propagation
  - Artifact collection
- **Permissions**: Full tool access (with verification)
- **Output**: Execution results and artifacts

#### 3. **Verifier Agent** (`verifier_agent.py`) ✨ NEW
- **Role**: Quality assurance and validation
- **Capabilities**:
  - Result verification against success criteria
  - Error and inconsistency detection
  - Correction suggestions
  - Confidence scoring
- **Permissions**: Read-only verification tools
- **Output**: Verification status and corrections

#### 4. **Memory Agent** (`memory_agent.py`)
- **Role**: Context management and learning
- **Capabilities**:
  - ChromaDB integration for long-term memory
  - Relevant memory retrieval
  - Learning persistence
- **Permissions**: Memory operations only
- **Output**: Relevant memories and insights

### Supporting Systems

#### Context Manager (`context_manager.py`) ✨ NEW
**Purpose**: Prevent "context rot" in long-running agents

Features:
- Short-term memory (last 10 interactions)
- Long-term memory (ChromaDB)
- Automatic context pruning
- Artifact references (not full content)
- Session isolation

#### Permission Manager (`permission_manager.py`) ✨ NEW
**Purpose**: Tool access control and safety

Features:
- 5-level permission system
- Budget tracking and enforcement
- Rate limiting
- Prerequisite checking
- Audit logging

#### Agent Logger (`agent_logger.py`) ✨ NEW
**Purpose**: Execution tracing and debugging

Features:
- Structured event logging
- Decision point tracking
- Tool invocation recording
- Replay capability
- Performance analytics

## Skills System ✨ NEW

Skills are reusable capability packages defined in `SKILL.md` files:

### Available Skills

1. **Business Operations** (`skills/business_operations/SKILL.md`)
   - Product creation
   - E-commerce management
   - Marketing campaigns
   - Analytics

2. **Research & Analysis** (`skills/research_analysis/SKILL.md`)
   - Market research
   - Competitor analysis
   - Web research
   - Data analysis

3. **Content Creation** (`skills/content_creation/SKILL.md`)
   - Blog posts
   - Social media
   - Email campaigns
   - Ad copy

### Creating New Skills

```bash
mkdir -p skills/my_skill
cat > skills/my_skill/SKILL.md << EOF
# My Skill

**Skill ID**: \`my_skill\`
**Version**: 1.0
**Category**: Your Category

## Description
What this skill does...

## Capabilities
- Capability 1
- Capability 2

## Tools Required
- tool_1
- tool_2

## Success Criteria
- ✅ Criterion 1
- ✅ Criterion 2
EOF
```

## Safety & Permissions

### Tool Access Levels

- **Level 1**: Safe read-only (free execution)
- **Level 2**: Safe write (auto-approve)
- **Level 3**: Moderate risk (budget check)
- **Level 4**: High impact (verification required)
- **Level 5**: Dangerous (explicit confirmation)

See `policies/permissions.yaml` for full configuration.

### Safety Rules

- Temporal constraints (authenticate before accessing)
- Budget limits (daily/monthly)
- Rate limiting (per tool/service)
- Audit trail for all operations
- Kill switch protocol

See `policies/safety_rules.md` for details.

## System Manifest

The `CLAUDE.md` file at project root defines:
- Agent capabilities
- Context discipline rules
- Tool permissions
- Safety constraints
- Operational patterns
- Quality standards

This serves as the "constitution" for the agent system.

## Usage Examples

### Basic Request Flow

```python
from src.core import AgentOrchestrator

# Initialize with permissions and context management
orchestrator = AgentOrchestrator(
    anthropic_api_key="...",
    config={...}
)

# Process request with full agent loop
result = await orchestrator.process(
    message="Create 3 t-shirt designs with mountain themes",
    session_id="user_123"
)

# Result includes:
# - response: Natural language summary
# - plan: Execution plan created
# - results: Tool execution outputs
# - artifacts: Generated files/images
# - verification: Quality check results
```

### With Business Context

```python
from src.core.autonomous_orchestrator import AutonomousOrchestrator, BusinessContext

orchestrator = AutonomousOrchestrator(...)

result = await orchestrator.execute_business_request(
    request="Launch a new product line",
    session_id="biz_456",
    business_context=BusinessContext(
        domain="ecommerce",
        goals=["Create 5 products", "Generate marketing"],
        budget=500.0
    )
)

# Includes KPI tracking, impact analysis, reasoning chain
```

## Logging & Debugging

### View Execution Traces

```python
from src.core import AgentLogger

logger = AgentLogger()

# Analyze a trace
analysis = logger.analyze_trace("trace_20260128_120000_abc123")

# Shows:
# - Total duration
# - Tool calls and costs
# - Errors encountered
# - Decision confidence
# - Performance bottlenecks
```

### Replay for Debugging

```python
# Replay step-by-step
events = logger.replay_trace("trace_id")

for event in events:
    print(f"{event['timestamp']}: {event['event_type']}")
    print(f"  Data: {event['data']}")
```

## Context Management

### Automatic Pruning

Context is automatically pruned to prevent degradation:
- Keep last 10 interactions
- Summarize older context
- Extract key facts to global state
- Reference artifacts by ID, not content

### Manual Management

```python
from src.core import ContextManager

context_mgr = ContextManager(memory_agent)

# Get optimized context for agent
context = context_mgr.get_context_for_agent(
    session_id="user_123",
    agent_type="planner"
)

# Manually prune if needed
context_mgr.prune_session("user_123")

# Cleanup old sessions
cleaned = context_mgr.cleanup_old_sessions(max_age_hours=24)
```

## Performance Metrics

### Target Performance

- Simple queries: < 3 seconds
- Tool execution: < 30 seconds
- Complex workflows: < 5 minutes
- Business operations: < 15 minutes

### Budget Tracking

```python
from src.core import PermissionManager

perm_mgr = PermissionManager()

# Check budget status
status = perm_mgr.get_budget_status()
# {
#   "daily_limit": 50.00,
#   "spent_today": 12.50,
#   "remaining_today": 37.50,
#   "usage_percent": 25.0
# }
```

## Migration Guide

### From Old Architecture

If you have existing code using the old orchestrator:

**Before:**
```python
orchestrator = AgentOrchestrator(api_key)
result = await orchestrator.process(message)
```

**After:**
```python
# Same interface! Just with better internals
orchestrator = AgentOrchestrator(api_key)
result = await orchestrator.process(message)

# Now includes verification, logging, permissions, context management
```

### New Capabilities Available

- Access verification results: `result.get("verification")`
- View execution trace: `result.get("trace_id")`
- Check tool permissions: `orchestrator.permission_manager.check_permission(...)`
- Analyze context usage: `orchestrator.context_manager.get_stats()`

## Best Practices

### 1. Use Skills for Reusable Capabilities
Define `SKILL.md` files instead of embedding logic in prompts.

### 2. Leverage Subagents
Let Planner, Executor, and Verifier work in sequence for complex tasks.

### 3. Monitor Context Size
Use Context Manager stats to prevent context rot:
```python
stats = context_mgr.get_stats()
if stats["total_tokens"] > 80000:
    context_mgr.prune_session(session_id)
```

### 4. Review Traces for Optimization
Regularly analyze traces to find bottlenecks:
```python
analysis = agent_logger.analyze_trace(trace_id)
# Check "slowest_tools" to optimize
```

### 5. Set Appropriate Permissions
Configure `policies/permissions.yaml` for your use case.

## Directory Structure

```
otto-universal/
├── CLAUDE.md                 # System manifest
├── skills/                   # Reusable capabilities
│   ├── business_operations/
│   ├── research_analysis/
│   └── content_creation/
├── policies/                 # Safety and permissions
│   ├── safety_rules.md
│   └── permissions.yaml
├── logs/
│   └── agent_traces/        # Execution logs
├── src/core/                # Core agents
│   ├── agent_orchestrator.py
│   ├── super_planning_agent.py
│   ├── execution_agent.py
│   ├── verifier_agent.py    # ✨ NEW
│   ├── memory_agent.py
│   ├── context_manager.py   # ✨ NEW
│   ├── permission_manager.py # ✨ NEW
│   └── agent_logger.py      # ✨ NEW
└── docs/                    # Documentation
    ├── ARCHITECTURE.md
    └── GETTING_STARTED.md
```

## Contributing

When adding new capabilities:

1. Create a `SKILL.md` file in `skills/`
2. Update `policies/permissions.yaml` for new tools
3. Add tests and validation
4. Document in skills README

## References

- [Anthropic Agent SDK](https://docs.anthropic.com/claude/docs/agent-sdk)
- [Agent Skills Guide](https://docs.anthropic.com/claude/docs/agent-skills)
- [Building Agents with Claude](https://www.anthropic.com/news/building-agents)

---

**Version**: 2.0  
**Last Updated**: January 28, 2026  
**Architecture**: Production-Grade Agentic System
