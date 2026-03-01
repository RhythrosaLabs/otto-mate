"""
API Authentication Module

Provides Bearer token authentication for securing API endpoints.
Supports multiple API keys with different permission levels.
"""

import os
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any
from functools import wraps
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

logger = logging.getLogger(__name__)

# Security scheme for OpenAPI docs
security = HTTPBearer(auto_error=False)


class APIKey:
    """Represents an API key with metadata."""
    
    def __init__(
        self,
        key_id: str,
        key_hash: str,
        name: str,
        permissions: List[str],
        created_at: str,
        expires_at: Optional[str] = None,
        last_used: Optional[str] = None,
        rate_limit: int = 1000,  # requests per hour
        enabled: bool = True
    ):
        self.key_id = key_id
        self.key_hash = key_hash
        self.name = name
        self.permissions = permissions
        self.created_at = created_at
        self.expires_at = expires_at
        self.last_used = last_used
        self.rate_limit = rate_limit
        self.enabled = enabled
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "key_id": self.key_id,
            "key_hash": self.key_hash,
            "name": self.name,
            "permissions": self.permissions,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "last_used": self.last_used,
            "rate_limit": self.rate_limit,
            "enabled": self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "APIKey":
        return cls(**data)
    
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.fromisoformat(self.expires_at) < datetime.utcnow()
    
    def has_permission(self, permission: str) -> bool:
        """Check if key has a specific permission or wildcard."""
        if "*" in self.permissions:
            return True
        if permission in self.permissions:
            return True
        # Check wildcards like "chat:*"
        parts = permission.split(":")
        if len(parts) > 1:
            wildcard = f"{parts[0]}:*"
            if wildcard in self.permissions:
                return True
        return False


class AuthManager:
    """Manages API keys and authentication."""
    
    # Permission levels
    PERMISSIONS = {
        "chat": "Access chat endpoints",
        "chat:read": "Read chat history",
        "chat:write": "Send messages",
        "tools": "Access tool endpoints",
        "tools:execute": "Execute tools",
        "sessions": "Manage sessions",
        "webhooks": "Access webhook endpoints",
        "admin": "Administrative access",
        "admin:keys": "Manage API keys",
        "*": "Full access (all permissions)"
    }
    
    def __init__(self):
        self.data_dir = Path("data/auth")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.keys_file = self.data_dir / "api_keys.json"
        self.usage_file = self.data_dir / "usage.json"
        
        # In-memory cache
        self._keys: Dict[str, APIKey] = {}
        self._usage: Dict[str, List[datetime]] = {}
        
        # Master key from environment (optional)
        self.master_key = os.getenv("OTTO_API_KEY")
        self.auth_enabled = os.getenv("OTTO_AUTH_ENABLED", "false").lower() == "true"
        
        # Load existing keys
        self._load_keys()
    
    def _load_keys(self):
        """Load API keys from storage."""
        if self.keys_file.exists():
            try:
                with open(self.keys_file, "r") as f:
                    data = json.load(f)
                    for key_data in data.get("keys", []):
                        key = APIKey.from_dict(key_data)
                        self._keys[key.key_id] = key
                logger.info(f"Loaded {len(self._keys)} API keys")
            except Exception as e:
                logger.error(f"Failed to load API keys: {e}")
    
    def _save_keys(self):
        """Save API keys to storage."""
        try:
            data = {"keys": [k.to_dict() for k in self._keys.values()]}
            with open(self.keys_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save API keys: {e}")
    
    def _hash_key(self, key: str) -> str:
        """Hash an API key for storage."""
        return hashlib.sha256(key.encode()).hexdigest()
    
    def generate_key(
        self,
        name: str,
        permissions: List[str] = None,
        expires_days: Optional[int] = None,
        rate_limit: int = 1000
    ) -> tuple[str, APIKey]:
        """Generate a new API key."""
        # Generate secure random key
        key_id = secrets.token_urlsafe(8)
        raw_key = f"otto_{secrets.token_urlsafe(32)}"
        key_hash = self._hash_key(raw_key)
        
        # Default permissions
        if permissions is None:
            permissions = ["chat:*", "tools:execute", "sessions"]
        
        # Expiration
        expires_at = None
        if expires_days:
            expires_at = (datetime.utcnow() + timedelta(days=expires_days)).isoformat()
        
        # Create key object
        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            permissions=permissions,
            created_at=datetime.utcnow().isoformat(),
            expires_at=expires_at,
            rate_limit=rate_limit
        )
        
        # Store and save
        self._keys[key_id] = api_key
        self._save_keys()
        
        logger.info(f"Generated new API key: {name} ({key_id})")
        return raw_key, api_key
    
    def validate_key(self, raw_key: str) -> Optional[APIKey]:
        """Validate an API key and return the key object if valid."""
        # Check master key first
        if self.master_key and raw_key == self.master_key:
            return APIKey(
                key_id="master",
                key_hash="",
                name="Master Key",
                permissions=["*"],
                created_at="",
                rate_limit=999999
            )
        
        # Hash and lookup
        key_hash = self._hash_key(raw_key)
        
        for api_key in self._keys.values():
            if api_key.key_hash == key_hash:
                if not api_key.enabled:
                    logger.warning(f"Disabled key used: {api_key.key_id}")
                    return None
                if api_key.is_expired():
                    logger.warning(f"Expired key used: {api_key.key_id}")
                    return None
                
                # Update last used
                api_key.last_used = datetime.utcnow().isoformat()
                self._save_keys()
                
                return api_key
        
        return None
    
    def check_rate_limit(self, key_id: str, rate_limit: int) -> bool:
        """Check if request is within rate limits."""
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        
        # Clean old entries
        if key_id in self._usage:
            self._usage[key_id] = [
                ts for ts in self._usage[key_id] 
                if ts > hour_ago
            ]
        else:
            self._usage[key_id] = []
        
        # Check limit
        if len(self._usage[key_id]) >= rate_limit:
            return False
        
        # Record usage
        self._usage[key_id].append(now)
        return True
    
    def revoke_key(self, key_id: str) -> bool:
        """Revoke an API key."""
        if key_id in self._keys:
            del self._keys[key_id]
            self._save_keys()
            logger.info(f"Revoked API key: {key_id}")
            return True
        return False
    
    def disable_key(self, key_id: str) -> bool:
        """Disable an API key without deleting it."""
        if key_id in self._keys:
            self._keys[key_id].enabled = False
            self._save_keys()
            return True
        return False
    
    def enable_key(self, key_id: str) -> bool:
        """Enable a disabled API key."""
        if key_id in self._keys:
            self._keys[key_id].enabled = True
            self._save_keys()
            return True
        return False
    
    def list_keys(self) -> List[Dict[str, Any]]:
        """List all API keys (without showing the actual key)."""
        return [
            {
                "key_id": k.key_id,
                "name": k.name,
                "permissions": k.permissions,
                "created_at": k.created_at,
                "expires_at": k.expires_at,
                "last_used": k.last_used,
                "rate_limit": k.rate_limit,
                "enabled": k.enabled
            }
            for k in self._keys.values()
        ]
    
    def get_key_info(self, key_id: str) -> Optional[Dict[str, Any]]:
        """Get info about a specific key."""
        if key_id in self._keys:
            k = self._keys[key_id]
            return {
                "key_id": k.key_id,
                "name": k.name,
                "permissions": k.permissions,
                "created_at": k.created_at,
                "expires_at": k.expires_at,
                "last_used": k.last_used,
                "rate_limit": k.rate_limit,
                "enabled": k.enabled
            }
        return None


# Singleton instance
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get or create the auth manager singleton."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager


async def get_current_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[APIKey]:
    """
    Dependency to get the current API key from the request.
    Returns None if auth is disabled or no key provided (for optional auth).
    """
    auth_manager = get_auth_manager()
    
    # Skip auth if disabled
    if not auth_manager.auth_enabled:
        return None
    
    # Check for Bearer token
    if credentials:
        api_key = auth_manager.validate_key(credentials.credentials)
        if api_key:
            # Check rate limit
            if not auth_manager.check_rate_limit(api_key.key_id, api_key.rate_limit):
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={"Retry-After": "3600"}
                )
            return api_key
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # No credentials provided
    raise HTTPException(
        status_code=401,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"}
    )


async def optional_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[APIKey]:
    """
    Optional authentication - doesn't require auth but validates if provided.
    Useful for endpoints that work with or without auth.
    """
    auth_manager = get_auth_manager()
    
    if credentials:
        api_key = auth_manager.validate_key(credentials.credentials)
        if api_key:
            if not auth_manager.check_rate_limit(api_key.key_id, api_key.rate_limit):
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            return api_key
        # Invalid key provided - reject even if auth not required
        if auth_manager.auth_enabled:
            raise HTTPException(status_code=401, detail="Invalid API key")
    
    return None


def require_permission(permission: str):
    """
    Decorator/dependency factory to require a specific permission.
    Use with FastAPI's Depends().
    """
    async def check_permission(
        api_key: Optional[APIKey] = Depends(get_current_key)
    ):
        auth_manager = get_auth_manager()
        
        # Skip if auth disabled
        if not auth_manager.auth_enabled:
            return True
        
        if not api_key:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        if not api_key.has_permission(permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {permission} required"
            )
        
        return True
    
    return check_permission


def require_admin():
    """Require admin permission."""
    return require_permission("admin")
