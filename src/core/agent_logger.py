"""
Agent Logger - Execution Tracing and Replay
============================================

Comprehensive logging system for agent execution with replay capabilities.

Features:
- Structured execution traces
- Decision point logging
- Tool invocation recording
- Error tracking
- Replay capability for debugging
- Performance metrics

Based on production-grade agent debugging patterns.
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of agent events to log."""
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    PLANNING = "planning"
    EXECUTION = "execution"
    VERIFICATION = "verification"
    TOOL_CALL = "tool_call"
    DECISION = "decision"
    ERROR = "error"
    CORRECTION = "correction"


@dataclass
class AgentEvent:
    """A single logged agent event."""
    event_type: EventType
    timestamp: str
    agent_id: str
    session_id: str
    
    # Event-specific data
    data: Dict[str, Any]
    
    # Metadata
    parent_event_id: Optional[str] = None
    duration_ms: Optional[float] = None
    success: bool = True


class AgentLogger:
    """
    Logger for agent execution with structured traces.
    
    Creates detailed execution logs that can be:
    1. Analyzed for debugging
    2. Replayed for testing
    3. Used for performance optimization
    4. Audited for compliance
    """
    
    def __init__(self, log_dir: Optional[str] = None):
        """Initialize agent logger."""
        if log_dir is None:
            log_dir = Path(__file__).parent.parent.parent / "logs" / "agent_traces"
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_traces = {}  # session_id -> trace
        self.event_counter = 0
        
        logger.info(f"Agent Logger initialized: {self.log_dir}")
    
    def start_trace(self, session_id: str, agent_id: str, task: str) -> str:
        """
        Start a new execution trace.
        
        Returns trace_id for reference.
        """
        trace_id = f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{session_id[:8]}"
        
        trace = {
            "trace_id": trace_id,
            "session_id": session_id,
            "agent_id": agent_id,
            "task": task,
            "started_at": datetime.now().isoformat(),
            "events": [],
            "metrics": {
                "total_events": 0,
                "tool_calls": 0,
                "errors": 0,
                "total_cost": 0.0
            }
        }
        
        self.current_traces[session_id] = trace
        
        # Log start event
        self.log_event(
            session_id=session_id,
            agent_id=agent_id,
            event_type=EventType.AGENT_START,
            data={"task": task}
        )
        
        return trace_id
    
    def end_trace(self, session_id: str, success: bool = True, result: Optional[Dict] = None):
        """End an execution trace and save to disk."""
        trace = self.current_traces.get(session_id)
        if not trace:
            logger.warning(f"No active trace for session {session_id}")
            return
        
        trace["ended_at"] = datetime.now().isoformat()
        trace["success"] = success
        trace["result"] = result
        
        # Calculate duration
        started = datetime.fromisoformat(trace["started_at"])
        ended = datetime.fromisoformat(trace["ended_at"])
        trace["duration_seconds"] = (ended - started).total_seconds()
        
        # Save trace to file
        self._save_trace(trace)
        
        # Remove from active traces
        del self.current_traces[session_id]
        
        logger.info(f"Trace ended: {trace['trace_id']}")
    
    def log_event(
        self,
        session_id: str,
        agent_id: str,
        event_type: EventType,
        data: Dict[str, Any],
        parent_event_id: Optional[str] = None,
        success: bool = True
    ) -> str:
        """
        Log an agent event.
        
        Returns event_id for reference.
        """
        trace = self.current_traces.get(session_id)
        if not trace:
            logger.warning(f"No active trace for session {session_id}")
            return ""
        
        self.event_counter += 1
        event_id = f"event_{self.event_counter}"
        
        event = AgentEvent(
            event_type=event_type,
            timestamp=datetime.now().isoformat(),
            agent_id=agent_id,
            session_id=session_id,
            data=data,
            parent_event_id=parent_event_id,
            success=success
        )
        
        # Add to trace
        trace["events"].append(asdict(event))
        trace["metrics"]["total_events"] += 1
        
        # Update metrics
        if event_type == EventType.TOOL_CALL:
            trace["metrics"]["tool_calls"] += 1
            if "cost" in data:
                trace["metrics"]["total_cost"] += data["cost"]
        
        if event_type == EventType.ERROR:
            trace["metrics"]["errors"] += 1
        
        return event_id
    
    def log_decision(
        self,
        session_id: str,
        agent_id: str,
        decision: str,
        reasoning: str,
        alternatives: List[str] = None,
        confidence: float = 1.0
    ):
        """Log an agent decision point for analysis."""
        self.log_event(
            session_id=session_id,
            agent_id=agent_id,
            event_type=EventType.DECISION,
            data={
                "decision": decision,
                "reasoning": reasoning,
                "alternatives": alternatives or [],
                "confidence": confidence
            }
        )
    
    def log_tool_call(
        self,
        session_id: str,
        agent_id: str,
        tool_name: str,
        parameters: Dict[str, Any],
        result: Dict[str, Any],
        duration_ms: float,
        cost: float = 0.0
    ):
        """Log a tool invocation with full details."""
        self.log_event(
            session_id=session_id,
            agent_id=agent_id,
            event_type=EventType.TOOL_CALL,
            data={
                "tool_name": tool_name,
                "parameters": self._sanitize(parameters),
                "result_summary": self._summarize_result(result),
                "success": result.get("success", False),
                "duration_ms": duration_ms,
                "cost": cost
            },
            success=result.get("success", False)
        )
    
    def log_error(
        self,
        session_id: str,
        agent_id: str,
        error: str,
        context: Dict[str, Any],
        recovery_action: Optional[str] = None
    ):
        """Log an error with context for debugging."""
        self.log_event(
            session_id=session_id,
            agent_id=agent_id,
            event_type=EventType.ERROR,
            data={
                "error": str(error),
                "context": context,
                "recovery_action": recovery_action
            },
            success=False
        )
    
    def get_trace(self, session_id: str) -> Optional[Dict]:
        """Get current trace for session."""
        return self.current_traces.get(session_id)
    
    def load_trace(self, trace_id: str) -> Optional[Dict]:
        """Load a saved trace from disk."""
        trace_files = list(self.log_dir.glob(f"{trace_id}*.json"))
        if not trace_files:
            return None
        
        with open(trace_files[0], 'r') as f:
            return json.load(f)
    
    def replay_trace(self, trace_id: str) -> List[Dict]:
        """
        Replay a trace step by step.
        
        Returns list of events in execution order for analysis.
        """
        trace = self.load_trace(trace_id)
        if not trace:
            return []
        
        return trace.get("events", [])
    
    def analyze_trace(self, trace_id: str) -> Dict[str, Any]:
        """
        Analyze a trace for insights.
        
        Returns:
        - Success/failure patterns
        - Performance bottlenecks
        - Error frequency
        - Cost breakdown
        """
        trace = self.load_trace(trace_id)
        if not trace:
            return {}
        
        events = trace.get("events", [])
        
        # Analyze events
        tool_calls = [e for e in events if e["event_type"] == "tool_call"]
        errors = [e for e in events if e["event_type"] == "error"]
        decisions = [e for e in events if e["event_type"] == "decision"]
        
        # Find slowest tools
        slowest_tools = sorted(
            [e for e in tool_calls if e.get("data", {}).get("duration_ms")],
            key=lambda x: x["data"]["duration_ms"],
            reverse=True
        )[:5]
        
        # Calculate averages
        avg_confidence = (
            sum(d["data"].get("confidence", 0) for d in decisions) / len(decisions)
            if decisions else 0
        )
        
        return {
            "trace_id": trace_id,
            "success": trace.get("success", False),
            "duration": trace.get("duration_seconds", 0),
            "total_events": len(events),
            "tool_calls": len(tool_calls),
            "errors": len(errors),
            "decisions": len(decisions),
            "total_cost": trace.get("metrics", {}).get("total_cost", 0),
            "avg_decision_confidence": avg_confidence,
            "slowest_tools": [
                {
                    "tool": e["data"]["tool_name"],
                    "duration_ms": e["data"]["duration_ms"]
                }
                for e in slowest_tools
            ],
            "error_summary": [e["data"]["error"] for e in errors[:5]]
        }
    
    def _save_trace(self, trace: Dict):
        """Save trace to JSON file."""
        trace_file = self.log_dir / f"{trace['trace_id']}.json"
        
        with open(trace_file, 'w') as f:
            json.dump(trace, f, indent=2, default=str)
        
        logger.info(f"Saved trace: {trace_file}")
    
    def _sanitize(self, data: Dict) -> Dict:
        """Remove sensitive data from logs."""
        sanitized = dict(data)
        sensitive = ["api_key", "password", "token", "secret"]
        
        for key in sensitive:
            if key in sanitized:
                sanitized[key] = "***"
        
        return sanitized
    
    def _summarize_result(self, result: Dict) -> Dict:
        """Create compact result summary for logging."""
        return {
            "success": result.get("success", False),
            "has_data": "data" in result,
            "has_error": "error" in result,
            "keys": list(result.keys())[:10]  # Limit key list
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get logging statistics."""
        return {
            "active_traces": len(self.current_traces),
            "total_events_logged": self.event_counter,
            "trace_files": len(list(self.log_dir.glob("*.json")))
        }
