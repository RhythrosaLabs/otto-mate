"""
AI Image Generation Tools
=========================

Tools for generating images using various AI models.
"""

import logging
import aiohttp
import asyncio
from typing import Optional, Dict, Any, List
from .core import tool, ToolBase

logger = logging.getLogger(__name__)


class ImageGenerationTools(ToolBase):
    """AI image generation tools using Replicate."""
    
    # Fallback models in order of preference (updated Feb 2026)
    FALLBACK_MODELS = [
        "prunaai/flux-fast",
        "black-forest-labs/flux-schnell",
        "stability-ai/sdxl",
        "ideogram-ai/ideogram-v2",
        "stability-ai/sd3.5-large",
        "playgroundai/playground-v2.5-1024px-aesthetic"
    ]
    
    def __init__(self, replicate_token: str):
        self.token = replicate_token
        self.base_url = "https://api.replicate.com/v1"
        # Use identity/gzip encoding to avoid brotli issues
        self.headers = {
            "Authorization": f"Token {replicate_token}",
            "Content-Type": "application/json",
            "Accept-Encoding": "identity, gzip, deflate"
        }
        
        # Model catalog - Updated from printify_clean (Feb 2026)
        self.models = {
            # ── Flux Family (Top Tier) ──
            "flux_fast": "prunaai/flux-fast",  # Fastest - 4 steps, default for speed
            "flux_schnell": "black-forest-labs/flux-schnell",  # Fast - 4 steps
            "flux_dev": "black-forest-labs/flux-dev",  # Development (slower, high quality)
            "flux_pro": "black-forest-labs/flux-1.1-pro",  # Premium quality
            "flux_pro_ultra": "black-forest-labs/flux-1.1-pro-ultra",  # Highest quality
            "flux_kontext": "black-forest-labs/flux-kontext-pro",  # Face-aware generation
            "flux_fill": "black-forest-labs/flux-fill-pro",  # Inpainting
            "flux_canny": "black-forest-labs/flux-canny-pro",  # Edge control
            "flux_depth": "black-forest-labs/flux-depth-pro",  # Depth control
            "flux_redux": "black-forest-labs/flux-redux-dev",  # Style transfer
            
            # ── Google Imagen ──
            "imagen4": "google/imagen-4-ultra",  # Google's highest quality
            
            # ── Stable Diffusion Family ──
            "sdxl": "stability-ai/sdxl",
            "sdxl_turbo": "stability-ai/sdxl-turbo",
            "sd3": "stability-ai/sd3.5-large",
            "sd3_turbo": "stability-ai/sd3.5-large-turbo",
            "sd3_medium": "stability-ai/sd3.5-medium",
            
            # ── Specialized Models ──
            "ideogram": "ideogram-ai/ideogram-v2",
            "ideogram_v3": "ideogram-ai/ideogram-v3",
            "recraft": "recraft-ai/recraft-v3",
            "recraft_svg": "recraft-ai/recraft-v3-svg",
            "seedream": "bytedance/seedream-4",  # 4K resolution
            "bria": "bria/image-3.2",  # Commercial-safe
            
            # ── Artistic/Creative ──
            "playground": "playgroundai/playground-v2.5-1024px-aesthetic",
            "kandinsky": "ai-forever/kandinsky-3",
            "kolors": "kwai-kolors/kolors",
            
            # ── Photorealistic ──
            "juggernaut": "lucataco/juggernaut-xl-v9",
            "dreamshaper": "lucataco/dreamshaper-xl-v2-turbo",
            "photon": "luma/photon",
            
            # ── Image Editing ──
            "nano_banana": "google/nano-banana",  # Gemini image editing
            "flux_edit": "hardikdava/flux-image-editing",
            "edit_fast": "reve/edit-fast",  # $0.01 per edit
            "next_scene": "lucataco/next-scene",  # Cinematic sequences
            "inpaint": "cjwbw/stable-diffusion-v2-inpainting",
            
            # ── Marketing/Ads ──
            "ads_for_products": "pipeline-examples/ads-for-products",
            "flux_static_ads": "loolau/flux-static-ads",
            "logo_in_context": "subhash25rawat/logo-in-context",
            "ad_inpaint": "logerzhu/ad-inpaint",
            
            # ── Utility ──
            "upscale": "nightmareai/real-esrgan",
            "upscale_creative": "philz1337x/clarity-upscaler",
            "remove_bg": "cjwbw/rembg",
            "face_restore": "tencentarc/gfpgan",
        }
        
        # Default model for fast generation
        self.default_model = "flux_fast"
        
        # Style presets with enhanced prompts and optimal models (updated Feb 2026)
        self.style_presets = {
            "photorealistic": {
                "model": "flux_pro",
                "prompt_suffix": "photorealistic, highly detailed, professional photography, 8k, sharp focus",
                "negative": "cartoon, illustration, painting, drawing, anime, low quality, blurry"
            },
            "cinematic": {
                "model": "flux_pro",
                "prompt_suffix": "cinematic lighting, dramatic atmosphere, film grain, movie still, masterpiece",
                "negative": "amateur, flat lighting, overexposed"
            },
            "anime": {
                "model": "sdxl",
                "prompt_suffix": "anime style, manga, vibrant colors, clean lines, studio ghibli quality",
                "negative": "photorealistic, photograph, 3d render"
            },
            "digital_art": {
                "model": "ideogram_v3",
                "prompt_suffix": "digital art, illustration, concept art, detailed, vibrant",
                "negative": "photograph, 3d render, ugly, deformed"
            },
            "oil_painting": {
                "model": "sdxl",
                "prompt_suffix": "oil painting, classical art style, rich textures, masterpiece, museum quality",
                "negative": "digital, photograph, smooth"
            },
            "watercolor": {
                "model": "sdxl",
                "prompt_suffix": "watercolor painting, soft edges, flowing colors, artistic, delicate",
                "negative": "digital, sharp edges, photograph"
            },
            "sketch": {
                "model": "recraft",
                "prompt_suffix": "pencil sketch, hand drawn, detailed linework, artistic",
                "negative": "color, photograph, digital"
            },
            "vector": {
                "model": "recraft_svg",
                "prompt_suffix": "vector art, clean lines, flat colors, minimalist, graphic design",
                "negative": "photograph, 3d, gradient, texture"
            },
            "3d_render": {
                "model": "flux_pro",
                "prompt_suffix": "3D render, octane render, ray tracing, detailed textures, studio lighting",
                "negative": "2d, flat, drawing, painting"
            },
            "pixel_art": {
                "model": "sdxl",
                "prompt_suffix": "pixel art, retro game style, 16-bit, vibrant colors, nostalgic",
                "negative": "realistic, smooth, high resolution"
            },
            "minimalist": {
                "model": "recraft",
                "prompt_suffix": "minimalist design, simple, clean, elegant, white space",
                "negative": "busy, cluttered, detailed, complex"
            },
            "pop_art": {
                "model": "sdxl",
                "prompt_suffix": "pop art style, bold colors, comic book halftone, Andy Warhol inspired",
                "negative": "realistic, subdued colors, photograph"
            },
            "cyberpunk": {
                "model": "flux_pro",
                "prompt_suffix": "cyberpunk style, neon lights, futuristic, dystopian, high tech low life",
                "negative": "natural, pastoral, historical"
            },
            "fantasy": {
                "model": "flux_pro",
                "prompt_suffix": "fantasy art, magical, ethereal, detailed, epic composition",
                "negative": "modern, realistic, mundane"
            },
            "vintage": {
                "model": "sdxl",
                "prompt_suffix": "vintage style, retro, nostalgic, film grain, faded colors, 1970s aesthetic",
                "negative": "modern, digital, sharp, oversaturated"
            },
            "isometric": {
                "model": "ideogram_v3",
                "prompt_suffix": "isometric view, 3D game style, detailed miniature, clean design",
                "negative": "perspective, realistic, flat"
            },
            "logo": {
                "model": "recraft_svg",
                "prompt_suffix": "professional logo design, clean, scalable, modern branding",
                "negative": "complex, photograph, realistic"
            },
            "product": {
                "model": "flux_fast",
                "prompt_suffix": "professional product photography, studio lighting, clean white background, commercial",
                "negative": "amateur, dark, blurry, cluttered background"
            },
            "marketing": {
                "model": "flux_static_ads",
                "prompt_suffix": "marketing advertisement, eye-catching, professional, brand-safe",
                "negative": "amateur, low quality, inappropriate"
            }
        }
        
        # Valid aspect ratios for Flux models
        self.valid_aspect_ratios = [
            "1:1", "16:9", "21:9", "3:2", "2:3", "4:5", "5:4", "3:4", "4:3", "9:16", "9:21"
        ]
    
    def _get_aspect_ratio(self, width: int, height: int) -> str:
        """Convert width/height to closest valid Flux aspect ratio."""
        import math
        
        target_ratio = width / height
        
        best_ratio = "1:1"
        best_diff = float('inf')
        
        for ar in self.valid_aspect_ratios:
            w, h = map(int, ar.split(":"))
            ratio = w / h
            diff = abs(ratio - target_ratio)
            if diff < best_diff:
                best_diff = diff
                best_ratio = ar
        
        return best_ratio
    
    def _normalize_aspect_ratio(self, aspect_ratio: str) -> str:
        """
        Normalize natural language aspect ratio descriptions to valid Flux format.
        
        Supports:
        - Natural language: "portrait", "tall", "vertical", "wide", "landscape", "horizontal", "square", "cinematic"
        - Standard ratios: "16:9", "9:16", "1:1", "4:3", "3:4", "2:3", "3:2", etc.
        """
        if not aspect_ratio:
            return "1:1"
            
        aspect_lower = aspect_ratio.lower().strip()
        
        # Natural language mappings
        natural_language_map = {
            # Portrait/Tall (vertical)
            "portrait": "2:3",
            "tall": "2:3",
            "vertical": "2:3",
            "phone": "9:16",
            "story": "9:16",
            "stories": "9:16",
            "instagram story": "9:16",
            "tiktok": "9:16",
            "reels": "9:16",
            "pinterest": "2:3",
            
            # Landscape/Wide (horizontal)
            "landscape": "3:2",
            "wide": "16:9",
            "widescreen": "16:9",
            "horizontal": "3:2",
            "youtube": "16:9",
            "banner": "21:9",
            "ultrawide": "21:9",
            "cinematic": "21:9",
            "cinema": "21:9",
            "movie": "21:9",
            
            # Square
            "square": "1:1",
            "instagram": "1:1",
            "profile": "1:1",
            "avatar": "1:1",
            
            # Standard photo
            "photo": "4:3",
            "standard": "4:3",
            "4x3": "4:3",
            "3x4": "3:4",
            "5x4": "5:4",
            "4x5": "4:5",
        }
        
        # Check for natural language match
        if aspect_lower in natural_language_map:
            return natural_language_map[aspect_lower]
        
        # Check if already a valid ratio format
        if ":" in aspect_ratio:
            # Validate it's in the allowed list
            if aspect_ratio in self.valid_aspect_ratios:
                return aspect_ratio
            # Try to find closest match
            try:
                w, h = map(int, aspect_ratio.split(":"))
                return self._get_aspect_ratio(w, h)
            except:
                pass
        
        # Default to square
        return "1:1"
    
    def _detect_aspect_ratio_from_prompt(self, prompt: str) -> str:
        """
        Intelligently detect desired aspect ratio from the prompt text.
        Returns None if no specific aspect is detected.
        """
        prompt_lower = prompt.lower()
        
        # Portrait/Tall indicators
        portrait_keywords = [
            "portrait", "tall", "vertical", "portrait dimension", "tall dimension",
            "portrait format", "vertical format", "portrait oriented", "portrait orientation",
            "taller than wide", "tall image", "vertical image", "portrait mode",
            "phone wallpaper", "mobile wallpaper", "story format", "stories format",
            "pinterest", "tiktok", "reels", "instagram story"
        ]
        
        # Landscape/Wide indicators
        landscape_keywords = [
            "landscape", "wide", "horizontal", "landscape dimension", "wide dimension",
            "landscape format", "horizontal format", "landscape oriented", "landscape orientation",
            "wider than tall", "wide image", "horizontal image", "landscape mode",
            "desktop wallpaper", "banner", "youtube thumbnail", "widescreen",
            "cinematic", "movie", "film", "panoramic", "panorama", "ultrawide"
        ]
        
        # Square indicators
        square_keywords = [
            "square", "1:1", "equal width and height", "square format",
            "square dimension", "square image", "instagram post", "profile picture"
        ]
        
        # Check for keywords
        for kw in portrait_keywords:
            if kw in prompt_lower:
                logger.info(f"Detected portrait aspect ratio from keyword: '{kw}'")
                return "2:3"
        
        for kw in landscape_keywords:
            if kw in prompt_lower:
                logger.info(f"Detected landscape aspect ratio from keyword: '{kw}'")
                return "16:9" if "cinematic" in prompt_lower or "widescreen" in prompt_lower else "3:2"
        
        for kw in square_keywords:
            if kw in prompt_lower:
                logger.info(f"Detected square aspect ratio from keyword: '{kw}'")
                return "1:1"
        
        # No specific aspect detected
        return None
    
    def _detect_style_from_prompt(self, prompt: str) -> Optional[str]:
        """
        Intelligently detect desired style from the prompt text.
        Returns the style preset name or None if no specific style is detected.
        """
        prompt_lower = prompt.lower()
        
        # Style keyword mappings (keyword -> style_preset)
        style_keywords = {
            # Photorealistic
            "photorealistic": "photorealistic",
            "photo realistic": "photorealistic",
            "realistic photo": "photorealistic",
            "photograph": "photorealistic",
            "real life": "photorealistic",
            "realistic": "photorealistic",
            "photography": "photorealistic",
            "dslr": "photorealistic",
            "hyperrealistic": "photorealistic",
            
            # Cinematic
            "cinematic": "cinematic",
            "movie still": "cinematic",
            "film still": "cinematic",
            "dramatic lighting": "cinematic",
            "hollywood": "cinematic",
            "blockbuster": "cinematic",
            
            # Anime
            "anime": "anime",
            "manga": "anime",
            "japanese animation": "anime",
            "studio ghibli": "anime",
            "anime style": "anime",
            
            # Digital Art
            "digital art": "digital_art",
            "digital illustration": "digital_art",
            "concept art": "digital_art",
            "artstation": "digital_art",
            
            # Oil Painting
            "oil painting": "oil_painting",
            "oil on canvas": "oil_painting",
            "classical painting": "oil_painting",
            "renaissance": "oil_painting",
            "baroque": "oil_painting",
            
            # Watercolor
            "watercolor": "watercolor",
            "watercolour": "watercolor",
            "aquarelle": "watercolor",
            "water color": "watercolor",
            
            # Sketch
            "sketch": "sketch",
            "pencil drawing": "sketch",
            "pencil sketch": "sketch",
            "hand drawn": "sketch",
            "charcoal": "sketch",
            
            # Vector
            "vector": "vector",
            "vector art": "vector",
            "flat design": "vector",
            "graphic design": "vector",
            "svg": "vector",
            
            # 3D Render
            "3d render": "3d_render",
            "3d art": "3d_render",
            "octane": "3d_render",
            "blender": "3d_render",
            "cgi": "3d_render",
            "unreal engine": "3d_render",
            
            # Pixel Art
            "pixel art": "pixel_art",
            "8-bit": "pixel_art",
            "16-bit": "pixel_art",
            "retro game": "pixel_art",
            "pixelated": "pixel_art",
            
            # Minimalist
            "minimalist": "minimalist",
            "minimal": "minimalist",
            "simple": "minimalist",
            "clean design": "minimalist",
            
            # Pop Art
            "pop art": "pop_art",
            "warhol": "pop_art",
            "comic": "pop_art",
            "halftone": "pop_art",
            
            # Cyberpunk
            "cyberpunk": "cyberpunk",
            "neon": "cyberpunk",
            "futuristic city": "cyberpunk",
            "blade runner": "cyberpunk",
            "synthwave": "cyberpunk",
            "vaporwave": "cyberpunk",
            
            # Fantasy
            "fantasy": "fantasy",
            "magical": "fantasy",
            "dungeons and dragons": "fantasy",
            "d&d": "fantasy",
            "lord of the rings": "fantasy",
            "epic fantasy": "fantasy",
            
            # Vintage
            "vintage": "vintage",
            "retro": "vintage",
            "nostalgic": "vintage",
            "old school": "vintage",
            "70s": "vintage",
            "80s": "vintage",
            
            # Isometric
            "isometric": "isometric",
            "isometric view": "isometric",
            "diorama": "isometric",
            
            # Logo
            "logo": "logo",
            "brand logo": "logo",
            "company logo": "logo",
            "icon design": "logo",
        }
        
        for keyword, style in style_keywords.items():
            if keyword in prompt_lower:
                logger.info(f"Detected style '{style}' from keyword: '{keyword}'")
                return style
        
        return None
    
    def _apply_style_preset(
        self, 
        prompt: str, 
        style: Optional[str], 
        model: Optional[str] = None
    ) -> tuple:
        """
        Apply a style preset to enhance the prompt and select optimal model.
        
        Returns:
            (enhanced_prompt, model_to_use, negative_prompt)
        """
        if not style:
            # Try to detect from prompt
            style = self._detect_style_from_prompt(prompt)
        
        if style and style in self.style_presets:
            preset = self.style_presets[style]
            # Only use preset model if no model explicitly specified
            model_to_use = model if model else preset["model"]
            enhanced_prompt = f"{prompt}, {preset['prompt_suffix']}"
            negative_prompt = preset.get("negative", "")
            logger.info(f"Applied style preset '{style}': model={model_to_use}")
            return enhanced_prompt, model_to_use, negative_prompt
        
        return prompt, model or "flux_schnell", ""
    
    async def _run_model(
        self,
        model: str,
        input_data: Dict[str, Any],
        wait: bool = True,
        _fallback_attempt: int = 0,
        _retry_attempt: int = 0
    ) -> Dict[str, Any]:
        """Run a Replicate model with automatic fallback on failure and exponential backoff retry."""
        url = f"{self.base_url}/predictions"
        base_delay = 12  # printify_clean uses 12s base delay for rate limits
        max_retries = 3
        
        # For versioned models (e.g., "owner/model:version_hash")
        if ":" in model:
            parts = model.split(":")
            data = {
                "version": parts[1],
                "input": input_data
            }
        else:
            # For official/deployment models (e.g., "owner/model")
            # Use the models endpoint which returns the latest version
            data = {
                "model": model,
                "input": input_data
            }
        
        try:
            async with aiohttp.ClientSession() as session:
                # Start prediction with rate limit retry
                for attempt in range(_retry_attempt, max_retries):
                    async with session.post(url, headers=self.headers, json=data) as response:
                        if response.status == 429:
                            # Rate limited - exponential backoff (12s, 24s, 48s)
                            delay = base_delay * (2 ** attempt)
                            logger.warning(f"Rate limited. Waiting {delay}s before retry {attempt + 1}/{max_retries}")
                            await asyncio.sleep(delay)
                            continue
                        if response.status >= 400:
                            error = await response.text()
                            raise Exception(f"Replicate API error: {error}")
                        result = await response.json()
                        break
                else:
                    raise Exception(f"Rate limited after {max_retries} retries")
                
                if not wait:
                    return result
                
                # Poll for completion with 15 min timeout for image generation
                prediction_url = result.get("urls", {}).get("get") or f"{url}/{result['id']}"
                timeout_seconds = 900  # 15 minutes from printify_clean
                start_time = asyncio.get_event_loop().time()
                
                while result.get("status") in ["starting", "processing"]:
                    if asyncio.get_event_loop().time() - start_time > timeout_seconds:
                        raise Exception("Timeout waiting for image generation")
                    await asyncio.sleep(1)
                    async with session.get(prediction_url, headers=self.headers) as response:
                        result = await response.json()
                
                if result.get("status") == "failed":
                    raise Exception(f"Prediction failed: {result.get('error')}")
                
                return result
                
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Model {model} failed: {error_msg}")
            
            # Try fallback models if available
            if _fallback_attempt < len(self.FALLBACK_MODELS):
                # Get next fallback model that's different from current
                for fallback_model in self.FALLBACK_MODELS[_fallback_attempt:]:
                    if fallback_model != model and not model.startswith(fallback_model.split('/')[0]):
                        logger.info(f"Trying fallback model: {fallback_model}")
                        return await self._run_model(
                            fallback_model, 
                            input_data, 
                            wait, 
                            _fallback_attempt + 1
                        )
            
            # No more fallbacks, raise the original error
            raise
    
    @tool(
        name="generate_image",
        description="""Generate an image from a text prompt using AI with customizable style, size, and model.
        
STYLE OPTIONS (auto-detected from prompt or explicit):
- "photorealistic", "cinematic", "anime", "digital_art", "oil_painting", "watercolor"
- "sketch", "vector", "3d_render", "pixel_art", "minimalist", "pop_art"
- "cyberpunk", "fantasy", "vintage", "isometric", "logo"

ASPECT RATIOS (natural language supported):
- "portrait", "tall", "vertical" → 2:3 ratio (portrait orientation)
- "landscape", "wide", "horizontal" → 3:2 ratio (landscape orientation)
- "cinematic", "widescreen", "movie" → 16:9 ratio (ultra-wide)
- "square" → 1:1 ratio (default)
- "pinterest", "tiktok", "reels" → 9:16 ratio (phone/story)

MODELS:
- flux_schnell (fast), flux_pro (best), flux_dev, sdxl, sd3_5, ideogram, recraft
- playground, juggernaut (photorealistic), kandinsky (artistic)

Examples:
- generate_image(prompt="a sunset", style="cinematic", aspect_ratio="widescreen")
- generate_image(prompt="anime girl", style="anime", aspect_ratio="portrait")
- generate_image(prompt="a photorealistic dragon") → auto-detects style from prompt
""",
        category="ai_models"
    )
    async def generate_image(
        self,
        prompt: str,
        model: Optional[str] = None,
        style: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        aspect_ratio: Optional[str] = None,
        num_outputs: int = 1,
        negative_prompt: Optional[str] = None,
        quality: str = "standard",
        guidance_scale: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate an image from text with style and size customization.
        
        Args:
            prompt: Text description of the image
            model: Model to use (flux_schnell, flux_pro, sdxl, ideogram, recraft, etc.)
                   If not specified, will be chosen based on style.
            style: Art style preset - "photorealistic", "anime", "digital_art", "oil_painting",
                   "watercolor", "sketch", "vector", "3d_render", "pixel_art", "minimalist",
                   "pop_art", "cyberpunk", "fantasy", "vintage", "cinematic", "isometric", "logo"
            width: Image width (optional, aspect_ratio preferred for Flux)
            height: Image height (optional, aspect_ratio preferred for Flux)
            aspect_ratio: Aspect ratio - accepts natural language like "portrait", "tall", "wide", 
                         "landscape", "square", "cinematic" OR standard ratios like "16:9", "2:3", etc.
                         If not provided, will auto-detect from prompt keywords.
            num_outputs: Number of images to generate (1-4)
            negative_prompt: What to avoid in the image
            quality: Image quality - "standard" or "hd" (affects generation time)
            guidance_scale: How closely to follow the prompt (1.0-20.0, default varies by model)
        """
        # Apply style preset (enhances prompt and may select optimal model)
        enhanced_prompt, selected_model, style_negative = self._apply_style_preset(
            prompt, style, model
        )
        
        # Use provided model if explicit, otherwise use style-selected model
        model_to_use = model if model else selected_model
        model_id = self.models.get(model_to_use, model_to_use)
        
        # Determine the final aspect ratio
        final_aspect_ratio = None
        
        # Priority: explicit aspect_ratio param > width/height > prompt detection > default
        if aspect_ratio:
            # Normalize natural language to valid ratio
            final_aspect_ratio = self._normalize_aspect_ratio(aspect_ratio)
            logger.info(f"Using explicit aspect_ratio: {aspect_ratio} → {final_aspect_ratio}")
        elif width and height and (width != 1024 or height != 1024):
            # Use provided dimensions
            final_aspect_ratio = self._get_aspect_ratio(width, height)
            logger.info(f"Using width/height: {width}x{height} → {final_aspect_ratio}")
        else:
            # Try to detect from prompt
            detected = self._detect_aspect_ratio_from_prompt(prompt)
            if detected:
                final_aspect_ratio = detected
                logger.info(f"Auto-detected aspect ratio from prompt: {final_aspect_ratio}")
            else:
                # Default to square
                final_aspect_ratio = "1:1"
        
        input_data = {
            "prompt": enhanced_prompt,
            "num_outputs": min(num_outputs, 4)  # Cap at 4
        }
        
        # Combine negative prompts (explicit + style preset)
        final_negative = ""
        if negative_prompt and style_negative:
            final_negative = f"{negative_prompt}, {style_negative}"
        elif negative_prompt:
            final_negative = negative_prompt
        elif style_negative:
            final_negative = style_negative
        
        if final_negative:
            input_data["negative_prompt"] = final_negative
        
        # Add quality and guidance if specified
        if quality == "hd" and "flux" in model_to_use.lower():
            input_data["num_inference_steps"] = 50  # Higher steps for HD
        
        if guidance_scale is not None:
            input_data["guidance_scale"] = guidance_scale
        
        # Model-specific adjustments
        if "flux" in model_to_use.lower():
            # Flux uses aspect_ratio strings like "1:1", "16:9" etc
            input_data["aspect_ratio"] = final_aspect_ratio
        else:
            # Other models use width/height - convert aspect ratio back to pixels
            ar_to_pixels = {
                "1:1": (1024, 1024),
                "2:3": (768, 1152),  # Portrait/Tall
                "3:2": (1152, 768),  # Landscape
                "3:4": (768, 1024),  # Portrait
                "4:3": (1024, 768),  # Landscape
                "4:5": (896, 1120),  # Portrait
                "5:4": (1120, 896),  # Landscape
                "9:16": (576, 1024), # Phone/Story portrait
                "16:9": (1024, 576), # Widescreen
                "9:21": (576, 1344), # Ultra tall
                "21:9": (1344, 576), # Ultra wide
            }
            px_width, px_height = ar_to_pixels.get(final_aspect_ratio, (1024, 1024))
            input_data["width"] = width or px_width
            input_data["height"] = height or px_height
        
        result = await self._run_model(model_id, input_data)
        
        output = result.get("output", [])
        if isinstance(output, str):
            output = [output]
        
        return {
            "success": True,
            "images": output,
            "model": model_to_use,
            "style": style or self._detect_style_from_prompt(prompt),
            "prompt": prompt,
            "enhanced_prompt": enhanced_prompt,
            "aspect_ratio": final_aspect_ratio,
            "prediction_id": result.get("id"),
            "quality": quality
        }
    
    @tool(
        name="generate_tshirt_design",
        description="Generate a t-shirt ready design with transparent background. Automatically handles style mapping for Recraft model.",
        category="ai_models"
    )
    async def generate_tshirt_design(
        self,
        prompt: str,
        style: str = "vector",
        model: str = "recraft"
    ) -> Dict[str, Any]:
        """
        Generate a t-shirt ready design.
        
        Args:
            prompt: Design description
            style: Design style - one of:
                - "vector": Clean vector-style poster art
                - "illustration": Digital illustration
                - "hand_drawn": Hand-drawn sketch style
                - "poster": Alternative poster art style
                - "realistic": Realistic image style
                - "minimalist": Simple outline style
                - "cute"/"kawaii": Cute illustration style
                - "cartoon": Cartoon style
            model: Model to use (recraft recommended)
        """
        # Enhanced prompt for t-shirt designs
        enhanced_prompt = f"{prompt}, {style} art style, clean design, suitable for t-shirt print, high contrast, no background, centered composition"
        
        if model == "recraft":
            model_id = self.models["recraft"]
            # Map user-friendly style names to valid Recraft styles
            # Valid Recraft styles: any, realistic_image, digital_illustration, 
            # digital_illustration/pixel_art, digital_illustration/hand_drawn,
            # digital_illustration/grain, digital_illustration/infantile_sketch,
            # digital_illustration/2d_art_poster, digital_illustration/handmade_3d,
            # digital_illustration/hand_drawn_outline, digital_illustration/engraving_color,
            # digital_illustration/2d_art_poster_2, realistic_image/b_and_w,
            # realistic_image/hard_flash, realistic_image/hdr, realistic_image/natural_light,
            # realistic_image/studio_portrait, realistic_image/enterprise, realistic_image/motion_blur
            style_map = {
                # Standard styles
                "vector": "digital_illustration/2d_art_poster",
                "illustration": "digital_illustration",
                "hand_drawn": "digital_illustration/hand_drawn",
                "poster": "digital_illustration/2d_art_poster_2",
                "realistic": "realistic_image",
                "minimalist": "digital_illustration/hand_drawn_outline",
                # Additional common style requests
                "cute": "digital_illustration/infantile_sketch",
                "kawaii": "digital_illustration/infantile_sketch",
                "cartoon": "digital_illustration",
                "anime": "digital_illustration",
                "pixel": "digital_illustration/pixel_art",
                "pixel_art": "digital_illustration/pixel_art",
                "sketch": "digital_illustration/hand_drawn",
                "3d": "digital_illustration/handmade_3d",
                "engraving": "digital_illustration/engraving_color",
                "vintage": "digital_illustration/engraving_color",
                "grainy": "digital_illustration/grain",
                "grain": "digital_illustration/grain",
                # Direct Recraft style names (pass-through)
                "digital_illustration": "digital_illustration",
                "digital_illustration/2d_art_poster": "digital_illustration/2d_art_poster",
                "digital_illustration/infantile_sketch": "digital_illustration/infantile_sketch",
                "any": "any",
            }
            # Get mapped style or default to digital_illustration for t-shirt designs
            recraft_style = style_map.get(style.lower(), "digital_illustration/2d_art_poster")
            input_data = {
                "prompt": enhanced_prompt,
                "style": recraft_style,
                "size": "1024x1024"
            }
            logger.info(f"Using Recraft style: {recraft_style} (from requested: {style})")
        else:
            model_id = self.models.get(model, self.models["flux_schnell"])
            input_data = {
                "prompt": enhanced_prompt,
                "aspect_ratio": "1:1"
            }
        
        result = await self._run_model(model_id, input_data)
        
        output = result.get("output", [])
        if isinstance(output, str):
            output = [output]
        
        return {
            "success": True,
            "images": output,
            "design_type": "tshirt",
            "style": style,
            "prompt": prompt
        }
    
    @tool(
        name="remove_background",
        description="Remove background from an image",
        category="ai_models"
    )
    async def remove_background(
        self,
        image_url: str,
        model: str = "birefnet"
    ) -> Dict[str, Any]:
        """
        Remove background from an image.
        
        Args:
            image_url: URL of the image
            model: Model to use (birefnet, rembg)
        """
        if model == "birefnet":
            model_id = "lucataco/remove-bg:95fcc2a26d3899cd6c2691c900465aaeff466285a65c14638cc5f36f34befaf1"
        else:
            model_id = "cjwbw/rembg:fb8af171cfa1616ddcf1242c093f9c46bcada5ad4cf6f2fbe8b81b330ec5c003"
        
        result = await self._run_model(model_id, {"image": image_url})
        
        return {
            "success": True,
            "image": result.get("output"),
            "original": image_url
        }
    
    @tool(
        name="upscale_image",
        description="Upscale an image to higher resolution",
        category="ai_models"
    )
    async def upscale_image(
        self,
        image_url: str,
        scale: int = 2
    ) -> Dict[str, Any]:
        """
        Upscale an image.
        
        Args:
            image_url: URL of the image
            scale: Upscale factor (2 or 4)
        """
        model_id = "nightmareai/real-esrgan:f121d640bd286e1fdc67f9799164c1d5be36ff74576ee11c803ae5b665dd46aa"
        
        result = await self._run_model(model_id, {
            "image": image_url,
            "scale": scale,
            "face_enhance": False
        })
        
        return {
            "success": True,
            "image": result.get("output"),
            "scale": scale
        }
    
    @tool(
        name="generate_lifestyle_scene",
        description="Generate a lifestyle scene showing a product in context",
        category="ai_models"
    )
    async def generate_lifestyle_scene(
        self,
        product_description: str,
        scene_type: str = "outdoor",
        style: str = "photorealistic",
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a lifestyle scene for product marketing.
        
        Args:
            product_description: Description of the product
            scene_type: Type of scene (outdoor, indoor, studio, urban, nature)
            style: Style (photorealistic, artistic, minimal)
            image_url: Optional product image URL to incorporate into scene
        """
        scene_prompts = {
            "outdoor": "outdoor setting, natural lighting, scenic background",
            "indoor": "cozy indoor setting, warm lighting, modern interior",
            "studio": "professional studio photography, clean background, soft lighting",
            "urban": "urban street scene, city background, dynamic composition",
            "nature": "natural environment, forest or beach, peaceful atmosphere"
        }
        
        scene = scene_prompts.get(scene_type, scene_prompts["outdoor"])
        
        # If image_url provided, generate composite scene
        if image_url:
            prompt = f"Professional product photography showing {product_description}, {scene}, {style} style, high quality marketing image, product prominently displayed"
        else:
            prompt = f"Person wearing {product_description}, {scene}, {style} style, high quality photography, professional marketing image"
        
        return await self.generate_image(
            prompt=prompt,
            model="flux_pro",
            width=1024,
            height=1024
        )
    
    @tool(
        name="generate_product_mockup",
        description="Generate a product mockup image",
        category="ai_models"
    )
    async def generate_product_mockup(
        self,
        product_type: str = None,
        design_description: str = None,
        background: str = "white",
        product: str = None,  # Alias for product_type
        design: str = None,  # Alias for design_description
        description: str = None,  # Alias for design_description
        prompt: str = None,  # Alias for complete scene description
        design_url: str = None  # Alias for design_description when URL provided
    ) -> Dict[str, Any]:
        """
        Generate a product mockup.
        
        Args:
            product_type: Type of product (tshirt, hoodie, mug, poster, phone_case)
            design_description: Description of the design on the product
            background: Background color/style
            product: Alias for product_type
            design: Alias for design_description
            description: Alias for design_description
            prompt: Alias for complete scene description (full mockup prompt)
            design_url: Alias for design_description (when design is referenced by URL)
        """
        # Handle aliases
        product_type = product_type or product or "mug"
        design_description = design_description or design or description or design_url or "colorful design"
        
        # If prompt provided (full scene), use it directly
        if prompt:
            return await self.generate_image(
                prompt=prompt,
                model="flux_pro",
                width=1024,
                height=1024
            )
        
        # Otherwise build prompt from components
        mockup_prompts = {
            "tshirt": "professional product photography of a t-shirt mockup",
            "hoodie": "professional product photography of a hoodie mockup",
            "mug": "professional product photography of a ceramic mug mockup",
            "poster": "professional product photography of a framed poster mockup",
            "phone_case": "professional product photography of a phone case mockup"
        }
        
        base_prompt = mockup_prompts.get(product_type, mockup_prompts["tshirt"])
        full_prompt = f"{base_prompt} with {design_description} design, {background} background, studio lighting, high resolution, commercial quality"
        
        return await self.generate_image(
            prompt=full_prompt,
            model="flux_pro",
            width=1024,
            height=1024
        )

    @tool(
        name="adjust_image",
        description="""Adjust image properties like brightness, contrast, saturation, and more.
        
Supports natural language adjustments:
- "make it brighter", "increase brightness" → brightness adjustment
- "more contrast", "increase contrast" → contrast adjustment
- "more saturated", "vibrant colors" → saturation adjustment
- "warmer", "cooler" → color temperature adjustment
- "sharper", "blur" → sharpness adjustment

All values are percentage adjustments from -100 to +100 (0 = no change).
""",
        category="ai_models"
    )
    async def adjust_image(
        self,
        image_url: str,
        brightness: Optional[float] = None,
        contrast: Optional[float] = None,
        saturation: Optional[float] = None,
        sharpness: Optional[float] = None,
        warmth: Optional[float] = None,
        exposure: Optional[float] = None,
        shadows: Optional[float] = None,
        highlights: Optional[float] = None,
        vibrance: Optional[float] = None,
        adjustment_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Adjust image properties using natural language or explicit values.
        
        Args:
            image_url: URL of the image to adjust
            brightness: Brightness adjustment (-100 to +100, 0 = no change)
            contrast: Contrast adjustment (-100 to +100, 0 = no change)
            saturation: Saturation adjustment (-100 to +100, 0 = no change)
            sharpness: Sharpness adjustment (-100 to +100, 0 = no change)
            warmth: Color temperature adjustment (-100=cooler to +100=warmer)
            exposure: Exposure adjustment (-100 to +100)
            shadows: Shadow detail adjustment (-100 to +100)
            highlights: Highlight detail adjustment (-100 to +100)
            vibrance: Vibrance adjustment (-100 to +100)
            adjustment_description: Natural language description of adjustments
        """
        import io
        from PIL import Image, ImageEnhance, ImageFilter
        
        # Parse natural language adjustments if provided
        if adjustment_description:
            desc_lower = adjustment_description.lower()
            
            # Brightness keywords
            if any(kw in desc_lower for kw in ["brighter", "lighten", "more light", "increase brightness"]):
                brightness = brightness if brightness is not None else 30
            elif any(kw in desc_lower for kw in ["darker", "darken", "less light", "decrease brightness"]):
                brightness = brightness if brightness is not None else -30
            
            # Contrast keywords
            if any(kw in desc_lower for kw in ["more contrast", "increase contrast", "punchier", "pop"]):
                contrast = contrast if contrast is not None else 30
            elif any(kw in desc_lower for kw in ["less contrast", "decrease contrast", "flatter", "softer"]):
                contrast = contrast if contrast is not None else -30
            
            # Saturation keywords
            if any(kw in desc_lower for kw in ["more saturated", "vibrant", "colorful", "richer colors"]):
                saturation = saturation if saturation is not None else 40
            elif any(kw in desc_lower for kw in ["desaturated", "less color", "muted", "grayscale"]):
                saturation = saturation if saturation is not None else -40
            
            # Warmth keywords
            if any(kw in desc_lower for kw in ["warmer", "warm", "orange", "golden"]):
                warmth = warmth if warmth is not None else 40
            elif any(kw in desc_lower for kw in ["cooler", "cool", "blue", "cold"]):
                warmth = warmth if warmth is not None else -40
            
            # Sharpness keywords
            if any(kw in desc_lower for kw in ["sharper", "crisp", "more detail", "sharpen"]):
                sharpness = sharpness if sharpness is not None else 50
            elif any(kw in desc_lower for kw in ["blur", "soften", "soft", "dreamy"]):
                sharpness = sharpness if sharpness is not None else -50
        
        # Fetch the image
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch image: HTTP {response.status}")
                image_data = await response.read()
        
        # Open image with PIL
        img = Image.open(io.BytesIO(image_data))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        applied_adjustments = []
        
        # Apply brightness adjustment
        if brightness is not None and brightness != 0:
            factor = 1 + (brightness / 100)
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(factor)
            applied_adjustments.append(f"brightness: {brightness:+.0f}%")
        
        # Apply contrast adjustment
        if contrast is not None and contrast != 0:
            factor = 1 + (contrast / 100)
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(factor)
            applied_adjustments.append(f"contrast: {contrast:+.0f}%")
        
        # Apply saturation adjustment
        if saturation is not None and saturation != 0:
            factor = 1 + (saturation / 100)
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(factor)
            applied_adjustments.append(f"saturation: {saturation:+.0f}%")
        
        # Apply sharpness adjustment
        if sharpness is not None and sharpness != 0:
            if sharpness > 0:
                factor = 1 + (sharpness / 50)
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(factor)
            else:
                # Apply blur for negative sharpness
                blur_radius = abs(sharpness) / 20
                img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
            applied_adjustments.append(f"sharpness: {sharpness:+.0f}%")
        
        # Apply warmth adjustment (shift color temperature)
        if warmth is not None and warmth != 0:
            import numpy as np
            img_array = np.array(img, dtype=np.float32)
            
            # Warm = more red/yellow, Cool = more blue
            warmth_factor = warmth / 100
            if warmth > 0:
                img_array[:, :, 0] = np.clip(img_array[:, :, 0] * (1 + warmth_factor * 0.15), 0, 255)  # Red
                img_array[:, :, 2] = np.clip(img_array[:, :, 2] * (1 - warmth_factor * 0.1), 0, 255)   # Blue
            else:
                img_array[:, :, 0] = np.clip(img_array[:, :, 0] * (1 + warmth_factor * 0.1), 0, 255)   # Red
                img_array[:, :, 2] = np.clip(img_array[:, :, 2] * (1 - warmth_factor * 0.15), 0, 255)  # Blue
            
            img = Image.fromarray(img_array.astype(np.uint8))
            applied_adjustments.append(f"warmth: {warmth:+.0f}%")
        
        # Save the adjusted image
        import uuid
        from pathlib import Path
        output_dir = Path("data/files/edited")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_filename = f"adjusted_{uuid.uuid4().hex[:8]}.png"
        output_path = output_dir / output_filename
        img.save(output_path, "PNG", quality=95)
        
        # Create a public URL (if possible)
        local_url = f"/files/edited/{output_filename}"
        
        return {
            "success": True,
            "image": local_url,
            "original": image_url,
            "adjustments": applied_adjustments,
            "adjustment_description": adjustment_description
        }

    @tool(
        name="edit_image_with_ai",
        description="""Use AI to edit an image based on natural language instructions.
        
Supports:
- "remove the background" → background removal
- "change the sky to sunset" → inpainting/replacement
- "make it look like anime" → style transfer
- "add a hat to the person" → object addition
- "remove the car" → object removal
- "extend the image to the left" → outpainting
""",
        category="ai_models"
    )
    async def edit_image_with_ai(
        self,
        image_url: str,
        instruction: str,
        mask_url: Optional[str] = None,
        strength: float = 0.8
    ) -> Dict[str, Any]:
        """
        Edit an image using AI based on natural language instructions.
        
        Args:
            image_url: URL of the image to edit
            instruction: Natural language description of the edit
            mask_url: Optional URL of a mask image (white = edit area)
            strength: How much to change (0.0 = no change, 1.0 = maximum)
        """
        instruction_lower = instruction.lower()
        
        # Determine the best editing approach based on instruction
        if any(kw in instruction_lower for kw in ["remove background", "remove bg", "transparent", "no background"]):
            # Use background removal model
            model_id = "lucataco/remove-bg:95fcc2a26d3899cd6c2691c900465aaeff466285a65c14638cc5f36f34befaf1"
            input_data = {"image": image_url}
            edit_type = "background_removal"
        
        elif any(kw in instruction_lower for kw in ["upscale", "higher resolution", "enhance quality", "4k", "hd"]):
            # Use upscaling model
            model_id = "nightmareai/real-esrgan:f121d640bd286e1fdc67f9799164c1d5be36ff74576ee11c803ae5b665dd46aa"
            input_data = {"image": image_url, "scale": 2}
            edit_type = "upscale"
        
        elif any(kw in instruction_lower for kw in ["colorize", "add color", "black and white to color"]):
            # Use colorization model
            model_id = "arielreplicate/deoldify_image:0da600fab0c45a66211339f1c16b71345d22f26ef5fea3dca1bb90bb5711e950"
            input_data = {"input_image": image_url}
            edit_type = "colorize"
        
        elif any(kw in instruction_lower for kw in ["enhance face", "restore face", "fix face"]):
            # Use face enhancement model
            model_id = "tencentarc/gfpgan:0fbacf7afc6c144e5be9767cff80f25aff23e52b0708f17e20f9879b2f21516c"
            input_data = {"img": image_url}
            edit_type = "face_enhance"
        
        else:
            # Use general image-to-image editing with SDXL
            model_id = "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
            input_data = {
                "image": image_url,
                "prompt": instruction,
                "strength": strength
            }
            if mask_url:
                input_data["mask"] = mask_url
            edit_type = "ai_edit"
        
        result = await self._run_model(model_id, input_data)
        
        output = result.get("output", [])
        if isinstance(output, str):
            output = [output]
        elif isinstance(output, list) and len(output) > 0:
            output = output[0] if isinstance(output[0], str) else output
        
        return {
            "success": True,
            "image": output[0] if isinstance(output, list) else output,
            "original": image_url,
            "instruction": instruction,
            "edit_type": edit_type
        }

    # ═══════════════════════════════════════════════════════════════════
    # TEXT OVERLAY FOR ADS (from printify_clean)
    # ═══════════════════════════════════════════════════════════════════
    
    @tool(
        name="add_text_overlay",
        description="""Add professional text overlay to an image for ads/marketing.
        
Supports:
- Headlines with glow/shadow effects
- Call-to-action buttons
- Price badges
- Brand logos/names
- Platform-optimized layouts (Instagram, Facebook, Pinterest, etc.)
""",
        category="image_editing"
    )
    async def add_text_overlay(
        self,
        image_url: str,
        headline: str,
        tagline: str = "",
        cta: str = "",
        price: str = "",
        brand_name: str = "",
        platform: str = "instagram_post",
        style: str = "bold",
        primary_color: str = "#ffffff",
        accent_color: str = "#ff6b35"
    ) -> Dict[str, Any]:
        """
        Add professional text overlay to an image.
        
        Args:
            image_url: URL or path of the base image
            headline: Main headline text
            tagline: Secondary tagline (optional)
            cta: Call-to-action text (optional)
            price: Price text (optional, e.g., "$24.99")
            brand_name: Brand name to display (optional)
            platform: Target platform for layout optimization
            style: Visual style (bold, minimal, luxury, playful)
            primary_color: Primary text color (hex)
            accent_color: Accent color for CTA (hex)
            
        Returns:
            {"success": bool, "image": str, "overlays_added": list}
        """
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        # Fetch image
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status != 200:
                    return {"success": False, "error": f"Failed to fetch image: HTTP {response.status}"}
                image_data = await response.read()
        
        # Load image
        img = Image.open(io.BytesIO(image_data)).convert("RGBA")
        width, height = img.size
        draw = ImageDraw.Draw(img)
        
        overlays_added = []
        
        # Calculate text sizes based on image dimensions
        headline_size = int(min(width, height) * 0.08)
        tagline_size = int(headline_size * 0.5)
        cta_size = int(headline_size * 0.6)
        price_size = int(headline_size * 0.7)
        brand_size = int(headline_size * 0.4)
        
        # Get system font (with fallbacks)
        def get_font(size: int, bold: bool = False):
            font_paths = [
                "/System/Library/Fonts/Helvetica.ttc",
                "/System/Library/Fonts/Arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]
            for path in font_paths:
                try:
                    if os.path.exists(path):
                        return ImageFont.truetype(path, size)
                except:
                    continue
            return ImageFont.load_default()
        
        headline_font = get_font(headline_size, bold=True)
        tagline_font = get_font(tagline_size)
        cta_font = get_font(cta_size, bold=True)
        price_font = get_font(price_size, bold=True)
        brand_font = get_font(brand_size)
        
        # Platform-specific layouts
        layouts = {
            "instagram_post": {"headline_y": 0.12, "tagline_y": 0.22, "price_y": 0.75, "cta_y": 0.85, "brand_y": 0.95},
            "instagram_story": {"headline_y": 0.15, "tagline_y": 0.22, "price_y": 0.78, "cta_y": 0.85, "brand_y": 0.93},
            "facebook_post": {"headline_y": 0.08, "tagline_y": 0.16, "price_y": 0.80, "cta_y": 0.88, "brand_y": 0.95},
            "twitter": {"headline_y": 0.10, "tagline_y": 0.20, "price_y": 0.78, "cta_y": 0.88, "brand_y": 0.95},
            "pinterest": {"headline_y": 0.08, "tagline_y": 0.14, "price_y": 0.85, "cta_y": 0.90, "brand_y": 0.96},
        }
        layout = layouts.get(platform, layouts["instagram_post"])
        
        def add_shadow_text(x, y, text, font, color, shadow_color="#000000"):
            """Draw text with shadow effect."""
            for offset in range(3, 0, -1):
                draw.text((x + offset, y + offset), text, font=font, fill=shadow_color)
            draw.text((x, y), text, font=font, fill=color)
        
        # Add headline
        if headline:
            bbox = draw.textbbox((0, 0), headline, font=headline_font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            y = int(height * layout["headline_y"])
            add_shadow_text(x, y, headline, headline_font, primary_color)
            overlays_added.append("headline")
        
        # Add tagline
        if tagline:
            bbox = draw.textbbox((0, 0), tagline, font=tagline_font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            y = int(height * layout["tagline_y"])
            add_shadow_text(x, y, tagline, tagline_font, primary_color)
            overlays_added.append("tagline")
        
        # Add price badge
        if price:
            bbox = draw.textbbox((0, 0), price, font=price_font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            y = int(height * layout["price_y"])
            # Draw price with accent background
            padding = 10
            draw.rectangle([x - padding, y - padding, x + text_width + padding, y + bbox[3] - bbox[1] + padding], fill=accent_color)
            draw.text((x, y), price, font=price_font, fill="#ffffff")
            overlays_added.append("price")
        
        # Add CTA
        if cta:
            bbox = draw.textbbox((0, 0), cta, font=cta_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (width - text_width) // 2
            y = int(height * layout["cta_y"])
            # Draw CTA button
            padding = 15
            draw.rounded_rectangle(
                [x - padding, y - padding//2, x + text_width + padding, y + text_height + padding],
                radius=8,
                fill=accent_color
            )
            draw.text((x, y), cta, font=cta_font, fill="#ffffff")
            overlays_added.append("cta")
        
        # Add brand name
        if brand_name:
            bbox = draw.textbbox((0, 0), brand_name, font=brand_font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            y = int(height * layout["brand_y"])
            draw.text((x, y), brand_name, font=brand_font, fill=primary_color)
            overlays_added.append("brand")
        
        # Save output
        import uuid
        from pathlib import Path
        output_dir = Path("data/files/ads")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_filename = f"ad_{uuid.uuid4().hex[:8]}.png"
        output_path = output_dir / output_filename
        
        # Convert back to RGB for saving
        img_rgb = Image.new("RGB", img.size, (255, 255, 255))
        img_rgb.paste(img, mask=img.split()[3] if len(img.split()) == 4 else None)
        img_rgb.save(output_path, "PNG", quality=95)
        
        return {
            "success": True,
            "image": f"/files/ads/{output_filename}",
            "original": image_url,
            "overlays_added": overlays_added,
            "platform": platform,
            "style": style
        }
