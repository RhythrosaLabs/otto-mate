# Workflow Automation Skill

## Overview
Build and execute multi-step automation pipelines with visual workflow builder capabilities.

## Capabilities

### create_workflow
Build multi-step automation pipelines.

**Inputs:**
- name: Workflow name
- description: What the workflow does
- steps: List of step definitions
- triggers: What initiates workflow (manual/schedule/event)

**Outputs:**
- workflow_id: Unique workflow identifier
- step_count: Number of steps
- validation: Workflow validation results

**Example:**
```
create_workflow(
    name="Daily Product Creator",
    steps=[
        {"type": "generate_image", "prompt": "{{product_concept}}"},
        {"type": "create_mockup", "image": "{{step_1_output}}"},
        {"type": "printify_create_mug", "design": "{{step_2_output}}"},
        {"type": "shopify_create_product", "product_id": "{{step_3_product_id}}"}
    ]
)
```

---

### execute_workflow
Run saved workflows with real-time progress tracking.

**Inputs:**
- workflow_id: Workflow to execute
- parameters: Input parameters for workflow
- background: Run in background (default: false)

**Outputs:**
- execution_id: Execution instance ID
- status: Running/completed/failed
- outputs: Results from each step

---

### workflow_templates
Access pre-built workflow templates.

**Inputs:**
- category: product_creation/content_marketing/social_media/automation
- search: Optional search term

**Outputs:**
- templates: List of available templates
- preview: Template configuration

**Available Templates:**
- Product Design Pipeline: idea → design → mockup → product
- Content Marketing Suite: blog → graphics → social posts → schedule
- Video Production Flow: script → video → thumbnail → publish
- Daily Social Media: generate → design → post → track

---

### step_chaining
Connect outputs from one step to next step inputs.

**Inputs:**
- workflow_id: Workflow to modify
- source_step: Step providing output
- target_step: Step receiving input
- mapping: How to map output to input

**Outputs:**
- connection_id: Chain connection identifier
- validation: Connection validation

---

### conditional_logic
Add if/then branches to workflows.

**Inputs:**
- workflow_id: Workflow to modify
- condition: Expression to evaluate
- true_path: Steps if true
- false_path: Steps if false

**Outputs:**
- branch_id: Conditional branch identifier

**Example:**
```
conditional_logic(
    condition="{{step_1_quality}} > 0.8",
    true_path=["publish_to_shopify"],
    false_path=["regenerate_design", "retry_publish"]
)
```

---

### schedule_workflow
Set up recurring workflow execution.

**Inputs:**
- workflow_id: Workflow to schedule
- schedule: cron expression or simple schedule
- enabled: Start/stop schedule

**Outputs:**
- schedule_id: Schedule identifier
- next_run: Next execution time

---

### workflow_builder_ui
Visual node-based workflow editor (for UI integration).

**Inputs:**
- workflow_id: Optional workflow to edit

**Outputs:**
- editor_data: Workflow configuration for UI
- available_nodes: All available step types

## Step Types

### Data Flow Steps
- **input**: Accept user input
- **variable**: Store intermediate values
- **transform**: Modify data between steps

### AI Generation Steps
- **generate_image**: Create images with AI
- **generate_video**: Create videos
- **generate_text**: Create written content
- **generate_design**: Create product designs

### Product Steps
- **create_mockup**: Product mockup generation
- **printify_create**: Create Printify products
- **shopify_publish**: Publish to Shopify

### Content Steps
- **write_blog**: Generate blog posts
- **create_social_post**: Social media content
- **generate_email**: Email campaigns

### Automation Steps
- **wait**: Delay execution
- **loop**: Repeat steps
- **condition**: If/then branching
- **parallel**: Run steps simultaneously

### Publishing Steps
- **publish_shopify**: Shopify store
- **publish_youtube**: YouTube upload
- **publish_social**: Social media posting
- **send_email**: Email delivery

## Workflows

### Standard Templates

#### Product Launch Pipeline
1. Generate product concept (AI)
2. Create 3 design variations
3. Generate mockups for each
4. Create Printify products
5. Publish to Shopify
6. Create marketing materials
7. Schedule social posts

#### Content Marketing Automation
1. Generate blog topic ideas
2. Write full blog post
3. Create featured image
4. Extract social snippets
5. Design social graphics
6. Schedule posts across platforms

#### Video Production Workflow
1. Generate video script
2. Create storyboard images
3. Generate video with AI
4. Add background music
5. Create thumbnail
6. Upload to YouTube
7. Post announcement to social

## Dependencies
- task_queue: For execution management
- execution_agent: For step running
- All tool categories: AI, product, publishing

## Configuration
- max_workflow_steps: 50
- max_parallel_branches: 5
- auto_save: true
- workflow_directory: data/workflows/
- execution_timeout: 3600 (seconds)
