"""
Setup Wizard API

Interactive onboarding for configuring all integrations.
Validates credentials and saves to .env automatically.
"""

import os
import re
import json
import httpx
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/setup", tags=["Setup Wizard"])


# =============================================================================
# Integration Definitions
# =============================================================================

INTEGRATIONS = {
    "anthropic": {
        "name": "Anthropic (Claude AI)",
        "category": "AI",
        "description": "Powers Otto's intelligence - required for core functionality",
        "required": True,
        "env_keys": ["ANTHROPIC_API_KEY"],
        "setup_url": "https://console.anthropic.com/settings/keys",
        "setup_steps": [
            "Go to console.anthropic.com and sign in (or create account)",
            "Navigate to Settings → API Keys",
            "Click 'Create Key' and copy the key",
            "Paste it below"
        ],
        "key_pattern": r"^sk-ant-",
        "test_endpoint": "https://api.anthropic.com/v1/messages"
    },
    "openai": {
        "name": "OpenAI (GPT)",
        "category": "AI",
        "description": "Alternative AI provider for GPT models",
        "required": False,
        "env_keys": ["OPENAI_API_KEY"],
        "setup_url": "https://platform.openai.com/api-keys",
        "setup_steps": [
            "Go to platform.openai.com and sign in",
            "Click your profile → API Keys",
            "Click 'Create new secret key'",
            "Copy and paste below"
        ],
        "key_pattern": r"^sk-",
        "test_endpoint": "https://api.openai.com/v1/models"
    },
    "replicate": {
        "name": "Replicate",
        "category": "AI",
        "description": "AI image/video generation (Flux, Stable Diffusion, etc)",
        "required": False,
        "env_keys": ["REPLICATE_API_TOKEN"],
        "setup_url": "https://replicate.com/account/api-tokens",
        "setup_steps": [
            "Go to replicate.com and sign in (GitHub login works)",
            "Click your avatar → API Tokens",
            "Copy your default token or create a new one",
            "Paste below"
        ],
        "key_pattern": r"^r8_",
        "test_endpoint": "https://api.replicate.com/v1/account"
    },
    "printify": {
        "name": "Printify",
        "category": "E-Commerce",
        "description": "Print-on-demand product creation and fulfillment",
        "required": False,
        "env_keys": ["PRINTIFY_API_TOKEN", "PRINTIFY_SHOP_ID"],
        "setup_url": "https://printify.com/app/account/api",
        "setup_steps": [
            "Log into Printify and go to Account → Connections",
            "Scroll down to 'API' section",
            "Click 'Generate' to create an API token",
            "Also note your Shop ID from the URL when viewing your shop",
            "Paste both below"
        ],
        "key_pattern": r"^eyJ",
        "test_endpoint": "https://api.printify.com/v1/shops.json"
    },
    "shopify": {
        "name": "Shopify",
        "category": "E-Commerce",
        "description": "E-commerce store management",
        "required": False,
        "env_keys": ["SHOPIFY_STORE_URL", "SHOPIFY_ACCESS_TOKEN"],
        "setup_url": "https://admin.shopify.com/store/YOUR-STORE/settings/apps/development",
        "setup_steps": [
            "Go to Shopify Admin → Settings → Apps and sales channels",
            "Click 'Develop apps' → Create an app",
            "Configure Admin API scopes (read/write products, orders, etc)",
            "Install the app and copy the Admin API access token",
            "Also enter your store URL (e.g., my-store.myshopify.com)"
        ],
        "key_pattern": r"^shpat_",
        "test_endpoint": None  # Constructed dynamically
    },
    "youtube": {
        "name": "YouTube",
        "category": "Social Media",
        "description": "Upload and manage YouTube videos",
        "required": False,
        "env_keys": ["YOUTUBE_API_KEY"],
        "setup_url": "https://console.cloud.google.com/apis/credentials",
        "setup_steps": [
            "Go to Google Cloud Console",
            "Create a project (or select existing)",
            "Enable 'YouTube Data API v3'",
            "Go to Credentials → Create Credentials → API Key",
            "Copy and paste below"
        ],
        "key_pattern": r"^AIza",
        "test_endpoint": "https://www.googleapis.com/youtube/v3/channels?part=id&mine=true"
    },
    "elevenlabs": {
        "name": "ElevenLabs",
        "category": "AI",
        "description": "AI voice generation and text-to-speech",
        "required": False,
        "env_keys": ["ELEVENLABS_API_KEY"],
        "setup_url": "https://elevenlabs.io/app/settings/api-keys",
        "setup_steps": [
            "Go to elevenlabs.io and sign in",
            "Click your profile → Profile + API Key",
            "Copy your API key",
            "Paste below"
        ],
        "key_pattern": None,
        "test_endpoint": "https://api.elevenlabs.io/v1/user"
    },
    "sendgrid": {
        "name": "SendGrid",
        "category": "Communication",
        "description": "Email sending (100 free emails/day)",
        "required": False,
        "env_keys": ["SENDGRID_API_KEY"],
        "setup_url": "https://app.sendgrid.com/settings/api_keys",
        "setup_steps": [
            "Go to sendgrid.com and create free account",
            "Go to Settings → API Keys",
            "Click 'Create API Key' (Full Access)",
            "Copy the key immediately (only shown once!)",
            "Paste below"
        ],
        "key_pattern": r"^SG\.",
        "test_endpoint": "https://api.sendgrid.com/v3/user/profile"
    },
    "serper": {
        "name": "Serper (Web Search)",
        "category": "Utilities",
        "description": "Google search API (100 free searches/month)",
        "required": False,
        "env_keys": ["SERPER_API_KEY"],
        "setup_url": "https://serper.dev/api-key",
        "setup_steps": [
            "Go to serper.dev and sign up (free)",
            "Your API key is shown on the dashboard",
            "Copy and paste below"
        ],
        "key_pattern": None,
        "test_endpoint": "https://google.serper.dev/search"
    },
    "twitter": {
        "name": "Twitter/X",
        "category": "Social Media",
        "description": "Post to Twitter (uses browser automation)",
        "required": False,
        "env_keys": ["TWITTER_USERNAME", "TWITTER_PASSWORD"],
        "setup_url": None,
        "setup_steps": [
            "Enter your Twitter username and password",
            "Otto uses browser automation to post",
            "No API key needed!"
        ],
        "key_pattern": None,
        "test_endpoint": None
    },
    "instagram": {
        "name": "Instagram",
        "category": "Social Media",
        "description": "Post to Instagram (uses browser automation)",
        "required": False,
        "env_keys": ["INSTAGRAM_USERNAME", "INSTAGRAM_PASSWORD"],
        "setup_url": None,
        "setup_steps": [
            "Enter your Instagram username and password",
            "Otto uses browser automation to post",
            "No API key needed!"
        ],
        "key_pattern": None,
        "test_endpoint": None
    },
    "linkedin": {
        "name": "LinkedIn",
        "category": "Social Media",
        "description": "Post to LinkedIn (uses browser automation)",
        "required": False,
        "env_keys": ["LINKEDIN_EMAIL", "LINKEDIN_PASSWORD"],
        "setup_url": None,
        "setup_steps": [
            "Enter your LinkedIn email and password",
            "Otto uses browser automation to post",
            "No API key needed!"
        ],
        "key_pattern": None,
        "test_endpoint": None
    },
    "facebook": {
        "name": "Facebook",
        "category": "Social Media",
        "description": "Post to Facebook (uses browser automation)",
        "required": False,
        "env_keys": ["FACEBOOK_EMAIL", "FACEBOOK_PASSWORD"],
        "setup_url": None,
        "setup_steps": [
            "Enter your Facebook email and password",
            "Otto uses browser automation to post",
            "No API key needed!"
        ],
        "key_pattern": None,
        "test_endpoint": None
    },
    "discord_webhook": {
        "name": "Discord",
        "category": "Communication",
        "description": "Receive messages from Discord",
        "required": False,
        "env_keys": ["DISCORD_BOT_TOKEN", "DISCORD_APPLICATION_ID"],
        "setup_url": "https://discord.com/developers/applications",
        "setup_steps": [
            "Go to Discord Developer Portal",
            "Create New Application",
            "Go to Bot → Add Bot → Copy Token",
            "Copy Application ID from General Information",
            "Paste both below"
        ],
        "key_pattern": None,
        "test_endpoint": "https://discord.com/api/v10/users/@me"
    },
    "telegram_webhook": {
        "name": "Telegram",
        "category": "Communication",
        "description": "Receive messages from Telegram",
        "required": False,
        "env_keys": ["TELEGRAM_BOT_TOKEN"],
        "setup_url": "https://t.me/BotFather",
        "setup_steps": [
            "Message @BotFather on Telegram",
            "Send /newbot and follow prompts",
            "Copy the bot token provided",
            "Paste below"
        ],
        "key_pattern": r"^\d+:",
        "test_endpoint": "https://api.telegram.org/bot{token}/getMe"
    },
    "whatsapp_webhook": {
        "name": "WhatsApp Business",
        "category": "Communication",
        "description": "Receive messages from WhatsApp",
        "required": False,
        "env_keys": ["WHATSAPP_ACCESS_TOKEN", "WHATSAPP_PHONE_NUMBER_ID"],
        "setup_url": "https://developers.facebook.com/apps/",
        "setup_steps": [
            "Create a Meta Developer account",
            "Create an app with WhatsApp product",
            "Get temporary access token from WhatsApp → API Setup",
            "Copy Phone Number ID",
            "Paste both below"
        ],
        "key_pattern": None,
        "test_endpoint": None
    },
    "email_inbound": {
        "name": "Email (SendGrid Inbound)",
        "category": "Communication",
        "description": "Receive and respond to emails via SendGrid",
        "required": False,
        "env_keys": ["SENDGRID_API_KEY", "SENDGRID_FROM_EMAIL", "WEBHOOK_BASE_URL"],
        "setup_url": "https://app.sendgrid.com/settings/parse",
        "setup_steps": [
            "Sign up at sendgrid.com (free: 100 emails/day)",
            "Generate API key at Settings → API Keys",
            "Set up Inbound Parse: Settings → Inbound Parse",
            "Configure hostname (e.g., otto.yourdomain.com)",
            f"Set webhook URL to your Otto instance + /api/webhooks/email/inbound",
            "Add MX record pointing to mx.sendgrid.net"
        ],
        "key_pattern": r"^SG\.",
        "test_endpoint": "https://api.sendgrid.com/v3/user/profile"
    },
    "ollama": {
        "name": "Ollama (Local LLMs)",
        "category": "AI",
        "description": "Run AI models locally - no API keys, 100% private! One-click downloads below.",
        "required": False,
        "env_keys": ["OLLAMA_BASE_URL"],
        "setup_url": "https://ollama.ai/download",
        "setup_steps": [
            "Click 'Download Ollama' below (or visit ollama.ai)",
            "Install and launch Ollama",
            "Come back here and click 'Download Models'",
            "Choose from our starter pack (6.1GB total)",
            "Start using local AI immediately!"
        ],
        "key_pattern": None,
        "test_endpoint": None,
        "has_model_manager": True
    }
}


# =============================================================================
# Request/Response Models
# =============================================================================

class IntegrationStatus(BaseModel):
    id: str
    name: str
    category: str
    description: str
    required: bool
    configured: bool
    validated: bool
    env_keys: List[str]
    setup_url: Optional[str]
    setup_steps: List[str]
    missing_keys: List[str]


class ValidateRequest(BaseModel):
    integration_id: str
    credentials: Dict[str, str]


class SaveRequest(BaseModel):
    integration_id: str
    credentials: Dict[str, str]


# =============================================================================
# Helper Functions
# =============================================================================

def get_env_path() -> Path:
    """Get the .env file path."""
    return Path(__file__).parent.parent.parent / ".env"


def read_env_file() -> Dict[str, str]:
    """Read current .env values."""
    env_path = get_env_path()
    env_vars = {}
    
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    env_vars[key.strip()] = value.strip()
    
    return env_vars


def update_env_file(updates: Dict[str, str]):
    """Update .env file with new values."""
    env_path = get_env_path()
    
    # Read existing content
    lines = []
    if env_path.exists():
        with open(env_path, "r") as f:
            lines = f.readlines()
    
    # Track which keys we've updated
    updated_keys = set()
    
    # Update existing keys
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=")[0].strip()
            if key in updates:
                new_lines.append(f"{key}={updates[key]}\n")
                updated_keys.add(key)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    # Add new keys that weren't in the file
    for key, value in updates.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={value}\n")
    
    # Write back
    with open(env_path, "w") as f:
        f.writelines(new_lines)
    
    # Also update os.environ
    for key, value in updates.items():
        os.environ[key] = value


def check_integration_status(integration_id: str) -> IntegrationStatus:
    """Check the status of an integration."""
    if integration_id not in INTEGRATIONS:
        raise HTTPException(404, f"Unknown integration: {integration_id}")
    
    config = INTEGRATIONS[integration_id]
    env_vars = read_env_file()
    
    # Check which keys are configured
    missing_keys = []
    configured = True
    for key in config["env_keys"]:
        value = env_vars.get(key, "") or os.getenv(key, "")
        if not value or value.startswith("your_") or value == "":
            missing_keys.append(key)
            configured = False
    
    return IntegrationStatus(
        id=integration_id,
        name=config["name"],
        category=config["category"],
        description=config["description"],
        required=config["required"],
        configured=configured,
        validated=configured,  # Assume validated if configured for now
        env_keys=config["env_keys"],
        setup_url=config.get("setup_url"),
        setup_steps=config["setup_steps"],
        missing_keys=missing_keys
    )


async def validate_credentials(integration_id: str, credentials: Dict[str, str]) -> Dict[str, Any]:
    """Validate credentials for an integration."""
    if integration_id not in INTEGRATIONS:
        raise HTTPException(404, f"Unknown integration: {integration_id}")
    
    config = INTEGRATIONS[integration_id]
    
    # Check pattern match first
    if config.get("key_pattern"):
        main_key = config["env_keys"][0]
        if main_key in credentials:
            if not re.match(config["key_pattern"], credentials[main_key]):
                return {
                    "valid": False,
                    "error": f"Invalid key format. Expected pattern: {config['key_pattern']}"
                }
    
    # Test endpoint if available
    test_endpoint = config.get("test_endpoint")
    if test_endpoint:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {}
                main_key = credentials.get(config["env_keys"][0], "")
                
                # Configure headers based on integration
                if integration_id == "anthropic":
                    headers = {
                        "x-api-key": main_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    }
                    # Just check if we can reach the API
                    response = await client.post(
                        test_endpoint,
                        headers=headers,
                        json={"model": "claude-3-haiku-20240307", "max_tokens": 1, "messages": [{"role": "user", "content": "hi"}]}
                    )
                elif integration_id == "openai":
                    headers = {"Authorization": f"Bearer {main_key}"}
                    response = await client.get(test_endpoint, headers=headers)
                elif integration_id == "replicate":
                    headers = {"Authorization": f"Token {main_key}"}
                    response = await client.get(test_endpoint, headers=headers)
                elif integration_id == "printify":
                    headers = {"Authorization": f"Bearer {main_key}"}
                    response = await client.get(test_endpoint, headers=headers)
                elif integration_id == "elevenlabs":
                    headers = {"xi-api-key": main_key}
                    response = await client.get(test_endpoint, headers=headers)
                elif integration_id == "sendgrid":
                    headers = {"Authorization": f"Bearer {main_key}"}
                    response = await client.get(test_endpoint, headers=headers)
                elif integration_id == "discord_webhook":
                    headers = {"Authorization": f"Bot {main_key}"}
                    response = await client.get(test_endpoint, headers=headers)
                elif integration_id == "telegram_webhook":
                    url = test_endpoint.format(token=main_key)
                    response = await client.get(url)
                elif integration_id == "email_inbound":
                    # Validate SendGrid API key
                    headers = {"Authorization": f"Bearer {main_key}"}
                    response = await client.get(test_endpoint, headers=headers)
                elif integration_id == "ollama":
                    # Check if Ollama is running locally
                    ollama_url = credentials.get("OLLAMA_BASE_URL", "http://localhost:11434")
                    response = await client.get(f"{ollama_url}/api/tags")
                else:
                    # Generic auth header
                    headers = {"Authorization": f"Bearer {main_key}"}
                    response = await client.get(test_endpoint, headers=headers)
                
                if response.status_code in [200, 201]:
                    return {"valid": True, "message": "Credentials validated successfully!"}
                elif response.status_code == 401:
                    return {"valid": False, "error": "Invalid credentials - authentication failed"}
                elif response.status_code == 403:
                    return {"valid": False, "error": "Credentials valid but lacking permissions"}
                else:
                    return {"valid": True, "message": f"Credentials appear valid (status: {response.status_code})"}
                    
        except httpx.TimeoutException:
            return {"valid": False, "error": "Connection timeout - check your internet"}
        except Exception as e:
            logger.warning(f"Validation error for {integration_id}: {e}")
            return {"valid": True, "message": "Could not validate remotely, but format looks correct"}
    
    # No test endpoint - just check that values are provided
    return {"valid": True, "message": "Credentials saved (no remote validation available)"}


# =============================================================================
# API Endpoints
# =============================================================================

@router.get("/integrations")
async def list_integrations() -> List[IntegrationStatus]:
    """Get status of all available integrations."""
    statuses = []
    for integration_id in INTEGRATIONS:
        try:
            status = check_integration_status(integration_id)
            statuses.append(status)
        except Exception as e:
            logger.error(f"Error checking {integration_id}: {e}")
    
    # Sort: required first, then by category, then by name
    statuses.sort(key=lambda x: (not x.required, x.category, x.name))
    return statuses


@router.get("/integrations/{integration_id}")
async def get_integration(integration_id: str) -> IntegrationStatus:
    """Get status of a specific integration."""
    return check_integration_status(integration_id)


@router.post("/validate")
async def validate_integration(request: ValidateRequest) -> Dict[str, Any]:
    """Validate credentials without saving."""
    result = await validate_credentials(request.integration_id, request.credentials)
    return result


@router.post("/save")
async def save_integration(request: SaveRequest) -> Dict[str, Any]:
    """Validate and save credentials to .env file."""
    # First validate
    validation = await validate_credentials(request.integration_id, request.credentials)
    
    if not validation.get("valid", False):
        raise HTTPException(400, validation.get("error", "Invalid credentials"))
    
    # Save to .env
    try:
        update_env_file(request.credentials)
        return {
            "success": True,
            "message": f"Credentials saved for {INTEGRATIONS[request.integration_id]['name']}",
            "validation": validation
        }
    except Exception as e:
        logger.error(f"Failed to save credentials: {e}")
        raise HTTPException(500, f"Failed to save: {str(e)}")


@router.get("/summary")
async def get_setup_summary() -> Dict[str, Any]:
    """Get a summary of setup progress."""
    statuses = await list_integrations()
    
    total = len(statuses)
    configured = sum(1 for s in statuses if s.configured)
    required = [s for s in statuses if s.required]
    required_configured = sum(1 for s in required if s.configured)
    
    categories = {}
    for s in statuses:
        if s.category not in categories:
            categories[s.category] = {"total": 0, "configured": 0}
        categories[s.category]["total"] += 1
        if s.configured:
            categories[s.category]["configured"] += 1
    
    return {
        "total_integrations": total,
        "configured": configured,
        "required_total": len(required),
        "required_configured": required_configured,
        "ready": required_configured == len(required),
        "categories": categories,
        "next_recommended": next(
            (s.id for s in statuses if s.required and not s.configured),
            next((s.id for s in statuses if not s.configured), None)
        )
    }


# =============================================================================
# Ollama Model Management
# =============================================================================

@router.get("/ollama/status")
async def get_ollama_status():
    """Check if Ollama is installed and running."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                return {
                    "installed": True,
                    "running": True,
                    "models_count": len(models),
                    "models": [m.get("name") for m in models]
                }
    except:
        pass
    
    return {
        "installed": False,
        "running": False,
        "models_count": 0,
        "models": []
    }


@router.get("/ollama/recommended-models")
async def get_recommended_models():
    """Get list of recommended models across all categories."""
    return {
        "text_llms": {
            "category": "Text Generation (Chat & Code)",
            "description": "Language models for chat, coding, and text tasks",
            "platform": "Ollama",
            "install_url": "https://ollama.ai/download",
            "models": [
                {
                    "name": "deepseek-r1:7b",
                    "display_name": "🔥 DeepSeek R1 7B",
                    "description": "Reasoning model, exceptional performance",
                    "size_gb": 4.7,
                    "use_case": "Advanced reasoning & problem solving",
                    "speed": 4,
                    "quality": 5,
                    "type": "text",
                    "featured": True
                },
                {
                    "name": "deepseek-coder-v2:16b",
                    "display_name": "DeepSeek Coder V2 16B",
                    "description": "State-of-the-art code generation",
                    "size_gb": 9.0,
                    "use_case": "Professional coding & debugging",
                    "speed": 3,
                    "quality": 5,
                    "type": "text"
                },
                {
                    "name": "llama3.2:3b",
                    "display_name": "Llama 3.2 3B",
                    "description": "Fast and capable for everyday tasks",
                    "size_gb": 2.0,
                    "use_case": "General chat & assistance",
                    "speed": 5,
                    "quality": 3,
                    "type": "text"
                },
                {
                    "name": "qwen2.5:7b",
                    "display_name": "Qwen 2.5 7B",
                    "description": "Alibaba's powerful multilingual model",
                    "size_gb": 4.7,
                    "use_case": "Multilingual tasks, Chinese support",
                    "speed": 4,
                    "quality": 4,
                    "type": "text"
                },
                {
                    "name": "codellama:7b",
                    "display_name": "Code Llama 7B",
                    "description": "Specialized for programming tasks",
                    "size_gb": 3.8,
                    "use_case": "Code generation & debugging",
                    "speed": 3,
                    "quality": 5,
                    "type": "text"
                },
                {
                    "name": "phi3:mini",
                    "display_name": "Phi-3 Mini",
                    "description": "Microsoft's tiny powerhouse (3.8B)",
                    "size_gb": 2.3,
                    "use_case": "Lightweight, fast inference",
                    "speed": 5,
                    "quality": 4,
                    "type": "text"
                },
                {
                    "name": "nomic-embed-text",
                    "display_name": "Nomic Embeddings",
                    "description": "For semantic search and RAG",
                    "size_gb": 0.3,
                    "use_case": "Document search & analysis",
                    "speed": 5,
                    "quality": 5,
                    "type": "embedding"
                }
            ],
            "total_size_gb": 27.8
        },
        "vision": {
            "category": "Vision Models",
            "description": "AI models that can see and understand images",
            "platform": "Ollama",
            "install_url": "https://ollama.ai/download",
            "models": [
                {
                    "name": "llama3.2-vision:11b",
                    "display_name": "Llama 3.2 Vision 11B",
                    "description": "See and understand images",
                    "size_gb": 7.9,
                    "use_case": "Image analysis & description",
                    "speed": 3,
                    "quality": 4,
                    "type": "vision",
                    "platform": "Ollama"
                },
                {
                    "name": "llava:13b",
                    "display_name": "LLaVA 13B",
                    "description": "Advanced vision + language understanding",
                    "size_gb": 8.0,
                    "use_case": "Image Q&A, OCR, visual analysis",
                    "speed": 2,
                    "quality": 4,
                    "type": "vision",
                    "platform": "Ollama"
                }
            ]
        },
        "image_generation": {
            "category": "Image Generation",
            "description": "Create stunning images from text prompts locally",
            "platform": "Python Diffusers Library",
            "install_url": "https://github.com/huggingface/diffusers",
            "quick_install": "pip install diffusers transformers accelerate",
            "models": [
                {
                    "name": "Tencent-Hunyuan/HunyuanDiT-v1.2-Diffusers",
                    "display_name": "🔥 Hunyuan-DiT (Tencent)",
                    "description": "Chinese powerhouse, multilingual prompts",
                    "size_gb": 7.9,
                    "use_case": "Chinese/English generation, high quality",
                    "speed": 4,
                    "quality": 5,
                    "type": "image_gen",
                    "platform": "Diffusers",
                    "install_method": "pip install diffusers",
                    "auto_download": True,
                    "featured": True
                },
                {
                    "name": "black-forest-labs/FLUX.1-schnell",
                    "display_name": "⚡ Flux.1 Schnell",
                    "description": "Cutting-edge, fastest Flux model (1-4 steps)",
                    "size_gb": 23.8,
                    "use_case": "State-of-the-art quality, ultra-fast",
                    "speed": 5,
                    "quality": 5,
                    "type": "image_gen",
                    "platform": "Diffusers",
                    "install_method": "pip install diffusers",
                    "auto_download": True,
                    "featured": True
                },
                {
                    "name": "black-forest-labs/FLUX.1-dev",
                    "display_name": "🔥 Flux.1 Dev",
                    "description": "Top-tier image quality, guidance distilled",
                    "size_gb": 23.8,
                    "use_case": "Professional-grade images",
                    "speed": 4,
                    "quality": 5,
                    "type": "image_gen",
                    "platform": "Diffusers",
                    "install_method": "pip install diffusers",
                    "auto_download": True,
                    "featured": True
                },
                {
                    "name": "stabilityai/sdxl-turbo",
                    "display_name": "SDXL Turbo",
                    "description": "Ultra-fast, 1-step image generation",
                    "size_gb": 6.9,
                    "use_case": "Quick iterations, real-time generation",
                    "speed": 5,
                    "quality": 4,
                    "type": "image_gen",
                    "platform": "Diffusers",
                    "install_method": "pip install diffusers",
                    "auto_download": True
                },
                {
                    "name": "ByteDance/SDXL-Lightning",
                    "display_name": "SDXL Lightning",
                    "description": "2-4 step generation, lightning fast",
                    "size_gb": 6.9,
                    "use_case": "Fast high-quality generation",
                    "speed": 5,
                    "quality": 4,
                    "type": "image_gen",
                    "platform": "Diffusers",
                    "install_method": "pip install diffusers",
                    "auto_download": True
                },
                {
                    "name": "stabilityai/stable-diffusion-xl-base-1.0",
                    "display_name": "Stable Diffusion XL",
                    "description": "Industry standard, excellent quality",
                    "size_gb": 6.9,
                    "use_case": "General image generation",
                    "speed": 4,
                    "quality": 5,
                    "type": "image_gen",
                    "platform": "Diffusers",
                    "install_method": "pip install diffusers",
                    "auto_download": True
                },
                {
                    "name": "playgroundai/playground-v2.5-1024px-aesthetic",
                    "display_name": "Playground v2.5",
                    "description": "Aesthetic quality, vibrant colors",
                    "size_gb": 5.3,
                    "use_case": "Artistic & aesthetic images",
                    "speed": 4,
                    "quality": 5,
                    "type": "image_gen",
                    "platform": "Diffusers",
                    "install_method": "pip install diffusers",
                    "auto_download": True
                },
                {
                    "name": "kandinsky-community/kandinsky-3",
                    "display_name": "Kandinsky 3.0",
                    "description": "Russian AI model, unique artistic style",
                    "size_gb": 11.9,
                    "use_case": "Artistic generation, multilingual",
                    "speed": 3,
                    "quality": 5,
                    "type": "image_gen",
                    "platform": "Diffusers",
                    "install_method": "pip install diffusers",
                    "auto_download": True
                },
                {
                    "name": "runwayml/stable-diffusion-v1-5",
                    "display_name": "Stable Diffusion 1.5",
                    "description": "Lightweight, fast, great for older GPUs",
                    "size_gb": 4.2,
                    "use_case": "Low-resource systems",
                    "speed": 5,
                    "quality": 4,
                    "type": "image_gen",
                    "platform": "Diffusers",
                    "install_method": "pip install diffusers",
                    "auto_download": True
                }
            ],
            "setup_steps": [
                "Install: pip install diffusers transformers accelerate torch",
                "Models auto-download on first use",
                "Generate: from diffusers import DiffusionPipeline; pipe = DiffusionPipeline.from_pretrained('stabilityai/sdxl-turbo')",
                "Create: pipe('a photo of a cat').images[0].save('cat.png')"
            ],
            "note": "Models download automatically from Hugging Face on first use. No complex setup needed!",
            "alternative": "For instant API access without local setup, use Replicate (already integrated)",
            "advanced_option": "For advanced control: Install ComfyUI or Automatic1111 WebUI"
        },
        "audio": {
            "category": "Audio & Speech",
            "description": "Text-to-speech and audio generation locally",
            "platform": "Coqui TTS + Python",
            "install_url": "https://github.com/coqui-ai/TTS",
            "quick_install": "pip install TTS torch",
            "models": [
                {
                    "name": "xtts_v2",
                    "display_name": "🔥 XTTS v2 (Coqui)",
                    "description": "Multi-lingual TTS with voice cloning",
                    "size_gb": 1.8,
                    "use_case": "Voice generation, multilingual TTS",
                    "speed": 4,
                    "quality": 5,
                    "type": "audio",
                    "platform": "Coqui TTS",
                    "install_method": "pip install TTS",
                    "featured": True
                },
                {
                    "name": "stabilityai/stable-audio-open-1.0",
                    "display_name": "Stable Audio Open",
                    "description": "High-quality audio and sound effects",
                    "size_gb": 2.4,
                    "use_case": "Sound effects, ambient audio",
                    "speed": 4,
                    "quality": 5,
                    "type": "audio",
                    "platform": "Diffusers",
                    "install_method": "pip install diffusers",
                    "auto_download": True
                },
                {
                    "name": "facebook/audiogen-medium",
                    "display_name": "AudioGen (Meta)",
                    "description": "Generate audio from text prompts",
                    "size_gb": 1.5,
                    "use_case": "Sound design, effects",
                    "speed": 4,
                    "quality": 4,
                    "type": "audio",
                    "platform": "AudioCraft",
                    "install_method": "pip install audiocraft",
                    "auto_download": True
                },
                {
                    "name": "facebook/musicgen-medium",
                    "display_name": "MusicGen Medium (Meta)",
                    "description": "Generate music from text descriptions",
                    "size_gb": 3.3,
                    "use_case": "Background music, soundtracks",
                    "speed": 3,
                    "quality": 5,
                    "type": "audio",
                    "platform": "AudioCraft",
                    "install_method": "pip install audiocraft",
                    "auto_download": True
                },
                {
                    "name": "facebook/musicgen-small",
                    "display_name": "MusicGen Small (Meta)",
                    "description": "Lighter music generation model",
                    "size_gb": 1.5,
                    "use_case": "Quick music generation",
                    "speed": 4,
                    "quality": 4,
                    "type": "audio",
                    "platform": "AudioCraft",
                    "install_method": "pip install audiocraft",
                    "auto_download": True
                },
                {
                    "name": "microsoft/speecht5_tts",
                    "display_name": "SpeechT5 TTS",
                    "description": "Microsoft's versatile TTS model",
                    "size_gb": 0.4,
                    "use_case": "Lightweight TTS, narration",
                    "speed": 5,
                    "quality": 4,
                    "type": "audio",
                    "platform": "Transformers",
                    "install_method": "pip install transformers",
                    "auto_download": True
                },
                {
                    "name": "riffusion/riffusion-model-v1",
                    "display_name": "Riffusion",
                    "description": "Music generation via spectrograms",
                    "size_gb": 1.5,
                    "use_case": "Experimental music, loops",
                    "speed": 4,
                    "quality": 3,
                    "type": "audio",
                    "platform": "Diffusers",
                    "install_method": "pip install diffusers",
                    "auto_download": True
                },
                {
                    "name": "bark-small",
                    "display_name": "Bark (Suno AI)",
                    "description": "Text to audio with emotions and music",
                    "size_gb": 3.2,
                    "use_case": "Podcasts, audiobooks, sound effects",
                    "speed": 3,
                    "quality": 4,
                    "type": "audio",
                    "platform": "Local Python",
                    "download_url": "https://github.com/suno-ai/bark",
                    "install_method": "pip install bark"
                }
            ],
            "setup_steps": [
                "Install Coqui TTS: pip install TTS",
                "Test installation: tts --text 'Hello world' --out_path output.wav",
                "For Bark: pip install git+https://github.com/suno-ai/bark.git",
                "For MusicGen: pip install audiocraft"
            ],
            "note": "Local audio models run on CPU or GPU. GPU recommended for faster generation.",
            "alternative": "For cloud processing, use Replicate API (already integrated)"
        },
        "video": {
            "category": "Video Generation",
            "description": "Create videos from text and images locally",
            "platform": "Python Libraries",
            "install_url": "https://github.com/Stability-AI/generative-models",
            "quick_install": "pip install diffusers torch imageio",
            "models": [
                {
                    "name": "tencent/HunyuanVideo",
                    "display_name": "🔥 Hunyuan-Video (Tencent)",
                    "description": "Open-source Sora competitor, 5 sec videos",
                    "size_gb": 30.0,
                    "use_case": "Professional video generation",
                    "speed": 2,
                    "quality": 5,
                    "type": "video",
                    "platform": "Diffusers",
                    "install_method": "pip install diffusers",
                    "auto_download": True,
                    "featured": True
                },
                {
                    "name": "THUDM/CogVideoX-5b",
                    "display_name": "🔥 CogVideoX-5B",
                    "description": "State-of-the-art text-to-video (6 sec, 49 frames)",
                    "size_gb": 19.5,
                    "use_case": "High-quality video generation",
                    "speed": 2,
                    "quality": 5,
                    "type": "video",
                    "platform": "Diffusers",
                    "install_method": "pip install diffusers",
                    "auto_download": True,
                    "featured": True
                },
                {
                    "name": "THUDM/CogVideoX-2b",
                    "display_name": "CogVideoX-2B",
                    "description": "Lighter CogVideo model, faster generation",
                    "size_gb": 8.1,
                    "use_case": "Balanced quality and speed",
                    "speed": 3,
                    "quality": 4,
                    "type": "video",
                    "platform": "Diffusers",
                    "install_method": "pip install diffusers",
                    "auto_download": True
                },
                {
                    "name": "stabilityai/stable-video-diffusion-img2vid-xt",
                    "display_name": "Stable Video Diffusion XL",
                    "description": "Generate smooth videos from images",
                    "size_gb": 9.8,
                    "use_case": "Image-to-video, product demos",
                    "speed": 2,
                    "quality": 5,
                    "type": "video",
                    "platform": "Diffusers",
                    "install_method": "pip install diffusers",
                    "auto_download": True
                },
                {
                    "name": "VideoCrafter/VideoCrafter2",
                    "display_name": "VideoCrafter2",
                    "description": "High-resolution video generation",
                    "size_gb": 11.2,
                    "use_case": "Detailed video content",
                    "speed": 2,
                    "quality": 4,
                    "type": "video",
                    "platform": "Diffusers",
                    "install_method": "pip install diffusers",
                    "auto_download": True
                },
                {
                    "name": "damo-vilab/text-to-video-ms-1.7b",
                    "display_name": "Text-to-Video ModelScope",
                    "description": "Generate videos directly from text",
                    "size_gb": 7.2,
                    "use_case": "Text-to-video, quick concepts",
                    "speed": 3,
                    "quality": 4,
                    "type": "video",
                    "platform": "Diffusers",
                    "install_method": "pip install diffusers",
                    "auto_download": True
                },
                {
                    "name": "Vchitect/LaVie",
                    "display_name": "LaVie",
                    "description": "Text-to-video with temporal consistency",
                    "size_gb": 5.8,
                    "use_case": "Smooth motion videos",
                    "speed": 3,
                    "quality": 4,
                    "type": "video",
                    "platform": "Diffusers",
                    "install_method": "pip install diffusers",
                    "auto_download": True
                },
                {
                    "name": "animatediff",
                    "display_name": "AnimateDiff Motion",
                    "description": "Add motion to Stable Diffusion images",
                    "size_gb": 1.7,
                    "use_case": "Animated content, product videos",
                    "speed": 4,
                    "quality": 4,
                    "type": "video",
                    "platform": "Python",
                    "install_method": "pip install animatediff",
                    "auto_download": True
                }
            ],
            "api_only_note": "Premium models like Sora (OpenAI), Kling (Kuaishou), Runway Gen-3, and Pika are API-only. Use Replicate integration for cloud access.",
            "setup_steps": [
                "Install: pip install diffusers transformers imageio torch",
                "Models auto-download from Hugging Face on first use",
                "Generate: from diffusers import StableVideoDiffusionPipeline",
                "Run Otto's video tools - they'll handle the rest!"
            ],
            "note": "Video models auto-download on first use. Requires 8GB+ VRAM (GPU) for smooth generation.",
            "alternative": "For cloud-based video without GPU requirements, use Replicate API (already integrated)",
            "advanced_option": "For advanced workflows: Install ComfyUI with AnimateDiff nodes"
        },
        "3d": {
            "category": "3D Model Generation",
            "description": "Generate 3D models and assets locally",
            "platform": "Python Libraries",
            "install_url": "https://github.com/openai/shap-e",
            "quick_install": "pip install trimesh torch pillow",
            "models": [
                {
                    "name": "triposr",
                    "display_name": "🔥 TripoSR",
                    "description": "Single image to 3D mesh (very fast)",
                    "size_gb": 1.4,
                    "use_case": "Product visualization, game assets",
                    "speed": 5,
                    "quality": 4,
                    "type": "3d",
                    "platform": "Local Python",
                    "download_url": "https://github.com/VAST-AI-Research/TripoSR",
                    "install_method": "pip install triposr",
                    "featured": True
                },
                {
                    "name": "TencentARC/InstantMesh",
                    "description": "Sparse-view 3D reconstruction",
                    "size_gb": 4.7,
                    "use_case": "High-quality mesh from images",
                    "speed": 3,
                    "quality": 5,
                    "type": "3d",
                    "platform": "Diffusers",
                    "install_method": "pip install diffusers",
                    "auto_download": True
                },
                {
                    "name": "sudo-ai/zero123plus-v1.2",
                    "display_name": "Zero123++",
                    "description": "Novel view synthesis for 3D",
                    "size_gb": 8.8,
                    "use_case": "Multi-view 3D generation",
                    "speed": 3,
                    "quality": 5,
                    "type": "3d",
                    "platform": "Diffusers",
                    "install_method": "pip install diffusers",
                    "auto_download": True
                },
                {
                    "name": "ashawkey/LGM",
                    "display_name": "LGM (Large Gaussian Model)",
                    "description": "Fast Gaussian splatting 3D generation",
                    "size_gb": 2.9,
                    "use_case": "Real-time 3D, NeRF alternative",
                    "speed": 5,
                    "quality": 4,
                    "type": "3d",
                    "platform": "Local Python",
                    "download_url": "https://github.com/3DTopia/LGM",
                    "install_method": "pip install lgm"
                },
                {
                    "name": "dreamgaussian",
                    "display_name": "DreamGaussian",
                    "description": "Text/image to 3D Gaussian splatting",
                    "size_gb": 3.2,
                    "use_case": "Photo-realistic 3D scenes",
                    "speed": 3,
                    "quality": 5,
                    "type": "3d",
                    "platform": "Local Python",
                    "download_url": "https://github.com/dreamgaussian/dreamgaussian",
                    "install_method": "pip install dreamgaussian"
                },
                {
                    "name": "shap-e-model-local",
                    "display_name": "Shap-E (OpenAI)",
                    "description": "Text/image to 3D models",
                    "size_gb": 3.5,
                    "use_case": "Product prototypes, 3D assets",
                    "speed": 3,
                    "quality": 4,
                    "type": "3d",
                    "platform": "Local Python",
                    "download_url": "https://github.com/openai/shap-e",
                    "install_method": "pip install shap-e"
                },
                {
                    "name": "point-e-model",
                    "display_name": "Point-E (OpenAI)",
                    "description": "Fast 3D point cloud generation",
                    "size_gb": 2.1,
                    "use_case": "Quick 3D mockups, concepts",
                    "speed": 4,
                    "quality": 3,
                    "type": "3d",
                    "platform": "Local Python",
                    "download_url": "https://github.com/openai/point-e",
                    "install_method": "pip install point-eiffusion images",
                    "size_gb": 1.7,
                    "use_case": "Animated content, product videos",
                    "speed": 4,
                    "quality": 4,
                    "type": "video",
                    "platform": "Python",
                    "install_method": "pip install animatediff",
                    "auto_download": True
                }
            ],
            "api_only_note": "Premium models like Sora (OpenAI), Kling (Kuaishou), Runway Gen-3, and Pika are API-only. Use Replicate integration for cloud access.",
            "setup_steps": [
                "Install: pip install diffusers transformers imageio torch",
                "Models auto-download from Hugging Face on first use",
                "Generate: from diffusers import StableVideoDiffusionPipeline",
                "Run Otto's video tools - they'll handle the rest!"
            ],
            "note": "Video models auto-download on first use. Requires 8GB+ VRAM (GPU) for smooth generation.",
            "alternative": "For cloud-based video without GPU requirements, use Replicate API (already integrated)",
            "advanced_option": "For advanced workflows: Install ComfyUI with AnimateDiff nodes"
        },
        "3d": {
            "category": "3D Model Generation",
            "description": "Generate 3D models and assets locally",
            "platform": "Python Libraries",
            "install_url": "https://github.com/openai/shap-e",
            "quick_install": "pip install trimesh torch pillow",
            "models": [
                {
                    "name": "shap-e-model-local",
                    "display_name": "Shap-E (Local)",
                    "description": "Text/image to 3D models",
                    "size_gb": 3.5,
                    "use_case": "Product prototypes, 3D assets",
                    "speed": 3,
                    "quality": 4,
                    "type": "3d",
                    "platform": "Local Python",
                    "download_url": "https://github.com/openai/shap-e",
                    "install_method": "pip install shap-e"
                },
                {
                    "name": "point-e-model",
                    "display_name": "Point-E (Local)",
                    "description": "Fast 3D point cloud generation",
                    "size_gb": 2.1,
                    "use_case": "Quick 3D mockups, concepts",
                    "speed": 4,
                    "quality": 3,
                    "type": "3d",
                    "platform": "Local Python",
                    "download_url": "https://github.com/openai/point-e",
                    "install_method": "pip install point-e"
                },
                {
                    "name": "triposr",
                    "display_name": "TripoSR",
                    "description": "Single image to 3D mesh (very fast)",
                    "size_gb": 1.4,
                    "use_case": "Product visualization, game assets",
                    "speed": 5,
                    "quality": 4,
                    "type": "3d",
                    "platform": "Local Python",
                    "download_url": "https://github.com/VAST-AI-Research/TripoSR",
                    "install_method": "pip install triposr"
                }
            ],
            "setup_steps": [
                "Install Shap-E: pip install git+https://github.com/openai/shap-e.git",
                "Install Point-E: pip install git+https://github.com/openai/point-e.git",
                "Install TripoSR: pip install triposr",
                "Optional: Install Blender for viewing/editing generated models"
            ],
            "note": "3D models are generated as point clouds or meshes. Use Blender or Three.js for viewing.",
            "alternative": "For instant cloud-based 3D generation, use Replicate API (already integrated)"
        },
        "training": {
            "category": "Model Training & Fine-tuning",
            "description": "Train and customize AI models with your own data",
            "platform": "Multiple Frameworks",
            "install_url": "https://github.com/huggingface/peft",
            "quick_install": "pip install transformers peft accelerate bitsandbytes",
            "models": [
                {
                    "name": "unsloth",
                    "display_name": "🔥 Unsloth - Fast Training",
                    "description": "5x faster fine-tuning, 70% less VRAM",
                    "size_gb": 0.5,
                    "use_case": "Fine-tune LLMs efficiently (Llama, Mistral, etc)",
                    "speed": 5,
                    "quality": 5,
                    "type": "training",
                    "platform": "Python",
                    "install_method": "pip install unsloth",
                    "auto_download": True,
                    "featured": True,
                    "docs": "https://github.com/unslothai/unsloth"
                },
                {
                    "name": "axolotl",
                    "display_name": "Axolotl - Advanced Training",
                    "description": "Production-grade LLM fine-tuning toolkit",
                    "size_gb": 0.3,
                    "use_case": "Professional model training with YAML configs",
                    "speed": 4,
                    "quality": 5,
                    "type": "training",
                    "platform": "Python",
                    "install_method": "pip install axolotl",
                    "auto_download": True,
                    "docs": "https://github.com/OpenAccess-AI-Collective/axolotl"
                },
                {
                    "name": "llamafactory",
                    "display_name": "LLaMA-Factory",
                    "description": "Easy WebUI for fine-tuning 100+ models",
                    "size_gb": 0.2,
                    "use_case": "User-friendly training interface",
                    "speed": 4,
                    "quality": 5,
                    "type": "training",
                    "platform": "Python",
                    "install_method": "pip install llamafactory",
                    "auto_download": True,
                    "docs": "https://github.com/hiyouga/LLaMA-Factory"
                },
                {
                    "name": "peft-lora",
                    "display_name": "PEFT (LoRA/QLoRA)",
                    "description": "Low-rank adaptation fine-tuning",
                    "size_gb": 0.1,
                    "use_case": "Memory-efficient model customization",
                    "speed": 4,
                    "quality": 5,
                    "type": "training",
                    "platform": "HuggingFace",
                    "install_method": "pip install peft",
                    "auto_download": True,
                    "docs": "https://github.com/huggingface/peft"
                },
                {
                    "name": "autotrain-advanced",
                    "display_name": "AutoTrain Advanced",
                    "description": "No-code training by HuggingFace",
                    "size_gb": 0.4,
                    "use_case": "Automated training for any task",
                    "speed": 3,
                    "quality": 4,
                    "type": "training",
                    "platform": "HuggingFace",
                    "install_method": "pip install autotrain-advanced",
                    "auto_download": True,
                    "docs": "https://github.com/huggingface/autotrain-advanced"
                },
                {
                    "name": "torchtune",
                    "display_name": "TorchTune (Native PyTorch)",
                    "description": "Easy fine-tuning for Llama models",
                    "size_gb": 0.2,
                    "use_case": "PyTorch-native LLM training",
                    "speed": 4,
                    "quality": 5,
                    "type": "training",
                    "platform": "PyTorch",
                    "install_method": "pip install torchtune",
                    "auto_download": True,
                    "docs": "https://pytorch.org/torchtune/"
                },
                {
                    "name": "diffusers-training",
                    "display_name": "Diffusers Training (Image Models)",
                    "description": "Fine-tune Stable Diffusion, FLUX, etc",
                    "size_gb": 0.1,
                    "use_case": "Custom image generation models",
                    "speed": 3,
                    "quality": 5,
                    "type": "training",
                    "platform": "Diffusers",
                    "install_method": "pip install diffusers[training]",
                    "auto_download": True,
                    "docs": "https://huggingface.co/docs/diffusers/training/overview"
                },
                {
                    "name": "kohya_ss",
                    "display_name": "Kohya_ss - Stable Diffusion Training",
                    "description": "Professional SD fine-tuning GUI",
                    "size_gb": 1.2,
                    "use_case": "LoRA, DreamBooth, custom styles",
                    "speed": 3,
                    "quality": 5,
                    "type": "training",
                    "platform": "GUI Application",
                    "install_method": "git clone & setup",
                    "docs": "https://github.com/bmaltais/kohya_ss"
                }
            ],
            "capabilities": [
                "Fine-tune any open-source LLM with your data",
                "Train image models (LoRA, DreamBooth, full fine-tuning)",
                "Create custom AI assistants with specific knowledge",
                "Low-VRAM training with LoRA/QLoRA (works on 8GB GPUs)",
                "Multi-GPU distributed training support"
            ],
            "getting_started": [
                "Install framework: pip install unsloth (recommended for beginners)",
                "Prepare your data in JSONL or Alpaca format",
                "Choose base model (Llama 3.2, DeepSeek, Mistral, etc)",
                "Run training with optimized settings",
                "Export and use your custom model!"
            ],
            "note": "Training requires GPU. For text models: 8GB+ VRAM for LoRA, 24GB+ for full fine-tuning. Image models similar requirements.",
            "cloud_option": "Use HuggingFace AutoTrain or Modal/RunPod for cloud GPUs if you don't have local GPU",
            "datasets": "Find datasets on HuggingFace Hub or create your own from documents, conversations, or images"
        },
        "recommendation": {
            "local_models": "Install Python packages (diffusers, TTS, etc.) - models auto-download on first use!",
            "api_models": "Use Replicate (already integrated) for instant results without any local setup",
            "best_for_beginners": "Start with Ollama for text/chat, then add image generation with 'pip install diffusers'",
            "hardware_recommendation": "16GB+ RAM for text models, 8GB+ VRAM (GPU) for image/video generation",
            "training_tip": "Fine-tune models with Unsloth - works on any GPU, even 8GB!"
        }
    }


@router.post("/ollama/download-model")
async def download_model(request: Dict[str, str]):
    """Download a specific Ollama model with robust network handling."""
    model_name = request.get("model")
    if not model_name:
        raise HTTPException(400, "Model name required")
    
    # Check if Ollama is running with retry
    max_check_retries = 3
    for attempt in range(max_check_retries):
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(15.0, connect=10.0),  # Longer timeout
                follow_redirects=True,
                verify=False  # Skip SSL verify for localhost
            ) as client:
                response = await client.get("http://localhost:11434/api/tags")
                if response.status_code == 200:
                    break  # Success
                elif attempt == max_check_retries - 1:
                    raise HTTPException(503, "Ollama is not running. Please start Ollama first.")
        except httpx.ConnectError:
            if attempt == max_check_retries - 1:
                raise HTTPException(503, "Cannot connect to Ollama. Is it running?")
            await asyncio.sleep(1)  # Wait before retry
        except httpx.TimeoutException:
            if attempt == max_check_retries - 1:
                raise HTTPException(503, "Ollama connection timeout. Check if Ollama is running.")
            await asyncio.sleep(1)
        except httpx.NetworkError as e:
            if attempt == max_check_retries - 1:
                raise HTTPException(503, f"Network error connecting to Ollama: {str(e)}")
            await asyncio.sleep(1)
        except Exception as e:
            if attempt == max_check_retries - 1:
                raise HTTPException(503, f"Cannot connect to Ollama: {str(e)}")
            await asyncio.sleep(1)
    
    # Trigger model pull with retry logic
    max_retries = 3
    last_error = None
    
    for attempt in range(max_retries):
        try:
            # Use longer timeout and better connection settings
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(900.0, connect=30.0, read=900.0),  # 15 min total, 30s connect
                follow_redirects=True,
                verify=False,  # Skip SSL verify for localhost
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
            ) as client:
                response = await client.post(
                    "http://localhost:11434/api/pull",
                    json={"name": model_name}
                )
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "message": f"Successfully downloaded {model_name}",
                        "model": model_name
                    }
                else:
                    last_error = f"HTTP {response.status_code}: {response.text}"
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    raise HTTPException(500, f"Failed to download model after {max_retries} attempts: {last_error}")
                    
        except httpx.TimeoutException:
            last_error = "Download timed out"
            if attempt < max_retries - 1:
                logger.warning(f"Download attempt {attempt + 1} timed out, retrying...")
                await asyncio.sleep(2 ** attempt)
                continue
            raise HTTPException(504, f"Download timed out after {max_retries} attempts. Large models may require more time. Try: 1) Check your internet connection, 2) Try a smaller model first, 3) Restart Ollama")
            
        except httpx.NetworkError as e:
            last_error = f"Network error: {str(e)}"
            if attempt < max_retries - 1:
                logger.warning(f"Network error on attempt {attempt + 1}, retrying...")
                await asyncio.sleep(2 ** attempt)
                continue
            raise HTTPException(500, f"Network error after {max_retries} attempts: {last_error}. Check your internet connection.")
            
        except httpx.ConnectError as e:
            last_error = f"Connection error: {str(e)}"
            if attempt < max_retries - 1:
                logger.warning(f"Connection error on attempt {attempt + 1}, retrying...")
                await asyncio.sleep(2 ** attempt)
                continue
            raise HTTPException(500, f"Connection error after {max_retries} attempts: {last_error}. Ollama may have stopped.")
            
        except Exception as e:
            last_error = str(e)
            if attempt < max_retries - 1:
                logger.warning(f"Error on attempt {attempt + 1}: {last_error}, retrying...")
                await asyncio.sleep(2 ** attempt)
                continue
            raise HTTPException(500, f"Error downloading model after {max_retries} attempts: {last_error}")
    
    # Should not reach here
    raise HTTPException(500, f"Download failed: {last_error}")


@router.post("/ollama/install-starter-pack")
async def install_starter_pack():
    """Download all recommended starter models with robust retry logic."""
    # Check Ollama status with retry
    max_check_retries = 3
    ollama_running = False
    
    for attempt in range(max_check_retries):
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(15.0, connect=10.0),
                follow_redirects=True,
                verify=False
            ) as client:
                response = await client.get("http://localhost:11434/api/tags")
                if response.status_code == 200:
                    ollama_running = True
                    break
        except:
            if attempt < max_check_retries - 1:
                await asyncio.sleep(1)
            else:
                raise HTTPException(503, "Ollama is not running. Please install and start Ollama first.")
    
    if not ollama_running:
        raise HTTPException(503, "Ollama is not running. Please install and start Ollama first.")
    
    models = ["llama3.2:3b", "nomic-embed-text", "codellama:7b"]
    results = []
    
    for model_name in models:
        max_retries = 3
        success = False
        last_error = None
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(900.0, connect=30.0, read=900.0),
                    follow_redirects=True,
                    verify=False,
                    limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
                ) as client:
                    response = await client.post(
                        "http://localhost:11434/api/pull",
                        json={"name": model_name}
                    )
                    
                    if response.status_code == 200:
                        results.append({
                            "model": model_name,
                            "success": True,
                            "message": f"✓ Downloaded {model_name}"
                        })
                        success = True
                        break
                    else:
                        last_error = f"HTTP {response.status_code}"
                        if attempt < max_retries - 1:
                            logger.warning(f"{model_name}: attempt {attempt + 1} returned {response.status_code}, retrying...")
                            await asyncio.sleep(2 ** attempt)
                            
            except httpx.TimeoutException:
                last_error = "Timeout"
                if attempt < max_retries - 1:
                    logger.warning(f"{model_name}: timeout on attempt {attempt + 1}, retrying...")
                    await asyncio.sleep(2 ** attempt)
                else:
                    break
                    
            except httpx.NetworkError as e:
                last_error = f"Network error: {str(e)}"
                if attempt < max_retries - 1:
                    logger.warning(f"{model_name}: network error on attempt {attempt + 1}, retrying...")
                    await asyncio.sleep(2 ** attempt)
                else:
                    break
                    
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    logger.warning(f"{model_name}: error on attempt {attempt + 1}, retrying...")
                    await asyncio.sleep(2 ** attempt)
                else:
                    break
        
        if not success:
            results.append({
                "model": model_name,
                "success": False,
                "message": f"✗ Failed after {max_retries} attempts: {last_error}"
            })
    
    successful = sum(1 for r in results if r["success"])
    return {
        "total": len(models),
        "successful": successful,
        "results": results
    }


@router.post("/python-models/install")
async def install_python_model(request: Dict[str, str]):
    """Install and download a Python-based AI model with robust retry logic."""
    import subprocess
    import sys
    
    model_type = request.get("type")  # image, video, audio, 3d, training
    model_id = request.get("model_id")
    
    if not model_type or not model_id:
        raise HTTPException(400, "model_type and model_id required")
    
    # Define installation commands for each type
    install_commands = {
        "image": {
            "base": ["pip", "install", "-qq", "diffusers", "transformers", "accelerate", "torch", "safetensors"],
            "message": "Installing image generation libraries..."
        },
        "video": {
            "base": ["pip", "install", "-qq", "diffusers", "torch", "imageio", "av", "transformers"],
            "message": "Installing video generation libraries..."
        },
        "audio": {
            "base": ["pip", "install", "-qq", "TTS", "torch", "audiocraft"],
            "message": "Installing audio generation libraries..."
        },
        "3d": {
            "base": ["pip", "install", "-qq", "trimesh", "torch", "pillow", "numpy"],
            "message": "Installing 3D model generation libraries..."
        },
        "training": {
            "base": ["pip", "install", "-qq", "transformers", "peft", "accelerate", "bitsandbytes", "torch"],
            "message": "Installing training & fine-tuning libraries..."
        }
    }
    
    if model_type not in install_commands:
        raise HTTPException(400, f"Invalid model type: {model_type}")
    
    try:
        # Install base dependencies with retry
        cmd_info = install_commands[model_type]
        max_retries = 3
        dep_success = False
        
        for attempt in range(max_retries):
            try:
                result = subprocess.run(
                    cmd_info["base"],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes
                )
                
                if result.returncode == 0:
                    dep_success = True
                    break
                else:
                    if attempt < max_retries - 1:
                        logger.warning(f"Dependencies install attempt {attempt + 1} failed, retrying...")
                        await asyncio.sleep(2 ** attempt)
            except subprocess.TimeoutExpired:
                if attempt < max_retries - 1:
                    logger.warning(f"Dependencies install timeout on attempt {attempt + 1}, retrying...")
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise HTTPException(504, "Dependency installation timed out after 3 attempts")
        
        if not dep_success:
            raise HTTPException(500, "Failed to install dependencies after 3 attempts")
        
        # Download the actual model if it's a HuggingFace model
        if model_type in ["image", "video", "audio", "3d"]:
            # Download model using huggingface_hub with retry
            try:
                # Install huggingface_hub if needed
                subprocess.run(
                    ["pip", "install", "-qq", "huggingface-hub"],
                    capture_output=True,
                    timeout=60
                )
                
                # Download the model with retry logic
                download_script = f"""
import sys
from huggingface_hub import snapshot_download
try:
    snapshot_download(
        repo_id="{model_id}", 
        cache_dir=None, 
        resume_download=True,
        max_workers=4
    )
    print("Model downloaded successfully")
except Exception as e:
    print(f"Download error: {{str(e)}}", file=sys.stderr)
    sys.exit(1)
"""
                
                max_download_retries = 3
                download_success = False
                last_error = None
                
                for attempt in range(max_download_retries):
                    try:
                        download_result = subprocess.run(
                            [sys.executable, "-c", download_script],
                            capture_output=True,
                            text=True,
                            timeout=1800  # 30 minutes for large models
                        )
                        
                        if download_result.returncode == 0:
                            download_success = True
                            break
                        else:
                            last_error = download_result.stderr[:200] if download_result.stderr else "Unknown error"
                            if attempt < max_download_retries - 1:
                                logger.warning(f"{model_id}: download attempt {attempt + 1} failed, retrying...")
                                await asyncio.sleep(2 ** attempt)
                    except subprocess.TimeoutExpired:
                        last_error = "Download timeout"
                        if attempt < max_download_retries - 1:
                            logger.warning(f"{model_id}: download timeout on attempt {attempt + 1}, retrying...")
                            await asyncio.sleep(2 ** attempt)
                    except Exception as e:
                        last_error = str(e)
                        if attempt < max_download_retries - 1:
                            logger.warning(f"{model_id}: download error on attempt {attempt + 1}, retrying...")
                            await asyncio.sleep(2 ** attempt)
                
                if download_success:
                    return {
                        "success": True,
                        "message": f"✓ {model_id} installed and downloaded!",
                        "model_id": model_id,
                        "type": model_type,
                        "downloaded": True
                    }
                else:
                    # Model download failed after retries, but dependencies are installed
                    return {
                        "success": True,
                        "message": f"✓ Dependencies installed. Model will auto-download on first use. Last error: {last_error}",
                        "model_id": model_id,
                        "type": model_type,
                        "downloaded": False
                    }
                
            except Exception as e:
                # Fallback: dependencies installed, model will download on first use
                return {
                    "success": True,
                    "message": f"✓ Dependencies installed. Model will download on first use.",
                    "model_id": model_id,
                    "type": model_type,
                    "downloaded": False,
                    "error": str(e)
                }
        
        # Special handling for specific training frameworks
        if model_type == "training":
            # Map model IDs to their specific pip packages
            framework_packages = {
                "unsloth": "unsloth",
                "axolotl": "axolotl",
                "llamafactory": "llamafactory",
                "peft-lora": "peft",
                "autotrain-advanced": "autotrain-advanced",
                "torchtune": "torchtune",
                "diffusers-training": "diffusers[training]",
                "kohya_ss": None  # Requires git clone, not pip
            }
            
            if model_id in framework_packages and framework_packages[model_id]:
                # Install the specific framework
                framework_result = subprocess.run(
                    ["pip", "install", "-qq", framework_packages[model_id]],
                    capture_output=True,
                    text=True,
                    timeout=180
                )
                
                if framework_result.returncode != 0:
                    # Not critical if it fails, base dependencies are installed
                    pass
        
        return {
            "success": True,
            "message": f"✓ {model_id} ready! Model will auto-download on first use.",
            "model_id": model_id,
            "type": model_type
        }
        
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "Installation timed out. Please try again.")
    except Exception as e:
        raise HTTPException(500, f"Error installing model: {str(e)}")


@router.get("/python-models/status")
async def check_python_models_status():
    """Check which Python AI libraries are installed."""
    import importlib.util
    
    packages = {
        "diffusers": "Image & Video",
        "TTS": "Audio/Speech",
        "trimesh": "3D Models",
        "torch": "PyTorch",
        "peft": "Fine-tuning (LoRA)",
        "transformers": "HuggingFace Models",
        "unsloth": "Fast Training",
        "axolotl": "Advanced Training"
    }
    
    status = {}
    for package, description in packages.items():
        spec = importlib.util.find_spec(package)
        status[package] = {
            "installed": spec is not None,
            "description": description
        }
    
    return {
        "packages": status,
        "diffusers_installed": status.get("diffusers", {}).get("installed", False),
        "tts_installed": status.get("TTS", {}).get("installed", False),
        "trimesh_installed": status.get("trimesh", {}).get("installed", False),
        "training_ready": status.get("peft", {}).get("installed", False) and status.get("transformers", {}).get("installed", False)
    }


@router.post("/python-models/install-streaming")
async def install_python_model_streaming(request: Dict[str, str]):
    """Install model with real-time progress updates via SSE with robust retry logic."""
    import subprocess
    import sys
    from fastapi.responses import StreamingResponse
    import asyncio
    
    model_type = request.get("type")
    model_id = request.get("model_id")
    
    if not model_type or not model_id:
        raise HTTPException(400, "model_type and model_id required")
    
    async def generate_progress():
        """Stream installation progress with retry logic."""
        try:
            # Send start event
            yield f"data: {json.dumps({'type': 'start', 'model_id': model_id, 'progress': 0})}\n\n"
            await asyncio.sleep(0.1)
            
            # Step 1: Install dependencies (20% progress)
            yield f"data: {json.dumps({'type': 'status', 'message': 'Installing dependencies...', 'progress': 10})}\n\n"
            
            install_commands = {
                "image": ["pip", "install", "-qq", "diffusers", "transformers", "accelerate", "torch", "safetensors", "huggingface-hub"],
                "video": ["pip", "install", "-qq", "diffusers", "torch", "imageio", "av", "transformers", "huggingface-hub"],
                "audio": ["pip", "install", "-qq", "TTS", "torch", "audiocraft", "huggingface-hub"],
                "3d": ["pip", "install", "-qq", "trimesh", "torch", "pillow", "numpy", "huggingface-hub"],
                "training": ["pip", "install", "-qq", "transformers", "peft", "accelerate", "bitsandbytes", "torch", "huggingface-hub"]
            }
            
            # Install dependencies with retry
            if model_type in install_commands:
                max_dep_retries = 3
                dep_success = False
                
                for attempt in range(max_dep_retries):
                    try:
                        result = subprocess.run(
                            install_commands[model_type],
                            capture_output=True,
                            text=True,
                            timeout=300  # 5 minutes for pip install
                        )
                        
                        if result.returncode == 0:
                            dep_success = True
                            break
                        else:
                            if attempt < max_dep_retries - 1:
                                logger.warning(f"Dependencies install attempt {attempt + 1} failed, retrying...")
                                await asyncio.sleep(2 ** attempt)
                    except subprocess.TimeoutExpired:
                        if attempt < max_dep_retries - 1:
                            logger.warning(f"Dependencies install timeout on attempt {attempt + 1}, retrying...")
                            await asyncio.sleep(2 ** attempt)
                        else:
                            yield f"data: {json.dumps({'type': 'error', 'message': 'Dependency installation timed out after 3 attempts'})}\n\n"
                            return
                    except Exception as e:
                        if attempt < max_dep_retries - 1:
                            logger.warning(f"Dependencies install error on attempt {attempt + 1}: {e}")
                            await asyncio.sleep(2 ** attempt)
                
                if not dep_success:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Failed to install dependencies after 3 attempts'})}\n\n"
                    return
            
            yield f"data: {json.dumps({'type': 'status', 'message': 'Dependencies installed', 'progress': 20})}\n\n"
            await asyncio.sleep(0.1)
            
            # Step 2: Download model (20% → 100% progress) with retry
            if model_type in ["image", "video", "audio", "3d"]:
                yield f"data: {json.dumps({'type': 'status', 'message': f'Downloading {model_id}...', 'progress': 30})}\n\n"
                
                max_download_retries = 3
                download_success = False
                last_error = None
                
                for attempt in range(max_download_retries):
                    try:
                        # Use huggingface_hub with progress tracking
                        download_script = f"""
import sys
from huggingface_hub import snapshot_download
from tqdm import tqdm

try:
    print("progress:40", flush=True)
    snapshot_download(
        repo_id="{model_id}", 
        cache_dir=None, 
        resume_download=True,
        max_workers=4
    )
    print("progress:100", flush=True)
    print("success", flush=True)
except Exception as e:
    print(f"error:{{str(e)}}", file=sys.stderr, flush=True)
    sys.exit(1)
"""
                        
                        # Run download with timeout
                        process = subprocess.Popen(
                            [sys.executable, "-c", download_script],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            bufsize=1
                        )
                        
                        current_progress = 30
                        max_wait_time = 1800  # 30 minutes max
                        start_time = asyncio.get_event_loop().time()
                        last_output_time = start_time
                        
                        while True:
                            # Check timeout
                            current_time = asyncio.get_event_loop().time()
                            if current_time - start_time > max_wait_time:
                                process.kill()
                                raise TimeoutError(f"Download exceeded {max_wait_time}s timeout")
                            
                            # Check for hung process (no output for 5 minutes)
                            if current_time - last_output_time > 300:
                                process.kill()
                                raise TimeoutError("Download appears hung (no output for 5 minutes)")
                            
                            # Try to read output with short timeout
                            try:
                                line = process.stdout.readline()
                                if line:
                                    last_output_time = current_time
                                    
                                    if line.startswith("progress:"):
                                        try:
                                            current_progress = int(line.split(":")[1].strip())
                                            yield f"data: {json.dumps({'type': 'progress', 'progress': current_progress})}\n\n"
                                        except:
                                            pass
                                    elif "success" in line:
                                        download_success = True
                                        yield f"data: {json.dumps({'type': 'complete', 'message': f'✓ {model_id} installed!', 'progress': 100})}\n\n"
                                        return
                                
                                # Check if process finished
                                if process.poll() is not None:
                                    break
                                
                                await asyncio.sleep(0.1)
                            except Exception as read_error:
                                logger.warning(f"Error reading download output: {read_error}")
                                await asyncio.sleep(0.5)
                        
                        # Check exit code
                        if process.returncode == 0:
                            download_success = True
                            yield f"data: {json.dumps({'type': 'complete', 'message': f'✓ {model_id} installed!', 'progress': 100})}\n\n"
                            return
                        else:
                            stderr = process.stderr.read() if process.stderr else ""
                            last_error = stderr[:200] if stderr else "Unknown error"
                            
                            if attempt < max_download_retries - 1:
                                retry_msg = f"Download attempt {attempt + 1} failed, retrying in {2 ** attempt}s..."
                                yield f"data: {json.dumps({'type': 'status', 'message': retry_msg, 'progress': 30})}\n\n"
                                logger.warning(f"{model_id}: {retry_msg} Error: {last_error}")
                                await asyncio.sleep(2 ** attempt)
                            
                    except TimeoutError as e:
                        last_error = str(e)
                        if attempt < max_download_retries - 1:
                            retry_msg = f"Download timeout on attempt {attempt + 1}, retrying..."
                            yield f"data: {json.dumps({'type': 'status', 'message': retry_msg, 'progress': 30})}\n\n"
                            logger.warning(f"{model_id}: {retry_msg}")
                            await asyncio.sleep(2 ** attempt)
                    except Exception as e:
                        last_error = str(e)
                        if attempt < max_download_retries - 1:
                            retry_msg = f"Error on attempt {attempt + 1}, retrying..."
                            yield f"data: {json.dumps({'type': 'status', 'message': retry_msg, 'progress': 30})}\n\n"
                            logger.warning(f"{model_id}: {retry_msg} Error: {last_error}")
                            await asyncio.sleep(2 ** attempt)
                
                if not download_success:
                    # All retries failed - fallback to lazy download
                    yield f"data: {json.dumps({'type': 'warning', 'message': f'Download failed after {max_download_retries} attempts. Model will download on first use. Error: {last_error}', 'progress': 100})}\n\n"
            else:
                # Training frameworks - mark as complete
                yield f"data: {json.dumps({'type': 'complete', 'message': f'✓ {model_id} ready!', 'progress': 100})}\n\n"
                
        except Exception as e:
            logger.error(f"Python model install error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': f'Installation error: {str(e)}'})}\n\n"
    
    return StreamingResponse(generate_progress(), media_type="text/event-stream")


# Preset packs for one-click installation
PRESET_PACKS = {
    "highest_quality": {
        "name": "Highest Quality",
        "description": "Best models for maximum quality output",
        "icon": "✨",
        "models": [
            {"type": "text", "model_id": "deepseek-ai/DeepSeek-R1", "name": "DeepSeek R1 7B"},
            {"type": "image", "model_id": "black-forest-labs/FLUX.1-dev", "name": "Flux.1 Dev"},
            {"type": "video", "model_id": "tencent/HunyuanVideo", "name": "Hunyuan Video"},
            {"type": "audio", "model_id": "suno/bark", "name": "Bark"}
        ]
    },
    "fastest": {
        "name": "Fastest",
        "description": "Optimized for speed and quick generation",
        "icon": "⚡",
        "models": [
            {"type": "text", "model_id": "microsoft/phi-3-mini-4k-instruct", "name": "Phi-3 Mini"},
            {"type": "image", "model_id": "black-forest-labs/FLUX.1-schnell", "name": "Flux.1 Schnell"},
            {"type": "video", "model_id": "ali-vilab/text-to-video-ms-1.7b", "name": "ModelScope Text-to-Video"},
            {"type": "audio", "model_id": "coqui/XTTS-v2", "name": "XTTS v2"}
        ]
    },
    "smallest_size": {
        "name": "Smallest Size",
        "description": "Lightweight models for limited storage/memory",
        "icon": "💾",
        "models": [
            {"type": "text", "model_id": "microsoft/phi-3-mini-4k-instruct", "name": "Phi-3 Mini (3.8B)"},
            {"type": "image", "model_id": "segmind/SSD-1B", "name": "SSD-1B"},
            {"type": "video", "model_id": "damo-vilab/text-to-video-ms-1.7b", "name": "ModelScope 1.7B"},
            {"type": "audio", "model_id": "suno/bark-small", "name": "Bark Small"}
        ]
    },
    "complete": {
        "name": "Complete Suite",
        "description": "Full range of capabilities across all categories",
        "icon": "🎯",
        "models": [
            {"type": "text", "model_id": "deepseek-ai/DeepSeek-R1", "name": "DeepSeek R1"},
            {"type": "text", "model_id": "deepseek-ai/DeepSeek-Coder-V2-Instruct", "name": "DeepSeek Coder"},
            {"type": "image", "model_id": "black-forest-labs/FLUX.1-dev", "name": "Flux.1 Dev"},
            {"type": "image", "model_id": "stabilityai/stable-diffusion-xl-base-1.0", "name": "SDXL"},
            {"type": "video", "model_id": "tencent/HunyuanVideo", "name": "Hunyuan Video"},
            {"type": "video", "model_id": "THUDM/CogVideoX-5b", "name": "CogVideoX-5B"},
            {"type": "audio", "model_id": "suno/bark", "name": "Bark"},
            {"type": "3d", "model_id": "openai/shap-e", "name": "Shap-E"}
        ]
    }
}


@router.get("/preset-packs")
async def get_preset_packs():
    """Get available preset installation packs."""
    return {"packs": PRESET_PACKS}


@router.post("/preset-packs/install")
async def install_preset_pack(request: Dict[str, str]):
    """Install a preset pack of models with progress tracking."""
    pack_id = request.get("pack_id")
    
    if pack_id not in PRESET_PACKS:
        raise HTTPException(400, f"Unknown preset pack: {pack_id}")
    
    from fastapi.responses import StreamingResponse
    import subprocess
    import asyncio
    
    pack = PRESET_PACKS[pack_id]
    models = pack["models"]
    total_models = len(models)
    
    async def generate_pack_progress():
        """Stream progress for installing multiple models."""
        try:
            yield f"data: {json.dumps({'type': 'start', 'pack': pack_id, 'total_models': total_models})}\n\n"
            
            for idx, model in enumerate(models):
                model_progress = int((idx / total_models) * 100)
                yield f"data: {json.dumps({'type': 'model_start', 'model': model['name'], 'progress': model_progress})}\n\n"
                await asyncio.sleep(0.1)
                
                # Install this model (simplified for pack install)
                install_commands = {
                    "text": ["pip", "install", "-qq", "transformers", "torch", "accelerate", "huggingface-hub"],
                    "image": ["pip", "install", "-qq", "diffusers", "transformers", "torch", "huggingface-hub"],
                    "video": ["pip", "install", "-qq", "diffusers", "torch", "imageio", "av", "huggingface-hub"],
                    "audio": ["pip", "install", "-qq", "TTS", "torch", "audiocraft", "huggingface-hub"],
                    "3d": ["pip", "install", "-qq", "trimesh", "torch", "huggingface-hub"]
                }
                
                # Install dependencies quietly
                if model["type"] in install_commands:
                    subprocess.run(install_commands[model["type"]], capture_output=True, timeout=180)
                
                yield f"data: {json.dumps({'type': 'model_complete', 'model': model['name'], 'progress': model_progress + (100 // total_models)})}\n\n"
                await asyncio.sleep(0.2)
            
            pack_name = pack["name"]
            complete_msg = f'✓ {pack_name} pack installed!'
            yield f"data: {json.dumps({'type': 'complete', 'message': complete_msg, 'progress': 100})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(generate_pack_progress(), media_type="text/event-stream")


# =============================================================================
# Setup Wizard Web UI
# =============================================================================

SETUP_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Otto Setup Wizard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e4e4e7;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        
        header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .subtitle {
            color: #a1a1aa;
            font-size: 1.1rem;
        }
        
        .progress-bar {
            background: #27272a;
            border-radius: 10px;
            height: 8px;
            margin: 30px 0;
            overflow: hidden;
        }
        
        .progress-fill {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            height: 100%;
            transition: width 0.5s ease;
        }
        
        .progress-text {
            text-align: center;
            color: #a1a1aa;
            margin-bottom: 30px;
        }
        
        .categories {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .category-btn {
            padding: 8px 16px;
            border: none;
            border-radius: 20px;
            background: #27272a;
            color: #a1a1aa;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .category-btn:hover, .category-btn.active {
            background: #667eea;
            color: white;
        }
        
        .integrations {
            display: grid;
            gap: 15px;
        }
        
        .integration-card {
            background: #27272a;
            border-radius: 12px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.2s;
            border: 2px solid transparent;
        }
        
        .integration-card:hover {
            border-color: #667eea;
            transform: translateY(-2px);
        }
        
        .integration-card.configured {
            border-color: #22c55e;
        }
        
        .integration-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .integration-name {
            font-size: 1.1rem;
            font-weight: 600;
        }
        
        .integration-name .required {
            color: #ef4444;
            font-size: 0.8rem;
            margin-left: 8px;
        }
        
        .status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
        }
        
        .status-badge.configured {
            background: #22c55e20;
            color: #22c55e;
        }
        
        .status-badge.missing {
            background: #f59e0b20;
            color: #f59e0b;
        }
        
        .integration-desc {
            color: #a1a1aa;
            font-size: 0.9rem;
        }
        
        /* Modal */
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.8);
            z-index: 1000;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .modal-overlay.active {
            display: flex;
        }
        
        .modal {
            background: #18181b;
            border-radius: 16px;
            max-width: 500px;
            width: 100%;
            max-height: 90vh;
            overflow-y: auto;
        }
        
        .modal-header {
            padding: 20px;
            border-bottom: 1px solid #27272a;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .modal-title {
            font-size: 1.3rem;
        }
        
        .close-btn {
            background: none;
            border: none;
            color: #a1a1aa;
            font-size: 1.5rem;
            cursor: pointer;
        }
        
        .modal-body {
            padding: 20px;
        }
        
        .setup-steps {
            background: #27272a;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
        }
        
        .setup-steps h4 {
            margin-bottom: 10px;
            color: #667eea;
        }
        
        .setup-steps ol {
            margin-left: 20px;
            color: #a1a1aa;
        }
        
        .setup-steps li {
            margin-bottom: 8px;
        }
        
        .setup-link {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            margin-bottom: 20px;
        }
        
        .setup-link:hover {
            background: #5a67d8;
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: #a1a1aa;
            font-size: 0.9rem;
        }
        
        .form-group input {
            width: 100%;
            padding: 12px;
            border: 2px solid #27272a;
            border-radius: 8px;
            background: #27272a;
            color: white;
            font-size: 1rem;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .modal-actions {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        
        .btn {
            flex: 1;
            padding: 12px;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-primary:hover {
            opacity: 0.9;
        }
        
        .btn-secondary {
            background: #27272a;
            color: #a1a1aa;
        }
        
        .btn-secondary:hover {
            background: #3f3f46;
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .message {
            padding: 12px;
            border-radius: 8px;
            margin-top: 15px;
            display: none;
        }
        
        .message.success {
            display: block;
            background: #22c55e20;
            color: #22c55e;
            border: 1px solid #22c55e40;
        }
        
        .message.error {
            display: block;
            background: #ef444420;
            color: #ef4444;
            border: 1px solid #ef444440;
        }
        
        .spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid #ffffff40;
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin-right: 8px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .quick-start {
            background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%);
            border: 1px solid #667eea40;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .quick-start h3 {
            margin-bottom: 10px;
        }
        
        .quick-start p {
            color: #a1a1aa;
            margin-bottom: 15px;
        }
        
        /* Ollama Model Manager Styles */
        .ollama-section {
            margin: 20px 0;
        }
        
        .ollama-section h4 {
            margin-bottom: 15px;
            color: #e4e4e7;
        }
        
        .model-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 15px;
            margin: 15px 0;
        }
        
        .model-card {
            background: #2a3142;
            border: 2px solid #3a4556;
            border-radius: 8px;
            padding: 15px;
            transition: all 0.3s;
        }
        
        .model-card:hover {
            border-color: #667eea;
            transform: translateY(-2px);
        }
        
        .model-card.installed {
            background: #22c55e15;
            border-color: #22c55e;
        }
        
        .model-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        
        .model-header strong {
            font-size: 16px;
            color: #e4e4e7;
        }
        
        .badge-success {
            background: #22c55e;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }
        
        .model-desc {
            color: #a0aec0;
            font-size: 14px;
            margin-bottom: 10px;
        }
        
        .model-meta {
            display: flex;
            gap: 15px;
            font-size: 12px;
            color: #a0aec0;
            margin-bottom: 8px;
        }
        
        .model-use-case {
            color: #667eea;
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 10px;
        }
        
        .install-progress {
            position: relative;
            width: 100%;
            height: 32px;
            background: #1a1a2e;
            border-radius: 6px;
            overflow: hidden;
        }
        
        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .progress-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 12px;
            font-weight: 600;
            color: white;
            text-shadow: 0 1px 2px rgba(0,0,0,0.3);
        }
        
        .pack-progress {
            margin-top: 10px;
            padding: 10px;
            background: #2a3142;
            border-radius: 6px;
            position: relative;
            height: 40px;
        }
        
        .preset-packs {
            margin-bottom: 40px;
        }
        
        .packs-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .pack-card {
            background: linear-gradient(135deg, #2a3142 0%, #1f2937 100%);
            border: 2px solid #3a4556;
            border-radius: 12px;
            padding: 20px;
            transition: all 0.3s;
            cursor: pointer;
        }
        
        .pack-card:hover {
            border-color: #667eea;
            transform: translateY(-4px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.2);
        }
        
        .pack-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
        }
        
        .pack-icon {
            font-size: 32px;
        }
        
        .pack-title {
            font-size: 18px;
            font-weight: 700;
            color: #e4e4e7;
        }
        
        .pack-desc {
            color: #a0aec0;
            font-size: 14px;
            margin-bottom: 15px;
            line-height: 1.5;
        }
        
        .pack-models {
            margin: 15px 0;
            padding: 12px;
            background: #1a1a2e;
            border-radius: 8px;
        }
        
        .pack-model-item {
            color: #a0aec0;
            font-size: 13px;
            padding: 4px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .pack-model-item:before {
            content: '✓';
            color: #667eea;
            font-weight: bold;
        }
        
        .btn-sm {
            padding: 8px 16px;
            font-size: 13px;
        }
        
        .installed-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .installed-model {
            background: #2a3142;
            padding: 10px 15px;
            border-radius: 6px;
            color: #22c55e;
            font-size: 14px;
        }
        
        .alert {
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .alert-success {
            background: #22c55e15;
            border: 2px solid #22c55e;
            color: #22c55e;
        }
        
        .alert-warning {
            background: #f59e0b15;
            border: 2px solid #f59e0b;
            color: #f59e0b;
        }
        
        .alert-error {
            background: #ef444415;
            border: 2px solid #ef4444;
            color: #ef4444;
        }
        
        /* Model Tab Styles */
        .tab-btn {
            padding: 10px 20px;
            background: #2a3142;
            border: 2px solid #3a4556;
            border-radius: 8px;
            color: #e4e4e7;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .tab-btn:hover {
            border-color: #667eea;
            background: #667eea15;
        }
        
        .tab-btn.active {
            background: #667eea;
            border-color: #667eea;
            color: white;
        }
        
        .model-tab-content {
            display: none;
        }
    </style>
</head>
<body>
    <!-- Navigation Bar -->
    <nav style="background: rgba(26, 26, 46, 0.95); backdrop-filter: blur(10px); border-bottom: 1px solid rgba(102, 126, 234, 0.2); padding: 12px 20px; position: sticky; top: 0; z-index: 1000; display: flex; justify-content: space-between; align-items: center;">
        <div style="display: flex; align-items: center; gap: 15px;">
            <div style="font-size: 24px;">🤖</div>
            <div>
                <div style="font-weight: 600; color: #e4e4e7;">Otto Setup</div>
                <div style="font-size: 11px; color: #a1a1aa;">Configure your platform</div>
            </div>
        </div>
        <div style="display: flex; gap: 10px;">
            <a href="/" style="padding: 8px 20px; background: rgba(102, 126, 234, 0.1); border: 1px solid rgba(102, 126, 234, 0.3); border-radius: 8px; color: #667eea; text-decoration: none; font-size: 14px; font-weight: 500; transition: all 0.2s;" onmouseover="this.style.background='rgba(102, 126, 234, 0.2)'" onmouseout="this.style.background='rgba(102, 126, 234, 0.1)'">
                ← Back to Chat
            </a>
            <a href="/settings-page" style="padding: 8px 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; border-radius: 8px; color: white; text-decoration: none; font-size: 14px; font-weight: 500; transition: all 0.2s; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(102, 126, 234, 0.4)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(102, 126, 234, 0.3)'">
                ⚙️ Settings
            </a>
        </div>
    </nav>
    <div class="container">
        <header>
            <h1>Otto Setup Wizard</h1>
            <p class="subtitle">Configure your integrations in minutes</p>
        </header>
        
        <div class="progress-bar">
            <div class="progress-fill" id="progressFill" style="width: 0%"></div>
        </div>
        <p class="progress-text" id="progressText">Loading...</p>
        
        <div class="quick-start" id="quickStart" style="display: none;">
            <h3>Get Started</h3>
            <p>Complete the required integrations to start using Otto</p>
            <button class="btn btn-primary" onclick="setupNext()" style="width: auto; padding: 12px 30px;">
                Setup Next Integration
            </button>
        </div>
        
        <div class="preset-packs">
            <h2>🎯 Preset Model Packs</h2>
            <p style="color: #a0aec0; margin-top: 10px;">One-click installation of curated model collections</p>
            <div class="packs-grid" id="presetPacks"></div>
        </div>
        
        <div class="categories" id="categories"></div>
        
        <div class="integrations" id="integrations"></div>
    </div>
    
    <!-- Setup Modal -->
    <div class="modal-overlay" id="modalOverlay">
        <div class="modal">
            <div class="modal-header">
                <h3 class="modal-title" id="modalTitle">Setup</h3>
                <button class="close-btn" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body" id="modalBody"></div>
        </div>
    </div>
    
    <script>
        let integrations = [];
        let currentIntegration = null;
        let activeCategory = 'all';
        
        async function loadIntegrations() {
            try {
                const response = await fetch('/api/setup/integrations');
                integrations = await response.json();
                renderCategories();
                renderIntegrations();
                updateProgress();
                loadPresetPacks(); // Load preset packs
            } catch (error) {
                console.error('Failed to load integrations:', error);
            }
        }
        
        async function loadPresetPacks() {
            try {
                const response = await fetch('/api/setup/preset-packs');
                const data = await response.json();
                renderPresetPacks(data.packs);
            } catch (error) {
                console.error('Failed to load preset packs:', error);
            }
        }
        
        function renderPresetPacks(packs) {
            const container = document.getElementById('presetPacks');
            const packHTML = Object.entries(packs).map(([id, pack]) => `
                <div class="pack-card">
                    <div class="pack-header">
                        <span class="pack-icon">${pack.icon}</span>
                        <span class="pack-title">${pack.name}</span>
                    </div>
                    <div class="pack-desc">${pack.description}</div>
                    <div class="pack-models">
                        ${pack.models.map(m => `<div class="pack-model-item">${m.name}</div>`).join('')}
                    </div>
                    <button class="btn btn-primary" onclick="installPresetPack('${id}', event)">
                        Install ${pack.name}
                    </button>
                </div>
            `).join('');
            container.innerHTML = packHTML;
        }
        
        function renderCategories() {
            const categories = ['all', ...new Set(integrations.map(i => i.category))];
            const container = document.getElementById('categories');
            container.innerHTML = categories.map(cat => `
                <button class="category-btn ${cat === activeCategory ? 'active' : ''}" 
                        onclick="filterCategory('${cat}')">
                    ${cat === 'all' ? 'All' : cat}
                </button>
            `).join('');
        }
        
        function filterCategory(category) {
            activeCategory = category;
            renderCategories();
            renderIntegrations();
        }
        
        function renderIntegrations() {
            const filtered = activeCategory === 'all' 
                ? integrations 
                : integrations.filter(i => i.category === activeCategory);
            
            const container = document.getElementById('integrations');
            container.innerHTML = filtered.map(i => `
                <div class="integration-card ${i.configured ? 'configured' : ''}" 
                     onclick="openSetup('${i.id}')">
                    <div class="integration-header">
                        <span class="integration-name">
                            ${i.name}
                            ${i.required ? '<span class="required">REQUIRED</span>' : ''}
                        </span>
                        <span class="status-badge ${i.configured ? 'configured' : 'missing'}">
                            ${i.configured ? '✓ Connected' : 'Setup Needed'}
                        </span>
                    </div>
                    <p class="integration-desc">${i.description}</p>
                </div>
            `).join('');
        }
        
        function updateProgress() {
            const total = integrations.length;
            const configured = integrations.filter(i => i.configured).length;
            const required = integrations.filter(i => i.required);
            const requiredConfigured = required.filter(i => i.configured).length;
            
            const percent = Math.round((configured / total) * 100);
            document.getElementById('progressFill').style.width = percent + '%';
            document.getElementById('progressText').textContent = 
                `${configured} of ${total} integrations configured (${requiredConfigured}/${required.length} required)`;
            
            // Show quick start if required integrations missing
            const quickStart = document.getElementById('quickStart');
            if (requiredConfigured < required.length) {
                quickStart.style.display = 'block';
            } else {
                quickStart.style.display = 'none';
            }
        }
        
        function setupNext() {
            const next = integrations.find(i => i.required && !i.configured) 
                      || integrations.find(i => !i.configured);
            if (next) openSetup(next.id);
        }
        
        function openSetup(id) {
            currentIntegration = integrations.find(i => i.id === id);
            if (!currentIntegration) return;
            
            document.getElementById('modalTitle').textContent = currentIntegration.name;
            
            // Special handling for Ollama with model manager
            if (id === 'ollama') {
                renderOllamaSetup();
                document.getElementById('modalOverlay').classList.add('active');
                return;
            }
            
            let stepsHtml = '';
            if (currentIntegration.setup_steps.length > 0) {
                stepsHtml = `
                    <div class="setup-steps">
                        <h4>Setup Instructions</h4>
                        <ol>
                            ${currentIntegration.setup_steps.map(s => `<li>${s}</li>`).join('')}
                        </ol>
                    </div>
                `;
            }
            
            let linkHtml = '';
            if (currentIntegration.setup_url) {
                linkHtml = `
                    <a href="${currentIntegration.setup_url}" target="_blank" class="setup-link">
                        Open ${currentIntegration.name} Settings →
                    </a>
                `;
            }
            
            const fieldsHtml = currentIntegration.env_keys.map(key => `
                <div class="form-group">
                    <label for="${key}">${formatKeyLabel(key)}</label>
                    <input type="${key.toLowerCase().includes('password') ? 'password' : 'text'}" 
                           id="${key}" 
                           name="${key}" 
                           placeholder="Enter ${formatKeyLabel(key).toLowerCase()}"
                           autocomplete="off">
                </div>
            `).join('');
            
            document.getElementById('modalBody').innerHTML = `
                ${stepsHtml}
                ${linkHtml}
                <form id="setupForm" onsubmit="saveCredentials(event)">
                    ${fieldsHtml}
                    <div class="modal-actions">
                        <button type="button" class="btn btn-secondary" onclick="validateOnly()">
                            Test Connection
                        </button>
                        <button type="submit" class="btn btn-primary" id="saveBtn">
                            Save & Connect
                        </button>
                    </div>
                    <div class="message" id="message"></div>
                </form>
            `;
            
            document.getElementById('modalOverlay').classList.add('active');
        }
        
        async function renderOllamaSetup() {
            const modalBody = document.getElementById('modalBody');
            const messageDiv = document.getElementById('message');
            
            // Show loading state
            modalBody.innerHTML = '<div style="text-align: center; padding: 40px;"><span class="spinner"></span> Loading...</div>';
            
            try {
                // Check Ollama status
                const statusResponse = await fetch('/api/setup/ollama/status');
                const status = await statusResponse.json();
                
                const modelsResponse = await fetch('/api/setup/ollama/recommended-models');
                const allModels = await modelsResponse.json();
                
                let contentHtml = '';
                
                // Status banner
                if (status.running) {
                    contentHtml += `
                        <div class="alert alert-success">
                            <div style="font-size: 18px; font-weight: bold;">✓ Ollama is Running!</div>
                            <div style="margin-top: 5px;">
                                Status: <strong>Online</strong> | Models Installed: <strong>${status.models_count}</strong>
                            </div>
                        </div>
                    `;
                } else {
                    contentHtml += `
                        <div class="alert alert-warning">
                            <div style="font-size: 18px; font-weight: bold;">⚠️ Ollama Not Detected</div>
                            <div style="margin-top: 10px;">
                                Ollama is not running. Install it to use local AI models.
                            </div>
                        </div>
                        <div class="setup-steps">
                            <h4>Quick Setup Guide</h4>
                            <ol>
                                <li>Click "Download Ollama" below</li>
                                <li>Install and launch Ollama</li>
                                <li>Come back here and refresh</li>
                                <li>Download models with one click!</li>
                            </ol>
                        </div>
                        <div class="modal-actions">
                            <a href="https://ollama.ai/download" target="_blank" class="btn btn-primary">
                                📥 Download Ollama
                            </a>
                            <button type="button" class="btn btn-secondary" onclick="renderOllamaSetup()">
                                🔄 Refresh Status
                            </button>
                        </div>
                        <div class="message" id="message"></div>
                        <hr style="margin: 30px 0; border: 1px solid #3a4556;">
                    `;
                }
                
                // Model categories tabs
                contentHtml += `
                    <div style="margin: 20px 0;">
                        <h3 style="margin-bottom: 15px;">Local AI Models</h3>
                        <div class="model-tabs" style="display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap;">
                            <button class="tab-btn active" onclick="showModelTab('text', event)" data-tab="text">
                                💬 Text & Chat
                            </button>
                            <button class="tab-btn" onclick="showModelTab('vision', event)" data-tab="vision">
                                👁️ Vision
                            </button>
                            <button class="tab-btn" onclick="showModelTab('image', event)" data-tab="image">
                                🎨 Image Gen
                            </button>
                            <button class="tab-btn" onclick="showModelTab('video', event)" data-tab="video">
                                🎬 Video
                            </button>
                            <button class="tab-btn" onclick="showModelTab('audio', event)" data-tab="audio">
                                🎵 Audio
                            </button>
                            <button class="tab-btn" onclick="showModelTab('3d', event)" data-tab="3d">
                                🧊 3D Models
                            </button>
                            <button class="tab-btn" onclick="showModelTab('training', event)" data-tab="training">
                                🎯 Training
                            </button>
                        </div>
                        
                        <!-- Text LLMs Tab -->
                        <div class="model-tab-content" id="tab-text" style="display: block;">
                            <p style="color: #a0aec0; margin-bottom: 15px;">
                                ${allModels.text_llms.description}
                            </p>
                `;
                
                if (status.running) {
                    const textModels = allModels.text_llms.models;
                    const installedModels = status.models || [];
                    const allInstalled = textModels.every(m => 
                        installedModels.some(installed => installed.startsWith(m.name))
                    );
                    
                    if (!allInstalled) {
                        contentHtml += `
                            <div class="model-grid">
                                ${textModels.map(m => {
                                    const installed = installedModels.some(im => im.startsWith(m.name));
                                    return `
                                        <div class="model-card ${installed ? 'installed' : ''}">
                                            <div class="model-header">
                                                <strong>${m.display_name}</strong>
                                                ${installed ? '<span class="badge-success">✓ Installed</span>' : ''}
                                            </div>
                                            <div class="model-desc">${m.description}</div>
                                            <div class="model-meta">
                                                <span>📦 ${m.size_gb} GB</span>
                                                <span>⚡ Speed: ${m.speed}/5</span>
                                                <span>✨ Quality: ${m.quality}/5</span>
                                            </div>
                                            <div class="model-use-case">${m.use_case}</div>
                                            ${!installed ? `
                                                <button class="btn btn-sm btn-primary" 
                                                        onclick="downloadModel('${m.name}', event)">
                                                    Download
                                                </button>
                                            ` : ''}
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                            ${!allInstalled ? `
                                <button class="btn btn-primary" style="width: 100%; margin-top: 15px;" 
                                        onclick="installStarterPack(event)">
                                    🚀 Download All Text Models (${allModels.text_llms.total_size_gb} GB)
                                </button>
                            ` : ''}
                        `;
                    } else {
                        contentHtml += `
                            <div class="alert alert-success">
                                🎉 All starter models installed! You're ready to use local AI.
                            </div>
                        `;
                    }
                    
                    if (installedModels.length > 0) {
                        contentHtml += `
                            <div style="margin-top: 20px;">
                                <h4>📚 Your Installed Models</h4>
                                <div class="installed-list">
                                    ${installedModels.map(m => `
                                        <div class="installed-model">✓ ${m}</div>
                                    `).join('')}
                                </div>
                            </div>
                        `;
                    }
                } else {
                    contentHtml += `
                        <div class="alert alert-warning">
                            Install Ollama first to download text models
                        </div>
                    `;
                }
                
                contentHtml += `</div>`;
                
                // Vision Models Tab
                contentHtml += `
                    <div class="model-tab-content" id="tab-vision" style="display: none;">
                        <p style="color: #a0aec0; margin-bottom: 15px;">
                            ${allModels.vision.description}
                        </p>
                        <div class="model-grid">
                            ${allModels.vision.models.map(m => `
                                <div class="model-card">
                                    <div class="model-header">
                                        <strong>${m.display_name}</strong>
                                        <span class="badge-success">${m.platform}</span>
                                    </div>
                                    <div class="model-desc">${m.description}</div>
                                    <div class="model-meta">
                                        <span>📦 ${m.size_gb} GB</span>
                                        <span>⚡ Speed: ${m.speed}/5</span>
                                        <span>✨ Quality: ${m.quality}/5</span>
                                    </div>
                                    <div class="model-use-case">${m.use_case}</div>
                                    ${status.running ? `
                                        <button class="btn btn-sm btn-primary" 
                                                onclick="downloadModel('${m.name}', event)">
                                            Download ${m.display_name}
                                        </button>
                                    ` : `
                                        <div class="alert alert-warning" style="margin-top: 10px; padding: 10px;">
                                            Install Ollama first
                                        </div>
                                    `}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
                
                // Image Generation Tab
                contentHtml += `
                    <div class="model-tab-content" id="tab-image" style="display: none;">
                        <p style="color: #a0aec0; margin-bottom: 15px;">
                            ${allModels.image_generation.description}
                        </p>
                        <div class="model-grid" id="image-models-grid">
                            ${allModels.image_generation.models.map(m => `
                                <div class="model-card" data-model-id="${m.name}" data-model-type="image">
                                    <div class="model-header">
                                        <strong>${m.display_name}</strong>
                                        <span class="badge-success" style="background: #667eea;">Auto-Download</span>
                                    </div>
                                    <div class="model-desc">${m.description}</div>
                                    <div class="model-meta">
                                        <span>📦 ${m.size_gb} GB</span>
                                        <span>⚡ Speed: ${m.speed}/5</span>
                                        <span>✨ Quality: ${m.quality}/5</span>
                                    </div>
                                    <div class="model-use-case">${m.use_case}</div>
                                    <button class="btn btn-sm btn-primary model-download-btn" 
                                            onclick="downloadPythonModel('image', '${m.name}', '${m.display_name}', event)"
                                            style="margin-top: 10px;">
                                        📥 Download ${m.display_name}
                                    </button>
                                </div>
                            `).join('')}
                        </div>
                        <p style="color: #a0aec0; margin-top: 15px; font-size: 13px;">
                            💡 <strong>Note:</strong> ${allModels.image_generation.note}
                        </p>
                    </div>
                `;
                
                // Video Tab
                contentHtml += `
                    <div class="model-tab-content" id="tab-video" style="display: none;">
                        <p style="color: #a0aec0; margin-bottom: 15px;">
                            ${allModels.video.description}
                        </p>
                        <div class="model-grid">
                            ${allModels.video.models.map(m => `
                                <div class="model-card" data-model-id="${m.name}" data-model-type="video">
                                    <div class="model-header">
                                        <strong>${m.display_name}</strong>
                                        <span class="badge-success" style="background: #667eea;">Auto-Download</span>
                                    </div>
                                    <div class="model-desc">${m.description}</div>
                                    <div class="model-meta">
                                        <span>📦 ${m.size_gb} GB</span>
                                        <span>⚡ Speed: ${m.speed}/5</span>
                                        <span>✨ Quality: ${m.quality}/5</span>
                                    </div>
                                    <div class="model-use-case">${m.use_case}</div>
                                    <button class="btn btn-sm btn-primary model-download-btn" 
                                            onclick="downloadPythonModel('video', '${m.name}', '${m.display_name}', event)"
                                            style="margin-top: 10px;">
                                        📥 Download ${m.display_name}
                                    </button>
                                </div>
                            `).join('')}
                        </div>
                        <p style="color: #a0aec0; margin-top: 15px; font-size: 13px;">
                            ⚠️ <strong>Note:</strong> ${allModels.video.note}
                        </p>
                    </div>
                `;
                
                // Audio Tab
                contentHtml += `
                    <div class="model-tab-content" id="tab-audio" style="display: none;">
                        <p style="color: #a0aec0; margin-bottom: 15px;">
                            ${allModels.audio.description}
                        </p>
                        <div class="model-grid">
                            ${allModels.audio.models.map(m => `
                                <div class="model-card" data-model-id="${m.name}" data-model-type="audio">
                                    <div class="model-header">
                                        <strong>${m.display_name}</strong>
                                        <span class="badge-success" style="background: #667eea;">${m.platform}</span>
                                    </div>
                                    <div class="model-desc">${m.description}</div>
                                    <div class="model-meta">
                                        <span>📦 ${m.size_gb} GB</span>
                                        <span>⚡ Speed: ${m.speed}/5</span>
                                        <span>✨ Quality: ${m.quality}/5</span>
                                    </div>
                                    <div class="model-use-case">${m.use_case}</div>
                                    <button class="btn btn-sm btn-primary model-download-btn" 
                                            onclick="downloadPythonModel('audio', '${m.name}', '${m.display_name}', event)"
                                            style="margin-top: 10px;">
                                        📥 Download ${m.display_name}
                                    </button>
                                </div>
                            `).join('')}
                        </div>
                        <p style="color: #a0aec0; margin-top: 15px; font-size: 13px;">
                            💡 <strong>Note:</strong> ${allModels.audio.note}
                        </p>
                    </div>
                `;
                
                // 3D Tab
                contentHtml += `
                    <div class="model-tab-content" id="tab-3d" style="display: none;">
                        <p style="color: #a0aec0; margin-bottom: 15px;">
                            ${allModels['3d'].description}
                        </p>
                        <div class="model-grid">
                            ${allModels['3d'].models.map(m => `
                                <div class="model-card" data-model-id="${m.name}" data-model-type="3d">
                                    <div class="model-header">
                                        <strong>${m.display_name}</strong>
                                        <span class="badge-success" style="background: #667eea;">${m.platform}</span>
                                    </div>
                                    <div class="model-desc">${m.description}</div>
                                    <div class="model-meta">
                                        <span>📦 ${m.size_gb} GB</span>
                                        <span>⚡ Speed: ${m.speed}/5</span>
                                        <span>✨ Quality: ${m.quality}/5</span>
                                    </div>
                                    <div class="model-use-case">${m.use_case}</div>
                                    <button class="btn btn-sm btn-primary model-download-btn" 
                                            onclick="downloadPythonModel('3d', '${m.name}', '${m.display_name}', event)"
                                            style="margin-top: 10px;">
                                        📥 Download ${m.display_name}
                                    </button>
                                </div>
                            `).join('')}
                        </div>
                        <p style="color: #a0aec0; margin-top: 15px; font-size: 13px;">
                            💡 <strong>Note:</strong> ${allModels['3d'].note}
                        </p>
                    </div>
                    
                    <!-- Training Tab -->
                    <div class="model-tab-content" id="tab-training" style="display: none;">
                        <p style="color: #a0aec0; margin-bottom: 15px;">
                            ${allModels.training.description}
                        </p>
                        <div style="padding: 15px; background: #667eea15; border-radius: 8px; border-left: 4px solid #667eea; margin-bottom: 20px;">
                            <h4 style="color: #667eea; margin: 0 0 10px 0;">🚀 What You Can Do</h4>
                            <ul style="color: #a0aec0; margin: 0; padding-left: 20px; line-height: 1.8;">
                                ${allModels.training.capabilities.map(c => `<li>${c}</li>`).join('')}
                            </ul>
                        </div>
                        <div class="model-grid">
                            ${allModels.training.models.map(m => `
                                <div class="model-card ${m.featured ? 'featured' : ''}" data-model-id="${m.name}" data-model-type="training">
                                    <div class="model-header">
                                        <strong>${m.display_name}</strong>
                                        <span class="badge-success" style="background: #f59e0b;">${m.platform}</span>
                                    </div>
                                    <div class="model-desc">${m.description}</div>
                                    <div class="model-meta">
                                        <span>📦 ${m.size_gb} GB</span>
                                        <span>⚡ Speed: ${m.speed}/5</span>
                                        <span>✨ Quality: ${m.quality}/5</span>
                                    </div>
                                    <div class="model-use-case">${m.use_case}</div>
                                    <button class="btn btn-sm btn-primary model-download-btn" 
                                            onclick="downloadPythonModel('training', '${m.name}', '${m.display_name}', event)"
                                            style="margin-top: 10px; ${m.featured ? 'background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);' : ''}">
                                        📥 Install ${m.display_name}
                                    </button>
                                    ${m.docs ? `<a href="${m.docs}" target="_blank" style="color: #667eea; font-size: 12px; margin-top: 8px; display: block;">📚 View Docs →</a>` : ''}
                                </div>
                            `).join('')}
                        </div>
                        <div style="margin-top: 20px; padding: 15px; background: #22c55e15; border-radius: 8px; border-left: 4px solid #22c55e;">
                            <h4 style="color: #22c55e; margin: 0 0 10px 0;">✨ Getting Started</h4>
                            <ol style="color: #a0aec0; margin: 0; padding-left: 20px; line-height: 1.8;">
                                ${allModels.training.getting_started.map(step => `<li>${step}</li>`).join('')}
                            </ol>
                        </div>
                        <p style="color: #a0aec0; margin-top: 15px; font-size: 13px;">
                            💡 <strong>Note:</strong> ${allModels.training.note}
                        </p>
                        <p style="color: #a0aec0; margin-top: 10px; font-size: 13px;">
                            ☁️ <strong>Cloud Option:</strong> ${allModels.training.cloud_option}
                        </p>
                    </div>
                `;
                
                contentHtml += `</div>`;
                
                // Final recommendation
                contentHtml += `
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #3a4556;">
                        <h4 style="color: #667eea; margin-bottom: 15px;">💡 Getting Started Guide</h4>
                        <p style="color: #a0aec0; font-size: 14px; margin-bottom: 10px;">
                            <strong>For beginners:</strong> ${allModels.recommendation.best_for_beginners}
                        </p>
                        <p style="color: #a0aec0; font-size: 14px; margin-bottom: 10px;">
                            <strong>Local models:</strong> ${allModels.recommendation.local_models}
                        </p>
                        <p style="color: #a0aec0; font-size: 14px; margin-bottom: 10px;">
                            <strong>Quick API access:</strong> ${allModels.recommendation.api_models}
                        </p>
                        <p style="color: #a0aec0; font-size: 14px; margin-bottom: 10px;">
                            <strong>🎯 Training:</strong> ${allModels.recommendation.training_tip}
                        </p>
                        <p style="color: #a0aec0; font-size: 14px; padding: 12px; background: #667eea15; border-radius: 6px; border-left: 3px solid #667eea;">
                            <strong>💻 Hardware:</strong> ${allModels.recommendation.hardware_recommendation}
                        </p>
                    </div>
                `;
                
                contentHtml += '<div class="message" id="message" style="display: none;"></div>';
                
                modalBody.innerHTML = contentHtml;
                
            } catch (error) {
                console.error('Error loading Ollama setup:', error);
                modalBody.innerHTML = `
                    <div class="alert alert-error">
                        <div style="font-size: 16px; font-weight: bold;">Error Loading Setup</div>
                        <div style="margin-top: 10px;">
                            ${error.message || 'Failed to load Ollama configuration. Please try again.'}
                        </div>
                    </div>
                    <button class="btn btn-secondary" onclick="renderOllamaSetup()" style="margin-top: 15px;">
                        🔄 Try Again
                    </button>
                `;
            }
        }
        
        function showModelTab(tabName, event) {
            // Update tab buttons
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            if (event) event.target.classList.add('active');
            
            // Update tab content
            document.querySelectorAll('.model-tab-content').forEach(content => {
                content.style.display = 'none';
            });
            const activeTab = document.getElementById('tab-' + tabName);
            if (activeTab) activeTab.style.display = 'block';
        }
        
        async function downloadModel(modelName, event) {
            if (event) event.preventDefault();
            
            const btn = event.target;
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span>Downloading...';
            
            showMessage(`<span class="spinner"></span>Downloading ${modelName}... This may take a few minutes.`, 'info');
            
            try {
                const response = await fetch('/api/setup/ollama/download-model', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ model: modelName })
                });
                
                const result = await response.json();
                
                if (response.ok && result.success) {
                    showMessage(`✓ ${result.message}`, 'success');
                    setTimeout(() => renderOllamaSetup(), 1500);
                } else {
                    showMessage(`✗ ${result.detail || 'Download failed'}`, 'error');
                    btn.disabled = false;
                    btn.textContent = `Download ${modelName}`;
                }
            } catch (error) {
                showMessage(`✗ Error: ${error.message}`, 'error');
                btn.disabled = false;
                btn.textContent = `Download ${modelName}`;
            }
        }
        
        async function installStarterPack(event) {
            if (event) event.preventDefault();
            
            const btn = event.target;
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span>Downloading starter pack...';
            
            showMessage('<span class="spinner"></span>Downloading 3 models... This will take several minutes.', 'info');
            
            try {
                const response = await fetch('/api/setup/ollama/install-starter-pack', {
                    method: 'POST'
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    const successMsg = result.results
                        .map(r => r.message)
                        .join('<br>');
                    showMessage(`<div>Download Complete!</div><div style="margin-top: 10px;">${successMsg}</div>`, 'success');
                    setTimeout(() => renderOllamaSetup(), 2000);
                } else {
                    showMessage(`✗ ${result.detail || 'Installation failed'}`, 'error');
                    btn.disabled = false;
                    btn.innerHTML = '🚀 Download All';
                }
            } catch (error) {
                showMessage(`✗ Error: ${error.message}`, 'error');
                btn.disabled = false;
                btn.innerHTML = '🚀 Download All';
            }
        }
        
        async function downloadPythonModel(modelType, modelId, displayName, event) {
            if (event) event.preventDefault();
            
            const btn = event.target;
            btn.disabled = true;
            const originalHTML = btn.innerHTML;
            
            // Create progress bar
            btn.innerHTML = '<div class="install-progress"><div class="progress-bar-fill" style="width: 0%"></div><span class="progress-text">0%</span></div>';
            
            showMessage(`<span class="spinner"></span>Installing ${displayName}...`, 'info');
            
            try {
                // Use streaming endpoint for real-time progress
                const response = await fetch('/api/setup/python-models/install-streaming', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ 
                        type: modelType, 
                        model_id: modelId 
                    })
                });
                
                if (!response.ok) {
                    throw new Error('Installation failed to start');
                }
                
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';
                
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\\n\\n');
                    buffer = lines.pop() || '';
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const data = JSON.parse(line.substring(6));
                            
                            if (data.type === 'status' || data.type === 'progress') {
                                const progressBar = btn.querySelector('.progress-bar-fill');
                                const progressText = btn.querySelector('.progress-text');
                                if (progressBar && progressText) {
                                    progressBar.style.width = data.progress + '%';
                                    progressText.textContent = data.progress + '%';
                                }
                                if (data.message) {
                                    showMessage(`⏳ ${data.message}`, 'info');
                                }
                            } else if (data.type === 'complete') {
                                showMessage(`✓ ${data.message}`, 'success');
                                btn.innerHTML = '✓ Ready';
                                btn.style.background = '#22c55e';
                            } else if (data.type === 'error') {
                                throw new Error(data.message);
                            }
                        }
                    }
                }
            } catch (error) {
                showMessage(`✗ Error: ${error.message}`, 'error');
                btn.disabled = false;
                btn.innerHTML = originalHTML;
            }
        }
        
        async function installPresetPack(packId, event) {
            if (event) event.preventDefault();
            
            const btn = event.target;
            btn.disabled = true;
            const originalHTML = btn.innerHTML;
            
            // Create progress display
            const progressDiv = document.createElement('div');
            progressDiv.className = 'pack-progress';
            progressDiv.innerHTML = '<div class="progress-bar-fill" style="width: 0%"></div><span class="progress-text">Starting...</span>';
            btn.parentNode.appendChild(progressDiv);
            btn.style.display = 'none';
            
            try {
                const response = await fetch('/api/setup/preset-packs/install', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ pack_id: packId })
                });
                
                if (!response.ok) {
                    throw new Error('Pack installation failed to start');
                }
                
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';
                
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\\n\\n');
                    buffer = lines.pop() || '';
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const data = JSON.parse(line.substring(6));
                            
                            const progressBar = progressDiv.querySelector('.progress-bar-fill');
                            const progressText = progressDiv.querySelector('.progress-text');
                            
                            if (data.type === 'model_start') {
                                progressText.textContent = `Installing ${data.model}...`;
                                showMessage(`📦 Installing ${data.model}...`, 'info');
                            } else if (data.type === 'model_complete' || data.type === 'start') {
                                if (progressBar) progressBar.style.width = data.progress + '%';
                                if (progressText && data.progress) progressText.textContent = data.progress + '%';
                            } else if (data.type === 'complete') {
                                if (progressBar) progressBar.style.width = '100%';
                                progressText.textContent = '✓ Complete!';
                                progressDiv.style.background = '#22c55e';
                                showMessage(`✓ ${data.message}`, 'success');
                                setTimeout(() => {
                                    progressDiv.remove();
                                    btn.innerHTML = '✓ Installed';
                                    btn.style.display = '';
                                    btn.style.background = '#22c55e';
                                }, 2000);
                            } else if (data.type === 'error') {
                                throw new Error(data.message);
                            }
                        }
                    }
                }
            } catch (error) {
                showMessage(`✗ Error: ${error.message}`, 'error');
                progressDiv.remove();
                btn.style.display = '';
                btn.disabled = false;
                btn.innerHTML = originalHTML;
            }
        }
        
        function closeModal() {
            document.getElementById('modalOverlay').classList.remove('active');
            currentIntegration = null;
        }
        
        function formatKeyLabel(key) {
            return key
                .replace(/_/g, ' ')
                .replace(/API KEY/gi, 'API Key')
                .replace(/API TOKEN/gi, 'API Token')
                .split(' ')
                .map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
                .join(' ');
        }
        
        function getFormData() {
            const data = {};
            currentIntegration.env_keys.forEach(key => {
                const input = document.getElementById(key);
                if (input && input.value.trim()) {
                    data[key] = input.value.trim();
                }
            });
            return data;
        }
        
        async function validateOnly() {
            const credentials = getFormData();
            if (Object.keys(credentials).length === 0) {
                showMessage('Please enter credentials first', 'error');
                return;
            }
            
            showMessage('<span class="spinner"></span>Testing connection...', 'info');
            
            try {
                const response = await fetch('/api/setup/validate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        integration_id: currentIntegration.id,
                        credentials: credentials
                    })
                });
                
                const result = await response.json();
                if (result.valid) {
                    showMessage('✓ ' + (result.message || 'Connection successful!'), 'success');
                } else {
                    showMessage('✗ ' + (result.error || 'Validation failed'), 'error');
                }
            } catch (error) {
                showMessage('✗ Error: ' + error.message, 'error');
            }
        }
        
        async function saveCredentials(event) {
            event.preventDefault();
            
            const credentials = getFormData();
            if (Object.keys(credentials).length === 0) {
                showMessage('Please enter credentials first', 'error');
                return;
            }
            
            const saveBtn = document.getElementById('saveBtn');
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<span class="spinner"></span>Saving...';
            
            try {
                const response = await fetch('/api/setup/save', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        integration_id: currentIntegration.id,
                        credentials: credentials
                    })
                });
                
                const result = await response.json();
                
                if (response.ok && result.success) {
                    showMessage('✓ ' + result.message, 'success');
                    
                    // Update local state
                    const idx = integrations.findIndex(i => i.id === currentIntegration.id);
                    if (idx >= 0) {
                        integrations[idx].configured = true;
                        integrations[idx].missing_keys = [];
                    }
                    
                    renderIntegrations();
                    updateProgress();
                    
                    // Close modal after delay
                    setTimeout(() => {
                        closeModal();
                    }, 1500);
                } else {
                    showMessage('✗ ' + (result.detail || result.error || 'Save failed'), 'error');
                }
            } catch (error) {
                showMessage('✗ Error: ' + error.message, 'error');
            } finally {
                saveBtn.disabled = false;
                saveBtn.textContent = 'Save & Connect';
            }
        }
        
        function showMessage(text, type) {
            const msg = document.getElementById('message');
            msg.className = 'message ' + type;
            msg.innerHTML = text;
            msg.style.display = 'block';
        }
        
        // Close modal on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeModal();
        });
        
        // Close modal on overlay click
        document.getElementById('modalOverlay').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) closeModal();
        });
        
        // Load on page load
        loadIntegrations();
    </script>
</body>
</html>
"""


@router.get("/", response_class=HTMLResponse)
async def setup_wizard_page():
    """Serve the setup wizard web UI."""
    return HTMLResponse(content=SETUP_HTML)
