"""
Voice Pipeline
==============

End-to-end voice conversation pipeline.
Speech -> Text -> AI -> Text -> Speech
"""

import logging
import asyncio
from typing import Optional, Dict, Any, Callable, AsyncGenerator
from openai import AsyncOpenAI

from .speech_to_text import SpeechToText
from .text_to_speech import TextToSpeech

logger = logging.getLogger(__name__)


class VoicePipeline:
    """
    Complete voice-to-voice conversation pipeline.
    
    Flow:
    1. Receive audio input
    2. Transcribe to text (STT)
    3. Process with AI agent
    4. Synthesize response (TTS)
    5. Return audio output
    """
    
    def __init__(
        self,
        openai_client: AsyncOpenAI = None,
        elevenlabs_api_key: Optional[str] = None,
        tts_provider: str = "openai",
        tts_voice: Optional[str] = None
    ):
        self.stt = SpeechToText(openai_client)
        self.tts = TextToSpeech(
            openai_client,
            elevenlabs_api_key=elevenlabs_api_key,
            default_provider=tts_provider
        )
        self.default_voice = tts_voice or "nova"
        
        # Callback for AI processing
        self._process_callback: Optional[Callable] = None
        
    def set_processor(self, callback: Callable):
        """
        Set the AI processing callback.
        
        Args:
            callback: Async function that takes text and returns response text
        """
        self._process_callback = callback
        
    async def process_audio(
        self,
        audio_data: bytes,
        audio_format: str = "wav",
        voice: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process audio input and return audio response.
        
        Args:
            audio_data: Input audio bytes
            audio_format: Audio format (wav, mp3, etc.)
            voice: TTS voice to use
            context: Additional context for processing
            
        Returns:
            Dict with response audio and metadata
        """
        result = {
            "success": False,
            "input_text": "",
            "output_text": "",
            "audio": b"",
            "audio_base64": ""
        }
        
        try:
            # Step 1: Speech to Text
            logger.info("Step 1: Transcribing audio...")
            stt_result = await self.stt.transcribe(audio_data, format=audio_format)
            
            if not stt_result["success"]:
                result["error"] = f"Transcription failed: {stt_result.get('error')}"
                return result
            
            input_text = stt_result["text"]
            result["input_text"] = input_text
            logger.info(f"Transcribed: {input_text[:100]}...")
            
            # Step 2: AI Processing
            logger.info("Step 2: Processing with AI...")
            if self._process_callback:
                output_text = await self._process_callback(input_text, context)
            else:
                output_text = f"I heard you say: {input_text}"
            
            result["output_text"] = output_text
            logger.info(f"Response: {output_text[:100]}...")
            
            # Step 3: Text to Speech
            logger.info("Step 3: Synthesizing speech...")
            tts_result = await self.tts.synthesize(
                output_text,
                voice=voice or self.default_voice
            )
            
            if not tts_result["success"]:
                result["error"] = f"Synthesis failed: {tts_result.get('error')}"
                return result
            
            result["audio"] = tts_result["audio"]
            result["audio_base64"] = tts_result["audio_base64"]
            result["audio_format"] = tts_result["format"]
            result["voice"] = tts_result["voice"]
            result["success"] = True
            
            logger.info("Voice pipeline complete!")
            return result
            
        except Exception as e:
            logger.error(f"Voice pipeline error: {e}", exc_info=True)
            result["error"] = str(e)
            return result
    
    async def process_audio_base64(
        self,
        audio_base64: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Process base64-encoded audio."""
        import base64
        audio_data = base64.b64decode(audio_base64)
        return await self.process_audio(audio_data, **kwargs)
    
    async def process_streaming(
        self,
        audio_data: bytes,
        audio_format: str = "wav",
        voice: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process audio with streaming response.
        
        Yields status updates and audio chunks as they become available.
        """
        # Transcription
        yield {"type": "status", "stage": "transcribing"}
        stt_result = await self.stt.transcribe(audio_data, format=audio_format)
        
        if not stt_result["success"]:
            yield {"type": "error", "error": stt_result.get("error")}
            return
        
        yield {
            "type": "transcription",
            "text": stt_result["text"]
        }
        
        # AI Processing
        yield {"type": "status", "stage": "thinking"}
        if self._process_callback:
            output_text = await self._process_callback(stt_result["text"], context)
        else:
            output_text = f"I heard: {stt_result['text']}"
        
        yield {
            "type": "response_text",
            "text": output_text
        }
        
        # TTS - stream chunks
        yield {"type": "status", "stage": "speaking"}
        async for chunk in self.tts.synthesize_streaming(
            output_text,
            voice=voice or self.default_voice
        ):
            yield {
                "type": "audio_chunk",
                "data": chunk
            }
        
        yield {"type": "complete"}
    
    async def transcribe_only(
        self,
        audio_data: bytes,
        audio_format: str = "wav"
    ) -> Dict[str, Any]:
        """Just transcribe audio without full pipeline."""
        return await self.stt.transcribe(audio_data, format=audio_format)
    
    async def speak_only(
        self,
        text: str,
        voice: Optional[str] = None
    ) -> Dict[str, Any]:
        """Just synthesize speech without full pipeline."""
        return await self.tts.synthesize(text, voice=voice or self.default_voice)
    
    def get_available_voices(self) -> Dict[str, list]:
        """Get all available TTS voices."""
        return self.tts.get_available_voices()
