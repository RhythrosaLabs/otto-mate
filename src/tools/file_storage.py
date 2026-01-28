"""
File Storage Tools
==================

Tools for storing, retrieving, and managing files.
Connects to the central file storage system.
"""

import logging
import aiohttp
from typing import Optional, Dict, Any, List
from .core import tool, ToolBase
from ..storage import FileStorage, StorageConfig

logger = logging.getLogger(__name__)


class FileStorageTools(ToolBase):
    """File storage and management tools."""
    
    def __init__(self, storage: Optional[FileStorage] = None):
        self.storage = storage or FileStorage(StorageConfig())
    
    @tool(
        name="save_file",
        description="Save content to file storage",
        category="files"
    )
    async def save_file(
        self,
        content: str,
        filename: str,
        category: str = "documents",
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Save text content to storage.
        
        Args:
            content: The content to save
            filename: Name for the file
            category: Category (documents, generated, uploads)
            tags: Optional tags for organization
        """
        try:
            metadata = await self.storage.store(
                data=content.encode('utf-8'),
                filename=filename,
                category=category,
                tags=tags or []
            )
            
            return {
                "success": True,
                "file_id": metadata.id,
                "filename": metadata.filename,
                "url": metadata.url,
                "size": metadata.size
            }
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            return {"success": False, "error": str(e)}
    
    @tool(
        name="save_image_from_url",
        description="Download and save an image from URL to storage",
        category="files"
    )
    async def save_image_from_url(
        self,
        url: str,
        filename: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Download an image from URL and save to storage.
        
        Args:
            url: URL of the image to download
            filename: Optional custom filename
            tags: Optional tags for organization
        """
        try:
            metadata = await self.storage.store_from_url(
                url=url,
                filename=filename,
                category="images",
                tags=tags or []
            )
            
            return {
                "success": True,
                "file_id": metadata.id,
                "filename": metadata.filename,
                "url": metadata.url,
                "original_url": url,
                "size": metadata.size
            }
        except Exception as e:
            logger.error(f"Failed to save image from URL: {e}")
            return {"success": False, "error": str(e)}
    
    @tool(
        name="save_generated_image",
        description="Save an AI-generated image to storage with optional filename and description",
        category="files"
    )
    async def save_generated_image(
        self,
        image_url: str,
        prompt: str = "",
        filename: str = None,
        description: str = None,
        model: str = "unknown",
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Save an AI-generated image with metadata.
        
        Args:
            image_url: URL of the generated image
            prompt: The prompt used to generate the image (optional if description provided)
            filename: Optional custom filename for the saved image
            description: Optional description of the image
            model: The AI model used
            tags: Additional tags
        """
        try:
            all_tags = tags or []
            all_tags.extend(["ai-generated", model])
            
            # Use description or prompt for metadata
            image_description = description or prompt or "AI generated image"
            
            metadata = await self.storage.store_from_url(
                url=image_url,
                category="generated",
                filename=filename,  # Pass filename if provided
                tags=all_tags,
                metadata={
                    "prompt": prompt,
                    "description": image_description,
                    "model": model,
                    "type": "ai_generated"
                }
            )
            
            return {
                "success": True,
                "file_id": metadata.id,
                "filename": metadata.filename,
                "url": metadata.url,
                "prompt": prompt,
                "description": image_description,
                "model": model
            }
        except Exception as e:
            logger.error(f"Failed to save generated image: {e}")
            return {"success": False, "error": str(e)}
    
    @tool(
        name="get_file",
        description="Retrieve a file from storage by ID",
        category="files"
    )
    async def get_file(
        self,
        file_id: str
    ) -> Dict[str, Any]:
        """
        Get a file from storage.
        
        Args:
            file_id: The file ID
        """
        try:
            data, metadata = await self.storage.retrieve(file_id)
            
            return {
                "success": True,
                "file_id": metadata.id,
                "filename": metadata.filename,
                "mime_type": metadata.mime_type,
                "size": metadata.size,
                "url": metadata.url,
                "category": metadata.category,
                "tags": metadata.tags,
                "created_at": metadata.created_at.isoformat() if metadata.created_at else None
            }
        except Exception as e:
            logger.error(f"Failed to get file: {e}")
            return {"success": False, "error": str(e)}
    
    @tool(
        name="list_files",
        description="List files in storage with optional filtering",
        category="files"
    )
    async def list_files(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 50,
        filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List files in storage.
        
        Args:
            category: Filter by category (images, documents, generated, etc.)
            tags: Filter by tags
            limit: Maximum number of files to return
            filter: General text filter (searches filenames and descriptions)
        """
        try:
            files = await self.storage.list_files(
                category=category,
                tags=tags,
                limit=limit
            )
            
            # Apply text filter if provided
            if filter and files:
                filter_lower = filter.lower()
                files = [
                    f for f in files
                    if filter_lower in f.get('filename', '').lower() or
                       filter_lower in f.get('description', '').lower()
                ]
            
            return {
                "success": True,
                "files": [
                    {
                        "id": f.id,
                        "filename": f.filename,
                        "mime_type": f.mime_type,
                        "size": f.size,
                        "url": f.url,
                        "category": f.category,
                        "tags": f.tags,
                        "created_at": f.created_at.isoformat() if f.created_at else None
                    }
                    for f in files
                ],
                "count": len(files)
            }
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return {"success": False, "error": str(e)}
    
    @tool(
        name="delete_file",
        description="Delete a file from storage",
        category="files"
    )
    async def delete_file(
        self,
        file_id: str
    ) -> Dict[str, Any]:
        """
        Delete a file from storage.
        
        Args:
            file_id: The file ID to delete
        """
        try:
            success = await self.storage.delete(file_id)
            return {
                "success": success,
                "file_id": file_id
            }
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return {"success": False, "error": str(e)}
    
    @tool(
        name="get_storage_stats",
        description="Get storage statistics",
        category="files"
    )
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage usage statistics."""
        try:
            stats = await self.storage.get_stats()
            return {
                "success": True,
                **stats
            }
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {"success": False, "error": str(e)}
