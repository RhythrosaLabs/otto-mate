"""Domain models for file functionality."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Literal, Optional
from uuid import uuid4


@dataclass
class FileMetadata:
    """Metadata for a file."""
    
    size: int
    mime_type: str
    checksum: str
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    encoding: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "size": self.size,
            "mime_type": self.mime_type,
            "checksum": self.checksum,
            "width": self.width,
            "height": self.height,
            "duration": self.duration,
            "encoding": self.encoding,
            **self.extra
        }


@dataclass
class File:
    """Domain model for a file."""
    
    id: str
    name: str
    path: str
    category: Literal["documents", "images", "videos", "audio", "other"]
    metadata: FileMetadata
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    user_id: str = "default"
    description: Optional[str] = None
    
    @classmethod
    def create(
        cls,
        name: str,
        path: str,
        category: Literal["documents", "images", "videos", "audio", "other"],
        metadata: FileMetadata,
        tags: Optional[List[str]] = None,
        user_id: str = "default",
        description: Optional[str] = None
    ) -> "File":
        """Create a new file record."""
        now = datetime.now()
        return cls(
            id=str(uuid4()),
            name=name,
            path=path,
            category=category,
            metadata=metadata,
            tags=tags or [],
            created_at=now,
            updated_at=now,
            user_id=user_id,
            description=description
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "category": self.category,
            "metadata": self.metadata.to_dict(),
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "user_id": self.user_id,
            "description": self.description
        }
