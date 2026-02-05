"""
Webhooks API Router
===================

Handle incoming webhooks from:
- Replicate (AI model predictions)
- Shopify (store events)
- Custom webhook endpoints
"""

import logging
import json
import hmac
import hashlib
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request, Header, BackgroundTasks
from pydantic import BaseModel

from ..tools.replicate_advanced import ReplicateWebhookHandler
from ..tools.scheduler import create_task_scheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

# Global webhook handlers
replicate_handler: Optional[ReplicateWebhookHandler] = None
webhook_history: list = []
MAX_HISTORY = 100


def get_replicate_handler() -> ReplicateWebhookHandler:
    """Get or create Replicate webhook handler."""
    global replicate_handler
    if replicate_handler is None:
        import os
        secret = os.getenv("REPLICATE_WEBHOOK_SECRET")
        replicate_handler = ReplicateWebhookHandler(secret=secret)
    return replicate_handler


# ==========================================
# WEBHOOK MODELS
# ==========================================

class WebhookEvent(BaseModel):
    """Generic webhook event."""
    source: str
    event_type: str
    payload: Dict[str, Any]
    received_at: str
    processed: bool = False


class ReplicateWebhookPayload(BaseModel):
    """Replicate prediction webhook payload."""
    id: str
    model: Optional[str] = None
    version: Optional[str] = None
    input: Optional[Dict] = None
    output: Optional[Any] = None
    error: Optional[str] = None
    status: str
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    metrics: Optional[Dict] = None


class ShopifyWebhookPayload(BaseModel):
    """Shopify webhook payload."""
    id: Optional[int] = None
    admin_graphql_api_id: Optional[str] = None
    # Other fields depend on webhook topic


# ==========================================
# REPLICATE WEBHOOKS
# ==========================================

@router.post("/replicate")
async def handle_replicate_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_replicate_signature: Optional[str] = Header(None)
):
    """
    Handle incoming Replicate prediction webhooks.
    
    Replicate sends webhooks when predictions:
    - Start (status: starting)
    - Produce output (status: processing)
    - Complete (status: succeeded/failed/canceled)
    """
    try:
        body = await request.body()
        payload = json.loads(body)
        
        # Verify signature if secret is configured
        handler = get_replicate_handler()
        if handler.secret and x_replicate_signature:
            expected = hmac.new(
                handler.secret.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(x_replicate_signature, expected):
                logger.warning("Invalid Replicate webhook signature")
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Log the webhook
        logger.info(f"Replicate webhook: {payload.get('id')} - {payload.get('status')}")
        
        # Record in history
        webhook_event = WebhookEvent(
            source="replicate",
            event_type=payload.get("status", "unknown"),
            payload=payload,
            received_at=datetime.now().isoformat()
        )
        webhook_history.append(webhook_event.dict())
        if len(webhook_history) > MAX_HISTORY:
            webhook_history.pop(0)
        
        # Process asynchronously
        background_tasks.add_task(
            handler.handle_webhook,
            payload
        )
        
        return {
            "received": True,
            "prediction_id": payload.get("id"),
            "status": payload.get("status")
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error(f"Replicate webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/replicate/register")
async def get_replicate_webhook_info():
    """Get information about the Replicate webhook endpoint."""
    import os
    
    # Get the base URL (you'd configure this in production)
    base_url = os.getenv("WEBHOOK_BASE_URL", "https://your-domain.com")
    
    return {
        "webhook_url": f"{base_url}/webhooks/replicate",
        "supported_events": ["start", "output", "logs", "completed"],
        "usage": {
            "description": "Add this URL as webhook when creating Replicate predictions",
            "example": {
                "webhook": f"{base_url}/webhooks/replicate",
                "webhook_events_filter": ["start", "completed"]
            }
        }
    }


# ==========================================
# SHOPIFY WEBHOOKS
# ==========================================

def verify_shopify_webhook(data: bytes, hmac_header: str, secret: str) -> bool:
    """Verify Shopify webhook HMAC signature."""
    digest = hmac.new(
        secret.encode('utf-8'),
        data,
        hashlib.sha256
    ).digest()
    
    import base64
    computed_hmac = base64.b64encode(digest).decode()
    
    return hmac.compare_digest(computed_hmac, hmac_header)


@router.post("/shopify/{topic}")
async def handle_shopify_webhook(
    topic: str,
    request: Request,
    background_tasks: BackgroundTasks,
    x_shopify_hmac_sha256: Optional[str] = Header(None),
    x_shopify_shop_domain: Optional[str] = Header(None),
    x_shopify_topic: Optional[str] = Header(None)
):
    """
    Handle incoming Shopify webhooks.
    
    Topics include:
    - orders/create, orders/paid, orders/fulfilled
    - products/create, products/update, products/delete
    - customers/create, customers/update
    - inventory_levels/update
    - app/uninstalled
    """
    import os
    
    try:
        body = await request.body()
        
        # Verify HMAC signature
        shopify_secret = os.getenv("SHOPIFY_WEBHOOK_SECRET")
        if shopify_secret and x_shopify_hmac_sha256:
            if not verify_shopify_webhook(body, x_shopify_hmac_sha256, shopify_secret):
                logger.warning("Invalid Shopify webhook signature")
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        payload = json.loads(body)
        actual_topic = x_shopify_topic or topic.replace("_", "/")
        
        logger.info(f"Shopify webhook: {actual_topic} from {x_shopify_shop_domain}")
        
        # Record in history
        webhook_event = WebhookEvent(
            source="shopify",
            event_type=actual_topic,
            payload={
                "topic": actual_topic,
                "shop": x_shopify_shop_domain,
                "data": payload
            },
            received_at=datetime.now().isoformat()
        )
        webhook_history.append(webhook_event.dict())
        if len(webhook_history) > MAX_HISTORY:
            webhook_history.pop(0)
        
        # Process based on topic
        background_tasks.add_task(
            process_shopify_webhook,
            actual_topic,
            payload,
            x_shopify_shop_domain
        )
        
        return {"received": True, "topic": actual_topic}
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error(f"Shopify webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_shopify_webhook(topic: str, payload: Dict, shop_domain: str):
    """Process Shopify webhook in background."""
    try:
        # Handle different webhook topics
        if topic.startswith("orders/"):
            await handle_order_webhook(topic, payload)
        elif topic.startswith("products/"):
            await handle_product_webhook(topic, payload)
        elif topic.startswith("customers/"):
            await handle_customer_webhook(topic, payload)
        elif topic.startswith("inventory"):
            await handle_inventory_webhook(topic, payload)
        else:
            logger.info(f"Unhandled Shopify webhook topic: {topic}")
            
    except Exception as e:
        logger.error(f"Error processing Shopify webhook: {e}")


async def handle_order_webhook(topic: str, payload: Dict):
    """Handle order-related webhooks."""
    order_id = payload.get("id")
    order_number = payload.get("order_number")
    
    if topic == "orders/create":
        logger.info(f"New order #{order_number} created")
        # Could trigger notification, update inventory, etc.
        
    elif topic == "orders/paid":
        logger.info(f"Order #{order_number} paid")
        # Could trigger fulfillment workflow
        
    elif topic == "orders/fulfilled":
        logger.info(f"Order #{order_number} fulfilled")
        # Could trigger follow-up email


async def handle_product_webhook(topic: str, payload: Dict):
    """Handle product-related webhooks."""
    product_id = payload.get("id")
    title = payload.get("title")
    
    if topic == "products/create":
        logger.info(f"New product created: {title}")
    elif topic == "products/update":
        logger.info(f"Product updated: {title}")
    elif topic == "products/delete":
        logger.info(f"Product deleted: {product_id}")


async def handle_customer_webhook(topic: str, payload: Dict):
    """Handle customer-related webhooks."""
    customer_id = payload.get("id")
    email = payload.get("email")
    
    if topic == "customers/create":
        logger.info(f"New customer: {email}")
        # Could trigger welcome email


async def handle_inventory_webhook(topic: str, payload: Dict):
    """Handle inventory-related webhooks."""
    inventory_item_id = payload.get("inventory_item_id")
    available = payload.get("available")
    
    logger.info(f"Inventory updated: item {inventory_item_id} = {available}")
    # Could trigger low stock alert


# ==========================================
# GENERIC WEBHOOKS
# ==========================================

@router.post("/custom/{webhook_id}")
async def handle_custom_webhook(
    webhook_id: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle custom webhook endpoints.
    
    Create named webhook endpoints for external integrations.
    """
    try:
        body = await request.body()
        
        # Try to parse as JSON, fall back to raw
        try:
            payload = json.loads(body)
        except:
            payload = {"raw": body.decode("utf-8", errors="ignore")}
        
        logger.info(f"Custom webhook received: {webhook_id}")
        
        # Record in history
        webhook_event = WebhookEvent(
            source="custom",
            event_type=webhook_id,
            payload=payload,
            received_at=datetime.now().isoformat()
        )
        webhook_history.append(webhook_event.dict())
        if len(webhook_history) > MAX_HISTORY:
            webhook_history.pop(0)
        
        return {
            "received": True,
            "webhook_id": webhook_id,
            "payload_size": len(body)
        }
        
    except Exception as e:
        logger.error(f"Custom webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# WEBHOOK MANAGEMENT
# ==========================================

@router.get("/history")
async def get_webhook_history(
    source: Optional[str] = None,
    limit: int = 50
):
    """Get recent webhook history."""
    history = webhook_history.copy()
    
    if source:
        history = [h for h in history if h.get("source") == source]
    
    # Return most recent first
    history.reverse()
    
    return {
        "total": len(history),
        "webhooks": history[:limit]
    }


@router.get("/endpoints")
async def list_webhook_endpoints():
    """List available webhook endpoints."""
    import os
    base_url = os.getenv("WEBHOOK_BASE_URL", "https://your-domain.com")
    
    return {
        "endpoints": {
            "replicate": {
                "url": f"{base_url}/webhooks/replicate",
                "description": "Replicate AI model predictions",
                "events": ["start", "output", "logs", "completed"]
            },
            "shopify": {
                "url": f"{base_url}/webhooks/shopify/{{topic}}",
                "description": "Shopify store events",
                "topics": [
                    "orders/create", "orders/paid", "orders/fulfilled",
                    "products/create", "products/update", "products/delete",
                    "customers/create", "customers/update",
                    "inventory_levels/update"
                ]
            },
            "custom": {
                "url": f"{base_url}/webhooks/custom/{{webhook_id}}",
                "description": "Custom webhook endpoints for any integration"
            }
        },
        "base_url": base_url,
        "note": "Set WEBHOOK_BASE_URL environment variable for production"
    }


@router.delete("/history")
async def clear_webhook_history():
    """Clear webhook history."""
    global webhook_history
    count = len(webhook_history)
    webhook_history = []
    return {"cleared": count}
