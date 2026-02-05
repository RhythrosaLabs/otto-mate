"""File service - Pure business logic for file operations."""
import os
import hashlib
from typing import List, Optional
from pathlib import Path

from ..models.file import File, FileMetadata


class FileService:
    """
    Business logic for file operations.
    
    No HTTP/upload middleware dependencies - just pure file management.
    """
    
    def __init__(self, storage_path: str = "data/files"):
        """Initialize with storage configuration."""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._file_registry = {}  # In-memory registry (replace with DB)
    
    async def save_file(
        self,
        file_data: bytes,
        filename: str,
        category: str = "documents",
        tags: Optional[List[str]] = None,
        user_id: str = "default"
    ) -> File:
        """
        Save a file and return file metadata.
        
        Args:
            file_data: Raw file bytes
            filename: Original filename
            category: File category
            tags: Optional tags
            user_id: User identifier
            
        Returns:
            File domain model
        """
        # Calculate checksum
        checksum = hashlib.sha256(file_data).hexdigest()
        
        # Determine storage path
        category_path = self.storage_path / category
        category_path.mkdir(parents=True, exist_ok=True)
        
        # Use checksum as filename to avoid duplicates
        file_extension = Path(filename).suffix
        storage_filename = f"{checksum}{file_extension}"
        storage_path = category_path / storage_filename
        
        # Save file
        with open(storage_path, "wb") as f:
            f.write(file_data)
        
        # Create metadata
        metadata = FileMetadata(
            size=len(file_data),
            mime_type=self._detect_mime_type(filename),
            checksum=checksum
        )
        
        # Create file record
        file_record = File.create(
            name=filename,
            path=str(storage_path),
            category=category,
            metadata=metadata,
            tags=tags,
            user_id=user_id
        )
        
        # Register file
        self._file_registry[file_record.id] = file_record
        
        return file_record
    
    async def get_file(self, file_id: str) -> Optional[File]:
        """Get file metadata by ID."""
        return self._file_registry.get(file_id)
    
    async def get_file_data(self, file_id: str) -> Optional[bytes]:
        """Get raw file data by ID."""
        file_record = self._file_registry.get(file_id)
        if not file_record:
            return None
        
        try:
            with open(file_record.path, "rb") as f:
                return f.read()
        except FileNotFoundError:
            return None
    
    async def list_files(
        self,
        user_id: str = "default",
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[File]:
        """List files with optional filters."""
        files = list(self._file_registry.values())
        
        # Filter by user
        files = [f for f in files if f.user_id == user_id]
        
        # Filter by category
        if category:
            files = [f for f in files if f.category == category]
        
        # Filter by tags
        if tags:
            files = [f for f in files if any(tag in f.tags for tag in tags)]
        
        # Sort by created_at (most recent first)
        files.sort(key=lambda f: f.created_at, reverse=True)
        
        return files
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete a file."""
        file_record = self._file_registry.get(file_id)
        if not file_record:
            return False
        
        # Delete physical file
        try:
            os.remove(file_record.path)
        except FileNotFoundError:
            pass
        
        # Remove from registry
        del self._file_registry[file_id]
        
        return True
    
    def _detect_mime_type(self, filename: str) -> str:
        """Detect MIME type from filename."""
        extension = Path(filename).suffix.lower()
        
        mime_types = {
            ".txt": "text/plain",
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".mp4": "video/mp4",
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
        }
        
        return mime_types.get(extension, "application/octet-stream")
