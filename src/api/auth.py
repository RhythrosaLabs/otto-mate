"""
API Key Management Endpoints

Provides endpoints for generating, listing, and managing API keys.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import logging

from src.core.auth import (
    get_auth_manager,
    get_current_key,
    require_permission,
    APIKey
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# Request/Response Models
class GenerateKeyRequest(BaseModel):
    """Request to generate a new API key."""
    name: str = Field(..., description="Name/description for the key")
    permissions: Optional[List[str]] = Field(
        None, 
        description="List of permissions (default: chat:*, tools:execute, sessions)"
    )
    expires_days: Optional[int] = Field(
        None, 
        description="Number of days until expiration (None = never)"
    )
    rate_limit: int = Field(
        1000, 
        description="Max requests per hour"
    )


class GenerateKeyResponse(BaseModel):
    """Response with the newly generated API key."""
    key: str = Field(..., description="The API key (only shown once!)")
    key_id: str
    name: str
    permissions: List[str]
    expires_at: Optional[str]
    rate_limit: int


class KeyInfo(BaseModel):
    """API key information (without the actual key)."""
    key_id: str
    name: str
    permissions: List[str]
    created_at: str
    expires_at: Optional[str]
    last_used: Optional[str]
    rate_limit: int
    enabled: bool


class AuthStatus(BaseModel):
    """Authentication system status."""
    enabled: bool
    master_key_set: bool
    total_keys: int
    permissions_available: dict


@router.get("/status", response_model=AuthStatus)
async def get_auth_status():
    """Get authentication system status."""
    auth = get_auth_manager()
    return AuthStatus(
        enabled=auth.auth_enabled,
        master_key_set=bool(auth.master_key),
        total_keys=len(auth._keys),
        permissions_available=auth.PERMISSIONS
    )


@router.post("/keys", response_model=GenerateKeyResponse)
async def generate_api_key(
    request: GenerateKeyRequest,
    _: bool = Depends(require_permission("admin:keys"))
):
    """
    Generate a new API key.
    
    **Requires admin:keys permission** (or auth disabled)
    
    The key is only returned once - store it securely!
    """
    auth = get_auth_manager()
    
    raw_key, api_key = auth.generate_key(
        name=request.name,
        permissions=request.permissions,
        expires_days=request.expires_days,
        rate_limit=request.rate_limit
    )
    
    return GenerateKeyResponse(
        key=raw_key,
        key_id=api_key.key_id,
        name=api_key.name,
        permissions=api_key.permissions,
        expires_at=api_key.expires_at,
        rate_limit=api_key.rate_limit
    )


@router.get("/keys", response_model=List[KeyInfo])
async def list_api_keys(
    _: bool = Depends(require_permission("admin:keys"))
):
    """
    List all API keys.
    
    **Requires admin:keys permission** (or auth disabled)
    
    Note: The actual key values are not returned.
    """
    auth = get_auth_manager()
    keys = auth.list_keys()
    return [KeyInfo(**k) for k in keys]


@router.get("/keys/{key_id}", response_model=KeyInfo)
async def get_api_key(
    key_id: str,
    _: bool = Depends(require_permission("admin:keys"))
):
    """
    Get information about a specific API key.
    
    **Requires admin:keys permission** (or auth disabled)
    """
    auth = get_auth_manager()
    key_info = auth.get_key_info(key_id)
    
    if not key_info:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return KeyInfo(**key_info)


@router.delete("/keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    _: bool = Depends(require_permission("admin:keys"))
):
    """
    Permanently revoke an API key.
    
    **Requires admin:keys permission** (or auth disabled)
    
    This action cannot be undone.
    """
    auth = get_auth_manager()
    
    if auth.revoke_key(key_id):
        return {"status": "revoked", "key_id": key_id}
    
    raise HTTPException(status_code=404, detail="API key not found")


@router.post("/keys/{key_id}/disable")
async def disable_api_key(
    key_id: str,
    _: bool = Depends(require_permission("admin:keys"))
):
    """
    Temporarily disable an API key.
    
    **Requires admin:keys permission** (or auth disabled)
    
    The key can be re-enabled later.
    """
    auth = get_auth_manager()
    
    if auth.disable_key(key_id):
        return {"status": "disabled", "key_id": key_id}
    
    raise HTTPException(status_code=404, detail="API key not found")


@router.post("/keys/{key_id}/enable")
async def enable_api_key(
    key_id: str,
    _: bool = Depends(require_permission("admin:keys"))
):
    """
    Re-enable a disabled API key.
    
    **Requires admin:keys permission** (or auth disabled)
    """
    auth = get_auth_manager()
    
    if auth.enable_key(key_id):
        return {"status": "enabled", "key_id": key_id}
    
    raise HTTPException(status_code=404, detail="API key not found")


@router.get("/me")
async def get_current_key_info(
    api_key: Optional[APIKey] = Depends(get_current_key)
):
    """
    Get information about the currently authenticated key.
    
    Returns the key's permissions and metadata.
    """
    auth = get_auth_manager()
    
    if not auth.auth_enabled:
        return {
            "authenticated": False,
            "auth_enabled": False,
            "message": "Authentication is disabled"
        }
    
    if not api_key:
        return {
            "authenticated": False,
            "auth_enabled": True
        }
    
    return {
        "authenticated": True,
        "key_id": api_key.key_id,
        "name": api_key.name,
        "permissions": api_key.permissions,
        "rate_limit": api_key.rate_limit
    }


@router.post("/verify")
async def verify_api_key(
    api_key: Optional[APIKey] = Depends(get_current_key)
):
    """
    Verify that a provided API key is valid.
    
    Use this to test if a key works before using it.
    """
    auth = get_auth_manager()
    
    if not auth.auth_enabled:
        return {
            "valid": True,
            "message": "Authentication is disabled - all requests allowed"
        }
    
    if api_key:
        return {
            "valid": True,
            "key_id": api_key.key_id,
            "name": api_key.name,
            "permissions": api_key.permissions
        }
    
    return {"valid": False}


# CLI helper endpoint - allows generating first key without auth
@router.post("/bootstrap")
async def bootstrap_first_key(request: GenerateKeyRequest):
    """
    Generate the first API key (bootstrap).
    
    **Only works when no keys exist yet.**
    
    Use this to create your initial admin key.
    """
    auth = get_auth_manager()
    
    # Only allow if no keys exist
    if len(auth._keys) > 0:
        raise HTTPException(
            status_code=403,
            detail="Bootstrap only available when no keys exist. Use /api/auth/keys instead."
        )
    
    # Generate admin key with full permissions
    raw_key, api_key = auth.generate_key(
        name=request.name or "Initial Admin Key",
        permissions=["*"],  # Full access for bootstrap key
        expires_days=request.expires_days,
        rate_limit=request.rate_limit or 10000
    )
    
    logger.info(f"Bootstrap key generated: {api_key.key_id}")
    
    return GenerateKeyResponse(
        key=raw_key,
        key_id=api_key.key_id,
        name=api_key.name,
        permissions=api_key.permissions,
        expires_at=api_key.expires_at,
        rate_limit=api_key.rate_limit
    )
