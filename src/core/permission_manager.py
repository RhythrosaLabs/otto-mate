"""
Permission Manager - Tool Access Control
=========================================

Enforces the permissions defined in policies/permissions.yaml
Implements safety checks, budget tracking, and audit logging.

Key Features:
- Tool access level enforcement
- Budget tracking and limits
- Rate limiting
- Audit trail logging
- Pre-execution safety checks
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """Tool permission levels matching safety_rules.md"""
    SAFE_READ = 1
    SAFE_WRITE = 2
    MODERATE_RISK = 3
    HIGH_IMPACT = 4
    DANGEROUS = 5


@dataclass
class PermissionCheck:
    """Result of a permission check."""
    allowed: bool
    reason: str
    requires_confirmation: bool = False
    requires_verification: bool = False
    estimated_cost: float = 0.0
    restrictions: List[str] = None


class PermissionManager:
    """
    Manages tool permissions, budget tracking, and safety enforcement.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize with permissions config."""
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "policies" / "permissions.yaml"
        
        self.config = self._load_config(config_path)
        self.budget_tracker = BudgetTracker(self.config.get("budget", {}))
        self.rate_limiter = RateLimiter(self.config.get("rate_limits", {}))
        self.audit_log = []
        
        logger.info("Permission Manager initialized")
    
    def check_permission(
        self,
        agent_id: str,
        tool_name: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> PermissionCheck:
        """
        Check if an agent has permission to use a tool.
        
        Args:
            agent_id: ID of the agent requesting access
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            context: Additional context
            
        Returns:
            PermissionCheck with decision and requirements
        """
        # 1. Check if agent is allowed to use this tool
        if not self._agent_can_use_tool(agent_id, tool_name):
            return PermissionCheck(
                allowed=False,
                reason=f"Agent '{agent_id}' not authorized for tool '{tool_name}'"
            )
        
        # 2. Get tool configuration
        tool_config = self.config.get("tools", {}).get(tool_name, {})
        
        # 3. Check rate limits
        if not self.rate_limiter.check_limit(tool_name):
            return PermissionCheck(
                allowed=False,
                reason=f"Rate limit exceeded for '{tool_name}'"
            )
        
        # 4. Estimate cost
        estimated_cost = self._estimate_cost(tool_name, parameters)
        
        # 5. Check budget
        if not self.budget_tracker.can_afford(estimated_cost):
            return PermissionCheck(
                allowed=False,
                reason=f"Budget insufficient. Cost: ${estimated_cost:.2f}, Remaining: ${self.budget_tracker.remaining():.2f}"
            )
        
        # 6. Check prerequisites
        prerequisites = tool_config.get("prerequisites", [])
        if prerequisites and context:
            missing = self._check_prerequisites(prerequisites, context)
            if missing:
                return PermissionCheck(
                    allowed=False,
                    reason=f"Missing prerequisites: {', '.join(missing)}"
                )
        
        # 7. Determine requirements
        level = tool_config.get("level", 1)
        requires_verification = tool_config.get("requires_verification", False)
        requires_confirmation = tool_config.get("requires_confirmation", False)
        
        # Auto-upgrade requirements based on cost
        safety_config = self.config.get("safety", {})
        if estimated_cost > safety_config.get("require_confirmation_above", 10.0):
            requires_confirmation = True
        elif estimated_cost > safety_config.get("require_verification_above", 1.0):
            requires_verification = True
        
        return PermissionCheck(
            allowed=True,
            reason="Permission granted",
            requires_confirmation=requires_confirmation,
            requires_verification=requires_verification,
            estimated_cost=estimated_cost,
            restrictions=self._get_agent_restrictions(agent_id)
        )
    
    def record_execution(
        self,
        agent_id: str,
        tool_name: str,
        parameters: Dict[str, Any],
        result: Dict[str, Any],
        actual_cost: float = 0.0,
        verified: bool = False
    ):
        """
        Record tool execution for audit and budget tracking.
        """
        # Update budget
        self.budget_tracker.charge(actual_cost)
        
        # Update rate limiter
        self.rate_limiter.record(tool_name)
        
        # Log for audit
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "tool_name": tool_name,
            "parameters": self._sanitize_params(parameters),
            "result_status": "success" if result.get("success") else "failure",
            "cost": actual_cost,
            "verified": verified,
            "user_session": result.get("session_id", "unknown")
        }
        
        self.audit_log.append(audit_entry)
        logger.info(f"Recorded execution: {agent_id}.{tool_name} - ${actual_cost:.2f}")
    
    def _load_config(self, config_path: Path) -> Dict:
        """Load permissions configuration."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load permissions config: {e}")
            return self._default_config()
    
    def _default_config(self) -> Dict:
        """Return safe default configuration."""
        return {
            "agents": {},
            "tools": {},
            "budget": {"daily_limit": 10.0},
            "rate_limits": {"global": {"requests_per_minute": 10}},
            "safety": {
                "auto_approve_under": 0.10,
                "require_verification_above": 1.00,
                "require_confirmation_above": 10.00
            }
        }
    
    def _agent_can_use_tool(self, agent_id: str, tool_name: str) -> bool:
        """Check if agent is authorized for tool."""
        agent_config = self.config.get("agents", {}).get(agent_id, {})
        allowed_tools = agent_config.get("allowed_tools", [])
        
        # "*" means all tools allowed
        if "*" in allowed_tools:
            return True
        
        return tool_name in allowed_tools
    
    def _estimate_cost(self, tool_name: str, parameters: Dict) -> float:
        """Estimate cost of tool execution."""
        tool_config = self.config.get("tools", {}).get(tool_name, {})
        max_cost = tool_config.get("max_cost", 0.0)
        
        # Could be enhanced with parameter-based estimation
        return max_cost
    
    def _check_prerequisites(self, prerequisites: List[str], context: Dict) -> List[str]:
        """Check which prerequisites are missing."""
        missing = []
        for prereq in prerequisites:
            if not context.get(prereq):
                missing.append(prereq)
        return missing
    
    def _get_agent_restrictions(self, agent_id: str) -> List[str]:
        """Get list of restrictions for agent."""
        agent_config = self.config.get("agents", {}).get(agent_id, {})
        return agent_config.get("restrictions", [])
    
    def _sanitize_params(self, params: Dict) -> Dict:
        """Remove sensitive data from parameters for logging."""
        sanitized = dict(params)
        sensitive_keys = ["api_key", "password", "token", "secret"]
        
        for key in sensitive_keys:
            if key in sanitized:
                sanitized[key] = "***REDACTED***"
        
        return sanitized
    
    def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget status."""
        return self.budget_tracker.status()
    
    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """Get recent audit log entries."""
        return self.audit_log[-limit:]


class BudgetTracker:
    """Tracks spending and enforces budget limits."""
    
    def __init__(self, budget_config: Dict):
        self.daily_limit = budget_config.get("daily_limit", 50.0)
        self.monthly_limit = budget_config.get("monthly_limit", 1000.0)
        self.spent_today = 0.0
        self.spent_this_month = 0.0
        self.last_reset = datetime.now()
    
    def can_afford(self, cost: float) -> bool:
        """Check if we can afford this cost."""
        self._check_reset()
        return (self.spent_today + cost) <= self.daily_limit
    
    def charge(self, cost: float):
        """Charge cost to budget."""
        self._check_reset()
        self.spent_today += cost
        self.spent_this_month += cost
    
    def remaining(self) -> float:
        """Get remaining budget for today."""
        self._check_reset()
        return max(0, self.daily_limit - self.spent_today)
    
    def status(self) -> Dict[str, Any]:
        """Get budget status."""
        self._check_reset()
        return {
            "daily_limit": self.daily_limit,
            "spent_today": self.spent_today,
            "remaining_today": self.remaining(),
            "monthly_limit": self.monthly_limit,
            "spent_this_month": self.spent_this_month,
            "usage_percent": (self.spent_today / self.daily_limit) * 100
        }
    
    def _check_reset(self):
        """Reset daily budget if day has changed."""
        now = datetime.now()
        if now.date() > self.last_reset.date():
            self.spent_today = 0.0
            self.last_reset = now
        
        # Reset monthly if month changed
        if now.month != self.last_reset.month:
            self.spent_this_month = 0.0


class RateLimiter:
    """Enforces rate limits on tool usage."""
    
    def __init__(self, rate_config: Dict):
        self.config = rate_config
        self.usage = defaultdict(list)  # tool_name -> [timestamps]
    
    def check_limit(self, tool_name: str) -> bool:
        """Check if tool can be called now."""
        self._cleanup_old_records()
        
        # Get tool-specific limit or global limit
        limit = self._get_limit(tool_name)
        if not limit:
            return True  # No limit configured
        
        count, window = self._parse_limit(limit)
        recent = self._count_recent(tool_name, window)
        
        return recent < count
    
    def record(self, tool_name: str):
        """Record tool usage."""
        self.usage[tool_name].append(datetime.now())
    
    def _get_limit(self, tool_name: str) -> Optional[str]:
        """Get rate limit for tool."""
        # Check tool-specific first
        if tool_name in self.config.get("by_service", {}):
            return self.config["by_service"][tool_name]
        
        # Fall back to global
        global_config = self.config.get("global", {})
        return f"{global_config.get('requests_per_minute', 100)}/minute"
    
    def _parse_limit(self, limit_str: str) -> tuple:
        """Parse limit string like '10/minute' to (count, seconds)."""
        count, period = limit_str.split("/")
        count = int(count)
        
        period_map = {
            "second": 1,
            "minute": 60,
            "hour": 3600
        }
        
        seconds = period_map.get(period, 60)
        return count, seconds
    
    def _count_recent(self, tool_name: str, window_seconds: int) -> int:
        """Count recent usages within window."""
        cutoff = datetime.now() - timedelta(seconds=window_seconds)
        recent = [ts for ts in self.usage[tool_name] if ts > cutoff]
        return len(recent)
    
    def _cleanup_old_records(self):
        """Remove records older than 1 hour."""
        cutoff = datetime.now() - timedelta(hours=1)
        for tool_name in list(self.usage.keys()):
            self.usage[tool_name] = [
                ts for ts in self.usage[tool_name] if ts > cutoff
            ]
