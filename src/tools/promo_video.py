"""
Product Promo Video Generation Service
=======================================

Professional multi-segment commercial production pipeline:
1. Fetch mockup images from Printify products
2. Generate AI videos using 15+ models (Ken Burns, Kling, Luma, Sora, Veo, etc.)
3. Create professional voiceovers with voice mapping
4. Generate background music with style presets
5. Mix audio (voiceover + music with volume control)
6. Add CTA cards and brand overlays
7. Compose final multi-segment commercial

Ported and enhanced from printify_clean's advanced video pipeline.
"""

import logging
import asyncio
import os
import re
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from .core import tool, ToolBase

# Import advanced video and audio modules
try:
    from .video_generation import (
        AdvancedVideoGenerator, get_video_generator,
        VOICE_MAP, MUSIC_PROMPTS, CAMERA_DIRECTIONS
    )
    from .audio_processing import (
        AudioProcessor, get_audio_processor,
        compose_video_with_audio, concatenate_video_segments
    )
except ImportError:
    # Fallback if modules not available
    VOICE_MAP = {"Professional": "Calm_Woman", "Energetic": "Lively_Girl", "Luxury": "Sophisticated", "Warm": "Friendly_Male"}
    MUSIC_PROMPTS = {
        "Cinematic": "epic cinematic orchestral soundtrack, dramatic swells, Hans Zimmer style, emotional and powerful",
        "Corporate": "professional upbeat corporate background music, inspiring, motivational",
        "Upbeat": "energetic upbeat electronic pop music, catchy rhythm, feel-good vibes",
        "Electronic": "modern electronic ambient music, synth pads, futuristic",
        "Luxury": "elegant sophisticated jazz piano, smooth and refined, high-end feel",
        "Emotional": "touching emotional piano music, heartfelt, inspiring",
        "Epic": "epic trailer music, powerful drums, orchestral hits, action movie quality",
        "Chill": "relaxing lofi hip hop beats, calm ambient, peaceful vibes"
    }
    CAMERA_DIRECTIONS = [
        "cinematic hero product shot with dramatic lighting and slow dolly zoom",
        "lifestyle close-up showing product in elegant use, bokeh background",
        "dynamic rotating beauty shot with studio lighting reflections",
        "bold closing shot with dramatic push-in, product centered with rim lighting"
    ]

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# ENHANCED SCRIPT GENERATION FOR PREMIUM COMMERCIALS
# ═══════════════════════════════════════════════════════════════════

SCRIPT_PROMPT_TEMPLATE = """You are an AWARD-WINNING video commercial scriptwriter who creates Apple/Nike/Tesla-level advertisements.

Create a {duration}-second PREMIUM advertisement script for '{product_name}'.

Product Description: {product_description}

The video will be {duration} seconds with {segment_count} segments of ~{segment_duration} seconds each.

PRODUCTION QUALITY REQUIREMENTS:
🎬 Script Style: Premium brand commercial (think Apple, Nike, Tesla quality)
🎯 Hook: Open with an EMOTIONAL question or bold statement that stops scrolling
🎭 Storytelling: Use the Problem → Desire → Solution → Transformation arc
🔊 Voiceover: Short, powerful sentences. No filler words. Each word counts.
⚡ Pacing: Build tension, then release. Create rhythm.
🎨 Visual Direction: Include specific camera movements and lighting notes

SEGMENT STRUCTURE:
1: HOOK (2-3 sec) - Emotional question OR bold contrarian statement
2: PAIN/DESIRE (3-4 sec) - Connect with viewer's aspiration or frustration  
3: SOLUTION (3-4 sec) - Present product as the answer with key differentiator
4: TRANSFORMATION (2-3 sec) - Show the after-state, the better life
5: CTA (2 sec) - Single, clear action with urgency

WRITING RULES:
✅ Maximum 8-12 words per segment voiceover
✅ Use sensory words: feel, experience, discover, transform
✅ Include ONE specific, memorable detail about the product
✅ End with action verb CTA: "Get yours", "Order now", "Experience it"
❌ NO generic phrases like "Check out" or "Amazing quality"
❌ NO listing features - focus on FEELINGS and TRANSFORMATION

Output format:
Segment 1: [HOOK - voiceover text]
Visual: [Detailed camera direction with lighting]

Segment 2: [PAIN/DESIRE - voiceover text]
Visual: [Detailed camera direction]

... continue for all segments

CTA: [Single powerful phrase]

FULL VOICEOVER: [All segments combined for TTS]"""

# Enhanced camera directions for each segment type
ENHANCED_CAMERA_DIRECTIONS = {
    "hook": [
        "slow-motion extreme close-up, dramatic rim lighting, shallow depth of field",
        "aerial pullback revealing product, golden hour lighting, cinematic scope",
        "macro lens detail shot with water droplets, studio lighting, 4K clarity",
        "dramatic silhouette reveal with backlight, dust particles in air"
    ],
    "feature": [
        "smooth 360° orbit around product, soft studio lighting, reflection highlights",
        "dolly zoom (vertigo effect) emphasizing product details, dramatic shadows",
        "rack focus from blurred foreground to sharp product reveal",
        "time-lapse of product in use, lifestyle setting, natural lighting"
    ],
    "lifestyle": [
        "medium shot of product in elegant hands, bokeh background, warm tones",
        "tracking shot following product through beautiful environment",
        "split-screen showing before/after transformation, clean transitions",
        "slow-motion interaction with product, soft diffused lighting"
    ],
    "closing": [
        "epic push-in to product hero shot, dramatic lighting surge, logo fade-in",
        "product centered on clean backdrop, spotlight illumination, subtle particle effects",
        "pull-out to reveal product in aspirational setting, sunset/golden hour",
        "fade to black with product glow remaining, minimal text overlay"
    ]
}

# Professional transition types for segment connections
TRANSITION_STYLES = [
    "smooth crossfade",
    "whip pan",
    "light flash transition", 
    "morph cut",
    "zoom through",
    "slide transition"
]


class PromoVideoService(ToolBase):
    """
    Professional multi-segment commercial production.
    
    Features:
    - 15+ AI video models (Ken Burns, Kling, Luma, Sora, Veo, Pixverse, etc.)
    - Multi-segment commercial generation (2-6 segments)
    - Professional voiceover with voice style mapping
    - Background music with style presets
    - Audio mixing (voiceover + music with volume control)
    - CTA cards and brand overlays
    - Full MoviePy composition pipeline
    
    Workflow:
    1. Get product mockup images (from Printify or URL)
    2. Generate video script with segments
    3. Generate video segment for each script section
    4. Generate voiceover narration
    5. Generate background music
    6. Mix audio with proper volume levels
    7. Concatenate video segments
    8. Add CTA card and brand overlay
    9. Compose final video with audio
    """
    
    # Available video models
    VIDEO_MODELS = [
        "ken_burns",    # Local, instant, free
        "kling",        # Premium quality
        "kling_turbo",  # Faster
        "luma_flash",   # Fast, 540p
        "luma_ray2",    # High quality
        "sora",         # Sora-2 quality
        "veo3",         # Google, audio support
        "veo3_fast",    # Google, faster
        "veo2",         # 4K quality
        "pixverse5",    # Anime style
        "hailuo",       # Image-only
        "minimax",      # General purpose
        "svd",          # Classic I2V
        "zeroscope",    # Free tier
    ]
    
    def __init__(
        self,
        replicate_api=None,
        anthropic_client=None,
        printify_tools=None
    ):
        self.replicate = replicate_api
        self.anthropic = anthropic_client
        self.printify = printify_tools
        
        # Initialize advanced video generator
        try:
            self.video_generator = get_video_generator(replicate_api)
        except:
            self.video_generator = None
        
        # Initialize audio processor
        try:
            self.audio_processor = get_audio_processor()
        except:
            self.audio_processor = None
        
        # Output directories
        self.output_dir = Path("./data/files/videos")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.audio_dir = Path("./data/files/audio")
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        self.temp_dir = Path("./data/files/temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Default settings
        self.default_duration = 15  # seconds
        self.default_segment_count = 3
        self.default_video_model = "kling"
        self.default_voice_style = "Professional"
        self.default_music_style = "Corporate"
    
    async def _ensure_public_url(self, file_path: str) -> Optional[str]:
        """
        Ensure file is accessible via a public URL.
        
        For local files or localhost URLs, uploads to a temporary host (catbox.moe).
        External URLs are returned as-is.
        """
        import aiohttp
        from aiohttp import FormData
        
        # External URLs - return as-is (but not localhost)
        if file_path.startswith("http") and "localhost" not in file_path and "127.0.0.1" not in file_path:
            return file_path
        
        logger.info(f"🔄 Converting local file to public URL: {file_path[:60]}...")
        
        try:
            file_data = None
            filename = "file"
            content_type = "image/png"
            
            if file_path.startswith("http://localhost") or file_path.startswith("http://127.0.0.1"):
                async with aiohttp.ClientSession() as session:
                    async with session.get(file_path) as response:
                        if response.status == 200:
                            file_data = await response.read()
                            filename = file_path.split("/")[-1] or "file"
                            content_type = response.headers.get("Content-Type", "image/png")
                        else:
                            return None
            
            elif file_path.startswith("/files/"):
                file_id = file_path.split("/")[-1]
                storage_path = Path("data/files")
                
                for subdir in ["generated", "images", "uploads"]:
                    for file in (storage_path / subdir).glob("*"):
                        if file_id in str(file) or file.stem == file_id:
                            with open(file, "rb") as f:
                                file_data = f.read()
                            filename = file.name
                            break
                    if file_data:
                        break
            
            elif Path(file_path).exists():
                with open(file_path, "rb") as f:
                    file_data = f.read()
                filename = Path(file_path).name
            
            if not file_data:
                return None
            
            # Upload to catbox.moe
            async with aiohttp.ClientSession() as session:
                data = FormData()
                data.add_field('reqtype', 'fileupload')
                data.add_field('fileToUpload', file_data, filename=filename, content_type=content_type)
                
                async with session.post('https://catbox.moe/user/api.php', data=data) as response:
                    if response.status == 200:
                        result = await response.text()
                        if result.startswith('https://'):
                            public_url = result.strip()
                            logger.info(f"✅ Uploaded to public URL: {public_url}")
                            return public_url
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to create public URL: {e}")
            return None
    
    async def get_printify_mockups(
        self,
        product_id: str
    ) -> List[Dict[str, str]]:
        """
        Fetch mockup image URLs from a Printify product.
        
        Returns list of mockup info:
        [{"url": "https://...", "position": "front", "variant": "black"}]
        """
        if not self.printify:
            logger.warning("Printify tools not configured")
            return []
        
        try:
            # Get product details
            product = await self.printify.get_product(product_id)
            
            if not product:
                return []
            
            mockups = []
            
            # Extract mockup URLs from images array
            images = product.get("images", [])
            for img in images:
                src = img.get("src")
                if src:
                    mockup_info = {
                        "url": src,
                        "position": img.get("position", "front"),
                        "variant_ids": img.get("variant_ids", []),
                        "is_default": img.get("is_default", False)
                    }
                    mockups.append(mockup_info)
            
            logger.info(f"Found {len(mockups)} mockup images for product {product_id}")
            return mockups
            
        except Exception as e:
            logger.error(f"Failed to fetch Printify mockups: {e}")
            return []
    
    async def generate_video_script(
        self,
        product_name: str,
        product_description: str,
        duration: int = 10,
        tone: str = "premium",
        target_audience: str = "aspirational buyers",
        commercial_style: str = "cinematic"
    ) -> Dict[str, Any]:
        """
        Generate a PREMIUM VIDEO SCRIPT using Claude.
        
        Commercial styles:
        - cinematic: Apple/Tesla style, emotional, minimal words, maximum impact
        - energetic: Nike/Red Bull style, action-packed, motivational
        - luxury: Rolex/Chanel style, elegant, sophisticated, exclusive
        - playful: Duolingo/Mailchimp style, fun, quirky, memorable
        - authentic: Patagonia/Dove style, genuine, story-driven, values-focused
        
        Returns:
            {
                "hook": "Opening attention grabber",
                "segments": [
                    {"duration": 3, "text": "...", "visual": "...", "camera": "...", "transition": "..."},
                    ...
                ],
                "cta": "Call to action",
                "full_voiceover": "Complete script for TTS",
                "music_style": "Recommended music style",
                "mood_arc": "Emotional journey description"
            }
        """
        if not self.anthropic:
            return self._generate_default_script(product_name, duration)
        
        segment_count = max(3, duration // 4)
        segment_duration = duration // segment_count
        
        # Use enhanced prompt template
        prompt = SCRIPT_PROMPT_TEMPLATE.format(
            duration=duration,
            product_name=product_name,
            product_description=product_description or f"A premium {product_name} for discerning customers",
            segment_count=segment_count,
            segment_duration=segment_duration,
            tone=f"{commercial_style} and {tone}"
        )
        
        prompt += f"""

ADDITIONAL CONTEXT:
- Target Audience: {target_audience}
- Commercial Style: {commercial_style.upper()}
- Desired Emotion: Make viewers FEEL something, not just understand

Return a JSON object:
{{
    "hook": "Opening line (max 8 words)",
    "segments": [
        {{
            "duration": 3,
            "text": "voiceover text (max 12 words)",
            "visual": "detailed visual direction",
            "camera": "specific camera movement",
            "transition": "transition to next segment"
        }}
    ],
    "cta": "Powerful 3-5 word call to action",
    "full_voiceover": "Complete script for TTS",
    "music_style": "Recommended from: Cinematic, Epic, Luxury, Electronic, Emotional",
    "mood_arc": "Description of emotional journey (e.g., curiosity → desire → excitement → action)"
}}"""

        try:
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse JSON from response
            import json
            text = response.content[0].text
            
            # Extract JSON from potential markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            script = json.loads(text.strip())
            
            # Enhance segments with camera directions if missing
            for i, segment in enumerate(script.get("segments", [])):
                if "camera" not in segment:
                    segment_type = "hook" if i == 0 else ("closing" if i == len(script["segments"]) - 1 else "feature")
                    segment["camera"] = ENHANCED_CAMERA_DIRECTIONS[segment_type][i % len(ENHANCED_CAMERA_DIRECTIONS[segment_type])]
                if "transition" not in segment:
                    segment["transition"] = TRANSITION_STYLES[i % len(TRANSITION_STYLES)]
            
            logger.info(f"Generated PREMIUM script with {len(script.get('segments', []))} segments, mood: {script.get('mood_arc', 'N/A')}")
            return script
            
        except Exception as e:
            logger.error(f"Script generation failed: {e}")
            return self._generate_default_script(product_name, duration)
    
    def _generate_default_script(
        self,
        product_name: str,
        duration: int
    ) -> Dict[str, Any]:
        """Generate a PREMIUM default script when Claude is unavailable."""
        segment_count = max(3, duration // 4)
        segment_duration = duration // segment_count
        
        return {
            "hook": f"What if {product_name.lower()} could change everything?",
            "segments": [
                {
                    "duration": segment_duration,
                    "text": f"Discover the {product_name} that redefines expectations.",
                    "visual": "Dramatic reveal with rim lighting, slow-motion product rotation",
                    "camera": ENHANCED_CAMERA_DIRECTIONS["hook"][0],
                    "transition": "light flash transition",
                    "emotion": "curiosity"
                },
                {
                    "duration": segment_duration,
                    "text": "Crafted for those who demand excellence.",
                    "visual": "Close-up details, texture focus, premium materials highlighted",
                    "camera": ENHANCED_CAMERA_DIRECTIONS["feature"][0],
                    "transition": "smooth crossfade",
                    "emotion": "desire"
                },
                {
                    "duration": segment_duration,
                    "text": "Experience the difference. Order yours today.",
                    "visual": "Product in aspirational lifestyle setting, warm lighting",
                    "camera": ENHANCED_CAMERA_DIRECTIONS["closing"][0],
                    "transition": "fade to black",
                    "emotion": "excitement"
                }
            ],
            "cta": "Get yours now.",
            "full_voiceover": f"What if {product_name.lower()} could change everything? Discover the {product_name} that redefines expectations. Crafted for those who demand excellence. Experience the difference. Order yours today.",
            "music_style": "Cinematic",
            "mood_arc": "curiosity → admiration → desire → action"
        }
    
    async def generate_voiceover(
        self,
        script_text: str,
        voice: str = "en_speaker_6",
        emotion: str = "excited"
    ) -> Dict[str, Any]:
        """
        Generate voiceover audio using TTS.
        
        Args:
            script_text: Text to convert to speech
            voice: Voice ID or style
            emotion: Emotion for the voice (excited, calm, serious, etc.)
            
        Returns:
            {"success": bool, "audio_url": str, "duration": float}
        """
        if not self.replicate:
            return {"success": False, "error": "Replicate API not configured"}
        
        try:
            # Use Bark for emotional TTS or standard TTS
            result = await self.replicate.run_model(
                model="cjwbw/bark",
                inputs={
                    "prompt": script_text,
                    "text_temp": 0.7 if emotion == "excited" else 0.5,
                    "waveform_temp": 0.7
                }
            )
            
            if result.get("success"):
                audio_url = result.get("output")
                if isinstance(audio_url, list):
                    audio_url = audio_url[0]
                
                # Download and save locally
                local_path = await self._download_audio(audio_url, "voiceover")
                
                return {
                    "success": True,
                    "audio_url": audio_url,
                    "local_path": str(local_path),
                    "duration_estimate": len(script_text.split()) / 2.5  # ~2.5 words/sec
                }
            
            return {"success": False, "error": result.get("error", "TTS failed")}
            
        except Exception as e:
            logger.error(f"Voiceover generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_background_music(
        self,
        duration: int = 10,
        style: str = "upbeat electronic",
        energy: str = "high"
    ) -> Dict[str, Any]:
        """
        Generate background music using MusicGen.
        
        Args:
            duration: Music duration in seconds
            style: Music style description
            energy: Energy level (low, medium, high)
            
        Returns:
            {"success": bool, "audio_url": str, "local_path": str}
        """
        if not self.replicate:
            return {"success": False, "error": "Replicate API not configured"}
        
        # Build music prompt
        energy_terms = {
            "low": "calm, ambient",
            "medium": "moderate tempo, engaging",
            "high": "energetic, driving beat"
        }
        
        prompt = f"{style}, {energy_terms.get(energy, 'medium tempo')}, commercial advertisement music, {duration} seconds"
        
        try:
            result = await self.replicate.run_model(
                model="meta/musicgen",
                inputs={
                    "prompt": prompt,
                    "duration": min(duration + 2, 30),  # Add 2s buffer, max 30s
                    "model_version": "stereo-large"
                }
            )
            
            if result.get("success"):
                audio_url = result.get("output")
                if isinstance(audio_url, list):
                    audio_url = audio_url[0]
                
                # Download and save locally
                local_path = await self._download_audio(audio_url, "music")
                
                return {
                    "success": True,
                    "audio_url": audio_url,
                    "local_path": str(local_path),
                    "duration": duration
                }
            
            return {"success": False, "error": result.get("error", "Music generation failed")}
            
        except Exception as e:
            logger.error(f"Music generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    @tool(
        name="generate_video_from_mockup",
        description="Generate a video from a product mockup image using AI. Animates the image with subtle motion for ads and marketing.",
        category="video"
    )
    async def generate_video_from_image(
        self,
        image_url: str,
        prompt: str,
        duration: int = 5,
        model: str = "kling"
    ) -> Dict[str, Any]:
        """
        Generate video from a static image using AI.
        
        Args:
            image_url: URL of the source image (mockup)
            prompt: Motion/action description
            duration: Video duration (5 or 10 seconds)
            model: Video model to use (kling, minimax, svd)
            
        Returns:
            {"success": bool, "video_url": str, "local_path": str}
        """
        if not self.replicate:
            return {"success": False, "error": "Replicate API not configured"}
        
        # Map model names to Replicate models
        model_map = {
            "kling": "kwaivgi/kling-v1.6-pro",
            "minimax": "minimax/video-01",
            "svd": "stability-ai/stable-video-diffusion"
        }
        
        replicate_model = model_map.get(model, model_map["kling"])
        
        try:
            # First ensure we have a public URL (handle local files)
            normalized_url = await self._ensure_public_url(image_url)
            if not normalized_url:
                return {"success": False, "error": f"Could not access image: {image_url}"}
            
            # Then normalize for strict video models (Kling, Minimax) that need proper extensions
            if hasattr(self.replicate, '_validate_and_normalize_image_url'):
                url_result = await self.replicate._validate_and_normalize_image_url(normalized_url, replicate_model)
                if url_result.get("success"):
                    normalized_url = url_result.get("url", normalized_url)
                    if url_result.get("normalized"):
                        logger.info(f"🔄 Normalized URL for video model: {normalized_url[:60]}...")
                elif url_result.get("error"):
                    logger.warning(f"URL normalization issue: {url_result.get('error')} - proceeding anyway")
            
            # Build inputs based on model
            if model == "svd":
                inputs = {
                    "input_image": normalized_url,
                    "motion_bucket_id": 127,  # Higher = more motion
                    "fps": 7
                }
            else:
                # Kling/Minimax style - use "image" key as expected by replicate_universal
                inputs = {
                    "prompt": prompt,
                    "image": normalized_url,
                    "duration": duration
                }
            
            result = await self.replicate.run_model(
                model=replicate_model,
                inputs=inputs
            )
            
            if result.get("success"):
                video_url = result.get("output")
                if isinstance(video_url, list):
                    video_url = video_url[0]
                
                # Download and save locally
                local_path = await self._download_video(video_url)
                
                return {
                    "success": True,
                    "video_url": video_url,
                    "local_path": str(local_path),
                    "duration": duration,
                    "model_used": replicate_model
                }
            
            return {"success": False, "error": result.get("error", "Video generation failed")}
            
        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    @tool(
        name="create_product_promo_video",
        description="Create a complete product promotional video with AI. Uses mockup images, generates video, voiceover, and background music. Perfect for product ads.",
        category="video"
    )
    async def create_product_promo_video(
        self,
        product_name: str,
        product_description: str = "",
        image_url: str = None,
        printify_product_id: str = None,
        duration: int = 10,
        include_voiceover: bool = True,
        include_music: bool = True,
        tone: str = "energetic",
        music_style: str = "upbeat electronic"
    ) -> Dict[str, Any]:
        """
        Create a complete product promotional video.
        
        This is the main entry point that orchestrates the full pipeline:
        1. Get mockup image (from Printify or provided URL)
        2. Generate video script
        3. Create video from mockup
        4. Generate voiceover (optional)
        5. Generate background music (optional)
        6. Compose final video with all elements
        
        Args:
            product_name: Name of the product
            product_description: Product description for script generation
            image_url: Direct image URL (used if no Printify product)
            printify_product_id: Printify product ID to fetch mockup from
            duration: Total video duration in seconds
            include_voiceover: Whether to add voiceover
            include_music: Whether to add background music
            tone: Script tone (energetic, calm, professional, fun)
            music_style: Background music style
            
        Returns:
            Complete video result with all generated assets
        """
        result = {
            "success": False,
            "product_name": product_name,
            "assets": {},
            "timeline": []
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Step 1: Get mockup image
            result["timeline"].append({"step": "get_mockup", "status": "started"})
            
            mockup_url = image_url
            
            if printify_product_id and not mockup_url:
                # Fetch mockup from Printify
                mockups = await self.get_printify_mockups(printify_product_id)
                if mockups:
                    # Use the default or first mockup
                    default_mockup = next((m for m in mockups if m.get("is_default")), mockups[0])
                    mockup_url = default_mockup.get("url")
                    result["assets"]["printify_mockups"] = mockups
                    logger.info(f"Using Printify mockup: {mockup_url}")
            
            if not mockup_url:
                return {
                    **result,
                    "error": "No image URL provided and couldn't fetch from Printify"
                }
            
            result["assets"]["mockup_url"] = mockup_url
            result["timeline"][-1]["status"] = "completed"
            
            # Step 2: Generate video script
            result["timeline"].append({"step": "generate_script", "status": "started"})
            
            script = await self.generate_video_script(
                product_name=product_name,
                product_description=product_description or f"Amazing {product_name} for your lifestyle",
                duration=duration,
                tone=tone
            )
            result["assets"]["script"] = script
            result["timeline"][-1]["status"] = "completed"
            
            # Step 3: Generate video from mockup (run in parallel with audio)
            result["timeline"].append({"step": "generate_video", "status": "started"})
            
            # Create motion prompt from script
            visual_prompts = [seg.get("visual", "") for seg in script.get("segments", [])]
            motion_prompt = f"Product showcase, {', '.join(visual_prompts)}, professional commercial style"
            
            video_task = self.generate_video_from_image(
                image_url=mockup_url,
                prompt=motion_prompt,
                duration=duration,
                model=self.default_video_model
            )
            
            # Step 4 & 5: Generate audio in parallel with video
            audio_tasks = []
            
            if include_voiceover:
                result["timeline"].append({"step": "generate_voiceover", "status": "started"})
                voiceover_task = self.generate_voiceover(
                    script_text=script.get("full_voiceover", script.get("hook", product_name)),
                    emotion="excited" if tone == "energetic" else "calm"
                )
                audio_tasks.append(("voiceover", voiceover_task))
            
            if include_music:
                result["timeline"].append({"step": "generate_music", "status": "started"})
                energy = "high" if tone == "energetic" else "medium"
                music_task = self.generate_background_music(
                    duration=duration,
                    style=music_style,
                    energy=energy
                )
                audio_tasks.append(("music", music_task))
            
            # Wait for video generation
            video_result = await video_task
            
            if video_result.get("success"):
                result["assets"]["video"] = video_result
                result["timeline"][2]["status"] = "completed"
            else:
                result["timeline"][2]["status"] = "failed"
                result["timeline"][2]["error"] = video_result.get("error")
            
            # Wait for audio tasks
            for i, (audio_type, task) in enumerate(audio_tasks):
                audio_result = await task
                
                timeline_idx = 3 + i
                if audio_result.get("success"):
                    result["assets"][audio_type] = audio_result
                    result["timeline"][timeline_idx]["status"] = "completed"
                else:
                    result["timeline"][timeline_idx]["status"] = "failed"
                    result["timeline"][timeline_idx]["error"] = audio_result.get("error")
            
            # Step 6: Compose final video (if we have all components)
            if video_result.get("success"):
                result["timeline"].append({"step": "compose_final", "status": "started"})
                
                # Try to compose with audio if available
                final_video = await self._compose_final_video(
                    video_path=video_result.get("local_path") or video_result.get("video_url"),
                    voiceover_path=result["assets"].get("voiceover", {}).get("local_path"),
                    music_path=result["assets"].get("music", {}).get("local_path"),
                    output_name=f"promo_{product_name.replace(' ', '_')}_{timestamp}"
                )
                
                if final_video.get("success"):
                    result["assets"]["final_video"] = final_video
                    result["timeline"][-1]["status"] = "completed"
                    result["success"] = True
                    result["output"] = final_video.get("local_path") or final_video.get("video_url")
                else:
                    # Still success if we have the base video
                    result["success"] = True
                    result["output"] = video_result.get("local_path") or video_result.get("video_url")
                    result["timeline"][-1]["status"] = "skipped"
                    result["timeline"][-1]["note"] = "Using base video without audio composition"
            else:
                result["error"] = "Video generation failed"
            
            return result
            
        except Exception as e:
            logger.error(f"Promo video creation failed: {e}")
            result["error"] = str(e)
            return result
    
    async def _compose_final_video(
        self,
        video_path: str,
        voiceover_path: str = None,
        music_path: str = None,
        output_name: str = "promo_video"
    ) -> Dict[str, Any]:
        """
        Compose final video with audio tracks using MoviePy.
        
        Args:
            video_path: Path to the base video
            voiceover_path: Path to voiceover audio (optional)
            music_path: Path to background music (optional)
            output_name: Name for the output file
            
        Returns:
            {"success": bool, "local_path": str}
        """
        try:
            from moviepy.editor import (
                VideoFileClip, AudioFileClip, 
                CompositeAudioClip, concatenate_videoclips
            )
        except ImportError:
            logger.warning("MoviePy not available, skipping audio composition")
            return {"success": False, "error": "MoviePy not installed"}
        
        try:
            # Load video
            if video_path.startswith("http"):
                # Download video first
                video_path = await self._download_video(video_path, output_name)
            
            video = VideoFileClip(str(video_path))
            audio_clips = []
            
            # Add voiceover
            if voiceover_path and Path(voiceover_path).exists():
                voiceover = AudioFileClip(str(voiceover_path))
                # Trim or loop to match video duration
                if voiceover.duration > video.duration:
                    voiceover = voiceover.subclip(0, video.duration)
                audio_clips.append(voiceover)
            
            # Add background music (lower volume)
            if music_path and Path(music_path).exists():
                music = AudioFileClip(str(music_path))
                # Trim or loop to match video duration
                if music.duration > video.duration:
                    music = music.subclip(0, video.duration)
                elif music.duration < video.duration:
                    # Loop the music
                    loops_needed = int(video.duration / music.duration) + 1
                    from moviepy.editor import concatenate_audioclips
                    music = concatenate_audioclips([music] * loops_needed)
                    music = music.subclip(0, video.duration)
                
                # Lower music volume when voiceover exists
                volume = 0.3 if voiceover_path else 0.6
                music = music.volumex(volume)
                audio_clips.append(music)
            
            # Combine audio tracks
            if audio_clips:
                final_audio = CompositeAudioClip(audio_clips)
                video = video.set_audio(final_audio)
            
            # Export
            output_path = self.output_dir / f"{output_name}.mp4"
            video.write_videofile(
                str(output_path),
                codec='libx264',
                audio_codec='aac',
                fps=24,
                logger=None  # Suppress moviepy logs
            )
            
            # Cleanup
            video.close()
            for clip in audio_clips:
                clip.close()
            
            logger.info(f"Composed final video: {output_path}")
            
            return {
                "success": True,
                "local_path": str(output_path),
                "duration": video.duration
            }
            
        except Exception as e:
            logger.error(f"Video composition failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _download_audio(self, url: str, prefix: str = "audio") -> Path:
        """Download audio file from URL."""
        import aiohttp
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.mp3"
        filepath = self.audio_dir / filename
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    filepath.write_bytes(content)
                    logger.info(f"Downloaded audio: {filepath}")
                    return filepath
        
        raise Exception(f"Failed to download audio from {url}")
    
    async def _download_video(self, url: str, name: str = "video") -> Path:
        """Download video file from URL."""
        import aiohttp
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.mp4"
        filepath = self.output_dir / filename
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    filepath.write_bytes(content)
                    logger.info(f"Downloaded video: {filepath}")
                    return filepath
        
        raise Exception(f"Failed to download video from {url}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ADVANCED MULTI-SEGMENT COMMERCIAL PRODUCTION
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _select_voice_for_product(self, product_name: str) -> Tuple[str, str]:
        """Select appropriate voice based on product type."""
        lowered = product_name.lower()
        
        if any(kw in lowered for kw in ["luxury", "elegant", "premium", "sophisticated"]):
            return "Luxury", "auto"
        elif any(kw in lowered for kw in ["kids", "children", "toy", "fun", "playful"]):
            return "Energetic", "happy"
        elif any(kw in lowered for kw in ["tech", "modern", "innovation", "smart"]):
            return "Professional", "auto"
        elif any(kw in lowered for kw in ["wellness", "health", "yoga", "meditation"]):
            return "Warm", "calm"
        elif any(kw in lowered for kw in ["adventure", "outdoor", "sport", "active"]):
            return "Casual", "excited"
        else:
            return "Friendly", "auto"
    
    def _get_camera_direction(self, segment_index: int) -> str:
        """Get camera direction prompt for segment."""
        directions = CAMERA_DIRECTIONS if CAMERA_DIRECTIONS else [
            "hero product shot with dynamic lighting",
            "lifestyle close-up showing usage",
            "bold closing shot with logo emphasis"
        ]
        return directions[segment_index] if segment_index < len(directions) else "smooth cinematic shot"
    
    def _extract_script_segments(self, script_text: str, expected_count: int) -> List[str]:
        """Parse numbered segments from generated script."""
        segments = []
        
        # Try different parsing patterns
        for line in script_text.split("\n"):
            # Pattern: "Segment X:" or "X:" or "X)"
            if any(marker in line for marker in ["Segment", "1:", "2:", "3:", "4:", "5:", "1)", "2)", "3)"]):
                if ":" in line:
                    text = line.split(":", 1)[1].strip()
                    if text:
                        segments.append(text)
                elif ")" in line:
                    text = line.split(")", 1)[1].strip()
                    if text:
                        segments.append(text)
        
        # Fallback: split by double newlines
        if len(segments) < expected_count:
            cleaned = [part.strip() for part in re.split(r"\n\s*\n+", script_text) if part.strip()]
            segments = cleaned[:expected_count]
        
        # Pad if needed
        while len(segments) < expected_count:
            segments.append(f"Amazing quality you'll love.")
        
        return segments[:expected_count]
    
    @tool(
        name="create_multi_segment_commercial",
        description="Create a professional multi-segment product commercial with script, voiceover, music, and video segments using AI. Full printify_clean-level production.",
        category="video"
    )
    async def create_multi_segment_commercial(
        self,
        product_name: str,
        product_description: str = "",
        image_url: str = None,
        total_duration: int = 15,
        segment_count: int = 3,
        video_model: str = "kling",
        voice_style: str = None,
        music_style: str = "Corporate",
        include_voiceover: bool = True,
        include_music: bool = True,
        add_cta: bool = True,
        cta_text: str = "Shop Now!",
        brand_color: str = None
    ) -> Dict[str, Any]:
        """
        Create a professional multi-segment product commercial.
        
        This is the FULL production pipeline matching printify_clean quality:
        1. Generate script with segment breakdowns
        2. Generate video for each segment
        3. Generate voiceover narration
        4. Generate background music
        5. Mix audio (voiceover + music with proper volumes)
        6. Concatenate video segments
        7. Add CTA card
        8. Add brand overlay (if brand_color provided)
        9. Compose final video with all audio
        
        Args:
            product_name: Name of the product
            product_description: Product description for script generation
            image_url: Product image URL for image-to-video models
            total_duration: Total commercial duration (10-30 seconds recommended)
            segment_count: Number of video segments (2-6)
            video_model: Model to use (ken_burns, kling, luma_flash, sora, veo3, etc.)
            voice_style: Voice style (Professional, Energetic, Luxury, Friendly)
            music_style: Music style (Cinematic, Corporate, Upbeat, Electronic)
            include_voiceover: Whether to include voiceover
            include_music: Whether to include background music
            add_cta: Whether to add CTA end card
            cta_text: Call-to-action text
            brand_color: Hex color for brand overlay (e.g., "#FF5733")
            
        Returns:
            Complete commercial result with all assets and final video path
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_slug = re.sub(r"[^A-Za-z0-9_-]+", "_", product_name.strip().replace(" ", "_")).lower() or "product"
        
        result = {
            "success": False,
            "product_name": product_name,
            "assets": {},
            "segments": [],
            "timeline": [],
            "errors": []
        }
        
        # Validate inputs
        segment_count = max(2, min(6, segment_count))
        total_duration = max(10, min(60, total_duration))
        segment_duration = max(3, int(total_duration / segment_count))
        total_duration = segment_duration * segment_count  # Recalculate for even segments
        
        # Auto-select voice if not provided
        if not voice_style:
            voice_style, voice_emotion = self._select_voice_for_product(product_name)
        else:
            voice_emotion = "auto"
        
        try:
            # ═══════════════════════════════════════════════════════════════
            # STEP 1: Generate Script with Segments
            # ═══════════════════════════════════════════════════════════════
            result["timeline"].append({"step": "generate_script", "status": "started"})
            logger.info(f"📝 Generating {segment_count}-segment script for {product_name}...")
            
            script_prompt = SCRIPT_PROMPT_TEMPLATE.format(
                duration=total_duration,
                product_name=product_name,
                product_description=product_description or product_name,
                segment_count=segment_count,
                segment_duration=segment_duration,
                tone="professional and compelling"
            )
            
            script_text = ""
            if self.anthropic:
                try:
                    response = self.anthropic.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=700,
                        messages=[{"role": "user", "content": script_prompt}]
                    )
                    script_text = response.content[0].text
                except Exception as e:
                    logger.warning(f"Claude script generation failed: {e}")
            
            if not script_text and self.replicate:
                try:
                    llama_result = await self.replicate.run_model(
                        model="meta/meta-llama-3-70b-instruct",
                        inputs={"prompt": script_prompt, "max_tokens": 700, "temperature": 0.7}
                    )
                    if llama_result.get("success"):
                        script_text = "".join(llama_result.get("output", []))
                except:
                    pass
            
            segments = self._extract_script_segments(script_text, segment_count)
            full_voiceover_text = " ".join(segments)
            
            result["assets"]["script"] = {
                "segments": segments,
                "full_text": full_voiceover_text
            }
            result["timeline"][-1]["status"] = "completed"
            
            # Save script to file
            script_file = self.temp_dir / f"{safe_slug}_script_{timestamp}.txt"
            script_file.write_text("\n\n".join(segments), encoding="utf-8")
            result["assets"]["script_file"] = str(script_file)
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 2: Generate Voiceover
            # ═══════════════════════════════════════════════════════════════
            voiceover_path = None
            if include_voiceover:
                result["timeline"].append({"step": "generate_voiceover", "status": "started"})
                logger.info(f"🎙️ Generating voiceover with {voice_style} voice...")
                
                if self.video_generator:
                    voice_result = await self.video_generator.generate_voiceover(
                        text=full_voiceover_text,
                        voice_style=voice_style,
                        emotion=voice_emotion
                    )
                else:
                    # Fallback to basic voiceover
                    voice_result = await self.generate_voiceover(
                        script_text=full_voiceover_text,
                        emotion="excited" if voice_style == "Energetic" else "calm"
                    )
                
                if voice_result.get("success"):
                    voiceover_path = voice_result.get("audio_path") or voice_result.get("local_path")
                    result["assets"]["voiceover"] = voice_result
                    result["timeline"][-1]["status"] = "completed"
                else:
                    result["timeline"][-1]["status"] = "failed"
                    result["errors"].append(f"Voiceover: {voice_result.get('error')}")
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 3: Generate Background Music
            # ═══════════════════════════════════════════════════════════════
            music_path = None
            if include_music:
                result["timeline"].append({"step": "generate_music", "status": "started"})
                logger.info(f"🎵 Generating {music_style} background music...")
                
                if self.video_generator:
                    music_result = await self.video_generator.generate_background_music(
                        duration=total_duration + 5,  # Extra for padding
                        style=music_style
                    )
                else:
                    music_result = await self.generate_background_music(
                        duration=total_duration + 5,
                        style=music_style
                    )
                
                if music_result.get("success"):
                    music_path = music_result.get("audio_path") or music_result.get("local_path")
                    result["assets"]["music"] = music_result
                    result["timeline"][-1]["status"] = "completed"
                else:
                    result["timeline"][-1]["status"] = "failed"
                    result["errors"].append(f"Music: {music_result.get('error')}")
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 4: Generate Video Segments
            # ═══════════════════════════════════════════════════════════════
            result["timeline"].append({"step": "generate_video_segments", "status": "started"})
            logger.info(f"🎬 Generating {segment_count} video segments with {video_model}...")
            
            segment_paths = []
            for idx, segment_text in enumerate(segments):
                logger.info(f"  Segment {idx + 1}/{segment_count}...")
                
                # Build visual prompt
                camera_dir = self._get_camera_direction(idx)
                visual_prompt = (
                    f"Product commercial for '{product_name}'. "
                    f"{camera_dir}. "
                    f"Style: modern, vibrant, clean, commercial-ready. "
                    f"Segment focus: {segment_text}. "
                    f"Professional quality, well-lit, high production value."
                )
                
                # Use image for first segment, or all if ken_burns
                use_image = image_url if (idx == 0 or video_model == "ken_burns") else None
                
                if self.video_generator:
                    video_result = await self.video_generator.generate_ai_video(
                        prompt=visual_prompt,
                        model=video_model,
                        image_url=use_image,
                        duration=segment_duration
                    )
                else:
                    video_result = await self.generate_video_from_image(
                        image_url=use_image or "",
                        prompt=visual_prompt,
                        duration=segment_duration,
                        model=video_model
                    )
                
                if video_result.get("success"):
                    segment_path = video_result.get("video_path") or video_result.get("local_path")
                    segment_paths.append(segment_path)
                    result["segments"].append({
                        "index": idx,
                        "text": segment_text,
                        "video_path": segment_path,
                        "duration": segment_duration
                    })
                else:
                    result["errors"].append(f"Segment {idx + 1}: {video_result.get('error')}")
            
            if not segment_paths:
                return {
                    **result,
                    "error": "No video segments generated"
                }
            
            result["timeline"][-1]["status"] = "completed"
            result["assets"]["segment_paths"] = segment_paths
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 5: Concatenate Video Segments
            # ═══════════════════════════════════════════════════════════════
            result["timeline"].append({"step": "concatenate_segments", "status": "started"})
            logger.info(f"🔗 Concatenating {len(segment_paths)} video segments...")
            
            concat_output = str(self.temp_dir / f"{safe_slug}_concat_{timestamp}.mp4")
            
            try:
                concat_result = concatenate_video_segments(segment_paths, concat_output)
                if concat_result.get("success"):
                    result["assets"]["concatenated_video"] = concat_result.get("video_path")
                    result["timeline"][-1]["status"] = "completed"
                else:
                    # Fallback: use first segment
                    result["assets"]["concatenated_video"] = segment_paths[0]
                    result["timeline"][-1]["status"] = "partial"
            except Exception as e:
                result["assets"]["concatenated_video"] = segment_paths[0]
                result["timeline"][-1]["status"] = "failed"
                result["errors"].append(f"Concat: {e}")
            
            base_video = result["assets"]["concatenated_video"]
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 6: Add CTA Card (if requested)
            # ═══════════════════════════════════════════════════════════════
            if add_cta and self.video_generator:
                result["timeline"].append({"step": "add_cta", "status": "started"})
                logger.info(f"📢 Adding CTA card: {cta_text}")
                
                cta_output = str(self.temp_dir / f"{safe_slug}_cta_{timestamp}.mp4")
                cta_result = self.video_generator.add_cta_card(
                    video_path=base_video,
                    output_path=cta_output,
                    cta_text=cta_text
                )
                
                if cta_result.get("success"):
                    base_video = cta_result.get("video_path")
                    result["assets"]["cta_video"] = base_video
                    result["timeline"][-1]["status"] = "completed"
                else:
                    result["timeline"][-1]["status"] = "skipped"
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 7: Add Brand Overlay (if color provided)
            # ═══════════════════════════════════════════════════════════════
            if brand_color and self.video_generator:
                result["timeline"].append({"step": "add_brand_overlay", "status": "started"})
                logger.info(f"🎨 Adding brand overlay with color: {brand_color}")
                
                brand_output = str(self.temp_dir / f"{safe_slug}_branded_{timestamp}.mp4")
                brand_result = self.video_generator.add_brand_overlay(
                    video_path=base_video,
                    output_path=brand_output,
                    primary_color=brand_color
                )
                
                if brand_result.get("success"):
                    base_video = brand_result.get("video_path")
                    result["assets"]["branded_video"] = base_video
                    result["timeline"][-1]["status"] = "completed"
                else:
                    result["timeline"][-1]["status"] = "skipped"
            
            # ═══════════════════════════════════════════════════════════════
            # STEP 8: Compose Final Video with Audio
            # ═══════════════════════════════════════════════════════════════
            result["timeline"].append({"step": "compose_final", "status": "started"})
            logger.info(f"🎬 Composing final video with audio...")
            
            final_output = str(self.output_dir / f"{safe_slug}_commercial_{timestamp}.mp4")
            
            if voiceover_path or music_path:
                try:
                    final_result = compose_video_with_audio(
                        video_path=base_video,
                        voiceover_path=voiceover_path,
                        music_path=music_path,
                        output_path=final_output,
                        voiceover_volume=1.0,
                        music_volume=0.35 if voiceover_path else 0.6
                    )
                    
                    if final_result.get("success"):
                        result["assets"]["final_video"] = final_result.get("video_path")
                        result["output"] = final_result.get("video_path")
                        result["timeline"][-1]["status"] = "completed"
                    else:
                        result["assets"]["final_video"] = base_video
                        result["output"] = base_video
                        result["timeline"][-1]["status"] = "partial"
                except Exception as e:
                    logger.warning(f"Audio composition failed: {e}, using base video")
                    result["assets"]["final_video"] = base_video
                    result["output"] = base_video
                    result["timeline"][-1]["status"] = "partial"
            else:
                result["assets"]["final_video"] = base_video
                result["output"] = base_video
                result["timeline"][-1]["status"] = "completed"
            
            result["success"] = True
            result["duration"] = total_duration
            result["model_used"] = video_model
            
            logger.info(f"✅ Commercial complete: {result['output']}")
            return result
            
        except Exception as e:
            logger.error(f"Multi-segment commercial failed: {e}", exc_info=True)
            result["error"] = str(e)
            return result
    
    @tool(
        name="list_video_models",
        description="List all available video generation models with their capabilities.",
        category="video"
    )
    async def list_video_models(self) -> Dict[str, Any]:
        """List all available video models."""
        models = []
        
        if self.video_generator and hasattr(self.video_generator, 'VIDEO_MODELS'):
            for name, config in self.video_generator.VIDEO_MODELS.items():
                replicate_model, supports_i2v, max_duration, notes = config
                models.append({
                    "name": name,
                    "replicate_model": replicate_model,
                    "supports_image_to_video": supports_i2v,
                    "max_duration": max_duration,
                    "notes": notes
                })
        else:
            # Fallback list
            models = [
                {"name": "ken_burns", "supports_image_to_video": True, "max_duration": 60, "notes": "Local, free, instant"},
                {"name": "kling", "supports_image_to_video": True, "max_duration": 10, "notes": "Premium quality"},
                {"name": "luma_flash", "supports_image_to_video": True, "max_duration": 5, "notes": "Fast, 540p"},
                {"name": "minimax", "supports_image_to_video": True, "max_duration": 10, "notes": "General purpose"},
            ]
        
        return {
            "success": True,
            "models": models,
            "voice_styles": list(VOICE_MAP.keys()),
            "music_styles": list(MUSIC_PROMPTS.keys())
        }


# Singleton instance
_promo_video_service = None


def get_promo_video_service(
    replicate_api=None,
    anthropic_client=None,
    printify_tools=None
) -> PromoVideoService:
    """Get or create the promo video service singleton."""
    global _promo_video_service
    
    if _promo_video_service is None:
        _promo_video_service = PromoVideoService(
            replicate_api=replicate_api,
            anthropic_client=anthropic_client,
            printify_tools=printify_tools
        )
    elif replicate_api:
        _promo_video_service.replicate = replicate_api
    elif anthropic_client:
        _promo_video_service.anthropic = anthropic_client
    elif printify_tools:
        _promo_video_service.printify = printify_tools
    
    return _promo_video_service
