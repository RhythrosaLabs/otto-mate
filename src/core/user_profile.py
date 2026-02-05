"""
User Profile System - Persistent Memory Across Chats
====================================================

Manages user profiles with preferences, business context, and learnings.
"""

import logging
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class UserProfile:
    """User profile with persistent memory."""
    user_id: str = "default"
    
    # Personal
    name: Optional[str] = None
    email: Optional[str] = None
    preferences: Dict[str, str] = field(default_factory=dict)
    
    # Business
    company_name: Optional[str] = None
    industry: Optional[str] = None
    target_audience: Optional[str] = None
    brand_voice: Optional[str] = None
    website: Optional[str] = None
    
    # Memory
    facts: List[str] = field(default_factory=list)
    learnings: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "UserProfile":
        """Create from dictionary."""
        return cls(**data)


class UserProfileManager:
    """Manages user profiles."""
    
    def __init__(self, storage_path: str = "./data/profiles"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"User Profile Manager initialized: {self.storage_path}")
    
    def load(self, user_id: str = "default") -> UserProfile:
        """Load user profile."""
        profile_file = self.storage_path / f"{user_id}.json"
        
        if profile_file.exists():
            try:
                with open(profile_file) as f:
                    data = json.load(f)
                    profile = UserProfile.from_dict(data)
                    logger.debug(f"Loaded profile: {user_id}")
                    return profile
            except Exception as e:
                logger.error(f"Failed to load profile {user_id}: {e}")
        
        # Create new profile
        profile = UserProfile(user_id=user_id)
        self.save(profile)
        return profile
    
    def save(self, profile: UserProfile):
        """Save user profile."""
        profile.updated_at = datetime.now().isoformat()
        profile_file = self.storage_path / f"{profile.user_id}.json"
        
        try:
            with open(profile_file, 'w') as f:
                json.dump(profile.to_dict(), f, indent=2)
            logger.debug(f"Saved profile: {profile.user_id}")
        except Exception as e:
            logger.error(f"Failed to save profile {profile.user_id}: {e}")
    
    def update(self, user_id: str, updates: Dict) -> UserProfile:
        """Update profile with new data."""
        profile = self.load(user_id)
        
        # Update fields
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        self.save(profile)
        return profile
    
    def add_fact(self, user_id: str, fact: str):
        """Add a fact to user profile."""
        profile = self.load(user_id)
        if fact and fact not in profile.facts:
            profile.facts.append(fact)
            self.save(profile)
            logger.info(f"Added fact to profile {user_id}")
    
    def add_learning(self, user_id: str, learning: str):
        """Add a learning to user profile."""
        profile = self.load(user_id)
        if learning and learning not in profile.learnings:
            profile.learnings.append(learning)
            self.save(profile)
            logger.info(f"Added learning to profile {user_id}")
    
    def add_goal(self, user_id: str, goal: str):
        """Add a goal to user profile."""
        profile = self.load(user_id)
        if goal and goal not in profile.goals:
            profile.goals.append(goal)
            self.save(profile)
            logger.info(f"Added goal to profile {user_id}")
    
    def set_preference(self, user_id: str, key: str, value: str):
        """Set a user preference."""
        profile = self.load(user_id)
        profile.preferences[key] = value
        self.save(profile)
        logger.info(f"Set preference {key} for profile {user_id}")
    
    def get_context(self, user_id: str = "default") -> str:
        """Get user context for AI prompts."""
        profile = self.load(user_id)
        
        context_parts = []
        
        # Personal info
        if profile.name:
            context_parts.append(f"User's name: {profile.name}")
        
        # Business info
        if profile.company_name:
            context_parts.append(f"Company: {profile.company_name}")
        
        if profile.industry:
            context_parts.append(f"Industry: {profile.industry}")
        
        if profile.target_audience:
            context_parts.append(f"Target audience: {profile.target_audience}")
        
        if profile.brand_voice:
            context_parts.append(f"Brand voice: {profile.brand_voice}")
        
        if profile.website:
            context_parts.append(f"Website: {profile.website}")
        
        # Preferences
        if profile.preferences:
            context_parts.append("\nPreferences:")
            for key, value in profile.preferences.items():
                context_parts.append(f"  • {key}: {value}")
        
        # Goals
        if profile.goals:
            context_parts.append("\nGoals:")
            for goal in profile.goals[-5:]:  # Last 5 goals
                context_parts.append(f"  • {goal}")
        
        # Facts
        if profile.facts:
            context_parts.append("\nKnown facts:")
            for fact in profile.facts[-10:]:  # Last 10 facts
                context_parts.append(f"  • {fact}")
        
        # Learnings
        if profile.learnings:
            context_parts.append("\nPast learnings:")
            for learning in profile.learnings[-5:]:  # Last 5 learnings
                context_parts.append(f"  • {learning}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def delete(self, user_id: str) -> bool:
        """Delete a user profile."""
        profile_file = self.storage_path / f"{user_id}.json"
        
        if profile_file.exists():
            try:
                profile_file.unlink()
                logger.info(f"Deleted profile: {user_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete profile {user_id}: {e}")
        
        return False
    
    def list_profiles(self) -> List[str]:
        """List all profile IDs."""
        return [f.stem for f in self.storage_path.glob("*.json")]


# Global manager
_profile_manager: Optional[UserProfileManager] = None


def get_profile_manager() -> UserProfileManager:
    """Get or create the global profile manager."""
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = UserProfileManager()
    return _profile_manager
