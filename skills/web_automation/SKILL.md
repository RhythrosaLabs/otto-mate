# Web Automation Skill

## Description
Advanced browser automation for web scraping, testing, data extraction, form filling, and automated workflows across any website.

## Capabilities
- **Web Scraping**: Extract data from any website
- **Form Automation**: Fill and submit forms
- **Testing**: Automated UI testing
- **Social Media**: Automated posting and interaction
- **Data Collection**: Bulk data extraction
- **Workflow Automation**: Complex multi-step web tasks

## Tools Required
- `browser_navigate`
- `browser_click`
- `browser_type`
- `browser_fill_form`
- `browser_get_page_content`
- `browser_get_text`
- `browser_screenshot`
- `browser_scroll`
- `browser_wait`
- `browser_execute_script`
- `browser_social_post`

## Workflows

### Data Scraping
```yaml
name: Scrape Website Data
steps:
  - Navigate to target URL
  - Wait for page load
  - "Extract desired elements: CSS selectors, XPath queries, Text content"
  - Handle pagination if needed
  - Store extracted data
  - Process and format results

success_criteria:
  - All target data extracted
  - Proper data formatting
  - No missing pages
  - Data validated
```

### Form Submission Automation
```yaml
name: Automate Form Submission
steps:
  - Navigate to form page
  - "Fill form fields: Text inputs, Dropdowns, Checkboxes, Radio buttons"
  - Upload files if needed
  - Solve CAPTCHA if present (manual intervention)
  - Submit form
  - Wait for confirmation
  - Capture confirmation data

success_criteria:
  - Form submitted successfully
  - Confirmation received
  - Data recorded
```

### Social Media Posting
```yaml
name: Post to Social Media
steps:
  - Navigate to platform
  - Login if needed (use stored credentials)
  - Navigate to post creation
  - Fill post content
  - Upload media if needed
  - Set posting options
  - Publish post
  - Capture post URL
  - Verify post is live

success_criteria:
  - Post published successfully
  - Media displayed correctly
  - Post URL captured
```

### Competitor Price Monitoring
```yaml
name: Monitor Competitor Prices
steps:
  - Navigate to competitor product pages
  - Extract product prices
  - Extract availability status
  - Capture product details
  - Store in database
  - Compare to our prices
  - Alert if price changes
  - Schedule next check

success_criteria:
  - All prices extracted
  - Price history tracked
  - Alerts configured
```

## Web Scraping Techniques

### Element Selection
```python
# CSS Selectors
".classname"  # By class
"#id"  # By ID
"tag"  # By tag name
"[attribute='value']"  # By attribute
".parent .child"  # Descendant
".parent > .child"  # Direct child

# XPath
"//div[@class='content']"
"//a[contains(text(), 'Click here')]"
"//input[@type='submit']"
```

### Common Patterns
```yaml
Extract List:
  - Find container element
  - Get all child items
  - Loop through and extract data
  - Store in structured format

Pagination:
  - Find "Next" button
  - Extract data from current page
  - Click next
  - Repeat until last page

Infinite Scroll:
  - Scroll to bottom
  - Wait for new content
  - Extract new items
  - Repeat until no new content
```

### Anti-Detection Strategies
- Random delays between actions (1-3 seconds)
- Vary mouse movements
- Rotate user agents
- Use residential proxies
- Respect robots.txt
- Limit request rate
- Handle CAPTCHAs gracefully

## Form Automation Patterns

### Login Forms
```yaml
steps:
  - Navigate to login page
  - Fill username/email
  - Fill password
  - Click "Remember me" if desired
  - Submit form
  - Wait for redirect
  - Verify logged in
  - Save session if needed
```

### Multi-Step Forms
```yaml
steps:
  - Complete step 1 fields
  - Click "Next"
  - Wait for step 2 to load
  - Complete step 2 fields
  - Click "Next"
  - Continue for all steps
  - Review and submit
  - Capture confirmation
```

### File Uploads
```yaml
steps:
  - Locate file input element
  - Set file path
  - Wait for upload progress
  - Verify upload complete
  - Continue with form
```

## Social Media Automation

### Platform-Specific Actions

#### Instagram
```yaml
Post Photo:
  - Login
  - Click "+ Create"
  - Select photo
  - Add caption
  - Add location
  - Add hashtags
  - Publish

Post Story:
  - Click "+ Your story"
  - Select media
  - Add stickers/text
  - Publish
```

#### Facebook
```yaml
Create Post:
  - Navigate to page
  - Click "Create post"
  - Type content
  - Add media
  - Tag people
  - Set audience
  - Publish

Create Event:
  - Go to Events
  - Click "+ Create Event"
  - Fill event details
  - Set date/time
  - Publish
```

#### Twitter/X
```yaml
Post Tweet:
  - Navigate to home
  - Click tweet compose
  - Type content
  - Add media
  - Add alt text
  - Tweet

Create Thread:
  - Post first tweet
  - Click "+ Add another tweet"
  - Post subsequent tweets
  - Tweet all
```

#### LinkedIn
```yaml
Create Post:
  - Navigate to feed
  - Click "Start a post"
  - Write content
  - Add hashtags
  - Add media if needed
  - Post

Share Article:
  - Click share button
  - Add commentary
  - Tag people/companies
  - Post
```

## Testing Automation

### UI Test Pattern
```yaml
name: Test User Flow
steps:
  - Navigate to starting page
  - Perform action (click, type, etc.)
  - Assert expected result
  - Capture screenshot
  - Continue flow
  - Verify final state
  - Report results

assertions:
  - Element exists
  - Text content matches
  - URL is correct
  - Element is visible
  - Form submitted successfully
```

### Regression Testing
```yaml
name: Run Regression Suite
steps:
  - Load test scenarios
  - "For each scenario: Execute steps, Capture actual results, Compare to expected, Screenshot on failure"
  - Generate test report
  - Alert on failures

success_criteria:
  - All tests pass
  - No regressions introduced
```

## Error Handling

### Common Issues

#### Element Not Found
```yaml
Solution:
  - Wait longer for page load
  - Check selector accuracy
  - Verify element exists on page
  - Try alternative selectors
  - Handle dynamic content
```

#### Timeout Errors
```yaml
Solution:
  - Increase wait time
  - Check network speed
  - Verify page is responding
  - Add retry logic
```

#### CAPTCHA/Bot Detection
```yaml
Solution:
  - Add human-like delays
  - Vary actions
  - Use residential proxies
  - Request manual intervention
  - Use CAPTCHA solving service
```

#### Session Expired
```yaml
Solution:
  - Detect logout state
  - Re-authenticate
  - Resume from last step
  - Save progress frequently
```

## Best Practices
- Always respect robots.txt
- Add delays between requests (1-3 seconds)
- Use polite scraping (don't overload servers)
- Handle errors gracefully
- Take screenshots for debugging
- Log all actions
- Clean up resources (close browsers)
- Rotate user agents
- Use headless mode for production
- Validate extracted data
- Handle dynamic content (AJAX)
- Set reasonable timeouts
- Implement retry logic
- Save progress incrementally

## Advanced Techniques

### JavaScript Execution
```javascript
// Scroll to bottom
await browser_execute_script("window.scrollTo(0, document.body.scrollHeight)")

// Click hidden element
await browser_execute_script("document.querySelector('.hidden-btn').click()")

// Extract data
const data = await browser_execute_script("return document.querySelectorAll('.item').length")

// Modify page
await browser_execute_script("document.querySelector('.ad').remove()")
```

### Handling Dynamic Content
```yaml
AJAX Content:
  - Wait for specific element
  - Check for loading indicators
  - Monitor network requests
  - Use explicit waits

Infinite Scroll:
  - Scroll incrementally
  - Wait for new content
  - Check for end marker

Single Page Apps:
  - Wait for route changes
  - Monitor history API
  - Check URL changes
```

### Data Extraction Patterns
```python
# Extract table data
rows = await browser_get_text("table tr")
data = [row.split("\t") for row in rows]

# Extract lists
items = await browser_get_text("ul.products li")

# Extract with attributes
links = await browser_get_page_content()
# Parse for href attributes

# Extract JSON from page
json_data = await browser_execute_script("return window.__DATA__")
```

## Security Considerations
- Never store passwords in plain text
- Use environment variables for credentials
- Implement rate limiting
- Respect website terms of service
- Use HTTPS when possible
- Validate and sanitize extracted data
- Don't expose sensitive data in logs
- Implement access controls
- Use secure credential storage
- Monitor for suspicious activity

## Performance Optimization
- Use headless mode when possible
- Disable images if not needed
- Disable CSS/JavaScript if not needed
- Use browser pooling
- Implement caching
- Parallelize when appropriate
- Clean up resources promptly
- Use lightweight selectors
- Minimize DOM queries

## Dependencies
- Playwright browser automation
- Stable internet connection
- Target website availability
- Valid credentials (for authenticated actions)

## Metadata
- **Domain**: automation, testing
- **Complexity**: Medium-High
- **Automation Level**: Full
- **Human Verification**: Optional (for CAPTCHA)
