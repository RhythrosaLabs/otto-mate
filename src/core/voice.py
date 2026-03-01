"""
Voice Capabilities for Otto

Implements Voice Wake (wake word detection) and Talk Mode (voice conversation).
"""

import logging
import asyncio
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class VoiceMode(Enum):
    """Voice interaction modes"""
    WAKE_WORD = "wake_word"  # Passive listening for "Hey Otto"
    TALK_MODE = "talk_mode"  # Active voice conversation


@dataclass
class VoiceConfig:
    """Voice capability configuration"""
    wake_word: str = "hey otto"
    language: str = "en"
    enable_wake_word: bool = True
    enable_talk_mode: bool = True
    stt_provider: str = "whisper"  # whisper, google, azure
    tts_provider: str = "elevenlabs"  # elevenlabs, google, azure, coqui
    voice_id: Optional[str] = None
    silence_timeout: float = 2.0  # seconds of silence before processing


class VoiceWake:
    """
    Voice Wake Word Detection
    
    Listens passively for wake word "Hey Otto" then activates.
    Uses porcupine for efficient on-device wake word detection.
    """
    
    def __init__(self, config: VoiceConfig, callback: Callable):
        self.config = config
        self.callback = callback
        self.is_listening = False
        self.porcupine = None
        self.audio_stream = None
        
        try:
            import pvporcupine
            self.pvporcupine = pvporcupine
        except ImportError:
            logger.warning("pvporcupine not installed. Run: pip install pvporcupine")
            self.pvporcupine = None
    
    async def start(self):
        """Start wake word detection"""
        if not self.pvporcupine:
            logger.error("Wake word detection requires pvporcupine")
            return
        
        try:
            # Initialize Porcupine with custom wake word
            self.porcupine = self.pvporcupine.create(
                keywords=["hey siri"]  # Use built-in, customize to "otto" with Porcupine Console
            )
            
            import pyaudio
            
            # Open audio stream
            pa = pyaudio.PyAudio()
            self.audio_stream = pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
            
            self.is_listening = True
            logger.info("👂 Voice Wake listening for: '%s'", self.config.wake_word)
            
            # Listen loop
            while self.is_listening:
                pcm = self.audio_stream.read(self.porcupine.frame_length, exception_on_overflow=False)
                pcm = [int.from_bytes(pcm[i:i+2], byteorder='little', signed=True) 
                       for i in range(0, len(pcm), 2)]
                
                keyword_index = self.porcupine.process(pcm)
                
                if keyword_index >= 0:
                    logger.info("🎤 Wake word detected!")
                    await self.callback()
                
                await asyncio.sleep(0.01)
        
        except Exception as e:
            logger.error(f"Wake word detection error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop wake word detection"""
        self.is_listening = False
        
        if self.audio_stream:
            self.audio_stream.close()
        
        if self.porcupine:
            self.porcupine.delete()
        
        logger.info("👂 Voice Wake stopped")


class TalkMode:
    """
    Talk Mode - Active Voice Conversation
    
    Records voice input, transcribes with Whisper, generates response,
    and speaks back with TTS.
    """
    
    def __init__(self, config: VoiceConfig):
        self.config = config
        self.is_active = False
        self.audio_buffer = []
        
        # Initialize STT
        if config.stt_provider == "whisper":
            try:
                import whisper
                self.whisper_model = whisper.load_model("base")
            except ImportError:
                logger.warning("whisper not installed. Run: pip install openai-whisper")
                self.whisper_model = None
        
        # Initialize TTS
        if config.tts_provider == "elevenlabs":
            try:
                from elevenlabs import generate, play, set_api_key
                # set_api_key() called with env var
                self.tts_generate = generate
                self.tts_play = play
            except ImportError:
                logger.warning("elevenlabs not installed. Run: pip install elevenlabs")
                self.tts_generate = None
                self.tts_play = None
    
    async def start_conversation(self, agent_callback: Callable):
        """Start voice conversation loop"""
        self.is_active = True
        logger.info("🎙️ Talk Mode activated")
        
        while self.is_active:
            try:
                # Record audio until silence
                audio_data = await self._record_until_silence()
                
                if not audio_data:
                    continue
                
                # Transcribe with STT
                text = await self._transcribe(audio_data)
                
                if not text:
                    continue
                
                logger.info(f"👤 User: {text}")
                
                # Get agent response
                response = await agent_callback(text)
                
                logger.info(f"🤖 Otto: {response}")
                
                # Speak response with TTS
                await self._speak(response)
            
            except Exception as e:
                logger.error(f"Talk Mode error: {e}")
                break
        
        logger.info("🎙️ Talk Mode deactivated")
    
    def stop_conversation(self):
        """Stop voice conversation"""
        self.is_active = False
    
    async def _record_until_silence(self) -> Optional[bytes]:
        """Record audio until silence detected"""
        import pyaudio
        import wave
        import io
        
        try:
            pa = pyaudio.PyAudio()
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024
            )
            
            frames = []
            silent_chunks = 0
            max_silent_chunks = int(self.config.silence_timeout * 16)  # ~2 seconds
            
            logger.info("🎤 Listening...")
            
            while self.is_active:
                data = stream.read(1024, exception_on_overflow=False)
                frames.append(data)
                
                # Simple silence detection (check amplitude)
                amplitude = max(abs(int.from_bytes(data[i:i+2], byteorder='little', signed=True)) 
                               for i in range(0, len(data), 2))
                
                if amplitude < 500:  # Threshold for silence
                    silent_chunks += 1
                else:
                    silent_chunks = 0
                
                # Stop if enough silence
                if silent_chunks > max_silent_chunks and len(frames) > 16:
                    break
                
                await asyncio.sleep(0.01)
            
            stream.close()
            
            if len(frames) < 16:
                return None
            
            # Convert to WAV
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(b''.join(frames))
            
            return wav_buffer.getvalue()
        
        except Exception as e:
            logger.error(f"Recording error: {e}")
            return None
    
    async def _transcribe(self, audio_data: bytes) -> Optional[str]:
        """Transcribe audio to text"""
        try:
            if self.config.stt_provider == "whisper" and self.whisper_model:
                import tempfile
                
                # Save to temp file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    f.write(audio_data)
                    temp_path = f.name
                
                # Transcribe
                result = self.whisper_model.transcribe(temp_path)
                text = result["text"].strip()
                
                import os
                os.unlink(temp_path)
                
                return text if text else None
        
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None
    
    async def _speak(self, text: str):
        """Convert text to speech and play"""
        try:
            if self.config.tts_provider == "elevenlabs" and self.tts_generate and self.tts_play:
                audio = self.tts_generate(
                    text=text,
                    voice=self.config.voice_id or "Adam"
                )
                self.tts_play(audio)
        
        except Exception as e:
            logger.error(f"TTS error: {e}")


class VoiceCapabilities:
    """
    Main voice capabilities manager
    
    Coordinates Voice Wake and Talk Mode.
    """
    
    def __init__(self, config: VoiceConfig, agent_callback: Callable):
        self.config = config
        self.agent_callback = agent_callback
        self.voice_wake = None
        self.talk_mode = None
        self.current_mode = None
    
    async def start(self):
        """Start voice capabilities"""
        if self.config.enable_wake_word:
            self.voice_wake = VoiceWake(self.config, self._on_wake_word)
            asyncio.create_task(self.voice_wake.start())
        
        if self.config.enable_talk_mode:
            self.talk_mode = TalkMode(self.config)
    
    async def _on_wake_word(self):
        """Handle wake word detection"""
        logger.info("🎤 Activating Talk Mode...")
        
        if self.talk_mode:
            await self.talk_mode.start_conversation(self.agent_callback)
    
    def activate_talk_mode(self):
        """Manually activate Talk Mode"""
        if self.talk_mode:
            asyncio.create_task(self.talk_mode.start_conversation(self.agent_callback))
    
    def deactivate_talk_mode(self):
        """Manually deactivate Talk Mode"""
        if self.talk_mode:
            self.talk_mode.stop_conversation()
    
    def stop(self):
        """Stop all voice capabilities"""
        if self.voice_wake:
            self.voice_wake.stop()
        
        if self.talk_mode:
            self.talk_mode.stop_conversation()
