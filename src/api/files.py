"""
Files API
=========

Endpoints for file upload, download, and management.
"""

import logging
import base64
from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from ..storage import FileStorage, StorageConfig

logger = logging.getLogger(__name__)

# Global file storage instance
file_storage: Optional[FileStorage] = None


def get_file_storage() -> FileStorage:
    """Get or create file storage instance."""
    global file_storage
    if file_storage is None:
        file_storage = FileStorage(StorageConfig())
    return file_storage


# Pydantic models
class FileUploadResponse(BaseModel):
    id: str
    filename: str
    original_name: str
    mime_type: str
    size: int
    url: str
    category: str


class FileListResponse(BaseModel):
    files: List[dict]
    total: int
    limit: int
    offset: int


class FileStoreFromURLRequest(BaseModel):
    url: str
    filename: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None


class FileUpdateRequest(BaseModel):
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None


class StorageStatsResponse(BaseModel):
    total_files: int
    total_size: int
    by_category: dict
    by_mime_type: dict


# Create router
router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    category: Optional[str] = Form(None),
    tags: Optional[str] = Form(None)  # Comma-separated tags
):
    """
    Upload a file.
    
    - **file**: The file to upload
    - **category**: Optional category (images, documents, audio, video, generated)
    - **tags**: Optional comma-separated tags
    """
    storage = get_file_storage()
    
    try:
        # Read file content
        content = await file.read()
        
        # Parse tags
        tag_list = [t.strip() for t in tags.split(",")] if tags else []
        
        # Store file
        metadata = await storage.store(
            data=content,
            filename=file.filename,
            category=category,
            tags=tag_list
        )
        
        return FileUploadResponse(
            id=metadata.id,
            filename=metadata.filename,
            original_name=metadata.original_name,
            mime_type=metadata.mime_type,
            size=metadata.size,
            url=metadata.url,
            category=metadata.category
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Upload failed")


@router.post("/upload-base64", response_model=FileUploadResponse)
async def upload_file_base64(
    filename: str,
    data: str,  # Base64 encoded
    category: Optional[str] = None,
    tags: Optional[List[str]] = None
):
    """
    Upload a file using base64 encoding.
    
    Useful for API integrations and generated content.
    """
    storage = get_file_storage()
    
    try:
        # Decode base64
        content = base64.b64decode(data)
        
        # Store file
        metadata = await storage.store(
            data=content,
            filename=filename,
            category=category,
            tags=tags
        )
        
        return FileUploadResponse(
            id=metadata.id,
            filename=metadata.filename,
            original_name=metadata.original_name,
            mime_type=metadata.mime_type,
            size=metadata.size,
            url=metadata.url,
            category=metadata.category
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Upload failed")


@router.post("/from-url", response_model=FileUploadResponse)
async def store_from_url(request: FileStoreFromURLRequest):
    """
    Store a file from a URL.
    
    Downloads the file and stores it locally.
    """
    storage = get_file_storage()
    
    try:
        metadata = await storage.store_from_url(
            url=request.url,
            filename=request.filename,
            category=request.category,
            tags=request.tags
        )
        
        return FileUploadResponse(
            id=metadata.id,
            filename=metadata.filename,
            original_name=metadata.original_name,
            mime_type=metadata.mime_type,
            size=metadata.size,
            url=metadata.url,
            category=metadata.category
        )
        
    except Exception as e:
        logger.error(f"Store from URL failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{file_id}")
async def get_file(file_id: str):
    """
    Download a file by ID.
    """
    storage = get_file_storage()
    
    try:
        data, metadata = await storage.retrieve(file_id)
        
        return Response(
            content=data,
            media_type=metadata.mime_type,
            headers={
                "Content-Disposition": f'inline; filename="{metadata.original_name}"',
                "Content-Length": str(metadata.size)
            }
        )
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Retrieve failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Retrieve failed")


@router.get("/{file_id}/download")
async def download_file(file_id: str):
    """
    Download a file as attachment.
    """
    storage = get_file_storage()
    
    try:
        data, metadata = await storage.retrieve(file_id)
        
        return Response(
            content=data,
            media_type=metadata.mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{metadata.original_name}"',
                "Content-Length": str(metadata.size)
            }
        )
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")


@router.get("/{file_id}/metadata")
async def get_file_metadata(file_id: str):
    """
    Get file metadata without downloading content.
    """
    storage = get_file_storage()
    
    metadata = storage.get_metadata(file_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    return metadata.to_dict()


@router.patch("/{file_id}")
async def update_file(file_id: str, request: FileUpdateRequest):
    """
    Update file metadata (tags, custom metadata).
    """
    storage = get_file_storage()
    
    metadata = await storage.update_metadata(
        file_id=file_id,
        tags=request.tags,
        metadata=request.metadata
    )
    
    if not metadata:
        raise HTTPException(status_code=404, detail="File not found")
    
    return metadata.to_dict()


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """
    Delete a file.
    """
    storage = get_file_storage()
    
    if await storage.delete(file_id):
        return {"message": "File deleted", "id": file_id}
    
    raise HTTPException(status_code=404, detail="File not found")


@router.get("", response_model=FileListResponse)
async def list_files(
    category: Optional[str] = Query(None, description="Filter by category"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """
    List files with optional filtering.
    """
    storage = get_file_storage()
    
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    
    files = storage.list_files(
        category=category,
        tags=tag_list,
        limit=limit,
        offset=offset
    )
    
    return FileListResponse(
        files=[f.to_dict() for f in files],
        total=len(storage._metadata_index),
        limit=limit,
        offset=offset
    )


@router.get("/stats/summary", response_model=StorageStatsResponse)
async def get_storage_stats():
    """
    Get storage statistics.
    """
    storage = get_file_storage()
    return storage.get_stats()


@router.post("/cleanup")
async def cleanup_temp_files(max_age_hours: int = 24):
    """
    Clean up temporary files older than specified age.
    """
    storage = get_file_storage()
    storage.cleanup_temp(max_age_hours=max_age_hours)
    return {"message": f"Cleaned up temp files older than {max_age_hours} hours"}
