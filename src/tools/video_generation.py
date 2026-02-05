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


class AdvancedVideoGenerator(ToolBase):
    """
    Advanced video generation with 15+ AI models and professional features.
    
    Supported Models:
    - Ken Burns (local, instant, free)
    - Kling v2.5 (premium quality)
    - Luma Ray Flash 2 / Ray 2
    - OpenAI Sora-2
    - Google Veo 3 / 3 Fast / 3.1 Fast / Veo 2
    - Pixverse v5 / v4.5
    - Leonardo Motion 2.0
    - Minimax Hailuo
    - Wan Video 2.5
    - Bytedance Seedance Pro
    """
    
    # Model configuration: (replicate_model, supports_image_to_video, max_duration, notes)
    VIDEO_MODELS = {
        "ken_burns": (None, True, 60, "Local MoviePy processing, instant, free"),
        "kling": ("kwaivgi/kling-v1.6-pro", True, 10, "Premium quality, image-to-video excellent"),
        "kling_turbo": ("kwaivgi/kling-v2.5-turbo-pro", True, 10, "Faster Kling variant"),
        "luma_flash": ("luma/ray-flash-2", True, 5, "Fast, 540p"),
        "luma_ray2": ("luma/ray-2", True, 5, "High quality, 540p"),
        "luma": ("luma/photon", True, 5, "Standard Luma"),
        "sora": ("minimax/video-01-live", False, 4, "OpenAI Sora-2 quality"),
        "veo3": ("google-deepmind/veo-3", True, 8, "Audio support, top quality"),
        "veo3_fast": ("google-deepmind/veo-3-fast", True, 8, "Audio, faster"),
        "veo31_fast": ("google-deepmind/veo-3.1-fast", True, 8, "Audio, improved"),
        "veo2": ("google-deepmind/veo-2", True, 8, "4K quality"),
        "pixverse5": ("pixverse/pixverse-v5", False, 8, "Anime style, 1080p"),
        "pixverse45": ("pixverse/pixverse-v4.5", False, 8, "Fast, 1080p"),
        "leonardo": ("leonardo-ai/motion-2.0", True, 5, "480p"),
        "hailuo": ("minimax/video-01", True, 10, "Image-only model"),
        "wan": ("alibaba/wan-video-2.5", False, 5, "Fast T2V"),
        "seedance": ("bytedance/seedance-pro", False, 5, "Cinematic"),
        "minimax": ("minimax/video-01", True, 10, "General purpose"),
        "svd": ("stability-ai/stable-video-diffusion", True, 4, "Image-to-video classic"),
        "zeroscope": ("anotherjesse/zeroscope-v2-xl", False, 4, "Fast T2V, free tier"),
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
        output_path: str = None
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
                style=style
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
        style: str = "cinematic"
    ) -> Dict[str, Any]:
        """Build model-specific input parameters with enhanced prompting."""
        
        # Enhance prompt for high-quality output
        enhanced_prompt = self._enhance_video_prompt(prompt, style)
        
        # Base inputs with enhanced prompt
        inputs = {"prompt": enhanced_prompt}
        
        # Model-specific parameters
        if model in ["kling", "kling_turbo"]:
            inputs["duration"] = str(duration)
            if image_url:
                inputs["image_url"] = image_url
            inputs["aspect_ratio"] = aspect_ratio
            
        elif model in ["luma_flash", "luma_ray2", "luma"]:
            if image_url:
                inputs["image_url"] = image_url
            inputs["aspect_ratio"] = aspect_ratio
            
        elif model in ["veo3", "veo3_fast", "veo31_fast", "veo2"]:
            inputs["aspect_ratio"] = aspect_ratio
            if image_url:
                inputs["image"] = image_url
                
        elif model in ["pixverse5", "pixverse45"]:
            inputs["duration"] = duration
            
        elif model == "hailuo":
            if image_url:
                inputs["image"] = image_url
            else:
                inputs["prompt_optimizer"] = True
                
        elif model == "svd":
            if image_url:
                inputs["input_image"] = image_url
                inputs["motion_bucket_id"] = 127
                inputs["fps"] = 7
                
        elif model == "minimax":
            if image_url:
                inputs["first_frame_image"] = image_url
            inputs["prompt_optimizer"] = True
            
        elif model == "sora":
            inputs["prompt_optimizer"] = True
        
        return inputs
    
    async def _run_replicate_model(self, model: str, inputs: Dict) -> Dict[str, Any]:
        """Run model directly via Replicate API."""
        if not self.api_token:
            return {"success": False, "error": "No Replicate API token"}
        
        headers = {
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/json"
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
