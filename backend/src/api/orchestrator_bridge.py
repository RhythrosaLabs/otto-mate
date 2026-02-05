"""
Backwards-compatible orchestrator bridge.

This module provides a bridge between the new service layer
and the existing AgentOrchestrator, allowing gradual migration.
"""
import os
from typing import Optional
from src.core.agent_orchestrator import AgentOrchestrator as OldOrchestrator


class OrchestratorBridge:
    """
    Bridge between new architecture and old orchestrator.
    
    This allows the new service layer to work with the existing
    orchestrator while we gradually migrate functionality.
    """
    
    _instance: Optional['OrchestratorBridge'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Initialize old orchestrator
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if not anthropic_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        self.orchestrator = OldOrchestrator(
            anthropic_api_key=anthropic_key,
            openai_api_key=openai_key
        )
        
        self._initialized = True
    
    def get_orchestrator(self) -> OldOrchestrator:
        """Get the orchestrator instance."""
        return self.orchestrator


# Global instance
_bridge = None


def get_orchestrator_bridge() -> OrchestratorBridge:
    """Get or create the orchestrator bridge singleton."""
    global _bridge
    if _bridge is None:
        _bridge = OrchestratorBridge()
    return _bridge


def get_orchestrator() -> OldOrchestrator:
    """Get the orchestrator instance (convenience function)."""
    return get_orchestrator_bridge().get_orchestrator()
