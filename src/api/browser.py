"""
Browser Use API Router
======================

Provides API endpoints for browser automation features.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/browser", tags=["browser"])

# ==========================================
# In-memory state
# ==========================================

browser_state = {
    "is_active": False,
    "current_task": None,
    "current_url": None,
    "last_screenshot": None,
    "history": [],
    "websocket_clients": []
}


# ==========================================
# Models
# ==========================================

class BrowserTaskRequest(BaseModel):
    task_type: str
    url: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class BrowserTaskResponse(BaseModel):
    success: bool
    task_id: Optional[str] = None
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


# ==========================================
# WebSocket for real-time updates
# ==========================================

@router.websocket("/ws")
async def browser_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time browser updates."""
    await websocket.accept()
    browser_state["websocket_clients"].append(websocket)
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Handle pings or commands
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        browser_state["websocket_clients"].remove(websocket)


async def broadcast_browser_event(event_type: str, data: Dict[str, Any]):
    """Broadcast browser event to all connected clients."""
    message = json.dumps({
        "type": event_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    })
    
    disconnected = []
    for client in browser_state["websocket_clients"]:
        try:
            await client.send_text(message)
        except:
            disconnected.append(client)
    
    # Clean up disconnected clients
    for client in disconnected:
        browser_state["websocket_clients"].remove(client)


# ==========================================
# API Endpoints
# ==========================================

@router.get("/status")
async def get_browser_status():
    """Get current browser status."""
    # Try to get state from BrowserUseTools if available
    try:
        from ..tools.browser_use_advanced import BrowserUseTools, BROWSER_USE_AVAILABLE
        if BROWSER_USE_AVAILABLE:
            tools_state = BrowserUseTools.get_state()
            return {
                "success": True,
                "is_active": tools_state.get("is_active", False) or browser_state["is_active"],
                "current_task": tools_state.get("current_task") or browser_state["current_task"],
                "current_url": tools_state.get("current_url") or browser_state["current_url"],
                "has_screenshot": browser_state["last_screenshot"] is not None,
                "active_connections": len(browser_state["websocket_clients"]),
                "actions": tools_state.get("actions", [])[-10:]  # Last 10 actions
            }
    except Exception as e:
        logger.debug(f"Could not get BrowserUseTools state: {e}")
    
    return {
        "success": True,
        "is_active": browser_state["is_active"],
        "current_task": browser_state["current_task"],
        "current_url": browser_state["current_url"],
        "has_screenshot": browser_state["last_screenshot"] is not None,
        "active_connections": len(browser_state["websocket_clients"])
    }


@router.get("/history")
async def get_browser_history(limit: int = 20):
    """Get browser session history."""
    history = browser_state["history"][-limit:]
    return {
        "success": True,
        "history": history,
        "total": len(browser_state["history"])
    }


@router.post("/clear-history")
async def clear_browser_history():
    """Clear browser history."""
    browser_state["history"] = []
    return {"success": True, "message": "History cleared"}


@router.get("/screenshot")
async def get_screenshot():
    """Get last browser screenshot."""
    if browser_state["last_screenshot"]:
        return {
            "success": True,
            "screenshot": browser_state["last_screenshot"],
            "url": browser_state["current_url"]
        }
    return {
        "success": False,
        "message": "No screenshot available"
    }


@router.post("/execute")
async def execute_browser_task(request: BrowserTaskRequest):
    """Execute a browser automation task."""
    try:
        from ..tools.browser_use_advanced import BrowserUseAdvanced, BROWSER_USE_AVAILABLE
        
        if not BROWSER_USE_AVAILABLE:
            return {
                "success": False,
                "message": "Browser-use library not installed. Run: pip install browser-use playwright && playwright install"
            }
        
        # Update state
        browser_state["is_active"] = True
        browser_state["current_task"] = request.task_type
        
        # Broadcast start event
        await broadcast_browser_event("browser_start", {
            "task": request.task_type,
            "url": request.url
        })
        
        # Initialize browser tools
        browser_tools = BrowserUseAdvanced()
        
        # Map task types to methods
        task_handlers = {
            "extract_leads": lambda: browser_tools.extract_leads(
                url=request.url,
                criteria=request.params.get("lead_types", None)
            ),
            "scrape_data": lambda: browser_tools.extract_data(
                url=request.url,
                data_description=request.params.get("data_type", "structured data"),
            ),
            "monitor_price": lambda: browser_tools.monitor_price(
                product_url=request.url,
            ),
            "analyze_competitor": lambda: browser_tools.analyze_competitor(
                competitor_url=request.url,
            ),
            "fill_form": lambda: browser_tools.fill_form(
                url=request.url,
                form_data=request.params.get("form_data", {}),
                submit=request.params.get("submit", False)
            ),
            "find_influencers": lambda: browser_tools.find_influencers(
                platform=request.params.get("platform", "instagram"),
                niche=request.params.get("niche", ""),
                max_results=request.params.get("count", 10)
            ),
            "take_screenshot": lambda: browser_tools.take_screenshot(
                url=request.url
            ),
            "social_media": lambda: browser_tools.social_media_action(
                platform=request.params.get("platform", "twitter"),
                action=request.params.get("action", "post"),
                content=request.params.get("content"),
                target_url=request.url,
            ),
            "custom": lambda: browser_tools.automate_task(
                task_description=request.description or "Navigate and interact",
                starting_url=request.url,
                stealth_mode=request.params.get("stealth_mode", "standard")
            )
        }
        
        handler = task_handlers.get(request.task_type, task_handlers["custom"])
        result = await handler()
        
        # Add to history
        history_entry = {
            "id": f"browser_{datetime.now().timestamp()}",
            "task": request.task_type,
            "url": request.url,
            "timestamp": datetime.now().isoformat(),
            "success": result.get("success", True),
            "summary": result.get("summary", "Task completed")
        }
        browser_state["history"].append(history_entry)
        
        # Update screenshot if available
        if result.get("screenshot"):
            browser_state["last_screenshot"] = result["screenshot"]
        
        # Broadcast completion
        await broadcast_browser_event("browser_complete", {
            "task": request.task_type,
            "result": result
        })
        
        return {
            "success": True,
            "task_id": history_entry["id"],
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Browser task error: {e}")
        
        # Broadcast error
        await broadcast_browser_event("browser_error", {
            "error": str(e)
        })
        
        return {
            "success": False,
            "message": str(e)
        }
    finally:
        browser_state["is_active"] = False
        browser_state["current_task"] = None


@router.post("/stop")
async def stop_browser():
    """Stop current browser session."""
    browser_state["is_active"] = False
    browser_state["current_task"] = None
    
    await broadcast_browser_event("browser_stop", {})
    
    return {"success": True, "message": "Browser stopped"}


# ==========================================
# Quick Actions
# ==========================================

@router.get("/quick-tasks")
async def get_quick_tasks():
    """Get available quick browser tasks."""
    return {
        "success": True,
        "tasks": [
            {
                "id": "extract_leads",
                "name": "Extract Leads",
                "icon": "🎯",
                "description": "Find contacts and leads from a website",
                "requires_url": True
            },
            {
                "id": "monitor_price",
                "name": "Monitor Price",
                "icon": "💰",
                "description": "Track product price changes",
                "requires_url": True
            },
            {
                "id": "analyze_competitor",
                "name": "Analyze Competitor",
                "icon": "🔍",
                "description": "Research competitor website",
                "requires_url": True
            },
            {
                "id": "fill_form",
                "name": "Fill Form",
                "icon": "📝",
                "description": "Auto-fill web forms",
                "requires_url": True
            },
            {
                "id": "scrape_data",
                "name": "Scrape Data",
                "icon": "📊",
                "description": "Extract structured data from pages",
                "requires_url": True
            },
            {
                "id": "find_influencers",
                "name": "Find Influencers",
                "icon": "⭐",
                "description": "Find social media influencers",
                "requires_url": False
            },
            {
                "id": "take_screenshot",
                "name": "Take Screenshot",
                "icon": "📸",
                "description": "Capture webpage screenshot",
                "requires_url": True
            }
        ]
    }


# ==========================================
# Settings
# ==========================================

@router.get("/settings")
async def get_browser_settings():
    """Get browser automation settings."""
    # Load from environment or config
    return {
        "success": True,
        "settings": {
            "headless": os.getenv("BROWSER_HEADLESS", "false") == "true",
            "llm_provider": os.getenv("BROWSER_LLM", "claude"),
            "timeout": int(os.getenv("BROWSER_TIMEOUT", "60")),
            "max_actions": int(os.getenv("BROWSER_MAX_ACTIONS", "100")),
            "demo_mode": os.getenv("BROWSER_DEMO_MODE", "false") == "true"
        }
    }


@router.post("/settings")
async def update_browser_settings(settings: Dict[str, Any]):
    """Update browser automation settings."""
    # These would typically be saved to a config file
    # For now, we'll just acknowledge them
    return {
        "success": True,
        "message": "Settings updated",
        "settings": settings
    }
