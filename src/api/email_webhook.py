"""
Email Inbound Webhook

Receives emails via SendGrid Inbound Parse and processes them through Otto.
Setup: https://docs.sendgrid.com/for-developers/parsing-email/setting-up-the-inbound-parse-webhook
"""

import os
import json
import base64
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Request, Form, File, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
import logging
from email.parser import Parser
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks/email", tags=["Email"])


class EmailMessage(BaseModel):
    """Parsed email message."""
    from_email: str
    from_name: Optional[str]
    to: List[str]
    subject: str
    text: Optional[str]
    html: Optional[str]
    attachments: List[Dict[str, Any]] = []
    headers: Dict[str, str] = {}
    timestamp: Optional[str]


class EmailStatus(BaseModel):
    """Email webhook status."""
    configured: bool
    webhook_url: Optional[str]
    sendgrid_configured: bool
    total_received: int
    pending_messages: int


# In-memory storage for received emails (use database in production)
_received_emails: List[EmailMessage] = []
_pending_messages: List[Dict[str, Any]] = []


@router.post("/inbound")
async def receive_email(
    request: Request,
    headers: Optional[str] = Form(None),
    dkim: Optional[str] = Form(None),
    to: Optional[str] = Form(None),
    from_: Optional[str] = Form(None, alias="from"),
    sender_ip: Optional[str] = Form(None),
    spam_report: Optional[str] = Form(None),
    envelope: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    html: Optional[str] = Form(None),
    attachments: Optional[int] = Form(0),
    attachment_info: Optional[str] = Form(None),
    charsets: Optional[str] = Form(None),
    SPF: Optional[str] = Form(None)
):
    """
    Receive inbound email from SendGrid Inbound Parse.
    
    SendGrid will POST to this endpoint when an email is received.
    Configure at: https://app.sendgrid.com/settings/parse
    
    Webhook URL: https://your-domain.com/api/webhooks/email/inbound
    """
    logger.info(f"Received email from {from_} to {to} - Subject: {subject}")
    
    try:
        # Parse email addresses
        to_addresses = to.split(",") if to else []
        
        # Extract sender info
        from_email = from_ or ""
        from_name = None
        if "<" in from_email:
            # Format: "John Doe <john@example.com>"
            parts = from_email.split("<")
            from_name = parts[0].strip().strip('"')
            from_email = parts[1].strip(">")
        
        # Parse headers if provided
        headers_dict = {}
        if headers:
            try:
                headers_dict = json.loads(headers)
            except:
                pass
        
        # Parse attachments
        attachments_list = []
        if attachment_info:
            try:
                attachments_list = json.loads(attachment_info)
            except:
                pass
        
        # Create message object
        email_msg = EmailMessage(
            from_email=from_email,
            from_name=from_name,
            to=to_addresses,
            subject=subject or "(no subject)",
            text=text,
            html=html,
            attachments=attachments_list,
            headers=headers_dict
        )
        
        # Store the email
        _received_emails.append(email_msg)
        
        # Add to pending messages for Otto to process
        message = {
            "channel": "email",
            "from": from_email,
            "from_name": from_name,
            "to": to_addresses,
            "subject": email_msg.subject,
            "message": text or html or "",
            "timestamp": headers_dict.get("Date", ""),
            "attachments": attachments_list
        }
        _pending_messages.append(message)
        
        logger.info(f"Email queued for processing: {email_msg.subject}")
        
        # Optionally process immediately (async)
        asyncio.create_task(process_email_message(email_msg))
        
        return Response(status_code=200, content="OK")
        
    except Exception as e:
        logger.error(f"Error processing inbound email: {e}", exc_info=True)
        # Return 200 anyway to prevent SendGrid retries
        return Response(status_code=200, content="Error recorded")


async def process_email_message(email: EmailMessage):
    """Process an email message through Otto's orchestrator."""
    try:
        # Import here to avoid circular dependency
        from ..core.agent_orchestrator import AgentOrchestrator
        from . import main
        
        if not main.orchestrator:
            logger.warning("Orchestrator not available for email processing")
            return
        
        # Create context
        context = {
            "channel": "email",
            "from": email.from_email,
            "subject": email.subject,
            "to": email.to
        }
        
        # Use email body as message
        user_message = email.text or email.html or ""
        
        # Add subject to message if meaningful
        if email.subject and email.subject != "(no subject)":
            user_message = f"Subject: {email.subject}\n\n{user_message}"
        
        # Process through orchestrator
        logger.info(f"Processing email from {email.from_email} through Otto")
        response = await main.orchestrator.process_message(
            user_message,
            context=context
        )
        
        logger.info(f"Email processed successfully: {response[:100] if response else 'No response'}")
        
        # TODO: Send response back via email using SendGrid
        # await send_email_response(email.from_email, email.subject, response)
        
    except Exception as e:
        logger.error(f"Error processing email message: {e}", exc_info=True)


@router.post("/send")
async def send_email(
    to: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    html: Optional[str] = None,
    attachments: Optional[List[Dict[str, str]]] = None
):
    """
    Send an email via SendGrid.
    
    Requires SENDGRID_API_KEY in environment.
    """
    api_key = os.getenv("SENDGRID_API_KEY")
    if not api_key or api_key.startswith("your_"):
        raise HTTPException(400, "SendGrid not configured. Set SENDGRID_API_KEY")
    
    try:
        import httpx
        
        default_from = os.getenv("SENDGRID_FROM_EMAIL", "otto@yourdomain.com")
        from_addr = from_email or default_from
        
        # Build SendGrid API request
        data = {
            "personalizations": [{
                "to": [{"email": to}],
                "subject": subject
            }],
            "from": {"email": from_addr},
            "content": []
        }
        
        # Add text content
        if body:
            data["content"].append({
                "type": "text/plain",
                "value": body
            })
        
        # Add HTML content
        if html:
            data["content"].append({
                "type": "text/html",
                "value": html
            })
        
        # Add attachments if provided
        if attachments:
            data["attachments"] = attachments
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json=data
            )
            
            if response.status_code == 202:
                return {
                    "success": True,
                    "message": "Email sent successfully",
                    "to": to,
                    "subject": subject
                }
            else:
                logger.error(f"SendGrid error: {response.status_code} - {response.text}")
                raise HTTPException(500, f"Failed to send email: {response.text}")
                
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise HTTPException(500, str(e))


@router.get("/status")
async def email_status() -> EmailStatus:
    """Get email webhook status."""
    api_key = os.getenv("SENDGRID_API_KEY")
    webhook_base = os.getenv("WEBHOOK_BASE_URL", "https://your-domain.com")
    
    return EmailStatus(
        configured=bool(api_key and not api_key.startswith("your_")),
        webhook_url=f"{webhook_base}/api/webhooks/email/inbound",
        sendgrid_configured=bool(api_key and not api_key.startswith("your_")),
        total_received=len(_received_emails),
        pending_messages=len(_pending_messages)
    )


@router.get("/received")
async def list_received_emails(limit: int = 50) -> List[EmailMessage]:
    """List recently received emails."""
    return _received_emails[-limit:]


@router.get("/pending")
async def list_pending_messages() -> List[Dict[str, Any]]:
    """List pending messages to be processed."""
    return _pending_messages


@router.delete("/pending/{index}")
async def clear_pending_message(index: int):
    """Clear a pending message after processing."""
    if 0 <= index < len(_pending_messages):
        _pending_messages.pop(index)
        return {"success": True}
    raise HTTPException(404, "Message not found")


@router.get("/setup-guide")
async def email_setup_guide():
    """Get instructions for setting up email integration."""
    webhook_base = os.getenv("WEBHOOK_BASE_URL", "https://your-domain.com")
    
    return {
        "name": "Email Integration via SendGrid Inbound Parse",
        "steps": [
            {
                "step": 1,
                "title": "Get SendGrid API Key",
                "description": "Sign up at sendgrid.com (free tier: 100 emails/day)",
                "url": "https://app.sendgrid.com/settings/api_keys"
            },
            {
                "step": 2,
                "title": "Add API Key to Otto",
                "description": f"Set SENDGRID_API_KEY in your .env file",
                "action": "Add to .env: SENDGRID_API_KEY=SG.xxx"
            },
            {
                "step": 3,
                "title": "Verify Domain or Email",
                "description": "Verify a sender in SendGrid to send emails",
                "url": "https://app.sendgrid.com/settings/sender_auth"
            },
            {
                "step": 4,
                "title": "Set up Inbound Parse",
                "description": "Configure SendGrid to forward emails to Otto",
                "url": "https://app.sendgrid.com/settings/parse",
                "details": [
                    f"Hostname: Use a subdomain like otto.yourdomain.com",
                    f"URL: {webhook_base}/api/webhooks/email/inbound",
                    "Check POST the raw, full MIME message"
                ]
            },
            {
                "step": 5,
                "title": "Configure MX Records",
                "description": "Point your subdomain's MX record to SendGrid",
                "details": [
                    "Add MX record: otto.yourdomain.com → mx.sendgrid.net (priority 10)",
                    "Emails sent to anything@otto.yourdomain.com will be parsed"
                ]
            },
            {
                "step": 6,
                "title": "Test",
                "description": f"Send an email to test@otto.yourdomain.com",
                "note": "Otto will receive it and respond automatically"
            }
        ],
        "webhook_url": f"{webhook_base}/api/webhooks/email/inbound",
        "sendgrid_docs": "https://docs.sendgrid.com/for-developers/parsing-email/setting-up-the-inbound-parse-webhook"
    }
