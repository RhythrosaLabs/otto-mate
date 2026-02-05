"""
Universal File Capture System
=============================

Automatically captures and organizes ALL generated files:
- Images (AI-generated, screenshots, uploads)
- Videos (AI-generated, processed)
- Audio (music, speech, sound effects)
- Documents (PDFs, reports, exports)
- 3D Models (meshes, textures)
- Data files (JSON, CSV, exports)

This module hooks into the execution pipeline to capture every file.
"""

import logging
import asyncio
import aiohttp
import aiofiles
import hashlib
import mimetypes
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field
import json
import uuid

logger = logging.getLogger(__name__)


# File type mappings
FILE_CATEGORIES = {
    # Images
    "image/png": "images",
    "image/jpeg": "images",
    "image/jpg": "images",
    "image/gif": "images",
    "image/webp": "images",
    "image/svg+xml": "images",
    "image/bmp": "images",
    "image/tiff": "images",
    
    # Videos
    "video/mp4": "videos",
    "video/webm": "videos",
    "video/quicktime": "videos",
    "video/x-msvideo": "videos",
    "video/mpeg": "videos",
    
    # Audio
    "audio/mpeg": "audio",
    "audio/mp3": "audio",
    "audio/wav": "audio",
    "audio/x-wav": "audio",
    "audio/ogg": "audio",
    "audio/flac": "audio",
    "audio/aac": "audio",
    "audio/m4a": "audio",
    
    # Documents
    "application/pdf": "documents",
    "application/msword": "documents",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "documents",
    "text/plain": "documents",
    "text/markdown": "documents",
    "text/html": "documents",
    
    # Data
    "application/json": "data",
    "text/csv": "data",
    "application/vnd.ms-excel": "data",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "data",
    
    # 3D Models
    "model/gltf-binary": "3d_models",
    "model/gltf+json": "3d_models",
    "model/obj": "3d_models",
    "application/octet-stream": "3d_models",  # Often used for .glb, .obj
}

# Extension to category mapping (fallback)
EXT_CATEGORIES = {
    # Images
    ".png": "images", ".jpg": "images", ".jpeg": "images", ".gif": "images",
    ".webp": "images", ".svg": "images", ".bmp": "images", ".tiff": "images",
    
    # Videos
    ".mp4": "videos", ".webm": "videos", ".mov": "videos", ".avi": "videos",
    ".mkv": "videos", ".mpeg": "videos",
    
    # Audio
    ".mp3": "audio", ".wav": "audio", ".ogg": "audio", ".flac": "audio",
    ".aac": "audio", ".m4a": "audio",
    
    # Documents
    ".pdf": "documents", ".doc": "documents", ".docx": "documents",
    ".txt": "documents", ".md": "documents", ".html": "documents",
    ".rtf": "documents",
    
    # Data
    ".json": "data", ".csv": "data", ".xlsx": "data", ".xls": "data",
    ".xml": "data", ".yaml": "data", ".yml": "data",
    
    # 3D Models
    ".glb": "3d_models", ".gltf": "3d_models", ".obj": "3d_models",
    ".fbx": "3d_models", ".stl": "3d_models", ".ply": "3d_models",
    ".usdz": "3d_models",
    
    # Code/Scripts
    ".py": "code", ".js": "code", ".ts": "code", ".html": "code",
    ".css": "code", ".sql": "code",
}


@dataclass
class CapturedFile:
    """Represents a captured file."""
    id: str
    original_url: Optional[str]
    local_path: str
    filename: str
    category: str
    mime_type: str
    size: int
    checksum: str
    source_tool: str
    source_operation: str
    prompt: Optional[str]
    metadata: Dict[str, Any]
    created_at: datetime
    session_id: Optional[str]
    tags: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "original_url": self.original_url,
            "local_path": self.local_path,
            "filename": self.filename,
            "category": self.category,
            "mime_type": self.mime_type,
            "size": self.size,
            "checksum": self.checksum,
            "source_tool": self.source_tool,
            "source_operation": self.source_operation,
            "prompt": self.prompt,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "session_id": self.session_id,
            "tags": self.tags
        }


class UniversalFileCapture:
    """
    Captures and organizes ALL generated files automatically.
    """
    
    def __init__(self, base_path: str = "./data/files"):
        self.base_path = Path(base_path)
        self.index_path = self.base_path / ".capture_index.json"
        self.captured_files: Dict[str, CapturedFile] = {}
        
        # Initialize directories
        self._init_directories()
        self._load_index()
        
        logger.info(f"✓ Universal File Capture initialized: {self.base_path}")
    
    def _init_directories(self):
        """Create all category directories."""
        categories = [
            "images", "images/generated", "images/uploads", "images/screenshots",
            "videos", "videos/generated", "videos/processed",
            "audio", "audio/music", "audio/speech", "audio/effects",
            "documents", "documents/reports", "documents/exports",
            "3d_models",
            "data",
            "code",
            "mockups",
            "temp"
        ]
        
        for category in categories:
            (self.base_path / category).mkdir(parents=True, exist_ok=True)
    
    def _load_index(self):
        """Load capture index from disk."""
        if self.index_path.exists():
            try:
                with open(self.index_path, "r") as f:
                    data = json.load(f)
                    # We just store the metadata, not reconstruct objects
                    self.captured_files = data
                logger.info(f"Loaded {len(self.captured_files)} captured files from index")
            except Exception as e:
                logger.error(f"Failed to load capture index: {e}")
                self.captured_files = {}
    
    def _save_index(self):
        """Save capture index to disk."""
        try:
            # Convert CapturedFile objects to dicts if needed
            data = {}
            for k, v in self.captured_files.items():
                if isinstance(v, CapturedFile):
                    data[k] = v.to_dict()
                else:
                    data[k] = v
            
            with open(self.index_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save capture index: {e}")
    
    def _get_category(self, mime_type: str, filename: str, url: str = None) -> str:
        """Determine file category from mime type, filename, or URL."""
        # First try mime type
        if mime_type and mime_type in FILE_CATEGORIES:
            return FILE_CATEGORIES[mime_type]
        
        # Try extension
        ext = Path(filename).suffix.lower() if filename else ""
        if ext in EXT_CATEGORIES:
            return EXT_CATEGORIES[ext]
        
        # Try to infer from URL
        if url:
            url_lower = url.lower()
            if any(x in url_lower for x in ["replicate", "flux", "dall-e", "midjourney", "stable-diffusion"]):
                return "images/generated"
            if any(x in url_lower for x in ["runway", "kling", "video"]):
                return "videos/generated"
            if any(x in url_lower for x in ["musicgen", "bark", "audio"]):
                return "audio"
        
        return "temp"
    
    def _generate_filename(self, original_name: str, category: str) -> str:
        """Generate unique organized filename."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        
        # Get extension
        ext = Path(original_name).suffix.lower() if original_name else ""
        if not ext:
            # Infer extension from category
            ext_map = {
                "images": ".png",
                "videos": ".mp4",
                "audio": ".mp3",
                "documents": ".txt",
                "3d_models": ".glb",
                "data": ".json"
            }
            base_cat = category.split("/")[0]
            ext = ext_map.get(base_cat, ".bin")
        
        # Clean original name for use in filename
        clean_name = re.sub(r'[^\w\-]', '_', Path(original_name).stem if original_name else "file")[:30]
        
        return f"{timestamp}_{clean_name}_{unique_id}{ext}"
    
    async def capture_from_url(
        self,
        url: str,
        source_tool: str,
        operation: str = "generate",
        prompt: str = None,
        filename: str = None,
        session_id: str = None,
        metadata: Dict[str, Any] = None,
        tags: List[str] = None
    ) -> CapturedFile:
        """
        Download and capture a file from URL.
        
        Args:
            url: URL to download from
            source_tool: Name of the tool that generated this
            operation: Type of operation (generate, process, upload)
            prompt: The prompt used (for AI-generated content)
            filename: Optional custom filename
            session_id: Current session ID
            metadata: Additional metadata
            tags: Tags for organization
        """
        logger.info(f"📥 Capturing file from URL: {url[:100]}...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=120)) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to download: HTTP {response.status}")
                    
                    content = await response.read()
                    content_type = response.headers.get("Content-Type", "").split(";")[0]
                    
                    # Try to get filename from headers
                    if not filename:
                        cd = response.headers.get("Content-Disposition", "")
                        if "filename=" in cd:
                            filename = cd.split("filename=")[1].strip('"\'')
                        else:
                            # Extract from URL
                            filename = url.split("/")[-1].split("?")[0]
                            if not filename or len(filename) < 3:
                                filename = f"file_{uuid.uuid4().hex[:8]}"
                    
                    return await self.capture_bytes(
                        data=content,
                        filename=filename,
                        mime_type=content_type,
                        source_tool=source_tool,
                        operation=operation,
                        prompt=prompt,
                        original_url=url,
                        session_id=session_id,
                        metadata=metadata,
                        tags=tags
                    )
                    
        except Exception as e:
            logger.error(f"Failed to capture from URL: {e}")
            raise
    
    async def capture_bytes(
        self,
        data: bytes,
        filename: str,
        mime_type: str = None,
        source_tool: str = "unknown",
        operation: str = "save",
        prompt: str = None,
        original_url: str = None,
        session_id: str = None,
        metadata: Dict[str, Any] = None,
        tags: List[str] = None
    ) -> CapturedFile:
        """
        Capture file from bytes.
        """
        # Determine mime type if not provided
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(filename)
            mime_type = mime_type or "application/octet-stream"
        
        # Get category
        category = self._get_category(mime_type, filename, original_url)
        
        # Enhance category based on source tool
        if "replicate" in source_tool.lower() or "flux" in source_tool.lower():
            if category == "images":
                category = "images/generated"
            elif category == "videos":
                category = "videos/generated"
        elif "screenshot" in source_tool.lower():
            category = "images/screenshots"
        elif "upload" in operation.lower():
            if category == "images":
                category = "images/uploads"
        
        # Generate filename
        stored_filename = self._generate_filename(filename, category)
        
        # Calculate checksum
        checksum = hashlib.sha256(data).hexdigest()
        
        # Check for duplicates
        for existing_id, existing in self.captured_files.items():
            existing_checksum = existing.get("checksum") if isinstance(existing, dict) else existing.checksum
            if existing_checksum == checksum:
                logger.info(f"File already captured: {existing_id}")
                if isinstance(existing, dict):
                    return CapturedFile(**{**existing, "created_at": datetime.fromisoformat(existing["created_at"])})
                return existing
        
        # Save file
        file_path = self.base_path / category / stored_filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(data)
        
        # Create capture record
        file_id = uuid.uuid4().hex
        captured = CapturedFile(
            id=file_id,
            original_url=original_url,
            local_path=str(file_path),
            filename=stored_filename,
            category=category,
            mime_type=mime_type,
            size=len(data),
            checksum=checksum,
            source_tool=source_tool,
            source_operation=operation,
            prompt=prompt,
            metadata=metadata or {},
            created_at=datetime.now(),
            session_id=session_id,
            tags=tags or []
        )
        
        # Add to index
        self.captured_files[file_id] = captured.to_dict()
        self._save_index()
        
        logger.info(f"✓ Captured {category}/{stored_filename} ({len(data)} bytes)")
        
        return captured
    
    async def capture_from_tool_result(
        self,
        result: Dict[str, Any],
        tool_name: str,
        session_id: str = None,
        prompt: str = None
    ) -> Optional[CapturedFile]:
        """
        Automatically capture files from tool execution results.
        Looks for URLs, file paths, or binary data in the result.
        """
        if not isinstance(result, dict):
            return None
        
        # Look for URLs to capture
        url_keys = ["url", "image_url", "video_url", "audio_url", "output_url", 
                   "result_url", "file_url", "download_url", "output"]
        
        for key in url_keys:
            url = result.get(key)
            if url and isinstance(url, str) and url.startswith("http"):
                try:
                    return await self.capture_from_url(
                        url=url,
                        source_tool=tool_name,
                        operation="generate",
                        prompt=prompt or result.get("prompt"),
                        session_id=session_id,
                        metadata={"tool_result": result},
                        tags=[tool_name, "auto-captured"]
                    )
                except Exception as e:
                    logger.warning(f"Could not auto-capture from {key}: {e}")
        
        # Check for list of URLs (some tools return multiple outputs)
        for key in ["urls", "images", "outputs", "results"]:
            urls = result.get(key)
            if isinstance(urls, list):
                captured = []
                for url in urls[:10]:  # Limit to 10
                    if isinstance(url, str) and url.startswith("http"):
                        try:
                            cap = await self.capture_from_url(
                                url=url,
                                source_tool=tool_name,
                                operation="generate",
                                prompt=prompt,
                                session_id=session_id,
                                tags=[tool_name, "auto-captured", "batch"]
                            )
                            captured.append(cap)
                        except:
                            pass
                if captured:
                    return captured[0]  # Return first one
        
        return None
    
    def list_files(
        self,
        category: str = None,
        source_tool: str = None,
        session_id: str = None,
        tags: List[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List captured files with optional filters."""
        results = []
        
        for file_id, file_data in self.captured_files.items():
            if isinstance(file_data, CapturedFile):
                file_data = file_data.to_dict()
            
            # Apply filters
            if category and not file_data.get("category", "").startswith(category):
                continue
            if source_tool and file_data.get("source_tool") != source_tool:
                continue
            if session_id and file_data.get("session_id") != session_id:
                continue
            if tags:
                file_tags = file_data.get("tags", [])
                if not any(t in file_tags for t in tags):
                    continue
            
            results.append(file_data)
            
            if len(results) >= limit:
                break
        
        # Sort by created_at descending
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return results
    
    def get_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get file by ID."""
        file_data = self.captured_files.get(file_id)
        if isinstance(file_data, CapturedFile):
            return file_data.to_dict()
        return file_data
    
    def get_stats(self) -> Dict[str, Any]:
        """Get capture statistics."""
        stats = {
            "total_files": len(self.captured_files),
            "by_category": {},
            "by_tool": {},
            "total_size": 0
        }
        
        for file_data in self.captured_files.values():
            if isinstance(file_data, CapturedFile):
                file_data = file_data.to_dict()
            
            # By category
            cat = file_data.get("category", "unknown")
            base_cat = cat.split("/")[0]
            stats["by_category"][base_cat] = stats["by_category"].get(base_cat, 0) + 1
            
            # By tool
            tool = file_data.get("source_tool", "unknown")
            stats["by_tool"][tool] = stats["by_tool"].get(tool, 0) + 1
            
            # Size
            stats["total_size"] += file_data.get("size", 0)
        
        stats["total_size_mb"] = round(stats["total_size"] / (1024 * 1024), 2)
        
        return stats


# Global instance
_file_capture: Optional[UniversalFileCapture] = None


def get_file_capture() -> UniversalFileCapture:
    """Get global file capture instance."""
    global _file_capture
    if _file_capture is None:
        _file_capture = UniversalFileCapture()
    return _file_capture


async def auto_capture_result(
    result: Dict[str, Any],
    tool_name: str,
    session_id: str = None,
    prompt: str = None
) -> Dict[str, Any]:
    """
    Automatically capture files from any tool result.
    Call this after every tool execution to ensure files are saved.
    
    Returns the result with capture info added.
    """
    capture = get_file_capture()
    
    try:
        captured = await capture.capture_from_tool_result(
            result=result,
            tool_name=tool_name,
            session_id=session_id,
            prompt=prompt
        )
        
        if captured:
            result["_captured"] = {
                "file_id": captured.id,
                "local_path": captured.local_path,
                "category": captured.category
            }
            logger.info(f"✓ Auto-captured file from {tool_name}: {captured.filename}")
    except Exception as e:
        logger.warning(f"Auto-capture failed for {tool_name}: {e}")
    
    return result
