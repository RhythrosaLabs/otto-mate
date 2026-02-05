"""
Email Marketing API Router
===========================

REST API endpoints for email campaign management and sending.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List
from pydantic import BaseModel, EmailStr
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/email", tags=["email"])


# Request/Response models
class SendEmailRequest(BaseModel):
    to_email: str
    subject: str
    html_content: str
    text_content: Optional[str] = None


class BulkEmailRequest(BaseModel):
    recipients: List[str]
    subject: str
    html_content: str
    text_content: Optional[str] = None
    delay_seconds: float = 0.5


class CreateEmailRequest(BaseModel):
    subject: str
    preview_text: str
    headline: str
    body: str
    cta_text: str
    cta_link: str
    product_image_url: Optional[str] = None
    brand_color: str = "#3b82f6"
    product_name: str = ""
    price: str = ""
    discount: str = ""
    footer_text: str = ""


class GenerateContentRequest(BaseModel):
    template_type: str
    product_name: str
    product_description: str
    target_audience: str = "general consumers"
    special_offer: str = ""
    tone: str = "professional and friendly"


class CreateCampaignRequest(BaseModel):
    name: str
    template_type: str
    recipients: List[str]
    subject: str
    content: dict
    schedule_time: Optional[str] = None


@router.get("/status")
async def get_email_status():
    """Check email service configuration status."""
    try:
        from src.tools.email_marketing import get_email_service
        service = get_email_service()
        
        return {
            "success": True,
            "configured": service.is_configured(),
            "provider": service.provider,
            "from_email": service.from_email,
            "from_name": service.from_name,
        }
    except Exception as e:
        logger.error(f"Failed to get email status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates")
async def get_email_templates():
    """Get available email template types."""
    try:
        from src.tools.email_marketing import EmailMarketingService
        
        return {
            "success": True,
            "templates": EmailMarketingService.TEMPLATE_TYPES,
        }
    except Exception as e:
        logger.error(f"Failed to get templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send")
async def send_email(request: SendEmailRequest):
    """Send a single email."""
    try:
        from src.tools.email_marketing import get_email_service
        service = get_email_service()
        
        if not service.is_configured():
            raise HTTPException(
                status_code=400, 
                detail="Email service not configured. Set SENDGRID_API_KEY or EMAIL credentials."
            )
        
        success = service.send_email(
            to_email=request.to_email,
            subject=request.subject,
            html_content=request.html_content,
            text_content=request.text_content,
        )
        
        return {
            "success": success,
            "message": "Email sent" if success else "Failed to send email",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-bulk")
async def send_bulk_email(request: BulkEmailRequest):
    """Send email to multiple recipients."""
    try:
        from src.tools.email_marketing import get_email_service
        service = get_email_service()
        
        if not service.is_configured():
            raise HTTPException(
                status_code=400,
                detail="Email service not configured"
            )
        
        results = service.send_bulk_email(
            recipients=request.recipients,
            subject=request.subject,
            html_content=request.html_content,
            text_content=request.text_content,
            delay_seconds=request.delay_seconds,
        )
        
        return {
            "success": True,
            **results,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send bulk email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-html")
async def create_html_email(request: CreateEmailRequest):
    """Create a responsive HTML email template."""
    try:
        from src.tools.email_marketing import get_email_service
        service = get_email_service()
        
        html = service.create_html_email(
            subject=request.subject,
            preview_text=request.preview_text,
            headline=request.headline,
            body=request.body,
            cta_text=request.cta_text,
            cta_link=request.cta_link,
            product_image_url=request.product_image_url,
            brand_color=request.brand_color,
            product_name=request.product_name,
            price=request.price,
            discount=request.discount,
            footer_text=request.footer_text,
        )
        
        return {
            "success": True,
            "html": html,
        }
    except Exception as e:
        logger.error(f"Failed to create HTML email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-content")
async def generate_email_content(request: GenerateContentRequest):
    """Generate AI-powered email content for a template type."""
    try:
        from src.tools.email_marketing import get_email_service
        service = get_email_service()
        
        content = service.generate_email_content(
            template_type=request.template_type,
            product_name=request.product_name,
            product_description=request.product_description,
            target_audience=request.target_audience,
            special_offer=request.special_offer,
            tone=request.tone,
        )
        
        return {
            "success": True,
            "content": content,
        }
    except Exception as e:
        logger.error(f"Failed to generate email content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/campaign")
async def create_campaign(request: CreateCampaignRequest):
    """Create an email campaign for tracking."""
    try:
        from src.tools.email_marketing import get_email_service
        from datetime import datetime
        
        service = get_email_service()
        
        schedule_time = None
        if request.schedule_time:
            schedule_time = datetime.fromisoformat(request.schedule_time)
        
        campaign = service.create_campaign(
            name=request.name,
            template_type=request.template_type,
            recipients=request.recipients,
            subject=request.subject,
            content=request.content,
            schedule_time=schedule_time,
        )
        
        return {
            "success": True,
            "campaign": campaign,
        }
    except Exception as e:
        logger.error(f"Failed to create campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/campaign/{campaign_id}/send")
async def send_campaign(campaign_id: str):
    """
    Send an existing campaign.
    
    Note: This is a placeholder - full campaign storage would be needed
    to implement this properly.
    """
    return {
        "success": False,
        "message": "Campaign storage not yet implemented. Use /send-bulk instead.",
    }
