"""
Notification Sender Plugin
==========================

Send notifications through various channels.

Supports:
- Email (SMTP)
- Slack (webhook)
- Discord (webhook)
- Generic webhooks
"""

import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

from src.core.plugin_system import IntegrationPlugin


class NotificationSenderPlugin(IntegrationPlugin):
    """Plugin for sending notifications through various channels."""
    
    async def initialize(self) -> None:
        """Initialize the plugin and register tools."""
        
        # Email tool
        self.register_tool(
            name="send_email",
            func=self.send_email,
            description="Send an email via SMTP",
            parameters={
                "to": {
                    "type": "string",
                    "required": True,
                    "description": "Recipient email address(es), comma-separated for multiple"
                },
                "subject": {
                    "type": "string",
                    "required": True,
                    "description": "Email subject line"
                },
                "body": {
                    "type": "string",
                    "required": True,
                    "description": "Email body content"
                },
                "html": {
                    "type": "boolean",
                    "required": False,
                    "description": "Send as HTML email (default: false)"
                }
            }
        )
        
        # Slack tool
        self.register_tool(
            name="send_slack_message",
            func=self.send_slack_message,
            description="Send a message to Slack via webhook",
            parameters={
                "message": {
                    "type": "string",
                    "required": True,
                    "description": "Message text to send"
                },
                "channel": {
                    "type": "string",
                    "required": False,
                    "description": "Channel name (if webhook supports it)"
                },
                "username": {
                    "type": "string",
                    "required": False,
                    "description": "Bot username to display"
                },
                "icon_emoji": {
                    "type": "string",
                    "required": False,
                    "description": "Emoji icon (e.g., :robot:)"
                }
            }
        )
        
        # Discord tool
        self.register_tool(
            name="send_discord_webhook",
            func=self.send_discord_webhook,
            description="Send a message to Discord via webhook",
            parameters={
                "message": {
                    "type": "string",
                    "required": True,
                    "description": "Message content"
                },
                "username": {
                    "type": "string",
                    "required": False,
                    "description": "Override bot username"
                },
                "embed_title": {
                    "type": "string",
                    "required": False,
                    "description": "Embed title"
                },
                "embed_description": {
                    "type": "string",
                    "required": False,
                    "description": "Embed description"
                },
                "embed_color": {
                    "type": "integer",
                    "required": False,
                    "description": "Embed color as decimal integer"
                }
            }
        )
        
        # Generic webhook
        self.register_tool(
            name="send_webhook",
            func=self.send_webhook,
            description="Send data to any webhook URL",
            parameters={
                "url": {
                    "type": "string",
                    "required": True,
                    "description": "Webhook URL"
                },
                "data": {
                    "type": "object",
                    "required": True,
                    "description": "JSON data to send"
                },
                "method": {
                    "type": "string",
                    "required": False,
                    "description": "HTTP method (default: POST)"
                }
            }
        )
    
    async def connect(self) -> bool:
        """Check if integrations are configured."""
        self._connected = True
        return True
    
    async def disconnect(self) -> None:
        """Cleanup connections."""
        self._connected = False
    
    async def send_email(
        self, 
        to: str, 
        subject: str, 
        body: str, 
        html: bool = False
    ) -> Dict[str, Any]:
        """Send an email via SMTP."""
        
        smtp_host = self.settings.get("smtp_host")
        smtp_port = self.settings.get("smtp_port", 587)
        smtp_user = self.settings.get("smtp_user")
        smtp_password = self.settings.get("smtp_password")
        
        if not all([smtp_host, smtp_user, smtp_password]):
            return {
                "success": False,
                "error": "SMTP not configured. Set smtp_host, smtp_user, and smtp_password in plugin settings."
            }
        
        try:
            # Create message
            if html:
                msg = MIMEMultipart("alternative")
                msg.attach(MIMEText(body, "html"))
            else:
                msg = MIMEMultipart()
                msg.attach(MIMEText(body, "plain"))
            
            msg["Subject"] = subject
            msg["From"] = smtp_user
            msg["To"] = to
            
            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                
                recipients = [addr.strip() for addr in to.split(",")]
                server.sendmail(smtp_user, recipients, msg.as_string())
            
            return {
                "success": True,
                "message": f"Email sent to {to}",
                "subject": subject
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_slack_message(
        self, 
        message: str, 
        channel: str = None,
        username: str = None,
        icon_emoji: str = None
    ) -> Dict[str, Any]:
        """Send a message to Slack via webhook."""
        
        if not HAS_AIOHTTP:
            return {
                "success": False,
                "error": "aiohttp not installed. Run: pip install aiohttp"
            }
        
        webhook_url = self.settings.get("slack_webhook_url")
        if not webhook_url:
            return {
                "success": False,
                "error": "Slack webhook URL not configured. Set slack_webhook_url in plugin settings."
            }
        
        try:
            payload = {"text": message}
            
            if channel:
                payload["channel"] = channel
            if username:
                payload["username"] = username
            if icon_emoji:
                payload["icon_emoji"] = icon_emoji
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        return {
                            "success": True,
                            "message": "Message sent to Slack"
                        }
                    else:
                        text = await response.text()
                        return {
                            "success": False,
                            "error": f"Slack returned {response.status}: {text}"
                        }
                        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_discord_webhook(
        self, 
        message: str,
        username: str = None,
        embed_title: str = None,
        embed_description: str = None,
        embed_color: int = None
    ) -> Dict[str, Any]:
        """Send a message to Discord via webhook."""
        
        if not HAS_AIOHTTP:
            return {
                "success": False,
                "error": "aiohttp not installed. Run: pip install aiohttp"
            }
        
        webhook_url = self.settings.get("discord_webhook_url")
        if not webhook_url:
            return {
                "success": False,
                "error": "Discord webhook URL not configured. Set discord_webhook_url in plugin settings."
            }
        
        try:
            payload = {"content": message}
            
            if username:
                payload["username"] = username
            
            # Add embed if provided
            if embed_title or embed_description:
                embed = {}
                if embed_title:
                    embed["title"] = embed_title
                if embed_description:
                    embed["description"] = embed_description
                if embed_color:
                    embed["color"] = embed_color
                payload["embeds"] = [embed]
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status in [200, 204]:
                        return {
                            "success": True,
                            "message": "Message sent to Discord"
                        }
                    else:
                        text = await response.text()
                        return {
                            "success": False,
                            "error": f"Discord returned {response.status}: {text}"
                        }
                        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_webhook(
        self, 
        url: str, 
        data: Dict[str, Any],
        method: str = "POST"
    ) -> Dict[str, Any]:
        """Send data to a generic webhook."""
        
        if not HAS_AIOHTTP:
            return {
                "success": False,
                "error": "aiohttp not installed. Run: pip install aiohttp"
            }
        
        try:
            async with aiohttp.ClientSession() as session:
                request_method = getattr(session, method.lower(), session.post)
                
                async with request_method(
                    url,
                    json=data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    response_text = await response.text()
                    
                    # Try to parse as JSON
                    try:
                        response_data = json.loads(response_text)
                    except:
                        response_data = response_text
                    
                    return {
                        "success": response.status < 400,
                        "status_code": response.status,
                        "response": response_data
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
