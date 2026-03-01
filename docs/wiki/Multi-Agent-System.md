# Multi-Agent System

Otto Chat uses a sophisticated multi-agent system that combines patterns from CrewAI, Claude SDK, AutoGPT, Browser-Use, and AgentOps into a unified framework.

---

## Overview

The multi-agent system enables Otto to break down complex tasks, delegate to specialized agents, execute in parallel where possible, and verify results — all autonomously.

```
┌──────────────────────────────────────────────────┐
│              Agent Orchestrator                    │
│   (Central brain — routes, classifies, decides)   │
└──────────┬──────────────┬────────────────────────┘
           │              │
     ┌─────▼─────┐ ┌─────▼──────┐
     │  Planning  │ │  Execution │
     │   Agent    │ │   Agent    │
     └─────┬─────┘ └─────┬──────┘
           │              │
     ┌─────▼──────────────▼────────────────────────┐
     │           Unified Agent System               │
     │  ┌────────┐ ┌──────────┐ ┌──────────────┐   │
     │  │Planner │ │Researcher│ │  Verifier    │   │
     │  └────────┘ └──────────┘ └──────────────┘   │
     │  ┌────────┐ ┌──────────┐ ┌──────────────┐   │
     │  │Executor│ │ Analyzer │ │Tool Specialist│  │
     │  └────────┘ └──────────┘ └──────────────┘   │
     └─────────────────────────────────────────────┘
```

---

## Agent Roles

| Role | Responsibility |
|------|---------------|
| **Orchestrator** | Top-level coordination, request classification, agent selection |
| **Planner** | Breaks complex tasks into steps with dependencies |
| **Executor** | Runs individual steps, manages tool calls |
| **Researcher** | Information gathering, web search, competitive analysis |
| **Analyzer** | Data analysis, pattern recognition, insight extraction |
| **Verifier** | Result validation, quality checks, error detection |
| **Memory** | Context management, knowledge retrieval, pattern learning |
| **Tool Specialist** | Expert tool selection and parameter optimization |
| **Vision** | Image understanding, visual inspection, screenshot analysis |

---

## Execution Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **Autonomous** | Full self-directed execution — Otto plans, executes, and verifies without user input | "Launch a new product line of nature wall art" |
| **Interactive** | Asks for user confirmation at key decision points | "Create a marketing campaign" (confirms strategy) |
| **Collaborative** | Works alongside the user, suggesting next steps | Brainstorming sessions, iterative design |
| **Supervised** | Executes but shows detailed progress and allows intervention | Complex operations where oversight is desired |

---

## Task Lifecycle

```
PENDING → PLANNING → EXECUTING → VERIFYING → COMPLETED
                                      ↓
                                   FAILED
                                      ↓
                                   BLOCKED
```

| Status | Description |
|--------|-------------|
| `PENDING` | Task received, waiting to be processed |
| `PLANNING` | Super Planning Agent is creating the execution plan |
| `EXECUTING` | Steps are being executed (may include parallel execution) |
| `VERIFYING` | Results are being validated |
| `COMPLETED` | Task finished successfully |
| `FAILED` | Task failed (with error details and retry info) |
| `BLOCKED` | Task blocked by a dependency or external condition |

---

## Agent Orchestrator

The `agent_orchestrator.py` (1825 lines) is the central brain:

### Request Classification

Every incoming message is classified as either:
- **Action** — Requires tool execution (image generation, product creation, research, etc.)
- **Question** — Requires conversational response (chat, explanation, advice)

### Browser vs Research Detection

For research-type requests, the orchestrator further classifies:
- **Browser Use** — When direct web browsing and interaction is needed
- **Deep Research** — When API-based search and analysis is sufficient

### Agent Delegation

Specialized agents are selected based on task domain:
- **Content Agent** — Blog posts, social media, email campaigns
- **Image Agent** — Image generation, editing, background removal
- **Video Agent** — Video generation, commercial production
- **Research Agent** — Web search, competitive analysis
- **Analytics Agent** — Data analysis, reporting
- **E-Commerce Agent** — Printify, Shopify operations

---

## Super Planning Agent

The Super Planning Agent uses Claude Opus 4 to create detailed execution plans:

### Plan Structure

```json
{
  "goal": "Create 3 t-shirt designs with sunset themes",
  "steps": [
    {
      "id": 1,
      "action": "generate_image",
      "params": {"prompt": "sunset beach tropical", "aspect_ratio": "1:1"},
      "parallel_group": "A"
    },
    {
      "id": 2,
      "action": "generate_image",
      "params": {"prompt": "sunset mountain golden hour", "aspect_ratio": "1:1"},
      "parallel_group": "A"
    },
    {
      "id": 3,
      "action": "generate_image",
      "params": {"prompt": "sunset desert silhouette", "aspect_ratio": "1:1"},
      "parallel_group": "A"
    },
    {
      "id": 4,
      "action": "create_printify_product",
      "params": {"image": "${step_1.output}", "title": "Tropical Sunset Tee"},
      "depends_on": [1],
      "parallel_group": "B"
    },
    {
      "id": 5,
      "action": "create_printify_product",
      "params": {"image": "${step_2.output}", "title": "Mountain Sunset Tee"},
      "depends_on": [2],
      "parallel_group": "B"
    },
    {
      "id": 6,
      "action": "create_printify_product",
      "params": {"image": "${step_3.output}", "title": "Desert Sunset Tee"},
      "depends_on": [3],
      "parallel_group": "B"
    }
  ]
}
```

### Key Features

- **Parallel Groups** — Steps in the same group execute concurrently
- **Dependencies** — Steps can depend on outputs from previous steps
- **Variable Interpolation** — `${step_N.output}` references prior step outputs
- **Context Preservation** — Remembers user preferences (models, styles, aspect ratios)
- **Batch Operations** — Creates multiple products efficiently

---

## Execution Agent

The Execution Agent runs the plan step-by-step:

1. **Topological Sort** — Orders steps respecting dependencies
2. **Parallel Execution** — Runs independent steps concurrently
3. **Output Chaining** — Passes outputs from completed steps to dependent steps
4. **Error Handling** — Retries failed steps with intelligent backoff
5. **Progress Reporting** — Sends real-time progress updates to the client

---

## Enhanced Intelligence

The Enhanced Intelligence layer wraps the chat interface with:

### Advanced Reasoning Engine
- Activates for queries above a complexity threshold
- Uses multi-strategy reasoning (chain-of-thought, decomposition, analogical)
- Selects the best reasoning approach per query

### Proactive Intelligence
- Analyzes conversation context to anticipate needs
- Suggests follow-up actions before the user asks
- Monitors for opportunities (e.g., "You created 3 designs — want to publish them?")

### Smart Tool Router
- Analyzes the request to determine which tools are needed
- Considers tool availability, cost, and expected quality
- Composes tool chains for multi-step operations

### Self-Improvement Loop
- Captures outcomes from every interaction
- Identifies successful and unsuccessful patterns
- Gradually improves tool selection, parameter tuning, and response quality

---

## Autonomous Business Orchestrator

For fully autonomous business operations, the `autonomous_orchestrator.py` provides:

### Business Domains

| Domain | Operations |
|--------|-----------|
| E-commerce | Product creation, inventory, pricing, listings |
| Marketing | Campaigns, content, social media, email |
| Content Creation | Blog, video, audio, design |
| Data Analysis | Reports, dashboards, insights |
| Customer Service | Response generation, issue resolution |
| Product Development | Design iterations, user feedback |
| Operations | Scheduling, automation, monitoring |
| Finance | Revenue tracking, cost analysis |

### KPI Tracking

The autonomous orchestrator tracks business KPIs and optimizes operations:
- Revenue metrics
- Content performance
- Customer engagement
- Operational efficiency
- Brand consistency

---

## Agent Communication

Agents communicate through an inter-agent message bus (`agent_communication.py`):

- **Publish/Subscribe** — Agents subscribe to relevant topics
- **Direct Messaging** — Point-to-point agent communication
- **Broadcast** — System-wide notifications
- **Priority Queues** — Urgent messages processed first

---

## Agent Health Monitoring

The `agent_health_monitor.py` tracks:

- Agent uptime and availability
- Response latencies
- Error rates and failure patterns
- Resource consumption
- Task completion rates

Access health metrics via `/health/detailed` or the Intelligence dashboard.
