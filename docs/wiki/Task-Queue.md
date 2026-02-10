# Task Queue

Otto Chat includes a powerful task queue system for managing and scheduling automation tasks.

## Overview

The Task Queue allows you to:

- View all pending, running, and completed tasks
- Track real-time progress of multi-step operations
- Schedule tasks for specific dates and times
- Set priorities and dependencies
- Create recurring tasks

---

## Accessing the Queue

### Via UI

Click the 📋 **Queue** button in the top toolbar.

### Keyboard Shortcut

Press `⌘+Q` (Mac) or `Ctrl+Q` (Windows).

---

## Task States

| State | Icon | Description |
|-------|------|-------------|
| **Pending** | ⏳ | Waiting to start |
| **Running** | 🔄 | Currently executing |
| **Completed** | ✅ | Finished successfully |
| **Failed** | ❌ | Encountered an error |
| **Cancelled** | 🚫 | Manually cancelled |
| **Scheduled** | 📅 | Waiting for scheduled time |

---

## Progress Tracking

### Progress Indicators

Running tasks show:

- **Progress bar** - Visual percentage complete
- **Step info** - Current step / total steps
- **Time elapsed** - Duration since start
- **ETA** - Estimated time remaining

### Live Updates

Progress updates automatically via WebSocket connection. No refresh needed.

---

## Priority System

| Priority | Description | Use Case |
|----------|-------------|----------|
| **Urgent** | Immediate execution | Critical business needs |
| **High** | Next in queue | Important tasks |
| **Normal** | Standard order | Default priority |
| **Low** | After other tasks | Background jobs |

### Setting Priority

Via chat:
```
"Create product images with high priority"
```

Via API:
```json
{
  "message": "Generate report",
  "priority": "high"
}
```

---

## Calendar Integration

### Scheduling Tasks

Click the 📅 calendar icon in the queue sidebar to view scheduled tasks.

#### Schedule via Chat

```
"Tomorrow at 9am, generate the weekly sales report"

"Every Monday at 10am, create social media posts"

"On February 15th, launch the new product line"
```

#### Schedule via UI

1. Open Task Queue
2. Click "Schedule Task"
3. Enter task description
4. Select date and time
5. Set optional recurrence

### Viewing Calendar

The calendar view shows:

- **Today's tasks** - Highlighted
- **Upcoming tasks** - Next 7 days
- **Overdue tasks** - Marked in red
- **Recurring tasks** - With repeat icon

---

## Recurring Tasks

### Recurrence Options

| Pattern | Description |
|---------|-------------|
| **Daily** | Every day at specified time |
| **Weekly** | Same day each week |
| **Monthly** | Same date each month |
| **Custom** | Flexible cron-like schedule |

### Examples

```
"Every day at 8am, check for new orders"

"Every Friday at 5pm, create weekly summary"

"First Monday of each month, generate report"
```

### Managing Recurring Tasks

- Edit individual instances or entire series
- Pause recurrence without deleting
- Skip specific occurrences

---

## Task Dependencies

Chain tasks that depend on each other:

```
"After the product images are done, create the listings"
```

The queue will:
1. Run the first task
2. Wait for completion
3. Pass results to dependent task
4. Execute dependent task

### Dependency Graph

Complex workflows show as a visual graph:

```
Task A ──┬── Task B ── Task D
         │
         └── Task C ──┘
```

---

## Queue Management

### Actions

| Action | Description |
|--------|-------------|
| **Pause** | Stop processing new tasks |
| **Resume** | Continue processing |
| **Clear Completed** | Remove finished tasks |
| **Cancel All** | Stop all pending tasks |
| **Retry Failed** | Re-run failed tasks |

### Filters

Filter tasks by:
- Status (pending, running, completed, failed)
- Priority
- Date range
- Category

### Sorting

Sort by:
- Created date
- Priority
- Status
- Progress

---

## API Endpoints

### List Tasks

```http
GET /api/tasks?status=running&limit=20
```

### Get Task

```http
GET /api/tasks/{task_id}
```

### Cancel Task

```http
POST /api/tasks/{task_id}/cancel
```

### Schedule Task

```http
POST /api/tasks/schedule
Content-Type: application/json

{
  "message": "Generate weekly report",
  "scheduled_for": "2026-02-10T09:00:00Z",
  "priority": "high",
  "recurring": "weekly"
}
```

### Retry Task

```http
POST /api/tasks/{task_id}/retry
```

---

## Best Practices

1. **Use priorities wisely** - Don't make everything urgent
2. **Schedule off-peak** - Run heavy tasks during low-usage times
3. **Chain related tasks** - Use dependencies for workflows
4. **Monitor the queue** - Check for stuck or failed tasks
5. **Clear completed regularly** - Keep the queue manageable
6. **Set realistic schedules** - Account for task duration

---

## Troubleshooting

### Task Stuck in Pending

- Check if queue is paused
- Verify no higher priority tasks
- Check for dependency deadlocks

### Task Keeps Failing

- Check error message in task details
- Verify API keys are valid
- Check external service status

### Schedule Not Running

- Verify server is running at scheduled time
- Check timezone settings
- Ensure task wasn't accidentally cancelled
