# Task Queue System

The Task Queue provides background task execution, scheduling, dependencies, and calendar integration.

---

## Overview

```
┌───────────────────────────────────────────────────────────────────┐
│                         Task Queue Engine                          │
├───────────────────────────────────────────────────────────────────┤
│                                                                    │
│   ┌─────────────┐     ┌──────────────┐     ┌──────────────┐       │
│   │   Pending   │────▶│   Running    │────▶│  Completed   │       │
│   │   Queue     │     │   Workers    │     │   Storage    │       │
│   └─────────────┘     └──────────────┘     └──────────────┘       │
│          │                   │                    │               │
│          │                   │                    │               │
│   ┌──────▼──────┐     ┌──────▼───────┐    ┌──────▼───────┐       │
│   │  Scheduler  │     │  WebSocket   │    │    Retry     │       │
│   │  (Calendar) │     │   Updates    │    │    Queue     │       │
│   └─────────────┘     └──────────────┘    └──────────────┘       │
│                                                                    │
└───────────────────────────────────────────────────────────────────┘
```

---

## Task States

| State | Description | Icon |
|-------|-------------|------|
| `pending` | Waiting to be executed | ⏳ |
| `scheduled` | Has future execution time | 📅 |
| `running` | Currently being processed | 🔄 |
| `completed` | Successfully finished | ✅ |
| `failed` | Execution failed | ❌ |
| `cancelled` | Manually cancelled | 🚫 |
| `paused` | Temporarily suspended | ⏸️ |

### State Transitions

```
                    ┌──────────────────────────────────────┐
                    ▼                                      │
   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌──────────┐ │
   │ pending │──▶│ running │──▶│completed│   │  failed  │ │
   └─────────┘   └─────────┘   └─────────┘   └──────────┘ │
        │             │                            │      │
        │             └─────────────▶──────────────┘      │
        │                                                 │
        ▼                                                 │
   ┌─────────┐                ┌─────────┐                │
   │scheduled│───────────────▶│cancelled│                │
   └─────────┘                └─────────┘                │
        │                                                 │
        └─────────────────────────────────────────────────┘
                    (when scheduled time arrives)
```

---

## Creating Tasks

### Via UI

1. Click the Task Queue icon in the sidebar
2. Click **"Add Task"** button
3. Fill in task details:
   - **Title**: Brief description
   - **Prompt**: What Otto should do
   - **Priority**: Low, Normal, High, Critical
   - **Schedule**: Optional future time

### Via Chat

Ask Otto naturally:
- "Schedule a task to generate 10 product images tomorrow at 9am"
- "Add to my queue: research top competitors in the coffee industry"
- "Create a recurring task to post on social media every Monday"

### Via API

```bash
# Create a simple task
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Generate product images",
    "prompt": "Create 5 t-shirt mockups with nature themes",
    "priority": "high"
  }'

# Create a scheduled task
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Weekly report",
    "prompt": "Generate analytics report for the past week",
    "scheduled_at": "2024-12-16T09:00:00Z",
    "recurring": "weekly"
  }'
```

---

## Task Priority

| Priority | Value | Behavior |
|----------|-------|----------|
| `critical` | 4 | Executes immediately, interrupts queue |
| `high` | 3 | Moves to front of queue |
| `normal` | 2 | Standard FIFO order |
| `low` | 1 | Executes when queue is empty |

Priority affects execution order but not scheduled times.

---

## Scheduling Options

### One-Time Schedule

Execute task at specific date/time:

```json
{
  "title": "Black Friday sale",
  "prompt": "Update all product prices with 30% discount",
  "scheduled_at": "2024-11-29T00:00:00Z"
}
```

### Recurring Tasks

| Pattern | Description |
|---------|-------------|
| `hourly` | Every hour |
| `daily` | Every day at same time |
| `weekly` | Every week on same day |
| `monthly` | Every month on same date |
| `custom` | Cron expression |

```json
{
  "title": "Daily backup",
  "prompt": "Export all data to backup storage",
  "scheduled_at": "2024-12-15T02:00:00Z",
  "recurring": "daily"
}
```

### Cron Expressions

For complex schedules:

```json
{
  "title": "Quarterly report",
  "prompt": "Generate quarterly business report",
  "cron": "0 9 1 */3 *"
}
```

| Field | Values |
|-------|--------|
| Minute | 0-59 |
| Hour | 0-23 |
| Day of Month | 1-31 |
| Month | 1-12 |
| Day of Week | 0-6 (0=Sunday) |

---

## Task Dependencies

Tasks can depend on other tasks:

```json
{
  "title": "Upload products to Shopify",
  "prompt": "Push all new products to Shopify store",
  "depends_on": ["task_abc123", "task_def456"]
}
```

The task won't execute until all dependencies are `completed`.

### Dependency Chain Example

```
┌─────────────────┐
│ Generate Images │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Create Products │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Publish to Shop │
└─────────────────┘
```

---

## Calendar Integration

The Task Queue integrates with a visual calendar.

### Viewing Calendar

1. Click Task Queue icon in sidebar
2. Click the **Calendar** tab
3. View scheduled tasks by day/week/month

### Calendar Features

| Feature | Description |
|---------|-------------|
| Drag & Drop | Move tasks to reschedule |
| Quick Add | Click on date to add task |
| Color Coding | By priority level |
| Recurring Indicators | Icon for repeating tasks |
| Conflict Detection | Warns of overlapping tasks |

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `←` / `→` | Navigate days |
| `T` | Jump to today |
| `M` | Month view |
| `W` | Week view |
| `D` | Day view |

---

## Monitoring Tasks

### Real-Time Updates

WebSocket events stream task updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'task_update') {
    console.log(`Task ${data.task_id}: ${data.status}`);
  }
};
```

### Event Types

| Event | Description |
|-------|-------------|
| `task_created` | New task added |
| `task_started` | Execution began |
| `task_progress` | Progress update (0-100%) |
| `task_completed` | Successfully finished |
| `task_failed` | Execution failed |
| `task_cancelled` | Manually cancelled |

---

## Retry System

Failed tasks can automatically retry.

### Retry Configuration

```json
{
  "title": "API call",
  "prompt": "Fetch data from external API",
  "retry": {
    "max_attempts": 3,
    "delay": 60,
    "backoff": "exponential"
  }
}
```

| Option | Description | Default |
|--------|-------------|---------|
| `max_attempts` | Total attempts | 3 |
| `delay` | Seconds between retries | 60 |
| `backoff` | `linear`, `exponential`, `fixed` | `exponential` |

### Backoff Strategies

| Strategy | Delay Pattern |
|----------|---------------|
| `fixed` | 60s, 60s, 60s |
| `linear` | 60s, 120s, 180s |
| `exponential` | 60s, 120s, 240s |

---

## API Reference

### List Tasks

```bash
GET /api/tasks
GET /api/tasks?status=pending
GET /api/tasks?priority=high
GET /api/tasks?from=2024-12-01&to=2024-12-31
```

### Get Task Details

```bash
GET /api/tasks/{task_id}
```

### Update Task

```bash
PUT /api/tasks/{task_id}
Content-Type: application/json

{
  "priority": "critical",
  "scheduled_at": "2024-12-20T10:00:00Z"
}
```

### Cancel Task

```bash
DELETE /api/tasks/{task_id}
```

### Pause/Resume Task

```bash
POST /api/tasks/{task_id}/pause
POST /api/tasks/{task_id}/resume
```

### Retry Failed Task

```bash
POST /api/tasks/{task_id}/retry
```

### Get Task Output

```bash
GET /api/tasks/{task_id}/output
```

---

## Best Practices

### Task Design

1. **Atomic Tasks**: Make tasks do one thing well
2. **Clear Prompts**: Be specific in task descriptions
3. **Error Handling**: Use retry for network-dependent tasks
4. **Dependencies**: Break complex workflows into dependent tasks

### Scheduling

1. **Spread Load**: Don't schedule many tasks at same time
2. **Off-Peak**: Run heavy tasks during low-usage hours
3. **Buffer Time**: Account for variable execution times
4. **Timezone**: All times are UTC unless specified

### Monitoring

1. **Check Failures**: Review failed tasks regularly
2. **Set Alerts**: Configure notifications for critical failures
3. **Clean Up**: Archive old completed tasks
4. **Logs**: Check task logs for optimization opportunities

---

## Troubleshooting

### Task Stuck in "Running"

```bash
# Force cancel
curl -X POST http://localhost:8000/api/tasks/{task_id}/force-cancel

# Or restart the worker
curl -X POST http://localhost:8000/api/admin/restart-workers
```

### Dependencies Not Resolving

Check that all dependency tasks exist and are completed:

```bash
curl http://localhost:8000/api/tasks/{task_id}/dependencies
```

### Scheduled Tasks Not Executing

1. Verify server timezone settings
2. Check that scheduler service is running
3. Ensure `scheduled_at` is in the future
