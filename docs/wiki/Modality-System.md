# Modality System

The Modality System is Otto's approach to intelligently selecting the right AI model for every task.

---

## Overview

Before selecting an AI model, Otto first determines the **output modality** — what type of content the user wants. This ensures the optimal model is always chosen for the job.

```
User Request → Detect Modality → Select Best Model → Execute → Return Result
```

---

## Supported Modalities

| Modality | Description | Example Request |
|----------|-------------|----------------|
| `TEXT` | Written content | "Write a blog post about..." |
| `IMAGE` | Visual content | "Generate an image of..." |
| `VIDEO` | Video content | "Create a video showing..." |
| `AUDIO` | Audio content | "Generate music for..." |
| `CODE` | Programming code | "Write a Python function..." |
| `VISION` | Image understanding | "What's in this image?" |
| `MULTIMODAL` | Multiple output types | "Create a product with image and description" |
| `3D` | 3D assets | "Generate a 3D model of..." |
| `DATA` | Structured data | "Analyze this dataset..." |

---

## Model Prioritization

For each modality, models are prioritized in this order to optimize for cost and speed:

```
1. Local Models (Ollama)    — Free, fast, no API calls
2. Remote APIs (Anthropic, OpenAI) — Reliable, high quality
3. Replicate               — Wide model selection, pay-per-use
```

### Per-Modality Model Selection

| Modality | Primary | Secondary | Fallback |
|----------|---------|-----------|----------|
| TEXT | Claude Opus 4 / Sonnet | GPT-4 Turbo | Ollama (local) |
| IMAGE | Flux Pro 1.1 | SDXL, Recraft V3 | Other Replicate models |
| VIDEO | Runway Gen-3 | Luma, Minimax | Kling |
| AUDIO | MusicGen | Audio models | — |
| CODE | Claude Opus 4 | GPT-4 Turbo | Ollama CodeLlama |
| VISION | Claude (vision) | GPT-4 Vision | — |

---

## Smart Features

### Dynamic Model Discovery

Otto can dynamically discover and use new models on Replicate without code changes. The modality system queries available models and selects the best one.

### Intelligent Retry

When a model fails, the system:
1. **Analyzes the failure** — Rate limit? Timeout? Invalid input?
2. **Selects alternative** — Picks a different model for the same modality
3. **Adjusts parameters** — May simplify the prompt or adjust settings
4. **Retries intelligently** — Exponential backoff for rate limits, immediate retry for transient errors

### Cost Optimization

The system tracks model costs and can optimize for budget:
- Prefer local models when available
- Use faster/cheaper models for iteration
- Reserve premium models for final output
- Batch operations to reduce API calls

---

## Configuration

```env
# Primary model for text tasks
DEFAULT_AI_MODEL=claude-sonnet-4-20250514

# Fallback when primary fails
FALLBACK_AI_MODEL=gpt-4-turbo

# Max retries per model
MAX_TOOL_RETRIES=3

# Timeout for model calls (seconds)
TOOL_TIMEOUT_SECONDS=300
```

---

## How It Works Internally

The `modality_system.py` module (796 lines) implements:

1. **Modality Detection** — Analyzes the user request to determine output type
2. **Model Registry** — Maintains a registry of available models per modality
3. **Priority Scoring** — Scores models based on quality, speed, cost, and availability
4. **Selection Algorithm** — Picks the best model considering constraints
5. **Fallback Chain** — Maintains ordered fallback list per modality
6. **Usage Tracking** — Monitors model reliability and performance over time
