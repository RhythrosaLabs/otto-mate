"""
Replicate Advanced Integration
==============================

Advanced Replicate API features:
- Webhook support for async predictions
- Model chaining for complex pipelines
- Batch processing
- Streaming predictions
- Training/fine-tuning support
- Model search and discovery
"""

import asyncio
import aiohttp
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field

from .core import tool, ToolBase

logger = logging.getLogger(__name__)

# ==========================================
# DATA MODELS
# ==========================================

@dataclass
class PredictionResult:
    """Result from a Replicate prediction"""
    prediction_id: str
    model: str
    status: str
    output: Any = None
    error: Optional[str] = None
    metrics: Optional[Dict] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class ChainStep:
    """A step in a model chain"""
    model: str
    input_mapping: Dict[str, str]  # Maps output from previous step to this input
    params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass
class WebhookConfig:
    """Webhook configuration"""
    url: str
    events: List[str] = field(default_factory=lambda: ["start", "completed"])
    secret: Optional[str] = None


# ==========================================
# RATE LIMITER (from printify_clean)
# ==========================================

class ReplicateRateLimiter:
    """
    Intelligent rate limiter for Replicate API when account has low credits.
    
    When account has <$5 credit, Replicate throttles to 6 requests/minute.
    This class batches and throttles requests to stay under the limit.
    Uses exponential backoff: 12s → 24s → 48s for rate limit recovery.
    """
    
    def __init__(self, requests_per_minute: int = 6):
        self.requests_per_minute = requests_per_minute
        self.min_interval = 60.0 / requests_per_minute  # ~10 seconds for 6/min
        self.last_request_time = 0.0
        self.is_rate_limited = False
        self.consecutive_failures = 0
        self.base_delay = 12  # Base delay for exponential backoff
    
    async def wait_if_needed(self):
        """Wait if necessary to respect rate limit."""
        import time
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Calculate delay with exponential backoff if rate limited
        if self.is_rate_limited:
            delay = self.base_delay * (2 ** min(self.consecutive_failures, 3))
        else:
            delay = self.min_interval
        
        if time_since_last < delay:
            wait_time = delay - time_since_last
            logger.info(f"⏳ Rate limit: waiting {wait_time:.1f}s before next request...")
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def mark_rate_limited(self):
        """Mark that we've hit the rate limit."""
        self.is_rate_limited = True
        self.consecutive_failures += 1
        self.last_request_time = time.time()
        logger.warning(f"⚠️ Rate limited. Consecutive failures: {self.consecutive_failures}")
    
    def mark_success(self):
        """Mark that a request succeeded."""
        self.is_rate_limited = False
        self.consecutive_failures = 0


# ==========================================
# API USAGE TRACKER (from printify_clean)
# ==========================================

@dataclass
class APICallRecord:
    """Record of a single API call for usage tracking."""
    timestamp: str
    provider: str
    model: str
    endpoint: str
    duration_ms: int
    success: bool
    error: Optional[str] = None
    metadata: Optional[Dict] = None


class APIUsageTracker:
    """
    Track API usage and costs for Replicate calls.
    Helps monitor spending and identify expensive operations.
    """
    
    def __init__(self, storage_path: str = "./data/api_usage.jsonl"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.session_calls: List[APICallRecord] = []
        self.session_start = datetime.now()
    
    def track_call(
        self,
        provider: str,
        model: str,
        endpoint: str,
        duration_ms: int,
        success: bool,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Track an API call."""
        record = APICallRecord(
            timestamp=datetime.now().isoformat(),
            provider=provider,
            model=model,
            endpoint=endpoint,
            duration_ms=duration_ms,
            success=success,
            error=error,
            metadata=metadata
        )
        self.session_calls.append(record)
        
        # Persist to file
        try:
            with open(self.storage_path, "a") as f:
                f.write(json.dumps(record.__dict__) + "\n")
        except Exception as e:
            logger.warning(f"Failed to persist usage record: {e}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session's API usage."""
        total_calls = len(self.session_calls)
        successful = sum(1 for c in self.session_calls if c.success)
        total_duration = sum(c.duration_ms for c in self.session_calls)
        
        # Group by model
        by_model: Dict[str, int] = {}
        for call in self.session_calls:
            by_model[call.model] = by_model.get(call.model, 0) + 1
        
        return {
            "total_calls": total_calls,
            "successful": successful,
            "failed": total_calls - successful,
            "total_duration_ms": total_duration,
            "avg_duration_ms": total_duration / total_calls if total_calls > 0 else 0,
            "by_model": by_model,
            "session_start": self.session_start.isoformat()
        }


# Global instances
_rate_limiter: Optional[ReplicateRateLimiter] = None
_usage_tracker: Optional[APIUsageTracker] = None

import time  # Import for rate limiter


def get_rate_limiter() -> ReplicateRateLimiter:
    """Get or create the global rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = ReplicateRateLimiter()
    return _rate_limiter


def get_usage_tracker() -> APIUsageTracker:
    """Get or create the global usage tracker."""
    global _usage_tracker
    if _usage_tracker is None:
        _usage_tracker = APIUsageTracker()
    return _usage_tracker


# ==========================================
# REPLICATE ADVANCED TOOLS
# ==========================================

class ReplicateAdvancedTools(ToolBase):
    """Advanced Replicate integration with webhooks, chaining, and batch processing."""
    
    # Model Catalog (updated Feb 2026 from printify_clean)
    MODEL_SHORTCUTS = {
        # ── Image Generation - Top Tier ──
        "flux": "black-forest-labs/flux-1.1-pro",
        "flux_fast": "prunaai/flux-fast",  # Fastest - 4 steps
        "flux_pro": "black-forest-labs/flux-1.1-pro",
        "flux_pro_ultra": "black-forest-labs/flux-pro-ultra",
        "flux_schnell": "black-forest-labs/flux-schnell",
        "flux_dev": "black-forest-labs/flux-dev",
        "flux_fill": "black-forest-labs/flux-fill-pro",
        "flux_canny": "black-forest-labs/flux-canny-pro",
        "flux_depth": "black-forest-labs/flux-depth-pro",
        "flux_redux": "black-forest-labs/flux-redux-dev",
        "flux_kontext": "black-forest-labs/flux-kontext-pro",  # Face-aware
        "ideogram": "ideogram-ai/ideogram-v2",
        "ideogram_v3": "ideogram-ai/ideogram-v3",
        "recraft": "recraft-ai/recraft-v3",
        "recraft_svg": "recraft-ai/recraft-v3-svg",
        "imagen4": "google/imagen-4-ultra",  # Google's highest quality
        "seedream": "bytedance/seedream-4",  # 4K resolution
        "bria": "bria/image-3.2",  # Commercial-safe
        
        # ── Image Generation - Stable Diffusion ──
        "sdxl": "stability-ai/sdxl",
        "sd3": "stability-ai/sd3.5-large",
        "sd3_turbo": "stability-ai/sd3.5-large-turbo",
        "sd3_medium": "stability-ai/sd3.5-medium",
        "photon": "luma/photon",
        "playground": "playgroundai/playground-v2.5-1024px-aesthetic",
        "juggernaut": "lucataco/juggernaut-xl-v9",
        "dreamshaper": "lucataco/dreamshaper-xl-v2-turbo",
        
        # ── Video Generation ──
        "sora": "openai/sora-2",  # OpenAI flagship
        "sora2": "openai/sora-2",
        "kling": "kwaivgi/kling-v2.5-turbo-pro",  # Latest Kling
        "kling_pro": "kwaivgi/kling-v2.5-turbo-pro",
        "kling_standard": "kwaivgi/kling-v1.5-standard",
        "veo": "google/veo-3.1-fast",  # Latest Veo with audio
        "veo3": "google/veo-3",
        "veo3_fast": "google/veo-3-fast",
        "veo31_fast": "google/veo-3.1-fast",
        "veo2": "google/veo-2",
        "pixverse": "pixverse/pixverse-v5",  # Latest Pixverse
        "pixverse5": "pixverse/pixverse-v5",
        "pixverse45": "pixverse/pixverse-v4.5",
        "leonardo": "leonardoai/motion-2.0",
        "hailuo": "minimax/hailuo-2.3-fast",
        "minimax": "minimax/video-01",
        "minimax_live": "minimax/video-01-live",
        "luma": "luma/ray-2-540p",
        "luma_ray": "luma/ray-2-540p",
        "luma_flash": "luma/ray-flash-2",
        "luma_modify": "luma/modify-video",
        "wan": "wan-video/wan-2.5-t2v-fast",
        "wan_fast": "wan-video/wan-2.5-t2v-fast",
        "wan_v2v": "wan-video/wan-2.5-v2v-fast",
        "seedance": "bytedance/seedance-1-pro-fast",
        "seedance_v2v": "bytedance/seedance-1-pro-v2v",
        "runway": "runway/gen-3-turbo",
        "runway_alpha": "runway/gen-3-alpha-turbo",
        "hunyuan": "tencent/hunyuan-video",
        "ltx": "lightricks/ltx-video",
        "svd": "stability-ai/stable-video-diffusion",
        "animate_diff": "lucataco/animate-diff",
        
        # ── 3D Generation ──
        "hunyuan3d": "tencent/hunyuan3d-2",
        "hunyuan3d_21": "ndreca/hunyuan3d-2.1",
        "luciddreamer": "jd7h/luciddreamer",
        "stable_fast_3d": "stabilityai/stable-fast-3d",
        "instant_mesh": "cjwbw/instant-mesh",
        "trellis": "firtoz/trellis",
        "tripo": "lucataco/tripo3d",
        "triposr": "tripo/tripo-sr-v2",
        "wonder3d": "camenduru/wonder3d",
        "lgm": "ashawkey/lgm",
        "craftsman": "adirik/craftsman",
        "rodin": "hyper3d/rodin",
        "morphix3d": "subhash25rawat/morphix3d",
        "shape": "cjwbw/shap-e",
        "shap_e": "cjwbw/shap-e",
        "vggt": "vufinder/vggt-1b",
        
        # ── Image Editing & Enhancement ──
        "nano_banana": "google/nano-banana",  # Gemini image editing
        "flux_edit": "hardikdava/flux-image-editing",
        "edit_fast": "reve/edit-fast",
        "next_scene": "lucataco/next-scene",
        "inpaint": "cjwbw/stable-diffusion-v2-inpainting",
        "sdxl_inpaint": "lucataco/sdxl-inpainting",
        "upscale": "nightmareai/real-esrgan",
        "upscale_4x": "nightmareai/real-esrgan",
        "upscale_creative": "philz1337x/clarity-upscaler",
        "remove_bg": "cjwbw/rembg",
        "rembg": "cjwbw/rembg",
        "face_restore": "tencentarc/gfpgan",
        "gfpgan": "tencentarc/gfpgan",
        "codeformer": "sczhou/codeformer",
        "face_swap": "lucataco/faceswap",
        "restore_photo": "microsoft/bringing-old-photos-back-to-life",
        "colorize": "arielreplicate/deoldify",
        "deoldify": "arielreplicate/deoldify",
        "style_transfer": "lucataco/neural-style-tf",
        "instruct_pix2pix": "timothybrooks/instruct-pix2pix",
        "controlnet": "jagilley/controlnet-normal",
        "controlnet_canny": "jagilley/controlnet-canny",
        "controlnet_depth": "jagilley/controlnet-depth",
        "controlnet_pose": "jagilley/controlnet-pose",
        "segment_anything": "meta/sam-2-video",
        "sam": "meta/sam-2-video",
        
        # ── Marketing/Ads ──
        "ads_for_products": "pipeline-examples/ads-for-products",
        "flux_static_ads": "loolau/flux-static-ads",
        "logo_in_context": "subhash25rawat/logo-in-context",
        "ad_inpaint": "logerzhu/ad-inpaint",
        
        # ── Video Editing ──
        "video_upscaler": "lucataco/video-upscaler",
        "video_stabilizer": "lucataco/video-stabilizer",
        "video_style_transfer": "lucataco/video-style-transfer",
        
        # ── Audio Generation ──
        "musicgen": "meta/musicgen",
        "musicgen_large": "meta/musicgen:large",
        "musicgen_melody": "meta/musicgen:melody",
        "musicgen_looper": "andreasjansson/musicgen-looper",
        "lyria2": "google/lyria-2",  # 48kHz stereo
        "music_15": "minimax/music-1.5",  # Full songs with vocals
        "stable_audio": "stability-ai/stable-audio-2.5",
        "flux_music": "zsxkib/flux-music",
        "bark": "suno-ai/bark",
        "xtts": "cjwbw/xtts-v2",
        "xtts_v2": "cjwbw/xtts-v2",
        "speech_hd": "minimax/speech-02-hd",  # HD voice synthesis
        "elevenlabs": "lucataco/elevenlabs-tts",
        "cosyvoice": "alibaba-research/cosyvoice",
        "whisper": "openai/whisper",
        "whisper_large": "openai/whisper:large-v3",
        "demucs": "cjwbw/demucs",
        "separate_vocals": "cjwbw/demucs",
        "rvc": "nateraw/rvc",
        "voice_clone": "cjwbw/xtts-v2",
        
        # ── Text/LLM ──
        "llama": "meta/meta-llama-3.1-405b-instruct",
        "llama_405b": "meta/meta-llama-3.1-405b-instruct",
        "llama_70b": "meta/meta-llama-3.1-70b-instruct",
        "llama_8b": "meta/meta-llama-3.1-8b-instruct",
        "mistral": "mistralai/mistral-7b-instruct",
        "mixtral": "mistralai/mixtral-8x7b-instruct",
        "codellama": "meta/codellama-34b-instruct",
        "qwen": "qwenai/qwen-2.5-coder-32b-instruct",
        "deepseek": "deepseek-ai/deepseek-r1",
        "deepseek_coder": "deepseek-ai/deepseek-coder-v2",
        
        # ── Vision & Analysis ──
        "blip": "salesforce/blip",
        "blip2": "salesforce/blip-2",
        "llava": "yorickvp/llava-13b",
        "llava_next": "yorickvp/llava-v1.6-mistral-7b",
        "moondream": "vikhyatk/moondream2",
        "florence": "microsoft/florence-2-large",
        
        # ── OCR & Document ──
        "ocr": "philz1337x/ocr-extractor",
        "doctr": "doctr/doctr",
        "surya": "vikp/surya",
        "pdf_to_text": "lucataco/pdf-to-text",
        
        # ── Specialized ──
        "qr_code": "andreasjansson/qr-code-ai-art-generator",
        "qr_art": "andreasjansson/qr-code-ai-art-generator",
        "logo": "lucataco/logo-generator",
        "icon": "lucataco/nsfw-filter",
        "nsfw_filter": "lucataco/nsfw-filter",
        "cog": "replicate/cog",
    }
    
    def __init__(
        self,
        api_token: str = None,
        default_webhook_url: str = None,
        results_dir: str = "./data/replicate_results"
    ):
        self.api_token = api_token or os.getenv("REPLICATE_API_TOKEN")
        self.default_webhook_url = default_webhook_url
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        self.base_url = "https://api.replicate.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept-Encoding": "identity, gzip, deflate"
        }
        
        # Track active predictions for chaining
        self._active_predictions: Dict[str, PredictionResult] = {}
        
        # Task-to-model mappings for smart selection (updated Feb 2026)
        self._task_mappings = {
            # Image Generation
            "generate image": ["flux_fast", "flux", "ideogram_v3", "recraft"],
            "create art": ["flux", "ideogram_v3", "recraft", "playground"],
            "draw": ["flux_fast", "ideogram_v3", "sdxl"],
            "illustration": ["ideogram_v3", "recraft", "flux"],
            "logo": ["ideogram_v3", "recraft_svg", "logo_in_context"],
            "icon": ["recraft_svg", "ideogram_v3"],
            "realistic photo": ["flux_pro_ultra", "photon", "juggernaut"],
            "product photo": ["flux_pro_ultra", "photon", "flux_fast"],
            "portrait": ["flux", "flux_kontext", "juggernaut", "dreamshaper"],
            "4k image": ["seedream", "imagen4", "flux_pro_ultra"],
            "commercial safe": ["bria", "flux_pro"],
            
            # Marketing/Ads
            "create ad": ["flux_static_ads", "ads_for_products", "ad_inpaint"],
            "product ad": ["ads_for_products", "flux_static_ads"],
            "marketing": ["flux_static_ads", "ads_for_products"],
            "ad creative": ["flux_static_ads", "ad_inpaint"],
            "logo design": ["logo_in_context", "recraft_svg"],
            "brand": ["logo_in_context", "flux_static_ads"],
            
            # Video 
            "generate video": ["sora", "kling", "veo", "pixverse"],
            "create video": ["sora", "kling_pro", "veo3"],
            "animate": ["kling", "animate_diff", "svd"],
            "video from image": ["kling", "svd", "hailuo"],
            "video ad": ["sora", "kling", "veo"],
            "product video": ["kling", "sora", "minimax"],
            "fast video": ["veo31_fast", "pixverse", "wan_fast"],
            
            # Video Editing
            "upscale video": ["video_upscaler"],
            "stabilize video": ["video_stabilizer"],
            "video style": ["video_style_transfer", "wan_v2v"],
            "edit video": ["luma_modify", "seedance_v2v", "wan_v2v"],
            
            # 3D
            "create 3d": ["hunyuan3d", "stable_fast_3d", "trellis"],
            "3d model": ["hunyuan3d", "instant_mesh", "tripo"],
            "generate mesh": ["stable_fast_3d", "instant_mesh", "triposr"],
            "fast 3d": ["stable_fast_3d", "lgm"],
            
            # Image Editing
            "upscale": ["upscale", "upscale_creative"],
            "enhance": ["upscale_creative", "face_restore"],
            "remove background": ["remove_bg", "rembg"],
            "inpaint": ["flux_fill", "sdxl_inpaint", "inpaint"],
            "edit image": ["nano_banana", "flux_edit", "edit_fast", "instruct_pix2pix"],
            "gemini edit": ["nano_banana"],
            "quick edit": ["edit_fast", "flux_edit"],
            "next scene": ["next_scene"],
            "restore photo": ["restore_photo", "colorize"],
            "colorize": ["colorize", "deoldify"],
            "face": ["face_restore", "codeformer", "gfpgan"],
            "face swap": ["face_swap"],
            "style transfer": ["style_transfer"],
            
            # Audio
            "generate music": ["musicgen", "stable_audio", "lyria2"],
            "create music": ["musicgen_melody", "stable_audio", "music_15"],
            "full song": ["music_15", "lyria2"],
            "music loop": ["musicgen_looper"],
            "text to speech": ["speech_hd", "xtts_v2", "bark"],
            "voice": ["speech_hd", "xtts_v2", "voice_clone"],
            "clone voice": ["xtts_v2", "rvc"],
            "transcribe": ["whisper", "whisper_large"],
            "speech to text": ["whisper", "whisper_large"],
            "separate audio": ["demucs", "separate_vocals"],
            
            # Vision/Analysis
            "describe image": ["llava_next", "moondream", "florence"],
            "analyze image": ["llava_next", "blip2", "florence"],
            "caption": ["blip2", "llava", "moondream"],
            "ocr": ["ocr", "florence"],
            "read text": ["ocr", "florence"],
            "extract text": ["ocr", "florence"],
            
            # LLM
            "chat": ["llama", "mixtral", "qwen"],
            "code": ["qwen", "deepseek_coder", "codellama"],
            "analyze": ["llama", "deepseek", "mixtral"],
        }
    
    def _resolve_model(self, model: str) -> str:
        """Resolve model shortcut to full model identifier."""
        return self.MODEL_SHORTCUTS.get(model.lower(), model)
    
    @tool(
        name="replicate_smart_select_model",
        description="Intelligently select the best AI model based on task description",
        category="replicate"
    )
    async def smart_select_model(
        self,
        task_description: str,
        prefer_quality: bool = True,
        prefer_speed: bool = False
    ) -> Dict[str, Any]:
        """
        Intelligently select the best model for a given task.
        
        Args:
            task_description: Natural language description of what you want to do
            prefer_quality: Prioritize output quality over speed
            prefer_speed: Prioritize speed over quality
            
        Returns:
            Recommended models with reasons
        """
        task_lower = task_description.lower()
        matched_models = []
        matched_tasks = []
        
        # Score each task mapping by keyword matches
        for task_key, models in self._task_mappings.items():
            task_words = set(task_key.split())
            desc_words = set(task_lower.split())
            
            # Check for word overlap or substring match
            overlap = len(task_words & desc_words)
            if overlap > 0 or task_key in task_lower:
                score = overlap + (2 if task_key in task_lower else 0)
                matched_tasks.append((task_key, models, score))
        
        # Sort by score and collect unique models
        matched_tasks.sort(key=lambda x: x[2], reverse=True)
        seen_models = set()
        
        for task_key, models, score in matched_tasks[:3]:
            for model in models:
                if model not in seen_models:
                    full_model = self.MODEL_SHORTCUTS.get(model, model)
                    matched_models.append({
                        "shortcut": model,
                        "full_name": full_model,
                        "matched_task": task_key,
                        "score": score
                    })
                    seen_models.add(model)
        
        # Pick recommendation based on preferences
        if matched_models:
            recommended = matched_models[0]["shortcut"]
            
            # Adjust for speed preference - pick schnell/turbo variants
            if prefer_speed:
                speed_models = ["flux_schnell", "sd3_turbo", "runway", "ltx"]
                for m in matched_models:
                    if any(s in m["shortcut"] for s in ["schnell", "turbo", "fast"]):
                        recommended = m["shortcut"]
                        break
                    if m["shortcut"] in speed_models:
                        recommended = m["shortcut"]
                        break
            
            return {
                "success": True,
                "task": task_description,
                "recommended_model": recommended,
                "recommended_full": self.MODEL_SHORTCUTS.get(recommended, recommended),
                "alternatives": matched_models[:5],
                "usage_example": f'await replicate.create_prediction_async("{recommended}", {{"prompt": "..."}})'
            }
        
        # No match - suggest based on category keywords
        category_defaults = {
            "image": "flux",
            "photo": "flux_pro_ultra",
            "video": "kling_pro",
            "3d": "trellis",
            "music": "musicgen",
            "audio": "xtts_v2",
            "speech": "whisper",
            "text": "llama",
            "code": "qwen"
        }
        
        for keyword, model in category_defaults.items():
            if keyword in task_lower:
                return {
                    "success": True,
                    "task": task_description,
                    "recommended_model": model,
                    "recommended_full": self.MODEL_SHORTCUTS.get(model, model),
                    "matched_category": keyword,
                    "alternatives": [],
                    "usage_example": f'await replicate.create_prediction_async("{model}", {{"prompt": "..."}})'
                }
        
        return {
            "success": False,
            "task": task_description,
            "message": "No specific model found. Use replicate_search_models to explore options.",
            "available_shortcuts": list(self.MODEL_SHORTCUTS.keys())[:30]
        }
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        headers: Dict = None,
        max_retries: int = 3,
        track_usage: bool = True
    ) -> Dict[str, Any]:
        """
        Make API request to Replicate with exponential backoff retry.
        
        Rate limiting pattern from printify_clean:
        - Exponential backoff: 12s → 24s → 48s for rate limits
        - 15 minute timeout for video/3D generation
        - Usage tracking for cost monitoring
        """
        url = f"{self.base_url}{endpoint}"
        req_headers = {**self.headers, **(headers or {})}
        
        rate_limiter = get_rate_limiter()
        tracker = get_usage_tracker() if track_usage else None
        
        base_delay = 12  # printify_clean uses 12s base delay for rate limits
        last_error = None
        start_time = time.time()
        
        # Wait for rate limit if needed
        await rate_limiter.wait_if_needed()
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method,
                        url,
                        headers=req_headers,
                        json=data,
                        timeout=aiohttp.ClientTimeout(total=900)  # 15 min for video/3D
                    ) as response:
                        result = await response.json()
                        
                        # Handle rate limiting with exponential backoff
                        if response.status == 429:
                            rate_limiter.mark_rate_limited()
                            delay = base_delay * (2 ** attempt)  # 12s, 24s, 48s
                            logger.warning(f"Rate limited. Waiting {delay}s before retry {attempt + 1}/{max_retries}")
                            await asyncio.sleep(delay)
                            continue
                        
                        if response.status >= 400:
                            raise Exception(f"Replicate API error: {result}")
                        
                        # Success - mark and track
                        rate_limiter.mark_success()
                        if tracker:
                            model_name = endpoint.split("/")[-1] if "/" in endpoint else "unknown"
                            tracker.track_call(
                                provider="replicate",
                                model=model_name,
                                endpoint=endpoint,
                                duration_ms=int((time.time() - start_time) * 1000),
                                success=True
                            )
                        
                        return result
                        
            except aiohttp.ClientError as e:
                last_error = e
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Request failed: {e}. Retry {attempt + 1}/{max_retries} in {delay}s")
                await asyncio.sleep(delay)
        
        # Track failure
        if tracker:
            tracker.track_call(
                provider="replicate",
                model="unknown",
                endpoint=endpoint,
                duration_ms=int((time.time() - start_time) * 1000),
                success=False,
                error=str(last_error)
            )
        
        raise Exception(f"Request failed after {max_retries} retries: {last_error}")
    
    # ==========================================
    # PREDICTIONS WITH WEBHOOKS
    # ==========================================
    
    @tool(
        name="replicate_create_prediction_async",
        description="Create a Replicate prediction with webhook for async notification",
        category="replicate"
    )
    async def create_prediction_async(
        self,
        model: str,
        input_params: Dict[str, Any],
        webhook_url: str = None,
        webhook_events: List[str] = None,
        timeout_minutes: int = None
    ) -> Dict[str, Any]:
        """
        Create a prediction with optional webhook notification.
        
        Args:
            model: Model name or shortcut (e.g., "flux", "kling", "trellis")
            input_params: Model input parameters
            webhook_url: HTTPS URL for webhook notifications
            webhook_events: Events to trigger webhook (start, output, logs, completed)
            timeout_minutes: Max time before auto-cancel
        """
        model = self._resolve_model(model)
        
        # Determine if using official model endpoint or version endpoint
        if "/" in model and ":" not in model:
            # Official model format: owner/model
            endpoint = f"/models/{model}/predictions"
        else:
            # Version format: needs version ID
            endpoint = "/predictions"
        
        payload = {"input": input_params}
        
        # Add webhook if provided
        webhook = webhook_url or self.default_webhook_url
        if webhook:
            payload["webhook"] = webhook
            payload["webhook_events_filter"] = webhook_events or ["start", "completed"]
        
        # Add timeout header
        headers = {}
        if timeout_minutes:
            headers["Cancel-After"] = f"{timeout_minutes}m"
        
        # Add version for non-official models
        if ":" in model:
            payload["version"] = model.split(":")[-1]
        
        try:
            result = await self._request("POST", endpoint, payload, headers)
            
            prediction = PredictionResult(
                prediction_id=result.get("id"),
                model=model,
                status=result.get("status"),
                created_at=result.get("created_at")
            )
            
            self._active_predictions[prediction.prediction_id] = prediction
            
            return {
                "success": True,
                "prediction_id": result.get("id"),
                "model": model,
                "status": result.get("status"),
                "webhook_configured": webhook is not None,
                "get_url": result.get("urls", {}).get("get"),
                "cancel_url": result.get("urls", {}).get("cancel"),
                "stream_url": result.get("urls", {}).get("stream")
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="replicate_get_prediction",
        description="Get the status and output of a prediction",
        category="replicate"
    )
    async def get_prediction(
        self,
        prediction_id: str
    ) -> Dict[str, Any]:
        """
        Get prediction status and output.
        
        Args:
            prediction_id: The prediction ID
        """
        try:
            result = await self._request("GET", f"/predictions/{prediction_id}")
            
            return {
                "prediction_id": result.get("id"),
                "model": result.get("model"),
                "status": result.get("status"),
                "output": result.get("output"),
                "error": result.get("error"),
                "metrics": result.get("metrics"),
                "created_at": result.get("created_at"),
                "completed_at": result.get("completed_at"),
                "logs": result.get("logs", "")[-500:]  # Last 500 chars of logs
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="replicate_wait_for_prediction",
        description="Wait for a prediction to complete and return the result",
        category="replicate"
    )
    async def wait_for_prediction(
        self,
        prediction_id: str,
        timeout_seconds: int = 300,
        poll_interval: int = 2
    ) -> Dict[str, Any]:
        """
        Wait for prediction to complete.
        
        Args:
            prediction_id: The prediction ID
            timeout_seconds: Max seconds to wait
            poll_interval: Seconds between status checks
        """
        start_time = asyncio.get_event_loop().time()
        
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout_seconds:
                return {
                    "success": False,
                    "error": "Timeout waiting for prediction",
                    "prediction_id": prediction_id
                }
            
            result = await self.get_prediction(prediction_id)
            status = result.get("status")
            
            if status == "succeeded":
                return {
                    "success": True,
                    "prediction_id": prediction_id,
                    "output": result.get("output"),
                    "metrics": result.get("metrics"),
                    "elapsed_seconds": elapsed
                }
            
            elif status in ["failed", "canceled"]:
                return {
                    "success": False,
                    "prediction_id": prediction_id,
                    "status": status,
                    "error": result.get("error")
                }
            
            await asyncio.sleep(poll_interval)
    
    @tool(
        name="replicate_cancel_prediction",
        description="Cancel a running prediction",
        category="replicate"
    )
    async def cancel_prediction(
        self,
        prediction_id: str
    ) -> Dict[str, Any]:
        """Cancel a prediction."""
        try:
            result = await self._request(
                "POST",
                f"/predictions/{prediction_id}/cancel"
            )
            return {
                "success": True,
                "prediction_id": prediction_id,
                "status": "canceled"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================
    # MODEL CHAINING
    # ==========================================
    
    @tool(
        name="replicate_run_chain",
        description="Run a chain of models where each output feeds into the next",
        category="replicate"
    )
    async def run_chain(
        self,
        chain: List[Dict[str, Any]],
        initial_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run a chain of models in sequence.
        
        Args:
            chain: List of chain steps, each with:
                - model: Model name/shortcut
                - input_mapping: Dict mapping "previous_output" or specific keys to input params
                - params: Additional fixed parameters
            initial_input: Initial input for first model
            
        Example:
            chain = [
                {"model": "flux", "params": {"prompt": "a cat"}},
                {"model": "upscale", "input_mapping": {"image": "output"}},
                {"model": "remove_bg", "input_mapping": {"image": "output"}}
            ]
        """
        results = []
        current_output = None
        
        for i, step in enumerate(chain):
            model = self._resolve_model(step.get("model"))
            params = step.get("params", {}).copy()
            input_mapping = step.get("input_mapping", {})
            
            # Build input from previous output and mapping
            if i == 0:
                # First step uses initial_input
                params.update(initial_input)
            else:
                # Map previous output to current input
                for target_key, source_key in input_mapping.items():
                    if source_key == "output":
                        # Use entire previous output
                        if isinstance(current_output, str):
                            params[target_key] = current_output
                        elif isinstance(current_output, list) and current_output:
                            params[target_key] = current_output[0]
                        elif isinstance(current_output, dict):
                            params[target_key] = current_output.get("output", current_output)
                    elif source_key.startswith("output."):
                        # Use specific key from output dict
                        key = source_key.split(".", 1)[1]
                        if isinstance(current_output, dict):
                            params[target_key] = current_output.get(key)
            
            logger.info(f"Chain step {i+1}: Running {model}")
            
            # Run prediction and wait
            create_result = await self.create_prediction_async(
                model=model,
                input_params=params
            )
            
            if not create_result.get("success"):
                return {
                    "success": False,
                    "error": f"Chain failed at step {i+1}: {create_result.get('error')}",
                    "completed_steps": results
                }
            
            # Wait for completion
            wait_result = await self.wait_for_prediction(
                create_result["prediction_id"],
                timeout_seconds=600
            )
            
            if not wait_result.get("success"):
                return {
                    "success": False,
                    "error": f"Chain failed at step {i+1}: {wait_result.get('error')}",
                    "completed_steps": results
                }
            
            current_output = wait_result.get("output")
            
            results.append({
                "step": i + 1,
                "model": model,
                "prediction_id": create_result["prediction_id"],
                "output": current_output
            })
        
        return {
            "success": True,
            "chain_length": len(chain),
            "final_output": current_output,
            "all_steps": results
        }
    
    @tool(
        name="replicate_create_pipeline",
        description="Create a reusable model pipeline definition",
        category="replicate"
    )
    async def create_pipeline(
        self,
        name: str,
        description: str,
        steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Save a pipeline definition for reuse.
        
        Args:
            name: Pipeline name
            description: What the pipeline does
            steps: List of pipeline steps
        """
        pipeline = {
            "name": name,
            "description": description,
            "steps": steps,
            "created_at": datetime.now().isoformat()
        }
        
        filepath = self.results_dir / f"pipeline_{name}.json"
        with open(filepath, "w") as f:
            json.dump(pipeline, f, indent=2)
        
        return {
            "success": True,
            "name": name,
            "steps": len(steps),
            "saved_to": str(filepath)
        }

    # ==========================================
    # BATCH PROCESSING
    # ==========================================
    
    @tool(
        name="replicate_batch_predictions",
        description="Run multiple predictions in parallel",
        category="replicate"
    )
    async def batch_predictions(
        self,
        model: str,
        inputs: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """
        Run multiple predictions in parallel.
        
        Args:
            model: Model name/shortcut
            inputs: List of input parameter dicts
            max_concurrent: Max concurrent predictions
        """
        model = self._resolve_model(model)
        
        results = []
        errors = []
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def run_single(idx: int, input_params: Dict):
            async with semaphore:
                try:
                    create_result = await self.create_prediction_async(
                        model=model,
                        input_params=input_params
                    )
                    
                    if not create_result.get("success"):
                        return {"index": idx, "error": create_result.get("error")}
                    
                    wait_result = await self.wait_for_prediction(
                        create_result["prediction_id"],
                        timeout_seconds=600
                    )
                    
                    if wait_result.get("success"):
                        return {
                            "index": idx,
                            "prediction_id": create_result["prediction_id"],
                            "output": wait_result.get("output")
                        }
                    else:
                        return {"index": idx, "error": wait_result.get("error")}
                        
                except Exception as e:
                    return {"index": idx, "error": str(e)}
        
        tasks = [run_single(i, inp) for i, inp in enumerate(inputs)]
        all_results = await asyncio.gather(*tasks)
        
        for res in all_results:
            if "error" in res:
                errors.append(res)
            else:
                results.append(res)
        
        return {
            "success": len(errors) == 0,
            "total": len(inputs),
            "succeeded": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }

    # ==========================================
    # MODEL DISCOVERY
    # ==========================================
    
    @tool(
        name="replicate_search_models",
        description="Search for models on Replicate",
        category="replicate"
    )
    async def search_models(
        self,
        query: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search for models.
        
        Args:
            query: Search query
            limit: Max results
        """
        try:
            result = await self._request(
                "GET",
                f"/search?query={query}&limit={limit}"
            )
            
            models = result.get("models", [])
            
            return {
                "query": query,
                "count": len(models),
                "models": [
                    {
                        "id": m.get("id") or f"{m.get('owner')}/{m.get('name')}",
                        "description": m.get("description", "")[:200],
                        "run_count": m.get("run_count"),
                        "cover_image": m.get("cover_image_url")
                    }
                    for m in models
                ]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="replicate_get_model_info",
        description="Get detailed information about a model",
        category="replicate"
    )
    async def get_model_info(
        self,
        model: str
    ) -> Dict[str, Any]:
        """
        Get model details including input schema.
        
        Args:
            model: Model name (owner/model)
        """
        model = self._resolve_model(model)
        
        try:
            result = await self._request("GET", f"/models/{model}")
            
            latest_version = result.get("latest_version", {})
            schema = latest_version.get("openapi_schema", {})
            input_schema = schema.get("components", {}).get("schemas", {}).get("Input", {})
            
            return {
                "model": model,
                "description": result.get("description"),
                "run_count": result.get("run_count"),
                "url": result.get("url"),
                "latest_version": latest_version.get("id"),
                "input_schema": input_schema.get("properties", {}),
                "required_inputs": input_schema.get("required", [])
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="replicate_list_predictions",
        description="List recent predictions",
        category="replicate"
    )
    async def list_predictions(
        self,
        limit: int = 50
    ) -> Dict[str, Any]:
        """List recent predictions."""
        try:
            result = await self._request("GET", "/predictions")
            
            predictions = result.get("results", [])[:limit]
            
            return {
                "count": len(predictions),
                "predictions": [
                    {
                        "id": p.get("id"),
                        "model": p.get("model"),
                        "status": p.get("status"),
                        "created_at": p.get("created_at"),
                        "completed_at": p.get("completed_at")
                    }
                    for p in predictions
                ]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================
    # TRAINING / FINE-TUNING
    # ==========================================
    
    @tool(
        name="replicate_create_training",
        description="Start a model training/fine-tuning job",
        category="replicate"
    )
    async def create_training(
        self,
        model: str,
        version: str,
        destination: str,
        input_params: Dict[str, Any],
        webhook_url: str = None
    ) -> Dict[str, Any]:
        """
        Start a training job.
        
        Args:
            model: Base model to train (owner/model)
            version: Model version ID
            destination: Destination for trained model (owner/model)
            input_params: Training inputs (train_data URL, etc.)
            webhook_url: Webhook for training completion
        """
        model = self._resolve_model(model)
        
        payload = {
            "destination": destination,
            "input": input_params
        }
        
        if webhook_url:
            payload["webhook"] = webhook_url
        
        try:
            result = await self._request(
                "POST",
                f"/models/{model}/versions/{version}/trainings",
                payload
            )
            
            return {
                "success": True,
                "training_id": result.get("id"),
                "status": result.get("status"),
                "destination": destination,
                "urls": result.get("urls", {})
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==========================================
    # MODEL CHAINING (from printify_clean Playground)
    # ==========================================
    
    @tool(
        name="replicate_chain_models",
        description="Chain multiple AI models together, passing output from one to the next",
        category="replicate"
    )
    async def chain_models(
        self,
        steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Chain multiple AI models together in a pipeline.
        
        From printify_clean's Playground model chaining feature.
        
        Each step can use output from previous step.
        Supported step types:
        - image_generation: Generate image from text
        - image_editing: Edit previous image
        - video_generation: Generate video from text/image
        - text_generation: Generate text
        
        Args:
            steps: List of step configurations, each with:
                - type: "image_generation" | "image_editing" | "video_generation" | "text_generation"
                - prompt: The prompt for generation
                - model: Optional model override
                - use_previous: Whether to use previous step's output (default: True)
                
        Example:
            await chain_models([
                {"type": "image_generation", "prompt": "A sunset over mountains"},
                {"type": "image_editing", "prompt": "Add a dramatic sky"},
                {"type": "video_generation", "prompt": "Cinematic camera movement"}
            ])
            
        Returns:
            {"success": bool, "results": list, "final_output": str}
        """
        try:
            results = []
            previous_output = None
            
            for idx, step in enumerate(steps):
                step_type = step.get("type")
                prompt = step.get("prompt", "")
                use_previous = step.get("use_previous", True)
                model_override = step.get("model")
                
                logger.info(f"🔗 Chain Step {idx + 1}/{len(steps)}: {step_type}")
                
                step_result = {
                    "step": idx + 1,
                    "type": step_type,
                    "prompt": prompt,
                    "success": False,
                    "output": None
                }
                
                try:
                    if step_type == "image_generation":
                        # Generate image
                        model = model_override or "prunaai/flux-fast"
                        inputs = {"prompt": prompt}
                        
                        result = await self.run_model(model=model, inputs=inputs)
                        
                        if result.get("success"):
                            output = result.get("output")
                            if isinstance(output, list):
                                output = output[0]
                            previous_output = output
                            step_result["success"] = True
                            step_result["output"] = output
                    
                    elif step_type == "image_editing":
                        # Edit image using previous output
                        model = model_override or "hardikdava/flux-image-editing"
                        
                        if use_previous and previous_output:
                            inputs = {
                                "image": previous_output,
                                "prompt": prompt
                            }
                        else:
                            inputs = {"prompt": prompt}
                        
                        result = await self.run_model(model=model, inputs=inputs)
                        
                        if result.get("success"):
                            output = result.get("output")
                            if isinstance(output, list):
                                output = output[0]
                            previous_output = output
                            step_result["success"] = True
                            step_result["output"] = output
                    
                    elif step_type == "video_generation":
                        # Generate video
                        model = model_override or "kwaivgi/kling-v2.5-turbo-pro"
                        
                        inputs = {"prompt": prompt}
                        if use_previous and previous_output:
                            # Use previous image as starting frame
                            inputs["image"] = previous_output
                        
                        result = await self.run_model(model=model, inputs=inputs, timeout=900)
                        
                        if result.get("success"):
                            output = result.get("output")
                            if isinstance(output, list):
                                output = output[0]
                            previous_output = output
                            step_result["success"] = True
                            step_result["output"] = output
                    
                    elif step_type == "text_generation":
                        # Generate text
                        model = model_override or "meta/meta-llama-3-70b-instruct"
                        
                        inputs = {"prompt": prompt}
                        
                        result = await self.run_model(model=model, inputs=inputs)
                        
                        if result.get("success"):
                            output = result.get("output")
                            if isinstance(output, list):
                                output = "".join(output)
                            previous_output = output
                            step_result["success"] = True
                            step_result["output"] = output
                    
                    else:
                        step_result["error"] = f"Unknown step type: {step_type}"
                        
                except Exception as e:
                    step_result["error"] = str(e)
                    logger.error(f"Chain step {idx + 1} failed: {e}")
                
                results.append(step_result)
                
                # Stop if a step fails
                if not step_result.get("success"):
                    logger.warning(f"Chain stopped at step {idx + 1}")
                    break
            
            success = all(r.get("success") for r in results)
            
            return {
                "success": success,
                "results": results,
                "final_output": previous_output,
                "steps_completed": sum(1 for r in results if r.get("success")),
                "total_steps": len(steps)
            }
            
        except Exception as e:
            logger.error(f"Model chain failed: {e}")
            return {"success": False, "error": str(e)}
    
    @tool(
        name="replicate_get_training",
        description="Get training job status",
        category="replicate"
    )
    async def get_training(
        self,
        training_id: str
    ) -> Dict[str, Any]:
        """Get training status."""
        try:
            result = await self._request("GET", f"/trainings/{training_id}")
            
            return {
                "training_id": result.get("id"),
                "status": result.get("status"),
                "model": result.get("model"),
                "output": result.get("output"),
                "error": result.get("error"),
                "logs": result.get("logs", "")[-1000:],
                "metrics": result.get("metrics"),
                "created_at": result.get("created_at"),
                "completed_at": result.get("completed_at")
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================
    # FILE HANDLING
    # ==========================================
    
    @tool(
        name="replicate_upload_file",
        description="Upload a file to Replicate for use as input",
        category="replicate"
    )
    async def upload_file(
        self,
        file_path: str,
        content_type: str = None
    ) -> Dict[str, Any]:
        """
        Upload a file to Replicate.
        
        Args:
            file_path: Path to local file
            content_type: MIME type (auto-detected if not provided)
        """
        path = Path(file_path)
        if not path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}
        
        # Detect content type
        if not content_type:
            ext = path.suffix.lower()
            content_types = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp",
                ".mp4": "video/mp4",
                ".mp3": "audio/mpeg",
                ".wav": "audio/wav",
                ".zip": "application/zip"
            }
            content_type = content_types.get(ext, "application/octet-stream")
        
        try:
            # Upload using multipart form
            url = f"{self.base_url}/files"
            
            async with aiohttp.ClientSession() as session:
                with open(path, "rb") as f:
                    data = aiohttp.FormData()
                    data.add_field(
                        "content",
                        f,
                        filename=path.name,
                        content_type=content_type
                    )
                    
                    async with session.post(
                        url,
                        headers={"Authorization": f"Bearer {self.api_token}"},
                        data=data
                    ) as response:
                        result = await response.json()
                        
                        if response.status >= 400:
                            return {"success": False, "error": str(result)}
                        
                        return {
                            "success": True,
                            "file_id": result.get("id"),
                            "url": result.get("urls", {}).get("get"),
                            "content_type": content_type
                        }
                        
        except Exception as e:
            return {"success": False, "error": str(e)}


# ==========================================
# WEBHOOK HANDLER (for FastAPI integration)
# ==========================================

class ReplicateWebhookHandler:
    """Handle incoming Replicate webhooks."""
    
    def __init__(self, secret: Optional[str] = None):
        self.secret = secret
        self.callbacks: Dict[str, List[Callable]] = {
            "start": [],
            "output": [],
            "logs": [],
            "completed": []
        }
    
    def on_start(self, callback: Callable):
        """Register callback for prediction start."""
        self.callbacks["start"].append(callback)
    
    def on_output(self, callback: Callable):
        """Register callback for prediction output."""
        self.callbacks["output"].append(callback)
    
    def on_completed(self, callback: Callable):
        """Register callback for prediction completion."""
        self.callbacks["completed"].append(callback)
    
    async def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming webhook payload."""
        prediction_id = payload.get("id")
        status = payload.get("status")
        
        # Determine event type
        if status == "starting":
            event = "start"
        elif status in ["succeeded", "failed", "canceled"]:
            event = "completed"
        elif payload.get("output"):
            event = "output"
        else:
            event = "logs"
        
        # Call registered callbacks
        for callback in self.callbacks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(payload)
                else:
                    callback(payload)
            except Exception as e:
                logger.error(f"Webhook callback error: {e}")
        
        return {
            "received": True,
            "prediction_id": prediction_id,
            "event": event,
            "status": status
        }


# Factory function
def create_replicate_advanced_tools(
    api_token: str = None,
    webhook_url: str = None
) -> ReplicateAdvancedTools:
    """Create ReplicateAdvancedTools instance."""
    return ReplicateAdvancedTools(
        api_token=api_token,
        default_webhook_url=webhook_url
    )


# ==========================================
# FILE DOWNLOAD UTILITIES (from printify_clean)
# ==========================================

async def download_replicate_output(
    url: str,
    output_path: Optional[str] = None,
    timeout: int = 300,
    chunk_size: int = 8192
) -> Optional[str]:
    """
    Download file from Replicate output URL.
    
    Args:
        url: URL to download from
        output_path: Where to save file (uses temp if None)
        timeout: Request timeout in seconds
        chunk_size: Download chunk size in bytes
        
    Returns:
        Path to downloaded file, or None if failed
    """
    import tempfile
    import os
    from urllib.parse import urlparse
    
    try:
        logger.info(f"⬇️ Downloading from {url[:50]}...")
        
        # Determine output path
        if not output_path:
            # Extract extension from URL
            parsed = urlparse(url)
            path = parsed.path
            ext = os.path.splitext(path)[1] or ".bin"
            if not ext.startswith("."):
                ext = "." + ext
            
            temp_dir = Path(tempfile.mkdtemp(prefix="replicate_download_"))
            output_path = str(temp_dir / f"output{ext}")
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Download with streaming
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                if response.status != 200:
                    logger.error(f"❌ Download failed: HTTP {response.status}")
                    return None
                
                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0
                
                with open(output_path, "wb") as f:
                    async for chunk in response.content.iter_chunked(chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
        
        # Format size
        if downloaded < 1024:
            size_str = f"{downloaded} B"
        elif downloaded < 1024 * 1024:
            size_str = f"{downloaded / 1024:.1f} KB"
        else:
            size_str = f"{downloaded / (1024 * 1024):.1f} MB"
        
        logger.info(f"✅ Downloaded {size_str} to {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"❌ Download failed: {e}")
        return None


def create_temp_directory(prefix: str = "replicate_") -> Path:
    """
    Create temporary directory for Replicate outputs.
    
    Args:
        prefix: Prefix for the directory name
        
    Returns:
        Path to the temporary directory
    """
    import tempfile
    temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
    logger.info(f"📁 Created temp directory: {temp_dir}")
    return temp_dir


def cleanup_temp_files(paths: List[str]) -> int:
    """
    Clean up temporary files.
    
    Args:
        paths: List of file paths to delete
        
    Returns:
        Number of files successfully deleted
    """
    import os
    deleted = 0
    for path in paths:
        try:
            if os.path.exists(path):
                os.remove(path)
                deleted += 1
        except Exception as e:
            logger.warning(f"Failed to delete {path}: {e}")
    
    logger.info(f"🗑️ Cleaned up {deleted} temporary files")
    return deleted
