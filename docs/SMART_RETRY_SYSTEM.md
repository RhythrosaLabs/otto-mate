# Smart Retry & Auto-Healing System

Otto now features an intelligent retry system that automatically diagnoses and fixes errors without requiring user intervention.

## Overview

When a tool execution fails, Otto will:
1. **Analyze the error** to determine if it's fixable
2. **Apply automatic fixes** based on error patterns
3. **Retry the operation** with corrected parameters
4. **Use exponential backoff** for rate limits and server errors

This eliminates the frustration of single-attempt failures and makes Otto truly autonomous.

## Features

### 1. Parameter Auto-Fixing

**Problem**: Tool receives wrong or missing parameters
**Solution**: Inspect function signature and add missing parameters with smart defaults

```python
# User request: "create a video"
# Missing parameters: duration, quality, format

# Otto automatically adds:
{
    "duration": 15,      # Smart default for video
    "quality": "high",   # Professional quality
    "format": "mp4"      # Standard format
}
```

**Smart defaults by parameter type:**
- `prompt/text/content` → Use description or title
- `width/height` → 1024 (standard resolution)
- `duration` → 15 seconds (video) or 30 seconds (audio)
- `style/art_style` → "professional"
- `format` → "png" (images) or "mp4" (video)
- `quality` → "high"
- `model` → "flux-schnell" (images) or "stable-video" (video)

### 2. Known Error Detection

Otto recognizes common API errors and applies specific fixes:

#### Printify Errors
- **Error 10300** (Image upload failed): 
  - Detects WebP format issues
  - Image already auto-converted to PNG in upload_image()
  - Retries with proper format

- **Unauthorized**: 
  - Reports missing API credentials
  - Does not retry (requires user action)

#### Replicate Errors
- **Rate Limit (429)**: 
  - Applies exponential backoff
  - Retries automatically

- **Model Not Found (404)**: 
  - Reports invalid model
  - Does not retry

#### Video Generation Errors
- **Missing Prompt**: 
  - Uses description or title as prompt
  - Retries with added prompt

- **Invalid Duration**: 
  - Sets to 15 seconds default
  - Retries with fixed duration

#### Network Errors
- **Timeout/Connection**: Always retries with backoff
- **Server Errors (500-504)**: Always retries with backoff

### 3. Exponential Backoff

For temporary errors, Otto waits progressively longer between retries:
- Attempt 1: Immediate
- Attempt 2: Wait 2 seconds (2^1)
- Attempt 3: Wait 4 seconds (2^2)

This prevents overwhelming APIs and respects rate limits.

### 4. Image Format Conversion

The Printify integration automatically converts images to PNG:
- Downloads image from URL
- Opens with PIL (Python Imaging Library)
- Converts RGBA/LA/P modes to RGB with white background
- Saves as optimized PNG
- Base64 encodes for upload

This ensures compatibility with Printify's image requirements.

## Configuration

Default settings in `execution_agent.py`:
```python
max_retries: int = 3  # Maximum retry attempts
```

Adjust in code if needed for specific use cases.

## Implementation Details

### Core Components

**1. `execute_tool()` - Main execution loop**
```python
for attempt in range(max_retries):
    try:
        result = await tool_func(**parameters)
        return {"success": True, "data": result}
    except TypeError as e:
        # Auto-fix parameter mismatches
        fixed_params = await self._fix_parameter_error(...)
        if fixed_params:
            parameters = fixed_params
            continue
    except Exception as e:
        # Analyze API errors
        should_retry, fixed_params = await self._analyze_and_fix_error(...)
        if should_retry:
            await asyncio.sleep(2 ** attempt)
            continue
```

**2. `_fix_parameter_error()` - Parameter analysis**
- Uses `inspect.signature()` to get expected parameters
- Compares with provided parameters
- Removes unexpected parameters
- Adds missing parameters with smart defaults

**3. `_analyze_and_fix_error()` - Error pattern matching**
- Parses error messages for known patterns
- Returns (should_retry, fixed_parameters)
- Applies tool-specific fixes

**4. `_get_smart_default()` - Default value generation**
- Analyzes parameter name and tool context
- Returns appropriate default value
- Falls back to None if unknown

### Error Flow

```
User Request
    ↓
Execute Tool (Attempt 1)
    ↓
Error Occurs
    ↓
TypeError? → Fix Parameters → Retry
    ↓
API Error? → Analyze Error
    ↓
Known Pattern? → Apply Fix → Backoff → Retry
    ↓
Unknown Error? → Report Failure
```

## Examples

### Example 1: Missing Video Parameters

```
Request: "Generate a product video"
Initial params: {"prompt": "product showcase"}
Missing: duration, format

Auto-fix adds:
  duration = 15
  format = "mp4"

✅ Retry succeeds
```

### Example 2: Printify Image Upload

```
Request: "Create a mug with my design"
Initial params: {"image_url": "https://example.com/design.webp"}

Error: 10300 (Upload failed)
Detection: WebP format issue
Auto-fix: Image already converted to PNG in upload_image()

✅ Retry succeeds
```

### Example 3: Rate Limit

```
Request: "Generate multiple images"

Error: 429 Rate Limit
Detection: Rate limit pattern
Auto-fix: None needed
Wait: 2 seconds (attempt 2)

✅ Retry succeeds
```

## Logging

All retry attempts are logged for debugging:

```
INFO: Executing create_video (attempt 1/3) with params: {...}
WARNING: Parameter error on attempt 1: missing required positional argument: 'duration'
INFO: Adding missing parameter duration = 15
INFO: Auto-fixed parameters, retrying...
INFO: Executing create_video (attempt 2/3) with params: {...}
INFO: Tool create_video completed successfully
```

## Benefits

1. **Eliminates user frustration** - No more "why did it fail?"
2. **Increases success rate** - Most common errors auto-fixed
3. **Saves time** - No manual parameter adjustment needed
4. **Professional behavior** - Otto handles errors gracefully
5. **True autonomy** - Works without constant user supervision

## Future Enhancements

Potential improvements:
- [ ] LLM-based error analysis for complex unknown errors
- [ ] Learning from past failures to improve future fixes
- [ ] User-configurable retry strategies per tool
- [ ] Detailed retry statistics and success rates
- [ ] Auto-discovery of new error patterns

## Testing

Test the system with intentional errors:

```bash
# Missing parameters
"Generate a video"

# Image format issues  
"Create mug with WebP design"

# Rate limits
"Generate 10 images rapidly"
```

All should self-heal and succeed.
