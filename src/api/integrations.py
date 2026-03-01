"""
Integrations Management API
===========================

REST API endpoints for managing external service integrations.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import json
from pathlib import Path
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/integrations", tags=["integrations"])

# Path to store integration configs securely
INTEGRATIONS_FILE = Path("data/integrations.json")


class IntegrationConfig(BaseModel):
    """Request body for saving an integration."""
    integration: str
    config: Dict[str, Any]


class IntegrationTestRequest(BaseModel):
    """Request body for testing an integration."""
    integration: str
    config: Dict[str, Any]


class IntegrationDisconnect(BaseModel):
    """Request body for disconnecting an integration."""
    integration: str


def load_integrations() -> Dict[str, Dict[str, Any]]:
    """Load all saved integrations."""
    if INTEGRATIONS_FILE.exists():
        try:
            with open(INTEGRATIONS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_integrations(data: Dict[str, Dict[str, Any]]):
    """Save integrations to file."""
    INTEGRATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(INTEGRATIONS_FILE, "w") as f:
        json.dump(data, f, indent=2)


@router.get("")
async def list_integrations() -> Dict[str, Any]:
    """List all configured integrations."""
    integrations = load_integrations()
    
    # Return integration IDs and connection status (mask actual credentials)
    result = {}
    for integration_id, config in integrations.items():
        result[integration_id] = {
            "connected": any(config.values()),
            "fields_configured": len([k for k, v in config.items() if v])
        }
    
    return {
        "integrations": result,
        "total_connected": sum(1 for v in result.values() if v.get("connected"))
    }


@router.post("")
async def save_integration(request: IntegrationConfig) -> Dict[str, Any]:
    """Save integration configuration."""
    integrations = load_integrations()
    integrations[request.integration] = request.config
    save_integrations(integrations)
    
    # Also set as environment variables for this session
    # This allows other parts of the app to use these credentials
    prefix = request.integration.upper()
    for key, value in request.config.items():
        if value:
            env_key = f"{prefix}_{key.upper()}"
            os.environ[env_key] = value
    
    logger.info(f"Saved integration config for: {request.integration}")
    
    return {
        "success": True,
        "integration": request.integration,
        "message": f"Integration {request.integration} configured"
    }


@router.post("/test")
async def test_integration(request: IntegrationTestRequest) -> Dict[str, Any]:
    """Test an integration connection."""
    integration = request.integration
    config = request.config
    
    try:
        # Test based on integration type
        if integration == "ollama":
            import httpx
            url = config.get("url", "http://localhost:11434")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{url}/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    return {"success": True, "message": f"Connected! {len(models)} models available"}
                else:
                    return {"success": False, "error": f"Status {response.status_code}"}
        
        elif integration == "github":
            import httpx
            token = config.get("access_token", "")
            if not token:
                return {"success": False, "error": "No access token provided"}
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.github.com/user",
                    headers={"Authorization": f"token {token}"}
                )
                if response.status_code == 200:
                    user = response.json()
                    return {"success": True, "message": f"Connected as {user.get('login')}"}
                else:
                    return {"success": False, "error": "Invalid token"}
        
        elif integration in ["gemini", "perplexity", "deepseek", "groq", "together", "mistral"]:
            # For API-based services, just verify the key format
            api_key = config.get("api_key", "")
            if not api_key:
                return {"success": False, "error": "No API key provided"}
            if len(api_key) < 10:
                return {"success": False, "error": "API key appears too short"}
            return {"success": True, "message": "API key saved (connection will be tested on first use)"}
        
        elif integration == "huggingface":
            import httpx
            token = config.get("api_key", "")
            if not token:
                return {"success": False, "error": "No access token provided"}
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://huggingface.co/api/whoami-v2",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if response.status_code == 200:
                    user = response.json()
                    return {"success": True, "message": f"Connected as {user.get('name', 'user')}"}
                else:
                    return {"success": False, "error": "Invalid token"}
        
        elif integration == "slack":
            import httpx
            token = config.get("bot_token", "")
            if not token:
                return {"success": False, "error": "No bot token provided"}
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://slack.com/api/auth.test",
                    headers={"Authorization": f"Bearer {token}"}
                )
                data = response.json()
                if data.get("ok"):
                    return {"success": True, "message": f"Connected to {data.get('team')}"}
                else:
                    return {"success": False, "error": data.get("error", "Unknown error")}
        
        elif integration == "discord":
            import httpx
            token = config.get("bot_token", "")
            if not token:
                # Check webhook instead
                webhook = config.get("webhook_url", "")
                if webhook:
                    return {"success": True, "message": "Webhook URL saved"}
                return {"success": False, "error": "No bot token or webhook provided"}
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://discord.com/api/users/@me",
                    headers={"Authorization": f"Bot {token}"}
                )
                if response.status_code == 200:
                    user = response.json()
                    return {"success": True, "message": f"Connected as {user.get('username')}"}
                else:
                    return {"success": False, "error": "Invalid token"}
        
        elif integration == "notion":
            import httpx
            token = config.get("api_key", "")
            if not token:
                return {"success": False, "error": "No integration token provided"}
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.notion.com/v1/users/me",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Notion-Version": "2022-06-28"
                    }
                )
                if response.status_code == 200:
                    return {"success": True, "message": "Connected to Notion"}
                else:
                    return {"success": False, "error": "Invalid token"}
        
        elif integration == "sendgrid":
            import httpx
            api_key = config.get("api_key", "")
            if not api_key:
                return {"success": False, "error": "No API key provided"}
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.sendgrid.com/v3/user/profile",
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                if response.status_code == 200:
                    return {"success": True, "message": "Connected to SendGrid"}
                else:
                    return {"success": False, "error": "Invalid API key"}
        
        elif integration == "stripe":
            import httpx
            secret_key = config.get("secret_key", "")
            if not secret_key:
                return {"success": False, "error": "No secret key provided"}
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.stripe.com/v1/balance",
                    auth=(secret_key, "")
                )
                if response.status_code == 200:
                    return {"success": True, "message": "Connected to Stripe"}
                else:
                    return {"success": False, "error": "Invalid secret key"}
        
        elif integration == "airtable":
            import httpx
            api_key = config.get("api_key", "")
            if not api_key:
                return {"success": False, "error": "No API key provided"}
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.airtable.com/v0/meta/whoami",
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                if response.status_code == 200:
                    return {"success": True, "message": "Connected to Airtable"}
                else:
                    return {"success": False, "error": "Invalid API key"}
        
        elif integration == "shopify":
            import httpx
            store_url = config.get("store_url", "")
            access_token = config.get("access_token", "")
            if not store_url or not access_token:
                return {"success": False, "error": "Store URL and access token required"}
            
            # Normalize store URL
            if not store_url.startswith("http"):
                store_url = f"https://{store_url}"
            store_url = store_url.rstrip("/")
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{store_url}/admin/api/2024-01/shop.json",
                    headers={"X-Shopify-Access-Token": access_token}
                )
                if response.status_code == 200:
                    shop = response.json().get("shop", {})
                    return {"success": True, "message": f"Connected to {shop.get('name', store_url)}"}
                else:
                    return {"success": False, "error": "Invalid credentials"}
        
        else:
            # Generic test - just verify something is configured
            has_config = any(config.values())
            if has_config:
                return {"success": True, "message": "Configuration saved (connection will be tested on first use)"}
            else:
                return {"success": False, "error": "No configuration provided"}
    
    except ImportError as e:
        return {"success": False, "error": f"Missing dependency: {e}"}
    except Exception as e:
        logger.error(f"Integration test failed for {integration}: {e}")
        return {"success": False, "error": str(e)}


@router.post("/disconnect")
async def disconnect_integration(request: IntegrationDisconnect) -> Dict[str, Any]:
    """Remove an integration configuration."""
    integrations = load_integrations()
    
    if request.integration in integrations:
        del integrations[request.integration]
        save_integrations(integrations)
        
        # Clear environment variables
        prefix = request.integration.upper()
        env_keys_to_remove = [k for k in os.environ.keys() if k.startswith(f"{prefix}_")]
        for k in env_keys_to_remove:
            del os.environ[k]
        
        logger.info(f"Disconnected integration: {request.integration}")
        return {
            "success": True,
            "message": f"Integration {request.integration} disconnected"
        }
    
    return {
        "success": True,
        "message": "Integration was not configured"
    }


@router.get("/{integration_id}")
async def get_integration(integration_id: str) -> Dict[str, Any]:
    """Get integration configuration (masked)."""
    integrations = load_integrations()
    
    if integration_id not in integrations:
        return {"configured": False, "fields": {}}
    
    config = integrations[integration_id]
    
    # Mask sensitive values
    masked = {}
    for key, value in config.items():
        if value:
            if len(value) > 8:
                masked[key] = value[:4] + "***" + value[-4:]
            else:
                masked[key] = "***configured***"
        else:
            masked[key] = ""
    
    return {
        "configured": True,
        "fields": masked
    }
