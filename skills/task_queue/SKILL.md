# Task Queue Management Skill

## Overview
Autonomous task planning and execution system with priority queue, dependency management, and artifact tracking.

## Capabilities

### queue_task
Add tasks to autonomous execution queue with priority and scheduling.

**Inputs:**
- description: Natural language task description
- priority: low/normal/high/urgent (default: normal)
- schedule_for: Optional datetime for delayed execution
- publish_to: List of platforms to publish results (printify, shopify, youtube, twitter)
- recurring: Boolean for recurring tasks
- recurrence_pattern: daily/weekly/monthly (if recurring=true)

**Outputs:**
- task_id: Unique task identifier
- status: Current task status
- estimated_steps: Number of planned steps

**Example:**
```
queue_task(
    description="Create a cyberpunk husky design, make it into a mug on Printify, and post to Instagram",
    priority="high",
    publish_to=["printify", "instagram"]
)
```

---

### plan_task
Break complex tasks into executable steps with dependencies.

**Inputs:**
- task_id: Task to plan
- context: Additional context for planning

**Outputs:**
- steps: List of planned steps with dependencies
- agents: Required agents for execution
- estimated_duration: Time estimate

---

### execute_task
Run queued tasks with dependency resolution and real-time progress.

**Inputs:**
- task_id: Task to execute
- background: Run in background (default: false)

**Outputs:**
- status: Execution status
- artifacts: Generated content (images, videos, products)
- progress: Percentage complete

---

### track_progress
Monitor task execution status and retrieve results.

**Inputs:**
- task_id: Task to track

**Outputs:**
- status: Current status
- current_step: Which step is executing
- artifacts: Generated artifacts so far
- errors: Any errors encountered

---

### manage_artifacts
Collect and organize generated content from tasks.

**Inputs:**
- task_id: Task to get artifacts from
- artifact_type: Filter by type (image/video/text/product)

**Outputs:**
- artifacts: List of generated content with URLs
- metadata: Creation info and parameters

---

### schedule_recurring
Set up daily/weekly automated tasks.

**Inputs:**
- task_id: Task to make recurring
- pattern: daily/weekly/monthly
- time: Execution time
- enabled: Start/stop recurring execution

**Outputs:**
- schedule_id: Recurring schedule identifier
- next_execution: When task will run next

---

### batch_operations
Process multiple items in parallel.

**Inputs:**
- operations: List of tasks to run
- max_parallel: Maximum concurrent tasks (default: 5)

**Outputs:**
- batch_id: Batch operation identifier
- task_ids: Individual task IDs

---

### priority_management
Control task execution order.

**Inputs:**
- task_id: Task to modify
- priority: New priority level

**Outputs:**
- updated: Confirmation of priority change
- queue_position: New position in queue

## Workflows

### Complete Product Campaign
1. queue_task with product concept
2. Auto-plans: design → mockup → video → product → publish
3. Executes all steps with artifact tracking
4. Publishes to specified platforms

### Recurring Content Schedule
1. schedule_recurring with content type
2. Generates fresh content on schedule
3. Auto-publishes to social media
4. Tracks performance metrics

## Dependencies
- execution_agent: For step execution
- super_planning_agent: For task decomposition
- memory_agent: For context and learning
- All integration tools: replicate, printify, shopify, etc.

## Configuration
- max_queue_size: 100
- default_priority: normal
- auto_execute: true
- save_artifacts: true
- artifact_directory: data/task_artifacts/
