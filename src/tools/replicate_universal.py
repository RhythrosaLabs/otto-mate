"""
Universal Replicate AI Tool
===========================

Dynamically discover, search, and run ANY Replicate model.
The ultimate AI model interface - if it's on Replicate, we can use it.
"""

import logging
import aiohttp
import asyncio
import json
import re
from typing import Optional, Dict, Any, List
from .core import tool, ToolBase

logger = logging.getLogger(__name__)


class ReplicateUniversal(ToolBase):
    """
    Universal Replicate interface - search, discover, and run ANY model.
    
    This tool enables:
    - Searching for models by capability/description
    - Getting model details and input schemas
    - Running any model with dynamic parameter inference
    - Intelligent model selection based on task requirements
    """
    
    # Models that require proper image URL extensions
    STRICT_URL_MODELS = [
        "kwaivgi/kling-v1.6-pro",
        "kwaivgi/kling-v2.5-turbo-pro",
        "luma/ray-2-540p",
        "luma/ray-flash-2",
        "minimax/video-01",
        "minimax/hailuo-2.3-fast",
    ]
    
    def __init__(self, api_token: str):
        self.token = api_token
        self.base_url = "https://api.replicate.com/v1"
        self.headers = {
            "Authorization": f"Token {api_token}",
            "Content-Type": "application/json"
        }
        
        # Cache for model schemas (avoid repeated lookups)
        self._model_cache: Dict[str, Dict] = {}
        
        # Comprehensive model shortcuts for ALL AI tasks
        self.model_shortcuts = {
            # ═══════════════════════════════════════════════════════════════
            # IMAGE GENERATION - Multiple quality tiers
            # ═══════════════════════════════════════════════════════════════
            "image": "black-forest-labs/flux-schnell",
            "image_fast": "black-forest-labs/flux-schnell",
            "image_pro": "black-forest-labs/flux-1.1-pro",
            "image_quality": "black-forest-labs/flux-1.1-pro",
            "flux": "black-forest-labs/flux-schnell",
            "flux_pro": "black-forest-labs/flux-1.1-pro",
            "sdxl": "stability-ai/sdxl",
            "sd3": "stability-ai/stable-diffusion-3",
            "ideogram": "ideogram-ai/ideogram-v2",
            "ideogram_text": "ideogram-ai/ideogram-v2",  # Best for text in images
            "recraft": "recraft-ai/recraft-v3",
            "recraft_vector": "recraft-ai/recraft-v3",  # Best for vector/illustration
            "midjourney": "tstramer/midjourney-diffusion",
            "realistic": "adirik/realvisxl-v4.0",
            "photorealistic": "adirik/realvisxl-v4.0",
            "anime": "cagliostrolab/animagine-xl-3.1",
            "artistic": "stability-ai/sdxl",
            
            # ═══════════════════════════════════════════════════════════════
            # IMAGE EDITING & ENHANCEMENT
            # ═══════════════════════════════════════════════════════════════
            "remove_bg": "cjwbw/rembg",
            "background_remove": "cjwbw/rembg",
            "upscale": "nightmareai/real-esrgan",
            "upscale_4x": "nightmareai/real-esrgan",
            "upscale_face": "tencentarc/gfpgan",
            "restore_face": "tencentarc/gfpgan",
            "face_restore": "tencentarc/gfpgan",
            "inpaint": "stability-ai/stable-diffusion-inpainting",
            "edit_image": "timothybrooks/instruct-pix2pix",
            "img2img": "stability-ai/sdxl",
            "colorize": "arielreplicate/deoldify_image",
            "outpaint": "stability-ai/stable-diffusion-inpainting",
            "style_transfer": "lucataco/neural-style-tf",
            "sketch_to_image": "jagilley/controlnet-scribble",
            "depth_to_image": "jagilley/controlnet-depth",
            "pose_to_image": "jagilley/controlnet-openpose",
            
            # ═══════════════════════════════════════════════════════════════
            # VIDEO GENERATION & EDITING - 15+ Models from printify_clean
            # ═══════════════════════════════════════════════════════════════
            # Primary models
            "video": "minimax/video-01",
            "video_fast": "anotherjesse/zeroscope-v2-xl",
            "video_pro": "kwaivgi/kling-v2.5-turbo-pro",
            "video_best": "openai/sora-2",
            "text_to_video": "minimax/video-01",
            "image_to_video": "kwaivgi/kling-v1.6-pro",
            "animate": "stability-ai/stable-video-diffusion",
            "animate_image": "kwaivgi/kling-v1.6-pro",
            
            # Kling models (Premium quality)
            "kling": "kwaivgi/kling-v1.6-pro",
            "kling_pro": "kwaivgi/kling-v1.6-pro",
            "kling_turbo": "kwaivgi/kling-v2.5-turbo-pro",
            
            # Luma models (Fast, high quality)
            "luma": "luma/ray-2-540p",
            "luma_video": "luma/ray-2-540p",
            "luma_flash": "luma/ray-flash-2",
            "luma_ray2": "luma/ray-2-540p",
            
            # OpenAI Sora (Best quality, slow)
            "sora": "openai/sora-2",
            "sora2": "openai/sora-2",
            
            # Google Veo models (Audio support)
            "veo": "google/veo-3",
            "veo3": "google/veo-3",
            "veo3_fast": "google/veo-3-fast",
            "veo31": "google/veo-3.1-fast",
            "veo2": "google/veo-2",
            
            # Pixverse (Anime style, 1080p)
            "pixverse": "pixverse/pixverse-v5",
            "pixverse5": "pixverse/pixverse-v5",
            "pixverse45": "pixverse/pixverse-v4.5",
            
            # Leonardo Motion
            "leonardo": "leonardoai/motion-2.0",
            "leonardo_motion": "leonardoai/motion-2.0",
            
            # Minimax/Hailuo
            "minimax": "minimax/video-01",
            "hailuo": "minimax/hailuo-2.3-fast",
            "hailuo_fast": "minimax/hailuo-2.3-fast",
            
            # Wan Video (Fast T2V)
            "wan": "wan-video/wan-2.5-t2v-fast",
            "wan_video": "wan-video/wan-2.5-t2v-fast",
            
            # Seedance (Cinematic)
            "seedance": "bytedance/seedance-1-pro-fast",
            "seedance_pro": "bytedance/seedance-1-pro-fast",
            
            # SVD (Classic image-to-video)
            "svd": "stability-ai/stable-video-diffusion",
            
            # Video editing
            "video_edit": "luma/modify-video",
            "video_modify": "luma/modify-video",
            "v2v": "wan-video/wan-2.5-v2v-fast",
            "video_to_video": "wan-video/wan-2.5-v2v-fast",
            "lip_sync": "chenxwh/video-retalking",
            "video_upscale": "lucataco/video-upscaler",
            "video_stabilize": "lucataco/video-stabilizer",
            "slow_motion": "pollinations/video-frame-interpolation",
            "remove_bg_video": "arielreplicate/robust_video_matting",
            
            # ═══════════════════════════════════════════════════════════════
            # AUDIO & MUSIC
            # ═══════════════════════════════════════════════════════════════
            "music": "meta/musicgen",
            "music_gen": "meta/musicgen",
            "music_melody": "meta/musicgen",
            "music_hd": "google/lyria-2",
            "music_vocals": "minimax/music-1.5",
            "music_loop": "andreasjansson/musicgen-looper",
            "stable_audio": "stability-ai/stable-audio-2.5",
            "speech_to_text": "openai/whisper",
            "transcribe": "openai/whisper",
            "whisper": "openai/whisper",
            "tts": "minimax/speech-02-hd",
            "text_to_speech": "minimax/speech-02-hd",
            "tts_hd": "minimax/speech-02-hd",
            "bark": "cjwbw/bark",
            "voice_clone": "lucataco/xtts-v2",
            "clone_voice": "lucataco/xtts-v2",
            "audio_enhance": "cjwbw/audio-super-res",
            "audio_separate": "cjwbw/demucs",
            "sound_effects": "haoheliu/audio-ldm-2",
            "audio_ldm": "haoheliu/audio-ldm-2",
            
            # ═══════════════════════════════════════════════════════════════
            # CODE GENERATION & ANALYSIS
            # ═══════════════════════════════════════════════════════════════
            "code": "meta/codellama-34b-instruct",
            "codellama": "meta/codellama-34b-instruct",
            "code_gen": "meta/codellama-34b-instruct",
            "code_completion": "meta/codellama-34b-instruct",
            "code_python": "meta/codellama-34b-python",
            "code_review": "meta/codellama-34b-instruct",
            "code_explain": "meta/codellama-34b-instruct",
            "sql": "defog/sqlcoder-7b-2",
            "sql_gen": "defog/sqlcoder-7b-2",
            
            # ═══════════════════════════════════════════════════════════════
            # LANGUAGE MODELS & TEXT
            # ═══════════════════════════════════════════════════════════════
            "llm": "meta/llama-2-70b-chat",
            "llama": "meta/llama-2-70b-chat",
            "llama3": "meta/meta-llama-3-70b-instruct",
            "mistral": "mistralai/mixtral-8x7b-instruct-v0.1",
            "mixtral": "mistralai/mixtral-8x7b-instruct-v0.1",
            "summarize": "meta/llama-2-70b-chat",
            "translate": "meta/llama-2-70b-chat",
            "chat": "meta/meta-llama-3-70b-instruct",
            
            # ═══════════════════════════════════════════════════════════════
            # VISION & IMAGE UNDERSTANDING
            # ═══════════════════════════════════════════════════════════════
            "vision": "yorickvp/llava-13b",
            "llava": "yorickvp/llava-13b",
            "image_caption": "salesforce/blip",
            "blip": "salesforce/blip",
            "describe_image": "yorickvp/llava-13b",
            "ocr": "abiruyt/text-extract-ocr",
            "text_extract": "abiruyt/text-extract-ocr",
            "nsfw_detect": "lucataco/nsfw_image_detection",
            "face_detect": "daanelson/face-detection",
            "object_detect": "adirik/grounding-dino",
            
            # ═══════════════════════════════════════════════════════════════
            # 3D GENERATION - Updated with working models (Feb 2026)
            # ═══════════════════════════════════════════════════════════════
            # Image-to-3D models (best quality)
            "3d": "firtoz/trellis",  # RECOMMENDED - fastest and best quality
            "3d_gen": "firtoz/trellis",
            "trellis": "firtoz/trellis",  # Can create 3D from single image in <1 min
            "image_to_3d": "firtoz/trellis",
            
            # Hunyuan3D variants (working versions)
            "hunyuan3d": "prunaai/hunyuan3d-2",  # Optimized version
            "hunyuan3d_mv": "tencent/hunyuan3d-2mv",  # Multiview support
            
            # Text-to-3D models
            "text_to_3d": "adirik/mvdream",  # Best for text-to-3D
            "mvdream": "adirik/mvdream",
            "shap_e": "cjwbw/shap-e",  # OpenAI's 3D model
            
            # Image-to-3D alternatives
            "wonder3d": "adirik/wonder3d",  # Good mesh generation
            "mesh": "adirik/wonder3d",
            "rodin": "hyper3d/rodin",  # Complex 3D from images (official)
            "imagedream": "adirik/imagedream",  # Multi-view diffusion
            
            # Multiview generation
            "multiview": "jd7h/zero123plusplus",  # Turn image into multiple views
            "zero123": "jd7h/zero123plusplus",
            
            # Texturing
            "texture_3d": "adirik/texture",
            "text2tex": "adirik/text2tex",
            
            # ═══════════════════════════════════════════════════════════════
            # AD & MARKETING SPECIFIC
            # ═══════════════════════════════════════════════════════════════
            "ad_image": "black-forest-labs/flux-1.1-pro",
            "ad_banner": "ideogram-ai/ideogram-v2",  # Good for text overlays
            "product_shot": "black-forest-labs/flux-1.1-pro",
            "product_mockup": "fofr/product-mockup",
            "lifestyle_shot": "black-forest-labs/flux-1.1-pro",
            "ad_video": "kwaivgi/kling-v2.5-turbo-pro",
            "promo_video": "kwaivgi/kling-v1.6-pro",
            "social_content": "black-forest-labs/flux-schnell",
            
            # ═══════════════════════════════════════════════════════════════
            # T-SHIRT & PRINT-ON-DEMAND SPECIFIC
            # ═══════════════════════════════════════════════════════════════
            "tshirt": "recraft-ai/recraft-v3",
            "tshirt_design": "recraft-ai/recraft-v3",
            "print_design": "recraft-ai/recraft-v3",
            "vector_art": "recraft-ai/recraft-v3",
            "logo": "ideogram-ai/ideogram-v2",
            "logo_design": "ideogram-ai/ideogram-v2",
            "sticker": "recraft-ai/recraft-v3",
            "icon": "recraft-ai/recraft-v3",
            "illustration": "recraft-ai/recraft-v3",
            "cartoon": "cagliostrolab/animagine-xl-3.1",
            
            # ═══════════════════════════════════════════════════════════════
            # FACE & PORTRAIT
            # ═══════════════════════════════════════════════════════════════
            "headshot": "tencentarc/photomaker",
            "portrait": "tencentarc/photomaker",
            "photomaker": "tencentarc/photomaker",
            "face_swap": "lucataco/facefusion",
            "face_age": "yuval-alaluf/sam",
            "avatar": "tencentarc/photomaker",
            
            # ═══════════════════════════════════════════════════════════════
            # DOCUMENT & DATA
            # ═══════════════════════════════════════════════════════════════
            "document_qa": "andreasjansson/llava-13b",
            "pdf_extract": "abiruyt/text-extract-ocr",
            "table_extract": "abiruyt/text-extract-ocr",
            "handwriting": "abiruyt/text-extract-ocr",
        }
        
        # Valid Flux aspect ratios
        self.valid_aspect_ratios = [
            "1:1", "16:9", "21:9", "3:2", "2:3", "4:5", "5:4", "3:4", "4:3", "9:16", "9:21"
        ]
    
    def _detect_aspect_ratio_from_text(self, text: str) -> Optional[str]:
        """
        Detect desired aspect ratio from natural language in text.
        
        Returns aspect ratio string or None if not detected.
        """
        text_lower = text.lower()
        
        # Natural language mappings for aspect ratios
        portrait_keywords = [
            "portrait", "tall", "vertical", "portrait dimension", "tall dimension",
            "portrait format", "vertical format", "portrait oriented", "portrait orientation",
            "taller than wide", "tall image", "vertical image", "portrait mode",
            "phone wallpaper", "mobile wallpaper", "story format", "stories format",
            "pinterest", "tiktok", "reels", "instagram story", "9:16"
        ]
        
        landscape_keywords = [
            "landscape", "wide", "horizontal", "landscape dimension", "wide dimension",
            "landscape format", "horizontal format", "landscape oriented", "landscape orientation",
            "wider than tall", "wide image", "horizontal image", "landscape mode",
            "desktop wallpaper", "banner", "youtube thumbnail", "widescreen",
            "cinematic", "movie", "film", "panoramic", "panorama", "ultrawide",
            "16:9", "21:9"
        ]
        
        square_keywords = [
            "square", "1:1", "equal width and height", "square format",
            "square dimension", "square image", "instagram post", "profile picture"
        ]
        
        # Check for portrait/tall
        for kw in portrait_keywords:
            if kw in text_lower:
                logger.info(f"Detected portrait aspect from: '{kw}'")
                return "2:3"  # Standard portrait
        
        # Check for landscape/wide
        for kw in landscape_keywords:
            if kw in text_lower:
                if "cinematic" in text_lower or "widescreen" in text_lower or "movie" in text_lower:
                    logger.info(f"Detected cinematic aspect from: '{kw}'")
                    return "16:9"
                if "ultrawide" in text_lower or "panoramic" in text_lower or "21:9" in text_lower:
                    logger.info(f"Detected ultrawide aspect from: '{kw}'")
                    return "21:9"
                logger.info(f"Detected landscape aspect from: '{kw}'")
                return "3:2"  # Standard landscape
        
        # Check for square
        for kw in square_keywords:
            if kw in text_lower:
                logger.info(f"Detected square aspect from: '{kw}'")
                return "1:1"
        
        return None
    
    def _get_closest_aspect_ratio(self, width: int, height: int) -> str:
        """Convert width/height to closest valid Flux aspect ratio."""
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
    
    async def _get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get model info and schema from Replicate."""
        if model_name in self._model_cache:
            return self._model_cache[model_name]
        
        # Handle shortcuts
        if model_name in self.model_shortcuts:
            model_name = self.model_shortcuts[model_name]
        
        # Parse model name (owner/model or owner/model:version)
        version = None
        if ":" in model_name:
            model_name, version = model_name.split(":", 1)
        
        async with aiohttp.ClientSession() as session:
            # Get model details
            url = f"{self.base_url}/models/{model_name}"
            async with session.get(url, headers=self.headers) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"Model not found: {model_name} - {error}")
                model_data = await response.json()
            
            # Get the latest version if not specified
            if not version:
                version = model_data.get("latest_version", {}).get("id")
            
            # Get version details with input schema
            if version:
                version_url = f"{self.base_url}/models/{model_name}/versions/{version}"
                async with session.get(version_url, headers=self.headers) as response:
                    if response.status == 200:
                        version_data = await response.json()
                        model_data["version_details"] = version_data
                        model_data["input_schema"] = version_data.get("openapi_schema", {}).get(
                            "components", {}
                        ).get("schemas", {}).get("Input", {})
            
            model_data["resolved_version"] = version
            self._model_cache[model_name] = model_data
            return model_data
    
    async def _run_prediction(
        self,
        model: str,
        version: str,
        inputs: Dict[str, Any] = None,
        input: Dict[str, Any] = None,  # Alias for inputs
        wait: bool = True,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """Run a prediction on a model."""
        url = f"{self.base_url}/predictions"
        
        data = {
            "version": version,
            "input": inputs
        }
        
        async with aiohttp.ClientSession() as session:
            # Start prediction
            async with session.post(url, headers=self.headers, json=data) as response:
                if response.status >= 400:
                    error = await response.text()
                    raise Exception(f"Prediction failed: {error}")
                result = await response.json()
            
            if not wait:
                return {
                    "status": "started",
                    "prediction_id": result.get("id"),
                    "urls": result.get("urls", {})
                }
            
            # Poll for completion
            prediction_url = result.get("urls", {}).get("get") or f"{url}/{result['id']}"
            start_time = asyncio.get_event_loop().time()
            
            while result.get("status") in ["starting", "processing"]:
                if asyncio.get_event_loop().time() - start_time > timeout:
                    return {
                        "status": "timeout",
                        "prediction_id": result.get("id"),
                        "message": f"Prediction still running after {timeout}s. Check status with prediction ID."
                    }
                
                await asyncio.sleep(2)
                async with session.get(prediction_url, headers=self.headers) as response:
                    result = await response.json()
            
            if result.get("status") == "failed":
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "logs": result.get("logs", "")
                }
            
            return {
                "success": True,
                "output": result.get("output"),
                "prediction_id": result.get("id"),
                "metrics": result.get("metrics", {})
            }
    
    @tool(
        name="replicate_search_models",
        description="Search Replicate for AI models by keyword, capability, or task description. Use this to find the best model for any AI task.",
        category="ai_models"
    )
    async def search_models(
        self,
        query: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search for models on Replicate.
        
        Args:
            query: Search query (e.g., "image generation", "text to speech", "video")
            limit: Maximum results to return
        """
        try:
            async with aiohttp.ClientSession() as session:
                # Search collections and models
                url = f"{self.base_url}/models"
                
                all_models = []
                query_lower = query.lower()
                cursor = None
                
                # Fetch models (paginated)
                while len(all_models) < limit * 3:  # Get extra to filter
                    params = {"cursor": cursor} if cursor else {}
                    async with session.get(url, headers=self.headers, params=params) as response:
                        if response.status != 200:
                            break
                        data = await response.json()
                    
                    for model in data.get("results", []):
                        # Score relevance (handle None values)
                        name = (model.get("name") or "").lower()
                        desc = (model.get("description") or "").lower()
                        owner = (model.get("owner") or "").lower()
                        
                        score = 0
                        if query_lower in name:
                            score += 10
                        if query_lower in desc:
                            score += 5
                        for word in query_lower.split():
                            if word in name:
                                score += 3
                            if word in desc:
                                score += 1
                        
                        if score > 0:
                            model["relevance_score"] = score
                            all_models.append(model)
                    
                    # Next page
                    next_cursor = data.get("next")
                    if not next_cursor:
                        break
                    # Extract cursor from URL if needed
                    if "cursor=" in str(next_cursor):
                        cursor = next_cursor.split("cursor=")[-1].split("&")[0]
                    else:
                        cursor = next_cursor
                    if not cursor:
                        break
                
                # Sort by relevance and run count
                all_models.sort(key=lambda x: (x.get("relevance_score", 0), x.get("run_count", 0)), reverse=True)
                
                # Format results
                results = []
                for model in all_models[:limit]:
                    model_owner = model.get('owner') or 'unknown'
                    model_name = model.get('name') or 'unknown'
                    results.append({
                        "name": f"{model_owner}/{model_name}",
                        "description": (model.get("description") or "")[:200],
                        "run_count": model.get("run_count", 0),
                        "url": model.get("url"),
                        "cover_image": model.get("cover_image_url")
                    })
                
                return {
                    "success": True,
                    "query": query,
                    "models": results,
                    "total_found": len(results)
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    @tool(
        name="replicate_get_model_info",
        description="Get detailed information about a specific Replicate model including its input parameters and schema. Use this before running a model to understand its capabilities.",
        category="ai_models"
    )
    async def get_model_info(
        self,
        model_name: str
    ) -> Dict[str, Any]:
        """
        Get detailed model information and input schema.
        
        Args:
            model_name: Model identifier (e.g., "stability-ai/sdxl" or shortcut like "image")
        """
        try:
            info = await self._get_model_info(model_name)
            
            # Extract useful input info
            input_schema = info.get("input_schema", {})
            properties = input_schema.get("properties", {})
            required = input_schema.get("required", [])
            
            inputs = []
            for name, details in properties.items():
                inputs.append({
                    "name": name,
                    "type": details.get("type", "string"),
                    "description": details.get("description", ""),
                    "default": details.get("default"),
                    "required": name in required,
                    "enum": details.get("enum")
                })
            
            return {
                "success": True,
                "model": f"{info.get('owner')}/{info.get('name')}",
                "description": info.get("description"),
                "version": info.get("resolved_version"),
                "run_count": info.get("run_count"),
                "inputs": inputs,
                "url": info.get("url"),
                "github_url": info.get("github_url"),
                "paper_url": info.get("paper_url")
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _validate_and_normalize_image_url(self, url: str, model_name: str = None) -> Dict[str, Any]:
        """
        Validate and normalize image URL for AI models.
        
        Some models (like Kling, Luma) require URLs with proper image extensions.
        Printify mockup URLs don't have extensions: https://images.printify.com/HEXID
        
        Args:
            url: The image URL to validate
            model_name: The model that will use this URL (for checking strict requirements)
        
        Returns:
            {"success": bool, "url": str, "normalized": bool, "error": str?}
        """
        if not url:
            return {"success": False, "url": None, "error": "No URL provided"}
        
        # Check if URL already has a valid image extension
        url_lower = url.lower()
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp']
        has_extension = any(ext in url_lower for ext in valid_extensions)
        
        if has_extension:
            return {"success": True, "url": url, "normalized": False}
        
        # Check if this model requires proper URLs
        needs_normalization = False
        if model_name:
            for strict_model in self.STRICT_URL_MODELS:
                if strict_model in model_name:
                    needs_normalization = True
                    break
        
        # Also check known CDN patterns that need normalization
        extensionless_cdns = [
            "images.printify.com",
            "cloudinary.com",
            "imgix.net",
        ]
        for cdn in extensionless_cdns:
            if cdn in url_lower:
                needs_normalization = True
                break
        
        if not needs_normalization:
            return {"success": True, "url": url, "normalized": False}
        
        # URL needs normalization - try to determine content type and download
        logger.info(f"🔄 Normalizing image URL (no extension detected): {url[:60]}...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # HEAD request to get content-type
                async with session.head(url, allow_redirects=True) as response:
                    if response.status != 200:
                        # Try GET if HEAD fails
                        async with session.get(url) as get_response:
                            if get_response.status != 200:
                                return {"success": True, "url": url, "normalized": False, "warning": f"Could not verify URL: HTTP {get_response.status}"}
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
                
                ext = '.jpg'  # Default
                for ct, extension in ext_map.items():
                    if ct in content_type.lower():
                        ext = extension
                        break
                
                # Download the image
                async with session.get(url) as response:
                    if response.status != 200:
                        return {"success": True, "url": url, "normalized": False, "warning": "Download failed"}
                    
                    image_data = await response.read()
                
                # Upload to catbox.moe (free temporary hosting)
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
                            normalized_url = result.strip()
                            logger.info(f"✅ Image URL normalized: {normalized_url}")
                            return {"success": True, "url": normalized_url, "normalized": True}
                
                # Fallback: try appending extension
                extended_url = f"{url}{ext}" if "?" not in url else f"{url}&ext={ext.replace('.', '')}"
                return {"success": True, "url": extended_url, "normalized": True}
                
        except Exception as e:
            logger.warning(f"URL normalization failed: {e}")
            return {"success": True, "url": url, "normalized": False, "warning": str(e)}
    
    @tool(
        name="replicate_run_model",
        description="Run ANY Replicate AI model with specified inputs. Use this to generate images, audio, video, text, 3D models, or any other AI task. First use replicate_get_model_info to understand required inputs.",
        category="ai_models"
    )
    async def run_model(
        self,
        model_name: str = None,
        model: str = None,  # Alias for model_name
        inputs: Dict[str, Any] = None,
        input: Dict[str, Any] = None,  # Alias for inputs
        wait: bool = True
    ) -> Dict[str, Any]:
        """
        Run any Replicate model.
        
        Args:
            model_name: Model identifier or shortcut
            inputs: Model inputs (varies by model)
            wait: Whether to wait for completion
        """
        try:
            # Resolve aliases
            model_name = model_name or model
            inputs = inputs or input or {}
            if not model_name:
                return {"success": False, "error": "Must provide model_name or model parameter"}
            
            # Resolve model name
            if model_name in self.model_shortcuts:
                model_name = self.model_shortcuts[model_name]
            
            # Get model info and version
            info = await self._get_model_info(model_name)
            version = info.get("resolved_version")
            
            if not version:
                return {
                    "success": False,
                    "error": f"Could not find version for model: {model_name}"
                }
            
            # Run the model
            result = await self._run_prediction(
                model=model_name,
                version=version,
                inputs=inputs,
                wait=wait
            )
            
            result["model"] = model_name
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _detect_content_type_and_model(self, description: str, style: Optional[str] = None, quality: str = "balanced") -> tuple:
        """
        Intelligently detect content type and select optimal model based on user request.
        
        Returns:
            tuple: (content_type, model_name, special_inputs)
        """
        desc_lower = description.lower()
        special_inputs = {}
        
        # ═══════════════════════════════════════════════════════════════
        # MARKETING & ADS DETECTION
        # ═══════════════════════════════════════════════════════════════
        marketing_keywords = ["ad", "advertisement", "banner", "promo", "marketing", "campaign", "social media post", "instagram", "facebook ad", "sponsored"]
        if any(kw in desc_lower for kw in marketing_keywords):
            if "banner" in desc_lower or "display ad" in desc_lower:
                return ("image", "ideogram-ai/ideogram-v2", {"aspect_ratio": "16:9"})  # Good for text overlays
            elif "video" in desc_lower or "reel" in desc_lower or "tiktok" in desc_lower:
                return ("video", "minimax/video-01", {})
            else:
                return ("image", "black-forest-labs/flux-1.1-pro", {})
        
        # ═══════════════════════════════════════════════════════════════
        # PRODUCT & E-COMMERCE DETECTION
        # ═══════════════════════════════════════════════════════════════
        product_keywords = ["product shot", "product photo", "mockup", "lifestyle shot", "e-commerce", "catalog", "product image"]
        if any(kw in desc_lower for kw in product_keywords):
            if "mockup" in desc_lower:
                return ("image", "fofr/product-mockup", {})
            else:
                return ("image", "black-forest-labs/flux-1.1-pro", {})
        
        # ═══════════════════════════════════════════════════════════════
        # PRINT-ON-DEMAND / T-SHIRT DETECTION
        # ═══════════════════════════════════════════════════════════════
        pod_keywords = ["t-shirt", "tshirt", "shirt design", "print design", "sticker", "mug design", "poster", "vector", "illustration", "clipart"]
        if any(kw in desc_lower for kw in pod_keywords):
            # Use valid Recraft style (digital_illustration/2d_art_poster for vector/illustration)
            return ("image", "recraft-ai/recraft-v3", {"style": "digital_illustration/2d_art_poster"})
        
        # ═══════════════════════════════════════════════════════════════
        # LOGO & BRANDING DETECTION
        # ═══════════════════════════════════════════════════════════════
        logo_keywords = ["logo", "brand", "icon", "emblem", "badge", "wordmark", "lettermark"]
        if any(kw in desc_lower for kw in logo_keywords):
            return ("image", "ideogram-ai/ideogram-v2", {"style": "design"})  # Best for text in images
        
        # ═══════════════════════════════════════════════════════════════
        # IMAGE EDITING DETECTION
        # ═══════════════════════════════════════════════════════════════
        if any(kw in desc_lower for kw in ["remove background", "remove bg", "transparent background", "cut out"]):
            return ("image_edit", "cjwbw/rembg", {})
        if any(kw in desc_lower for kw in ["upscale", "enhance resolution", "increase resolution", "higher resolution"]):
            return ("image_edit", "nightmareai/real-esrgan", {})
        if any(kw in desc_lower for kw in ["restore face", "fix face", "enhance face", "face restoration"]):
            return ("image_edit", "tencentarc/gfpgan", {})
        if any(kw in desc_lower for kw in ["colorize", "add color", "black and white to color"]):
            return ("image_edit", "arielreplicate/deoldify_image", {})
        if any(kw in desc_lower for kw in ["style transfer", "apply style", "in the style of"]):
            return ("image_edit", "lucataco/neural-style-tf", {})
        if any(kw in desc_lower for kw in ["inpaint", "fill in", "remove object", "edit part"]):
            return ("image_edit", "stability-ai/stable-diffusion-inpainting", {})
        
        # ═══════════════════════════════════════════════════════════════
        # VIDEO EDITING DETECTION
        # ═══════════════════════════════════════════════════════════════
        if any(kw in desc_lower for kw in ["lip sync", "talking head", "face animation", "audio to video"]):
            return ("video_edit", "chenxwh/video-retalking", {})
        if any(kw in desc_lower for kw in ["video upscale", "enhance video", "video quality"]):
            return ("video_edit", "lucataco/real-esrgan-video", {})
        if any(kw in desc_lower for kw in ["slow motion", "slowmo", "slow-mo", "frame interpolation"]):
            return ("video_edit", "pollinations/video-frame-interpolation", {})
        if any(kw in desc_lower for kw in ["video background", "remove video bg", "green screen"]):
            return ("video_edit", "arielreplicate/robust_video_matting", {})
        
        # ═══════════════════════════════════════════════════════════════
        # VIDEO GENERATION DETECTION
        # ═══════════════════════════════════════════════════════════════
        video_keywords = ["video", "animate", "motion", "clip", "movie", "film", "footage", "reel"]
        if any(kw in desc_lower for kw in video_keywords):
            models = {
                "fast": "kwaivgi/kling-v1.6-pro",
                "balanced": "kwaivgi/kling-v1.6-pro",
                "best": "minimax/video-01"
            }
            return ("video", models.get(quality, "kwaivgi/kling-v1.6-pro"), {})
        
        # ═══════════════════════════════════════════════════════════════
        # 3D GENERATION DETECTION - Updated Feb 2026
        # ═══════════════════════════════════════════════════════════════
        threed_keywords = ["3d", "mesh", "sculpture", "3d model", "avatar", "character model", "asset", "3d object", "3d render"]
        if any(kw in desc_lower for kw in threed_keywords):
            # Note: Most 3D models work best with an input IMAGE
            # For text-to-3D, we use mvdream or shap-e
            # For image-to-3D, trellis is best
            if "text" in desc_lower or "from description" in desc_lower or "from prompt" in desc_lower:
                # Text-to-3D path
                models = {
                    "fast": "cjwbw/shap-e",
                    "balanced": "adirik/mvdream",
                    "best": "adirik/mvdream"
                }
                return ("3d", models.get(quality, "adirik/mvdream"), {"text_to_3d": True})
            else:
                # Image-to-3D path (default, more reliable)
                models = {
                    "fast": "firtoz/trellis",
                    "balanced": "firtoz/trellis",
                    "best": "hyper3d/rodin"
                }
                return ("3d", models.get(quality, "firtoz/trellis"), {})
        
        # ═══════════════════════════════════════════════════════════════
        # AUDIO & MUSIC DETECTION
        # ═══════════════════════════════════════════════════════════════
        if any(kw in desc_lower for kw in ["transcribe", "speech to text", "audio to text"]):
            return ("audio", "openai/whisper", {})
        if any(kw in desc_lower for kw in ["voice clone", "clone voice", "copy voice"]):
            return ("audio", "lucataco/xtts-v2", {})
        if any(kw in desc_lower for kw in ["text to speech", "tts", "speak", "narrate", "voiceover"]):
            return ("audio", "cjwbw/bark", {})
        if any(kw in desc_lower for kw in ["sound effect", "sfx", "ambience", "ambient sound"]):
            return ("audio", "haoheliu/audio-ldm-2", {})
        audio_keywords = ["music", "song", "audio", "sound", "melody", "beat", "instrumental"]
        if any(kw in desc_lower for kw in audio_keywords):
            return ("audio", "meta/musicgen", {})
        
        # ═══════════════════════════════════════════════════════════════
        # CODE GENERATION DETECTION
        # ═══════════════════════════════════════════════════════════════
        code_keywords = ["code", "programming", "script", "function", "algorithm", "python", "javascript", "program"]
        if any(kw in desc_lower for kw in code_keywords):
            if "sql" in desc_lower or "database" in desc_lower or "query" in desc_lower:
                return ("code", "defog/sqlcoder-7b-2", {})
            if "python" in desc_lower:
                return ("code", "meta/codellama-34b-python", {})
            return ("code", "meta/codellama-34b-instruct", {})
        
        # ═══════════════════════════════════════════════════════════════
        # TEXT GENERATION DETECTION
        # ═══════════════════════════════════════════════════════════════
        text_keywords = ["write", "story", "article", "blog", "essay", "summarize", "translate", "explain"]
        if any(kw in desc_lower for kw in text_keywords):
            models = {
                "fast": "meta/llama-2-13b-chat",
                "balanced": "meta/meta-llama-3-70b-instruct",
                "best": "meta/meta-llama-3-70b-instruct"
            }
            return ("text", models.get(quality, "meta/meta-llama-3-70b-instruct"), {})
        
        # ═══════════════════════════════════════════════════════════════
        # IMAGE STYLE DETECTION
        # ═══════════════════════════════════════════════════════════════
        if any(kw in desc_lower for kw in ["anime", "manga", "cartoon", "animated"]):
            return ("image", "cagliostrolab/animagine-xl-3.1", {})
        if any(kw in desc_lower for kw in ["realistic", "photorealistic", "photo realistic", "photograph"]):
            return ("image", "adirik/realvisxl-v4.0", {})
        if any(kw in desc_lower for kw in ["artistic", "art", "painting", "fine art"]):
            return ("image", "stability-ai/sdxl", {})
        if any(kw in desc_lower for kw in ["portrait", "headshot", "face"]):
            return ("image", "tencentarc/photomaker", {})
        
        # ═══════════════════════════════════════════════════════════════
        # VISION / IMAGE UNDERSTANDING DETECTION
        # ═══════════════════════════════════════════════════════════════
        if any(kw in desc_lower for kw in ["describe image", "what is in", "analyze image", "caption"]):
            return ("vision", "yorickvp/llava-13b", {})
        if any(kw in desc_lower for kw in ["ocr", "extract text", "read text", "text from image"]):
            return ("vision", "abiruyt/text-extract-ocr", {})
        
        # ═══════════════════════════════════════════════════════════════
        # DEFAULT: IMAGE GENERATION
        # ═══════════════════════════════════════════════════════════════
        models = {
            "fast": "black-forest-labs/flux-schnell",
            "balanced": "black-forest-labs/flux-schnell",
            "best": "black-forest-labs/flux-1.1-pro"
        }
        return ("image", models.get(quality, "black-forest-labs/flux-schnell"), {})

    @tool(
        name="replicate_smart_generate",
        description="Intelligently generate content using the best available model. Describe what you want and the system will select and configure the optimal model automatically. Supports: images, videos, audio, music, 3D, code, text, marketing content, product shots, t-shirt designs, logos, image editing (upscale, remove bg, colorize), video editing (lip sync, slow motion), and more.",
        category="ai_models"
    )
    async def smart_generate(
        self,
        description: str,
        content_type: str = "auto",
        style: Optional[str] = None,
        quality: str = "balanced",
        duration: Optional[int] = None,
        image_url: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Smart content generation - automatically selects best model based on your description.
        
        Args:
            description: What to generate (detailed description) - be specific about what you want
            content_type: Type of content (image, video, audio, 3d, text, code, auto) - defaults to auto-detect
            style: Optional style hints (e.g., "realistic", "cartoon", "vector")
            quality: Quality preset (fast, balanced, best) - affects model selection and output quality
            duration: Duration in seconds (for video/audio)
            image_url: Input image URL (for image-to-video, upscaling, editing, etc.)
            width: Output width (for images/video)
            height: Output height (for images/video)
        
        Automatically detects and routes to optimal models for:
        - Marketing & Ads: banners, social posts, promotional content
        - Product shots: e-commerce, catalog, mockups
        - Print-on-demand: t-shirt designs, stickers, posters, vectors
        - Logos & branding: icons, wordmarks, emblems
        - Image editing: upscale, remove background, colorize, style transfer
        - Video editing: lip sync, slow motion, upscale
        - Video generation: animated content, clips, reels
        - 3D generation: models, avatars, meshes
        - Audio: music, voice, sound effects, transcription
        - Code: Python, SQL, general programming
        - Text: articles, stories, summaries
        """
        # Use smart detection if auto
        if content_type == "auto":
            content_type, selected_model, special_inputs = self._detect_content_type_and_model(description, style, quality)
            logger.info(f"Smart detection: type={content_type}, model={selected_model}")
        else:
            # Manual content type - use default model map
            special_inputs = {}
            model_map = {
                "image": {
                    "fast": "black-forest-labs/flux-schnell",
                    "balanced": "black-forest-labs/flux-schnell",
                    "best": "black-forest-labs/flux-1.1-pro"
                },
                "video": {
                    "fast": "kwaivgi/kling-v1.6-pro",
                    "balanced": "kwaivgi/kling-v1.6-pro",
                    "best": "minimax/video-01"
                },
                "audio": {
                    "fast": "meta/musicgen",
                    "balanced": "meta/musicgen",
                    "best": "meta/musicgen"
                },
                "3d": {
                    "fast": "firtoz/trellis",
                    "balanced": "firtoz/trellis",
                    "best": "hyper3d/rodin"
                },
                "text": {
                    "fast": "meta/llama-2-13b-chat",
                    "balanced": "meta/meta-llama-3-70b-instruct",
                    "best": "meta/meta-llama-3-70b-instruct"
                },
                "code": {
                    "fast": "meta/codellama-34b-instruct",
                    "balanced": "meta/codellama-34b-instruct",
                    "best": "meta/codellama-34b-instruct"
                }
            }
            selected_model = model_map.get(content_type, model_map["image"]).get(quality, "balanced")
        
        # Merge any special inputs from detection
        inputs = {**special_inputs}
        
        # Build inputs based on content type
        if content_type == "image":
            prompt = description
            if style:
                prompt = f"{description}, {style} style"
            inputs["prompt"] = prompt
            inputs["num_outputs"] = 1
            
            # Smart aspect ratio detection
            if "flux" in selected_model.lower():
                # Detect aspect ratio from natural language in description
                detected_ratio = self._detect_aspect_ratio_from_text(description)
                
                # Priority: explicit width/height > detected from text > default
                if width and height:
                    # Convert to closest valid Flux aspect ratio
                    inputs["aspect_ratio"] = self._get_closest_aspect_ratio(width, height)
                    logger.info(f"Using width/height {width}x{height} → {inputs['aspect_ratio']}")
                elif detected_ratio:
                    inputs["aspect_ratio"] = detected_ratio
                    logger.info(f"Detected aspect ratio from prompt: {detected_ratio}")
                else:
                    inputs.setdefault("aspect_ratio", "1:1")
                    
            elif "recraft" in selected_model.lower():
                # Validate and fix Recraft style - Recraft requires specific style formats
                valid_recraft_styles = [
                    "any", "realistic_image", "digital_illustration",
                    "digital_illustration/pixel_art", "digital_illustration/hand_drawn",
                    "digital_illustration/grain", "digital_illustration/infantile_sketch",
                    "digital_illustration/2d_art_poster", "digital_illustration/handmade_3d",
                    "digital_illustration/hand_drawn_outline", "digital_illustration/engraving_color",
                    "digital_illustration/2d_art_poster_2", "vector_illustration"
                ]
                # Map common user styles to valid Recraft styles
                recraft_style_map = {
                    "vector": "digital_illustration/2d_art_poster",
                    "vector_illustration": "digital_illustration/2d_art_poster",
                    "illustration": "digital_illustration",
                    "cartoon": "digital_illustration/infantile_sketch",
                    "realistic": "realistic_image",
                    "minimal": "digital_illustration/2d_art_poster",
                    "cute": "digital_illustration/infantile_sketch",
                    "kawaii": "digital_illustration/infantile_sketch",
                    "hand_drawn": "digital_illustration/hand_drawn",
                    "pixel": "digital_illustration/pixel_art",
                    "3d": "digital_illustration/handmade_3d",
                }
                current_style = inputs.get("style", "")
                if current_style and current_style not in valid_recraft_styles:
                    # Try to map to valid style
                    mapped = recraft_style_map.get(current_style.lower(), "digital_illustration/2d_art_poster")
                    logger.info(f"Mapping invalid Recraft style '{current_style}' → '{mapped}'")
                    inputs["style"] = mapped
                elif not current_style:
                    inputs["style"] = "digital_illustration/2d_art_poster"  # Default
                    
            elif width and height:
                inputs["width"] = width
                inputs["height"] = height
        
        elif content_type == "image_edit":
            # Image editing operations - require input image
            if not image_url:
                return {
                    "success": False,
                    "error": "Image editing requires an image_url parameter with the image to edit"
                }
            inputs["image"] = image_url
            if "rembg" in selected_model:
                pass  # Just needs image
            elif "real-esrgan" in selected_model:
                inputs["scale"] = 4
            elif "gfpgan" in selected_model:
                pass  # Just needs image
            elif "neural-style" in selected_model and style:
                inputs["style_image"] = style  # Style image URL
        
        elif content_type == "video_edit":
            # Video editing operations
            if not image_url:  # video_url passed as image_url
                return {
                    "success": False,
                    "error": "Video editing requires the video URL passed as image_url parameter"
                }
            inputs["video"] = image_url
        
        elif content_type == "video":
            inputs = {
                "prompt": description
            }
            # Add image_url for image-to-video (with URL validation)
            if image_url:
                # Validate and normalize URL for strict models (Kling, Luma, etc.)
                url_result = await self._validate_and_normalize_image_url(image_url, selected_model)
                if url_result.get("success"):
                    normalized_url = url_result.get("url", image_url)
                    if url_result.get("normalized"):
                        logger.info(f"🔄 Image URL normalized for video model: {normalized_url[:60]}...")
                    inputs["image"] = normalized_url
                else:
                    # Still try with original URL
                    logger.warning(f"URL validation issue: {url_result.get('error')} - proceeding with original")
                    inputs["image"] = image_url
            # Set duration if provided - constrain to valid values (5 or 10 seconds)
            if duration:
                # Parse duration if it's a string (e.g., "15 seconds" -> 15)
                if isinstance(duration, str):
                    # Extract number from string like "15 seconds" or "15s"
                    import re
                    match = re.search(r'(\d+)', duration)
                    if match:
                        duration = int(match.group(1))
                    else:
                        duration = 10  # Default if can't parse
                
                # Ensure duration is an integer
                duration = int(duration) if not isinstance(duration, int) else duration
                
                # Most video models only support 5 or 10 second durations
                if duration <= 7:
                    duration = 5
                else:
                    duration = 10
                logger.info(f"Video duration constrained to {duration} seconds")
                inputs["duration"] = duration
            else:
                inputs["num_frames"] = 24
        
        elif content_type == "audio":
            inputs = {
                "prompt": description
            }
            # Set duration if provided
            if duration:
                # Parse duration if it's a string
                if isinstance(duration, str):
                    import re
                    match = re.search(r'(\d+)', duration)
                    if match:
                        duration = int(match.group(1))
                    else:
                        duration = 8
                inputs["duration"] = int(duration)
            else:
                inputs["duration"] = 8
        
        elif content_type == "3d":
            inputs["prompt"] = description
            if image_url:
                inputs["image"] = image_url  # For image-to-3d
        
        elif content_type == "text":
            inputs["prompt"] = description
            inputs["max_new_tokens"] = 1024
        
        elif content_type == "code":
            inputs["prompt"] = f"Write code for: {description}"
            inputs["max_new_tokens"] = 2048
        
        elif content_type == "vision":
            if not image_url:
                return {
                    "success": False,
                    "error": "Vision/image analysis requires an image_url parameter"
                }
            inputs["image"] = image_url
            inputs["prompt"] = description
        
        else:
            inputs["prompt"] = description
        
        # Run the model
        try:
            info = await self._get_model_info(selected_model)
            version = info.get("resolved_version")
            
            result = await self._run_prediction(
                model=selected_model,
                version=version,
                inputs=inputs,
                wait=True
            )
            
            result["model_used"] = selected_model
            result["content_type"] = content_type
            result["quality_preset"] = quality
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "attempted_model": selected_model
            }
    
    @tool(
        name="replicate_create_3d_model",
        description="""Create a 3D model from text description or image. 
        
IMPORTANT: For best results, provide an IMAGE URL. Most 3D models work by converting images to 3D.
If you only have a text description, the system will first generate an image, then convert to 3D.

Models available:
- trellis (default): Best image-to-3D, fast <1 min, high quality
- mvdream: Best for text-to-3D generation
- rodin: Complex detailed 3D from images (official)
- wonder3d: Good mesh generation from images
- hunyuan3d: Tencent's 3D model
- shap_e: OpenAI's text-to-3D

Output: Returns .glb or .obj 3D model file.""",
        category="ai_generation"
    )
    async def create_3d_model(
        self,
        description: str,
        image_url: Optional[str] = None,
        model: str = "auto",
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a 3D model from text or image.
        
        Args:
            description: What 3D object to create (e.g., "a red sports car", "medieval castle")
            image_url: Optional input image URL - HIGHLY RECOMMENDED for best results
            model: Model to use: auto, trellis, mvdream, rodin, wonder3d, hunyuan3d, shap_e
            seed: Random seed for reproducibility
        
        Returns:
            Dict with 3D model URL (.glb or .obj format)
        """
        # Model mapping
        model_map = {
            "trellis": "firtoz/trellis",
            "mvdream": "adirik/mvdream",
            "rodin": "hyper3d/rodin",
            "wonder3d": "adirik/wonder3d",
            "hunyuan3d": "prunaai/hunyuan3d-2",
            "shap_e": "cjwbw/shap-e",
            "imagedream": "adirik/imagedream",
        }
        
        # Auto-select model based on input
        if model == "auto":
            if image_url:
                # Image-to-3D: trellis is fastest and best
                selected_model = "firtoz/trellis"
            else:
                # Text-to-3D: mvdream is best
                selected_model = "adirik/mvdream"
        else:
            selected_model = model_map.get(model.lower(), "firtoz/trellis")
        
        logger.info(f"3D generation: model={selected_model}, has_image={bool(image_url)}")
        
        # Build inputs based on model
        inputs = {}
        
        # If no image provided and model needs one, generate one first
        if not image_url and selected_model in ["firtoz/trellis", "hyper3d/rodin", "adirik/wonder3d", "adirik/imagedream"]:
            logger.info("No image provided - generating reference image first...")
            
            # Generate an image from the description
            image_result = await self.smart_generate(
                description=f"Single object on white background, centered, {description}, product photo style, clean isolated object",
                content_type="image",
                quality="balanced"
            )
            
            if not image_result.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to generate reference image: {image_result.get('error', 'Unknown error')}",
                    "tip": "Try providing an image_url directly for better results"
                }
            
            # Get the image URL from result
            output = image_result.get("output")
            if isinstance(output, list) and output:
                image_url = output[0]
            elif isinstance(output, str):
                image_url = output
            else:
                return {
                    "success": False,
                    "error": "Generated image but couldn't extract URL",
                    "result": image_result
                }
            
            logger.info(f"Generated reference image: {image_url}")
        
        # Configure inputs based on model
        if selected_model == "firtoz/trellis":
            inputs["image"] = image_url
            if seed is not None:
                inputs["seed"] = seed
        
        elif selected_model == "adirik/mvdream":
            inputs["prompt"] = description
            inputs["negative_prompt"] = "blurry, low quality, distorted"
            if seed is not None:
                inputs["seed"] = seed
        
        elif selected_model == "hyper3d/rodin":
            inputs["image"] = image_url
            if description:
                inputs["prompt"] = description
            if seed is not None:
                inputs["seed"] = seed
        
        elif selected_model == "adirik/wonder3d":
            inputs["image"] = image_url
            if seed is not None:
                inputs["seed"] = seed
        
        elif selected_model == "prunaai/hunyuan3d-2":
            if image_url:
                inputs["image"] = image_url
            inputs["prompt"] = description
            if seed is not None:
                inputs["seed"] = seed
        
        elif selected_model == "cjwbw/shap-e":
            inputs["prompt"] = description
            if seed is not None:
                inputs["seed"] = seed
        
        elif selected_model == "adirik/imagedream":
            inputs["image"] = image_url
            inputs["prompt"] = description
            if seed is not None:
                inputs["seed"] = seed
        
        # Get model info and run
        try:
            info = await self._get_model_info(selected_model)
            version = info.get("resolved_version")
            
            result = await self._run_prediction(
                model=selected_model,
                version=version,
                inputs=inputs,
                wait=True
            )
            
            result["model_used"] = selected_model
            result["content_type"] = "3d"
            if image_url and "firtoz/trellis" in selected_model:
                result["reference_image"] = image_url
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "attempted_model": selected_model,
                "tip": "Try a different model or provide an input image URL"
            }
    
    @tool(
        name="replicate_list_collections",
        description="List curated collections of models on Replicate (e.g., text-to-image, audio-generation, etc.)",
        category="ai_models"
    )
    async def list_collections(self) -> Dict[str, Any]:
        """List available model collections."""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/collections"
            async with session.get(url, headers=self.headers) as response:
                if response.status != 200:
                    error = await response.text()
                    return {"success": False, "error": error}
                data = await response.json()
            
            collections = []
            for coll in data.get("results", []):
                collections.append({
                    "slug": coll.get("slug"),
                    "name": coll.get("name"),
                    "description": coll.get("description")
                })
            
            return {
                "success": True,
                "collections": collections
            }
    
    @tool(
        name="replicate_get_collection",
        description="Get models in a specific Replicate collection",
        category="ai_models"
    )
    async def get_collection(self, slug: str) -> Dict[str, Any]:
        """
        Get models in a collection.
        
        Args:
            slug: Collection slug (e.g., "text-to-image", "audio-generation")
        """
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/collections/{slug}"
            async with session.get(url, headers=self.headers) as response:
                if response.status != 200:
                    error = await response.text()
                    return {"success": False, "error": error}
                data = await response.json()
            
            models = []
            for model in data.get("models", []):
                models.append({
                    "name": f"{model.get('owner')}/{model.get('name')}",
                    "description": model.get("description", "")[:150],
                    "run_count": model.get("run_count", 0)
                })
            
            return {
                "success": True,
                "collection": data.get("name"),
                "description": data.get("description"),
                "models": models
            }
    
    @tool(
        name="replicate_list_shortcuts",
        description="List all available model shortcuts organized by category. Shows quick-access names for common AI tasks.",
        category="ai_models"
    )
    async def list_shortcuts(self, category: str = None) -> Dict[str, Any]:
        """
        List all available model shortcuts organized by category.
        
        Args:
            category: Filter by category (image, video, audio, code, 3d, text, ad, tshirt, face, vision, edit)
        """
        # Organize shortcuts by category
        categories = {
            "image_generation": [
                "image", "image_fast", "image_pro", "image_quality", "flux", "flux_pro",
                "sdxl", "sd3", "ideogram", "ideogram_text", "recraft", "recraft_vector",
                "midjourney", "realistic", "photorealistic", "anime", "artistic"
            ],
            "image_editing": [
                "remove_bg", "background_remove", "upscale", "upscale_4x", "upscale_face",
                "restore_face", "face_restore", "inpaint", "edit_image", "img2img",
                "colorize", "outpaint", "style_transfer", "sketch_to_image",
                "depth_to_image", "pose_to_image"
            ],
            "video": [
                "video", "video_fast", "video_pro", "text_to_video", "image_to_video",
                "animate", "animate_image", "luma", "luma_video", "kling", "kling_pro",
                "minimax", "video_edit", "lip_sync", "video_upscale", "slow_motion",
                "remove_bg_video"
            ],
            "audio": [
                "music", "music_gen", "music_melody", "speech_to_text", "transcribe",
                "whisper", "tts", "text_to_speech", "bark", "voice_clone", "clone_voice",
                "audio_enhance", "audio_separate", "sound_effects", "audio_ldm"
            ],
            "code": [
                "code", "codellama", "code_gen", "code_completion", "code_python",
                "code_review", "code_explain", "sql", "sql_gen"
            ],
            "language_models": [
                "llm", "llama", "llama3", "mistral", "mixtral", "summarize",
                "translate", "chat"
            ],
            "vision": [
                "vision", "llava", "image_caption", "blip", "describe_image",
                "ocr", "text_extract", "nsfw_detect", "face_detect", "object_detect"
            ],
            "3d_generation": [
                "3d", "3d_gen", "text_to_3d", "image_to_3d", "mesh", "wonder3d",
                "3d_avatar", "triposr"
            ],
            "advertising": [
                "ad_image", "ad_banner", "product_shot", "product_mockup",
                "lifestyle_shot", "ad_video", "promo_video", "social_content"
            ],
            "print_design": [
                "tshirt", "tshirt_design", "print_design", "vector_art", "logo",
                "logo_design", "sticker", "icon", "illustration", "cartoon"
            ],
            "face_portrait": [
                "headshot", "portrait", "photomaker", "face_swap", "face_age", "avatar"
            ],
            "document": [
                "document_qa", "pdf_extract", "table_extract", "handwriting"
            ]
        }
        
        if category:
            category_lower = category.lower().replace(" ", "_").replace("-", "_")
            # Find matching category
            matching_cats = {k: v for k, v in categories.items() if category_lower in k}
            if not matching_cats:
                # Try to find shortcuts containing the category term
                matching_shortcuts = {
                    k: [s for s in v if category_lower in s]
                    for k, v in categories.items()
                }
                matching_shortcuts = {k: v for k, v in matching_shortcuts.items() if v}
                if matching_shortcuts:
                    matching_cats = matching_shortcuts
            
            if matching_cats:
                result = {}
                for cat_name, shortcuts in matching_cats.items():
                    result[cat_name] = {
                        s: self.model_shortcuts.get(s, "unknown")
                        for s in shortcuts if s in self.model_shortcuts
                    }
                return {
                    "success": True,
                    "category_filter": category,
                    "shortcuts": result
                }
            else:
                return {
                    "success": False,
                    "error": f"Category '{category}' not found",
                    "available_categories": list(categories.keys())
                }
        
        # Return all shortcuts organized by category
        result = {}
        for cat_name, shortcuts in categories.items():
            result[cat_name] = {
                s: self.model_shortcuts.get(s, "unknown")
                for s in shortcuts if s in self.model_shortcuts
            }
        
        return {
            "success": True,
            "total_shortcuts": len(self.model_shortcuts),
            "categories": list(categories.keys()),
            "shortcuts_by_category": result,
            "usage": "Use any shortcut name with replicate_run_model or replicate_smart_generate"
        }

    # ═══════════════════════════════════════════════════════════════
    # SPECIALIZED CONVENIENCE TOOLS
    # ═══════════════════════════════════════════════════════════════
    
    @tool(
        name="replicate_create_ad",
        description="Create marketing/advertising images. Optimized for ads, banners, social media posts, and promotional content.",
        category="ai_models"
    )
    async def create_ad(
        self,
        description: str,
        ad_type: str = "social",
        include_text: Optional[str] = None,
        style: str = "professional"
    ) -> Dict[str, Any]:
        """
        Create advertising/marketing images.
        
        Args:
            description: What the ad should show/promote
            ad_type: Type of ad (social, banner, display, story)
            include_text: Text to include in the ad (uses Ideogram for text rendering)
            style: Style (professional, bold, minimal, vibrant, luxury)
        """
        # Select model based on whether text is needed
        if include_text:
            model = "ideogram-ai/ideogram-v2"  # Best for text in images
            prompt = f"{description}. Include text: '{include_text}'. Style: {style}, advertising, marketing, professional"
        else:
            model = "black-forest-labs/flux-1.1-pro"
            prompt = f"{description}. Style: {style}, advertising, marketing, professional, high quality"
        
        # Set aspect ratio based on ad type
        aspect_ratios = {
            "social": "1:1",
            "banner": "16:9",
            "display": "300:250",
            "story": "9:16",
            "wide": "21:9"
        }
        aspect = aspect_ratios.get(ad_type, "1:1")
        
        inputs = {
            "prompt": prompt,
            "aspect_ratio": aspect
        }
        
        try:
            info = await self._get_model_info(model)
            version = info.get("resolved_version")
            
            result = await self._run_prediction(
                model=model,
                version=version,
                inputs=inputs,
                wait=True
            )
            
            result["ad_type"] = ad_type
            result["model_used"] = model
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="replicate_edit_image",
        description="Edit an existing image: remove background, upscale, restore faces, colorize, or apply style transfer.",
        category="ai_models"
    )
    async def edit_image(
        self,
        image_url: str,
        operation: str,
        style_image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Edit an existing image.
        
        Args:
            image_url: URL of the image to edit
            operation: What to do (remove_bg, upscale, restore_face, colorize, style_transfer)
            style_image_url: For style transfer, the URL of the style reference image
        """
        operation_models = {
            "remove_bg": ("cjwbw/rembg", {"image": image_url}),
            "upscale": ("nightmareai/real-esrgan", {"image": image_url, "scale": 4}),
            "upscale_2x": ("nightmareai/real-esrgan", {"image": image_url, "scale": 2}),
            "restore_face": ("tencentarc/gfpgan", {"img": image_url}),
            "colorize": ("arielreplicate/deoldify_image", {"input_image": image_url}),
            "style_transfer": ("lucataco/neural-style-tf", {"content": image_url, "style": style_image_url or ""})
        }
        
        if operation not in operation_models:
            return {
                "success": False,
                "error": f"Unknown operation: {operation}",
                "available_operations": list(operation_models.keys())
            }
        
        if operation == "style_transfer" and not style_image_url:
            return {
                "success": False,
                "error": "style_transfer requires a style_image_url parameter"
            }
        
        model, inputs = operation_models[operation]
        
        try:
            info = await self._get_model_info(model)
            version = info.get("resolved_version")
            
            result = await self._run_prediction(
                model=model,
                version=version,
                inputs=inputs,
                wait=True
            )
            
            result["operation"] = operation
            result["model_used"] = model
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="replicate_create_product_design",
        description="Create designs for print-on-demand products: t-shirts, mugs, stickers, posters. Uses vector-optimized models.",
        category="ai_models"
    )
    async def create_product_design(
        self,
        description: str,
        product_type: str = "tshirt",
        style: str = "vector",
        transparent_bg: bool = True
    ) -> Dict[str, Any]:
        """
        Create designs optimized for print-on-demand products.
        
        Args:
            description: What the design should show
            product_type: Type of product (tshirt, mug, sticker, poster, hoodie)
            style: Design style (vector, illustration, cartoon, realistic, minimal)
            transparent_bg: Whether to remove background (recommended for POD)
        """
        # Build optimized prompt for POD
        style_hints = {
            "vector": "vector art, clean lines, solid colors, print-ready",
            "illustration": "digital illustration, detailed, artistic",
            "cartoon": "cartoon style, fun, colorful",
            "realistic": "realistic art, detailed, high quality",
            "minimal": "minimalist design, simple, clean"
        }
        
        prompt = f"{description}. Style: {style_hints.get(style, style)}, suitable for {product_type} printing"
        if transparent_bg:
            prompt += ", on transparent background, isolated design"
        
        # Map user-friendly styles to valid Recraft API styles
        # Valid Recraft styles: any, realistic_image, digital_illustration, 
        # digital_illustration/pixel_art, digital_illustration/hand_drawn, 
        # digital_illustration/grain, digital_illustration/infantile_sketch,
        # digital_illustration/2d_art_poster, digital_illustration/handmade_3d,
        # digital_illustration/hand_drawn_outline, digital_illustration/engraving_color,
        # digital_illustration/2d_art_poster_2
        recraft_style_map = {
            "vector": "digital_illustration/2d_art_poster",
            "illustration": "digital_illustration",
            "cartoon": "digital_illustration/infantile_sketch",
            "realistic": "realistic_image",
            "minimal": "digital_illustration/2d_art_poster",
            "cute": "digital_illustration/infantile_sketch",
            "kawaii": "digital_illustration/infantile_sketch",
            "hand_drawn": "digital_illustration/hand_drawn",
            "pixel": "digital_illustration/pixel_art",
            "3d": "digital_illustration/handmade_3d",
        }
        recraft_style = recraft_style_map.get(style.lower(), "digital_illustration/2d_art_poster")
        
        # Use Recraft for vector/illustration, Ideogram for text-heavy designs
        model = "recraft-ai/recraft-v3"
        inputs = {
            "prompt": prompt,
            "style": recraft_style
        }
        
        try:
            info = await self._get_model_info(model)
            version = info.get("resolved_version")
            
            result = await self._run_prediction(
                model=model,
                version=version,
                inputs=inputs,
                wait=True
            )
            
            # If transparent background requested and we got a result, remove bg
            if transparent_bg and result.get("success") and result.get("output"):
                output_url = result["output"]
                if isinstance(output_url, list):
                    output_url = output_url[0]
                
                # Run background removal
                bg_result = await self.edit_image(output_url, "remove_bg")
                if bg_result.get("success"):
                    result["output_with_transparent_bg"] = bg_result.get("output")
            
            result["product_type"] = product_type
            result["model_used"] = model
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="replicate_create_video",
        description="Create AI-generated videos with 15+ model options. Supports text-to-video and image-to-video with models like Kling, Sora, Veo3, Luma, Pixverse, and more.",
        category="ai_models"
    )
    async def create_video(
        self,
        description: str,
        image_url: Optional[str] = None,
        duration: int = 5,
        quality: str = "balanced",
        model: str = "auto",
        aspect_ratio: str = "16:9"
    ) -> Dict[str, Any]:
        """
        Create AI-generated videos with premium model selection.
        
        Args:
            description: What the video should show (motion, action, scene)
            image_url: Optional starting image to animate
            duration: Video duration in seconds (2-10 depending on model)
            quality: Quality preset (fast, balanced, best)
            model: Model to use (auto, kling, luma, veo3, pixverse, sora, minimax, wan, seedance)
            aspect_ratio: Video aspect ratio (16:9, 9:16, 1:1, 4:3)
        """
        # Model configuration: (model_id, supports_i2v, max_duration, image_param_name)
        model_configs = {
            "kling": ("kwaivgi/kling-v1.6-pro", True, 10, "start_image"),
            "kling_turbo": ("kwaivgi/kling-v2.5-turbo-pro", True, 10, "start_image"),
            "luma": ("luma/ray-2-540p", True, 5, "first_frame_image"),
            "luma_flash": ("luma/ray-flash-2", True, 5, "first_frame_image"),
            "veo3": ("google/veo-3", True, 8, "first_frame_image"),
            "veo3_fast": ("google/veo-3-fast", True, 8, "first_frame_image"),
            "veo2": ("google/veo-2", True, 8, "first_frame_image"),
            "pixverse": ("pixverse/pixverse-v5", True, 8, "first_frame_image"),
            "pixverse45": ("pixverse/pixverse-v4.5", True, 8, "first_frame_image"),
            "sora": ("openai/sora-2", True, 10, "image"),
            "minimax": ("minimax/video-01", True, 10, "first_frame_image"),
            "hailuo": ("minimax/hailuo-2.3-fast", True, 10, "first_frame_image"),
            "leonardo": ("leonardoai/motion-2.0", True, 5, "first_frame_image"),
            "wan": ("wan-video/wan-2.5-t2v-fast", False, 5, None),
            "seedance": ("bytedance/seedance-1-pro-fast", False, 5, None),
            "svd": ("stability-ai/stable-video-diffusion", True, 4, "image"),
            "zeroscope": ("anotherjesse/zeroscope-v2-xl", False, 4, None),
        }
        
        # Auto-select model based on input
        if model == "auto":
            if image_url:
                # For image-to-video, prefer Kling or Luma
                if quality == "best":
                    model = "kling"
                elif quality == "fast":
                    model = "luma_flash"
                else:
                    model = "kling"
            else:
                # For text-to-video
                if quality == "best":
                    model = "veo3"
                elif quality == "fast":
                    model = "wan"
                else:
                    model = "minimax"
        
        # Get model config
        config = model_configs.get(model)
        if not config:
            model = "minimax"  # Fallback
            config = model_configs["minimax"]
        
        model_id, supports_i2v, max_dur, img_param = config
        
        # Constrain duration to model limits
        duration = min(duration, max_dur)
        
        # Build inputs based on model
        inputs = {"prompt": description}
        
        # Add image input if provided and supported
        if image_url and supports_i2v and img_param:
            inputs[img_param] = image_url
        elif image_url and not supports_i2v:
            # Model doesn't support i2v, warn and proceed without image
            logger.warning(f"Model {model} doesn't support image-to-video, using text-to-video instead")
        
        # Add model-specific parameters
        if model.startswith("kling"):
            inputs["duration"] = duration
            inputs["cfg_scale"] = 0.5
            if aspect_ratio:
                inputs["aspect_ratio"] = aspect_ratio
        elif model.startswith("luma"):
            inputs["aspect_ratio"] = aspect_ratio
        elif model.startswith("veo"):
            inputs["duration"] = duration
            inputs["aspect_ratio"] = aspect_ratio
            if model == "veo3":
                inputs["guidance_scale"] = 3.0
        elif model.startswith("pixverse"):
            inputs["aspect_ratio"] = aspect_ratio
            inputs["seed"] = 0
        elif model == "sora":
            inputs["duration"] = min(duration, 10)
            inputs["quality"] = "high" if quality == "best" else "standard"
        elif model == "minimax":
            inputs["prompt_optimizer"] = True
        elif model == "hailuo":
            inputs["duration"] = duration
            inputs["resolution"] = "768p"
        elif model == "leonardo":
            inputs["motion_strength"] = 5
            ar_map = {"16:9": "16_9", "9:16": "9_16", "1:1": "1_1"}
            inputs["aspect_ratio"] = ar_map.get(aspect_ratio, "16_9")
        elif model == "wan":
            inputs["aspect_ratio"] = aspect_ratio
        elif model == "seedance":
            inputs["aspect_ratio"] = aspect_ratio
        
        try:
            info = await self._get_model_info(model_id)
            version = info.get("resolved_version")
            
            result = await self._run_prediction(
                model=model_id,
                version=version,
                inputs=inputs,
                wait=True
            )
            
            result["duration"] = duration
            result["model_used"] = model_id
            result["model_shortcut"] = model
            result["aspect_ratio"] = aspect_ratio
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e), "model_attempted": model_id}
