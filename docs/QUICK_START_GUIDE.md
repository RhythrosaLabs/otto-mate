# Quick Start Guide - New Agentic Systems

## 🚀 Quick Reference

### Health Monitoring

```python
from src.core.agent_health_monitor import get_health_monitor

# Initialize
monitor = get_health_monitor()

# Register agents
monitor.register_agent("agent-001", "planner")

# Record task
monitor.record_task_execution(
    agent_id="agent-001",
    success=True,
    response_time_ms=1500,
    token_usage=500
)

# Check health
health = monitor.get_agent_health("agent-001")
print(f"Status: {health.health_status.value}")
print(f"Success Rate: {health.success_rate}%")

# Get system overview
system = monitor.get_system_health()
print(f"Total Tasks: {system['total_tasks_executed']}")
```

### Error Recovery

```python
from src.core.error_recovery import get_recovery_manager

manager = get_recovery_manager()

# Execute with recovery
success, result, error = await manager.execute_with_recovery(
    service_name="api_service",
    func=my_api_call,
    param1="value",
    max_retries=3
)

if success:
    print(f"Result: {result}")
else:
    print(f"Failed: {error}")

# Check recovery stats
stats = manager.get_recovery_stats()
print(f"Circuit Breakers: {stats['circuit_breakers']}")
```

### Performance Analytics

```python
from src.core.agent_analytics import get_analytics

analytics = get_analytics()

# Record execution
analytics.record_task_execution(
    task_id="task-123",
    agent_id="agent-001",
    agent_type="planner",
    start_time=start,
    end_time=end,
    success=True,
    token_usage=500,
    cost=0.02,
    tools_used=["tool1", "tool2"]
)

# Get metrics
performance = analytics.get_system_performance()
print(f"Avg Duration: {performance['avg_duration_ms']}ms")
print(f"Total Cost: ${performance['total_cost']}")

# Find bottlenecks
bottlenecks = analytics.identify_bottlenecks()
for bottleneck in bottlenecks:
    print(f"Issue: {bottleneck['type']}")
    print(f"Severity: {bottleneck['severity']}")

# Cost analysis
costs = analytics.get_cost_analysis(days=7)
print(f"Projected Monthly: ${costs['projected_monthly_cost']}")
```

### Inter-Agent Communication

```python
from src.core.agent_communication import get_message_bus

bus = get_message_bus()

# Register agents
agent1 = bus.register_agent("agent-001")
agent2 = bus.register_agent("agent-002")

# Send message
await agent1.send(
    to_agent="agent-002",
    content={"action": "process", "data": "..."}
)

# Request/response
response = await agent1.request(
    to_agent="agent-002",
    content={"query": "status"},
    timeout=10.0
)

# Pub/sub
agent1.subscribe("task_completed")
await agent2.publish(
    topic="task_completed",
    content={"task_id": "123"}
)

# Collaboration
collab_id = await bus.initiate_collaboration(
    initiator_agent="master",
    participating_agents=["agent-001", "agent-002"],
    task_description="Process data",
    shared_context={"data": "..."}
)
```

## 📊 Monitoring Dashboard Data

### System Health Endpoint
```python
GET /api/health
{
    "total_agents": 5,
    "healthy_agents": 4,
    "degraded_agents": 1,
    "total_tasks_executed": 1234,
    "total_errors": 45,
    "avg_success_rate": 96.5
}
```

### Agent Health Endpoint
```python
GET /api/health/agent-001
{
    "agent_type": "planner",
    "health_status": "healthy",
    "total_tasks": 250,
    "success_rate": 98.0,
    "error_rate": 2.0,
    "avg_response_time_ms": 1500,
    "last_activity": "2026-01-28T10:30:00Z"
}
```

### Performance Metrics
```python
GET /api/analytics/performance
{
    "total_tasks": 1234,
    "successful_tasks": 1189,
    "success_rate": 96.35,
    "avg_duration_ms": 2345,
    "median_duration_ms": 1800,
    "p95_duration_ms": 5000,
    "total_cost": 124.50,
    "avg_cost_per_task": 0.10
}
```

### Bottlenecks
```python
GET /api/analytics/bottlenecks
[
    {
        "type": "slow_tool",
        "tool_name": "image_generator",
        "avg_duration_ms": 8500,
        "severity": "high"
    },
    {
        "type": "high_error_rate",
        "agent_id": "agent-003",
        "error_rate": 15.5,
        "severity": "medium"
    }
]
```

## 🔧 Configuration Examples

### Health Thresholds
```python
config = {
    "health_thresholds": {
        "error_rate_warning": 10.0,      # Warn at 10% errors
        "error_rate_critical": 25.0,     # Critical at 25%
        "response_time_warning": 5000,   # Warn at 5s
        "response_time_critical": 10000, # Critical at 10s
        "success_rate_warning": 90.0,    # Warn below 90%
        "success_rate_critical": 75.0    # Critical below 75%
    }
}

monitor = AgentHealthMonitor(config)
```

### Circuit Breaker
```python
CircuitBreaker(
    service_name="external_api",
    failure_threshold=5,      # Open after 5 failures
    success_threshold=2,      # Close after 2 successes
    timeout_seconds=60.0      # Retry after 60s
)
```

### Error Patterns
```python
ErrorPattern(
    pattern="rate limit|429",
    severity=ErrorSeverity.RATE_LIMIT,
    retry_strategy="backoff",
    max_retries=5,
    backoff_base=2.0,
    backoff_max=120.0
)
```

## 🎯 Common Use Cases

### 1. Monitor Agent Health
```python
# Start monitoring all agents
monitor = get_health_monitor()
await monitor.start_monitoring(interval_seconds=30)

# Check specific agent
health = monitor.get_agent_health("agent-001")
if health.health_status != HealthStatus.HEALTHY:
    print(f"Alert: Agent {agent_id} is {health.health_status.value}")
```

### 2. Handle API Failures
```python
# Wrap API calls with recovery
manager = get_recovery_manager()
success, result, error = await manager.execute_with_recovery(
    service_name="printify_api",
    func=create_product,
    **product_params
)
```

### 3. Track Costs
```python
# Analyze costs over time
analytics = get_analytics()
costs = analytics.get_cost_analysis(days=30)
print(f"Monthly cost: ${costs['projected_monthly_cost']}")

# Find expensive agents
report = analytics.get_analytics_report()
for agent_id, profile in report['agent_profiles'].items():
    if profile['avg_cost'] > 0.50:
        print(f"Expensive: {agent_id} - ${profile['avg_cost']}/task")
```

### 4. Coordinate Multiple Agents
```python
# Set up collaboration
bus = get_message_bus()
collab_id = await bus.initiate_collaboration(
    initiator_agent="master",
    participating_agents=["planner", "executor", "verifier"],
    task_description="Complete product creation",
    shared_context={"product_id": "123"},
    coordination_strategy="sequential"
)

# Monitor collaboration
collab = bus.get_collaboration(collab_id)
print(f"Status: {collab.status}")
```

## 🐛 Debugging Tips

### View Recent Errors
```python
# Get error history
manager = get_recovery_manager()
stats = manager.get_recovery_stats()
for error in stats['recent_errors']:
    print(f"{error['timestamp']}: {error['error']}")
```

### Check Agent Performance
```python
# Get detailed agent profile
analytics = get_analytics()
profile = analytics.get_agent_profile("agent-001")
print(f"P95 latency: {profile.p95_duration_ms}ms")
print(f"Most used tools: {profile.most_used_tools}")
```

### Review Message History
```python
# Get recent messages
bus = get_message_bus()
history = bus.get_message_history(
    agent_id="agent-001",
    limit=50
)
for msg in history:
    print(f"{msg.from_agent} -> {msg.to_agent}: {msg.content}")
```

## 📈 Performance Optimization

### Identify Slow Operations
```python
analytics = get_analytics()
bottlenecks = analytics.identify_bottlenecks()
for b in bottlenecks:
    if b['type'] == 'slow_tool':
        print(f"Optimize: {b['tool_name']} ({b['avg_duration_ms']}ms)")
```

### Monitor Resource Usage
```python
monitor = get_health_monitor()
for agent_id, metrics in monitor.agent_metrics.items():
    print(f"{agent_id}:")
    print(f"  Response time: {metrics.avg_response_time_ms}ms")
    print(f"  Token usage: {metrics.avg_token_usage}")
```

### Compare Agent Efficiency
```python
analytics = get_analytics()
comparison = analytics.compare_agents()
print(f"Fastest: {comparison['metrics']['fastest']}")
print(f"Most accurate: {comparison['metrics']['most_accurate']}")
print(f"Most efficient: {comparison['metrics']['most_efficient']}")
```

## 🔔 Alert Handling

### Set Up Alert Handler
```python
def handle_alert(alert):
    if alert.severity == AlertSeverity.CRITICAL:
        # Send email/Slack notification
        notify_team(alert.message)
    
    # Log to external system
    log_alert(alert)

monitor = get_health_monitor()
monitor.add_alert_handler(handle_alert)
```

### Get Recent Alerts
```python
report = monitor.get_health_report()
for alert in report['recent_alerts']:
    if not alert['acknowledged']:
        print(f"[{alert['severity']}] {alert['message']}")
```

## 💡 Best Practices

1. **Always register agents** with health monitor on initialization
2. **Wrap external API calls** with error recovery
3. **Record all executions** in analytics for metrics
4. **Use message bus** for agent coordination instead of direct calls
5. **Monitor health regularly** with background monitoring
6. **Set appropriate thresholds** based on your SLAs
7. **Review analytics weekly** to identify optimization opportunities
8. **Act on alerts promptly** to prevent cascading issues

---

For complete documentation, see:
- `AGENTIC_IMPROVEMENTS.md` - Full feature documentation
- `IMPROVEMENTS_SUMMARY.md` - Implementation summary
- `docs/AGENTIC_ARCHITECTURE.md` - Architecture overview
