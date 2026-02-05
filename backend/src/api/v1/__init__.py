"""API v1 router initialization."""
from fastapi import APIRouter

from . import chat, files, agents, settings

# Create main v1 router
router = APIRouter()

# Include sub-routers
router.include_router(chat.router)
router.include_router(files.router)
router.include_router(agents.router)
router.include_router(settings.router)

__all__ = ["router"]
