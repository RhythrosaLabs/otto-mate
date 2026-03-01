# Workflow Diagram → Implementation Mapping

This document maps the workflow from your diagram to the actual implementation.

## Your Diagram

```
Otto (orchestrator)
      ↓
Task Interpretation
      ↓
Parsing
      ↓
Task Delegation
      ↓
Agents Creation
      ↓
┌──────────────┬──────────────┐
│ Specialties  │    Tools     │
│ Skills       │  AI Models   │
│ & Features   │  (Integr.)   │
└──────────────┴──────────────┘
      ↓
Task performance + completion
      ↓
   Results
```

## Implementation Mapping

### 1. Otto (orchestrator)
**File**: `src/core/enhanced_workflow_orchestrator.py`  
**Class**: `EnhancedWorkflowOrchestrator`

**Code Location**:
```python
orchestrator = get_enhanced_orchestrator(anthropic_client, tool_registry)
result = await orchestrator.execute_workflow(user_request)
```

**Integration**: `src/core/agent_orchestrator.py` (line ~640)
```python
if self.enhanced_orchestrator:
    workflow_result = await self.enhanced_orchestrator.execute_workflow(...)
```

---

### 2. Task Interpretation
**File**: `src/core/langchain_task_interpreter.py`  
**Class**: `LangChainTaskInterpreter`

**What It Does**:
- Analyzes user request with strict prompt engineering (LangChain pattern)
- Extracts task type, complexity, parameters
- Uses chain-of-thought reasoning
- Creates structured `InterpretedTask`

**Code**:
```python
interpreter = get_task_interpreter(anthropic_client)
interpreted_task = await interpreter.interpret_task(user_request, context)

# Returns:
# - task_type (CREATE, ANALYZE, WORKFLOW, etc.)
# - complexity (SIMPLE, MODERATE, COMPLEX, etc.)
# - primary_goal
# - detailed_description
# - success_criteria
# - parameters
# - steps
```

**Prompt Template**: `TASK_INTERPRETATION_PROMPT` (lines 103-190)

---

### 3. Parsing → MODALITY DETECTION ⭐
**File**: `src/core/modality_system.py`  
**Class**: `ModalityDetector`

**What Changed**: Instead of just "parsing", we now **detect modalities first**

**What It Does**:
- Determines WHAT type of content is needed (IMAGE, TEXT, VIDEO, etc.)
- Assigns priorities
- Sets quality levels
- **This is where MODALITY → MODEL enforcement starts**

**Code**:
```python
detector = get_modality_detector(anthropic_client)
detected_modalities = await detector.detect_modalities(user_request, context)

# Returns list of ModalityRequirement:
# - modality (IMAGE, VIDEO, TEXT, etc.)
# - priority (1 = highest)
# - quality_level (quick/standard/high/ultra)
# - constraints
```

**KEY PRINCIPLE**: We determine WHAT is needed BEFORE selecting HOW to create it.

---

### 4. MODEL SELECTION (MODALITY → MODEL) ⭐⭐⭐
**File**: `src/core/modality_system.py`  
**Class**: `ModalityToModelMapper`

**What It Does**:
- Maps each modality to the appropriate AI model
- **Enforces MODALITY → MODEL, not MODEL → MODALITY**
- Considers quality preferences, speed, cost
- Returns explicit model mapping

**Code**:
```python
mapper = get_modality_mapper()
model_mapping = mapper.select_models_for_requirements(
    detected_modalities,
    context
)

# Returns: {
#   Modality.IMAGE: "black-forest-labs/flux-1.1-pro",
#   Modality.TEXT: "claude-sonnet-4-20250514",
#   Modality.VIDEO: "runway/gen3"
# }
```

**Model Registry**: `MODEL_CAPABILITIES` (lines 79-320)
- Defines what each model can do
- Maps modalities to capabilities
- Scoring system for selection

**Example Mappings**:
```python
IMAGE → FLUX Pro (highest quality) or DALL-E 3 (consistency)
TEXT → Claude Sonnet (balanced) or Opus (complex)
VIDEO → Runway Gen-3 (cinematic) or Luma (camera control)
AUDIO → ElevenLabs (voice) or Whisper (transcription)
CODE → Claude Sonnet (programming)
3D → Meshy (3D generation)
```

---

### 5. Task Validation
**File**: `src/core/enhanced_workflow_orchestrator.py`  
**Method**: `_validate_task_execution_plan()` (line ~390)

**What It Does**:
- Verifies all modalities have model mappings
- Checks task has execution steps
- Validates success criteria exist
- Ensures MODALITY → MODEL enforcement worked

**Code**:
```python
validation_result = await self._validate_task_execution_plan(
    interpreted_task,
    detected_modalities,
    model_mapping
)

# Returns: {
#   "valid": True/False,
#   "issues": [...],
#   "confidence": 0.9
# }
```

---

### 6. Task Delegation (CrewAI Pattern) ⭐
**File**: `src/core/crewai_delegation.py`  
**Class**: `CrewAITaskDelegator`

**What It Does**:
- Selects specialized agents based on modalities
- Coordinates multi-agent execution
- Orchestrates complex workflows
- Synthesizes results

**Code**:
```python
delegator = get_crew_delegator(anthropic_client, tool_registry)
delegation_result = await delegator.delegate_task(
    interpreted_task,
    model_mapping,  # Uses MODALITY → MODEL mapping
    callback
)
```

**Agent Selection** (lines 315-365):
```python
# Maps modalities to agent roles
modality_to_role = {
    "TEXT": AgentRole.TEXT_SPECIALIST,      # Wordsmith
    "IMAGE": AgentRole.VISION_SPECIALIST,   # Picasso
    "VIDEO": AgentRole.VIDEO_SPECIALIST,    # Director
    "AUDIO": AgentRole.AUDIO_SPECIALIST,    # Composer
    "CODE": AgentRole.CODE_SPECIALIST,      # DevOps
    "DATA": AgentRole.DATA_ANALYST,         # Analyst
}
```

**Orchestration Logic** (lines 395-490):
- Simple tasks: Direct execution
- Complex tasks: Orchestrator coordinates multiple specialists

---

### 7. Agents Creation
**File**: `src/core/crewai_delegation.py`  
**Definition**: `DEFAULT_CREW_AGENTS` (lines 56-255)

**Specialties & Skills** (matching left side of diagram):

#### **Maestro** (Orchestrator)
- **Specialties**: Task decomposition, coordination, synthesis
- **Skills**: Planning, delegation, quality assessment
- **Features**: Hierarchical delegation, result aggregation

#### **Wordsmith** (Text Specialist)
- **Specialties**: Writing, content creation
- **Skills**: Copywriting, technical writing, creative writing, editing
- **Features**: Tone adaptation, audience targeting

#### **Picasso** (Vision Specialist)
- **Specialties**: Image creation, visual design
- **Skills**: Artistic design, composition, style transfer
- **Features**: Visual analysis, aesthetic judgment

#### **Director** (Video Specialist)
- **Specialties**: Video production
- **Skills**: Storytelling, cinematography, editing
- **Features**: Pacing, visual narrative

#### **Composer** (Audio Specialist)
- **Specialties**: Audio production
- **Skills**: Music composition, voice acting, sound design
- **Features**: Audio mixing, sonic branding

#### **DevOps** (Code Specialist)
- **Specialties**: Programming
- **Skills**: Coding, debugging, optimization, testing
- **Features**: Multi-language support, best practices

#### **Scholar** (Researcher)
- **Specialties**: Information gathering
- **Skills**: Research, source validation, synthesis
- **Features**: Critical thinking, fact-checking

#### **Inspector** (Quality Assurer)
- **Specialties**: Quality validation
- **Skills**: Quality assessment, attention to detail
- **Features**: Constructive feedback, validation

---

### 8. Tools & AI Models (right side of diagram)
**File**: `src/core/modality_system.py`  
**Registry**: `MODEL_CAPABILITIES` (lines 79-320)

**AI Models (Integration)**:
Each agent uses the model selected by MODALITY → MODEL mapping:

```python
# Example from agent execution (line 400):
primary_modality = task.required_modalities[0]
model = modality_mapping.get(primary_modality, agent.model)

# Agent now executes with CORRECT model for the modality
if "claude" in model:
    response = anthropic.messages.create(model=model, ...)
# For other modalities, delegate to appropriate tool
```

**Tools Available**:
- Image generation: FLUX, DALL-E, Stable Diffusion
- Video generation: Runway, Luma
- Audio: ElevenLabs, Whisper
- Code execution: Various engines
- Text: Claude models, GPT models
- 3D: Meshy
- Research: Web search, scraping
- Integration: Printify, Shopify, etc.

---

### 9. Task Performance + Completion
**File**: `src/core/crewai_delegation.py`  
**Methods**: 
- `_execute_direct()` (lines 367-450) - Simple tasks
- `_execute_orchestrated()` (lines 452-538) - Complex tasks

**What Happens**:

#### Direct Execution (Simple):
```python
1. Build agent prompt with task details
2. Select model from MODALITY → MODEL mapping
3. Execute with appropriate model
4. Return result
5. Update agent statistics
```

#### Orchestrated Execution (Complex):
```python
1. Orchestrator creates coordination plan
2. Delegate to specialists sequentially/parallel
3. Each specialist uses their mapped model:
   - Picasso uses FLUX for IMAGE
   - Wordsmith uses Claude for TEXT
   - Director uses Runway for VIDEO
4. Orchestrator synthesizes results
5. Quality assurance validates
6. Return unified result
```

**Quality Assurance** (lines 540-580):
```python
qa_result = await self._quality_assurance_check(
    task,
    result,
    callback
)
# Inspector agent validates:
# - Meets success criteria?
# - Complete and accurate?
# - Quality score (0.0-1.0)
```

---

### 10. Results
**File**: `src/core/enhanced_workflow_orchestrator.py`  
**Class**: `WorkflowResult` (lines 45-90)

**What's Returned**:
```python
WorkflowResult(
    success=True,
    final_output=delegation_result.final_output,
    
    # Show what was detected
    detected_modalities=[...],
    
    # Show MODALITY → MODEL mapping  
    modality_model_mapping={
        "IMAGE": "flux-1.1-pro",
        "TEXT": "claude-sonnet-4"
    },
    
    # Show execution stages
    stages=[
        WorkflowStage("task_interpretation", duration=0.5s),
        WorkflowStage("modality_detection", duration=0.3s),
        WorkflowStage("model_selection", duration=0.1s),
        WorkflowStage("task_delegation", duration=2.5s),
        ...
    ],
    
    # Metrics
    total_duration=3.4,
    quality_score=0.92,
    
    # Full delegation details
    delegation_result={...}
)
```

---

## Complete Flow Example

### User Request: "Create a logo for my coffee shop and write a tagline"

```python
# 1. ORCHESTRATOR
orchestrator.execute_workflow("Create a logo and tagline")

# 2. TASK INTERPRETATION (LangChain)
→ InterpretedTask(
    task_type=CREATE,
    complexity=MODERATE,
    primary_goal="Create brand identity with logo and tagline",
    steps=[
      {1: "Generate logo design"},
      {2: "Create tagline text"}
    ]
  )

# 3. MODALITY DETECTION ⭐
→ [
    ModalityRequirement(IMAGE, priority=1, quality="high"),
    ModalityRequirement(TEXT, priority=2, quality="standard")
  ]

# 4. MODEL SELECTION (MODALITY → MODEL) ⭐⭐⭐
→ {
    IMAGE: "black-forest-labs/flux-1.1-pro",  # Best image model
    TEXT: "claude-sonnet-4-20250514"          # Best text model
  }

# 5. TASK VALIDATION
→ ✅ Valid: All modalities have models, steps defined, criteria set

# 6. TASK DELEGATION (CrewAI)
→ Select agents: [Maestro, Picasso, Wordsmith]
→ Orchestrated execution mode

# 7. AGENTS CREATION & EXECUTION
Maestro: "Coordinate logo and tagline creation"
  ↓
Picasso: "Create logo using FLUX Pro" ← Uses IMAGE model
  Result: Beautiful logo image ✅
  ↓
Wordsmith: "Write tagline using Claude" ← Uses TEXT model
  Result: "Brewing happiness, one cup at a time" ✅
  ↓
Maestro: "Synthesize results"
  Result: Logo + Tagline package ✅
  ↓
Inspector: "Validate quality"
  Quality Score: 0.94 ✅

# 8. RESULTS
→ WorkflowResult(
    success=True,
    final_output={
      logo: <image>,
      tagline: "Brewing happiness, one cup at a time"
    },
    modality_model_mapping={
      "IMAGE": "flux-1.1-pro",
      "TEXT": "claude-sonnet-4"
    },
    quality_score=0.94,
    total_duration=4.2s
  )
```

---

## Key Implementation Details

### Where MODALITY → MODEL is Enforced

1. **Detection**: `modality_system.py:ModalityDetector.detect_modalities()`
   - Line ~470: Analyzes request for required modalities

2. **Mapping**: `modality_system.py:ModalityToModelMapper.select_models_for_requirements()`
   - Line ~670: Maps each modality to appropriate model
   - Uses capability scoring system

3. **Validation**: `enhanced_workflow_orchestrator.py:_validate_task_execution_plan()`
   - Line ~390: Ensures all modalities have model mappings

4. **Usage**: `crewai_delegation.py:_execute_direct()`
   - Line ~400: Uses model from MODALITY → MODEL mapping
   - `model = modality_mapping.get(primary_modality, agent.model)`

### Where It's Integrated

**File**: `src/core/agent_orchestrator.py`

**Location**: Line ~640 (in `process()` method)

**Logic**:
```python
if (self.enhanced_orchestrator and 
    request_type.get("is_action") and
    any(keyword in message.lower() for keyword in 
        ["create", "generate", "make", "design", "build", "workflow", "campaign"])):
    
    # Use enhancedworkflow with MODALITY → MODEL
    workflow_result = await self.enhanced_orchestrator.execute_workflow(
        user_request=message,
        session_id=session["id"],
        context=context
    )
```

---

## Testing

**File**: `test_enhanced_workflow.py`

**Run**:
```bash
export ANTHROPIC_API_KEY=your_key
python test_enhanced_workflow.py
```

**Tests**:
1. Modality detection
2. MODALITY → MODEL mapping
3. Task interpretation
4. Full workflow execution

---

## Summary

Your diagram → Our implementation:

| Diagram Step | Implementation | Key File |
|-------------|----------------|----------|
| Otto (orchestrator) | `EnhancedWorkflowOrchestrator` | `enhanced_workflow_orchestrator.py` |
| Task Interpretation | `LangChainTaskInterpreter` | `langchain_task_interpreter.py` |
| Parsing | `ModalityDetector` ⭐ | `modality_system.py` |
| (NEW) Model Selection | `ModalityToModelMapper` ⭐⭐⭐ | `modality_system.py` |
| Task Delegation | `CrewAITaskDelegator` | `crewai_delegation.py` |
| Agents Creation | `DEFAULT_CREW_AGENTS` | `crewai_delegation.py` |
| Specialties/Skills | Agent configurations | `crewai_delegation.py` |
| Tools/AI Models | `MODEL_CAPABILITIES` registry | `modality_system.py` |
| Task Performance | Agent execution methods | `crewai_delegation.py` |
| Results | `WorkflowResult` | `enhanced_workflow_orchestrator.py` |

**Key Innovation**: Between "Parsing" and "Task Delegation", we added explicit **MODALITY DETECTION** and **MODALITY → MODEL MAPPING** to ensure the right AI model is selected for each task type.

This is the core of the enhancement: **MODALITY → MODEL, not MODEL → MODALITY**.
