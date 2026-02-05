"""
Profile API
===========

Endpoints for managing user profiles and persistent memory.
"""

import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.user_profile import get_profile_manager, UserProfile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileUpdate(BaseModel):
    """Profile update request."""
    name: Optional[str] = None
    email: Optional[str] = None
    company_name: Optional[str] = None
    industry: Optional[str] = None
    target_audience: Optional[str] = None
    brand_voice: Optional[str] = None
    website: Optional[str] = None
    preferences: Optional[Dict[str, str]] = None


class AddItemRequest(BaseModel):
    """Request to add an item to a list."""
    item: str


@router.get("", response_model=UserProfile)
async def get_profile(user_id: str = "default"):
    """
    Get user profile.
    
    Returns complete user profile including preferences, facts, and learnings.
    """
    try:
        manager = get_profile_manager()
        profile = manager.load(user_id)
        return profile
    except Exception as e:
        logger.error(f"Failed to get profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("", response_model=UserProfile)
async def update_profile(updates: ProfileUpdate, user_id: str = "default"):
    """
    Update user profile.
    
    Only provided fields will be updated. Omitted fields remain unchanged.
    """
    try:
        manager = get_profile_manager()
        profile = manager.update(user_id, updates.dict(exclude_unset=True))
        return profile
    except Exception as e:
        logger.error(f"Failed to update profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context")
async def get_profile_context(user_id: str = "default"):
    """
    Get formatted profile context for AI.
    
    Returns a formatted string suitable for including in AI prompts.
    """
    try:
        manager = get_profile_manager()
        context = manager.get_context(user_id)
        return {
            "user_id": user_id,
            "context": context,
            "has_context": bool(context)
        }
    except Exception as e:
        logger.error(f"Failed to get profile context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/facts")
async def add_fact(request: AddItemRequest, user_id: str = "default"):
    """
    Add a fact to user profile.
    
    Facts are persistent pieces of information learned about the user.
    """
    try:
        manager = get_profile_manager()
        manager.add_fact(user_id, request.item)
        return {
            "success": True,
            "message": "Fact added",
            "fact": request.item
        }
    except Exception as e:
        logger.error(f"Failed to add fact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learnings")
async def add_learning(request: AddItemRequest, user_id: str = "default"):
    """
    Add a learning to user profile.
    
    Learnings are insights or patterns discovered through interactions.
    """
    try:
        manager = get_profile_manager()
        manager.add_learning(user_id, request.item)
        return {
            "success": True,
            "message": "Learning added",
            "learning": request.item
        }
    except Exception as e:
        logger.error(f"Failed to add learning: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/goals")
async def add_goal(request: AddItemRequest, user_id: str = "default"):
    """
    Add a goal to user profile.
    
    Goals are objectives or targets the user wants to achieve.
    """
    try:
        manager = get_profile_manager()
        manager.add_goal(user_id, request.item)
        return {
            "success": True,
            "message": "Goal added",
            "goal": request.item
        }
    except Exception as e:
        logger.error(f"Failed to add goal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preferences")
async def set_preference(key: str, value: str, user_id: str = "default"):
    """
    Set a user preference.
    
    Preferences are key-value pairs for user settings and choices.
    """
    try:
        manager = get_profile_manager()
        manager.set_preference(user_id, key, value)
        return {
            "success": True,
            "message": "Preference set",
            "key": key,
            "value": value
        }
    except Exception as e:
        logger.error(f"Failed to set preference: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("")
async def delete_profile(user_id: str = "default"):
    """
    Delete a user profile.
    
    WARNING: This cannot be undone.
    """
    if user_id == "default":
        raise HTTPException(
            status_code=400,
            detail="Cannot delete default profile. Create a new profile first."
        )
    
    try:
        manager = get_profile_manager()
        success = manager.delete(user_id)
        
        if success:
            return {"success": True, "message": f"Profile {user_id} deleted"}
        
        raise HTTPException(status_code=404, detail="Profile not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_profiles():
    """
    List all profile IDs.
    
    Returns a list of all user profile identifiers.
    """
    try:
        manager = get_profile_manager()
        profiles = manager.list_profiles()
        return {
            "profiles": profiles,
            "count": len(profiles)
        }
    except Exception as e:
        logger.error(f"Failed to list profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_profile(user_id: str = "default"):
    """
    Reset profile to defaults while keeping user_id.
    
    Clears all facts, learnings, goals, and preferences.
    """
    try:
        manager = get_profile_manager()
        # Create fresh profile with same ID
        profile = UserProfile(user_id=user_id)
        manager.save(profile)
        return {
            "success": True,
            "message": "Profile reset to defaults",
            "profile": profile
        }
    except Exception as e:
        logger.error(f"Failed to reset profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))
