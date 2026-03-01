# Enhanced Workflow System - MODALITY → MODEL Enforcement

## Overview

Otto now enforces **MODALITY → MODEL** selection instead of the previous **MODEL → MODALITY** inference pattern. This fundamental architectural change is inspired by LangChain and CrewAI patterns and ensures precise, efficient task execution.

## The Problem We Solved

### Before (MODEL → MODALITY)
```
User: "Create a logo"
     ↓
Otto: "I'll use Claude Sonnet"
     ↓
Claude: "I can generate text, but I'll describe an image for you..."
     ❌ Wrong approach - text model trying to handle image task
```

### After (MODALITY → MODEL)
```
User: "Create a logo"
     ↓
Otto: "This requires IMAGE modality"
     ↓
Modality Mapper: "IMAGE → FLUX Pro (best quality image model)"
     ↓
FLUX Pro: Generates actual logo
     ✅ Correct approach - modality determines model
```

## Architecture

### Workflow Diagram

```
Otto (orchestrator)
       ↓
Task Interpretation (LangChain)
   - Parse user intent
   - Extract parameters
   - Chain-of-thought reasoning
       ↓
Modality Detection
   - Determine WHAT is needed (TEXT, IMAGE, VIDEO, etc.)
   - Priority and quality levels
       ↓
Model Selection (MODALITY → MODEL)
   - Map each modality to appropriate model
   - Consider quality, speed, cost preferences
       ↓
Task Validation
   - Verify completeness
   - Check dependencies
       ↓
Task Delegation (CrewAI)
   - Select specialized agents
   - Orchestrate execution
   - Coordinate collaboration
       ↓
┌────────────────────┬────────────────────┐
│   Specialties      │      Tools         │
│   - Skills         │  - AI Models       │
│   - Features       │  - Integrations    │
└────────────────────┴────────────────────┘
       ↓
Task Performance + Completion
   - Execute with correct models
   - Quality assurance
   - Error recovery
       ↓
   Results
   - Synthesized output
   - Artifacts
   - Quality metrics
```

## Components

### 1. Modality System (`modality_system.py`)

**Purpose:** Detects required modalities and maps them to appropriate models.

**Key Classes:**
- `Modality` enum: TEXT, IMAGE, VIDEO, AUDIO, CODE, VISION, 3D, DATA
- `ModalityDetector`: Analyzes user requests to detect required modalities
- `ModalityToModelMapper`: Maps modalities to best models
- `ModelCapability`: Defines what each model can do

**Example:**
```python
detector = get_modality_detector(anthropic_client)
modalities = await detector.detect_modalities("Create a logo and write tagline")
# Returns: [IMAGE (priority 1), TEXT (priority 2)]

mapper = get_modality_mapper()
model_mapping = mapper.select_models_for_requirements(modalities)
# Returns: {IMAGE: "flux-1.1-pro", TEXT: "claude-sonnet-4"}
```

### 2. LangChain Task Interpreter (`langchain_task_interpreter.py`)

**Purpose:** Strict prompt engineering and task parsing inspired by LangChain.

**Key Features:**
- Structured prompt templates
- Chain-of-thought reasoning
- Parameter extraction
- Step decomposition
- Task validation

**Example:**
```python
interpreter = get_task_interpreter(anthropic_client)
task = await interpreter.interpret_task("Create marketing campaign")

# Returns InterpretedTask with:
# - task_type: WORKFLOW
# - complexity: COMPLEX
# - steps: [research competitors, create content, design graphics, ...]
# - required_modalities: [TEXT, IMAGE, VIDEO]
# - parameters: [brand: "...", audience: "...", ...]
```

### 3. CrewAI Delegation (`crewai_delegation.py`)

**Purpose:** Multi-agent collaboration and task delegation inspired by CrewAI.

**Key Features:**
- Specialized agents with roles, goals, and backstories
- Hierarchical delegation
- Parallel and sequential execution  
- Result synthesis
- Quality assurance

**Default Agents:**
- **Maestro** (Orchestrator): Coordinates all agents
- **Wordsmith** (Text Specialist): Creates text content
- **Picasso** (Vision Specialist): Handles images
- **Director** (Video Specialist): Creates videos
- **Composer** (Audio Specialist): Produces audio
- **DevOps** (Code Specialist): Writes code
- **Scholar** (Researcher): Gathers information
- **Inspector** (Quality Assurer): Validates quality

**Example:**
```python
delegator = get_crew_delegator(anthropic_client, tool_registry)
result = await delegator.delegate_task(interpreted_task, modality_mapping)

# Maestro coordinates:
# 1. Scholar researches topic
# 2. Wordsmith writes content
# 3. Picasso creates graphics
# 4. Maestro synthesizes final result
# 5. Inspector validates quality
```

### 4. Enhanced Workflow Orchestrator (`enhanced_workflow_orchestrator.py`)

**Purpose:** Master orchestrator that ties everything together.

**Workflow Stages:**
1. **Task Interpretation** (LangChain-style)
2. **Modality Detection** (MODALITY first)
3. **Model Selection** (MODALITY → MODEL mapping)
4. **Task Validation** (ensure completeness)
5. **Task Delegation** (CrewAI-style)
6. **Execution** (with correct models)
7. **Quality Validation** (QA check)

**Example:**
```python
orchestrator = get_enhanced_orchestrator(anthropic_client, tool_registry)
result = await orchestrator.execute_workflow(
    "Create a product launch campaign",
    callback=progress_callback
)

# Returns WorkflowResult with:
# - detected_modalities
# - modality_model_mapping  
# - stages (with timing)
# - delegation_result
# - quality_score
# - final_output
```

## Integration

The enhanced workflow system is automatically used by `AgentOrchestrator` for complex requests:

```python
# In agent_orchestrator.py
if (self.enhanced_orchestrator and 
    request_type.get("is_action") and
    any(kw in message.lower() for kw in ["create", "generate", "make", ...])):
    
    # Use enhanced orchestrator (MODALITY → MODEL)
    workflow_result = await self.enhanced_orchestrator.execute_workflow(
        user_request=message,
        session_id=session["id"],
        context=context
    )
```

## Model Capabilities

The system maintains a registry of model capabilities:

### Text Models
- **Claude Sonnet 4**: TEXT, CODE, DATA, VISION
- **Claude Opus 4**: TEXT, CODE, DATA, VISION (highest quality)
- **Claude Haiku**: TEXT, CODE (fastest)
- **GPT-4o**: TEXT, CODE, VISION, AUDIO

### Image Models
- **FLUX Pro**: IMAGE (highest quality)
- **FLUX Dev**: IMAGE (balanced)
- **DALL-E 3**: IMAGE (ease of use)
- **Stable Diffusion XL**: IMAGE (cost-effective)

### Video Models
- **Runway Gen-3**: VIDEO (cinematic quality)
- **Luma Dream Machine**: VIDEO (camera control)

### Audio Models
- **ElevenLabs**: AUDIO (voice synthesis)
- **Whisper**: AUDIO (transcription)

### Other
- **Meshy**: 3D modeling
- Various code execution engines

## Example Usage

### Simple Request
```python
# User: "Write a blog post about AI"
# Flow:
# 1. Detect modality: TEXT
# 2. Select model: claude-sonnet-4
# 3. Delegate to: Wordsmith (Text Specialist)
# 4. Execute with Claude Sonnet
# 5. Return high-quality blog post
```

### Complex Request
```python
# User: "Create a product launch campaign with video, graphics, and website"
# Flow:
# 1. Detect modalities: VIDEO, IMAGE, CODE, TEXT
# 2. Select models:
#    - VIDEO → runway/gen3
#    - IMAGE → flux-1.1-pro
#    - CODE → claude-sonnet-4
#    - TEXT → claude-sonnet-4
# 3. Delegate to:
#    - Maestro (Orchestrator)
#    - Director (Video)
#    - Picasso (Graphics)
#    - DevOps (Code)
#    - Wordsmith (Text)
# 4. Execute in coordinated workflow
# 5. Synthesize complete campaign
# 6. Validate quality
```

## Key Principles

### 1. Modality First
**Always** determine WHAT is needed before selecting HOW to create it.

❌ Wrong: "Use Claude for everything"
✅ Right: "Need IMAGE → Use FLUX, Need TEXT → Use Claude"

### 2. Explicit Not Implicit
Models don't infer capabilities - the system explicitly maps modalities to models.

### 3. Quality Over Inference
Better to select the right tool for the job than to force a general tool to adapt.

### 4. Separation of Concerns
- **Interpretation** (what user wants)
- **Detection** (what modalities needed)
- **Selection** (which models to use)
- **Delegation** (which agents execute)
- **Execution** (actual work)

## Testing

Run the test suite:

```bash
python test_enhanced_workflow.py
```

Tests include:
1. Modality detection
2. Model selection
3. Task interpretation
4. Full workflow execution

## Configuration

Configure preferences in your config:

```python
config = {
    "prefer_speed": False,  # Prefer fast models
    "prefer_cost": False,   # Prefer cheap models
    "enable_qa": True,      # Enable quality assurance
}
```

## Monitoring

Track workflow performance:

```python
orchestrator = get_enhanced_orchestrator(client, tools)
stats = orchestrator.get_workflow_stats()

# Returns:
# - total_workflows
# - success_rate
# - avg_duration
# - avg_quality_score
# - modality_usage
```

## Benefits

1. **Accuracy**: Right tool for the job, every time
2. **Efficiency**: No wasted attempts with wrong models
3. **Quality**: Specialized models deliver better results
4. **Transparency**: Clear modality → model mappings
5. **Scalability**: Easy to add new models and modalities
6. **Reliability**: Explicit selection eliminates guesswork

## Future Enhancements

- [ ] Dynamic model discovery from APIs
- [ ] User preference learning
- [ ] Cost optimization algorithms
- [ ] A/B testing of model selections
- [ ] Real-time model performance monitoring
- [ ] Multi-provider model fallbacks

## Credits

Inspired by:
- **LangChain**: Structured prompting and chain-of-thought
- **CrewAI**: Multi-agent collaboration patterns
- **AutoGPT**: Autonomous execution workflows
- **Browser-Use**: State management patterns

---

**Key Takeaway**: Otto now enforces MODALITY → MODEL selection, ensuring the right AI model is used for each task type, resulting in higher quality, more efficient, and more reliable outcomes.
