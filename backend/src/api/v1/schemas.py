"""Pydantic schemas for API v1."""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime


# ==================== Chat Schemas ====================

class ChatRequest(BaseModel):
    """Request schema for sending a chat message."""
    message: str = Field(..., description="User's message")
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(default="default", description="User identifier")


class ChatResponse(BaseModel):
    """Response schema for chat message."""
    message_id: str
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}


class StreamChunk(BaseModel):
    """Schema for streaming response chunk."""
    type: Literal["thinking", "text", "tool_start", "tool_end", "artifact", "complete", "error"]
    content: str
    metadata: Dict[str, Any] = {}


class ChatHistoryResponse(BaseModel):
    """Response schema for chat history."""
    session_id: str
    messages: List[ChatResponse]
    total_messages: int = 0
    has_more: bool = False


# ==================== File Schemas ====================

class FileUploadResponse(BaseModel):
    """Response schema for file upload."""
    file_id: str
    name: str
    category: str
    size: int
    mime_type: str
    checksum: str


class FileMetadataResponse(BaseModel):
    """Response schema for file metadata."""
    id: str
    name: str
    path: str
    category: str
    size: int
    mime_type: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime


class FileListResponse(BaseModel):
    """Response schema for file list."""
    files: List[FileMetadataResponse]
    total: int


# ==================== Agent Schemas ====================

class ToolSchema(BaseModel):
    """Schema for tool information."""
    name: str
    description: str
    category: str
    parameters: Dict[str, Any]
    enabled: bool = True


class AgentCreateRequest(BaseModel):
    """Request schema for creating an agent."""
    name: str
    role: str
    description: str
    system_prompt: str
    tools: Optional[List[str]] = []


class AgentResponse(BaseModel):
    """Response schema for agent."""
    id: str
    name: str
    role: str
    description: str
    tools: List[ToolSchema]
    model: str
    temperature: float
    max_tokens: int


class AgentListResponse(BaseModel):
    """Response schema for agent list."""
    agents: List[AgentResponse]
    total: int


# ==================== Settings Schemas ====================

class SettingsResponse(BaseModel):
    """Response schema for settings."""
    api_keys: Dict[str, bool]  # Key name -> is_set
    models: Dict[str, Any]
    features: Dict[str, bool]


class SettingsUpdateRequest(BaseModel):
    """Request schema for updating settings."""
    api_keys: Optional[Dict[str, str]] = None
    models: Optional[Dict[str, Any]] = None
    features: Optional[Dict[str, bool]] = None


# ==================== Common Schemas ====================

class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Generic error response."""
    detail: str
    status_code: int
