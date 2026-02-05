"""Domain models for chat functionality."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Literal, Optional
from uuid import uuid4


@dataclass
class ChatMessage:
    """Domain model for a chat message."""
    
    id: str
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        role: Literal["user", "assistant", "system"],
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "ChatMessage":
        """Create a new chat message with auto-generated ID."""
        return cls(
            id=str(uuid4()),
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatMessage":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"])
            if isinstance(data["timestamp"], str)
            else data["timestamp"],
            metadata=data.get("metadata", {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class ChatSession:
    """Domain model for a chat session."""
    
    id: str
    user_id: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create(cls, user_id: str = "default") -> "ChatSession":
        """Create a new chat session."""
        now = datetime.now()
        return cls(
            id=str(uuid4()),
            user_id=user_id,
            messages=[],
            created_at=now,
            updated_at=now,
            metadata={}
        )
    
    def add_message(self, message: ChatMessage) -> None:
        """Add a message to the session."""
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class StreamingChunk:
    """Domain model for a streaming response chunk."""
    
    type: Literal["thinking", "text", "tool_start", "tool_end", "artifact", "complete", "error"]
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "content": self.content,
            "metadata": self.metadata
        }
