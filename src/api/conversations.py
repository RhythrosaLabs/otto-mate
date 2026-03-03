"""
Conversation Management API Router
==================================

Provides API endpoints for chat history and conversation management.
"""

import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..tools.chat_history import get_chat_history_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["conversations"])


# Pydantic models
class ConversationCreate(BaseModel):
    messages: List[Dict[str, str]]
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    messages: Optional[List[Dict[str, str]]] = None
    metadata: Optional[Dict[str, Any]] = None


class ConversationSearch(BaseModel):
    query: str
    limit: Optional[int] = 20


# Routes
@router.get("/conversations")
async def list_conversations(limit: int = 50, project_id: Optional[str] = None):
    """
    List all conversations, sorted by most recent.
    
    Args:
        limit: Maximum number of conversations to return
        project_id: Optional filter by project
    """
    try:
        manager = get_chat_history_manager()
        conversations = manager.list_conversations(limit=limit, project_id=project_id)
        return conversations
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/statistics")
async def get_conversation_statistics():
    """
    Get statistics about stored conversations.
    """
    try:
        manager = get_chat_history_manager()
        return manager.get_statistics()
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Get a specific conversation by ID.
    
    Args:
        conversation_id: The conversation ID
    """
    try:
        manager = get_chat_history_manager()
        result = manager.load_conversation(conversation_id)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result.get("error", "Conversation not found"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations")
async def save_conversation(request: ConversationCreate):
    """
    Save a new conversation.
    
    Args:
        request: Conversation data with messages and optional title/metadata
    """
    try:
        manager = get_chat_history_manager()
        result = manager.save_conversation(
            messages=request.messages,
            title=request.title,
            metadata=request.metadata
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to save conversation"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/conversations/{conversation_id}")
async def update_conversation(conversation_id: str, request: ConversationUpdate):
    """
    Update an existing conversation.
    
    Args:
        conversation_id: The conversation ID
        request: Fields to update
    """
    try:
        manager = get_chat_history_manager()
        
        # Load existing conversation
        existing = manager.load_conversation(conversation_id)
        if not existing["success"]:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conv = existing["conversation"]
        
        # Update fields
        messages = request.messages if request.messages is not None else conv.get("messages", [])
        title = request.title if request.title is not None else conv.get("title")
        metadata = request.metadata if request.metadata is not None else conv.get("metadata", {})
        
        # Save updated conversation
        result = manager.save_conversation(
            messages=messages,
            conversation_id=conversation_id,
            title=title,
            metadata=metadata
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to update conversation"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation.
    
    Args:
        conversation_id: The conversation ID
    """
    try:
        manager = get_chat_history_manager()
        result = manager.delete_conversation(conversation_id)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result.get("error", "Conversation not found"))
        
        return {"success": True, "message": "Conversation deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/search")
async def search_conversations(request: ConversationSearch):
    """
    Search conversations by content.
    
    Args:
        request: Search query and optional limit
    """
    try:
        manager = get_chat_history_manager()
        results = manager.search_conversations(query=request.query, limit=request.limit or 20)
        return {"results": results}
    except Exception as e:
        logger.error(f"Error searching conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/conversations/{conversation_id}/rename")
async def rename_conversation(conversation_id: str, title: str):
    """
    Rename a conversation.
    
    Args:
        conversation_id: The conversation ID
        title: New title
    """
    try:
        manager = get_chat_history_manager()
        result = manager.rename_conversation(conversation_id, title)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result.get("error", "Conversation not found"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error renaming conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}/export")
async def export_conversation(conversation_id: str, format: str = "markdown"):
    """
    Export a conversation to different formats.
    
    Args:
        conversation_id: The conversation ID
        format: Export format (markdown, json, text)
    """
    try:
        manager = get_chat_history_manager()
        result = manager.export_conversation(conversation_id, format=format)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result.get("error", "Conversation not found"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Integration status endpoint
@router.get("/integrations/status")
async def get_integrations_status():
    """
    Get the connection status of all integrations.
    """
    import os
    
    # Check which integrations have API keys configured
    statuses = {
        "printify": bool(os.getenv("PRINTIFY_API_KEY") or os.getenv("PRINTIFY_API_TOKEN")),
        "shopify": bool(os.getenv("SHOPIFY_API_KEY")),
        "replicate": bool(os.getenv("REPLICATE_API_TOKEN")),
        "browser": True,  # Browser use is always available
        "tasks": True,  # Task scheduler is always available
        "email": bool(os.getenv("EMAIL_ADDRESS") or os.getenv("SENDGRID_API_KEY")),
        "youtube": bool(os.getenv("YOUTUBE_API_KEY")),
        "twitter": bool(os.getenv("TWITTER_API_KEY") or os.getenv("X_API_KEY")),
        "instagram": bool(os.getenv("INSTAGRAM_ACCESS_TOKEN")),
        "facebook": bool(os.getenv("FACEBOOK_ACCESS_TOKEN")),
        "linkedin": bool(os.getenv("LINKEDIN_ACCESS_TOKEN")),
        "tiktok": bool(os.getenv("TIKTOK_ACCESS_TOKEN")),
        "calendar": bool(os.getenv("GOOGLE_CALENDAR_CREDENTIALS")),
    }
    
    return statuses
