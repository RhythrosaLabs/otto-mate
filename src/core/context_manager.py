"""
Context Manager - Memory Pruning and Session Management
========================================================

Handles context discipline to prevent "context rot" in long-running agents.

Key Features:
- Short-term and long-term memory separation
- Automatic context pruning
- Session isolation
- Compact state management
- Memory prioritization

Based on Anthropic best practices for sustained agent autonomy.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ContextWindow:
    """A managed context window with automatic pruning."""
    max_interactions: int = 10
    max_tokens: int = 100000
    max_age_hours: int = 24
    
    # Current state
    interactions: deque = None
    total_tokens: int = 0
    created_at: datetime = None
    
    def __post_init__(self):
        if self.interactions is None:
            self.interactions = deque(maxlen=self.max_interactions)
        if self.created_at is None:
            self.created_at = datetime.now()


class ContextManager:
    """
    Manages agent context with disciplined pruning to prevent degradation.
    
    Strategy:
    1. Keep recent interactions in short-term memory (last 10)
    2. Summarize older context
    3. Store artifacts by reference, not content
    4. Prune irrelevant details
    5. Maintain global state compactly
    """
    
    def __init__(self, memory_agent: Any):
        self.memory_agent = memory_agent
        self.windows = {}  # session_id -> ContextWindow
        self.global_state = {}  # Compact global facts
        self.artifact_refs = {}  # ID -> metadata only
        
        logger.info("Context Manager initialized")
    
    def get_context_for_agent(
        self,
        session_id: str,
        agent_type: str,
        include_memories: bool = True
    ) -> Dict[str, Any]:
        """
        Get optimized context for an agent.
        
        Returns minimal necessary context:
        - Recent interactions (not all history)
        - Relevant artifacts (by reference)
        - Compact global state
        - Agent-specific memory
        """
        window = self._get_or_create_window(session_id)
        
        # Build minimal context
        context = {
            "session_id": session_id,
            "agent_type": agent_type,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add recent interactions (last N only)
        context["recent_interactions"] = list(window.interactions)[-5:]
        
        # Add compact global state
        context["global_state"] = self.global_state.copy()
        
        # Add artifact references (not full content)
        context["artifacts"] = {
            ref_id: meta for ref_id, meta in self.artifact_refs.items()
            if meta.get("session_id") == session_id
        }
        
        # Add relevant memories (limited)
        if include_memories:
            memories = self.memory_agent.search(
                session_id=session_id,
                query=context.get("last_message", ""),
                limit=5  # Only top 5 relevant
            )
            context["relevant_memories"] = self._summarize_memories(memories)
        
        return context
    
    def add_interaction(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """Add interaction and automatically prune if needed."""
        window = self._get_or_create_window(session_id)
        
        interaction = {
            "role": role,
            "content": content[:1000],  # Truncate long content
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        window.interactions.append(interaction)
        window.total_tokens += self._estimate_tokens(content)
        
        # Auto-prune if over limit
        if window.total_tokens > window.max_tokens:
            self._prune_window(session_id)
    
    def add_artifact(
        self,
        session_id: str,
        artifact_id: str,
        artifact_type: str,
        metadata: Dict[str, Any]
    ):
        """
        Store artifact by reference, not content.
        
        Instead of including full images/files in context,
        we store metadata and IDs for efficient reference.
        """
        self.artifact_refs[artifact_id] = {
            "session_id": session_id,
            "type": artifact_type,
            "created_at": datetime.now().isoformat(),
            **metadata
        }
    
    def update_global_state(self, key: str, value: Any):
        """Update compact global state."""
        self.global_state[key] = value
    
    def prune_session(self, session_id: str):
        """
        Manually trigger pruning for a session.
        
        Removes old interactions but preserves essential facts.
        """
        self._prune_window(session_id)
    
    def _get_or_create_window(self, session_id: str) -> ContextWindow:
        """Get existing window or create new one."""
        if session_id not in self.windows:
            self.windows[session_id] = ContextWindow()
        return self.windows[session_id]
    
    def _prune_window(self, session_id: str):
        """
        Prune context window to prevent rot.
        
        Strategy:
        1. Keep last 5 interactions as-is
        2. Summarize older interactions
        3. Extract and preserve key facts
        4. Remove redundant information
        """
        window = self.windows.get(session_id)
        if not window:
            return
        
        # Keep recent, summarize old
        if len(window.interactions) > 5:
            old_interactions = list(window.interactions)[:-5]
            recent_interactions = list(window.interactions)[-5:]
            
            # Extract key facts from old interactions
            facts = self._extract_facts(old_interactions)
            for key, value in facts.items():
                self.global_state[key] = value
            
            # Replace window with recent only
            window.interactions = deque(recent_interactions, maxlen=window.max_interactions)
            window.total_tokens = sum(
                self._estimate_tokens(i["content"]) for i in recent_interactions
            )
        
        logger.info(f"Pruned context for session {session_id}")
    
    def _extract_facts(self, interactions: List[Dict]) -> Dict[str, Any]:
        """
        Extract persistent facts from old interactions.
        
        Examples of facts:
        - User preferences
        - Completed tasks
        - Created products
        - Important decisions
        """
        facts = {}
        
        for interaction in interactions:
            metadata = interaction.get("metadata", {})
            
            # Preserve task completions
            if metadata.get("task_completed"):
                task_id = metadata.get("task_id")
                facts[f"completed_{task_id}"] = True
            
            # Preserve created artifacts
            if metadata.get("artifact_created"):
                artifact_id = metadata.get("artifact_id")
                facts[f"artifact_{artifact_id}"] = metadata.get("artifact_type")
            
            # Preserve user preferences
            if metadata.get("user_preference"):
                pref_key = metadata.get("preference_key")
                facts[f"pref_{pref_key}"] = metadata.get("preference_value")
        
        return facts
    
    def _summarize_memories(self, memories: List[Dict]) -> List[Dict]:
        """Summarize memories to reduce context size."""
        return [
            {
                "content": mem.get("content", "")[:200],  # Truncate
                "relevance": mem.get("score", 0.0),
                "timestamp": mem.get("timestamp")
            }
            for mem in memories[:3]  # Only top 3
        ]
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars ≈ 1 token)."""
        return len(text) // 4
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Remove context for old inactive sessions."""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        
        to_remove = []
        for session_id, window in self.windows.items():
            if window.created_at < cutoff:
                to_remove.append(session_id)
        
        for session_id in to_remove:
            del self.windows[session_id]
            logger.info(f"Cleaned up old session: {session_id}")
        
        return len(to_remove)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get context management statistics."""
        total_interactions = sum(
            len(w.interactions) for w in self.windows.values()
        )
        total_tokens = sum(
            w.total_tokens for w in self.windows.values()
        )
        
        return {
            "active_sessions": len(self.windows),
            "total_interactions": total_interactions,
            "total_tokens": total_tokens,
            "global_facts": len(self.global_state),
            "artifact_refs": len(self.artifact_refs)
        }
