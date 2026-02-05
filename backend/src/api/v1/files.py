"""File API routes (v1)."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import List, Optional

from ...core.services import FileService
from .dependencies import get_file_service
from .schemas import FileUploadResponse, FileMetadataResponse, FileListResponse, SuccessResponse

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    category: str = Form(default="documents"),
    tags: str = Form(default="[]"),
    user_id: str = Form(default="default"),
    file_service: FileService = Depends(get_file_service)
):
    """Upload a file."""
    try:
        import json
        tags_list = json.loads(tags) if isinstance(tags, str) else tags
        
        # Read file data
        file_data = await file.read()
        
        # Call service
        file_record = await file_service.save_file(
            file_data=file_data,
            filename=file.filename,
            category=category,
            tags=tags_list,
            user_id=user_id
        )
        
        return FileUploadResponse(
            file_id=file_record.id,
            name=file_record.name,
            category=file_record.category,
            size=file_record.metadata.size,
            mime_type=file_record.metadata.mime_type,
            checksum=file_record.metadata.checksum
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{file_id}", response_model=FileMetadataResponse)
async def get_file_metadata(
    file_id: str,
    file_service: FileService = Depends(get_file_service)
):
    """Get file metadata."""
    file_record = await file_service.get_file(file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileMetadataResponse(
        id=file_record.id,
        name=file_record.name,
        path=file_record.path,
        category=file_record.category,
        size=file_record.metadata.size,
        mime_type=file_record.metadata.mime_type,
        tags=file_record.tags,
        created_at=file_record.created_at,
        updated_at=file_record.updated_at
    )


@router.get("/", response_model=FileListResponse)
async def list_files(
    user_id: str = "default",
    category: Optional[str] = None,
    tags: Optional[str] = None,
    file_service: FileService = Depends(get_file_service)
):
    """List files with optional filters."""
    try:
        import json
        tags_list = json.loads(tags) if tags else None
        
        files = await file_service.list_files(
            user_id=user_id,
            category=category,
            tags=tags_list
        )
        
        file_responses = [
            FileMetadataResponse(
                id=f.id,
                name=f.name,
                path=f.path,
                category=f.category,
                size=f.metadata.size,
                mime_type=f.metadata.mime_type,
                tags=f.tags,
                created_at=f.created_at,
                updated_at=f.updated_at
            )
            for f in files
        ]
        
        return FileListResponse(
            files=file_responses,
            total=len(file_responses)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{file_id}", response_model=SuccessResponse)
async def delete_file(
    file_id: str,
    file_service: FileService = Depends(get_file_service)
):
    """Delete a file."""
    success = await file_service.delete_file(file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    
    return SuccessResponse(
        success=True,
        message=f"File {file_id} deleted"
    )
