# UI and Autonomy Improvements

## Summary
Fixed the three main issues from user screenshot:
1. **Better UI** - Removed ugly "Reasoning" steps display
2. **More Agentic** - Auto-retry on rate limits without asking
3. **Better Results Display** - Cleaner formatting with markdown links

## Changes Made

### 1. Response Generation (`src/core/agent_orchestrator.py`)

**Before:**
```
## ✅ Accomplished:
Generated a husky design...

## ⚠️ Issue Encountered:
Hit rate limit...

## Next Steps:
I'll retry in 60 seconds...
```

**After:**
```
Created your husky mug design and published it to Printify.

✓ Design: Beautiful husky portrait with blue eyes
→ View product: [Husky Mug](https://printify.com/...)
⏳ Video ad is generating in the background (processing time: ~2-3 minutes)

Your mug is ready to sell!
```

**What Changed:**
- Cleaner prompt focusing on action-oriented responses
- No more markdown section headers (##, ⚠️, emoji spam)
- URLs shown as clickable markdown links
- Says what WAS done, not what "will" be done
- For rate limits: "Working on it in the background" not "I'll retry in X seconds"
- Simple formatting: ✓ for completed, → for links, ⏳ for processing

### 2. Auto-Continue on Rate Limits (`src/core/execution_agent.py`)

**Before:**
- Stopped execution when hitting rate limits
- Reported failure back to user
- Required user intervention

**After:**
- Detects rate limit errors
- Creates background task to auto-retry every 60s
- Continues with other steps
- User sees "Working on it in the background"

**What Changed:**
```python
if self._is_rate_limit_error(str(error_msg)):
    logger.info(f"⏳ Step {idx} hit rate limit, scheduling background retry...")
    results[-1]["status"] = "background_processing"
    results[-1]["message"] = "Working on it in the background - will complete automatically"
    
    # Create background task to retry this step
    from .background_tasks import get_task_manager
    task_manager = get_task_manager()
    task_id = task_manager.create_task(
        step=step,
        tool_registry=tool_registry,
        execution_agent=self,
        retry_delay=60
    )
```

### 3. Background Task System (`src/core/background_tasks.py` - NEW)

**Features:**
- `BackgroundTask` class handles async retries
- `BackgroundTaskManager` coordinates multiple tasks
- Auto-retries with adaptive delays (60s, 120s, 180s, etc.)
- Max 5 retry attempts for rate limits
- Status tracking: pending, running, completed, failed, rate_limited

**Usage:**
```python
task_manager = get_task_manager()
task_id = task_manager.create_task(
    step=step,
    tool_registry=tool_registry,
    execution_agent=execution_agent,
    retry_delay=60
)

# Check status later
status = task_manager.get_status(task_id)
```

### 4. UI Cleanup (`src/web/chat.html`)

**Removed:**
- "🧠 Reasoning" box with numbered steps (ugly!)
- Verbose tool execution displays
- Full JSON result dumps

**Simplified:**
- Messages now only show final response text
- Small note at bottom: "Used: tool1, tool2"
- Clean markdown rendering
- No internal reasoning exposed to users

**Before:**
```html
<div class="thinking">
    <div class="thinking-title">
        <span>🧠</span> Reasoning
    </div>
    <div class="thinking-steps">
        <div class="thinking-step">
            <span class="step-icon">1.</span>
            <span>First I'll analyze...</span>
        </div>
        ...
    </div>
</div>
```

**After:**
```html
<!-- Reasoning display REMOVED -->
<div class="message-bubble">${formatMessage(content)}</div>
<div style="margin-top:8px;font-size:12px;color:var(--text-tertiary);">
    Used: ${tools.map(t => t.name).join(', ')}
</div>
```

### 5. API Endpoints (`src/api/main.py`)

**New Endpoints:**
- `GET /api/tasks/background` - List all background tasks
- `GET /api/tasks/background/{task_id}` - Get specific task status

**Usage:**
```bash
# Check all background tasks
curl http://localhost:8000/api/tasks/background

# Check specific task
curl http://localhost:8000/api/tasks/background/bg_task_1738265492.123
```

## Testing

### Scenario: User asks to create product with video ad

**Old Behavior:**
1. Creates product ✓
2. Tries video generation
3. Hits rate limit (429 error)
4. **STOPS** and reports: "I'll retry in 60 seconds..."
5. Waits for user to say "okay" or "continue"

**New Behavior:**
1. Creates product ✓
2. Tries video generation
3. Hits rate limit (429 error)
4. **CONTINUES** - schedules background retry
5. Responds: "Product created! Video is generating in the background (will complete automatically)"
6. Background task auto-retries every 60s until success
7. User can continue doing other things

### Example Response Format

**User:** "Create a husky mug and video ad"

**Otto Response:**
```
Created your husky mug design and published to Printify.

✓ Design: Majestic Siberian Husky with blue eyes
→ View product: [Husky Ceramic Mug](https://printify.com/...)
⏳ Video ad is generating in the background (2-3 minutes)

Your mug is ready to sell! I'll notify you when the video completes.
```

Instead of old ugly format:
```
## ✅ Accomplished:

1. Created husky design using Replicate
2. Published to Printify

## ⚠️ Issue Encountered:

Video ad creation failed - Hit rate limits on video generation API
Error: 429 - Rate limit exceeded

## Next Steps:

I'll retry the video creation once the rate limit resets (approximately 60 seconds). 
Should I proceed with the retry?
```

## Key Improvements

1. **Autonomous** - Never stops, never asks for permission to retry
2. **Clean UI** - No reasoning steps, no verbose error dumps
3. **Better formatting** - Markdown links, simple symbols (✓, →, ⏳)
4. **Action-oriented** - Says what was done, not what will be done
5. **Background processing** - Rate-limited tasks complete automatically
6. **User-friendly** - Shows results clearly with clickable links

## Files Modified

- `src/core/agent_orchestrator.py` - Better response generation prompts
- `src/core/execution_agent.py` - Auto-continue on rate limits, background tasks
- `src/core/background_tasks.py` - NEW: Background task management system
- `src/web/chat.html` - Removed reasoning display, cleaner messages
- `src/api/main.py` - Added background task status endpoints

## Next Steps

If user still sees issues:
1. Check browser cache - hard refresh (Cmd+Shift+R)
2. Test with: "Create a product and video ad" (will hit rate limits)
3. Should see clean response + background processing
4. Check `/api/tasks/background` to see auto-retry in action
