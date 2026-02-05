"""
Audio Processing Module
=======================

Professional audio manipulation for video production:
- Volume mixing and adjustment
- Audio looping and trimming
- Crossfade and fade effects
- Voiceover + music composition
- Audio normalization

Ported from printify_clean's audio_processing.py with async support.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

# Lazy imports for MoviePy to avoid initialization issues
AudioFileClip = None
CompositeAudioClip = None
concatenate_audioclips = None


def _ensure_moviepy():
    """Lazy import MoviePy to avoid SDL/pygame issues."""
    global AudioFileClip, CompositeAudioClip, concatenate_audioclips
    if AudioFileClip is None:
        try:
            from moviepy.editor import AudioFileClip as _AudioFileClip
            from moviepy.editor import CompositeAudioClip as _CompositeAudioClip
            from moviepy.editor import concatenate_audioclips as _concatenate_audioclips
            
            AudioFileClip = _AudioFileClip
            CompositeAudioClip = _CompositeAudioClip
            concatenate_audioclips = _concatenate_audioclips
        except ImportError as e:
            raise ImportError(f"MoviePy required for audio processing: {e}")


class AudioProcessor:
    """
    Professional audio processing for video production.
    
    Features:
    - Load and analyze audio files
    - Adjust volume, loop, trim
    - Apply fade effects
    - Mix multiple tracks (voiceover + music)
    - Export composed audio
    """
    
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir or "./data/files/audio")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def load_audio(self, audio_path: str) -> Optional[Any]:
        """
        Load audio file into MoviePy clip.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            AudioFileClip or None if failed
        """
        _ensure_moviepy()
        
        try:
            if not os.path.exists(audio_path):
                logger.error(f"❌ Audio file not found: {audio_path}")
                return None
            
            audio = AudioFileClip(audio_path)
            logger.info(f"✅ Loaded audio: {audio.duration:.2f}s")
            return audio
            
        except Exception as e:
            logger.error(f"❌ Failed to load audio: {e}")
            return None
    
    def adjust_volume(self, audio, volume_factor: float = 1.0):
        """
        Adjust audio volume.
        
        Args:
            audio: AudioFileClip
            volume_factor: Multiplier (0.0-2.0+, 1.0=unchanged)
            
        Returns:
            Adjusted AudioFileClip
        """
        try:
            return audio.volumex(volume_factor)
        except Exception as e:
            logger.error(f"❌ Volume adjustment failed: {e}")
            return audio
    
    def loop_audio(self, audio, target_duration: float):
        """
        Loop audio to match target duration.
        
        Args:
            audio: AudioFileClip
            target_duration: Target duration in seconds
            
        Returns:
            Looped AudioFileClip
        """
        _ensure_moviepy()
        
        try:
            if audio.duration >= target_duration:
                return audio.subclip(0, target_duration)
            
            # Use MoviePy's audio_loop
            looped = audio.audio_loop(duration=target_duration)
            logger.info(f"✅ Looped audio from {audio.duration:.2f}s to {target_duration:.2f}s")
            return looped
            
        except Exception as e:
            logger.error(f"❌ Audio looping failed: {e}")
            # Fallback: manual loop
            try:
                loops_needed = int(target_duration / audio.duration) + 1
                looped = concatenate_audioclips([audio] * loops_needed)
                return looped.subclip(0, target_duration)
            except:
                return audio
    
    def trim_audio(self, audio, duration: float):
        """
        Trim audio to specific duration.
        
        Args:
            audio: AudioFileClip
            duration: Target duration
            
        Returns:
            Trimmed AudioFileClip
        """
        try:
            if audio.duration <= duration:
                return audio
            return audio.subclip(0, duration)
        except Exception as e:
            logger.error(f"❌ Audio trim failed: {e}")
            return audio
    
    def add_fade(
        self,
        audio,
        fade_in: float = 0.0,
        fade_out: float = 0.0
    ):
        """
        Add fade in/out effects.
        
        Args:
            audio: AudioFileClip
            fade_in: Fade in duration (seconds)
            fade_out: Fade out duration (seconds)
            
        Returns:
            AudioFileClip with fades
        """
        try:
            if fade_in > 0:
                audio = audio.audio_fadein(fade_in)
            if fade_out > 0:
                audio = audio.audio_fadeout(fade_out)
            logger.info(f"✅ Added fade: in={fade_in}s, out={fade_out}s")
            return audio
        except Exception as e:
            logger.error(f"❌ Fade effect failed: {e}")
            return audio
    
    def mix_tracks(
        self,
        tracks: List[Any],
        volumes: Optional[List[float]] = None
    ):
        """
        Mix multiple audio tracks into composite.
        
        Args:
            tracks: List of AudioFileClips
            volumes: Optional volume multipliers per track
            
        Returns:
            CompositeAudioClip
        """
        _ensure_moviepy()
        
        try:
            if not tracks:
                logger.warning("⚠️ No tracks to mix")
                return None
            
            # Apply volumes
            if volumes and len(volumes) == len(tracks):
                tracks = [t.volumex(v) for t, v in zip(tracks, volumes)]
            
            mixed = CompositeAudioClip(tracks)
            logger.info(f"✅ Mixed {len(tracks)} audio tracks")
            return mixed
            
        except Exception as e:
            logger.error(f"❌ Audio mixing failed: {e}")
            return None
    
    def concatenate(
        self,
        tracks: List[Any],
        crossfade: float = 0.0
    ):
        """
        Concatenate audio clips in sequence.
        
        Args:
            tracks: List of AudioFileClips
            crossfade: Crossfade duration between clips
            
        Returns:
            Concatenated AudioFileClip
        """
        _ensure_moviepy()
        
        try:
            if not tracks:
                return None
            
            if crossfade > 0:
                for i in range(len(tracks) - 1):
                    tracks[i] = tracks[i].audio_fadeout(crossfade)
                    tracks[i + 1] = tracks[i + 1].audio_fadein(crossfade)
            
            concatenated = concatenate_audioclips(tracks)
            logger.info(f"✅ Concatenated {len(tracks)} audio clips")
            return concatenated
            
        except Exception as e:
            logger.error(f"❌ Concatenation failed: {e}")
            return None
    
    def prepare_background_music(
        self,
        music_path: str,
        target_duration: float,
        volume: float = 0.3,
        fade_in: float = 0.5,
        fade_out: float = 1.0
    ) -> Optional[Any]:
        """
        Prepare background music: load, loop, adjust volume, add fades.
        
        Args:
            music_path: Path to music file
            target_duration: Target duration
            volume: Volume factor (default 0.3 = 30%)
            fade_in: Fade in duration
            fade_out: Fade out duration
            
        Returns:
            Processed AudioFileClip
        """
        try:
            logger.info(f"🎵 Preparing background music: {music_path}")
            
            music = self.load_audio(music_path)
            if not music:
                return None
            
            music = self.loop_audio(music, target_duration)
            music = self.adjust_volume(music, volume)
            music = self.add_fade(music, fade_in, fade_out)
            
            logger.info(f"✅ Music ready: {music.duration:.2f}s at {volume*100:.0f}% volume")
            return music
            
        except Exception as e:
            logger.error(f"❌ Music preparation failed: {e}")
            return None
    
    def compose_video_audio(
        self,
        voiceover_path: str = None,
        music_path: str = None,
        target_duration: float = None,
        voiceover_volume: float = 1.0,
        music_volume: float = 0.3
    ) -> Dict[str, Any]:
        """
        Compose final audio for video (voiceover + background music).
        
        Args:
            voiceover_path: Path to voiceover audio
            music_path: Path to background music
            target_duration: Target duration (uses longest track if None)
            voiceover_volume: Voiceover volume (default 1.0)
            music_volume: Music volume (default 0.3)
            
        Returns:
            {"success": bool, "audio": CompositeAudioClip, "duration": float}
        """
        _ensure_moviepy()
        
        try:
            tracks = []
            max_duration = 0
            
            # Load voiceover
            if voiceover_path and os.path.exists(voiceover_path):
                voice = self.load_audio(voiceover_path)
                if voice:
                    voice = self.adjust_volume(voice, voiceover_volume)
                    tracks.append(voice)
                    max_duration = max(max_duration, voice.duration)
            
            # Determine target duration
            duration = target_duration or max_duration or 10
            
            # Load and prepare music
            if music_path and os.path.exists(music_path):
                music = self.prepare_background_music(
                    music_path,
                    target_duration=duration,
                    volume=music_volume
                )
                if music:
                    tracks.append(music)
            
            if not tracks:
                return {"success": False, "error": "No audio tracks to compose"}
            
            # Mix tracks
            composed = self.mix_tracks(tracks)
            if composed:
                composed = composed.set_duration(duration)
                return {
                    "success": True,
                    "audio": composed,
                    "duration": duration
                }
            
            return {"success": False, "error": "Audio mixing failed"}
            
        except Exception as e:
            logger.error(f"❌ Audio composition failed: {e}")
            return {"success": False, "error": str(e)}
    
    def export_audio(
        self,
        audio,
        output_path: str,
        fps: int = 44100,
        codec: str = "libmp3lame",
        bitrate: str = "192k"
    ) -> bool:
        """
        Export audio clip to file.
        
        Args:
            audio: AudioFileClip
            output_path: Output path
            fps: Sample rate
            codec: Audio codec
            bitrate: Audio bitrate
            
        Returns:
            True if successful
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            audio.write_audiofile(
                output_path,
                fps=fps,
                codec=codec,
                bitrate=bitrate,
                verbose=False,
                logger=None
            )
            
            logger.info(f"✅ Audio exported: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Audio export failed: {e}")
            return False
    
    def get_duration(self, audio_path: str) -> Optional[float]:
        """
        Get duration of audio file.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Duration in seconds
        """
        try:
            audio = self.load_audio(audio_path)
            if audio:
                duration = audio.duration
                audio.close()
                return duration
            return None
        except:
            return None
    
    def normalize_volume(self, audio) -> Any:
        """
        Normalize audio to peak at 0dB.
        
        Args:
            audio: AudioFileClip
            
        Returns:
            Normalized AudioFileClip
        """
        try:
            max_amp = audio.max_volume()
            if max_amp > 0:
                normalized = audio.volumex(1.0 / max_amp)
                logger.info(f"✅ Normalized audio (peak was {max_amp:.2f})")
                return normalized
            return audio
        except Exception as e:
            logger.error(f"❌ Normalization failed: {e}")
            return audio


# Singleton instance
_audio_processor = None


def get_audio_processor(output_dir: str = None) -> AudioProcessor:
    """Get or create audio processor singleton."""
    global _audio_processor
    if _audio_processor is None:
        _audio_processor = AudioProcessor(output_dir)
    return _audio_processor


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def compose_video_with_audio(
    video_path: str,
    voiceover_path: str = None,
    music_path: str = None,
    output_path: str = None,
    voiceover_volume: float = 1.0,
    music_volume: float = 0.3
) -> Dict[str, Any]:
    """
    Compose video with voiceover and background music.
    
    Args:
        video_path: Input video path
        voiceover_path: Voiceover audio path
        music_path: Background music path
        output_path: Output video path
        voiceover_volume: Voiceover volume
        music_volume: Music volume
        
    Returns:
        {"success": bool, "video_path": str}
    """
    _ensure_moviepy()
    
    try:
        from moviepy.editor import VideoFileClip
        
        logger.info(f"🎬 Composing video with audio: {video_path}")
        
        video = VideoFileClip(video_path)
        processor = get_audio_processor()
        
        # Compose audio
        audio_result = processor.compose_video_audio(
            voiceover_path=voiceover_path,
            music_path=music_path,
            target_duration=video.duration,
            voiceover_volume=voiceover_volume,
            music_volume=music_volume
        )
        
        if not audio_result.get("success"):
            # Use original video without modification
            logger.warning("Audio composition failed, using original video")
            return {"success": True, "video_path": video_path, "note": "No audio added"}
        
        # Set audio on video
        video = video.set_audio(audio_result["audio"])
        
        # Export
        if not output_path:
            output_path = video_path.replace(".mp4", "_final.mp4")
        
        video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            threads=1,
            verbose=False,
            logger=None
        )
        
        video.close()
        
        logger.info(f"✅ Final video: {output_path}")
        return {"success": True, "video_path": output_path}
        
    except Exception as e:
        logger.error(f"❌ Video composition failed: {e}")
        return {"success": False, "error": str(e)}


def concatenate_video_segments(
    segment_paths: List[str],
    output_path: str = None,
    transition: str = None
) -> Dict[str, Any]:
    """
    Concatenate multiple video segments.
    
    Args:
        segment_paths: List of video file paths
        output_path: Output video path
        transition: Transition type (currently unused, for future)
        
    Returns:
        {"success": bool, "video_path": str}
    """
    _ensure_moviepy()
    
    try:
        from moviepy.editor import VideoFileClip, concatenate_videoclips
        
        logger.info(f"🎬 Concatenating {len(segment_paths)} video segments")
        
        clips = []
        for path in segment_paths:
            if os.path.exists(path):
                clips.append(VideoFileClip(path))
            else:
                logger.warning(f"Segment not found: {path}")
        
        if not clips:
            return {"success": False, "error": "No valid video segments"}
        
        final = concatenate_videoclips(clips, method="compose")
        
        if not output_path:
            output_path = "./data/files/videos/concatenated_video.mp4"
        
        final.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            threads=1,
            verbose=False,
            logger=None
        )
        
        # Cleanup
        for clip in clips:
            clip.close()
        final.close()
        
        logger.info(f"✅ Concatenated video: {output_path}")
        return {"success": True, "video_path": output_path, "duration": final.duration}
        
    except Exception as e:
        logger.error(f"❌ Concatenation failed: {e}")
        return {"success": False, "error": str(e)}
