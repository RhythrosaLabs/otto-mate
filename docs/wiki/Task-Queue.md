# Task Queue & Scheduling

Otto Chat includes a persistent task queue and scheduling system for managing background operations.

---

## Task Queue

### Overview

The task queue manages background tasks with priorities, dependencies, progress tracking, and retry logic. Tasks persist across server restarts.

### Creating Tasks

#### Via Chat
```
"Schedule a task to generate 10 product images tomorrow at 9am"
"Create a daily task to post on social media"
```

#### Via API
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Generate product images",
    "description": "Create 10 new t-shirt designs",
    "priority": "high",
    "scheduled_at": "2026-03-02T09:00:00Z"
  }'
```

#### Via Web UI
Click the **Queue** button (⌘+Q) to open the task queue panel. Use the "+" button to create new tasks.

### Task Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | string | Unique task identifier |
| `title` | string | Task name |
| `description` | string | Detailed description |
| `status` | string | pending, running, completed, failed, cancelled |
| `priority` | string | low, normal, high, urgent |
| `progress` | float | Completion percentage (0–100) |
| `current_step` | string | Current step description |
| `created_at` | datetime | When the task was created |
| `scheduled_at` | datetime | When to execute (null = immediate) |
| `started_at` | datetime | When execution began |
| `completed_at` | datetime | When execution finished |
| `depends_on` | array | Task IDs this depends on |
| `result` | object | Task output data |
| `error` | string | Error message if failed |
| `retries` | int | Number of retry attempts |

### Priority System

| Priority | Order | Use Case |
|----------|-------|----------|
| `urgent` | 1 (first) | Critical operations |
| `high` | 2 | Important but not critical |
| `normal` | 3 | Standard operations |
| `low` | 4 (last) | Background/maintenance tasks |

### Task Dependencies

Tasks can depend on other tasks:

```json
{
  "title": "Publish products",
  "depends_on": ["task_generate_images", "task_create_products"],
  "description": "Publish all products after images and products are created"
}
```

Dependent tasks wait until all dependencies are completed before executing.

### Progress Tracking

Tasks report real-time progress visible in the UI:

```json
{
  "progress": 60,
  "current_step": "Generating image 3 of 5",
  "steps_completed": 3,
  "steps_total": 5
}
```

The web UI shows progress bars and step descriptions in real-time.

---

## Scheduling

### Overview

Otto uses APScheduler for cron-like task scheduling with support for one-time, interval, and cron triggers.

### Scheduling Modes

#### One-Time
Execute a task at a specific date/time:

```bash
curl -X POST http://localhost:8000/api/scheduler/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "trigger": "date",
    "run_date": "2026-03-15T10:00:00",
    "task": "generate_blog_post",
    "params": {"topic": "AI trends"}
  }'
```

#### Interval
Execute a task at regular intervals:

```bash
curl -X POST http://localhost:8000/api/scheduler/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "trigger": "interval",
    "hours": 6,
    "task": "check_inventory",
    "params": {}
  }'
```

#### Cron
Execute on a cron schedule:

```bash
curl -X POST http://localhost:8000/api/scheduler/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "trigger": "cron",
    "hour": 9,
    "minute": 0,
    "day_of_week": "mon-fri",
    "task": "generate_social_post",
    "params": {"topic": "productivity tips"}
  }'
```

### Managing Jobs

```bash
# List all scheduled jobs
curl http://localhost:8000/api/scheduler/jobs

# Remove a job
curl -X DELETE http://localhost:8000/api/scheduler/jobs/job_123

# Get scheduler status
curl http://localhost:8000/api/scheduler/status
```

---

## Calendar View

The web UI includes a calendar view for visualizing scheduled tasks:

- **Monthly/weekly/daily views** — Navigate scheduled tasks
- **Drag-and-drop** — Reschedule tasks
- **Color coding** — Tasks colored by priority
- **Quick create** — Click a date to create a new scheduled task

Access via the **Calendar** tab in the chat interface or press **⌘+J**.

---

## Recurring Task Examples

### Daily Social Media Post
```
"Schedule a daily post at 9am with AI-generated productivity tips"
```

### Weekly Analytics Report
```
"Every Monday at 8am, generate a weekly business analytics report"
```

### Hourly Inventory Check
```
"Check my Shopify inventory levels every 4 hours and alert me if anything is low"
```

### Monthly Newsletter
```
"On the 1st of each month, generate and send a newsletter to my email list"
```

---

## Task Queue API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tasks` | List all tasks |
| POST | `/api/tasks` | Create a task |
| GET | `/api/tasks/{id}` | Get task details |
| DELETE | `/api/tasks/{id}` | Cancel/delete task |
| PUT | `/api/tasks/{id}/priority` | Update priority |
| GET | `/api/tasks/background` | List background tasks |
| GET | `/task_queue` | Frontend-compatible task list |
| POST | `/task_queue` | Frontend-compatible task create |
| DELETE | `/task_queue` | Frontend-compatible task clear |

---

## Business Workflows

Pre-built workflow templates that combine multiple tasks:

| Workflow | Steps |
|----------|-------|
| **Product Launch** | Design → Product → Description → Pricing → Publish |
| **Marketing Campaign** | Research → Strategy → Content → Schedule → Execute |
| **Content Pipeline** | Topic → Research → Write → Edit → Publish |
| **Sales Funnel** | Lead capture → Nurture → Convert → Follow-up |
| **Customer Onboarding** | Welcome → Setup → Training → Check-in |
| **Analytics Dashboard** | Collect → Process → Analyze → Report |
| **Inventory Management** | Monitor → Alert → Reorder → Confirm |
| **Email Sequence** | Design → Segment → Schedule → Send → Analyze |

Execute via:
```bash
curl -X POST http://localhost:8000/workflow \
  -H "Content-Type: application/json" \
  -d '{"workflow": "product_launch", "params": {"product_name": "Sunset Collection"}}'
```
