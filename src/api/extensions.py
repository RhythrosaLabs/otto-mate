"""
Extensions API
==============

Endpoints for managing extensions (integrations).
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.extension_registry import (
    get_extension_registry,
    Extension,
    ExtensionCategory
)
from ..utils.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/extensions", tags=["extensions"])


class ExtensionResponse(BaseModel):
    """Extension response model."""
    id: str
    name: str
    description: str
    category: str
    icon: str
    enabled: bool
    required_keys: List[str]
    optional_keys: List[str]
    tools: List[str]
    configured: bool = False
    missing_keys: List[str] = []


@router.get("", response_model=List[ExtensionResponse])
async def list_extensions(
    category: Optional[str] = None,
    enabled_only: bool = False
):
    """
    List all available extensions.
    
    Args:
        category: Filter by category
        enabled_only: Only return enabled extensions
    """
    registry = get_extension_registry()
    settings = get_settings()
    config = settings.dict()
    
    # Get extensions based on filters
    if category:
        try:
            cat_enum = ExtensionCategory(category)
            extensions = registry.get_by_category(cat_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
    elif enabled_only:
        extensions = registry.get_enabled_extensions()
    else:
        extensions = registry.get_all_extensions()
    
    # Build response with configuration status
    response = []
    for ext in extensions:
        configured = registry.is_extension_configured(ext.id, config)
        missing_keys = registry.get_missing_keys(ext.id, config)
        
        response.append(ExtensionResponse(
            id=ext.id,
            name=ext.name,
            description=ext.description,
            category=ext.category.value,
            icon=ext.icon,
            enabled=ext.enabled,
            required_keys=ext.required_keys,
            optional_keys=ext.optional_keys,
            tools=ext.tools,
            configured=configured,
            missing_keys=missing_keys
        ))
    
    return response


@router.get("/categories")
async def list_categories():
    """List all extension categories."""
    return [
        {"value": cat.value, "label": cat.value.replace("_", " ").title()}
        for cat in ExtensionCategory
    ]


@router.get("/{extension_id}", response_model=ExtensionResponse)
async def get_extension(extension_id: str):
    """Get extension details."""
    registry = get_extension_registry()
    settings = get_settings()
    config = settings.dict()
    
    extension = registry.get_extension(extension_id)
    
    if not extension:
        raise HTTPException(status_code=404, detail="Extension not found")
    
    configured = registry.is_extension_configured(extension_id, config)
    missing_keys = registry.get_missing_keys(extension_id, config)
    
    return ExtensionResponse(
        id=extension.id,
        name=extension.name,
        description=extension.description,
        category=extension.category.value,
        icon=extension.icon,
        enabled=extension.enabled,
        required_keys=extension.required_keys,
        optional_keys=extension.optional_keys,
        tools=extension.tools,
        configured=configured,
        missing_keys=missing_keys
    )


@router.post("/{extension_id}/enable")
async def enable_extension(extension_id: str):
    """Enable an extension."""
    registry = get_extension_registry()
    
    if registry.enable(extension_id):
        return {
            "success": True,
            "message": f"Extension {extension_id} enabled",
            "note": "Restart the server to apply changes"
        }
    
    raise HTTPException(status_code=404, detail="Extension not found")


@router.post("/{extension_id}/disable")
async def disable_extension(extension_id: str):
    """Disable an extension."""
    registry = get_extension_registry()
    
    if registry.disable(extension_id):
        return {
            "success": True,
            "message": f"Extension {extension_id} disabled",
            "note": "Restart the server to apply changes"
        }
    
    raise HTTPException(status_code=404, detail="Extension not found")


@router.get("/{extension_id}/status")
async def get_extension_status(extension_id: str):
    """
    Check if extension is configured and ready.
    
    Returns detailed status including configuration requirements.
    """
    registry = get_extension_registry()
    settings = get_settings()
    config = settings.dict()
    
    extension = registry.get_extension(extension_id)
    
    if not extension:
        raise HTTPException(status_code=404, detail="Extension not found")
    
    configured = registry.is_extension_configured(extension_id, config)
    missing_keys = registry.get_missing_keys(extension_id, config)
    
    # Check which keys are present
    present_keys = [
        key for key in extension.required_keys + extension.optional_keys
        if config.get(key)
    ]
    
    return {
        "extension_id": extension_id,
        "name": extension.name,
        "enabled": extension.enabled,
        "configured": configured,
        "ready": extension.enabled and configured,
        "required_keys": extension.required_keys,
        "optional_keys": extension.optional_keys,
        "present_keys": present_keys,
        "missing_keys": missing_keys,
        "tools_count": len(extension.tools),
        "status": (
            "ready" if extension.enabled and configured
            else "not_configured" if extension.enabled
            else "disabled"
        )
    }


@router.get("/{extension_id}/tools")
async def get_extension_tools(extension_id: str):
    """Get list of tools provided by an extension."""
    registry = get_extension_registry()
    extension = registry.get_extension(extension_id)
    
    if not extension:
        raise HTTPException(status_code=404, detail="Extension not found")
    
    return {
        "extension_id": extension_id,
        "extension_name": extension.name,
        "tools": extension.tools,
        "count": len(extension.tools)
    }
