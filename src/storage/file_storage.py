"""
File Storage System
===================

Manages file uploads, storage, and retrieval.
Supports local filesystem and cloud storage (S3, GCS).
"""

import os
import uuid
import hashlib
import mimetypes
import aiofiles
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, BinaryIO
from dataclasses import dataclass, field
from enum import Enum
import json
import shutil

logger = logging.getLogger(__name__)


class StorageProvider(Enum):
    """Supported storage providers."""
    LOCAL = "local"
    S3 = "s3"
    GCS = "gcs"


@dataclass
class StorageConfig:
    """Configuration for file storage."""
    provider: StorageProvider = StorageProvider.LOCAL
    base_path: str = "./data/files"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_extensions: List[str] = field(default_factory=lambda: [
        # Images
        ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".tiff",
        # Videos
        ".mp4", ".mov", ".avi", ".webm", ".mkv",
        # Audio
        ".mp3", ".wav", ".ogg", ".m4a", ".flac", ".aac",
        # Documents
        ".pdf", ".doc", ".docx", ".txt", ".md", ".rtf",
        # Data
        ".json", ".csv", ".xlsx", ".xml", ".yaml", ".yml",
        # Code files
        ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".scss", ".sass",
        ".java", ".c", ".cpp", ".h", ".hpp", ".go", ".rs", ".rb", ".php",
        ".swift", ".kt", ".scala", ".sql", ".sh", ".bash", ".zsh",
        # 3D Models
        ".glb", ".gltf", ".obj", ".fbx", ".stl", ".ply", ".usdz"
    ])
    
    # S3 config
    s3_bucket: Optional[str] = None
    s3_region: Optional[str] = None
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None
    
    # GCS config
    gcs_bucket: Optional[str] = None
    gcs_credentials_path: Optional[str] = None


@dataclass
class FileMetadata:
    """Metadata for a stored file."""
    id: str
    filename: str
    original_name: str
    mime_type: str
    size: int
    checksum: str
    path: str
    url: Optional[str]
    category: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "filename": self.filename,
            "original_name": self.original_name,
            "mime_type": self.mime_type,
            "size": self.size,
            "checksum": self.checksum,
            "path": self.path,
            "url": self.url,
            "category": self.category,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileMetadata":
        return cls(
            id=data["id"],
            filename=data["filename"],
            original_name=data["original_name"],
            mime_type=data["mime_type"],
            size=data["size"],
            checksum=data["checksum"],
            path=data["path"],
            url=data.get("url"),
            category=data.get("category", "general"),
            tags=data.get("tags", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {})
        )


class FileStorage:
    """
    File storage system with support for multiple backends.
    """
    
    def __init__(self, config: Optional[StorageConfig] = None):
        self.config = config or StorageConfig()
        self.base_path = Path(self.config.base_path)
        self.metadata_path = self.base_path / ".metadata"
        
        # Create directories
        self._init_directories()
        
        # Load metadata index
        self._metadata_index: Dict[str, FileMetadata] = {}
        self._load_metadata_index()
        
        logger.info(f"File storage initialized: {self.config.provider.value}")
    
    def _init_directories(self):
        """Initialize storage directories."""
        directories = [
            self.base_path,
            self.base_path / "images",
            self.base_path / "documents",
            self.base_path / "audio",
            self.base_path / "video",
            self.base_path / "generated",
            self.base_path / "uploads",
            self.base_path / "temp",
            self.metadata_path
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _load_metadata_index(self):
        """Load metadata index from disk."""
        index_file = self.metadata_path / "index.json"
        if index_file.exists():
            try:
                with open(index_file, "r") as f:
                    data = json.load(f)
                    self._metadata_index = {
                        k: FileMetadata.from_dict(v) for k, v in data.items()
                    }
                logger.info(f"Loaded {len(self._metadata_index)} file metadata entries")
            except Exception as e:
                logger.error(f"Failed to load metadata index: {e}")
                self._metadata_index = {}
    
    def _save_metadata_index(self):
        """Save metadata index to disk."""
        index_file = self.metadata_path / "index.json"
        try:
            with open(index_file, "w") as f:
                data = {k: v.to_dict() for k, v in self._metadata_index.items()}
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metadata index: {e}")
    
    def _get_category_path(self, mime_type: str, filename: str = "") -> Path:
        """Get storage path based on MIME type and filename."""
        # Check filename extension for code files
        if filename:
            ext = Path(filename).suffix.lower()
            code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss',
                            '.json', '.yaml', '.yml', '.xml', '.sql', '.sh', '.bash',
                            '.java', '.c', '.cpp', '.h', '.hpp', '.go', '.rs', '.rb', '.php'}
            if ext in code_extensions:
                return self.base_path / "code"
            
            # 3D model extensions
            model_extensions = {'.glb', '.gltf', '.obj', '.fbx', '.stl', '.ply', '.usdz'}
            if ext in model_extensions:
                return self.base_path / "3d_models"
        
        if mime_type.startswith("image/"):
            return self.base_path / "images"
        elif mime_type.startswith("video/"):
            return self.base_path / "video"
        elif mime_type.startswith("audio/"):
            return self.base_path / "audio"
        elif mime_type in ["application/pdf", "application/msword", "text/plain"]:
            return self.base_path / "documents"
        else:
            return self.base_path / "uploads"
    
    def _get_category(self, mime_type: str, filename: str = "") -> str:
        """Get category based on MIME type and filename."""
        # Check filename extension for code files
        if filename:
            ext = Path(filename).suffix.lower()
            code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss',
                            '.json', '.yaml', '.yml', '.xml', '.sql', '.sh', '.bash',
                            '.java', '.c', '.cpp', '.h', '.hpp', '.go', '.rs', '.rb', '.php'}
            if ext in code_extensions:
                return "code"
            
            # 3D model extensions
            model_extensions = {'.glb', '.gltf', '.obj', '.fbx', '.stl', '.ply', '.usdz'}
            if ext in model_extensions:
                return "3d_models"
        
        if mime_type.startswith("image/"):
            return "images"
        elif mime_type.startswith("video/"):
            return "video"
        elif mime_type.startswith("audio/"):
            return "audio"
        elif mime_type in ["application/pdf", "application/msword", "text/plain"]:
            return "documents"
        else:
            return "general"
    
    def _calculate_checksum(self, data: bytes) -> str:
        """Calculate SHA-256 checksum."""
        return hashlib.sha256(data).hexdigest()
    
    def _generate_filename(self, original_name: str) -> str:
        """Generate unique filename."""
        ext = Path(original_name).suffix.lower()
        unique_id = uuid.uuid4().hex[:12]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_{unique_id}{ext}"
    
    def _validate_file(self, filename: str, size: int):
        """Validate file against constraints."""
        ext = Path(filename).suffix.lower()
        
        if ext not in self.config.allowed_extensions:
            raise ValueError(f"File extension '{ext}' not allowed")
        
        if size > self.config.max_file_size:
            raise ValueError(f"File size {size} exceeds maximum {self.config.max_file_size}")
    
    async def store(
        self,
        data: bytes,
        filename: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FileMetadata:
        """
        Store a file.
        
        Args:
            data: File content as bytes
            filename: Original filename
            category: Optional category override
            tags: Optional tags for organization
            metadata: Optional additional metadata
            
        Returns:
            FileMetadata object
        """
        # Validate
        self._validate_file(filename, len(data))
        
        # Determine MIME type and category
        mime_type, _ = mimetypes.guess_type(filename)
        mime_type = mime_type or "application/octet-stream"
        
        if category is None:
            category = self._get_category(mime_type, filename)
        
        # Generate unique filename
        stored_filename = self._generate_filename(filename)
        
        # Determine storage path
        if category == "generated":
            storage_path = self.base_path / "generated"
        elif category == "code":
            storage_path = self.base_path / "code"
        elif category == "3d_models":
            storage_path = self.base_path / "3d_models"
        else:
            storage_path = self._get_category_path(mime_type, filename)
        
        file_path = storage_path / stored_filename
        
        # Calculate checksum
        checksum = self._calculate_checksum(data)
        
        # Check for duplicates
        for existing in self._metadata_index.values():
            if existing.checksum == checksum:
                logger.info(f"File already exists: {existing.id}")
                return existing
        
        # Store file
        if self.config.provider == StorageProvider.LOCAL:
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(data)
        elif self.config.provider == StorageProvider.S3:
            await self._store_s3(data, stored_filename)
        elif self.config.provider == StorageProvider.GCS:
            await self._store_gcs(data, stored_filename)
        
        # Create metadata
        now = datetime.now()
        file_id = uuid.uuid4().hex
        
        file_metadata = FileMetadata(
            id=file_id,
            filename=stored_filename,
            original_name=filename,
            mime_type=mime_type,
            size=len(data),
            checksum=checksum,
            path=str(file_path.relative_to(self.base_path)),
            url=f"/files/{file_id}",
            category=category,
            tags=tags or [],
            created_at=now,
            updated_at=now,
            metadata=metadata or {}
        )
        
        # Save to index
        self._metadata_index[file_id] = file_metadata
        self._save_metadata_index()
        
        logger.info(f"Stored file: {file_id} ({filename})")
        return file_metadata
    
    async def store_from_url(
        self,
        url: str,
        filename: Optional[str] = None,
        **kwargs
    ) -> FileMetadata:
        """Store a file from URL."""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise ValueError(f"Failed to fetch URL: {response.status}")
                
                data = await response.read()
                
                if filename is None:
                    # Extract filename from URL or content-disposition
                    filename = url.split("/")[-1].split("?")[0]
                    if not filename:
                        filename = f"download_{uuid.uuid4().hex[:8]}"
                
                return await self.store(data, filename, **kwargs)
    
    async def retrieve(self, file_id: str) -> tuple[bytes, FileMetadata]:
        """
        Retrieve a file by ID.
        
        Returns:
            Tuple of (file data, metadata)
        """
        if file_id not in self._metadata_index:
            raise FileNotFoundError(f"File not found: {file_id}")
        
        metadata = self._metadata_index[file_id]
        file_path = self.base_path / metadata.path
        
        if self.config.provider == StorageProvider.LOCAL:
            if not file_path.exists():
                raise FileNotFoundError(f"File not found on disk: {metadata.path}")
            
            async with aiofiles.open(file_path, "rb") as f:
                data = await f.read()
        else:
            # Cloud storage retrieval
            data = await self._retrieve_cloud(metadata)
        
        return data, metadata
    
    def get_metadata(self, file_id: str) -> Optional[FileMetadata]:
        """Get file metadata without retrieving content."""
        return self._metadata_index.get(file_id)
    
    def list_files(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[FileMetadata]:
        """
        List files with optional filtering.
        """
        files = list(self._metadata_index.values())
        
        # Filter by category
        if category:
            files = [f for f in files if f.category == category]
        
        # Filter by tags
        if tags:
            files = [f for f in files if any(t in f.tags for t in tags)]
        
        # Sort by creation date (newest first)
        files.sort(key=lambda x: x.created_at, reverse=True)
        
        # Paginate
        return files[offset:offset + limit]
    
    async def delete(self, file_id: str) -> bool:
        """Delete a file."""
        if file_id not in self._metadata_index:
            return False
        
        metadata = self._metadata_index[file_id]
        file_path = self.base_path / metadata.path
        
        # Delete from storage
        if self.config.provider == StorageProvider.LOCAL:
            if file_path.exists():
                file_path.unlink()
        else:
            await self._delete_cloud(metadata)
        
        # Remove from index
        del self._metadata_index[file_id]
        self._save_metadata_index()
        
        logger.info(f"Deleted file: {file_id}")
        return True
    
    async def update_metadata(
        self,
        file_id: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[FileMetadata]:
        """Update file metadata."""
        if file_id not in self._metadata_index:
            return None
        
        file_meta = self._metadata_index[file_id]
        
        if tags is not None:
            file_meta.tags = tags
        
        if metadata is not None:
            file_meta.metadata.update(metadata)
        
        file_meta.updated_at = datetime.now()
        
        self._save_metadata_index()
        return file_meta
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        stats = {
            "total_files": len(self._metadata_index),
            "total_size": sum(f.size for f in self._metadata_index.values()),
            "by_category": {},
            "by_mime_type": {}
        }
        
        for f in self._metadata_index.values():
            # By category
            if f.category not in stats["by_category"]:
                stats["by_category"][f.category] = {"count": 0, "size": 0}
            stats["by_category"][f.category]["count"] += 1
            stats["by_category"][f.category]["size"] += f.size
            
            # By MIME type
            base_type = f.mime_type.split("/")[0]
            if base_type not in stats["by_mime_type"]:
                stats["by_mime_type"][base_type] = {"count": 0, "size": 0}
            stats["by_mime_type"][base_type]["count"] += 1
            stats["by_mime_type"][base_type]["size"] += f.size
        
        return stats
    
    def cleanup_temp(self, max_age_hours: int = 24):
        """Clean up temporary files older than max_age."""
        temp_path = self.base_path / "temp"
        now = datetime.now()
        
        for file_path in temp_path.iterdir():
            if file_path.is_file():
                age = now - datetime.fromtimestamp(file_path.stat().st_mtime)
                if age.total_seconds() > max_age_hours * 3600:
                    file_path.unlink()
                    logger.info(f"Cleaned up temp file: {file_path.name}")
    
    # Cloud storage methods (stubs for now)
    async def _store_s3(self, data: bytes, filename: str):
        """Store to S3."""
        raise NotImplementedError("S3 storage not yet implemented")
    
    async def _store_gcs(self, data: bytes, filename: str):
        """Store to GCS."""
        raise NotImplementedError("GCS storage not yet implemented")
    
    async def _retrieve_cloud(self, metadata: FileMetadata) -> bytes:
        """Retrieve from cloud storage."""
        raise NotImplementedError("Cloud retrieval not yet implemented")
    
    async def _delete_cloud(self, metadata: FileMetadata):
        """Delete from cloud storage."""
        raise NotImplementedError("Cloud deletion not yet implemented")
