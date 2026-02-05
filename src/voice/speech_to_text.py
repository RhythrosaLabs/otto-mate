"""
Speech-to-Text Module
=====================

Converts audio to text using OpenAI Whisper.
"""

import logging
import base64
import tempfile
import os
from typing import Optional, Dict, Any
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class SpeechToText:
    """Converts speech audio to text using OpenAI Whisper."""
    
    def __init__(self, openai_client: AsyncOpenAI = None):
        self.client = openai_client
        self.model = "whisper-1"
        self.supported_formats = ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]
        
    async def transcribe(
        self,
        audio_data: bytes,
        format: str = "wav",
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text.
        
        Args:
            audio_data: Raw audio bytes
            format: Audio format (wav, mp3, etc.)
            language: Optional language hint (ISO-639-1 code)
            prompt: Optional prompt to guide transcription
            
        Returns:
            Dict with transcription and metadata
        """
        # Check if client is available
        if self.client is None:
            logger.error("OpenAI client not configured for speech-to-text")
            return {
                "text": "",
                "error": "OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.",
                "success": False
            }
        
        try:
            # Write audio to temp file (Whisper API requires file)
            with tempfile.NamedTemporaryFile(
                suffix=f".{format}",
                delete=False
            ) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            try:
                # Transcribe
                with open(temp_path, "rb") as audio_file:
                    kwargs = {
                        "model": self.model,
                        "file": audio_file,
                        "response_format": "verbose_json"
                    }
                    
                    if language:
                        kwargs["language"] = language
                    if prompt:
                        kwargs["prompt"] = prompt
                    
                    response = await self.client.audio.transcriptions.create(**kwargs)
                
                logger.info(f"Transcribed {len(audio_data)} bytes -> {len(response.text)} chars")
                
                return {
                    "text": response.text,
                    "language": getattr(response, "language", language),
                    "duration": getattr(response, "duration", None),
                    "segments": getattr(response, "segments", []),
                    "success": True
                }
                
            finally:
                # Cleanup temp file
                os.unlink(temp_path)
                
        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            return {
                "text": "",
                "error": str(e),
                "success": False
            }
    
    async def transcribe_base64(
        self,
        audio_base64: str,
        format: str = "wav",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Transcribe base64-encoded audio.
        
        Args:
            audio_base64: Base64-encoded audio data
            format: Audio format
            **kwargs: Additional args passed to transcribe()
            
        Returns:
            Dict with transcription and metadata
        """
        try:
            audio_data = base64.b64decode(audio_base64)
            return await self.transcribe(audio_data, format=format, **kwargs)
        except Exception as e:
            logger.error(f"Base64 decode error: {e}")
            return {
                "text": "",
                "error": f"Invalid base64 audio: {e}",
                "success": False
            }
    
    async def transcribe_streaming(
        self,
        audio_chunks: list,
        format: str = "wav"
    ) -> Dict[str, Any]:
        """
        Transcribe streaming audio chunks.
        
        Args:
            audio_chunks: List of audio byte chunks
            format: Audio format
            
        Returns:
            Dict with transcription
        """
        # Combine chunks
        combined = b"".join(audio_chunks)
        return await self.transcribe(combined, format=format)
