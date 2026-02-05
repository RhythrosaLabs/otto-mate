"""Dependency injection for API routes."""
from functools import lru_cache
from typing import Optional

from ...core.services import ChatService, FileService, AgentService
from ..orchestrator_bridge import get_orchestrator as get_orch


# Service singletons
_chat_service: Optional[ChatService] = None
_file_service: Optional[FileService] = None
_agent_service: Optional[AgentService] = None


def get_orchestrator():
    """Get or create orchestrator instance."""
    return get_orch()


def get_chat_service() -> ChatService:
    """Dependency injection for ChatService."""
    global _chat_service
    if _chat_service is None:
        orchestrator = get_orchestrator()
        _chat_service = ChatService(orchestrator)
    return _chat_service


def get_file_service() -> FileService:
    """Dependency injection for FileService."""
    global _file_service
    if _file_service is None:
        _file_service = FileService(storage_path="data/files")
    return _file_service


def get_agent_service() -> AgentService:
    """Dependency injection for AgentService."""
    global _agent_service
    if _agent_service is None:
        orchestrator = get_orchestrator()
        _agent_service = AgentService(orchestrator)
    return _agent_service
