"""
Text-to-Speech Module
=====================

Converts text to speech using OpenAI TTS or ElevenLabs.
"""

import logging
import base64
import aiohttp
from typing import Optional, Dict, Any, Literal
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class TextToSpeech:
    """Converts text to speech audio."""
    
    # OpenAI voices
    OPENAI_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    
    def __init__(
        self,
        openai_client: AsyncOpenAI = None,
        elevenlabs_api_key: Optional[str] = None,
        default_provider: str = "openai"
    ):
        self.openai = openai_client
        self.elevenlabs_key = elevenlabs_api_key
        self.default_provider = default_provider
        
        # ElevenLabs settings
        self.elevenlabs_base_url = "https://api.elevenlabs.io/v1"
        self.default_elevenlabs_voice = "21m00Tcm4TlvDq8ikWAM"  # Rachel
        
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        provider: Optional[str] = None,
        speed: float = 1.0,
        format: str = "mp3"
    ) -> Dict[str, Any]:
        """
        Convert text to speech.
        
        Args:
            text: Text to synthesize
            voice: Voice ID (provider-specific)
            provider: "openai" or "elevenlabs"
            speed: Speech speed (0.25 to 4.0 for OpenAI)
            format: Output format (mp3, wav, etc.)
            
        Returns:
            Dict with audio data and metadata
        """
        provider = provider or self.default_provider
        
        if provider == "elevenlabs" and self.elevenlabs_key:
            return await self._synthesize_elevenlabs(text, voice, format)
        else:
            return await self._synthesize_openai(text, voice, speed, format)
    
    async def _synthesize_openai(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        format: str = "mp3"
    ) -> Dict[str, Any]:
        """Synthesize using OpenAI TTS."""
        # Check if client is available
        if self.openai is None:
            logger.error("OpenAI client not configured for text-to-speech")
            return {
                "audio": b"",
                "error": "OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.",
                "success": False
            }
        
        try:
            voice = voice or "nova"
            if voice not in self.OPENAI_VOICES:
                voice = "nova"
            
            response = await self.openai.audio.speech.create(
                model="tts-1-hd",
                voice=voice,
                input=text,
                speed=max(0.25, min(4.0, speed)),
                response_format=format
            )
            
            audio_data = response.content
            
            logger.info(f"Synthesized {len(text)} chars -> {len(audio_data)} bytes")
            
            return {
                "audio": audio_data,
                "audio_base64": base64.b64encode(audio_data).decode(),
                "format": format,
                "provider": "openai",
                "voice": voice,
                "duration_estimate": len(text) / 15,  # ~15 chars/sec estimate
                "success": True
            }
            
        except Exception as e:
            logger.error(f"OpenAI TTS error: {e}", exc_info=True)
            return {
                "audio": b"",
                "error": str(e),
                "success": False
            }
    
    async def _synthesize_elevenlabs(
        self,
        text: str,
        voice: Optional[str] = None,
        format: str = "mp3"
    ) -> Dict[str, Any]:
        """Synthesize using ElevenLabs."""
        try:
            voice_id = voice or self.default_elevenlabs_voice
            
            url = f"{self.elevenlabs_base_url}/text-to-speech/{voice_id}"
            
            headers = {
                "Accept": f"audio/{format}",
                "Content-Type": "application/json",
                "xi-api-key": self.elevenlabs_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status != 200:
                        error = await response.text()
                        raise Exception(f"ElevenLabs API error: {error}")
                    
                    audio_data = await response.read()
            
            logger.info(f"ElevenLabs synthesized {len(text)} chars -> {len(audio_data)} bytes")
            
            return {
                "audio": audio_data,
                "audio_base64": base64.b64encode(audio_data).decode(),
                "format": format,
                "provider": "elevenlabs",
                "voice": voice_id,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {e}", exc_info=True)
            # Fallback to OpenAI
            logger.info("Falling back to OpenAI TTS")
            return await self._synthesize_openai(text, format=format)
    
    async def synthesize_streaming(
        self,
        text: str,
        voice: Optional[str] = None,
        chunk_size: int = 1024
    ):
        """
        Stream audio synthesis (yields chunks).
        
        Args:
            text: Text to synthesize
            voice: Voice ID
            chunk_size: Size of audio chunks to yield
            
        Yields:
            Audio data chunks
        """
        # For now, synthesize fully then chunk
        result = await self.synthesize(text, voice)
        
        if result["success"]:
            audio = result["audio"]
            for i in range(0, len(audio), chunk_size):
                yield audio[i:i + chunk_size]
    
    def get_available_voices(self, provider: Optional[str] = None) -> Dict[str, list]:
        """Get available voices by provider."""
        voices = {}
        
        if provider in [None, "openai"]:
            voices["openai"] = [
                {"id": "alloy", "name": "Alloy", "gender": "neutral"},
                {"id": "echo", "name": "Echo", "gender": "male"},
                {"id": "fable", "name": "Fable", "gender": "neutral"},
                {"id": "onyx", "name": "Onyx", "gender": "male"},
                {"id": "nova", "name": "Nova", "gender": "female"},
                {"id": "shimmer", "name": "Shimmer", "gender": "female"},
            ]
        
        if provider in [None, "elevenlabs"] and self.elevenlabs_key:
            voices["elevenlabs"] = [
                {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "gender": "female"},
                {"id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi", "gender": "female"},
                {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella", "gender": "female"},
                {"id": "ErXwobaYiN019PkySvjV", "name": "Antoni", "gender": "male"},
                {"id": "MF3mGyEYCl7XYWbV9V6O", "name": "Elli", "gender": "female"},
                {"id": "TxGEqnHWrfWFTfGW9XjX", "name": "Josh", "gender": "male"},
            ]
        
        return voices
