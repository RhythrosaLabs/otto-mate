"""
Agent Health Monitoring System
===============================

Monitors the health and performance of all agents in the system.

Features:
- Real-time agent status tracking
- Performance metrics collection
- Error rate monitoring
- Resource usage tracking
- Automatic health alerts
- Self-healing triggers
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import statistics

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Agent health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    OFFLINE = "offline"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AgentMetrics:
    """Metrics for a single agent."""
    agent_id: str
    agent_type: str
    
    # Performance metrics
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    avg_response_time_ms: float = 0.0
    avg_token_usage: float = 0.0
    
    # Error tracking
    error_count: int = 0
    error_rate: float = 0.0
    recent_errors: deque = field(default_factory=lambda: deque(maxlen=10))
    
    # Resource usage
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    
    # Health indicators
    health_status: HealthStatus = HealthStatus.HEALTHY
    last_health_check: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    
    # Response times for analysis
    _recent_response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    
    @property
    def success_rate(self) -> float:
        """Calculate task success rate."""
        if self.total_tasks == 0:
            return 100.0
        return (self.successful_tasks / self.total_tasks) * 100.0
    
    @property
    def is_responsive(self) -> bool:
        """Check if agent is responsive."""
        if not self.last_activity:
            return False
        return (datetime.now() - self.last_activity) < timedelta(minutes=5)
    
    def record_task(self, success: bool, response_time_ms: float, token_usage: int = 0):
        """Record a task execution."""
        self.total_tasks += 1
        if success:
            self.successful_tasks += 1
        else:
            self.failed_tasks += 1
            self.error_count += 1
        
        # Update response time
        self._recent_response_times.append(response_time_ms)
        if self._recent_response_times:
            self.avg_response_time_ms = statistics.mean(self._recent_response_times)
        
        # Update token usage
        if token_usage > 0:
            self.avg_token_usage = (self.avg_token_usage * 0.9) + (token_usage * 0.1)
        
        # Calculate error rate
        if self.total_tasks > 0:
            self.error_rate = (self.failed_tasks / self.total_tasks) * 100.0
        
        self.last_activity = datetime.now()
    
    def record_error(self, error: str, context: Optional[Dict] = None):
        """Record an error."""
        self.recent_errors.append({
            "error": error,
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        })
        self.error_count += 1


@dataclass
class HealthAlert:
    """Health alert for agent issues."""
    alert_id: str
    agent_id: str
    severity: AlertSeverity
    message: str
    details: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False


class AgentHealthMonitor:
    """
    Monitors health and performance of all agents.
    
    Responsibilities:
    - Track agent metrics in real-time
    - Detect performance degradation
    - Generate health alerts
    - Trigger self-healing actions
    - Provide health dashboards
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        self.alerts: List[HealthAlert] = []
        self.alert_handlers: List[Callable] = []
        
        # Health thresholds
        self.thresholds = {
            "error_rate_warning": 10.0,  # %
            "error_rate_critical": 25.0,  # %
            "response_time_warning": 5000,  # ms
            "response_time_critical": 10000,  # ms
            "success_rate_warning": 90.0,  # %
            "success_rate_critical": 75.0,  # %
            "inactivity_timeout": 300,  # seconds
        }
        self.thresholds.update(self.config.get("health_thresholds", {}))
        
        # Start background monitoring
        self._monitoring_task = None
        self._is_running = False
        
        logger.info("Agent Health Monitor initialized")
    
    def register_agent(self, agent_id: str, agent_type: str) -> AgentMetrics:
        """Register a new agent for monitoring."""
        if agent_id not in self.agent_metrics:
            self.agent_metrics[agent_id] = AgentMetrics(
                agent_id=agent_id,
                agent_type=agent_type,
                last_activity=datetime.now()
            )
            logger.info(f"Registered agent for monitoring: {agent_id} ({agent_type})")
        
        return self.agent_metrics[agent_id]
    
    def record_task_execution(
        self,
        agent_id: str,
        success: bool,
        response_time_ms: float,
        token_usage: int = 0,
        error: Optional[str] = None,
        context: Optional[Dict] = None
    ):
        """Record a task execution for an agent."""
        if agent_id not in self.agent_metrics:
            logger.warning(f"Agent {agent_id} not registered, registering now")
            self.register_agent(agent_id, "unknown")
        
        metrics = self.agent_metrics[agent_id]
        metrics.record_task(success, response_time_ms, token_usage)
        
        if error:
            metrics.record_error(error, context)
        
        # Check health after recording
        self._check_agent_health(agent_id)
    
    def get_agent_health(self, agent_id: str) -> Optional[AgentMetrics]:
        """Get health metrics for a specific agent."""
        return self.agent_metrics.get(agent_id)
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health summary."""
        total_agents = len(self.agent_metrics)
        healthy_agents = sum(
            1 for m in self.agent_metrics.values()
            if m.health_status == HealthStatus.HEALTHY
        )
        
        total_tasks = sum(m.total_tasks for m in self.agent_metrics.values())
        total_errors = sum(m.error_count for m in self.agent_metrics.values())
        
        avg_success_rate = statistics.mean(
            [m.success_rate for m in self.agent_metrics.values()]
        ) if self.agent_metrics else 100.0
        
        return {
            "total_agents": total_agents,
            "healthy_agents": healthy_agents,
            "degraded_agents": total_agents - healthy_agents,
            "total_tasks_executed": total_tasks,
            "total_errors": total_errors,
            "avg_success_rate": avg_success_rate,
            "active_alerts": len([a for a in self.alerts if not a.acknowledged]),
            "timestamp": datetime.now().isoformat()
        }
    
    def _check_agent_health(self, agent_id: str):
        """Check and update agent health status."""
        metrics = self.agent_metrics.get(agent_id)
        if not metrics:
            return
        
        previous_status = metrics.health_status
        
        # Determine health status based on metrics
        if not metrics.is_responsive:
            metrics.health_status = HealthStatus.OFFLINE
        elif metrics.error_rate >= self.thresholds["error_rate_critical"]:
            metrics.health_status = HealthStatus.CRITICAL
        elif (metrics.error_rate >= self.thresholds["error_rate_warning"] or
              metrics.success_rate < self.thresholds["success_rate_critical"]):
            metrics.health_status = HealthStatus.UNHEALTHY
        elif (metrics.avg_response_time_ms >= self.thresholds["response_time_warning"] or
              metrics.success_rate < self.thresholds["success_rate_warning"]):
            metrics.health_status = HealthStatus.DEGRADED
        else:
            metrics.health_status = HealthStatus.HEALTHY
        
        metrics.last_health_check = datetime.now()
        
        # Generate alert if status changed to worse
        if metrics.health_status != previous_status:
            self._generate_health_alert(agent_id, previous_status, metrics)
    
    def _generate_health_alert(
        self,
        agent_id: str,
        previous_status: HealthStatus,
        metrics: AgentMetrics
    ):
        """Generate a health alert."""
        severity = AlertSeverity.INFO
        
        if metrics.health_status == HealthStatus.CRITICAL:
            severity = AlertSeverity.CRITICAL
        elif metrics.health_status == HealthStatus.UNHEALTHY:
            severity = AlertSeverity.ERROR
        elif metrics.health_status == HealthStatus.DEGRADED:
            severity = AlertSeverity.WARNING
        
        alert = HealthAlert(
            alert_id=f"alert_{datetime.now().timestamp()}_{agent_id}",
            agent_id=agent_id,
            severity=severity,
            message=f"Agent {agent_id} health changed from {previous_status.value} to {metrics.health_status.value}",
            details={
                "previous_status": previous_status.value,
                "current_status": metrics.health_status.value,
                "error_rate": metrics.error_rate,
                "success_rate": metrics.success_rate,
                "avg_response_time_ms": metrics.avg_response_time_ms,
                "recent_errors": list(metrics.recent_errors)
            }
        )
        
        self.alerts.append(alert)
        logger.warning(f"Health alert generated: {alert.message}")
        
        # Trigger alert handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")
    
    def add_alert_handler(self, handler: Callable[[HealthAlert], None]):
        """Add a handler for health alerts."""
        self.alert_handlers.append(handler)
    
    async def start_monitoring(self, interval_seconds: int = 30):
        """Start background health monitoring."""
        if self._is_running:
            logger.warning("Monitoring already running")
            return
        
        self._is_running = True
        self._monitoring_task = asyncio.create_task(self._monitor_loop(interval_seconds))
        logger.info(f"Started health monitoring (interval: {interval_seconds}s)")
    
    async def stop_monitoring(self):
        """Stop background health monitoring."""
        self._is_running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped health monitoring")
    
    async def _monitor_loop(self, interval_seconds: int):
        """Background monitoring loop."""
        while self._is_running:
            try:
                # Check all agents
                for agent_id in list(self.agent_metrics.keys()):
                    self._check_agent_health(agent_id)
                
                # Clean old alerts (keep last 100)
                if len(self.alerts) > 100:
                    self.alerts = self.alerts[-100:]
                
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(interval_seconds)
    
    def get_health_report(self) -> Dict[str, Any]:
        """Generate a comprehensive health report."""
        return {
            "system_health": self.get_system_health(),
            "agents": {
                agent_id: {
                    "agent_type": metrics.agent_type,
                    "health_status": metrics.health_status.value,
                    "total_tasks": metrics.total_tasks,
                    "success_rate": metrics.success_rate,
                    "error_rate": metrics.error_rate,
                    "avg_response_time_ms": metrics.avg_response_time_ms,
                    "last_activity": metrics.last_activity.isoformat() if metrics.last_activity else None,
                }
                for agent_id, metrics in self.agent_metrics.items()
            },
            "recent_alerts": [
                {
                    "alert_id": alert.alert_id,
                    "agent_id": alert.agent_id,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "acknowledged": alert.acknowledged
                }
                for alert in self.alerts[-20:]  # Last 20 alerts
            ]
        }


# Singleton instance
_health_monitor: Optional[AgentHealthMonitor] = None


def get_health_monitor() -> AgentHealthMonitor:
    """Get the global health monitor instance."""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = AgentHealthMonitor()
    return _health_monitor
