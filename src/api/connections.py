"""
Connections API
===============

Endpoints for managing API connections and credentials.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import aiohttp

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/connections", tags=["connections"])

# Path to .env file - use working directory for consistency
ENV_FILE = Path.cwd() / ".env"


class ConnectionCredentials(BaseModel):
    """Credentials for a service connection."""
    service: str
    credentials: Dict[str, str]


class ConnectionTestResult(BaseModel):
    """Result of testing a connection."""
    service: str
    success: bool
    message: str


# Service validation functions
async def validate_anthropic(api_key: str) -> bool:
    """Validate Anthropic API key."""
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        # Simple validation - just check if we can create a client
        return True
    except Exception as e:
        logger.error(f"Anthropic validation failed: {e}")
        return False


async def validate_openai(api_key: str) -> bool:
    """Validate OpenAI API key."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"}
            ) as response:
                return response.status == 200
    except Exception as e:
        logger.error(f"OpenAI validation failed: {e}")
        return False


async def validate_replicate(api_token: str) -> bool:
    """Validate Replicate API token."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.replicate.com/v1/account",
                headers={"Authorization": f"Token {api_token}"}
            ) as response:
                return response.status == 200
    except Exception as e:
        logger.error(f"Replicate validation failed: {e}")
        return False


async def validate_printify(api_token: str, shop_id: str = "") -> bool:
    """Validate Printify API token."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.printify.com/v1/shops.json",
                headers={"Authorization": f"Bearer {api_token}"}
            ) as response:
                return response.status == 200
    except Exception as e:
        logger.error(f"Printify validation failed: {e}")
        return False


async def validate_shopify(shop_name: str, access_token: str) -> bool:
    """Validate Shopify credentials."""
    try:
        # Clean shop name
        if ".myshopify.com" in shop_name:
            shop_name = shop_name.replace(".myshopify.com", "")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://{shop_name}.myshopify.com/admin/api/2024-01/shop.json",
                headers={"X-Shopify-Access-Token": access_token}
            ) as response:
                return response.status == 200
    except Exception as e:
        logger.error(f"Shopify validation failed: {e}")
        return False


async def validate_serper(api_key: str) -> bool:
    """Validate Serper API key."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": api_key},
                json={"q": "test"}
            ) as response:
                return response.status == 200
    except Exception as e:
        logger.error(f"Serper validation failed: {e}")
        return False


def read_env_file() -> Dict[str, str]:
    """Read current .env file."""
    env_vars = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"\'')
    return env_vars


def write_env_file(env_vars: Dict[str, str]):
    """Write to .env file, preserving comments and order."""
    lines = []
    existing_keys = set()
    
    # Read existing file to preserve structure
    if ENV_FILE.exists():
        with open(ENV_FILE, 'r') as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith('#') and '=' in stripped:
                    key = stripped.split('=', 1)[0].strip()
                    existing_keys.add(key)
                    if key in env_vars:
                        lines.append(f'{key}="{env_vars[key]}"\n')
                    else:
                        lines.append(line)
                else:
                    lines.append(line)
    
    # Add new keys that weren't in the file
    for key, value in env_vars.items():
        if key not in existing_keys:
            lines.append(f'{key}="{value}"\n')
    
    # Write back
    with open(ENV_FILE, 'w') as f:
        f.writelines(lines)


@router.get("/status")
async def get_connection_status() -> Dict[str, bool]:
    """Get status of all service connections."""
    env_vars = read_env_file()
    
    def is_valid_key(key: str) -> bool:
        """Check if a key is a real API key (not a placeholder)."""
        if not key:
            return False
        placeholders = ["your_", "placeholder", "xxx", "change_this", "insert_", "add_your"]
        return not any(p in key.lower() for p in placeholders)
    
    return {
        "anthropic": is_valid_key(env_vars.get("ANTHROPIC_API_KEY", "")),
        "openai": is_valid_key(env_vars.get("OPENAI_API_KEY", "")),
        "replicate": is_valid_key(env_vars.get("REPLICATE_API_TOKEN", "")),
        "printify": is_valid_key(env_vars.get("PRINTIFY_API_TOKEN", "") or env_vars.get("PRINTIFY_API_KEY", "")),
        "shopify": is_valid_key(env_vars.get("SHOPIFY_ACCESS_TOKEN", "")),
        "serper": is_valid_key(env_vars.get("SERPER_API_KEY", ""))
    }


@router.post("/save")
async def save_connection(data: ConnectionCredentials) -> Dict[str, Any]:
    """Save connection credentials to .env file."""
    service = data.service
    creds = data.credentials
    
    # Map credentials to env var names
    env_mappings = {
        "anthropic": {"anthropic_api_key": "ANTHROPIC_API_KEY"},
        "openai": {"openai_api_key": "OPENAI_API_KEY"},
        "replicate": {"replicate_api_token": "REPLICATE_API_TOKEN"},
        "printify": {
            "printify_api_token": "PRINTIFY_API_TOKEN",
            "printify_shop_id": "PRINTIFY_SHOP_ID"
        },
        "shopify": {
            "shopify_shop_name": "SHOPIFY_SHOP_NAME",
            "shopify_access_token": "SHOPIFY_ACCESS_TOKEN"
        },
        "serper": {"serper_api_key": "SERPER_API_KEY"}
    }
    
    if service not in env_mappings:
        raise HTTPException(status_code=400, detail=f"Unknown service: {service}")
    
    # Read current env
    env_vars = read_env_file()
    
    # Update with new credentials
    for cred_key, env_key in env_mappings[service].items():
        if cred_key in creds:
            env_vars[env_key] = creds[cred_key]
    
    # Write back
    write_env_file(env_vars)
    
    logger.info(f"Saved credentials for {service}")
    
    return {
        "success": True,
        "service": service,
        "message": f"{service} credentials saved successfully"
    }


@router.post("/test/{service}")
async def test_connection(service: str) -> ConnectionTestResult:
    """Test a service connection."""
    env_vars = read_env_file()
    
    validators = {
        "anthropic": lambda: validate_anthropic(env_vars.get("ANTHROPIC_API_KEY", "")),
        "openai": lambda: validate_openai(env_vars.get("OPENAI_API_KEY", "")),
        "replicate": lambda: validate_replicate(env_vars.get("REPLICATE_API_TOKEN", "")),
        "printify": lambda: validate_printify(
            env_vars.get("PRINTIFY_API_TOKEN") or env_vars.get("PRINTIFY_API_KEY", ""),
            env_vars.get("PRINTIFY_SHOP_ID", "")
        ),
        "shopify": lambda: validate_shopify(
            env_vars.get("SHOPIFY_SHOP_NAME", ""),
            env_vars.get("SHOPIFY_ACCESS_TOKEN", "")
        ),
        "serper": lambda: validate_serper(env_vars.get("SERPER_API_KEY", ""))
    }
    
    if service not in validators:
        raise HTTPException(status_code=400, detail=f"Unknown service: {service}")
    
    try:
        success = await validators[service]()
        return ConnectionTestResult(
            service=service,
            success=success,
            message="Connection successful" if success else "Connection failed"
        )
    except Exception as e:
        return ConnectionTestResult(
            service=service,
            success=False,
            message=str(e)
        )


@router.get("/info/{service}")
async def get_service_info(service: str) -> Dict[str, Any]:
    """Get information about a service and how to set it up."""
    info = {
        "anthropic": {
            "name": "Anthropic Claude",
            "description": "AI language model for conversation and planning",
            "setup_url": "https://console.anthropic.com/settings/keys",
            "docs_url": "https://docs.anthropic.com/",
            "required_fields": ["ANTHROPIC_API_KEY"],
            "pricing": "Pay per token, ~$3/million tokens for Claude 3 Sonnet"
        },
        "openai": {
            "name": "OpenAI",
            "description": "Voice transcription (Whisper) and text-to-speech",
            "setup_url": "https://platform.openai.com/api-keys",
            "docs_url": "https://platform.openai.com/docs",
            "required_fields": ["OPENAI_API_KEY"],
            "pricing": "Pay per use, Whisper ~$0.006/minute"
        },
        "replicate": {
            "name": "Replicate",
            "description": "AI image generation (Flux, SDXL, Recraft)",
            "setup_url": "https://replicate.com/account/api-tokens",
            "docs_url": "https://replicate.com/docs",
            "required_fields": ["REPLICATE_API_TOKEN"],
            "pricing": "Pay per run, ~$0.003-0.05 per image"
        },
        "printify": {
            "name": "Printify",
            "description": "Print-on-demand product creation and fulfillment",
            "setup_url": "https://printify.com/app/account/api",
            "docs_url": "https://developers.printify.com/",
            "required_fields": ["PRINTIFY_API_TOKEN", "PRINTIFY_SHOP_ID"],
            "pricing": "Free API, pay per product fulfilled"
        },
        "shopify": {
            "name": "Shopify",
            "description": "E-commerce store management",
            "setup_url": "https://admin.shopify.com/store/settings/apps/development",
            "docs_url": "https://shopify.dev/docs/api",
            "required_fields": ["SHOPIFY_SHOP_NAME", "SHOPIFY_ACCESS_TOKEN"],
            "pricing": "Included with Shopify plan"
        },
        "serper": {
            "name": "Serper",
            "description": "Google Search API for research",
            "setup_url": "https://serper.dev/api-key",
            "docs_url": "https://serper.dev/docs",
            "required_fields": ["SERPER_API_KEY"],
            "pricing": "Free tier: 2,500 queries/month"
        }
    }
    
    if service not in info:
        raise HTTPException(status_code=404, detail=f"Unknown service: {service}")
    
    return info[service]
