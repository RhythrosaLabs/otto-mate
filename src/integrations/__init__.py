"""Integrations module for Otto Universal AI."""

from .whatsapp import WhatsAppClient, WhatsAppMessage, create_whatsapp_router

__all__ = ["WhatsAppClient", "WhatsAppMessage", "create_whatsapp_router"]
