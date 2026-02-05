"""
Agent Performance Analytics System
===================================

Provides comprehensive performance metrics, analytics, and insights for agents.

Features:
- Real-time performance tracking
- Task execution analytics
- Cost and token usage tracking
- Performance trend analysis
- Agent comparison metrics
- Bottleneck identification
"""

import logging
import statistics
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics to track."""
    LATENCY = "latency"
    TOKEN_USAGE = "token_usage"
    COST = "cost"
    SUCCESS_RATE = "success_rate"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"


@dataclass
class PerformanceSnapshot:
    """Point-in-time performance snapshot."""
    timestamp: datetime
    agent_id: str
    metric_type: MetricType
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskExecution:
    """Details of a single task execution."""
    task_id: str
    agent_id: str
    agent_type: str
    start_time: datetime
    end_time: datetime
    duration_ms: float
    success: bool
    token_usage: int
    cost: float
    steps_executed: int
    tools_used: List[str]
    error: Optional[str] = None
    
    @property
    def duration_seconds(self) -> float:
        """Get duration in seconds."""
        return self.duration_ms / 1000.0


@dataclass
class AgentPerformanceProfile:
    """Performance profile for an agent."""
    agent_id: str
    agent_type: str
    
    # Aggregated metrics
    total_tasks: int = 0
    total_duration_ms: float = 0.0
    total_tokens: int = 0
    total_cost: float = 0.0
    
    # Statistical metrics
    avg_duration_ms: float = 0.0
    median_duration_ms: float = 0.0
    p95_duration_ms: float = 0.0
    p99_duration_ms: float = 0.0
    
    avg_tokens_per_task: float = 0.0
    avg_cost_per_task: float = 0.0
    
    success_rate: float = 100.0
    error_rate: float = 0.0
    
    # Tool usage statistics
    tool_usage_count: Dict[str, int] = field(default_factory=dict)
    most_used_tools: List[Tuple[str, int]] = field(default_factory=list)
    
    # Time-based metrics
    tasks_per_hour: float = 0.0
    avg_tasks_per_session: float = 0.0
    
    # Recent performance (for trend analysis)
    recent_durations: deque = field(default_factory=lambda: deque(maxlen=100))
    recent_costs: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def update_metrics(self, execution: TaskExecution):
        """Update profile with new execution."""
        self.total_tasks += 1
        self.total_duration_ms += execution.duration_ms
        self.total_tokens += execution.token_usage
        self.total_cost += execution.cost
        
        # Update recent data
        self.recent_durations.append(execution.duration_ms)
        self.recent_costs.append(execution.cost)
        
        # Recalculate averages
        if self.total_tasks > 0:
            self.avg_duration_ms = self.total_duration_ms / self.total_tasks
            self.avg_tokens_per_task = self.total_tokens / self.total_tasks
            self.avg_cost_per_task = self.total_cost / self.total_tasks
        
        # Calculate percentiles
        if len(self.recent_durations) > 0:
            sorted_durations = sorted(self.recent_durations)
            self.median_duration_ms = statistics.median(sorted_durations)
            
            if len(sorted_durations) >= 20:
                p95_idx = int(len(sorted_durations) * 0.95)
                p99_idx = int(len(sorted_durations) * 0.99)
                self.p95_duration_ms = sorted_durations[p95_idx]
                self.p99_duration_ms = sorted_durations[p99_idx]
        
        # Update tool usage
        for tool in execution.tools_used:
            self.tool_usage_count[tool] = self.tool_usage_count.get(tool, 0) + 1
        
        # Update most used tools
        self.most_used_tools = sorted(
            self.tool_usage_count.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]


class PerformanceAnalytics:
    """
    Comprehensive performance analytics for agent system.
    
    Tracks and analyzes:
    - Task execution metrics
    - Agent performance profiles
    - Cost and token usage
    - Performance trends
    - Bottleneck identification
    """
    
    def __init__(self):
        self.task_executions: List[TaskExecution] = []
        self.agent_profiles: Dict[str, AgentPerformanceProfile] = {}
        self.snapshots: List[PerformanceSnapshot] = []
        
        # Analytics data
        self.hourly_stats: defaultdict = defaultdict(lambda: {
            "tasks": 0,
            "duration_ms": 0,
            "tokens": 0,
            "cost": 0.0
        })
        
        logger.info("Performance Analytics initialized")
    
    def record_task_execution(
        self,
        task_id: str,
        agent_id: str,
        agent_type: str,
        start_time: datetime,
        end_time: datetime,
        success: bool,
        token_usage: int = 0,
        cost: float = 0.0,
        steps_executed: int = 0,
        tools_used: Optional[List[str]] = None,
        error: Optional[str] = None
    ):
        """Record a task execution for analytics."""
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        execution = TaskExecution(
            task_id=task_id,
            agent_id=agent_id,
            agent_type=agent_type,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            success=success,
            token_usage=token_usage,
            cost=cost,
            steps_executed=steps_executed,
            tools_used=tools_used or [],
            error=error
        )
        
        self.task_executions.append(execution)
        
        # Update agent profile
        if agent_id not in self.agent_profiles:
            self.agent_profiles[agent_id] = AgentPerformanceProfile(
                agent_id=agent_id,
                agent_type=agent_type
            )
        
        self.agent_profiles[agent_id].update_metrics(execution)
        
        # Update hourly stats
        hour_key = start_time.strftime("%Y-%m-%d-%H")
        self.hourly_stats[hour_key]["tasks"] += 1
        self.hourly_stats[hour_key]["duration_ms"] += duration_ms
        self.hourly_stats[hour_key]["tokens"] += token_usage
        self.hourly_stats[hour_key]["cost"] += cost
        
        # Create snapshots
        self._create_snapshots(agent_id, execution)
        
        # Keep only recent executions (last 1000)
        if len(self.task_executions) > 1000:
            self.task_executions = self.task_executions[-1000:]
    
    def _create_snapshots(self, agent_id: str, execution: TaskExecution):
        """Create performance snapshots from execution."""
        timestamp = execution.end_time
        
        snapshots = [
            PerformanceSnapshot(
                timestamp=timestamp,
                agent_id=agent_id,
                metric_type=MetricType.LATENCY,
                value=execution.duration_ms
            ),
            PerformanceSnapshot(
                timestamp=timestamp,
                agent_id=agent_id,
                metric_type=MetricType.TOKEN_USAGE,
                value=float(execution.token_usage)
            ),
            PerformanceSnapshot(
                timestamp=timestamp,
                agent_id=agent_id,
                metric_type=MetricType.COST,
                value=execution.cost
            ),
            PerformanceSnapshot(
                timestamp=timestamp,
                agent_id=agent_id,
                metric_type=MetricType.SUCCESS_RATE,
                value=100.0 if execution.success else 0.0
            )
        ]
        
        self.snapshots.extend(snapshots)
        
        # Keep only recent snapshots (last 5000)
        if len(self.snapshots) > 5000:
            self.snapshots = self.snapshots[-5000:]
    
    def get_agent_profile(self, agent_id: str) -> Optional[AgentPerformanceProfile]:
        """Get performance profile for an agent."""
        return self.agent_profiles.get(agent_id)
    
    def get_system_performance(self) -> Dict[str, Any]:
        """Get overall system performance metrics."""
        if not self.task_executions:
            return {
                "total_tasks": 0,
                "avg_duration_ms": 0.0,
                "total_cost": 0.0,
                "total_tokens": 0
            }
        
        total_tasks = len(self.task_executions)
        successful_tasks = sum(1 for t in self.task_executions if t.success)
        total_duration = sum(t.duration_ms for t in self.task_executions)
        total_cost = sum(t.cost for t in self.task_executions)
        total_tokens = sum(t.token_usage for t in self.task_executions)
        
        recent_executions = self.task_executions[-100:] if len(self.task_executions) > 100 else self.task_executions
        recent_durations = [t.duration_ms for t in recent_executions]
        
        return {
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "success_rate": (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "avg_duration_ms": total_duration / total_tasks if total_tasks > 0 else 0,
            "median_duration_ms": statistics.median(recent_durations) if recent_durations else 0,
            "p95_duration_ms": statistics.quantiles(recent_durations, n=20)[18] if len(recent_durations) >= 20 else 0,
            "total_cost": total_cost,
            "avg_cost_per_task": total_cost / total_tasks if total_tasks > 0 else 0,
            "total_tokens": total_tokens,
            "avg_tokens_per_task": total_tokens / total_tasks if total_tasks > 0 else 0,
            "active_agents": len(self.agent_profiles)
        }
    
    def get_performance_trends(
        self,
        agent_id: Optional[str] = None,
        metric_type: Optional[MetricType] = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get performance trends over time."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter snapshots
        filtered = [
            s for s in self.snapshots
            if s.timestamp >= cutoff_time
            and (agent_id is None or s.agent_id == agent_id)
            and (metric_type is None or s.metric_type == metric_type)
        ]
        
        # Group by hour
        hourly_data = defaultdict(list)
        for snapshot in filtered:
            hour_key = snapshot.timestamp.strftime("%Y-%m-%d %H:00")
            hourly_data[hour_key].append(snapshot.value)
        
        # Calculate averages
        trends = []
        for hour_key in sorted(hourly_data.keys()):
            values = hourly_data[hour_key]
            trends.append({
                "timestamp": hour_key,
                "avg_value": statistics.mean(values),
                "min_value": min(values),
                "max_value": max(values),
                "sample_count": len(values)
            })
        
        return trends
    
    def identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks."""
        bottlenecks = []
        
        # Check agent performance
        for agent_id, profile in self.agent_profiles.items():
            # Slow response time
            if profile.avg_duration_ms > 5000:  # > 5 seconds
                bottlenecks.append({
                    "type": "slow_agent",
                    "agent_id": agent_id,
                    "agent_type": profile.agent_type,
                    "avg_duration_ms": profile.avg_duration_ms,
                    "severity": "high" if profile.avg_duration_ms > 10000 else "medium"
                })
            
            # High error rate
            if profile.error_rate > 10:
                bottlenecks.append({
                    "type": "high_error_rate",
                    "agent_id": agent_id,
                    "agent_type": profile.agent_type,
                    "error_rate": profile.error_rate,
                    "severity": "high" if profile.error_rate > 25 else "medium"
                })
            
            # High cost
            if profile.avg_cost_per_task > 0.5:  # > $0.50 per task
                bottlenecks.append({
                    "type": "high_cost",
                    "agent_id": agent_id,
                    "agent_type": profile.agent_type,
                    "avg_cost_per_task": profile.avg_cost_per_task,
                    "severity": "medium"
                })
        
        # Check tool usage
        all_tools = defaultdict(int)
        slow_tools = defaultdict(list)
        
        for execution in self.task_executions[-100:]:  # Last 100 tasks
            for tool in execution.tools_used:
                all_tools[tool] += 1
                if execution.duration_ms > 3000:  # > 3 seconds
                    slow_tools[tool].append(execution.duration_ms)
        
        for tool, durations in slow_tools.items():
            if len(durations) > 5:  # Multiple slow executions
                avg_duration = statistics.mean(durations)
                bottlenecks.append({
                    "type": "slow_tool",
                    "tool_name": tool,
                    "avg_duration_ms": avg_duration,
                    "occurrences": len(durations),
                    "severity": "high" if avg_duration > 10000 else "medium"
                })
        
        return sorted(bottlenecks, key=lambda x: x.get("severity", "low"), reverse=True)
    
    def compare_agents(
        self,
        agent_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Compare performance across agents."""
        if agent_ids is None:
            agent_ids = list(self.agent_profiles.keys())
        
        comparison = {
            "agents": [],
            "metrics": {}
        }
        
        for agent_id in agent_ids:
            profile = self.agent_profiles.get(agent_id)
            if not profile:
                continue
            
            comparison["agents"].append({
                "agent_id": agent_id,
                "agent_type": profile.agent_type,
                "total_tasks": profile.total_tasks,
                "avg_duration_ms": profile.avg_duration_ms,
                "success_rate": profile.success_rate,
                "avg_cost": profile.avg_cost_per_task,
                "avg_tokens": profile.avg_tokens_per_task,
                "most_used_tool": profile.most_used_tools[0] if profile.most_used_tools else None
            })
        
        # Calculate rankings
        if comparison["agents"]:
            comparison["metrics"]["fastest"] = min(
                comparison["agents"],
                key=lambda x: x["avg_duration_ms"]
            )["agent_id"]
            
            comparison["metrics"]["most_accurate"] = max(
                comparison["agents"],
                key=lambda x: x["success_rate"]
            )["agent_id"]
            
            comparison["metrics"]["most_efficient"] = min(
                [a for a in comparison["agents"] if a["avg_cost"] > 0],
                key=lambda x: x["avg_cost"],
                default=None
            )
            if comparison["metrics"]["most_efficient"]:
                comparison["metrics"]["most_efficient"] = comparison["metrics"]["most_efficient"]["agent_id"]
        
        return comparison
    
    def get_cost_analysis(self, days: int = 7) -> Dict[str, Any]:
        """Get cost analysis over time."""
        cutoff_time = datetime.now() - timedelta(days=days)
        recent_executions = [
            e for e in self.task_executions
            if e.start_time >= cutoff_time
        ]
        
        if not recent_executions:
            return {
                "total_cost": 0.0,
                "daily_costs": [],
                "cost_by_agent": {}
            }
        
        # Daily costs
        daily_costs = defaultdict(float)
        for execution in recent_executions:
            day_key = execution.start_time.strftime("%Y-%m-%d")
            daily_costs[day_key] += execution.cost
        
        # Cost by agent
        cost_by_agent = defaultdict(float)
        for execution in recent_executions:
            cost_by_agent[execution.agent_id] += execution.cost
        
        total_cost = sum(e.cost for e in recent_executions)
        
        return {
            "total_cost": total_cost,
            "avg_daily_cost": total_cost / days if days > 0 else 0,
            "daily_costs": [
                {"date": date, "cost": cost}
                for date, cost in sorted(daily_costs.items())
            ],
            "cost_by_agent": [
                {"agent_id": agent_id, "cost": cost, "percentage": (cost / total_cost * 100) if total_cost > 0 else 0}
                for agent_id, cost in sorted(cost_by_agent.items(), key=lambda x: x[1], reverse=True)
            ],
            "projected_monthly_cost": (total_cost / days) * 30 if days > 0 else 0
        }
    
    def get_analytics_report(self) -> Dict[str, Any]:
        """Generate comprehensive analytics report."""
        return {
            "system_performance": self.get_system_performance(),
            "agent_profiles": {
                agent_id: {
                    "agent_type": profile.agent_type,
                    "total_tasks": profile.total_tasks,
                    "avg_duration_ms": profile.avg_duration_ms,
                    "p95_duration_ms": profile.p95_duration_ms,
                    "success_rate": profile.success_rate,
                    "avg_cost": profile.avg_cost_per_task,
                    "most_used_tools": profile.most_used_tools[:5]
                }
                for agent_id, profile in self.agent_profiles.items()
            },
            "bottlenecks": self.identify_bottlenecks(),
            "cost_analysis": self.get_cost_analysis(),
            "generated_at": datetime.now().isoformat()
        }


# Singleton instance
_analytics: Optional[PerformanceAnalytics] = None


def get_analytics() -> PerformanceAnalytics:
    """Get the global performance analytics instance."""
    global _analytics
    if _analytics is None:
        _analytics = PerformanceAnalytics()
    return _analytics
