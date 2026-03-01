"""
Files API
=========

Endpoints for file upload, download, management, and AI analysis.
"""

import logging
import base64
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from ..storage import FileStorage, StorageConfig
from ..storage.universal_capture import get_file_capture as get_universal_capture
from ..tools.file_analysis import FileAnalyzer
from ..core.memory_agent import MemoryAgent

logger = logging.getLogger(__name__)

# Global instances
file_storage: Optional[FileStorage] = None
file_analyzer: Optional[FileAnalyzer] = None
memory_agent: Optional[MemoryAgent] = None


def get_file_storage() -> FileStorage:
    """Get or create file storage instance."""
    global file_storage
    if file_storage is None:
        file_storage = FileStorage(StorageConfig())
    return file_storage


def get_memory_agent() -> MemoryAgent:
    """Get or create memory agent instance."""
    global memory_agent
    if memory_agent is None:
        memory_agent = MemoryAgent()
    return memory_agent


def get_file_analyzer() -> FileAnalyzer:
    """Get or create file analyzer instance with AI clients."""
    global file_analyzer
    if file_analyzer is None:
        import os
        from openai import OpenAI, AsyncOpenAI
        from anthropic import AsyncAnthropic
        
        openai_client = None
        openai_sync_client = None
        anthropic_client = None
        
        if os.getenv("OPENAI_API_KEY"):
            openai_client = AsyncOpenAI()
            openai_sync_client = OpenAI()  # Sync client for audio
        if os.getenv("ANTHROPIC_API_KEY"):
            anthropic_client = AsyncAnthropic()
        
        file_analyzer = FileAnalyzer(
            openai_client=openai_client,
            openai_sync_client=openai_sync_client,
            anthropic_client=anthropic_client
        )
    return file_analyzer


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


class FileAnalysisRequest(BaseModel):
    context: Optional[str] = None
    detail_level: str = "comprehensive"  # "quick", "standard", "comprehensive"


class FileAnalysisResponse(BaseModel):
    success: bool
    filename: str
    category: str
    mime_type: str
    size: int
    summary: str
    key_points: List[str] = []
    entities: List[str] = []
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
    error: Optional[str] = None


class FileUploadWithAnalysisResponse(BaseModel):
    id: str
    filename: str
    original_name: str
    mime_type: str
    size: int
    url: str
    category: str
    analysis: Optional[FileAnalysisResponse] = None


class SaveTextRequest(BaseModel):
    content: str
    filename: str
    category: Optional[str] = "code"
    tags: Optional[List[str]] = None


# Create router
router = APIRouter(prefix="/files", tags=["files"])


@router.post("/save-text", response_model=FileUploadResponse)
async def save_text_content(request: SaveTextRequest):
    """
    Save text content as a file (for artifacts/code snippets).
    
    - **content**: The text content to save
    - **filename**: Desired filename
    - **category**: Optional category (default: code)
    - **tags**: Optional tags
    """
    storage = get_file_storage()
    
    try:
        # Convert text to bytes
        content_bytes = request.content.encode('utf-8')
        
        # Store file
        metadata = await storage.store(
            data=content_bytes,
            filename=request.filename,
            category=request.category or "code",
            tags=request.tags or []
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
        logger.error(f"Save text failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Save failed")


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


@router.post("/upload-and-analyze", response_model=FileUploadWithAnalysisResponse)
async def upload_and_analyze_file(
    file: UploadFile = File(...),
    category: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    analyze: bool = Form(True),
    context: Optional[str] = Form(None),
    detail_level: str = Form("comprehensive")
):
    """
    Upload a file and optionally analyze it with AI.
    
    - **file**: The file to upload
    - **category**: Optional category (images, documents, audio, video, generated)
    - **tags**: Optional comma-separated tags
    - **analyze**: Whether to analyze the file (default: True)
    - **context**: Additional context to help with analysis
    - **detail_level**: "quick", "standard", or "comprehensive"
    
    The analysis will understand:
    - **Images**: Visual content, objects, text (OCR), style, composition
    - **Audio**: Transcription, language, duration
    - **Video**: Duration, resolution, codec info
    - **Documents**: Text extraction, summarization, key points
    - **Code**: Language, functions, dependencies, purpose
    - **Data**: Structure, schema, content preview
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
        
        analysis_result = None
        
        # Analyze if requested
        if analyze:
            try:
                analyzer = get_file_analyzer()
                analysis = await analyzer.analyze(
                    file_data=content,
                    filename=file.filename,
                    mime_type=metadata.mime_type,
                    context=context,
                    detail_level=detail_level
                )
                
                analysis_result = FileAnalysisResponse(
                    success=analysis.get("success", False),
                    filename=analysis.get("filename", file.filename),
                    category=analysis.get("category", "unknown"),
                    mime_type=analysis.get("mime_type", ""),
                    size=analysis.get("size", len(content)),
                    summary=analysis.get("summary", ""),
                    key_points=analysis.get("key_points", []),
                    entities=analysis.get("entities", []),
                    tags=analysis.get("analysis", {}).get("tags", []),
                    metadata=analysis.get("metadata", {}),
                    error=analysis.get("error")
                )
                
                # Store analysis in file metadata
                await storage.update_metadata(
                    file_id=metadata.id,
                    metadata={
                        "analysis": {
                            "summary": analysis_result.summary,
                            "key_points": analysis_result.key_points,
                            "entities": analysis_result.entities,
                            "tags": analysis_result.tags,
                        }
                    }
                )
                
                # Store in memory for long-term context
                if analysis_result.success:
                    try:
                        mem = get_memory_agent()
                        await mem.store_file_analysis(
                            file_id=metadata.id,
                            filename=metadata.original_name,
                            category=analysis_result.category,
                            mime_type=metadata.mime_type,
                            summary=analysis_result.summary,
                            key_points=analysis_result.key_points,
                            entities=analysis_result.entities,
                            tags=analysis_result.tags
                        )
                        logger.info(f"Stored file analysis in memory: {metadata.id}")
                    except Exception as mem_err:
                        logger.warning(f"Failed to store in memory: {mem_err}")
                
            except Exception as e:
                logger.warning(f"Analysis failed but upload succeeded: {e}")
                analysis_result = FileAnalysisResponse(
                    success=False,
                    filename=file.filename,
                    category=category or "unknown",
                    mime_type=metadata.mime_type,
                    size=len(content),
                    summary="Analysis failed",
                    error=str(e)
                )
        
        return FileUploadWithAnalysisResponse(
            id=metadata.id,
            filename=metadata.filename,
            original_name=metadata.original_name,
            mime_type=metadata.mime_type,
            size=metadata.size,
            url=metadata.url,
            category=metadata.category,
            analysis=analysis_result
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Upload and analyze failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Upload failed")


@router.post("/analyze/{file_id}", response_model=FileAnalysisResponse)
async def analyze_file(
    file_id: str,
    request: FileAnalysisRequest = FileAnalysisRequest()
):
    """
    Analyze an already-uploaded file with AI.
    
    - **file_id**: ID of the uploaded file
    - **context**: Additional context to help with analysis
    - **detail_level**: "quick", "standard", or "comprehensive"
    
    Returns comprehensive analysis based on file type.
    """
    storage = get_file_storage()
    analyzer = get_file_analyzer()
    
    try:
        # Retrieve file
        data, metadata = await storage.retrieve(file_id)
        if not data:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Analyze
        analysis = await analyzer.analyze(
            file_data=data,
            filename=metadata.original_name,
            mime_type=metadata.mime_type,
            context=request.context,
            detail_level=request.detail_level
        )
        
        response = FileAnalysisResponse(
            success=analysis.get("success", False),
            filename=analysis.get("filename", metadata.original_name),
            category=analysis.get("category", "unknown"),
            mime_type=analysis.get("mime_type", metadata.mime_type),
            size=analysis.get("size", metadata.size),
            summary=analysis.get("summary", ""),
            key_points=analysis.get("key_points", []),
            entities=analysis.get("entities", []),
            tags=analysis.get("analysis", {}).get("tags", []),
            metadata=analysis.get("metadata", {}),
            error=analysis.get("error")
        )
        
        # Store analysis in file metadata
        await storage.update_metadata(
            file_id=file_id,
            metadata={
                "analysis": {
                    "summary": response.summary,
                    "key_points": response.key_points,
                    "entities": response.entities,
                    "tags": response.tags,
                }
            }
        )
        
        # Store in memory for long-term context
        if response.success:
            try:
                mem = get_memory_agent()
                await mem.store_file_analysis(
                    file_id=file_id,
                    filename=metadata.original_name,
                    category=response.category,
                    mime_type=metadata.mime_type,
                    summary=response.summary,
                    key_points=response.key_points,
                    entities=response.entities,
                    tags=response.tags
                )
                logger.info(f"Stored file analysis in memory: {file_id}")
            except Exception as mem_err:
                logger.warning(f"Failed to store in memory: {mem_err}")
        
        return response
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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


# ============================================================================
# LIST ENDPOINTS (must come before /{file_id} to avoid route conflicts)
# ============================================================================

@router.get("", response_model=FileListResponse)
async def list_files(
    category: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),  # Comma-separated
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """
    List all files with optional filtering.
    """
    storage = get_file_storage()
    
    # Parse tags
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    
    files = storage.list_files(
        category=category,
        tags=tag_list,
        limit=limit,
        offset=offset
    )
    
    stats = storage.get_stats()
    total = stats.total_files if hasattr(stats, 'total_files') else stats.get('total_files', len(files))
    
    return FileListResponse(
        files=[f.to_dict() for f in files],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/list", response_model=FileListResponse)
async def list_files_alias(
    category: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """Alias for list_files (backwards compatibility)."""
    return await list_files(category=category, tags=tags, limit=limit, offset=offset)


@router.get("/stats/summary", response_model=StorageStatsResponse)
async def get_storage_stats():
    """Get storage statistics."""
    storage = get_file_storage()
    return storage.get_stats()


@router.get("/captured")
async def list_captured_files_early(
    category: Optional[str] = Query(None, description="Filter by category"),
    source_tool: Optional[str] = Query(None, description="Filter by source tool"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    limit: int = Query(100, ge=1, le=500)
):
    """List captured files (early route to avoid conflict with /{file_id})."""
    capture = get_universal_capture()
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    
    files = capture.list_files(
        category=category,
        source_tool=source_tool,
        tags=tag_list,
        limit=limit
    )
    
    return {"files": files, "total": len(files), "limit": limit}


@router.get("/download-all")
async def download_all_files_as_zip(category: Optional[str] = None):
    """
    Download all files as a ZIP archive.
    
    Optionally filter by category: images, videos, audio, documents, code, 3d_models, mockups
    """
    import io
    import zipfile
    from datetime import datetime
    
    storage = get_file_storage()
    
    try:
        # Get all files
        files = storage.list_files(category=category)
        
        if not files:
            raise HTTPException(status_code=404, detail="No files to download")
        
        # Create in-memory zip file
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_meta in files:
                try:
                    # FileMetadata is a dataclass — use attribute access
                    file_id = file_meta.id if hasattr(file_meta, 'id') else file_meta.get('id')
                    original_name = getattr(file_meta, 'original_name', None) or (file_meta.get('original_name') if isinstance(file_meta, dict) else file_id)
                    file_category = getattr(file_meta, 'category', None) or (file_meta.get('category', 'other') if isinstance(file_meta, dict) else 'other')
                    
                    # Get file data
                    data, metadata = await storage.retrieve(file_id)
                    
                    # Organize in folders by category
                    zip_path = f"{file_category}/{original_name}"
                    zip_file.writestr(zip_path, data)
                    
                except Exception as e:
                    logger.warning(f"Skipping file in zip: {e}")
                    continue
        
        zip_buffer.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        category_suffix = f"_{category}" if category else ""
        filename = f"otto_files{category_suffix}_{timestamp}.zip"
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download all failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create zip archive")


# ============================================================================
# FILE BY ID ENDPOINTS (must come after specific routes)
# ============================================================================

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


@router.post("/cleanup")
async def cleanup_temp_files(max_age_hours: int = 24):
    """
    Clean up temporary files older than specified age.
    """
    storage = get_file_storage()
    storage.cleanup_temp(max_age_hours=max_age_hours)
    return {"message": f"Cleaned up temp files older than {max_age_hours} hours"}


# ============================================================================
# UNIVERSAL FILE CAPTURE ADDITIONAL ENDPOINTS
# ============================================================================

@router.get("/captured/{file_id}")
async def get_captured_file(file_id: str):
    """Get details of a captured file."""
    from ..storage.universal_capture import get_file_capture
    
    capture = get_file_capture()
    file_data = capture.get_file(file_id)
    
    if not file_data:
        raise HTTPException(status_code=404, detail="Captured file not found")
    
    return file_data


@router.get("/captured/stats/summary")
async def get_capture_stats():
    """
    Get statistics about all captured files.
    Shows breakdown by category, tool, and total size.
    """
    from ..storage.universal_capture import get_file_capture
    
    capture = get_file_capture()
    return capture.get_stats()


class CaptureURLRequest(BaseModel):
    url: str
    category: Optional[str] = None
    source_tool: str = "manual"
    tags: Optional[List[str]] = None
    prompt: Optional[str] = None
    session_id: Optional[str] = None


@router.post("/capture/url")
async def capture_from_url(request: CaptureURLRequest):
    """
    Manually capture a file from URL.
    Use this to save any external file to the organized storage.
    """
    from ..storage.universal_capture import get_file_capture
    
    capture = get_file_capture()
    
    try:
        captured = await capture.capture_from_url(
            url=request.url,
            source_tool=request.source_tool,
            operation="manual_capture",
            prompt=request.prompt,
            tags=request.tags,
            session_id=request.session_id
        )
        
        return {
            "success": True,
            "file_id": captured.id,
            "local_path": captured.local_path,
            "category": captured.category,
            "filename": captured.filename,
            "size": captured.size
        }
    except Exception as e:
        logger.error(f"Capture from URL failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# FILE CONTEXT RECALL (for AI memory integration)
# ============================================================================

class FileContextQuery(BaseModel):
    query: str
    file_types: Optional[List[str]] = None  # Filter by category: image, audio, video, document, code, data
    limit: int = 5


@router.post("/recall-context")
async def recall_file_context(request: FileContextQuery):
    """
    Recall relevant file context from memory based on a query.
    
    This enables the AI to remember and reference previously analyzed files.
    Use this to find relevant file information when answering questions.
    
    - **query**: Natural language query to search for relevant files
    - **file_types**: Optional filter by file categories
    - **limit**: Maximum number of results
    """
    try:
        mem = get_memory_agent()
        contexts = await mem.recall_file_context(
            query=request.query,
            file_types=request.file_types,
            k=request.limit
        )
        
        return {
            "success": True,
            "results": contexts,
            "count": len(contexts)
        }
        
    except Exception as e:
        logger.error(f"File context recall failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
