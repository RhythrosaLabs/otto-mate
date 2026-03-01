# Smart Model Selection & Retry System

## Overview

Otto now has three powerful new systems that work together to make AI model selection intelligent, autonomous, and highly reliable:

1. **Smart Model Prioritization** - Intelligently selects local/remote models first, Replicate only when needed
2. **Dynamic Replicate Model Discovery** - Accesses ALL Replicate models dynamically, not just hardcoded ones
3. **Intelligent Retry System** - Analyzes failures, adjusts parameters, tries alternatives, minimizes human intervention

## Key Rules

### Model Selection Priority

**The system ALWAYS follows this priority:**

```
1. LOCAL MODELS (highest priority)
   ├─ Local FLUX (ComfyUI, local deployment)
   ├─ Local Stable Diffusion (Automatic1111, ComfyUI)
   ├─ Ollama (local LLMs)
   └─ vLLM (local model serving)

2. REMOTE API SERVICES (if no local available)
   ├─ DALL-E 3 (OpenAI - API-only, cannot be local)
   ├─ Claude (Anthropic - API-only, cannot be local)
   ├─ GPT-4 (OpenAI - API-only, cannot be local)
   ├─ Whisper (OpenAI - API-only, cannot be local)
   └─ ElevenLabs (API-only, cannot be local)

3. REPLICATE (only when)
   ├─ User explicitly requests "use replicate"
   └─ No local/remote models available for that modality
```

**Critical Distinction:**
- **API-only models** (DALL-E 3, Claude, GPT-4): Cannot be run locally, always require API key
- **Deployable models** (FLUX, SDXL, Stable Diffusion): Can run locally OR via Replicate
- **Local beats remote**: If you have FLUX running locally, it will be used instead of DALL-E 3 API

**Important:** Otto prioritizes LOCAL models first, then remote APIs, then Replicate as last resort.

### Understanding Model Types

There are two fundamentally different types of AI models:

**API-Only Models** (Cannot be run locally):
- **DALL-E 3** - OpenAI's image generation (API-only)
- **GPT-4** - OpenAI's language model (API-only)  
- **Claude** - Anthropic's language model (API-only)
- **Whisper** - OpenAI's audio transcription (API-only)
- **ElevenLabs** - Text-to-speech service (API-only)

These models ALWAYS require an API key and remote API call. They cannot be deployed locally.

**Deployable Models** (Can be local OR Replicate):
- **FLUX** - Can run via ComfyUI, local deployment, OR Replicate
- **SDXL** - Can run via ComfyUI, Automatic1111, OR Replicate
- **Stable Diffusion** - Can run locally OR Replicate
- **Llama** - Can run via Ollama locally OR Replicate
- **Mistral** - Can run via Ollama locally OR Replicate

These models CAN be deployed on your own hardware OR accessed via Replicate.

**Priority Logic for Image Generation:**
1. If you have FLUX running locally → Use local FLUX ✓ (highest priority)
2. If you only have OpenAI API key → Use DALL-E 3 (API-only service)
3. If you have neither → Use Replicate FLUX as fallback

### Retry Strategy

When something fails, Otto:
1. **Analyzes why it failed** (rate limit? bad params? model error?)
2. **Determines if retry is worthwhile** (some errors aren't worth retrying)
3. **Adjusts approach intelligently**:
   - Rate limit → Wait with exponential backoff
   - Invalid params → Adjust the parameters
   - Model error → Try a different model
   - Auth error → Give up (can't fix)
4. **Learns from patterns** - remembers what worked before
5. **Tries up to 5 times** before giving up

##Local Models** (checked via system/environment) - **HIGHEST PRIORITY**:
- Ollama models (if `ollama` command available)
  - Text models: Llama, Mistral, etc.
- vLLM models (if `VLLM_ENDPOINT` configured)
  - Text model serving
- ComfyUI (if `COMFYUI_ENDPOINT` configured)
  - Local FLUX, SDXL, Stable Diffusion
- Local FLUX (if `FLUX_ENDPOINT` configured)
  - Direct FLUX deployment
- Automatic1111/SD WebUI (if `SD_ENDPOINT` configured)
  - Stable Diffusion local deployment

**Remote API Services** (checked via API keys) - **SECOND PRIORITY**:
- Anthropic Claude (requires `ANTHROPIC_API_KEY`) - **API-only, cannot be local**
  - claude-sonnet-4, claude-opus-4, claude-3-5-sonnet, etc.
- OpenAI (requires `OPENAI_API_KEY`) - **API-only, cannot be local**
  - gpt-4o, gpt-4o-mini, gpt-4-turbo
  - **DALL-E 3** (API-only image generation)
  - **Whisper** (API-only audio transcription)
- ElevenLabs (requires `ELEVENLABS_API_KEY`) - **API-only, cannot be local**
  - eleven_multilingual_v2 for TTSctually available

#### Detected Models

**Remote Models** (checked via API keys):
- Anthropic Claude (requires `ANTHROPIC_API_KEY`)
  - claude-sonnet-4, claude-opus-4, claude-3-5-sonnet, etc.
- OpenAI (requires `OPENAI_API_KEY`)
  - gpt-4o, gpt-4o-mini, gpt-4-turbo, dall-e-3, whisper-1
- ElevenLabs (requires `ELEVENLABS_API_KEY`)
  - eleven_multilingual_v2 for TTS

**Local Models** (checked via system):
- Ollama models (if `ollama` command available)
- vLLM models (if `VLLM_ENDPOINT` configured)

**Replicate** (fallback only):
- Used ONLY when no local/remote models available
- Or when user explicitly says "use replicate"

#### Usage

```python
from src.core.smart_model_prioritization import get_prioritization_system

prioritizer = get_prioritization_system()

# Select model smartly
selection = prioritizer.select_model(
    modality="image",
    capabilities=["generation"],
    explicit_model=None,  # Or "dall-e-3" if user requested it
    prefer_speed=False,
    prefer_cost=False,
    quality_level="high"
)

print(f"Selected: {selection.model.name}")
print(f"Source: {selection.model.source}")  # LOCAL, REMOTE, or REPLICATE
print(f"Reason: {selection.reason}")
print(f"Replicate avoided: {selection.replicate_avoided}")
Local FLUX installed**
```
User: "Create an image of a sunset"

Otto detects:
- COMFYUI_ENDPOINT = set ✓
- Local FLUX available ✓
- OPENAI_API_KEY = set ✓ (but ignored)

Result: Uses local FLUX (LOCAL)
Reason: Local model beats remote API
DALL-E 3: NOT USED (local beats API-only services)
Replicate: NOT USED
```3: User explicitly requests

**Example 2: Only remote APIs available**
```
User: "Create an image of a sunset"

Otto detects:
- No local image models ✗
- OPENAI_API_KEY = set ✓
- dall-e-3 available ✓

Result: Uses dall-e-3 (REMOTE API
**Example 1: Remote models installed**
```
User: "Create an image of a sunset"

Otto detects:
- ANTHROPIC_API_KEY = set ✓
- OPENAI_API_KEY = set ✓
- dall-e-3 available ✓

Result: Us4s dall-e-3 (REMOTE)
Replicate: NOT USED
```

**Example 2: No remote models, but user asks for Replicate**
```
User: "Create an image of a sunset using replicate"

Otto detects:
- "replicate" explicitly mentioned ✓

Result: Uses Replicate (EXPLICIT REQUEST)
Reason: User explicitly requested Replicate
```

**Example 3: No models available**
```
User: "Create an image of a sunset"

Otto detects:
- No API keys set ✗
- No local models ✗

Result: Uses Replicate (FALLBACK)
Reason: No local/remote models available
```

### 2. Dynamic Replicate Model Discovery

**File:** `src/core/replicate_model_registry.py`

#### What It Does
- Discovers ALL Replicate models dynamically (not hardcoded)
- Categorizes by modality (text, image, video, audio, etc.)
- Detects capabilities automatically
- Caches results for performance
- Finds the best model for your specific need

#### How It Works

1. **Searches by modality** - Looks for models that match your need
2. **Searches collections** - Browses Replicate's model collections
3. **Gets featured models** - Includes popular, well-tested models
4. **Scores models** - Ranks by popularity, recency, performance
5. **Filters smartly** - Only shows models matching your criteria

#### Usage

```python
from src.core.replicate_model_registry import get_replicate_registry
from src.core.replicate_model_registry import ReplicateModality, ModelSearchCriteria

registry = get_replicate_registry()

# Discover models for a modality
criteria = ModelSearchCriteria(
    modality=ReplicateModality.IMAGE,
    capabilities=["generation"],
    max_cost=1.0,  # Max cost per run
    min_popularity=10.0
)

models = await registry.discover_models(criteria)

for model in models[:5]:
    print(f"{model.full_name}")
    print(f"  Modality: {model.modality.value}")
    print(f"  Capabilities: {model.capabilities}")
    print(f"  Popularity: {model.popularity_score}")
    print()

# Get best model for a task
best = await registry.get_best_model_for_task(
    modality=ReplicateModality.VIDEO,
    capabilities=["generation"],
    prefer_speed=True
)

print(f"Best video model: {best.full_name}")
```

#### Modality Detection

The registry automatically detects modalities from model names/descriptions:

- **TEXT**: llm, language, gpt, llama, mistral, claude
- **IMAGE**: image, diffusion, sdxl, flux, dalle, midjourney
- **VIDEO**: video, animation, gen-3, runway
- **AUDIO**: audio, music, tts, speech, musicgen, whisper
- **MULTIMODAL**: vision, vlm, llava, cogvlm
- **CODE**: code, programming, codegen, starcoder
- **3D**: 3d, mesh, shape, model
- **EMBEDDING**: embedding, encoder, vector

#### Capability Detection

Automatically detects what models can do:

- **generation**: generate, create, synthesis
- **editing**: edit, modify, transform, inpaint
- **upscaling**: upscale, super-resolution, enhance
- **style_transfer**: style, transfer, artistic
- **segmentation**: segment, mask, detect
- **classification**: classify, categorize, predict
- **translation**: translate, convert
- **summarization**: summarize, condense
- **qa**: question, answer
- **chat**: chat, conversation, dialogue
- **analysis**: analyze, understand, interpret

### 3. Intelligent Retry System

**File:** `src/core/intelligent_retry_system.py`

#### What It Does
- Analyzes WHY something failed
- Determines IF it's worth retrying
- Applies the RIGHT retry strategy
- Learns from patterns over time
- Minimizes need for human intervention

#### Failure Types Detected

The system recognizes 12 types of failures:

1. **RATE_LIMIT** - Hit API rate limit → Wait with backoff
2. **TIMEOUT** - Request timed out → Adjust timeout params
3. **INVALID_PARAMS** - Bad parameters → Fix the parameters
4. **MODEL_ERROR** - Model failed → Try different model
5. **API_ERROR** - Service error → Retry with backoff
6. **AUTH_ERROR** - Bad API key → Give up (can't fix)
7. **QUOTA_EXCEEDED** - Out of credits → Try different model
8. **MODEL_UNAVAILABLE** - Model not found → Try alternative
9. **INVALID_INPUT** - Safety filter → Adjust input
10. **SERVER_ERROR** - Server issue → Retry with backoff
11. **NETWORK_ERROR** - Network problem → Retry immediately
12. **UNKNOWN** - Unknown error → Conservative approach

#### Retry Strategies

Based on the failure type, the system applies one of these strategies:

1. **IMMEDIATE** - Retry right away (network errors)
2. **BACKOFF** - Wait with exponential backoff (rate limits, server errors)
3. **ADJUST_PARAMS** - Change parameters and retry (invalid params, timeouts)
4. **ALTERNATIVE_MODEL** - Try a different model (model errors, unavailable)
5. **GIVE_UP** - Stop trying (auth errors, unfixable issues)

#### Usage

```python
from src.core.intelligent_retry_system import get_retry_system

retry_system = get_retry_system()

async def my_ai_operation(prompt, model):
    # Your AI operation that might fail
    return await call_ai_api(prompt, model)

# Execute with intelligent retry
result = await retry_system.execute_with_retry(
    operation=my_ai_operation,
    operation_args={"prompt": "Create an image..."},
    modality="image",
    original_model="flux-pro",
    alternative_models=["flux-dev", "sdxl", "dalle-3"],
    model_selector=lambda mod, exclude: get_alternatives(mod, exclude)
)

if result.success:
    print(f"✓ Success after {len(result.attempts)} attempts")
    print(f"Final model: {result.final_model_used}")
    print(f"Total duration: {result.total_duration:.1f}s")
    print(f"Output: {result.final_output}")
else:
    print(f"✗ Failed after {len(result.attempts)} attempts")
    print(f"Reason: {result.gave_up_reason}")

# Review attempts
for attempt in result.attempts:
    print(f"Attempt {attempt.attempt_number}:")
    print(f"  Strategy: {attempt.strategy}")
    print(f"  Model: {attempt.model_used}")
    print(f"  Success: {attempt.success}")
    if not attempt.success:
        print(f"  Error: {attempt.error[:100]}")
```

#### Example Retry Scenarios

**Scenario 1: Rate Limit**
```
Attempt 1: flux-pro → Rate limit (429)
Analysis: Rate limit detected
Strategy: Exponential backoff
Wait: 4 seconds
Attempt 2: flux-pro → Success ✓
```

**Scenario 2: Model Error**
```
Attempt 1: custom-model → Model overloaded
Analysis: Model error detected
Strategy: Try alternative model
Attempt 2: flux-dev → Success ✓
```

**Scenario 3: Invalid Parameters**
```
Attempt 1: sdxl → "prompt too long" error
Analysis: Invalid params detected
Strategy: Adjust parameters
Adjustments: max_tokens=4000, truncate_prompt=True
Attempt 2: sdxl → Success ✓
```

**Scenario 4: Multiple Failures**
```
Attempt 1: model-a → Model unavailable
Strategy: Try alternative
Attempt 2: model-b → Rate limit
Strategy: Backoff (wait 4s)
Attempt 3: model-b → Invalid params
Strategy: Adjust params
Attempt 4: model-b → Success ✓
```

#### Learning from Patterns

The retry system learns over time:

```python
# After several successful retries, the system knows:
# "When flux-pro fails with rate limit, flux-dev usually works"

stats = retry_system.get_stats()
print(stats)
# {
#   "total_failures": 45,
#   "total_successes_after_retry": 38,
#   "failure_types": {
#     "rate_limit": 20,
#     "model_error": 12,
#     "invalid_params": 8,
#     ...
#   },
#   "success_patterns": {
#     "image": 15,  # 15 successful retries for images
#     "video": 10,
#     ...
#   }
# }
```

## Integration

### In Modality System

The modality system (`modality_system.py`) now integrates all three systems:

```python
# When selecting a model:
# 1. Check smart prioritization first
# 2. Use Replicate discovery if needed
# 3. Wrap execution in retry system

mapper = get_modality_mapper()

model = mapper.select_model(
    modality=Modality.IMAGE,
    quality_level="high",
    explicit_model=None,
    user_input="Create an image of a cat"  # Checks for "replicate"
)

# Result follows priority rules:
# - Uses remote model if available
# - Uses Replicate only if:
#   * User said "replicate"
#   * No remote models available
```

### In Enhanced Workflow

The enhanced workflow orchestrator uses these systems automatically:

```python
# Stage 3: Model Selection uses smart prioritization
modality_model_mapping = self.modality_mapper.select_models_for_requirements(
    detected_modalities, 
    context,
    user_request  # Passed to check for "replicate"
)

# When executing:
# - Smart prioritization selects best model
# - Retry system handles any failures
# - Replicate discovery finds alternatives if needed
```

## Configuration

### Environment Variables

```bash
# Local Models (HIGHEST PRIORITY - checked first)
COMFYUI_ENDPOINT=http://localhost:8188    # ComfyUI for FLUX, SDXL, SD
COMFYUI_URL=http://localhost:8188         # Alternative name
FLUX_ENDPOINT=http://localhost:7860       # Direct FLUX deployment
FLUX_LOCAL=http://localhost:7860          # Alternative name
SD_ENDPOINT=http://localhost:7860         # Automatic1111/SD WebUI
AUTOMATIC1111_URL=http://localhost:7860   # Alternative name
VLLM_ENDPOINT=http://localhost:8000       # vLLM text model serving
# Ollama detected automatically if installed

# Remote API Services (API-only - checked second)
ANTHROPIC_API_KEY=sk-ant-...    # Enables Claude models (API-only)
OPENAI_API_KEY=sk-...           # Enables GPT-4, DALL-E 3, Whisper (API-only)
ELEVENLABS_API_KEY=...          # Enables ElevenLabs TTS (API-only)

# Replicate (fallback only - used last)
REPLICATE_API_TOKEN=r8_...      # Used only when needed

# Retry System
RETRY_MAX_ATTEMPTS=5            # Max retry attempts (default: 5)
RETRY_MAX_DURATION=300          # Max seconds to retry (default: 300)
RETRY_ENABLE_LEARNING=true      # Enable learning from patterns
```

### Programmatic Configuration

```python
# Configure retry system
from src.core.intelligent_retry_system import get_retry_system

retry = get_retry_system(
    max_retries=10,
    max_total_duration=600,
    enable_learning=True
)

# Configure Replicate registry
from src.core.replicate_model_registry import get_replicate_registry

registry = get_replicate_registry(
    api_token="r8_your_token",
    cache_duration=3600  # Cache for 1 hour
)

# Force model rescan
from src.core.smart_model_prioritization import get_prioritization_system

prioritizer = get_prioritization_system()
prioritizer.force_rescan()  # Rescan for new models
```

## Testing

### Test Smart Prioritization

```python
from src.core.smart_model_prioritization import get_prioritization_system

prioritizer = get_prioritization_system()

# Check what's installed
stats = prioritizer.get_stats()
print(f"Remote models: {stats['remote_models_enabled']}")
print(f"Local models: {stats['local_models_enabled']}")
print(f"Total: {stats['total_models']}")
print(f"By source: {stats['by_source']}")

# Test model selection
selection = prioritizer.select_model(
    modality="image",
    prefer_speed=True
)
print(f"Selected: {selection.model.name} ({selection.model.source})")
print(f"Replicate avoided: {selection.replicate_avoided}")
```

### Test Replicate Discovery

```python
from src.core.replicate_model_registry import get_replicate_registry, ReplicateModality

registry = get_replicate_registry()

# Discover image models
models = await registry.discover_models(
    criteria=ModelSearchCriteria(modality=ReplicateModality.IMAGE)
)

print(f"Found {len(models)} image models")
for model in models[:5]:
    print(f"- {model.full_name} (popularity: {model.popularity_score})")
```

### Test Retry System

```python
from src.core.intelligent_retry_system import get_retry_system

retry = get_retry_system()

async def failing_operation(prompt, model):
    # Simulate failures
    import random
    if random.random() < 0.5:
        raise Exception("Rate limit exceeded")
    return {"success": True, "output": "Generated image"}

result = await retry.execute_with_retry(
    operation=failing_operation,
    operation_args={"prompt": "test"},
    modality="image",
    original_model="test-model",
    alternative_models=["backup-model"]
)

print(f"Success: {result.success}")
print(f"Attempts: {len(result.attempts)}")
```

## Benefits

### 1. Autonomous Operation
- Otto figures out and fixes problems itself
- Minimal human intervention needed
- Learns from patterns over time

### 2. Cost Optimization
- Uses local models when available (free)
- Falls back to remote only when needed
- Replicate as last resort

### 3. Reliability
- Intelligent retry with failure analysis
- Automatic parameter adjustment
- Alternative model selection

### 4. Flexibility
- Respects explicit user requests
- Discovers models dynamically
- Adapts to what's installed

### 5. Transparency
- Clear reasoning for decisions
- Detailed retry information
- Statistics and monitoring

## Monitoring

### Get System Statistics

```python
from src.core.smart_model_prioritization import get_prioritization_system
from src.core.replicate_model_registry import get_replicate_registry
from src.core.intelligent_retry_system import get_retry_system

# Prioritization stats
prioritizer = get_prioritization_system()
print("=== Model Prioritization ===")
print(prioritizer.get_stats())

# Replicate registry stats
registry = get_replicate_registry()
print("\n=== Replicate Registry ===")
print(registry.get_stats())

# Retry system stats
retry = get_retry_system()
print("\n=== Retry System ===")
print(retry.get_stats())
```

### Logging

All three systems log extensively:

```
INFO - Smart model prioritization enabled
INFO - ✓ Anthropic API key found
INFO - ✓ OpenAI API key found (Local FLUX available)

```python
# User request: "Create a professional logo"

# System behavior:
1. Checks installed models
   - COMFYUI_ENDPOINT found ✓
   - Local FLUX available ✓
   - OPENAI_API_KEY found ✓

2. Selects model: flux-local (LOCAL)
   - Reason: Local model beats remote APIs
   - DALL-E 3: Available but not used (local priority)
   - Replicate: NOT USED

3. Executes with retry
   - Attempt 1: Success ✓
```

### Example 1b: Smart Image Generation (Only API available)

```python
# User request: "Create a professional logo"

# System behavior:
1. Checks installed models
   - No local image models ✗
   - OPENAI_API_KEY found ✓
   - dall-e-3 available ✓

2. Selects model: dall-e-3 (REMOTE API)
   - Reason: No local models, using remote API

## Examples

### Example 1: Smart Image Generation

```python
# User request: "Create a professional logo"

# System behavior:
1. Checks installed models
   - OPENAI_API_KEY found ✓
   - dall-e-3 available ✓

2. Selects model: dall-e-3 (REMOTE)
   - Reason: Remote model available
   - Replicate: NOT USED

3. Executes with retry
   - Attempt 1: Success ✓
```

### Example 2: Replicate Explicit Request

```python
# User request: "Generate a video using Replicate"

# System behavior:
1. Detects "replicate" keyword
   - explicit_source = REPLICATE

2. Selects model from Replicate
   - Discovers available video models
   - Ranks by popularity
   - Selects: stability-ai/stable-video-diffusion

3. Executes (no retry needed)
```

### Example 3: Failover Chain

```python
# User request: "Create an image"

# System behavior:
1. Checks installed models
   - OPENAI_API_KEY found ✓

2. Selects: dall-e-3
   
3. Execution with retry:
   Attempt 1: dall-e-3 → Rate limit
   - Strategy: Backoff (wait 4s)
   
   Attempt 2: dall-e-3 → Still rate limited
   - Strategy: Try alternative
   
   Attempt 3: flux-dev (Replicate fallback) → Success ✓

Result: Image generated successfully
Total time: 12.5 seconds
Models tried: dall-e-3, flux-dev
```

## Troubleshooting

### Issue: Always using Replicate

**Cause:** No API keys configured

**Solution:**
```bash
# Configure at least one remote API
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...

# Restart Otto to rescan models
python run.py
```

### Issue: Retry giving up too quickly

**Cause:** Default max_retries too low

**Solution:**
```python
from src.core.intelligent_retry_system import get_retry_system

retry = get_retry_system(
    max_retries=10,  # Increase from default 5
    max_total_duration=600  # Increase from default 300
)
```

### Issue: Not discovering Replicate models

**Cause:** Missing REPLICATE_API_TOKEN

**Solution:**
```bash
export REPLICATE_API_TOKEN=r8_...
```

### Issue: Local models not detected

**Cause:** Ollama not running or not in PATH

**Solution:**
```bash
# Check Ollama is running
ollama list

# If not, start it
ollama serve

# Force rescan
python -c "from src.core.smart_model_prioritization import get_prioritization_system; get_prioritization_system().force_rescan()"
```

## Summary

These three systems work together to make Otto:

1. **Smart** - Automatically uses best available models
2. **Autonomous** - Figures out and fixes problems itself
3. **Reliable** - Intelligent retry with failure analysis
4. **Flexible** - Works with what you have installed
5. **Transparent** - Clear reasoning and logging

**The Golden Rule:**
> LOCAL/REMOTE FIRST, REPLICATE ONLY WHEN NECESSARY

Otto will NEVER use Replicate if you have remote models installed, unless you explicitly ask for it.
