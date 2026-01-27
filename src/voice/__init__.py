"""Voice processing module for Otto Universal AI."""

from .speech_to_text import SpeechToText
from .text_to_speech import TextToSpeech
from .voice_pipeline import VoicePipeline
from typing import Optional
from openai import AsyncOpenAI

__all__ = ["SpeechToText", "TextToSpeech", "VoicePipeline", "transcribe_audio", "synthesize_speech"]


async def transcribe_audio(audio_data: bytes, client: AsyncOpenAI, format: str = "wav") -> str:
    """Convenience function to transcribe audio to text."""
    stt = SpeechToText(client)
    result = await stt.transcribe(audio_data, format=format)
    return result.get("text", "")


async def synthesize_speech(text: str, client: AsyncOpenAI, voice: str = "nova") -> bytes:
    """Convenience function to synthesize text to speech."""
    tts = TextToSpeech(client)
    result = await tts.synthesize(text, voice=voice)
    return result.get("audio", b"")
