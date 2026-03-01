"""
Replicate Model Catalog
=======================

Centralized catalog of AI model shortcuts for Replicate API.
Shared across replicate_universal.py and replicate_advanced.py.

Last updated: February 2026
"""

# ═══════════════════════════════════════════════════════════════════════════
# COMPREHENSIVE MODEL SHORTCUTS
# ═══════════════════════════════════════════════════════════════════════════

REPLICATE_MODEL_CATALOG = {
    # ═══════════════════════════════════════════════════════════════
    # IMAGE GENERATION - Multiple quality tiers
    # ═══════════════════════════════════════════════════════════════
    "image": "prunaai/flux-fast",  # Fastest - 4 steps
    "image_fast": "prunaai/flux-fast",
    "image_pro": "black-forest-labs/flux-1.1-pro",
    "image_quality": "black-forest-labs/flux-1.1-pro",
    "image_4k": "bytedance/seedream-4",
    "image_safe": "bria/image-3.2",  # Commercial-safe
    "flux": "black-forest-labs/flux-schnell",
    "flux_fast": "prunaai/flux-fast",
    "flux_pro": "black-forest-labs/flux-1.1-pro",
    "flux_kontext": "black-forest-labs/flux-kontext-pro",  # Face-aware
    "sdxl": "stability-ai/sdxl",
    "sd3": "stability-ai/sd3.5-large",
    "ideogram": "ideogram-ai/ideogram-v2",
    "ideogram_v3": "ideogram-ai/ideogram-v3",
    "ideogram_text": "ideogram-ai/ideogram-v3",  # Best for text in images
    "recraft": "recraft-ai/recraft-v3",
    "recraft_svg": "recraft-ai/recraft-v3-svg",
    "recraft_vector": "recraft-ai/recraft-v3-svg",
    "seedream": "bytedance/seedream-4",
    "imagen4": "google/imagen-4-ultra",
    "realistic": "lucataco/juggernaut-xl-v9",
    "photorealistic": "lucataco/juggernaut-xl-v9",
    "anime": "stability-ai/sdxl",
    "artistic": "stability-ai/sdxl",
    
    # ═══════════════════════════════════════════════════════════════
    # MARKETING / ADS
    # ═══════════════════════════════════════════════════════════════
    "ads": "pipeline-examples/ads-for-products",
    "product_ad": "pipeline-examples/ads-for-products",
    "ads_for_products": "pipeline-examples/ads-for-products",
    "static_ad": "loolau/flux-static-ads",
    "flux_ads": "loolau/flux-static-ads",
    "logo_context": "subhash25rawat/logo-in-context",
    "ad_inpaint": "logerzhu/ad-inpaint",
    
    # ═══════════════════════════════════════════════════════════════
    # IMAGE EDITING & ENHANCEMENT
    # ═══════════════════════════════════════════════════════════════
    "remove_bg": "cjwbw/rembg",
    "background_remove": "cjwbw/rembg",
    "upscale": "nightmareai/real-esrgan",
    "upscale_4x": "nightmareai/real-esrgan",
    "upscale_creative": "philz1337x/clarity-upscaler",
    "upscale_face": "tencentarc/gfpgan",
    "restore_face": "tencentarc/gfpgan",
    "face_restore": "tencentarc/gfpgan",
    "inpaint": "cjwbw/stable-diffusion-v2-inpainting",
    "edit_image": "hardikdava/flux-image-editing",
    "flux_edit": "hardikdava/flux-image-editing",
    "edit_fast": "reve/edit-fast",
    "gemini_edit": "google/nano-banana",
    "nano_banana": "google/nano-banana",
    "next_scene": "lucataco/next-scene",
    "img2img": "stability-ai/sdxl",
    "colorize": "arielreplicate/deoldify",
    "outpaint": "stability-ai/stable-diffusion-inpainting",
    "style_transfer": "lucataco/neural-style-tf",
    "sketch_to_image": "jagilley/controlnet-scribble",
    "depth_to_image": "jagilley/controlnet-depth",
    "pose_to_image": "jagilley/controlnet-openpose",
    
    # ═══════════════════════════════════════════════════════════════
    # VIDEO GENERATION & EDITING
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
    # 3D GENERATION
    # ═══════════════════════════════════════════════════════════════
    # Fast 3D (recommended)
    "3d": "stabilityai/stable-fast-3d",  # FASTEST - <1 second
    "3d_fast": "stabilityai/stable-fast-3d",
    "stable_fast_3d": "stabilityai/stable-fast-3d",
    
    # Premium quality 3D
    "3d_pro": "tencent/hunyuan3d-2",
    "hunyuan3d": "tencent/hunyuan3d-2",
    "hunyuan3d_21": "ndreca/hunyuan3d-2.1",  # Quality mode
    
    # Image-to-3D models
    "3d_gen": "firtoz/trellis",
    "trellis": "firtoz/trellis",
    "image_to_3d": "cjwbw/instant-mesh",
    "instant_mesh": "cjwbw/instant-mesh",
    
    # Text-to-3D models
    "text_to_3d": "jd7h/luciddreamer",
    "luciddreamer": "jd7h/luciddreamer",
    "mvdream": "adirik/mvdream",
    "shap_e": "cjwbw/shap-e",
    
    # Mesh generation
    "mesh": "cjwbw/instant-mesh",
    "wonder3d": "camenduru/wonder3d",
    "tripo": "lucataco/tripo3d",
    "triposr": "tripo/tripo-sr-v2",
    "craftsman": "adirik/craftsman",
    
    # Other 3D tools
    "rodin": "hyper3d/rodin",
    "lgm": "ashawkey/lgm",  # Gaussian splatting
    "morphix3d": "subhash25rawat/morphix3d",
    "vggt": "vufinder/vggt-1b",  # Scene generation
    
    # Multiview generation
    "multiview": "jd7h/zero123plusplus",
    "zero123": "jd7h/zero123plusplus",
    
    # Texturing
    "texture_3d": "adirik/texture",
    "text2tex": "adirik/text2tex",
    
    # ═══════════════════════════════════════════════════════════════
    # AD & MARKETING SPECIFIC
    # ═══════════════════════════════════════════════════════════════
    "ad_image": "loolau/flux-static-ads",
    "ad_banner": "ideogram-ai/ideogram-v3",  # Good for text overlays
    "product_shot": "prunaai/flux-fast",
    "product_mockup": "fofr/product-mockup",
    "lifestyle_shot": "black-forest-labs/flux-1.1-pro",
    "ad_video": "openai/sora-2",
    "promo_video": "kwaivgi/kling-v2.5-turbo-pro",
    "social_content": "prunaai/flux-fast",
    
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
VALID_ASPECT_RATIOS = [
    "1:1", "16:9", "21:9", "3:2", "2:3", "4:5", "5:4", "3:4", "4:3", "9:16", "9:21"
]

# Model categories for filtering
MODEL_CATEGORIES = {
    "image": ["image", "image_fast", "image_pro", "flux", "sdxl", "sd3", "ideogram", "recraft"],
    "video": ["video", "video_fast", "video_pro", "kling", "luma", "sora", "veo", "minimax"],
    "audio": ["music", "tts", "whisper", "bark", "voice_clone", "audio_ldm"],
    "3d": ["3d", "3d_fast", "3d_pro", "trellis", "hunyuan3d", "mesh"],
    "code": ["code", "codellama", "sql"],
    "text": ["llm", "llama", "mistral", "mixtral", "chat"],
    "vision": ["vision", "llava", "blip", "ocr"],
}


def get_model(shortcut: str) -> str:
    """Get full model name from shortcut."""
    return REPLICATE_MODEL_CATALOG.get(shortcut, shortcut)


def get_shortcuts_for_category(category: str) -> list:
    """Get all shortcuts for a model category."""
    return MODEL_CATEGORIES.get(category, [])


def search_models(query: str) -> list:
    """Search for models by name or description."""
    query_lower = query.lower()
    matches = []
    for shortcut, model in REPLICATE_MODEL_CATALOG.items():
        if query_lower in shortcut or query_lower in model.lower():
            matches.append({"shortcut": shortcut, "model": model})
    return matches
