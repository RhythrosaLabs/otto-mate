"""
Advanced Video Generation Module
================================

Professional video generation with 15+ AI models, Ken Burns effect,
audio composition, CTA cards, and brand overlays.

Ported and enhanced from printify_clean's video pipeline for:
- Ken Burns (local MoviePy processing)
- Kling, Luma, Sora-2, Veo, Pixverse, etc.
- Multi-segment commercial production
- Professional audio mixing

Dependencies (install via pip):
- moviepy
- opencv-python (cv2)
- numpy
- aiohttp
"""

import logging
import os
import time
import asyncio
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime

# Optional async HTTP client
try:
    import aiohttp
except ImportError:
    aiohttp = None

from .core import tool, ToolBase

logger = logging.getLogger(__name__)


class VideoGenerationError(Exception):
    """Custom exception for video generation errors."""
    pass


# Voice mapping for professional voiceovers (Minimax Speech compatible)
VOICE_MAP = {
    "Professional": "Calm_Woman",
    "Energetic": "Lively_Girl",
    "Luxury": "Elegant_Man",
    "Friendly": "Friendly_Person",
    "Authoritative": "Determined_Man",
    "Warm": "Wise_Woman",
    "Casual": "Casual_Guy",
    "Inspirational": "Inspirational_Girl",
    "Deep": "Deep_Voice_Man",
    "Patient": "Patient_Man",
    # Style aliases
    "Female_Calm": "Calm_Woman",
    "Female_Lively": "Lively_Girl",
    "Male_Elegant": "Elegant_Man",
    "Male_Deep": "Deep_Voice_Man",
    "Neutral": "Friendly_Person",
}

# Music style prompts for MusicGen
MUSIC_PROMPTS = {
    "Cinematic": "cinematic epic background music, dramatic, inspiring, orchestral swells",
    "Electronic": "electronic background music, modern synths, dynamic beat, professional",
    "Upbeat": "upbeat energetic background music, happy, positive, driving rhythm",
    "Ambient": "ambient atmospheric background music, calm, soothing, minimal",
    "Corporate": "corporate inspiring background music, uplifting, confident, professional",
    "Hip Hop": "hip hop beat background music, urban, cool, modern trap",
    "Jazz": "smooth jazz background music, sophisticated, elegant, saxophone",
    "Luxury": "elegant orchestral background music, sophisticated, premium feel",
    "Pop": "catchy pop background music, mainstream, upbeat, commercial",
    "Rock": "rock background music, energetic, guitar-driven, powerful",
    "Acoustic": "warm acoustic background music, friendly, inviting, guitar",
    "Dramatic": "dramatic tension background music, building suspense, cinematic",
    # Legacy compatibility
    "Professional": "corporate inspiring background music, uplifting, confident",
    "Energetic": "upbeat electronic background music, energetic, exciting",
}

# Camera direction prompts for video segments
CAMERA_DIRECTIONS = [
    "hero product shot with dynamic lighting, professional commercial style",
    "lifestyle close-up showing product in use, authentic feel",
    "bold feature highlight with smooth camera movement",
    "emotional connection shot, warm lighting",
    "closing shot with logo emphasis, call to action vibe"
]

# Visual styles for different ad tones (from printify_clean)
VISUAL_STYLES = {
    "Exciting & Energetic": "dynamic, high-energy, vibrant colors, fast-paced, bold movements",
    "Warm & Friendly": "warm lighting, friendly atmosphere, cozy environment, soft tones",
    "Professional & Trustworthy": "clean, professional, modern setting, confident presentation",
    "Fun & Playful": "bright, colorful, animated expressions, joyful energy",
    "Luxury & Premium": "elegant, sophisticated, high-end materials, golden lighting, refined",
    "Urgent & Action-Driven": "dramatic, bold, intense, action-packed, compelling",
}

# Ad tone to voice mapping
AD_TONE_VOICE_MAP = {
    "Exciting & Energetic": "Lively_Girl",
    "Warm & Friendly": "Friendly_Person",
    "Professional & Trustworthy": "Deep_Voice_Man",
    "Fun & Playful": "Casual_Guy",
    "Luxury & Premium": "Elegant_Man",
    "Urgent & Action-Driven": "Determined_Man",
}

# Ad tone to music style mapping
AD_TONE_MUSIC_MAP = {
    "Exciting & Energetic": "Energetic",
    "Warm & Friendly": "Friendly",
    "Professional & Trustworthy": "Professional",
    "Fun & Playful": "Upbeat",
    "Luxury & Premium": "Luxury",
    "Urgent & Action-Driven": "Cinematic",
}

# Rate limiting constants (from printify_clean)
VIDEO_RATE_LIMIT_DELAY = 12  # 12 seconds between video requests (Replicate limit: 6/min)


class AdvancedVideoGenerator(ToolBase):
    """
    Advanced video generation with 25+ AI models and professional features.
    
    Updated from printify_clean (Feb 2026):
    - Ken Burns (local, instant, free)
    - Sora-2 (OpenAI flagship)
    - Kling v2.5 Turbo Pro (premium)
    - Veo 3.1 Fast (audio support)
    - Pixverse v5, Leonardo Motion 2.0
    - Luma Ray 2, Hailuo 2.3 Fast
    - Wan 2.5, Seedance Pro
    """
    
    # Video Model Catalog (updated Feb 2026 from printify_clean)
    # Format: (replicate_model, supports_image_to_video, max_duration, notes)
    VIDEO_MODELS = {
        # ── Local / Free ──
        "ken_burns": (None, True, 60, "Local MoviePy processing, instant, free"),
        
        # ── OpenAI Sora ──
        "sora": ("openai/sora-2", True, 10, "OpenAI flagship with synced audio"),
        "sora2": ("openai/sora-2", True, 10, "OpenAI flagship with synced audio"),
        
        # ── Kling Family ──
        "kling": ("kwaivgi/kling-v2.5-turbo-pro", True, 10, "Pro-level text/image-to-video"),
        "kling_turbo": ("kwaivgi/kling-v2.5-turbo-pro", True, 10, "Latest Kling turbo"),
        "kling_pro": ("kwaivgi/kling-v2.5-turbo-pro", True, 10, "Alias for kling_turbo"),
        
        # ── Google Veo Family ──
        "veo": ("google/veo-3.1-fast", True, 8, "Latest Veo with context-aware audio"),
        "veo3": ("google/veo-3", True, 8, "Veo 3 high quality"),
        "veo3_fast": ("google/veo-3-fast", True, 8, "Faster Veo 3"),
        "veo31_fast": ("google/veo-3.1-fast", True, 8, "Audio support, improved"),
        "veo2": ("google/veo-2", True, 8, "4K quality"),
        
        # ── Pixverse ──
        "pixverse": ("pixverse/pixverse-v5", False, 8, "Latest Pixverse"),
        "pixverse5": ("pixverse/pixverse-v5", False, 8, "1080p"),
        "pixverse45": ("pixverse/pixverse-v4.5", False, 8, "Fast, 1080p"),
        
        # ── Luma Family ──
        "luma": ("luma/ray-2-540p", True, 5, "High quality 540p"),
        "luma_ray": ("luma/ray-2-540p", True, 5, "Ray 2 540p"),
        "luma_flash": ("luma/ray-flash-2", True, 5, "Fast 540p"),
        "luma_modify": ("luma/modify-video", True, 10, "Video modification"),
        
        # ── Leonardo ──
        "leonardo": ("leonardoai/motion-2.0", True, 5, "Motion engine, 480p"),
        
        # ── Minimax Hailuo ──
        "hailuo": ("minimax/hailuo-2.3-fast", True, 10, "Fast image-to-video"),
        "hailuo_fast": ("minimax/hailuo-2.3-fast", True, 10, "768p"),
        "minimax": ("minimax/video-01", True, 10, "General purpose"),
        
        # ── Wan Video ──
        "wan": ("wan-video/wan-2.5-t2v-fast", False, 5, "Fast T2V"),
        "wan_fast": ("wan-video/wan-2.5-t2v-fast", False, 5, "Text-to-video"),
        "wan_v2v": ("wan-video/wan-2.5-v2v-fast", True, 5, "Video-to-video transform"),
        
        # ── Bytedance Seedance ──
        "seedance": ("bytedance/seedance-1-pro-fast", False, 5, "Cinematic 3x faster"),
        "seedance_v2v": ("bytedance/seedance-1-pro-v2v", True, 5, "Video editing"),
        
        # ── Stability AI ──
        "svd": ("stability-ai/stable-video-diffusion", True, 4, "Image-to-video classic"),
        
        # ── Video Editing / Utility ──
        "upscale": ("lucataco/video-upscaler", True, 60, "Upscale videos 2x/4x"),
        "stabilize": ("lucataco/video-stabilizer", True, 60, "Stabilize shaky video"),
        "style_transfer": ("lucataco/video-style-transfer", True, 30, "Apply artistic styles"),
    }
    
    def __init__(self, replicate_api=None, api_token: str = None):
        self.replicate = replicate_api
        self.api_token = api_token or os.getenv("REPLICATE_API_TOKEN")
        
        # Output directories
        self.output_dir = Path("./data/files/videos")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir = Path("./data/files/audio")
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path("./data/files/temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    # ═══════════════════════════════════════════════════════════════════
    # URL VALIDATION AND NORMALIZATION
    # ═══════════════════════════════════════════════════════════════════
    
    async def _validate_and_normalize_image_url(self, url: str) -> Dict[str, Any]:
        """
        Validate and normalize image URL for AI video models.
        
        Some models (like Kling) require URLs with proper image extensions.
        Printify mockup URLs don't have extensions: https://images.printify.com/HEXID
        
        This function:
        1. Checks if URL has a valid image extension
        2. If not, downloads the image and re-uploads to a temp hosting service
        3. Returns either the original URL or a normalized one
        
        Returns:
            {"success": bool, "url": str, "original": str, "normalized": bool, "error": str?}
        """
        if not url:
            return {"success": False, "url": None, "error": "No URL provided"}
        
        # Check if URL already has a valid image extension
        url_lower = url.lower()
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp']
        
        has_extension = any(ext in url_lower for ext in valid_extensions)
        
        if has_extension:
            return {"success": True, "url": url, "original": url, "normalized": False}
        
        # URL needs normalization - download and get proper format
        logger.info(f"🔄 Normalizing image URL (no extension detected): {url[:60]}...")
        
        try:
            if not aiohttp:
                # Fallback: try appending .jpg as some CDNs accept it
                normalized = f"{url}.jpg" if "?" not in url else f"{url}&format=jpg"
                return {"success": True, "url": normalized, "original": url, "normalized": True}
            
            async with aiohttp.ClientSession() as session:
                # First, try a HEAD request to get content-type
                async with session.head(url, allow_redirects=True) as response:
                    if response.status != 200:
                        # Try GET if HEAD fails
                        async with session.get(url) as get_response:
                            if get_response.status != 200:
                                return {"success": False, "url": url, "error": f"Failed to fetch: HTTP {get_response.status}"}
                            content_type = get_response.headers.get('Content-Type', '')
                    else:
                        content_type = response.headers.get('Content-Type', '')
                
                # Map content-type to extension
                ext_map = {
                    'image/jpeg': '.jpg',
                    'image/jpg': '.jpg',
                    'image/png': '.png',
                    'image/webp': '.webp',
                    'image/gif': '.gif',
                }
                
                ext = None
                for ct, extension in ext_map.items():
                    if ct in content_type.lower():
                        ext = extension
                        break
                
                if not ext:
                    ext = '.jpg'  # Default fallback
                
                # Download the image
                async with session.get(url) as response:
                    if response.status != 200:
                        return {"success": False, "url": url, "error": f"Download failed: HTTP {response.status}"}
                    
                    image_data = await response.read()
                
                # Save locally with proper extension
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                local_filename = f"normalized_image_{timestamp}{ext}"
                local_path = self.temp_dir / local_filename
                
                with open(local_path, 'wb') as f:
                    f.write(image_data)
                
                logger.info(f"✅ Image saved locally: {local_path}")
                
                # Try to upload to a hosting service
                # Option 1: Use catbox.moe (free, temporary hosting)
                try:
                    upload_url = await self._upload_to_catbox(session, local_path, image_data, ext)
                    if upload_url:
                        logger.info(f"✅ Uploaded to catbox: {upload_url}")
                        return {"success": True, "url": upload_url, "original": url, "normalized": True, "local_path": str(local_path)}
                except Exception as upload_error:
                    logger.warning(f"Catbox upload failed: {upload_error}")
                
                # Option 2: Use file:// path (works for some local models)
                file_url = f"file://{local_path.absolute()}"
                
                # Option 3: Try URL with extension appended (some CDNs support this)
                extended_url = f"{url}{ext}" if "?" not in url else f"{url}&ext={ext.replace('.', '')}"
                
                return {
                    "success": True, 
                    "url": extended_url,
                    "original": url, 
                    "normalized": True,
                    "local_path": str(local_path),
                    "alternatives": [file_url, local_path.absolute().as_uri()]
                }
                
        except Exception as e:
            logger.error(f"URL normalization failed: {e}")
            # Return original URL as fallback
            return {"success": True, "url": url, "original": url, "normalized": False, "warning": str(e)}
    
    async def _upload_to_catbox(self, session: "aiohttp.ClientSession", local_path: Path, image_data: bytes, ext: str) -> Optional[str]:
        """Upload image to catbox.moe for temporary hosting with proper URL."""
        try:
            from aiohttp import FormData
            
            data = FormData()
            data.add_field('reqtype', 'fileupload')
            data.add_field('fileToUpload', 
                          image_data, 
                          filename=f"image{ext}",
                          content_type=f"image/{ext.replace('.', '')}")
            
            async with session.post('https://catbox.moe/user/api.php', data=data) as response:
                if response.status == 200:
                    result = await response.text()
                    if result.startswith('https://'):
                        return result.strip()
        except Exception as e:
            logger.warning(f"Catbox upload error: {e}")
        
        return None
    
    # ═══════════════════════════════════════════════════════════════════
    # KEN BURNS EFFECT (Local, Instant, Free)
    # ═══════════════════════════════════════════════════════════════════
    
    def generate_ken_burns_video(
        self,
        image_path: str,
        output_path: str = None,
        duration: int = 10,
        fps: int = 30,
        resolution: str = "1080p",
        zoom_type: str = "zoom_in"
    ) -> Dict[str, Any]:
        """
        Generate Ken Burns style video from image using local MoviePy processing.
        
        Args:
            image_path: Path to source image
            output_path: Path for output video (auto-generated if None)
            duration: Video duration in seconds
            fps: Frames per second
            resolution: Output resolution (720p, 1080p, 4K)
            zoom_type: Type of zoom effect (zoom_in, zoom_out, pan_right, pan_left)
            
        Returns:
            {"success": bool, "video_path": str, "duration": float}
        """
        try:
            import cv2
            import numpy as np
            from moviepy.editor import ImageSequenceClip
            
            logger.info(f"🎬 Generating Ken Burns video: {image_path}")
            
            # Read source image
            img = cv2.imread(image_path)
            if img is None:
                # Try downloading if it's a URL
                if image_path.startswith("http"):
                    import requests
                    response = requests.get(image_path, timeout=60)
                    if response.status_code == 200:
                        nparr = np.frombuffer(response.content, np.uint8)
                        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if img is None:
                    raise VideoGenerationError(f"Failed to read image: {image_path}")
            
            h, w = img.shape[:2]
            
            # Get resolution dimensions
            res_map = {
                "720p": (1280, 720),
                "1080p": (1920, 1080),
                "4K": (3840, 2160)
            }
            target_w, target_h = res_map.get(resolution, (1920, 1080))
            
            # Generate frames
            frames = []
            total_frames = duration * fps
            center_x, center_y = w // 2, h // 2
            
            for i in range(total_frames):
                progress = i / total_frames
                
                # Smooth easing (cubic ease-in-out)
                if progress < 0.5:
                    eased_progress = 2 * progress * progress
                else:
                    eased_progress = 1 - pow(-2 * progress + 2, 2) / 2
                
                # Calculate zoom/pan
                if zoom_type == "zoom_in":
                    scale = 1.0 + eased_progress * 0.4  # 1.0x to 1.4x
                elif zoom_type == "zoom_out":
                    scale = 1.4 - eased_progress * 0.4  # 1.4x to 1.0x
                elif zoom_type == "pan_right":
                    scale = 1.2
                    center_x = int(w // 2 + (w * 0.15 * eased_progress))
                elif zoom_type == "pan_left":
                    scale = 1.2
                    center_x = int(w // 2 - (w * 0.15 * eased_progress))
                else:
                    scale = 1.0
                
                # Calculate crop box
                crop_w = int(w / scale)
                crop_h = int(h / scale)
                
                x1 = max(0, min(w - crop_w, center_x - crop_w // 2))
                y1 = max(0, min(h - crop_h, center_y - crop_h // 2))
                x2 = min(w, x1 + crop_w)
                y2 = min(h, y1 + crop_h)
                
                # Crop and resize
                cropped = img[y1:y2, x1:x2]
                frame = cv2.resize(cropped, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(frame_rgb)
            
            # Create output path if not provided
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"ken_burns_{timestamp}.mp4")
            
            # Create video
            clip = ImageSequenceClip(frames, fps=fps)
            clip.write_videofile(output_path, codec="libx264", audio=False, threads=1, logger=None)
            
            logger.info(f"✅ Ken Burns video generated: {output_path}")
            
            return {
                "success": True,
                "video_path": output_path,
                "duration": duration,
                "resolution": resolution,
                "model": "ken_burns"
            }
            
        except ImportError as e:
            logger.error(f"Ken Burns requires cv2 and moviepy: {e}")
            return {"success": False, "error": f"Missing dependencies: {e}"}
        except Exception as e:
            logger.error(f"Ken Burns generation failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    # ═══════════════════════════════════════════════════════════════════
    # AI VIDEO GENERATION (Multiple Models)
    # ═══════════════════════════════════════════════════════════════════
    
    @tool(
        name="generate_ai_video",
        description="Generate PREMIUM AI video using 15+ models. Supports text-to-video and image-to-video with cinematic quality enhancements.",
        category="video"
    )
    async def generate_ai_video(
        self,
        prompt: str,
        model: str = "kling",
        image_url: str = None,
        duration: int = 5,
        resolution: str = "1080p",
        aspect_ratio: str = "16:9",
        style: str = "cinematic",
        output_path: str = None,
        motion_level: int = 2,
        cfg_scale: float = 7.5,
        negative_prompt: str = None,
        seed: int = -1
    ) -> Dict[str, Any]:
        """
        Generate PREMIUM quality video using AI models.
        
        Args:
            prompt: Video generation prompt (will be enhanced for quality)
            model: Model to use (ken_burns, kling, luma_flash, sora, veo3, etc.)
            image_url: Optional source image for image-to-video
            duration: Video duration in seconds
            resolution: Output resolution
            aspect_ratio: Aspect ratio (16:9, 9:16, 1:1)
            style: Production style - "cinematic", "commercial", "luxury", "dynamic", "ambient"
            output_path: Output path (auto-generated if None)
            motion_level: Amount of motion 1-5 (default 2, higher=more movement)
            cfg_scale: Guidance scale (default 7.5)
            negative_prompt: What to avoid in generation
            seed: Reproducibility seed (-1 for random)
            
        Returns:
            {"success": bool, "video_path": str, "video_url": str, "duration": float}
        """
        # Ken Burns is handled locally
        if model == "ken_burns":
            if not image_url:
                return {"success": False, "error": "Ken Burns requires an image"}
            
            # Download image first
            local_image = await self._download_file(image_url, "image")
            return self.generate_ken_burns_video(
                image_path=str(local_image),
                output_path=output_path,
                duration=duration,
                resolution=resolution
            )
        
        # Get model config
        model_config = self.VIDEO_MODELS.get(model)
        if not model_config:
            return {"success": False, "error": f"Unknown model: {model}. Available: {list(self.VIDEO_MODELS.keys())}"}
        
        replicate_model, supports_i2v, max_duration, _ = model_config
        
        # Validate
        if image_url and not supports_i2v:
            logger.warning(f"Model {model} doesn't support image-to-video, using text-to-video")
            image_url = None
        
        # Normalize image URL for models that require proper extensions
        # Kling, Luma, and some other models reject URLs without extensions
        if image_url and model in ["kling", "kling_turbo", "luma_flash", "luma_ray2", "luma", "hailuo"]:
            url_result = await self._validate_and_normalize_image_url(image_url)
            if url_result.get("success"):
                if url_result.get("normalized"):
                    logger.info(f"🔄 Image URL normalized for {model}: {url_result.get('url', '')[:60]}...")
                image_url = url_result.get("url")
            else:
                logger.warning(f"URL validation warning: {url_result.get('error')} - proceeding with original URL")
        
        duration = min(duration, max_duration)
        
        try:
            # Build model inputs based on model type with style enhancement
            inputs = self._build_model_inputs(
                model=model,
                prompt=prompt,
                image_url=image_url,
                duration=duration,
                aspect_ratio=aspect_ratio,
                style=style,
                motion_level=motion_level,
                cfg_scale=cfg_scale,
                negative_prompt=negative_prompt,
                seed=seed
            )
            
            logger.info(f"🎬 Generating PREMIUM {style} video with {model}: {prompt[:50]}...")
            
            # Run via Replicate
            if self.replicate:
                result = await self.replicate.run_model(
                    model=replicate_model,
                    inputs=inputs
                )
            else:
                # Direct API call
                result = await self._run_replicate_model(replicate_model, inputs)
            
            if not result.get("success"):
                return {"success": False, "error": result.get("error", "Video generation failed")}
            
            # Extract video URL
            video_url = result.get("output")
            if isinstance(video_url, list):
                video_url = video_url[0] if video_url else None
            
            if not video_url:
                return {"success": False, "error": "No video URL in response"}
            
            # Download video
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{model}_{timestamp}.mp4")
            
            local_path = await self._download_file(video_url, "video", output_path)
            
            return {
                "success": True,
                "video_path": str(local_path),
                "video_url": video_url,
                "duration": duration,
                "model": model,
                "prompt": prompt
            }
            
        except Exception as e:
            logger.error(f"Video generation failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _enhance_video_prompt(self, prompt: str, style: str = "cinematic") -> str:
        """
        Enhance video prompt for professional, commercial-quality output.
        
        Styles:
        - cinematic: Film-quality, dramatic lighting, epic scale
        - commercial: Product advertising style, clean, professional
        - luxury: High-end, elegant, sophisticated visuals
        - dynamic: Action-packed, fast cuts, energetic
        - ambient: Calm, atmospheric, artistic
        """
        style_enhancements = {
            "cinematic": (
                "cinematic 4K quality, professional color grading, dramatic lighting, "
                "shallow depth of field, smooth camera movement, film grain, "
                "anamorphic lens flare, epic scale, Hollywood production value"
            ),
            "commercial": (
                "professional product commercial, clean studio lighting, "
                "soft shadows, polished and refined, advertising quality, "
                "crisp focus, beautiful bokeh, premium brand aesthetic"
            ),
            "luxury": (
                "luxury brand aesthetic, elegant and sophisticated, golden hour lighting, "
                "silk-smooth motion, premium materials, high-end production value, "
                "refined color palette, subtle reflections, exclusive feel"
            ),
            "dynamic": (
                "dynamic camera movement, energetic pacing, action sequence, "
                "bold colors, high contrast, impactful moments, "
                "speed ramping, dramatic reveals, intense energy"
            ),
            "ambient": (
                "atmospheric and moody, soft diffused lighting, ethereal quality, "
                "gentle camera drift, serene and peaceful, artistic composition, "
                "dream-like quality, subtle color tones"
            )
        }
        
        enhancement = style_enhancements.get(style, style_enhancements["cinematic"])
        
        # Add enhancement to prompt
        enhanced = f"{prompt}, {enhancement}"
        logger.info(f"Enhanced video prompt style: {style}")
        return enhanced
    
    def _build_model_inputs(
        self,
        model: str,
        prompt: str,
        image_url: str = None,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        style: str = "cinematic",
        motion_level: int = 2,
        cfg_scale: float = 7.5,
        negative_prompt: str = None,
        seed: int = -1
    ) -> Dict[str, Any]:
        """
        Build model-specific input parameters with enhanced prompting.
        
        Advanced parameters (from printify_clean):
        - motion_level: 1-5, higher = more movement (default 2)
        - cfg_scale: Guidance scale (default 7.5)
        - negative_prompt: What to avoid in generation
        - seed: Reproducibility (-1 for random)
        """
        
        # Enhance prompt for high-quality output
        enhanced_prompt = self._enhance_video_prompt(prompt, style)
        
        # Base inputs with enhanced prompt
        inputs = {"prompt": enhanced_prompt}
        
        # Model-specific parameters with advanced Kling support from printify_clean
        if model in ["kling", "kling_turbo", "kling_pro"]:
            inputs["duration"] = duration
            inputs["aspect_ratio"] = aspect_ratio
            inputs["motion_level"] = motion_level
            inputs["cfg_scale"] = cfg_scale
            if image_url:
                inputs["image"] = image_url  # Kling uses "image" not "image_url"
            if negative_prompt:
                inputs["negative_prompt"] = negative_prompt
            if seed != -1:
                inputs["seed"] = seed
            
        elif model in ["luma_flash", "luma_ray2", "luma", "luma_ray"]:
            if image_url:
                inputs["first_frame_image"] = image_url  # Luma uses first_frame_image
            inputs["aspect_ratio"] = aspect_ratio
            
        elif model in ["veo", "veo3", "veo3_fast", "veo31_fast", "veo2"]:
            # Veo-specific parameters from printify_clean
            inputs["aspect_ratio"] = aspect_ratio
            inputs["duration"] = duration
            inputs["guidance_scale"] = cfg_scale  # Veo uses guidance_scale
            if image_url:
                inputs["first_frame_image"] = image_url  # Veo uses first_frame_image
                
        elif model in ["pixverse", "pixverse5", "pixverse45"]:
            inputs["duration"] = duration
            
        elif model in ["hailuo", "hailuo_fast"]:
            inputs["motion_level"] = motion_level
            if image_url:
                inputs["image"] = image_url
            else:
                inputs["prompt_optimizer"] = True
                
        elif model == "svd":
            if image_url:
                inputs["input_image"] = image_url
                inputs["motion_bucket_id"] = 127
                inputs["fps"] = 7
                
        elif model in ["minimax", "minimax_live"]:
            if image_url:
                inputs["first_frame_image"] = image_url
            inputs["prompt_optimizer"] = True
            
        elif model in ["sora", "sora2"]:
            # Sora-2 specific parameters from printify_clean
            inputs["aspect_ratio"] = "landscape" if aspect_ratio == "16:9" else "portrait"
            inputs["seconds"] = duration
            inputs["resolution"] = "1080p"
            inputs["include_audio"] = True  # Sora-2 supports synchronized audio
            if image_url:
                inputs["input_reference"] = image_url  # KEY: Sora uses input_reference for image-to-video
            if seed != -1:
                inputs["seed"] = seed
            
        elif model in ["wan", "wan_fast"]:
            inputs["duration"] = duration
            
        elif model in ["seedance", "seedance_v2v"]:
            inputs["duration"] = duration
            if image_url and model == "seedance_v2v":
                inputs["video"] = image_url  # For video-to-video
        
        return inputs
    
    async def _run_replicate_model(self, model: str, inputs: Dict) -> Dict[str, Any]:
        """Run model directly via Replicate API."""
        if not self.api_token:
            return {"success": False, "error": "No Replicate API token"}
        
        # Use identity/gzip encoding to avoid brotli decoding issues
        headers = {
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/json",
            "Accept-Encoding": "identity, gzip, deflate"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # Create prediction
                async with session.post(
                    f"https://api.replicate.com/v1/models/{model}/predictions",
                    headers=headers,
                    json={"input": inputs}
                ) as response:
                    if response.status >= 400:
                        error = await response.text()
                        return {"success": False, "error": error}
                    result = await response.json()
                
                # Poll for completion
                prediction_url = result.get("urls", {}).get("get")
                max_wait = 300
                start_time = time.time()
                
                while result.get("status") in ["starting", "processing"]:
                    if time.time() - start_time > max_wait:
                        return {"success": False, "error": "Generation timeout"}
                    
                    await asyncio.sleep(3)
                    async with session.get(prediction_url, headers=headers) as response:
                        result = await response.json()
                
                if result.get("status") == "succeeded":
                    return {"success": True, "output": result.get("output")}
                else:
                    return {"success": False, "error": result.get("error", "Generation failed")}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ═══════════════════════════════════════════════════════════════════
    # VOICEOVER GENERATION (Minimax Speech)
    # ═══════════════════════════════════════════════════════════════════
    
    @tool(
        name="generate_voiceover",
        description="Generate professional voiceover audio using Minimax Speech with voice style mapping.",
        category="audio"
    )
    async def generate_voiceover(
        self,
        text: str,
        voice_style: str = "Professional",
        speed: float = 1.0,
        emotion: str = "auto",
        output_path: str = None
    ) -> Dict[str, Any]:
        """
        Generate professional voiceover.
        
        Args:
            text: Text to convert to speech
            voice_style: Voice style (Professional, Energetic, Luxury, Friendly, etc.)
            speed: Speech speed (0.5-2.0)
            emotion: Voice emotion (auto, happy, excited, calm)
            output_path: Output path (auto-generated if None)
            
        Returns:
            {"success": bool, "audio_path": str, "duration_estimate": float}
        """
        try:
            voice_id = VOICE_MAP.get(voice_style, "Calm_Woman")
            
            logger.info(f"🎙️ Generating voiceover with {voice_id}: {text[:50]}...")
            
            inputs = {
                "text": text,
                "voice_id": voice_id,
                "speed": speed
            }
            if emotion != "auto":
                inputs["emotion"] = emotion
            
            if self.replicate:
                result = await self.replicate.run_model(
                    model="minimax/speech-02-hd",
                    inputs=inputs
                )
            else:
                result = await self._run_replicate_model("minimax/speech-02-hd", inputs)
            
            if not result.get("success"):
                # Fallback to Bark TTS
                logger.warning("Minimax failed, trying Bark TTS")
                if self.replicate:
                    result = await self.replicate.run_model(
                        model="cjwbw/bark",
                        inputs={"prompt": text, "text_temp": 0.7}
                    )
                else:
                    result = await self._run_replicate_model(
                        "cjwbw/bark",
                        {"prompt": text, "text_temp": 0.7}
                    )
            
            if not result.get("success"):
                return {"success": False, "error": result.get("error", "Voiceover generation failed")}
            
            audio_url = result.get("output")
            if isinstance(audio_url, list):
                audio_url = audio_url[0]
            
            # Download
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.audio_dir / f"voiceover_{timestamp}.mp3")
            
            local_path = await self._download_file(audio_url, "audio", output_path)
            
            # Estimate duration (2.5 words per second)
            duration_estimate = len(text.split()) / 2.5
            
            return {
                "success": True,
                "audio_path": str(local_path),
                "audio_url": audio_url,
                "duration_estimate": duration_estimate,
                "voice_style": voice_style,
                "voice_id": voice_id
            }
            
        except Exception as e:
            logger.error(f"Voiceover generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    # ═══════════════════════════════════════════════════════════════════
    # BACKGROUND MUSIC GENERATION (MusicGen)
    # ═══════════════════════════════════════════════════════════════════
    
    @tool(
        name="generate_background_music",
        description="Generate background music using MusicGen with style presets.",
        category="audio"
    )
    async def generate_background_music(
        self,
        duration: int = 15,
        style: str = "Corporate",
        custom_prompt: str = "",
        output_path: str = None
    ) -> Dict[str, Any]:
        """
        Generate background music.
        
        Args:
            duration: Duration in seconds (max 30)
            style: Music style (Cinematic, Corporate, Upbeat, Electronic, etc.)
            custom_prompt: Additional prompt text
            output_path: Output path (auto-generated if None)
            
        Returns:
            {"success": bool, "audio_path": str, "duration": float}
        """
        try:
            # Build prompt
            base_prompt = MUSIC_PROMPTS.get(style, MUSIC_PROMPTS["Corporate"])
            prompt = f"{base_prompt}, {custom_prompt}" if custom_prompt else base_prompt
            
            logger.info(f"🎵 Generating {duration}s background music ({style})...")
            
            inputs = {
                "prompt": prompt,
                "duration": min(duration, 30),
                "model_version": "stereo-large"
            }
            
            if self.replicate:
                result = await self.replicate.run_model(
                    model="meta/musicgen",
                    inputs=inputs
                )
            else:
                result = await self._run_replicate_model("meta/musicgen", inputs)
            
            if not result.get("success"):
                return {"success": False, "error": result.get("error", "Music generation failed")}
            
            audio_url = result.get("output")
            if isinstance(audio_url, list):
                audio_url = audio_url[0]
            
            # Download
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.audio_dir / f"music_{timestamp}.mp3")
            
            local_path = await self._download_file(audio_url, "audio", output_path)
            
            return {
                "success": True,
                "audio_path": str(local_path),
                "audio_url": audio_url,
                "duration": duration,
                "style": style
            }
            
        except Exception as e:
            logger.error(f"Music generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    # ═══════════════════════════════════════════════════════════════════
    # CTA CARD GENERATION
    # ═══════════════════════════════════════════════════════════════════
    
    def add_cta_card(
        self,
        video_path: str,
        output_path: str = None,
        cta_text: str = "Shop Now!",
        card_duration: float = 3.5,
        background_color: Tuple[int, int, int] = (0, 0, 0)
    ) -> Dict[str, Any]:
        """
        Add CTA end card to video.
        
        Args:
            video_path: Input video path
            output_path: Output path
            cta_text: Call-to-action text
            card_duration: Duration of CTA card
            background_color: RGB background color
            
        Returns:
            {"success": bool, "video_path": str}
        """
        try:
            from moviepy.editor import (
                ColorClip, CompositeVideoClip, TextClip,
                VideoFileClip, concatenate_videoclips
            )
            
            logger.info(f"Adding CTA card to video: {video_path}")
            
            video = VideoFileClip(video_path)
            w, h = video.size
            
            # Create CTA card
            bg_clip = ColorClip(size=(w, h), color=background_color).set_duration(card_duration)
            
            txt_clip = (
                TextClip(
                    cta_text,
                    fontsize=min(w, h) // 10,
                    color="white",
                    font="Arial-Bold",
                    method="caption",
                    size=(int(w * 0.8), None)
                )
                .set_position("center")
                .set_duration(card_duration)
            )
            
            cta_card = CompositeVideoClip([bg_clip, txt_clip])
            final_video = concatenate_videoclips([video, cta_card])
            
            if not output_path:
                output_path = video_path.replace(".mp4", "_cta.mp4")
            
            final_video.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                threads=1,
                logger=None
            )
            
            video.close()
            final_video.close()
            
            return {"success": True, "video_path": output_path}
            
        except ImportError:
            return {"success": False, "error": "MoviePy not installed"}
        except Exception as e:
            logger.error(f"CTA card addition failed: {e}")
            return {"success": False, "error": str(e)}
    
    # ═══════════════════════════════════════════════════════════════════
    # BRAND OVERLAY
    # ═══════════════════════════════════════════════════════════════════
    
    def add_brand_overlay(
        self,
        video_path: str,
        output_path: str = None,
        logo_path: str = None,
        primary_color: str = "#000000"
    ) -> Dict[str, Any]:
        """
        Add brand overlay (logo and color bar) to video.
        
        Args:
            video_path: Input video path
            output_path: Output path
            logo_path: Path to logo image
            primary_color: Hex color for accent bar
            
        Returns:
            {"success": bool, "video_path": str}
        """
        try:
            from moviepy.editor import (
                ColorClip, CompositeVideoClip, ImageClip, VideoFileClip
            )
            
            logger.info(f"Adding brand overlay to video: {video_path}")
            
            video = VideoFileClip(video_path)
            w, h = video.size
            
            overlays = [video]
            
            # Logo overlay
            if logo_path and os.path.exists(logo_path):
                logo = ImageClip(logo_path).set_duration(video.duration)
                logo = logo.resize(width=int(w * 0.08))
                logo = logo.set_pos(("right", "top")).margin(right=20, top=20)
                overlays.append(logo)
            
            # Color bar
            try:
                hexc = primary_color.lstrip("#")
                rgb = tuple(int(hexc[i:i+2], 16) for i in (0, 2, 4))
            except:
                rgb = (0, 0, 0)
            
            bar_height = int(h * 0.06)
            color_bar = ColorClip(size=(w, bar_height), color=rgb).set_duration(video.duration)
            color_bar = color_bar.set_pos(("center", h - bar_height))
            overlays.append(color_bar)
            
            final = CompositeVideoClip(overlays)
            
            if not output_path:
                output_path = video_path.replace(".mp4", "_branded.mp4")
            
            final.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                threads=1,
                logger=None
            )
            
            video.close()
            final.close()
            
            return {"success": True, "video_path": output_path}
            
        except ImportError:
            return {"success": False, "error": "MoviePy not installed"}
        except Exception as e:
            logger.error(f"Brand overlay failed: {e}")
            return {"success": False, "error": str(e)}
    
    # ═══════════════════════════════════════════════════════════════════
    # COMMERCIAL VIDEO PRODUCTION (from printify_clean)
    # ═══════════════════════════════════════════════════════════════════
    
    @tool(
        name="generate_commercial_script",
        description="Generate a professional ad script for product commercials",
        category="video"
    )
    async def generate_commercial_script(
        self,
        product_name: str,
        target_audience: str,
        ad_tone: str = "Professional & Trustworthy",
        key_benefits: str = "",
        call_to_action: str = "Shop Now",
        duration: int = 20
    ) -> Dict[str, Any]:
        """
        Generate sophisticated ad script following proven commercial structure.
        
        Args:
            product_name: Name of the product
            target_audience: Target audience description
            ad_tone: Tone from VISUAL_STYLES (Professional, Exciting, Luxury, etc.)
            key_benefits: Key benefits to highlight
            call_to_action: CTA text
            duration: Total duration in seconds (segments = duration // 5)
            
        Returns:
            {"success": bool, "script": str, "segments": list}
        """
        import re
        
        num_segments = duration // 5
        
        script_prompt = f"""You are an expert advertising copywriter creating a {duration}-second commercial script.

Product: {product_name}
Target Audience: {target_audience}
Tone: {ad_tone}
Key Benefits: {key_benefits}
Call to Action: {call_to_action}

Create a {num_segments}-segment script (5 seconds each) following this proven commercial structure:

Segment 1 - HOOK/PROBLEM (5s):
- Grab attention immediately with a relatable problem or exciting hook
- 6-8 words maximum - punchy and memorable
- Create emotional connection or curiosity

Segment 2 - SOLUTION (5s):
- Introduce {product_name} as the perfect solution
- 6-8 words - highlight the "aha" moment
- Show transformation or relief

Segment 3 - CALL TO ACTION (5s):
- Strong, urgent call to action: {call_to_action}
- 6-8 words - clear, action-oriented, and compelling
- Create sense of urgency or exclusivity

Each segment must be exactly 6-8 words for perfect 5-second delivery.
Make it persuasive, memorable, and emotionally resonant.
Label each section as '1:', '2:', and '3:'.

Write ONLY the script segments - no additional commentary."""

        try:
            # Use Replicate for text generation
            if self.replicate:
                result = await self.replicate.run_model(
                    model="meta/meta-llama-3-70b-instruct",
                    inputs={
                        "prompt": script_prompt,
                        "max_tokens": 400,
                        "temperature": 0.8
                    }
                )
                full_script = result.get("output", "")
            else:
                # Direct API call
                result = await self._run_replicate_model(
                    "meta/meta-llama-3-70b-instruct",
                    {
                        "prompt": script_prompt,
                        "max_tokens": 400,
                        "temperature": 0.8
                    }
                )
                full_script = result.get("output", "")
            
            # Extract segments
            segments = re.findall(r"\d+:\s*(.+)", str(full_script))
            
            if len(segments) < num_segments:
                # Fallback segments
                segments = [
                    f"Discover {product_name} - Your solution awaits",
                    f"{product_name} transforms your experience completely",
                    f"{call_to_action} - Limited time only"
                ][:num_segments]
            
            return {
                "success": True,
                "script": full_script,
                "segments": segments[:num_segments],
                "product": product_name,
                "ad_tone": ad_tone
            }
            
        except Exception as e:
            logger.error(f"Script generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    @tool(
        name="generate_multi_segment_video",
        description="Generate multi-segment commercial video with rate limiting and professional orchestration",
        category="video"
    )
    async def generate_multi_segment_video(
        self,
        script_segments: List[str],
        product_name: str = "",
        product_image: str = None,
        ad_tone: str = "Professional & Trustworthy",
        model: str = "kling",
        aspect_ratio: str = "16:9",
        motion_level: int = 2,
        cfg_scale: float = 7.5
    ) -> Dict[str, Any]:
        """
        Generate multi-segment video with rate limiting between segments.
        
        From printify_clean: Uses 12-second delay between video requests
        to avoid Replicate rate limits (6 requests/minute).
        
        Args:
            script_segments: List of script text for each segment
            product_name: Product being advertised
            product_image: Optional product image for image-to-video
            ad_tone: Tone from VISUAL_STYLES
            model: Video model (kling, sora, veo3, etc.)
            aspect_ratio: Output aspect ratio
            motion_level: 1-5, movement amount
            cfg_scale: Guidance scale
            
        Returns:
            {"success": bool, "video_paths": list, "segments_completed": int}
        """
        logger.info(f"🎥 PHASE 1: VIDEO GENERATION - Creating {len(script_segments)} video segments (5 seconds each)")
        logger.info(f"   📹 Style: {ad_tone}")
        logger.info(f"   ⏱️ Estimated time: ~{len(script_segments) * 30} seconds")
        
        video_paths = []
        style_description = VISUAL_STYLES.get(ad_tone, "professional, appealing")
        
        for i, segment in enumerate(script_segments):
            try:
                # Rate limit: Wait between video requests (printify_clean pattern)
                if i > 0:
                    logger.info(f"   ⏱️ Rate limit cooldown: Waiting {VIDEO_RATE_LIMIT_DELAY}s before next video...")
                    await asyncio.sleep(VIDEO_RATE_LIMIT_DELAY)
                
                progress_pct = int((i / len(script_segments)) * 100)
                logger.info(f"🎬 Generating video segment {i+1}/{len(script_segments)} ({progress_pct}% complete)...")
                
                # Build commercial video prompt
                if product_image and i == 0:
                    # Hero segment with product image
                    video_prompt = (
                        f"Transform this product into a beautiful commercial scene. "
                        f"Cinematic slow camera movement. {style_description}. "
                        f"Professional lighting, 4K quality, smooth motion. "
                        f"Visual narrative: {segment}. No text overlays."
                    )
                else:
                    video_prompt = (
                        f"Commercial advertisement: {style_description}. "
                        f"Professional shot for {product_name}. "
                        f"Cinematic quality, engaging visuals. "
                        f"Visual narrative: {segment}. No text overlays."
                    )
                
                # Generate video
                result = await self.generate_ai_video(
                    prompt=video_prompt,
                    model=model,
                    image_url=product_image if i == 0 else None,
                    duration=5,
                    aspect_ratio=aspect_ratio,
                    style="commercial",
                    motion_level=motion_level,
                    cfg_scale=cfg_scale
                )
                
                if not result.get("success"):
                    logger.error(f"   ❌ Segment {i+1} failed: {result.get('error')}")
                    continue
                
                video_paths.append(result.get("video_path"))
                logger.info(f"   ✅ Video segment {i+1} complete")
                
            except Exception as e:
                logger.error(f"Segment {i+1} generation failed: {e}")
                continue
        
        if not video_paths:
            return {"success": False, "error": "No video segments were generated"}
        
        return {
            "success": True,
            "video_paths": video_paths,
            "segments_completed": len(video_paths),
            "total_segments": len(script_segments)
        }
    
    # ═══════════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════════════════════════
    
    async def _download_file(
        self,
        url: str,
        file_type: str = "file",
        output_path: str = None
    ) -> Path:
        """Download file from URL."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=180)) as response:
                    if response.status != 200:
                        raise Exception(f"Download failed: HTTP {response.status}")
                    
                    content = await response.read()
                    
                    if not output_path:
                        ext = {"video": ".mp4", "audio": ".mp3", "image": ".png"}.get(file_type, "")
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        output_path = str(self.temp_dir / f"{file_type}_{timestamp}{ext}")
                    
                    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                    Path(output_path).write_bytes(content)
                    
                    logger.info(f"Downloaded {file_type}: {output_path}")
                    return Path(output_path)
                    
        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise


    # ═══════════════════════════════════════════════════════════════════
    # ASSEMBLE FINAL VIDEO WITH AUDIO (from printify_clean)
    # ═══════════════════════════════════════════════════════════════════
    
    @tool(
        name="assemble_video_with_audio",
        description="Assemble final video by combining video clips with voiceover and background music",
        category="video"
    )
    async def assemble_video_with_audio(
        self,
        video_paths: List[str],
        voiceover_path: str = None,
        music_path: str = None,
        output_path: str = None,
        voiceover_volume: float = 1.0,
        music_volume: float = 0.25,
        add_cta: bool = False,
        cta_text: str = "Shop Now!"
    ) -> Dict[str, Any]:
        """
        Assemble final video with sophisticated audio/video sync.
        From printify_clean's proven multi-attempt encoding strategy.
        
        Args:
            video_paths: List of video clip paths to concatenate
            voiceover_path: Path to voiceover audio
            music_path: Path to background music
            output_path: Output path (auto-generated if None)
            voiceover_volume: Voiceover volume multiplier (default 1.0)
            music_volume: Music volume multiplier (default 0.25)
            add_cta: Whether to add CTA endcard
            cta_text: Call-to-action text
            
        Returns:
            {"success": bool, "video_path": str, "duration": float}
        """
        try:
            from moviepy.editor import (
                AudioFileClip, CompositeAudioClip, VideoFileClip,
                concatenate_audioclips, concatenate_videoclips
            )
            import numpy as np
            from moviepy.audio.AudioClip import AudioArrayClip
            
            logger.info("🎬 PHASE 4: FINAL ASSEMBLY - Combining all elements")
            logger.info(f"   📊 Components: {len(video_paths)} video clips + voiceover + music")
            
            # Load and combine video segments
            logger.info(f"   📼 Loading {len(video_paths)} video segments...")
            clips = [VideoFileClip(path) for path in video_paths if os.path.exists(path)]
            
            if not clips:
                return {"success": False, "error": "No valid video clips found"}
            
            logger.info("   🔗 Concatenating video clips...")
            final_video = concatenate_videoclips(clips, method="compose")
            video_duration = final_video.duration
            logger.info(f"   ⏱️ Video duration: {video_duration:.2f}s")
            
            audio_clips = []
            
            # Load voiceover
            if voiceover_path and os.path.exists(voiceover_path):
                logger.info("   🎙️ Loading voiceover audio...")
                voice_clip = AudioFileClip(voiceover_path)
                
                # Sync with video duration
                if voice_clip.duration > video_duration:
                    voice_clip = voice_clip.subclip(0, video_duration)
                elif voice_clip.duration < video_duration:
                    # Pad with silence
                    silence_duration = video_duration - voice_clip.duration
                    silence_array = np.zeros((int(silence_duration * 22050), 2))
                    silence_clip = AudioArrayClip(silence_array, fps=22050)
                    voice_clip = concatenate_audioclips([voice_clip, silence_clip])
                
                voice_clip = voice_clip.volumex(voiceover_volume)
                audio_clips.append(voice_clip)
            
            # Load background music
            if music_path and os.path.exists(music_path):
                logger.info("   🎵 Loading background music...")
                music_clip = AudioFileClip(music_path)
                
                # Loop/trim to match video duration
                if music_clip.duration > video_duration:
                    music_clip = music_clip.subclip(0, video_duration)
                elif music_clip.duration < video_duration:
                    loops_needed = int(video_duration / music_clip.duration) + 1
                    music_clip = concatenate_audioclips([music_clip] * loops_needed)
                    music_clip = music_clip.subclip(0, video_duration)
                
                music_clip = music_clip.volumex(music_volume)
                audio_clips.append(music_clip)
            
            # Mix audio
            if audio_clips:
                logger.info("   🎚️ Mixing audio tracks...")
                final_audio = CompositeAudioClip(audio_clips)
                final_audio = final_audio.subclip(0, video_duration)
                final_video = final_video.set_audio(final_audio)
            
            # Generate output path
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"final_commercial_{timestamp}.mp4")
            
            # Multi-attempt encoding (proven approach from printify_clean)
            encoding_success = False
            
            # Attempt 1: Standard encoding
            try:
                logger.info("   💾 Encoding final video (standard quality)...")
                final_video.write_videofile(
                    output_path,
                    codec="libx264",
                    audio_codec="aac",
                    fps=24,
                    bitrate="2000k",
                    verbose=False,
                    logger=None,
                    preset="ultrafast"
                )
                encoding_success = True
            except Exception as e:
                logger.warning(f"Standard encoding failed: {str(e)[:100]}")
            
            # Attempt 2: Simplified encoding
            if not encoding_success:
                try:
                    logger.info("   💾 Encoding attempt 2: Simplified encoding...")
                    final_video.write_videofile(
                        output_path,
                        codec="libx264",
                        audio_codec="aac",
                        fps=24,
                        verbose=False,
                        logger=None,
                        preset="ultrafast",
                        threads=1
                    )
                    encoding_success = True
                except Exception as e:
                    logger.warning(f"Simplified encoding failed: {str(e)[:100]}")
            
            # Cleanup
            for clip in clips:
                try:
                    clip.close()
                except:
                    pass
            
            if not encoding_success:
                return {"success": False, "error": "All encoding attempts failed"}
            
            # Add CTA if requested
            if add_cta:
                cta_result = self.add_cta_card(output_path, cta_text=cta_text)
                if cta_result.get("success"):
                    output_path = cta_result["video_path"]
            
            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"✅ Video assembly complete! Final video ready.")
            logger.info(f"   📦 Output: {output_path}")
            logger.info(f"   💾 File size: {file_size_mb:.2f} MB")
            
            return {
                "success": True,
                "video_path": output_path,
                "duration": video_duration,
                "file_size_mb": round(file_size_mb, 2)
            }
            
        except ImportError:
            return {"success": False, "error": "MoviePy not installed. Run: pip install moviepy"}
        except Exception as e:
            logger.error(f"Video assembly failed: {e}")
            return {"success": False, "error": str(e)}
    
    # ═══════════════════════════════════════════════════════════════════
    # END-TO-END COMMERCIAL CREATION (from printify_clean)
    # ═══════════════════════════════════════════════════════════════════
    
    @tool(
        name="create_full_commercial",
        description="Create a complete product commercial with script, video segments, voiceover, and music",
        category="video"
    )
    async def create_full_commercial(
        self,
        product_name: str,
        target_audience: str = "General consumers",
        ad_tone: str = "Professional & Trustworthy",
        key_benefits: str = "",
        call_to_action: str = "Shop Now",
        duration: int = 20,
        product_image: str = None,
        video_model: str = "kling",
        add_cta_card: bool = True,
        include_voiceover: bool = True,
        include_music: bool = True
    ) -> Dict[str, Any]:
        """
        Complete end-to-end product ad creation pipeline.
        From printify_clean's AdvancedVideoProducer.create_product_ad().
        
        This is the full commercial workflow:
        1. Generate commercial script (3-4 segments)
        2. Generate video for each segment
        3. Generate professional voiceover
        4. Generate background music
        5. Assemble everything into final video
        6. Add CTA endcard
        
        Args:
            product_name: Name of the product
            target_audience: Target demographic
            ad_tone: Tone/style from VISUAL_STYLES
            key_benefits: Key product benefits
            call_to_action: CTA text
            duration: Target duration in seconds
            product_image: Optional product image for image-to-video
            video_model: Video model to use
            add_cta_card: Add CTA endcard
            include_voiceover: Include professional voiceover
            include_music: Include background music
            
        Returns:
            {"success": bool, "video_path": str, "script": str, "components": dict}
        """
        try:
            logger.info(f"🎬 CREATING FULL COMMERCIAL FOR: {product_name}")
            
            components = {
                "script_segments": [],
                "video_paths": [],
                "voiceover_path": None,
                "music_path": None
            }
            
            # Step 1: Generate script
            logger.info("📝 Step 1: Generating commercial script...")
            script_result = await self.generate_commercial_script(
                product_name=product_name,
                target_audience=target_audience,
                ad_tone=ad_tone,
                key_benefits=key_benefits,
                call_to_action=call_to_action,
                duration=duration
            )
            
            if not script_result.get("success"):
                return {"success": False, "error": f"Script generation failed: {script_result.get('error')}"}
            
            script_segments = script_result.get("segments", [])
            components["script_segments"] = script_segments
            full_script = " ".join(script_segments)
            
            # Step 2: Generate video segments
            logger.info("🎥 Step 2: Generating video segments...")
            video_result = await self.generate_multi_segment_video(
                script_segments=script_segments,
                product_name=product_name,
                product_image=product_image,
                ad_tone=ad_tone,
                model=video_model
            )
            
            if not video_result.get("success"):
                return {"success": False, "error": f"Video generation failed: {video_result.get('error')}"}
            
            video_paths = video_result.get("video_paths", [])
            components["video_paths"] = video_paths
            
            # Step 3: Generate voiceover
            if include_voiceover:
                logger.info("🎙️ Step 3: Generating voiceover...")
                voice_result = await self.generate_voiceover(
                    text=full_script,
                    tone=ad_tone
                )
                
                if voice_result.get("success"):
                    components["voiceover_path"] = voice_result.get("audio_path")
            
            # Step 4: Generate background music
            if include_music:
                logger.info("🎵 Step 4: Generating background music...")
                music_style = AD_TONE_MUSIC_MAP.get(ad_tone, "Professional")
                music_result = await self.generate_background_music(
                    duration=duration,
                    style=music_style,
                    custom_prompt=f"commercial for {product_name}"
                )
                
                if music_result.get("success"):
                    components["music_path"] = music_result.get("audio_path")
            
            # Step 5: Assemble final video
            logger.info("🎬 Step 5: Assembling final video...")
            assembly_result = await self.assemble_video_with_audio(
                video_paths=video_paths,
                voiceover_path=components.get("voiceover_path"),
                music_path=components.get("music_path"),
                add_cta=add_cta_card,
                cta_text=call_to_action
            )
            
            if not assembly_result.get("success"):
                return {"success": False, "error": f"Assembly failed: {assembly_result.get('error')}"}
            
            logger.info(f"✅ COMMERCIAL COMPLETE: {assembly_result.get('video_path')}")
            
            return {
                "success": True,
                "video_path": assembly_result.get("video_path"),
                "duration": assembly_result.get("duration"),
                "script": full_script,
                "components": components
            }
            
        except Exception as e:
            logger.error(f"Commercial creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    # ═══════════════════════════════════════════════════════════════════
    # YOUTUBE UPLOAD (from printify_clean)
    # ═══════════════════════════════════════════════════════════════════
    
    @tool(
        name="upload_to_youtube",
        description="Upload a video to YouTube with AI-optimized metadata for virality",
        category="distribution"
    )
    async def upload_to_youtube(
        self,
        video_path: str,
        title: str = None,
        description: str = None,
        product_name: str = None,
        target_audience: str = None,
        category: str = "22",  # People & Blogs
        privacy: str = "private",
        tags: List[str] = None,
        use_ai_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Upload video to YouTube with AI-generated viral metadata.
        
        From printify_clean's YouTubeUploadService.
        
        Args:
            video_path: Path to video file
            title: Video title (AI-generated if None)
            description: Video description (AI-generated if None)
            product_name: Product name for AI metadata
            target_audience: Target audience for AI metadata
            category: YouTube category ID
            privacy: Privacy setting (private, unlisted, public)
            tags: Video tags
            use_ai_metadata: Use AI to generate viral title/description
            
        Returns:
            {"success": bool, "video_id": str, "url": str}
        """
        try:
            # Check for YouTube credentials
            client_secrets = os.getenv("YOUTUBE_CLIENT_SECRETS_PATH", "./client_secret.json")
            token_path = os.getenv("YOUTUBE_TOKEN_PATH", "./token.pickle")
            
            if not os.path.exists(video_path):
                return {"success": False, "error": f"Video not found: {video_path}"}
            
            # Generate AI metadata if requested
            if use_ai_metadata and product_name:
                logger.info("🤖 Generating AI-optimized YouTube metadata...")
                
                # Viral title templates
                viral_templates = [
                    f"{product_name} - You Won't Believe What Happens!",
                    f"This {product_name} Changed Everything",
                    f"Why Everyone is Talking About {product_name}",
                    f"{product_name}: The Secret They Don't Want You to Know",
                    f"I Tried {product_name} - Here's What Happened"
                ]
                
                import random
                if not title:
                    title = random.choice(viral_templates)
                
                if not description:
                    description = f"""🔥 {product_name} - The Ultimate Review & Demo

In this video, we explore everything you need to know about {product_name}.

✨ Key Features:
• Premium quality design
• Perfect for {target_audience or 'everyone'}
• Limited availability

👉 Shop Now: [Link in description]

🔔 Subscribe for more amazing product reviews!

#ProductReview #{product_name.replace(' ', '')} #Trending #Viral #MustHave
"""
            
            if not title:
                title = f"Product Video - {datetime.now().strftime('%Y%m%d')}"
            
            if not description:
                description = "Product showcase video"
            
            # Try to upload via Google API
            try:
                from googleapiclient.discovery import build
                from googleapiclient.http import MediaFileUpload
                from google.oauth2.credentials import Credentials
                import pickle
                
                if not os.path.exists(token_path):
                    return {
                        "success": False,
                        "error": "YouTube authentication required. Run: python setup_youtube.py",
                        "video_path": video_path,
                        "generated_title": title,
                        "generated_description": description
                    }
                
                with open(token_path, "rb") as token:
                    creds = pickle.load(token)
                
                youtube = build("youtube", "v3", credentials=creds)
                
                body = {
                    "snippet": {
                        "title": title[:100],  # YouTube limit
                        "description": description[:5000],
                        "tags": tags or ["product", "review", "viral"],
                        "categoryId": category
                    },
                    "status": {
                        "privacyStatus": privacy,
                        "selfDeclaredMadeForKids": False
                    }
                }
                
                media = MediaFileUpload(video_path, mimetype="video/*", resumable=True)
                
                request = youtube.videos().insert(
                    part="snippet,status",
                    body=body,
                    media_body=media
                )
                
                response = request.execute()
                video_id = response.get("id")
                
                logger.info(f"✅ YouTube upload complete: https://youtube.com/watch?v={video_id}")
                
                return {
                    "success": True,
                    "video_id": video_id,
                    "url": f"https://youtube.com/watch?v={video_id}",
                    "title": title,
                    "privacy": privacy
                }
                
            except ImportError:
                return {
                    "success": False,
                    "error": "Google API client not installed. Run: pip install google-api-python-client google-auth",
                    "video_path": video_path,
                    "generated_title": title,
                    "generated_description": description
                }
                
        except Exception as e:
            logger.error(f"YouTube upload failed: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
_video_generator = None


def get_video_generator(replicate_api=None, api_token=None) -> AdvancedVideoGenerator:
    """Get or create video generator singleton."""
    global _video_generator
    if _video_generator is None:
        _video_generator = AdvancedVideoGenerator(replicate_api, api_token)
    elif replicate_api:
        _video_generator.replicate = replicate_api
    return _video_generator
