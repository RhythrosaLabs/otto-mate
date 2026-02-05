# Printify Clean Features → Otto Skills Migration Plan

Based on analysis of `/useful repos/printify_clean/`, the following key features should be converted into Otto skills:

---

## 1. 🔧 Custom Workflows System

**Location:** `app/tabs/abp_custom_workflows.py` (2,422 lines)

**Core Capabilities:**
- Visual workflow builder with drag-and-drop steps
- Multi-step AI pipelines (image → video → product → publish)
- Step types:
  - Image Generation
  - Image Editing/Enhancement
  - Video Generation
  - Text Generation
  - Product Creation (Printify)
  - Publishing (Shopify, YouTube, Twitter)
  - File Operations (save, load, process)
- Background execution support
- Workflow templates and saving/loading
- Step dependencies and conditional execution
- Progress tracking per step
- Error handling and retry logic

**Otto Skill Conversion:**
```
Skill Name: workflow_automation
Capabilities:
  - create_workflow: Build multi-step automation pipelines
  - execute_workflow: Run saved workflows with real-time progress
  - workflow_templates: Access pre-built workflow templates
  - step_chaining: Connect outputs from one step to next step inputs
  - conditional_logic: Add if/then branches to workflows
  - schedule_workflow: Set up recurring workflow execution
```

---

## 2. 🤖 Task Queue Engine

**Location:** `app/services/task_queue_engine.py` (2,053 lines)

**Core Capabilities:**
- Autonomous task planning and decomposition
- Multi-step task execution with dependency management
- Task status tracking (pending, planning, running, completed, failed)
- Priority queue (low, normal, high, urgent)
- Artifact management (images, videos, text, products, blog posts)
- Task scheduling and recurring tasks
- Parallel execution support
- Real-time progress updates
- Task chaining and dependencies
- Publishing to multiple platforms (Printify, Shopify, YouTube, Twitter)

**Key Classes:**
- `Task`: Complete task representation
- `TaskStep`: Individual step in task execution
- `Artifact`: Generated content (image/video/text)
- `TaskStatus`: Execution state management
- `TaskPriority`: Queue prioritization

**Otto Skill Conversion:**
```
Skill Name: task_queue_management
Capabilities:
  - queue_task: Add tasks to autonomous execution queue
  - plan_task: Break complex tasks into executable steps
  - execute_task: Run queued tasks with dependency resolution
  - track_progress: Monitor task execution status
  - manage_artifacts: Collect and organize generated content
  - schedule_recurring: Set up daily/weekly automated tasks
  - batch_operations: Process multiple items in parallel
  - priority_management: Control task execution order
```

---

## 3. 🎮 Replicate Playground

**Location:** `app/tabs/abp_playground.py` (1,379 lines)

**Core Capabilities:**
- **Image Generation**: Test 50+ image models
- **Image Editing**: Transform, enhance, style transfer
- **Video Generation**: Text-to-video, image-to-video
- **Video Editing**: Cut, enhance, add effects
- **3D Generation**: Text-to-3D models
- **Audio Studio**: Music generation, speech synthesis
- **Document/Code Editors**: Interactive coding playgrounds
- **Model Chaining**: Pipeline multiple AI models

**Otto Skill Conversion:**
```
Skill Name: ai_playground_experimentation
Capabilities:
  - test_models: Experiment with different AI models
  - chain_models: Build multi-model pipelines
  - compare_results: A/B test different model outputs
  - save_experiments: Store successful prompts/configs
  - quick_prototyping: Rapid iteration on creative ideas
  - parameter_tuning: Fine-tune model settings
```

---

## 4. 🔗 Model Chaining System

**Location:** `app/tabs/abp_playground.py` lines 286-450

**Core Capabilities:**
- Sequential model execution
- Pass output from one model to next
- Pipeline types:
  - Image → Edit → Video → Publish
  - Text → Image → Product → Store
  - Video → Audio → Social → Schedule
- Visual pipeline builder
- Step configuration and reordering
- Error handling and retry
- Result preview at each step

**Otto Skill Conversion:**
```
Skill Name: model_chaining_pipelines
Capabilities:
  - create_chain: Build multi-model execution pipelines
  - execute_chain: Run chained model sequence
  - chain_templates: Pre-built pipelines for common workflows
  - step_reordering: Rearrange pipeline steps
  - conditional_branching: Add logic gates to chains
  - output_transformation: Format data between models
```

---

## 5. 🏠 Dashboard Automation

**Location:** `app/tabs/abp_dashboard.py` (1,871 lines)

**Core Capabilities:**
- Smart concept generation (AI-powered ideas)
- One-click campaign launches
- Real-time activity feed
- Notification center
- Cross-page state management
- Campaign status tracking
- Resource usage monitoring
- Quick actions and shortcuts
- Integration status indicators
- Auto-save and session persistence

**Features to Convert:**
- **Activity Feed**: Track all actions across platform
- **Smart Dashboard Widget**: Real-time updates and notifications
- **Campaign Generator**: Full product line creation from single idea
- **Quick Launch**: Pre-configured workflows for common tasks
- **Status Monitoring**: Track running jobs across all services

**Otto Skill Conversion:**
```
Skill Name: dashboard_automation
Capabilities:
  - activity_tracking: Monitor all platform actions
  - smart_suggestions: AI-powered next action recommendations
  - quick_launch: One-click execution of common workflows
  - status_dashboard: Real-time job and campaign monitoring
  - campaign_orchestration: Full product lifecycle automation
  - notification_management: Alert on important events
  - session_persistence: Save and restore work across sessions
```

---

## 6. 🔄 Global Job Queue

**Location:** `app/services/global_job_queue.py` (508 lines)

**Core Capabilities:**
- Ray-powered distributed job execution
- Resource allocation by job type
- Priority queue management
- Parallel job processing
- Job types:
  - Image/Video/Text generation
  - Product creation
  - Campaign generation
  - Workflow execution
  - Batch operations
- Resource profiles for different workloads
- Job status tracking
- Cross-tab job submission

**Otto Skill Conversion:**
```
Skill Name: distributed_job_processing
Capabilities:
  - submit_job: Add work to distributed queue
  - allocate_resources: Assign CPU/memory per job type
  - parallel_execution: Run multiple jobs simultaneously
  - monitor_cluster: Track resource usage and job health
  - optimize_throughput: Balance workload across workers
```

---

## Implementation Strategy

### Phase 1: Core Infrastructure
1. **Workflow Engine** - Build visual workflow system
2. **Task Queue** - Implement autonomous task planning
3. **Job Queue** - Add distributed processing support

### Phase 2: Model Integration
4. **Playground** - Add interactive model testing
5. **Model Chaining** - Enable sequential AI pipelines

### Phase 3: Dashboard & UX
6. **Dashboard Automation** - Smart suggestions and quick launch
7. **Activity Feed** - Track all platform actions
8. **Notification System** - Real-time updates

---

## Key Architectural Patterns to Adopt

### 1. Step-Based Execution
```python
@dataclass
class WorkflowStep:
    id: str
    type: str  # image_gen, video_gen, publish, etc.
    config: Dict
    status: str
    output: Any
    depends_on: List[str]
```

### 2. Artifact Management
```python
@dataclass
class Artifact:
    id: str
    type: ArtifactType  # image, video, product, blog
    url: Optional[str]
    metadata: Dict
    created_at: datetime
```

### 3. Background Task Execution
```python
class BackgroundTaskManager:
    async def submit_task(task: Task) -> str
    async def check_status(task_id: str) -> TaskStatus
    async def get_results(task_id: str) -> Dict
```

### 4. Model Pipeline Builder
```python
class ModelChain:
    steps: List[ChainStep]
    
    async def execute(input_data: Any) -> List[Artifact]
    def add_step(model: str, config: Dict) -> None
    def remove_step(step_id: str) -> None
```

---

## Integration Points with Otto

### Existing Otto Systems to Leverage:
- **Tool Registry**: Register new workflow/queue tools
- **Execution Agent**: Use for step-by-step execution
- **Super Planning Agent**: Leverage for task decomposition
- **Memory Agent**: Store workflow templates and results

### New Systems to Build:
- **Workflow Builder UI**: Visual node-based editor
- **Task Queue Service**: Background job processing
- **Model Chain Executor**: Sequential AI model pipelines
- **Dashboard Widget System**: Real-time activity tracking

---

## Priority Order

1. **HIGH** - Task Queue Engine (most impactful)
2. **HIGH** - Workflow Automation (core capability)
3. **MEDIUM** - Model Chaining (enhances creativity)
4. **MEDIUM** - Dashboard Automation (improves UX)
5. **LOW** - Playground (nice-to-have experimentation)
6. **LOW** - Global Job Queue (optimization for scale)

---

## File References

**Key Files to Study:**
- `app/services/task_queue_engine.py` - Task management core
- `app/tabs/abp_custom_workflows.py` - Workflow builder
- `app/tabs/abp_playground.py` - Model chaining (lines 286-450)
- `app/tabs/abp_dashboard.py` - Dashboard automation
- `app/services/global_job_queue.py` - Distributed processing
- `app/services/tab_job_helpers.py` - Job management utilities

**Supporting Services:**
- `app/services/platform_integrations.py` - API tracking
- `app/services/background_tasks.py` - Async execution
- `app/utils/cross_page_state.py` - Session management
- `playground_models.py` - Model definitions

---

## Next Steps

1. Review this analysis with stakeholders
2. Prioritize which features to implement first
3. Create detailed skill definitions for each system
4. Build prototypes for workflow and task queue
5. Integrate with existing Otto architecture
6. Test with real user workflows
