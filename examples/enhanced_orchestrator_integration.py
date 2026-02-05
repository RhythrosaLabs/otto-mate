"""
Example: Integrating New Agentic Systems
=========================================

This example shows how to integrate the new agentic systems
into the existing Otto Universal architecture.
"""

import asyncio
import logging
from datetime import datetime

# Import new systems
from src.core.agent_health_monitor import get_health_monitor, HealthStatus
from src.core.error_recovery import get_recovery_manager
from src.core.agent_analytics import get_analytics
from src.core.agent_communication import get_message_bus

# Import existing components
from src.core.agent_orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)


class EnhancedAgentOrchestrator(AgentOrchestrator):
    """
    Enhanced orchestrator with health monitoring, error recovery,
    analytics, and inter-agent communication.
    """
    
    def __init__(self, anthropic_api_key: str, openai_api_key: str = None, config: dict = None):
        # Initialize base orchestrator
        super().__init__(anthropic_api_key, openai_api_key, config)
        
        # Initialize new systems
        self.health_monitor = get_health_monitor()
        self.recovery_manager = get_recovery_manager()
        self.analytics = get_analytics()
        self.message_bus = get_message_bus()
        
        # Register agents for monitoring
        self._register_agents()
        
        logger.info("Enhanced Agent Orchestrator initialized with monitoring systems")
    
    def _register_agents(self):
        """Register all agents with health monitor and message bus."""
        agents = [
            ("planning", "planner"),
            ("execution", "executor"),
            ("memory", "memory"),
            ("master", "master")
        ]
        
        for agent_id, agent_type in agents:
            self.health_monitor.register_agent(agent_id, agent_type)
            self.message_bus.register_agent(agent_id)
            logger.info(f"Registered agent: {agent_id} ({agent_type})")
    
    async def start_monitoring(self):
        """Start background health monitoring."""
        await self.health_monitor.start_monitoring(interval_seconds=30)
        logger.info("Background health monitoring started")
    
    async def process_with_monitoring(
        self,
        message: str,
        session_id: str = None,
        stream: bool = False
    ):
        """
        Process a message with full monitoring and error recovery.
        
        This wraps the existing process method with:
        - Performance tracking
        - Health monitoring
        - Error recovery
        - Analytics
        """
        start_time = datetime.now()
        task_id = f"task_{start_time.timestamp()}"
        
        # Estimate token usage (rough estimate)
        estimated_tokens = len(message.split()) * 2
        
        try:
            # Execute with error recovery
            success, result, error = await self.recovery_manager.execute_with_recovery(
                service_name="agent_orchestrator",
                func=self.process,
                message=message,
                session_id=session_id,
                stream=stream
            )
            
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            # Record in health monitor
            self.health_monitor.record_task_execution(
                agent_id="planning",
                success=success,
                response_time_ms=duration_ms,
                token_usage=estimated_tokens,
                error=error
            )
            
            # Record in analytics
            self.analytics.record_task_execution(
                task_id=task_id,
                agent_id="planning",
                agent_type="orchestrator",
                start_time=start_time,
                end_time=end_time,
                success=success,
                token_usage=estimated_tokens,
                cost=estimated_tokens * 0.00001,  # Rough cost estimate
                tools_used=["planning_agent", "execution_agent"]
            )
            
            if success:
                return result
            else:
                raise Exception(f"Processing failed: {error}")
                
        except Exception as e:
            logger.error(f"Error in process_with_monitoring: {e}")
            
            # Record failure
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            self.health_monitor.record_task_execution(
                agent_id="planning",
                success=False,
                response_time_ms=duration_ms,
                error=str(e)
            )
            
            self.analytics.record_task_execution(
                task_id=task_id,
                agent_id="planning",
                agent_type="orchestrator",
                start_time=start_time,
                end_time=end_time,
                success=False,
                error=str(e)
            )
            
            raise
    
    async def get_system_status(self) -> dict:
        """Get comprehensive system status."""
        health = self.health_monitor.get_system_health()
        performance = self.analytics.get_system_performance()
        recovery = self.recovery_manager.get_recovery_stats()
        
        return {
            "health": health,
            "performance": performance,
            "recovery": recovery,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_agent_status(self, agent_id: str) -> dict:
        """Get detailed status for a specific agent."""
        health = self.health_monitor.get_agent_health(agent_id)
        profile = self.analytics.get_agent_profile(agent_id)
        
        return {
            "agent_id": agent_id,
            "health_status": health.health_status.value if health else "unknown",
            "success_rate": health.success_rate if health else 0,
            "avg_response_time_ms": health.avg_response_time_ms if health else 0,
            "total_tasks": profile.total_tasks if profile else 0,
            "avg_cost": profile.avg_cost_per_task if profile else 0
        }


# Example usage
async def main():
    """Example of using the enhanced orchestrator."""
    
    # Initialize
    orchestrator = EnhancedAgentOrchestrator(
        anthropic_api_key="your_key_here"
    )
    
    # Start monitoring
    await orchestrator.start_monitoring()
    
    # Process a request with monitoring
    try:
        result = await orchestrator.process_with_monitoring(
            message="Create a t-shirt design with mountains",
            session_id="demo_session"
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Check system status
    status = await orchestrator.get_system_status()
    print(f"\nSystem Status:")
    print(f"  Total Tasks: {status['performance']['total_tasks']}")
    print(f"  Success Rate: {status['performance']['success_rate']}%")
    print(f"  Healthy Agents: {status['health']['healthy_agents']}/{status['health']['total_agents']}")
    
    # Check specific agent
    agent_status = await orchestrator.get_agent_status("planning")
    print(f"\nPlanning Agent:")
    print(f"  Status: {agent_status['health_status']}")
    print(f"  Success Rate: {agent_status['success_rate']}%")
    print(f"  Avg Response Time: {agent_status['avg_response_time_ms']}ms")
    
    # Get analytics report
    analytics = get_analytics()
    report = analytics.get_analytics_report()
    
    print(f"\nPerformance Report:")
    print(f"  Total Cost: ${report['system_performance']['total_cost']:.2f}")
    print(f"  Avg Duration: {report['system_performance']['avg_duration_ms']:.0f}ms")
    
    # Check for bottlenecks
    bottlenecks = report['bottlenecks']
    if bottlenecks:
        print(f"\nBottlenecks Found:")
        for bottleneck in bottlenecks[:3]:
            print(f"  - {bottleneck['type']}: {bottleneck.get('agent_id', bottleneck.get('tool_name'))}")
    
    # Stop monitoring
    await orchestrator.health_monitor.stop_monitoring()


# FastAPI integration example
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Otto Universal with Monitoring")

# Global orchestrator instance
orchestrator: EnhancedAgentOrchestrator = None


@app.on_event("startup")
async def startup():
    """Initialize orchestrator on startup."""
    global orchestrator
    orchestrator = EnhancedAgentOrchestrator(
        anthropic_api_key="your_key_here"
    )
    await orchestrator.start_monitoring()


@app.on_event("shutdown")
async def shutdown():
    """Clean up on shutdown."""
    if orchestrator:
        await orchestrator.health_monitor.stop_monitoring()


class ProcessRequest(BaseModel):
    message: str
    session_id: str = None


@app.post("/api/process")
async def process_message(request: ProcessRequest):
    """Process a message with monitoring."""
    try:
        result = await orchestrator.process_with_monitoring(
            message=request.message,
            session_id=request.session_id
        )
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def get_health():
    """Get system health status."""
    return orchestrator.health_monitor.get_system_health()


@app.get("/api/health/{agent_id}")
async def get_agent_health(agent_id: str):
    """Get health status for a specific agent."""
    health = orchestrator.health_monitor.get_agent_health(agent_id)
    if not health:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    return {
        "agent_id": health.agent_id,
        "agent_type": health.agent_type,
        "health_status": health.health_status.value,
        "total_tasks": health.total_tasks,
        "success_rate": health.success_rate,
        "error_rate": health.error_rate,
        "avg_response_time_ms": health.avg_response_time_ms
    }


@app.get("/api/analytics/performance")
async def get_performance():
    """Get system performance metrics."""
    return orchestrator.analytics.get_system_performance()


@app.get("/api/analytics/bottlenecks")
async def get_bottlenecks():
    """Identify system bottlenecks."""
    return orchestrator.analytics.identify_bottlenecks()


@app.get("/api/analytics/cost")
async def get_cost_analysis(days: int = 7):
    """Get cost analysis."""
    return orchestrator.analytics.get_cost_analysis(days=days)


@app.get("/api/analytics/report")
async def get_analytics_report():
    """Get comprehensive analytics report."""
    return orchestrator.analytics.get_analytics_report()


@app.get("/api/status")
async def get_system_status():
    """Get comprehensive system status."""
    return await orchestrator.get_system_status()


@app.get("/api/recovery/stats")
async def get_recovery_stats():
    """Get error recovery statistics."""
    return orchestrator.recovery_manager.get_recovery_stats()


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
