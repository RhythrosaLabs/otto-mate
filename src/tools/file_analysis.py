"""
File Analysis Tools
===================

Analyze uploaded files of any type (images, videos, audio, documents, etc.)
and store the analysis in memory context for future reference.
"""

import logging
import base64
import mimetypes
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class FileAnalyzer:
    """
    Universal file analyzer supporting multiple media types.
    Uses appropriate AI models based on file type.
    """
    
    def __init__(self, openai_client=None, openai_sync_client=None, anthropic_client=None, replicate_client=None):
        self.openai = openai_client  # Async client for chat/vision
        self.openai_sync = openai_sync_client  # Sync client for audio transcription
        self.anthropic = anthropic_client
        self.replicate = replicate_client
        
        # File type to analyzer mapping
        self.analyzers = {
            "image": self._analyze_image,
            "video": self._analyze_video,
            "audio": self._analyze_audio,
            "text": self._analyze_text,
            "document": self._analyze_document,
            "code": self._analyze_code,
            "data": self._analyze_data,
        }
        
        # MIME type categories
        self.mime_categories = {
            "image": ["image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml", "image/bmp", "image/tiff"],
            "video": ["video/mp4", "video/webm", "video/quicktime", "video/x-msvideo", "video/mpeg"],
            "audio": ["audio/mpeg", "audio/wav", "audio/ogg", "audio/webm", "audio/mp4", "audio/flac", "audio/aac"],
            "text": ["text/plain", "text/markdown", "text/csv", "text/html", "text/xml"],
            "document": ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        "application/vnd.ms-powerpoint", "application/vnd.openxmlformats-officedocument.presentationml.presentation"],
            "code": ["text/x-python", "application/javascript", "text/x-java", "text/x-c", "text/x-cpp", 
                    "application/json", "application/x-yaml", "text/css"],
            "data": ["application/json", "text/csv", "application/xml", "application/x-yaml"],
        }
    
    def _get_file_category(self, mime_type: str, filename: str) -> str:
        """Determine file category from MIME type and filename."""
        # Check MIME type
        for category, mime_types in self.mime_categories.items():
            if mime_type in mime_types:
                return category
        
        # Fallback to extension
        ext = Path(filename).suffix.lower()
        ext_map = {
            ".py": "code", ".js": "code", ".ts": "code", ".java": "code",
            ".c": "code", ".cpp": "code", ".h": "code", ".css": "code",
            ".html": "text", ".md": "text", ".txt": "text",
            ".json": "data", ".yaml": "data", ".yml": "data", ".csv": "data", ".xml": "data",
            ".pdf": "document", ".doc": "document", ".docx": "document",
            ".xls": "document", ".xlsx": "document", ".ppt": "document", ".pptx": "document",
            ".jpg": "image", ".jpeg": "image", ".png": "image", ".gif": "image", ".webp": "image",
            ".mp4": "video", ".webm": "video", ".mov": "video", ".avi": "video",
            ".mp3": "audio", ".wav": "audio", ".ogg": "audio", ".flac": "audio",
        }
        return ext_map.get(ext, "unknown")
    
    async def analyze(
        self,
        file_data: bytes,
        filename: str,
        mime_type: Optional[str] = None,
        context: Optional[str] = None,
        detail_level: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Analyze a file and return structured analysis.
        
        Args:
            file_data: Raw file bytes
            filename: Original filename
            mime_type: MIME type (auto-detected if not provided)
            context: Additional context for analysis
            detail_level: "quick", "standard", or "comprehensive"
            
        Returns:
            Analysis results with metadata
        """
        # Detect MIME type if not provided
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(filename)
            mime_type = mime_type or "application/octet-stream"
        
        # Determine category
        category = self._get_file_category(mime_type, filename)
        
        logger.info(f"Analyzing file: {filename} (type: {category}, mime: {mime_type})")
        
        # Get appropriate analyzer
        analyzer = self.analyzers.get(category, self._analyze_generic)
        
        try:
            analysis = await analyzer(
                file_data=file_data,
                filename=filename,
                mime_type=mime_type,
                context=context,
                detail_level=detail_level
            )
            
            return {
                "success": True,
                "filename": filename,
                "category": category,
                "mime_type": mime_type,
                "size": len(file_data),
                "analysis": analysis,
                "summary": analysis.get("summary", ""),
                "key_points": analysis.get("key_points", []),
                "entities": analysis.get("entities", []),
                "metadata": analysis.get("metadata", {}),
            }
            
        except Exception as e:
            logger.error(f"Analysis failed for {filename}: {e}", exc_info=True)
            return {
                "success": False,
                "filename": filename,
                "category": category,
                "mime_type": mime_type,
                "size": len(file_data),
                "error": str(e),
                "summary": f"Failed to analyze file: {str(e)}",
            }
    
    async def _analyze_image(
        self,
        file_data: bytes,
        filename: str,
        mime_type: str,
        context: Optional[str] = None,
        detail_level: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Analyze image using vision models."""
        
        # Convert to base64 for API calls
        b64_data = base64.b64encode(file_data).decode()
        data_url = f"data:{mime_type};base64,{b64_data}"
        
        analysis_prompt = f"""Analyze this image in detail. {"Context: " + context if context else ""}

Provide:
1. **Summary**: A comprehensive description of what the image shows
2. **Key Elements**: List the main visual elements, objects, people, text, etc.
3. **Style & Composition**: Describe the visual style, colors, composition
4. **Text/OCR**: Extract any visible text
5. **Context & Purpose**: What appears to be the purpose or context of this image
6. **Tags**: Relevant keywords/tags for this image
7. **Technical Details**: Resolution quality, format observations

Be thorough and specific."""

        if self.anthropic:
            # Use Claude for vision
            try:
                response = await self.anthropic.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=2000,
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": mime_type,
                                    "data": b64_data
                                }
                            },
                            {
                                "type": "text",
                                "text": analysis_prompt
                            }
                        ]
                    }]
                )
                
                analysis_text = response.content[0].text
                
                return self._parse_analysis_response(analysis_text, "image")
                
            except Exception as e:
                logger.warning(f"Claude vision failed: {e}, trying OpenAI")
        
        if self.openai:
            # Use GPT-4 Vision
            try:
                response = await self.openai.chat.completions.create(
                    model="gpt-4o",
                    max_tokens=2000,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": analysis_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": data_url, "detail": "high"}
                            }
                        ]
                    }]
                )
                
                analysis_text = response.choices[0].message.content
                return self._parse_analysis_response(analysis_text, "image")
                
            except Exception as e:
                logger.warning(f"OpenAI vision failed: {e}")
        
        # Fallback to basic analysis
        return {
            "summary": f"Image file: {filename}",
            "key_points": ["Image uploaded but detailed analysis unavailable"],
            "entities": [],
            "metadata": {"mime_type": mime_type, "size": len(file_data)}
        }
    
    async def _analyze_video(
        self,
        file_data: bytes,
        filename: str,
        mime_type: str,
        context: Optional[str] = None,
        detail_level: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Analyze video file."""
        
        # For video, we can extract key frames and analyze them
        # Or use specialized video analysis models
        
        analysis = {
            "summary": f"Video file: {filename}",
            "key_points": [
                f"Video format: {mime_type}",
                f"File size: {len(file_data) / (1024*1024):.2f} MB",
                "Video content analysis requires frame extraction"
            ],
            "entities": [],
            "metadata": {
                "mime_type": mime_type,
                "size": len(file_data),
                "type": "video"
            }
        }
        
        # Try to get video metadata using ffprobe if available
        try:
            import subprocess
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as f:
                f.write(file_data)
                temp_path = f.name
            
            try:
                result = subprocess.run(
                    ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", temp_path],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    import json
                    probe_data = json.loads(result.stdout)
                    
                    format_info = probe_data.get("format", {})
                    streams = probe_data.get("streams", [])
                    
                    video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
                    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})
                    
                    analysis["metadata"].update({
                        "duration": float(format_info.get("duration", 0)),
                        "duration_formatted": f"{float(format_info.get('duration', 0)):.1f}s",
                        "bitrate": format_info.get("bit_rate"),
                        "width": video_stream.get("width"),
                        "height": video_stream.get("height"),
                        "fps": video_stream.get("r_frame_rate"),
                        "video_codec": video_stream.get("codec_name"),
                        "audio_codec": audio_stream.get("codec_name"),
                    })
                    
                    analysis["key_points"] = [
                        f"Duration: {analysis['metadata']['duration_formatted']}",
                        f"Resolution: {video_stream.get('width')}x{video_stream.get('height')}",
                        f"Video codec: {video_stream.get('codec_name')}",
                        f"Audio codec: {audio_stream.get('codec_name', 'None')}",
                    ]
                    
                    analysis["summary"] = f"Video: {filename} - {analysis['metadata']['duration_formatted']}, {video_stream.get('width')}x{video_stream.get('height')}"
                    
            finally:
                os.unlink(temp_path)
                
        except Exception as e:
            logger.debug(f"ffprobe analysis failed: {e}")
        
        return analysis
    
    async def _analyze_audio(
        self,
        file_data: bytes,
        filename: str,
        mime_type: str,
        context: Optional[str] = None,
        detail_level: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Analyze audio file with transcription."""
        
        analysis = {
            "summary": f"Audio file: {filename}",
            "key_points": [
                f"Audio format: {mime_type}",
                f"File size: {len(file_data) / 1024:.1f} KB",
            ],
            "entities": [],
            "metadata": {
                "mime_type": mime_type,
                "size": len(file_data),
                "type": "audio"
            }
        }
        
        # Try to transcribe using Whisper (use sync client)
        if self.openai_sync is not None:
            try:
                import tempfile
                
                ext = Path(filename).suffix or ".wav"
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                    f.write(file_data)
                    temp_path = f.name
                
                try:
                    with open(temp_path, "rb") as audio_file:
                        transcription = self.openai_sync.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            response_format="verbose_json"
                        )
                    
                    analysis["transcription"] = transcription.text
                    analysis["summary"] = f"Audio transcription: {transcription.text[:500]}{'...' if len(transcription.text) > 500 else ''}"
                    analysis["metadata"]["duration"] = getattr(transcription, "duration", None)
                    analysis["metadata"]["language"] = getattr(transcription, "language", None)
                    
                    analysis["key_points"] = [
                        f"Transcribed text ({len(transcription.text)} chars)",
                        f"Language: {getattr(transcription, 'language', 'unknown')}",
                        f"Duration: {getattr(transcription, 'duration', 'unknown')}s"
                    ]
                    
                finally:
                    os.unlink(temp_path)
                    
            except Exception as e:
                logger.warning(f"Audio transcription failed: {e}")
                analysis["key_points"].append(f"Transcription unavailable: {str(e)}")
        else:
            analysis["key_points"].append("Transcription unavailable (no OpenAI API key)")
        
        return analysis
    
    async def _analyze_text(
        self,
        file_data: bytes,
        filename: str,
        mime_type: str,
        context: Optional[str] = None,
        detail_level: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Analyze text content."""
        
        try:
            # Try different encodings
            for encoding in ["utf-8", "latin-1", "cp1252"]:
                try:
                    text = file_data.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                text = file_data.decode("utf-8", errors="replace")
            
            # Truncate for analysis
            max_chars = 50000
            text_preview = text[:max_chars]
            truncated = len(text) > max_chars
            
            analysis = {
                "content": text_preview,
                "full_text": text if len(text) <= max_chars else None,
                "metadata": {
                    "char_count": len(text),
                    "line_count": text.count("\n") + 1,
                    "word_count": len(text.split()),
                    "truncated": truncated,
                    "mime_type": mime_type,
                }
            }
            
            # Use LLM for smart analysis
            if self.anthropic or self.openai:
                analysis_prompt = f"""Analyze this text document:

```
{text_preview[:10000]}
```

Provide:
1. **Summary**: What is this document about?
2. **Key Points**: Main topics, themes, or information
3. **Entities**: Names, places, organizations, dates mentioned
4. **Document Type**: What type of document is this?
5. **Tags**: Relevant keywords

Be concise but thorough."""

                try:
                    if self.anthropic:
                        response = await self.anthropic.messages.create(
                            model="claude-sonnet-4-20250514",
                            max_tokens=1500,
                            messages=[{"role": "user", "content": analysis_prompt}]
                        )
                        analysis_text = response.content[0].text
                    else:
                        response = await self.openai.chat.completions.create(
                            model="gpt-4o-mini",
                            max_tokens=1500,
                            messages=[{"role": "user", "content": analysis_prompt}]
                        )
                        analysis_text = response.choices[0].message.content
                    
                    parsed = self._parse_analysis_response(analysis_text, "text")
                    analysis.update(parsed)
                    
                except Exception as e:
                    logger.warning(f"LLM text analysis failed: {e}")
                    analysis["summary"] = f"Text document: {filename} ({len(text)} characters)"
                    analysis["key_points"] = [f"Contains {len(text.split())} words across {text.count(chr(10))+1} lines"]
            
            return analysis
            
        except Exception as e:
            return {
                "summary": f"Text file: {filename}",
                "error": str(e),
                "key_points": ["Could not parse text content"],
                "entities": [],
                "metadata": {"size": len(file_data)}
            }
    
    async def _analyze_document(
        self,
        file_data: bytes,
        filename: str,
        mime_type: str,
        context: Optional[str] = None,
        detail_level: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Analyze document files (PDF, Word, etc.)."""
        
        analysis = {
            "summary": f"Document: {filename}",
            "key_points": [],
            "entities": [],
            "metadata": {
                "mime_type": mime_type,
                "size": len(file_data),
                "type": "document"
            }
        }
        
        text_content = ""
        
        # Try to extract text from PDF
        if mime_type == "application/pdf":
            try:
                import fitz  # PyMuPDF
                
                doc = fitz.open(stream=file_data, filetype="pdf")
                pages = []
                for page in doc:
                    pages.append(page.get_text())
                text_content = "\n\n".join(pages)
                
                analysis["metadata"]["page_count"] = len(doc)
                analysis["key_points"].append(f"PDF with {len(doc)} pages")
                
            except ImportError:
                logger.debug("PyMuPDF not available for PDF extraction")
            except Exception as e:
                logger.debug(f"PDF extraction failed: {e}")
        
        # Analyze extracted text
        if text_content:
            text_analysis = await self._analyze_text(
                text_content.encode("utf-8"),
                filename,
                "text/plain",
                context,
                detail_level
            )
            analysis.update(text_analysis)
        else:
            analysis["summary"] = f"Document file: {filename} (text extraction not available)"
            analysis["key_points"].append("Install PyMuPDF for PDF text extraction")
        
        return analysis
    
    async def _analyze_code(
        self,
        file_data: bytes,
        filename: str,
        mime_type: str,
        context: Optional[str] = None,
        detail_level: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Analyze code files."""
        
        try:
            code = file_data.decode("utf-8")
        except UnicodeDecodeError:
            code = file_data.decode("latin-1")
        
        ext = Path(filename).suffix.lower()
        language_map = {
            ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
            ".java": "Java", ".c": "C", ".cpp": "C++", ".h": "C Header",
            ".css": "CSS", ".html": "HTML", ".rb": "Ruby", ".go": "Go",
            ".rs": "Rust", ".php": "PHP", ".swift": "Swift", ".kt": "Kotlin",
        }
        language = language_map.get(ext, "Unknown")
        
        analysis = {
            "content": code[:50000],
            "metadata": {
                "language": language,
                "extension": ext,
                "line_count": code.count("\n") + 1,
                "char_count": len(code),
                "size": len(file_data),
            }
        }
        
        # Use LLM for code analysis
        if self.anthropic or self.openai:
            analysis_prompt = f"""Analyze this {language} code:

```{ext[1:] if ext else ''}
{code[:15000]}
```

Provide:
1. **Summary**: What does this code do?
2. **Key Functions/Classes**: Main components
3. **Dependencies**: Libraries/imports used
4. **Code Quality**: Brief assessment
5. **Purpose**: What problem does this solve?

Be technical but concise."""

            try:
                if self.anthropic:
                    response = await self.anthropic.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1500,
                        messages=[{"role": "user", "content": analysis_prompt}]
                    )
                    analysis_text = response.content[0].text
                else:
                    response = await self.openai.chat.completions.create(
                        model="gpt-4o-mini",
                        max_tokens=1500,
                        messages=[{"role": "user", "content": analysis_prompt}]
                    )
                    analysis_text = response.choices[0].message.content
                
                parsed = self._parse_analysis_response(analysis_text, "code")
                analysis.update(parsed)
                
            except Exception as e:
                logger.warning(f"LLM code analysis failed: {e}")
                analysis["summary"] = f"{language} code file: {filename}"
                analysis["key_points"] = [f"{analysis['metadata']['line_count']} lines of {language} code"]
        
        return analysis
    
    async def _analyze_data(
        self,
        file_data: bytes,
        filename: str,
        mime_type: str,
        context: Optional[str] = None,
        detail_level: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Analyze data files (JSON, CSV, YAML)."""
        
        try:
            content = file_data.decode("utf-8")
        except UnicodeDecodeError:
            content = file_data.decode("latin-1")
        
        ext = Path(filename).suffix.lower()
        analysis: Dict[str, Any] = {
            "metadata": {
                "format": ext,
                "size": len(file_data),
            },
            "summary": "",
            "key_points": [],
            "entities": [],
        }
        
        # Parse based on format
        try:
            if ext == ".json":
                import json
                data = json.loads(content)
                analysis["metadata"]["structure"] = self._describe_structure(data)
                analysis["summary"] = f"JSON data with {self._count_items(data)} items"
                analysis["key_points"] = [f"Root type: {type(data).__name__}"]
                if isinstance(data, dict):
                    analysis["key_points"].append(f"Top-level keys: {list(data.keys())[:10]}")
                    
            elif ext in [".yaml", ".yml"]:
                import yaml
                data = yaml.safe_load(content)
                analysis["metadata"]["structure"] = self._describe_structure(data)
                analysis["summary"] = f"YAML data with {self._count_items(data)} items"
                
            elif ext == ".csv":
                lines = content.strip().split("\n")
                headers = lines[0].split(",") if lines else []
                analysis["metadata"]["columns"] = headers
                analysis["metadata"]["row_count"] = len(lines) - 1
                analysis["summary"] = f"CSV with {len(headers)} columns, {len(lines)-1} rows"
                analysis["key_points"] = [f"Columns: {', '.join(headers[:10])}{'...' if len(headers) > 10 else ''}"]
                
        except Exception as e:
            analysis["summary"] = f"Data file: {filename}"
            analysis["key_points"] = [f"Could not parse: {str(e)}"]
        
        analysis["content"] = content[:10000]
        return analysis
    
    async def _analyze_generic(
        self,
        file_data: bytes,
        filename: str,
        mime_type: str,
        context: Optional[str] = None,
        detail_level: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Generic analysis for unknown file types."""
        
        return {
            "summary": f"File: {filename} ({mime_type})",
            "key_points": [
                f"Size: {len(file_data)} bytes",
                f"Type: {mime_type}",
                "Detailed analysis not available for this file type"
            ],
            "entities": [],
            "metadata": {
                "mime_type": mime_type,
                "size": len(file_data),
            }
        }
    
    def _parse_analysis_response(self, text: str, file_type: str) -> Dict[str, Any]:
        """Parse LLM analysis response into structured format."""
        
        result = {
            "summary": "",
            "key_points": [],
            "entities": [],
            "tags": [],
            "raw_analysis": text
        }
        
        # Extract summary
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if "summary" in line.lower() and ":" in line:
                # Get content after colon or next lines
                summary_content = line.split(":", 1)[-1].strip()
                if not summary_content and i + 1 < len(lines):
                    summary_content = lines[i + 1].strip()
                result["summary"] = summary_content.strip("*- ")
                break
        
        if not result["summary"]:
            # Use first non-empty line
            for line in lines:
                clean = line.strip("*#- ")
                if clean and len(clean) > 20:
                    result["summary"] = clean[:500]
                    break
        
        # Extract key points
        in_key_points = False
        for line in lines:
            lower = line.lower()
            if "key" in lower and ("point" in lower or "element" in lower or "function" in lower):
                in_key_points = True
                continue
            if in_key_points:
                if line.strip().startswith(("-", "*", "•", "1", "2", "3", "4", "5", "6", "7", "8", "9")):
                    point = line.strip("*-•0123456789. ")
                    if point:
                        result["key_points"].append(point)
                elif line.strip().startswith("**") and ":" not in line[:20]:
                    in_key_points = False
        
        # Extract tags if present
        for line in lines:
            if "tag" in line.lower() and ":" in line:
                tags_part = line.split(":", 1)[-1]
                tags = [t.strip("*-• ,") for t in tags_part.split(",")]
                result["tags"] = [t for t in tags if t and len(t) < 50]
                break
        
        return result
    
    def _describe_structure(self, data: Any, depth: int = 0) -> str:
        """Describe data structure recursively."""
        if depth > 3:
            return "..."
        
        if isinstance(data, dict):
            items = [f"{k}: {self._describe_structure(v, depth+1)}" for k, v in list(data.items())[:5]]
            suffix = f"... +{len(data)-5} more" if len(data) > 5 else ""
            return "{" + ", ".join(items) + suffix + "}"
        elif isinstance(data, list):
            if data:
                return f"[{self._describe_structure(data[0], depth+1)}...] ({len(data)} items)"
            return "[]"
        else:
            return type(data).__name__
    
    def _count_items(self, data: Any) -> int:
        """Count items in data structure."""
        if isinstance(data, dict):
            return len(data) + sum(self._count_items(v) for v in data.values())
        elif isinstance(data, list):
            return len(data) + sum(self._count_items(v) for v in data)
        return 1


# Tool functions for orchestrator
def create_file_analysis_tools(openai_client=None, anthropic_client=None, replicate_client=None):
    """Create file analysis tool functions."""
    
    analyzer = FileAnalyzer(openai_client, anthropic_client, replicate_client)
    
    async def analyze_uploaded_file(
        file_id: str = "",
        file_path: str = "",
        context: str = "",
        detail_level: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Analyze an uploaded file and understand its contents.
        
        Works with any file type:
        - Images: Visual analysis, object detection, OCR, style analysis
        - Videos: Duration, resolution, codec info, frame analysis
        - Audio: Transcription, duration, language detection
        - Text/Documents: Content extraction, summarization, entity extraction
        - Code: Language detection, function analysis, documentation
        - Data: Structure analysis, schema detection, content preview
        
        Args:
            file_id: ID of uploaded file (from file storage)
            file_path: Or direct path to file
            context: Additional context for better analysis
            detail_level: "quick", "standard", or "comprehensive"
            
        Returns:
            Comprehensive analysis with summary, key points, and metadata
        """
        from ..storage import FileStorage, StorageConfig
        
        storage = FileStorage(StorageConfig())
        
        # Get file data
        if file_id:
            file_data, metadata = await storage.retrieve(file_id)
            if not file_data:
                return {"error": f"File not found: {file_id}"}
            filename = metadata.original_name
            mime_type = metadata.mime_type
        elif file_path:
            with open(file_path, "rb") as f:
                file_data = f.read()
            filename = Path(file_path).name
            mime_type = mimetypes.guess_type(file_path)[0]
        else:
            return {"error": "Must provide either file_id or file_path"}
        
        return await analyzer.analyze(
            file_data=file_data,
            filename=filename,
            mime_type=mime_type,
            context=context,
            detail_level=detail_level
        )
    
    return {
        "analyze_uploaded_file": analyze_uploaded_file,
        "analyzer": analyzer
    }
