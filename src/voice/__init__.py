"""Voice processing module for Otto Universal AI."""

from .speech_to_text import SpeechToText
from .text_to_speech import TextToSpeech
from .voice_pipeline import VoicePipeline

__all__ = ["SpeechToText", "TextToSpeech", "VoicePipeline"]
