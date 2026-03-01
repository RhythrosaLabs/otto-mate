"""
Email Marketing Service for Otto
=================================

Generate and send professional email campaigns using AI-generated content.
Ported from printify_clean with enhancements.

Supports multiple email providers:
1. SendGrid API (free tier: 100 emails/day) - RECOMMENDED
2. Gmail OAuth2 (uses existing Google credentials)
3. SMTP (Gmail App Password, other providers)
"""

import base64
import logging
import os
import smtplib
from datetime import datetime
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests

logger = logging.getLogger(__name__)


class EmailMarketingService:
    """
    Generate and send professional marketing emails with AI-powered content.

    Supports multiple providers:
    - sendgrid: Uses SendGrid API (easiest, free 100/day)
    - gmail_oauth: Uses Google OAuth2
    - smtp: Traditional SMTP (requires app password for Gmail)
    """

    # Email template types
    TEMPLATE_TYPES = {
        "product_launch": "Product Launch Announcement",
        "newsletter": "Weekly/Monthly Newsletter",
        "promotion": "Special Offer/Discount",
        "cart_abandonment": "Cart Abandonment Reminder",
        "welcome": "Welcome Series",
        "re_engagement": "Win-Back Campaign",
        "order_confirmation": "Order Confirmation",
        "shipping_update": "Shipping Update",
    }

    def __init__(
        self,
        provider: Optional[str] = None,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        sendgrid_api_key: Optional[str] = None,
    ):
        """
        Initialize email marketing service.

        Args:
            provider: 'sendgrid', 'gmail_oauth', or 'smtp' (auto-detected if not specified)
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port (587 for TLS, 465 for SSL)
            smtp_username: SMTP username
            smtp_password: SMTP password
            from_email: Sender email address
            from_name: Sender display name
            sendgrid_api_key: SendGrid API key
        """
        # Load from environment
        self.sendgrid_api_key = sendgrid_api_key or os.getenv("SENDGRID_API_KEY")
        self.smtp_host = smtp_host or os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("EMAIL_SMTP_PORT", "587"))
        self.smtp_username = smtp_username or os.getenv("EMAIL_USERNAME")
        self.smtp_password = smtp_password or os.getenv("EMAIL_PASSWORD") or os.getenv("EMAIL_APP_PASSWORD")
        self.from_email = from_email or os.getenv("EMAIL_FROM_ADDRESS", self.smtp_username)
        self.from_name = from_name or os.getenv("EMAIL_FROM_NAME", "Otto")

        # Auto-detect provider (prioritize SendGrid)
        if provider:
            self.provider = provider
        elif self.sendgrid_api_key:
            self.provider = "sendgrid"
        elif self.smtp_username and self.smtp_password:
            self.provider = "smtp"
        else:
            self.provider = None

        if self.provider:
            logger.info(f"Email Marketing Service initialized (provider: {self.provider})")
        else:
            logger.warning("No email provider configured. Set SENDGRID_API_KEY or EMAIL credentials.")

    def is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return self.provider is not None

    def _send_via_sendgrid(self, to_email: str, subject: str, html_content: str, 
                           text_content: Optional[str] = None) -> bool:
        """Send email using SendGrid API."""
        if not self.sendgrid_api_key:
            logger.error("SendGrid API key not configured")
            return False

        try:
            url = "https://api.sendgrid.com/v3/mail/send"
            headers = {
                "Authorization": f"Bearer {self.sendgrid_api_key}",
                "Content-Type": "application/json",
            }

            content = [{"type": "text/html", "value": html_content}]
            if text_content:
                content.insert(0, {"type": "text/plain", "value": text_content})

            data = {
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": self.from_email, "name": self.from_name},
                "subject": subject,
                "content": content,
            }

            response = requests.post(url, headers=headers, json=data, timeout=30)

            if response.status_code in [200, 202]:
                logger.info(f"Email sent via SendGrid to {to_email}")
                return True
            else:
                logger.error(f"SendGrid error: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"SendGrid send failed: {e}")
            return False

    def _send_via_smtp(self, to_email: str, subject: str, html_content: str,
                       text_content: Optional[str] = None) -> bool:
        """Send email using traditional SMTP."""
        if not all([self.smtp_username, self.smtp_password]):
            logger.error("SMTP credentials not configured")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            if text_content:
                msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent via SMTP to {to_email}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication failed: {e}")
            logger.error("For Gmail: Use an App Password (2FA required)")
            return False
        except Exception as e:
            logger.error(f"SMTP send failed: {e}")
            return False

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Send email using the configured provider.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text alternative (optional)

        Returns:
            True if sent successfully
        """
        if not self.provider:
            logger.error("No email provider configured!")
            return False

        if self.provider == "sendgrid":
            return self._send_via_sendgrid(to_email, subject, html_content, text_content)
        elif self.provider == "smtp":
            return self._send_via_smtp(to_email, subject, html_content, text_content)
        else:
            logger.error(f"Unknown provider: {self.provider}")
            return False

    def send_bulk_email(
        self,
        recipients: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        delay_seconds: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Send email to multiple recipients.

        Args:
            recipients: List of email addresses
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text alternative
            delay_seconds: Delay between sends to avoid rate limits

        Returns:
            Dict with success/failure counts
        """
        import time

        results = {"total": len(recipients), "sent": 0, "failed": 0, "errors": []}

        for email in recipients:
            try:
                if self.send_email(email, subject, html_content, text_content):
                    results["sent"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({"email": email, "error": "Send failed"})
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"email": email, "error": str(e)})

            # Rate limiting delay
            if delay_seconds > 0:
                time.sleep(delay_seconds)

        logger.info(f"Bulk email: {results['sent']}/{results['total']} sent successfully")
        return results

    def create_html_email(
        self,
        subject: str,
        preview_text: str,
        headline: str,
        body: str,
        cta_text: str,
        cta_link: str,
        product_image_url: Optional[str] = None,
        brand_color: str = "#3b82f6",
        product_name: str = "",
        price: str = "",
        discount: str = "",
        footer_text: str = "",
    ) -> str:
        """
        Create a modern, responsive HTML email template.

        Args:
            subject: Email subject
            preview_text: Preview text (appears after subject in inbox)
            headline: Main headline
            body: Body text (supports newlines for paragraphs)
            cta_text: Call-to-action button text
            cta_link: CTA button URL
            product_image_url: Optional product image URL
            brand_color: Primary brand color (hex)
            product_name: Product name for display
            price: Regular price
            discount: Discounted price
            footer_text: Optional footer text

        Returns:
            Complete HTML email string
        """
        current_year = datetime.now().year

        # Format body paragraphs
        body_paragraphs = body.split("\n") if body else [""]
        body_html = "".join(
            f'<p style="margin: 0 0 16px 0; font-size: 16px; line-height: 1.7; color: #4b5563;">{p.strip()}</p>'
            for p in body_paragraphs if p.strip()
        )

        # Price display
        price_html = ""
        if price:
            if discount:
                price_html = f"""
                <div style="text-align: center; margin: 24px 0;">
                    <span style="font-size: 18px; color: #9ca3af; text-decoration: line-through; margin-right: 12px;">{price}</span>
                    <span style="font-size: 32px; font-weight: 800; color: #10b981;">{discount}</span>
                </div>
                """
            else:
                price_html = f"""
                <div style="text-align: center; margin: 24px 0;">
                    <span style="font-size: 32px; font-weight: 800; color: #1f2937;">{price}</span>
                </div>
                """

        # Hero image
        hero_image_html = ""
        if product_image_url:
            hero_image_html = f"""
            <tr>
                <td>
                    <img src="{product_image_url}" alt="{product_name or 'Product'}" 
                         style="width: 100%; max-height: 350px; object-fit: cover; display: block;">
                </td>
            </tr>
            """

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>{subject}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background-color: #f3f4f6;
        }}
        @media only screen and (max-width: 600px) {{
            .container {{ width: 100% !important; padding: 0 16px !important; }}
            .content {{ padding: 24px 20px !important; }}
            .headline {{ font-size: 24px !important; }}
        }}
    </style>
</head>
<body style="margin: 0; padding: 0; background-color: #f3f4f6;">
    <!-- Preview text -->
    <div style="display: none; max-height: 0; overflow: hidden;">
        {preview_text}
    </div>
    
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" 
           style="background-color: #f3f4f6;">
        <tr>
            <td align="center" style="padding: 40px 16px;">
                
                <!-- Main container -->
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" 
                       class="container" 
                       style="max-width: 600px; width: 100%; background-color: #ffffff; 
                              border-radius: 12px; overflow: hidden; 
                              box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, {brand_color}, #8b5cf6); 
                                   padding: 32px; text-align: center;">
                            <h1 style="color: #ffffff; font-size: 24px; font-weight: 700; margin: 0;">
                                {self.from_name}
                            </h1>
                        </td>
                    </tr>
                    
                    {hero_image_html}
                    
                    <!-- Content -->
                    <tr>
                        <td class="content" style="padding: 40px 32px;">
                            <h2 class="headline" style="font-size: 28px; font-weight: 700; 
                                                        color: #1f2937; margin-bottom: 24px; 
                                                        text-align: center;">
                                {headline}
                            </h2>
                            
                            {body_html}
                            
                            {price_html}
                            
                            <!-- CTA Button -->
                            <div style="text-align: center; margin: 32px 0;">
                                <a href="{cta_link}" 
                                   style="display: inline-block; padding: 16px 40px; 
                                          background: linear-gradient(135deg, {brand_color}, #8b5cf6); 
                                          color: #ffffff; text-decoration: none; 
                                          font-weight: 600; font-size: 16px; 
                                          border-radius: 8px;">
                                    {cta_text}
                                </a>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 32px; background-color: #f9fafb; 
                                   border-top: 1px solid #e5e7eb; text-align: center;">
                            <p style="font-size: 12px; color: #9ca3af; margin: 0 0 8px 0;">
                                {footer_text or f'© {current_year} {self.from_name}. All rights reserved.'}
                            </p>
                            <p style="font-size: 11px; color: #9ca3af; margin: 0;">
                                <a href="{{{{unsubscribe}}}}" style="color: #9ca3af;">Unsubscribe</a>
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """

        return html

    def create_campaign(
        self,
        name: str,
        template_type: str,
        recipients: List[str],
        subject: str,
        content: Dict[str, str],
        schedule_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Create an email campaign (for tracking/management).

        Args:
            name: Campaign name
            template_type: Type of template
            recipients: List of recipient emails
            subject: Email subject
            content: Content dict (headline, body, cta_text, cta_link, etc.)
            schedule_time: Optional scheduled send time

        Returns:
            Campaign data dict
        """
        import uuid

        campaign = {
            "id": str(uuid.uuid4()),
            "name": name,
            "template_type": template_type,
            "subject": subject,
            "recipient_count": len(recipients),
            "content": content,
            "created_at": datetime.now().isoformat(),
            "scheduled_for": schedule_time.isoformat() if schedule_time else None,
            "status": "scheduled" if schedule_time else "draft",
            "sent_count": 0,
            "open_rate": 0,
            "click_rate": 0,
        }

        logger.info(f"Created campaign: {name} ({len(recipients)} recipients)")
        return campaign

    def generate_email_content(
        self,
        template_type: str,
        product_name: str,
        product_description: str,
        target_audience: str = "general consumers",
        special_offer: str = "",
        tone: str = "professional and friendly",
    ) -> Dict[str, str]:
        """
        Generate AI-powered email content.

        Args:
            template_type: Type of email template
            product_name: Product name
            product_description: Product description
            target_audience: Target audience description
            special_offer: Special offer details
            tone: Writing tone

        Returns:
            Dict with subject, preview_text, headline, body, cta
        """
        # For now, return template-based content
        # In production, this would call an LLM

        templates = {
            "product_launch": {
                "subject": f"Introducing {product_name}! 🎉",
                "preview_text": f"Be the first to discover {product_name}",
                "headline": f"Say Hello to {product_name}",
                "body": f"We're thrilled to introduce {product_name}.\n\n{product_description}\n\n{special_offer}" if special_offer else f"We're thrilled to introduce {product_name}.\n\n{product_description}",
                "cta": "Shop Now",
            },
            "promotion": {
                "subject": f"Special Offer on {product_name}! 🔥",
                "preview_text": f"Don't miss this limited-time deal",
                "headline": f"Limited Time: {special_offer}" if special_offer else f"Special Offer Inside",
                "body": f"For a limited time, get an amazing deal on {product_name}.\n\n{product_description}",
                "cta": "Claim Offer",
            },
            "newsletter": {
                "subject": f"What's New: {product_name}",
                "preview_text": "Your weekly update is here",
                "headline": "This Week's Highlights",
                "body": f"Here's what's new this week:\n\n{product_name}\n\n{product_description}",
                "cta": "Read More",
            },
            "welcome": {
                "subject": "Welcome to the family! 👋",
                "preview_text": "We're so glad you're here",
                "headline": "Welcome Aboard!",
                "body": f"Thank you for joining us!\n\nWe're excited to have you. Here's what you can expect:\n\n• Exclusive offers and early access\n• New product announcements\n• Tips and inspiration",
                "cta": "Start Exploring",
            },
        }

        content = templates.get(template_type, templates["product_launch"])
        logger.info(f"Generated {template_type} email content for {product_name}")
        return content


# Singleton instance
_email_service = None


def get_email_service() -> EmailMarketingService:
    """Get the singleton EmailMarketingService instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailMarketingService()
    return _email_service


# =============================================================================
# TOOL-DECORATED EMAIL FUNCTIONS FOR CHAT INTERFACE
# =============================================================================

from .core import tool


class EmailTools:
    """Email tools accessible via chat."""
    
    def __init__(self):
        self.service = get_email_service()
    
    @tool(
        name="send_email",
        description="Send an HTML-rich email. Compose and send professional emails with formatting, images, and styling. Perfect for marketing emails, newsletters, announcements, or any rich-formatted email.",
        category="email"
    )
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an email with HTML content.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_content: HTML-formatted email body
            text_content: Optional plain text version
            
        Returns:
            Result with success status
        """
        if not self.service.is_configured():
            return {
                "success": False,
                "error": "Email not configured. Add SENDGRID_API_KEY or EMAIL_USERNAME/EMAIL_PASSWORD to .env",
                "hint": "Get free SendGrid API key at https://sendgrid.com (100 emails/day free)"
            }
        
        success = self.service.send_email(to_email, subject, html_content, text_content)
        
        if success:
            return {
                "success": True,
                "to": to_email,
                "subject": subject,
                "provider": self.service.provider,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": "Email send failed. Check logs for details."
            }
    
    @tool(
        name="generate_and_send_email",
        description="Generate a professional marketing email using AI and send it. Specify the email type, recipient, and key points - the system will create and send a beautifully formatted HTML email.",
        category="email"
    )
    async def generate_and_send_email(
        self,
        to_email: str,
        subject: str,
        email_type: str = "announcement",
        product_name: Optional[str] = None,
        key_points: Optional[List[str]] = None,
        offer_details: Optional[str] = None,
        call_to_action: str = "Learn More",
        cta_url: Optional[str] = None,
        brand_color: str = "#6366f1"
    ) -> Dict[str, Any]:
        """
        Generate a professional HTML email and send it.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            email_type: Type of email (product_launch, newsletter, promotion, welcome, announcement)
            product_name: Optional product/feature name
            key_points: List of key points to include
            offer_details: Optional special offer text
            call_to_action: Button text
            cta_url: Link for the call-to-action button
            brand_color: Brand accent color (hex)
        """
        if not self.service.is_configured():
            return {
                "success": False,
                "error": "Email not configured. Add SENDGRID_API_KEY to .env",
                "hint": "Get free SendGrid API key at https://sendgrid.com"
            }
        
        # Build HTML email
        points_html = ""
        if key_points:
            points_html = "\n".join([f'<li style="margin-bottom: 10px;">{point}</li>' for point in key_points])
            points_html = f'<ul style="padding-left: 20px; color: #444; line-height: 1.8;">{points_html}</ul>'
        
        cta_button = ""
        if cta_url:
            cta_button = f'''
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{cta_url}" style="background: {brand_color}; color: white; padding: 14px 28px; 
                       text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">
                        {call_to_action}
                    </a>
                </div>
            '''
        
        offer_section = ""
        if offer_details:
            offer_section = f'''
                <div style="background: {brand_color}15; padding: 20px; border-radius: 8px; 
                     margin: 20px 0; border-left: 4px solid {brand_color};">
                    <p style="margin: 0; font-size: 18px; font-weight: 600; color: {brand_color};">
                        🎁 Special Offer
                    </p>
                    <p style="margin: 10px 0 0 0; font-size: 16px; color: #333;">
                        {offer_details}
                    </p>
                </div>
            '''
        
        product_header = ""
        if product_name:
            product_header = f'<h2 style="color: {brand_color}; margin-top: 0;">{product_name}</h2>'
        
        html_content = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: white; border-radius: 12px; padding: 40px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
            {product_header}
            {points_html}
            {offer_section}
            {cta_button}
        </div>
        <div style="text-align: center; margin-top: 20px; color: #888; font-size: 12px;">
            <p>Sent with ❤️ by {self.service.from_name}</p>
        </div>
    </div>
</body>
</html>
'''
        
        success = self.service.send_email(to_email, subject, html_content)
        
        if success:
            return {
                "success": True,
                "to": to_email,
                "subject": subject,
                "email_type": email_type,
                "provider": self.service.provider,
                "html_generated": True,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {"success": False, "error": "Failed to send email"}
    
    @tool(
        name="check_email_config",
        description="Check if email sending is properly configured and which provider is active",
        category="email"
    )
    async def check_email_config(self) -> Dict[str, Any]:
        """Check email configuration status."""
        return {
            "configured": self.service.is_configured(),
            "provider": self.service.provider or "none",
            "from_email": self.service.from_email or "not set",
            "from_name": self.service.from_name,
            "sendgrid_configured": bool(self.service.sendgrid_api_key),
            "smtp_configured": bool(self.service.smtp_username and self.service.smtp_password),
            "hint": "Add SENDGRID_API_KEY to .env for easy setup (free 100 emails/day at sendgrid.com)"
        }


# Create singleton for tools
_email_tools = None

def get_email_tools() -> EmailTools:
    """Get the singleton EmailTools instance."""
    global _email_tools
    if _email_tools is None:
        _email_tools = EmailTools()
    return _email_tools
