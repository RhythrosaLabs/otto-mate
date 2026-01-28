# Agent Safety Rules and Policies

## Safety Philosophy

**Principle**: Autonomy with accountability. Agents should be empowered to act independently while maintaining safety guardrails and human oversight where needed.

## Tool Access Levels

### Level 1: Safe Read-Only (No Confirmation Required)
These tools can be used freely without risk:
- `search_web`
- `browse_url`
- `research_topic`
- `get_trending_topics`
- `search_images`
- `list_files`
- `get_file`
- `read_file`
- `list_workspace_files`
- `get_storage_stats`

### Level 2: Safe Write (Automatic Approval)
These tools create content but don't affect live systems:
- `generate_image`
- `generate_lifestyle_scene`
- `generate_product_mockup`
- `generate_tshirt_design`
- `upscale_image`
- `remove_background`
- `save_file`
- `save_generated_image`
- `save_image_from_url`
- `create_file` (in workspace only)
- All content generation tools (blog, ad copy, etc.)

### Level 3: Moderate Risk (Budget Check Required)
These tools cost money or create draft products:
- `generate_image` (expensive models)
- `printify_create_product` (creates draft, not published)
- `printify_upload_image`
- `replicate_run_model` (expensive models)
- `execute_python` (limited scope)
- `execute_shell` (read-only commands)

**Rules**:
- Check budget before execution
- Log all operations
- Prevent excessive API calls (rate limit)

### Level 4: High Impact (Verification Required)
These tools publish or modify live systems:
- `printify_publish_product`
- `shopify_create_product`
- `shopify_update_product`
- `shopify_delete_product`
- `shopify_update_inventory`
- `browser_social_post`
- `delete_file`

**Rules**:
- MUST verify results before execution
- MUST check against success criteria
- Log for audit trail
- Allow user review for first-time actions

### Level 5: Dangerous (Explicit Confirmation)
These tools can cause data loss or system changes:
- `execute_shell` (write operations)
- `delete_file` (important files)
- `browser_fill_form` (with payment info)
- `shopify_delete_product` (with sales)
- Any destructive operations

**Rules**:
- MUST get explicit user confirmation
- MUST provide clear explanation of impact
- MUST offer undo/rollback options
- Log everything for debugging

## Temporal Safety Constraints

### Authentication Rules
```
BEFORE accessing ANY external service:
  → Must authenticate (API key check)
  
BEFORE creating products:
  → Must have Printify + Shopify credentials
  
BEFORE posting to social media:
  → Must have platform authorization
```

### Sequencing Rules
```
BEFORE publishing:
  → Must create draft first
  → Must verify content quality
  → Must check against brand guidelines

BEFORE deleting:
  → Must backup data
  → Must confirm no dependencies
  → Must log deletion reason

BEFORE charging costs:
  → Must check budget remaining
  → Must estimate total cost
  → Must log transaction
```

### Prerequisite Checks
```
Product Creation:
  1. Research trends ✓
  2. Generate design ✓
  3. Create product ✓
  4. Verify quality ✓
  5. THEN publish

Marketing Campaign:
  1. Define strategy ✓
  2. Generate content ✓
  3. Review for brand fit ✓
  4. Get user approval ✓
  5. THEN post
```

## Budget & Rate Limiting

### Cost Thresholds
- **Free**: < $0.10 per operation → Auto-approve
- **Low**: $0.10 - $1.00 → Budget check
- **Medium**: $1.00 - $10.00 → Warn user
- **High**: > $10.00 → Require confirmation

### API Rate Limits
- Replicate: Max 10 requests/minute
- Printify: Max 5 products/minute
- Shopify: Max 2 requests/second
- Web search: Max 100 requests/hour
- Image generation: Max 20 images/hour

### Budget Management
```yaml
daily_budget: 50.00  # USD
monthly_budget: 1000.00

per_operation_limits:
  image_generation: 5.00
  model_inference: 10.00
  product_creation: 2.00
  
budget_alerts:
  - threshold: 0.50  # Alert at 50% used
  - threshold: 0.80  # Alert at 80% used
  - threshold: 0.95  # Block at 95% used
```

## Error Handling Policy

### Retry Strategy
```
1st Failure:
  → Retry immediately with same params

2nd Failure:
  → Analyze error
  → Adjust strategy
  → Retry with modifications

3rd Failure:
  → Escalate to user
  → Log detailed error
  → Suggest manual intervention
```

### Fallback Behavior
```
If primary tool fails:
  → Try alternative tool
  → Simplify parameters
  → Reduce scope if needed
  → Report partial success
```

### Graceful Degradation
```
If external service down:
  → Use cached data if available
  → Provide best-effort result
  → Clearly communicate limitations
  → Schedule retry when service recovers
```

## Data Privacy & Security

### User Data Rules
- Never log sensitive info (API keys, passwords)
- Anonymize user data in logs
- Don't store payment information
- Follow GDPR/privacy regulations

### API Key Security
- Keys stored in environment variables only
- Never expose keys in logs or responses
- Rotate keys regularly
- Use read-only keys when possible

### File System Access
```
ALLOWED:
- /data/files/ (user uploads)
- /workspace/ (code execution)
- /logs/ (system logs)

RESTRICTED:
- /src/ (source code)
- /.env (environment config)
- System directories
```

## Kill Switch Protocol

### Emergency Stop Conditions
```
IMMEDIATE STOP if:
- User says "stop", "cancel", "halt"
- Budget exceeded by 10%
- 5 consecutive failures
- Dangerous operation detected
- System health degraded
```

### Graceful Shutdown
```
1. Stop new operations
2. Complete current task if safe
3. Save progress and context
4. Log stop reason
5. Report status to user
```

## Compliance & Audit

### Required Logging
All Level 3+ operations must log:
- Timestamp
- Agent ID
- Tool name and parameters
- Result status
- Cost incurred
- User who initiated
- Verification result

### Audit Trail Format
```json
{
  "timestamp": "2026-01-28T12:00:00Z",
  "agent": "executor",
  "tool": "shopify_create_product",
  "parameters": {"title": "..."},
  "result": "success",
  "cost": 0.00,
  "verified": true,
  "user_id": "session_123"
}
```

## Agent Interaction Rules

### Subagent Communication
- Planner delegates to Executor
- Executor reports to Verifier
- Verifier approves or rejects
- Memory stores learnings

### Conflict Resolution
```
If agents disagree:
  1. Planner reviews task requirements
  2. Verifier checks results independently
  3. If still unclear, escalate to user
  4. Log decision for learning
```

---

**Last Updated**: January 28, 2026  
**Review Schedule**: Monthly  
**Owner**: RhythrosaLabs Security Team
