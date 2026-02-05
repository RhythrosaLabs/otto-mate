# Model Chaining Skill

## Overview
Create sequential AI model pipelines where output from one model feeds into the next, enabling complex multi-stage content generation.

## Capabilities

### create_chain
Build multi-model execution pipelines.

**Inputs:**
- name: Chain name
- description: What the chain produces
- steps: List of model steps with configs

**Outputs:**
- chain_id: Unique chain identifier
- model_count: Number of models in chain
- estimated_cost: API cost estimate

**Example:**
```
create_chain(
    name="Product Video Pipeline",
    steps=[
        {"model": "flux_pro", "type": "image", "prompt": "{{concept}}"},
        {"model": "runway_gen3", "type": "video", "image": "{{step_1}}"},
        {"model": "stable_audio", "type": "audio", "style": "upbeat"},
        {"model": "video_compositor", "video": "{{step_2}}", "audio": "{{step_3}}"}
    ]
)
```

---

### execute_chain
Run chained model sequence with automatic data passing.

**Inputs:**
- chain_id: Chain to execute
- input_data: Initial input for first model
- parameters: Override default configs

**Outputs:**
- outputs: Result from each model step
- final_output: Final pipeline output
- artifacts: All intermediate results

---

### chain_templates
Pre-built pipelines for common workflows.

**Inputs:**
- category: image/video/content/product
- complexity: simple/moderate/advanced

**Outputs:**
- templates: Available chain templates

**Built-in Templates:**

#### Image Enhancement Chain
1. Image generation (FLUX Pro)
2. Background removal
3. Upscaling (4x)
4. Style transfer

#### Video Production Chain
1. Script generation (LLM)
2. Storyboard images
3. Image-to-video
4. Music generation
5. Video editing/composition

#### Product Design Chain
1. Concept generation (text)
2. Design creation (image)
3. Multiple variations (editing)
4. Mockup generation
5. Product creation

#### Content Marketing Chain
1. Topic research (web search)
2. Article writing (LLM)
3. Feature image generation
4. Social graphics (image variants)
5. Video summary creation

---

### step_reordering
Rearrange pipeline steps.

**Inputs:**
- chain_id: Chain to modify
- step_id: Step to move
- new_position: Target position

**Outputs:**
- updated_order: New step sequence

---

### conditional_branching
Add logic gates to chains.

**Inputs:**
- chain_id: Chain to modify
- after_step: Step to add condition after
- condition: Evaluation expression
- true_branch: Steps if condition true
- false_branch: Steps if condition false

**Outputs:**
- branch_id: Branch identifier

**Example:**
```
conditional_branching(
    after_step=1,
    condition="{{quality_score}} > 0.85",
    true_branch=[{"model": "publish"}],
    false_branch=[{"model": "regenerate"}]
)
```

---

### output_transformation
Format data between models.

**Inputs:**
- chain_id: Chain to modify
- between_steps: [source_step, target_step]
- transform: Transformation function

**Outputs:**
- transform_id: Transformation identifier

**Transforms:**
- `extract_url`: Get URL from model response
- `resize_image`: Resize image to specific dimensions
- `extract_text`: Pull text content from response
- `format_json`: Convert to JSON structure
- `merge_outputs`: Combine multiple step outputs

---

### save_chain_template
Save custom chain as reusable template.

**Inputs:**
- chain_id: Chain to save
- template_name: Name for template
- category: Template category
- description: What it does

**Outputs:**
- template_id: Saved template identifier

---

### parallel_execution
Run multiple models simultaneously.

**Inputs:**
- chain_id: Chain to modify
- steps: Steps to run in parallel
- merge_strategy: How to combine outputs

**Outputs:**
- parallel_group_id: Parallel execution group

## Model Categories

### Image Models
- **flux_pro**: Highest quality images
- **flux_dev**: Fast iterations
- **sdxl**: Stable Diffusion XL
- **ideogram**: Text rendering
- **recraft_v3**: Vector graphics

### Video Models
- **runway_gen3**: Text/image to video
- **kling_v2**: High-quality video
- **luma_dream_machine**: Creative video
- **pika**: Video editing

### Editing Models
- **photomaker**: Photo editing
- **controlnet**: Structured editing
- **instruct_pix2pix**: Instruction-based editing

### Audio Models
- **stable_audio**: Music generation
- **eleven_labs**: Text-to-speech
- **musicgen**: Background music

### 3D Models
- **shap_e**: 3D generation
- **wonder3d**: Image to 3D

### Text Models
- **llama_70b**: Text generation
- **gpt4**: Advanced reasoning
- **mixtral**: Fast text

## Chain Patterns

### Sequential Pipeline
Model 1 → Model 2 → Model 3 → Output

### Parallel Processing
```
Model 1 → [Model 2A, Model 2B, Model 2C] → Merge → Output
```

### Iterative Refinement
```
Model 1 → Quality Check → [Pass: Next Step | Fail: Regenerate]
```

### Multi-Output Chain
```
Input → Model 1 → [Branch A → Output A, Branch B → Output B]
```

## Workflows

### Complete Product Creation
1. Generate design concept (text model)
2. Create design (image model)
3. Generate 3 variations (editing model)
4. Create mockups (mockup model)
5. Enhance quality (upscale model)
6. Create video ad (video model)
7. Add music (audio model)

### Marketing Content Suite
1. Research topic (web search)
2. Write article (text model)
3. Generate hero image (image model)
4. Create social variants (editing model × 5)
5. Generate video summary (video model)
6. Add voiceover (speech model)

## Dependencies
- replicate_universal: For all AI models
- execution_agent: For chain execution
- memory_agent: For chain templates

## Configuration
- max_chain_length: 20
- max_parallel_models: 5
- auto_retry_failures: true
- save_intermediates: true
- chain_directory: data/model_chains/
