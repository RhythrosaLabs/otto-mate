"""
Planning Agent - Task Decomposition and Strategy
=================================================

DEPRECATED: This module is kept for backwards compatibility.
Use super_planning_agent.py directly - it provides enhanced planning
with fallback strategies, adaptive replanning, and better tool discovery.

The SuperPlanningAgent is exported as PlanningAgent for compatibility.
"""

# Re-export SuperPlanningAgent as PlanningAgent for backwards compatibility
from .super_planning_agent import SuperPlanningAgent, PlanningAgent

__all__ = ['PlanningAgent', 'SuperPlanningAgent']

# Note: Original PlanningAgent implementation has been removed.
# All functionality has been consolidated into SuperPlanningAgent which provides:
# - Multi-strategy problem decomposition
# - Adaptive plan modification
# - Failure recovery and retries
# - Code generation for novel problems
# - Model discovery for AI tasks
