"""
Universal AI Editor
====================

AI-powered editing for any file type using Replicate models.
Supports images, videos, audio, 3D models, and text.
Automatically selects the right models based on the task.
"""

import asyncio
import logging
import os
import re
import uuid
import json
import httpx
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime
from enum import Enum

from .core import tool, ToolBase

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# STATUS UPDATE CALLBACK TYPE FOR REAL-TIME PROGRESS
# ═══════════════════════════════════════════════════════════════════

# Status callback type: (step: str, progress: float, message: str) -> None
StatusCallback = Optional[Callable[[str, float, str], None]]


class MediaType(Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"
    THREE_D = "3d"
    UNKNOWN = "unknown"


# ═══════════════════════════════════════════════════════════════════
# REPLICATE MODEL CATALOG - Organized by task and media type
# ═══════════════════════════════════════════════════════════════════

REPLICATE_MODELS = {
    # ─────────────────────────────────────────────────────────────
    # IMAGE EDITING MODELS
    # ─────────────────────────────────────────────────────────────
    "image": {
        # Background operations
        "remove_background": {
            "model": "lucataco/remove-bg:95fcc2a26d3899cd6c2691c900465aaeff466285a65c14638cc5f36f34befaf1",
            "description": "Remove background from image",
            "input_key": "image"
        },
        "replace_background": {
            "model": "stability-ai/stable-diffusion-img2img:15a3689ee13b0d2616e98820eca31d4c3abcd36672df6afce5cb6feb1d66087d",
            "description": "Replace background with AI-generated scene",
            "input_key": "image"
        },
        
        # Enhancement & Restoration
        "upscale": {
            "model": "nightmareai/real-esrgan:f121d640bd286e1fdc67f9799164c1d5be36ff74576ee11c803ae5b665dd46aa",
            "description": "Upscale image 4x with AI enhancement",
            "input_key": "image"
        },
        "enhance": {
            "model": "tencentarc/gfpgan:0fbacf7afc6c144e5be9767cff80f25aff23e52b0708f17e20f9879b2f21516c",
            "description": "Enhance and restore faces in images",
            "input_key": "img"
        },
        "colorize": {
            "model": "arielreplicate/deoldify_image:0da600fab0c45a66211339f1c16b71345d22f26ef5fea3dca1bb90bb5711e950",
            "description": "Colorize black and white images",
            "input_key": "input_image"
        },
        "denoise": {
            "model": "megvii-research/nafnet:f91e9a6b0e55d9fb16f8d654ba5f08e65d01cc7ac60b86d0cc84ce31c8dbec1f",
            "description": "Remove noise from images",
            "input_key": "image"
        },
        
        # Style Transfer & Artistic
        "style_transfer": {
            "model": "logerzhu/ad-inpaint:b1c17d148455c1fda435ababe9ab1e03bc0d917cc3cf4251916f22c45c83c7df",
            "description": "Apply artistic style to image",
            "input_key": "image_path"
        },
        "cartoonize": {
            "model": "cjwbw/informative-drawings:4d633c9e8b7d81e9f1b8a7d2bbee9df17d1e8c5d5a6f7c8d9e0a1b2c3d4e5f6g",
            "description": "Convert image to cartoon/sketch style",
            "input_key": "image"
        },
        
        # Editing & Manipulation
        "inpaint": {
            "model": "stability-ai/stable-diffusion-inpainting:95b7223104132402a9ae91cc677285bc5eb997834bd2349fa486f53910fd68b3",
            "description": "Edit parts of image with AI (inpainting)",
            "input_key": "image"
        },
        "outpaint": {
            "model": "andreasjansson/stable-diffusion-inpainting:e490d072a34a94a11e9711ed5a6ba621c3fab884eda1665d9d3a282d65a21f4",
            "description": "Extend image beyond its borders",
            "input_key": "image"
        },
        "object_removal": {
            "model": "sczhou/codeformer:7de2ea26c616d5bf2245ad0d5e24f0ff9a6204578a5c876db53142edd9d2cd56",
            "description": "Remove unwanted objects from image",
            "input_key": "image"
        },
        
        # Generation from image
        "image_to_image": {
            "model": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            "description": "Transform image based on prompt",
            "input_key": "image"
        },
        "controlnet": {
            "model": "jagilley/controlnet-canny:aff48af9c68d162388d230a2ab003f68d2638a88e22e05f1d35a11e1c9db4a2",
            "description": "Generate image following structure of input",
            "input_key": "image"
        }
    },
    
    # ─────────────────────────────────────────────────────────────
    # VIDEO EDITING MODELS
    # ─────────────────────────────────────────────────────────────
    "video": {
        # Enhancement
        "upscale": {
            "model": "lucataco/real-esrgan-video:c26aa5ff3d9f98f5c5a1fb7f1c91a8757ae2d8f8d3b7a5f6c7d8e9a0b1c2d3e4",
            "description": "Upscale video resolution",
            "input_key": "video"
        },
        "interpolate": {
            "model": "pollinations/rife-video-interpolation:b577c92d3e8d14e11c539f8f05df6e5e6e1e9f7c6d5b4a3c2b1a0d9e8f7c6b5",
            "description": "Increase video framerate with interpolation",
            "input_key": "video"
        },
        "stabilize": {
            "model": "lucataco/video-stabilization:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
            "description": "Stabilize shaky video",
            "input_key": "video"
        },
        
        # Generation
        "image_to_video": {
            "model": "stability-ai/stable-video-diffusion:3f0457e4619daac51203dedb472816fd4af51f3149fa7a9e0b5ffcf1b8172438",
            "description": "Animate an image into a video",
            "input_key": "input_image"
        },
        "text_to_video": {
            "model": "anotherjesse/zeroscope-v2-xl:71996d331e8ede8ef7bd76eba9fae076d31792e4ddf4ad057779b443d6aea62f",
            "description": "Generate video from text prompt",
            "input_key": "prompt"
        },
        "video_to_video": {
            "model": "chenxwh/video-to-video:a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef12345678",
            "description": "Transform video style with AI",
            "input_key": "video"
        },
        
        # Effects
        "remove_background": {
            "model": "lucataco/video-background-removal:73d2128a371922d5d1abf0712a1d974be0e4e2358cc1218e4e34714767232bac",
            "description": "Remove background from video",
            "input_key": "video"
        },
        "slow_motion": {
            "model": "pollinations/rife-video-interpolation:b577c92d3e8d14e11c539f8f05df6e5e6e1e9f7c6d5b4a3c2b1a0d9e8f7c6b5",
            "description": "Create slow motion effect",
            "input_key": "video"
        },
        
        # Video composition
        "add_captions": {
            "model": "openai/whisper:4d50797290df275329f202e48c76360b3f22b08d28c65f8f0a3e0c20c71cf2ca",
            "description": "Auto-generate captions from audio in video",
            "input_key": "audio"
        },
        "add_music": {
            "model": "meta/musicgen:671ac645ce5e552cc63a54a2bbff63fcf798043055d2dac5fc9e36a837eedcfb",
            "description": "Generate and add background music to video",
            "input_key": "prompt"
        },
        "add_voiceover": {
            "model": "suno-ai/bark:b76242b40d67c76ab6742e987628a2a9ac019e11d56ab96c4e91ce03b79b2787",
            "description": "Generate and add AI voiceover to video",
            "input_key": "prompt"
        }
    },
    
    # ─────────────────────────────────────────────────────────────
    # AUDIO EDITING MODELS
    # ─────────────────────────────────────────────────────────────
    "audio": {
        # Separation & Extraction
        "separate_vocals": {
            "model": "cjwbw/demucs:25a173108cff36ef9f80f854c162d01df9e6528be175794b81b7a0f3b7527c5d",
            "description": "Separate vocals from music",
            "input_key": "audio",
            "output_type": "stems"
        },
        "extract_stems": {
            "model": "cjwbw/demucs:25a173108cff36ef9f80f854c162d01df9e6528be175794b81b7a0f3b7527c5d",
            "description": "Extract drums, bass, vocals, other from audio",
            "input_key": "audio",
            "output_type": "stems"
        },
        
        # Enhancement
        "enhance": {
            "model": "lucataco/resemble-enhance:df0c80700e67c4e4db38595af8f26b18ef34b167f60de9b80cc68c630fa5506e",
            "description": "Enhance and clean audio quality",
            "input_key": "audio"
        },
        "audio_enhance": {
            "model": "lucataco/resemble-enhance:df0c80700e67c4e4db38595af8f26b18ef34b167f60de9b80cc68c630fa5506e",
            "description": "Enhance and clean audio quality",
            "input_key": "audio"
        },
        "denoise": {
            "model": "lucataco/resemble-enhance:df0c80700e67c4e4db38595af8f26b18ef34b167f60de9b80cc68c630fa5506e",
            "description": "Remove noise from audio",
            "input_key": "audio",
            "extra_params": {"denoise": True}
        },
        
        # Transcription
        "transcribe": {
            "model": "openai/whisper:4d50797290df275329f202e48c76360b3f22b08d28c65f8f0a3e0c20c71cf2ca",
            "description": "Transcribe audio to text",
            "input_key": "audio",
            "output_type": "text"
        },
        
        # Generation
        "text_to_speech": {
            "model": "suno-ai/bark:b76242b40d67c76ab6742e987628a2a9ac019e11d56ab96c4e91ce03b79b2787",
            "description": "Generate speech from text",
            "input_key": "prompt",
            "requires_text": True
        },
        "voice_clone": {
            "model": "lucataco/xtts-v2:684bc3855b37866c0c65add2ff39c78f3dea3f4ff103a436465326e0f438d55e",
            "description": "Clone voice and generate speech",
            "input_key": "text",
            "requires_audio": True,
            "requires_text": True
        },
        "music_generation": {
            "model": "meta/musicgen:671ac645ce5e552cc63a54a2bbff63fcf798043055d2dac5fc9e36a837eedcfb",
            "description": "Generate music from text description",
            "input_key": "prompt",
            "requires_text": True
        },
        
        # Transformation
        "change_pitch": {
            "model": "audio-effects/pitch-shift:a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
            "description": "Change audio pitch",
            "input_key": "audio"
        },
        "speed_change": {
            "model": "audio-effects/tempo-change:b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0",
            "description": "Change audio speed/tempo",
            "input_key": "audio"
        }
    },
    
    # ─────────────────────────────────────────────────────────────
    # 3D MODEL EDITING
    # ─────────────────────────────────────────────────────────────
    "3d": {
        "image_to_3d": {
            "model": "cjwbw/shap-e:5957069d5c509126a73c7cb68abcddbb985aeefa4d318e7c63ec1352ce6da68c",
            "description": "Generate 3D model from image",
            "input_key": "image"
        },
        "text_to_3d": {
            "model": "cjwbw/shap-e:5957069d5c509126a73c7cb68abcddbb985aeefa4d318e7c63ec1352ce6da68c",
            "description": "Generate 3D model from text",
            "input_key": "prompt"
        },
        "mesh_refinement": {
            "model": "cjwbw/shap-e:5957069d5c509126a73c7cb68abcddbb985aeefa4d318e7c63ec1352ce6da68c",
            "description": "Refine and smooth 3D mesh",
            "input_key": "prompt"
        },
        "texture_generation": {
            "model": "cjwbw/shap-e:5957069d5c509126a73c7cb68abcddbb985aeefa4d318e7c63ec1352ce6da68c",
            "description": "Generate textures for 3D model",
            "input_key": "prompt"
        }
    },
    
    # ─────────────────────────────────────────────────────────────
    # TEXT/DOCUMENT PROCESSING
    # ─────────────────────────────────────────────────────────────
    "text": {
        "rewrite": {
            "model": "USE_OPENAI",
            "description": "Rewrite text with AI",
            "input_key": "prompt",
            "use_llm": True,
            "system_prompt": "Rewrite the following text to improve clarity, flow, and readability while preserving the original meaning."
        },
        "summarize": {
            "model": "USE_OPENAI",
            "description": "Summarize text content",
            "input_key": "prompt",
            "use_llm": True,
            "system_prompt": "Summarize the following text concisely, capturing the key points and main ideas."
        },
        "translate": {
            "model": "USE_OPENAI",
            "description": "Translate text to another language",
            "input_key": "prompt",
            "use_llm": True,
            "system_prompt": "You are a professional translator. Translate the following text accurately, preserving meaning, tone, and formatting."
        },
        "expand": {
            "model": "USE_OPENAI",
            "description": "Expand and elaborate on text",
            "input_key": "prompt",
            "use_llm": True,
            "system_prompt": "Expand and elaborate on the following text, adding more detail and context while maintaining the original tone and message."
        },
        "format": {
            "model": "USE_OPENAI",
            "description": "Format and structure text",
            "input_key": "prompt",
            "use_llm": True,
            "system_prompt": "Format and structure the following text professionally. Use appropriate headings, bullet points, and organization."
        },
        "code_explain": {
            "model": "USE_OPENAI",
            "description": "Explain code in plain language",
            "input_key": "prompt",
            "use_llm": True,
            "system_prompt": "Explain the following code in clear, simple language. Describe what it does, how it works, and any important concepts."
        },
        "code_refactor": {
            "model": "USE_OPENAI",
            "description": "Refactor and improve code",
            "input_key": "prompt",
            "use_llm": True,
            "system_prompt": "Refactor the following code to improve readability, performance, and maintainability. Explain the changes made."
        },
        "ocr": {
            "model": "abiruyt/text-extract-ocr:a524caeaa23495bc9edc805ab08ab5fe943afd3febed884a4f3747aa32e9cd61",
            "description": "Extract text from image",
            "input_key": "image"
        }
    }
}


# Task keyword mappings for auto-detection
TASK_KEYWORDS = {
    # Image tasks
    "remove background": ("image", "remove_background"),
    "remove bg": ("image", "remove_background"),
    "transparent": ("image", "remove_background"),
    "no background": ("image", "remove_background"),
    "cut out": ("image", "remove_background"),
    "background removal": ("image", "remove_background"),
    "remove the background": ("image", "remove_background"),
    "upscale": ("image", "upscale"),
    "enhance": ("image", "enhance"),
    "improve quality": ("image", "upscale"),
    "higher resolution": ("image", "upscale"),
    "4k": ("image", "upscale"),
    "hd": ("image", "upscale"),
    "sharpen": ("image", "upscale"),
    "colorize": ("image", "colorize"),
    "add color": ("image", "colorize"),
    "black and white to color": ("image", "colorize"),
    "realistic colors": ("image", "colorize"),
    "natural colors": ("image", "colorize"),
    "denoise": ("image", "denoise"),
    "remove noise": ("image", "denoise"),
    "noise reduction": ("audio", "denoise"),
    "clean audio": ("audio", "denoise"),
    "style transfer": ("image", "image_to_image"),
    "artistic style": ("image", "image_to_image"),
    "apply style": ("image", "image_to_image"),
    "cartoon": ("image", "image_to_image"),
    "sketch": ("image", "image_to_image"),
    "inpaint": ("image", "image_to_image"),
    "edit part": ("image", "image_to_image"),
    "remove object": ("image", "image_to_image"),
    "extend": ("image", "outpaint"),
    "outpaint": ("image", "outpaint"),
    "transform": ("image", "image_to_image"),
    "change style": ("image", "image_to_image"),
    
    # Image adjustments (brightness, contrast, etc.)
    "brighter": ("image", "adjust"),
    "brighten": ("image", "adjust"),
    "make it brighter": ("image", "adjust"),
    "increase brightness": ("image", "adjust"),
    "darker": ("image", "adjust"),
    "darken": ("image", "adjust"),
    "make it darker": ("image", "adjust"),
    "decrease brightness": ("image", "adjust"),
    "more contrast": ("image", "adjust"),
    "increase contrast": ("image", "adjust"),
    "punchier": ("image", "adjust"),
    "less contrast": ("image", "adjust"),
    "decrease contrast": ("image", "adjust"),
    "flatter": ("image", "adjust"),
    "more saturated": ("image", "adjust"),
    "saturate": ("image", "adjust"),
    "vibrant": ("image", "adjust"),
    "colorful": ("image", "adjust"),
    "richer colors": ("image", "adjust"),
    "desaturated": ("image", "adjust"),
    "desaturate": ("image", "adjust"),
    "muted": ("image", "adjust"),
    "muted colors": ("image", "adjust"),
    "warmer": ("image", "adjust"),
    "warm it up": ("image", "adjust"),
    "golden": ("image", "adjust"),
    "warm tones": ("image", "adjust"),
    "cooler": ("image", "adjust"),
    "cool it down": ("image", "adjust"),
    "blue tones": ("image", "adjust"),
    "cold tones": ("image", "adjust"),
    "sharper": ("image", "adjust"),
    "crisp": ("image", "adjust"),
    "more detail": ("image", "adjust"),
    "blur": ("image", "adjust"),
    "soften": ("image", "adjust"),
    "soft focus": ("image", "adjust"),
    "dreamy": ("image", "adjust"),
    
    # Video tasks
    "animate": ("video", "image_to_video"),
    "make video": ("video", "image_to_video"),
    "video from image": ("video", "image_to_video"),
    "motion": ("video", "image_to_video"),
    "stabilize": ("video", "stabilize"),
    "steady": ("video", "stabilize"),
    "slow motion": ("video", "slow_motion"),
    "slow down": ("video", "slow_motion"),
    "remove video background": ("video", "remove_background"),
    "video upscale": ("video", "upscale"),
    "higher fps": ("video", "interpolate"),
    "smooth video": ("video", "interpolate"),
    
    # Audio tasks
    "separate vocals": ("audio", "separate_vocals"),
    "remove vocals": ("audio", "separate_vocals"),
    "isolate voice": ("audio", "separate_vocals"),
    "extract stems": ("audio", "extract_stems"),
    "audio enhance": ("audio", "enhance"),
    "clean audio": ("audio", "denoise"),
    "remove noise audio": ("audio", "denoise"),
    "text to speech": ("audio", "text_to_speech"),
    "tts": ("audio", "text_to_speech"),
    "speak": ("audio", "text_to_speech"),
    "clone voice": ("audio", "voice_clone"),
    "voice clone": ("audio", "voice_clone"),
    "generate music": ("audio", "music_generation"),
    "make music": ("audio", "music_generation"),
    "create song": ("audio", "music_generation"),
    "transcribe": ("audio", "transcribe"),
    "transcript": ("audio", "transcribe"),
    "audio to text": ("audio", "transcribe"),
    "speech to text": ("audio", "transcribe"),
    
    # Video composition tasks
    "add music": ("video", "add_music"),
    "add background music": ("video", "add_music"),
    "add voiceover": ("video", "add_voiceover"),
    "add narration": ("video", "add_voiceover"),
    "add captions": ("video", "add_captions"),
    "add subtitles": ("video", "add_captions"),
    "auto captions": ("video", "add_captions"),
    
    # 3D tasks
    "image to 3d": ("3d", "image_to_3d"),
    "make 3d": ("3d", "image_to_3d"),
    "3d model from image": ("3d", "image_to_3d"),
    "3d model": ("3d", "image_to_3d"),
    "convert to 3d": ("3d", "image_to_3d"),
    "to 3d": ("3d", "image_to_3d"),
    "text to 3d": ("3d", "text_to_3d"),
    "generate 3d": ("3d", "text_to_3d"),
    "refine mesh": ("3d", "mesh_refinement"),
    "smooth mesh": ("3d", "mesh_refinement"),
    "add texture": ("3d", "texture_generation"),
    "texture 3d": ("3d", "texture_generation"),
    
    # Text tasks
    "rewrite": ("text", "rewrite"),
    "rephrase": ("text", "rewrite"),
    "paraphrase": ("text", "rewrite"),
    "summarize": ("text", "summarize"),
    "summary": ("text", "summarize"),
    "shorten": ("text", "summarize"),
    "translate": ("text", "translate"),
    "expand": ("text", "expand"),
    "elaborate": ("text", "expand"),
    "make longer": ("text", "expand"),
    "format": ("text", "format"),
    "structure": ("text", "format"),
    "ocr": ("text", "ocr"),
    "extract text": ("text", "ocr"),
    "read text": ("text", "ocr"),
    "explain code": ("text", "code_explain"),
    "code explanation": ("text", "code_explain"),
    "refactor code": ("text", "code_refactor"),
    "improve code": ("text", "code_refactor"),
}


class UniversalEditor:
    """
    Universal AI-powered editor for any media type.
    
    Automatically detects file type and task, selects appropriate
    Replicate models, and executes transformations.
    
    Supports status callbacks for real-time progress updates.
    """
    
    def __init__(self, replicate_token: Optional[str] = None, status_callback: StatusCallback = None):
        self.api_token = replicate_token or os.getenv("REPLICATE_API_TOKEN")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.output_dir = Path("data/files/edited")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.status_callback = status_callback
    
    def _update_status(self, step: str, progress: float, message: str):
        """Send status update if callback is set."""
        logger.info(f"📊 [{step}] {int(progress*100)}% - {message}")
        if self.status_callback:
            try:
                self.status_callback(step, progress, message)
            except Exception as e:
                logger.error(f"Status callback error: {e}")
    
    def detect_media_type(self, file_path: str) -> MediaType:
        """Detect media type from file extension."""
        ext = Path(file_path).suffix.lower()
        
        image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.svg'}
        video_exts = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv'}
        audio_exts = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma'}
        text_exts = {'.txt', '.md', '.doc', '.docx', '.pdf', '.rtf', '.html'}
        three_d_exts = {'.obj', '.glb', '.gltf', '.fbx', '.stl', '.ply', '.3ds'}
        
        if ext in image_exts:
            return MediaType.IMAGE
        elif ext in video_exts:
            return MediaType.VIDEO
        elif ext in audio_exts:
            return MediaType.AUDIO
        elif ext in text_exts:
            return MediaType.TEXT
        elif ext in three_d_exts:
            return MediaType.THREE_D
        else:
            return MediaType.UNKNOWN
    
    def detect_task(self, instruction: str, media_type: MediaType) -> Tuple[str, str, Dict]:
        """
        Detect the task from instruction and select appropriate model.
        
        Returns:
            (media_type, task_name, model_info)
        """
        instruction_lower = instruction.lower()
        
        # Check keyword mappings first
        for keyword, (detected_type, task) in TASK_KEYWORDS.items():
            if keyword in instruction_lower:
                if detected_type in REPLICATE_MODELS and task in REPLICATE_MODELS[detected_type]:
                    return detected_type, task, REPLICATE_MODELS[detected_type][task]
        
        # Fall back to media type defaults
        type_str = media_type.value
        if type_str in REPLICATE_MODELS:
            models = REPLICATE_MODELS[type_str]
            
            # Select most appropriate based on instruction
            if "upscale" in instruction_lower or "enhance" in instruction_lower or "quality" in instruction_lower:
                if "upscale" in models:
                    return type_str, "upscale", models["upscale"]
                if "enhance" in models:
                    return type_str, "enhance", models["enhance"]
            
            if "background" in instruction_lower:
                if "remove_background" in models:
                    return type_str, "remove_background", models["remove_background"]
            
            # Default to first available model for type
            first_task = list(models.keys())[0]
            return type_str, first_task, models[first_task]
        
        return "unknown", "unknown", {}
    
    async def _ensure_public_url(self, file_path: str) -> Optional[str]:
        """
        Ensure file is accessible via a public URL.
        
        For local files or localhost URLs, uploads to a temporary host (catbox.moe).
        External URLs are returned as-is.
        
        Args:
            file_path: Local path, localhost URL, or external URL
            
        Returns:
            Public URL or None if failed
        """
        import aiohttp
        from aiohttp import FormData
        
        # External URLs - return as-is
        if file_path.startswith("http") and "localhost" not in file_path and "127.0.0.1" not in file_path:
            return file_path
        
        # Local file or localhost URL - need to upload
        logger.info(f"🔄 Converting local file to public URL: {file_path[:60]}...")
        
        try:
            # Get file data
            file_data = None
            filename = "file"
            
            if file_path.startswith("http://localhost") or file_path.startswith("http://127.0.0.1"):
                # Localhost URL - fetch it
                async with aiohttp.ClientSession() as session:
                    async with session.get(file_path) as response:
                        if response.status == 200:
                            file_data = await response.read()
                            # Try to get filename from URL
                            filename = file_path.split("/")[-1] or "file"
                            content_type = response.headers.get("Content-Type", "image/png")
                        else:
                            logger.error(f"Failed to fetch local file: HTTP {response.status}")
                            return None
            
            elif file_path.startswith("/files/"):
                # Internal file reference - read from storage
                file_id = file_path.split("/")[-1]
                storage_path = Path("data/files")
                
                # Search for file in storage
                found_path = None
                for subdir in ["generated", "images", "uploads", "videos", "audio"]:
                    for file in (storage_path / subdir).glob("*"):
                        if file_id in str(file) or file.stem == file_id:
                            found_path = file
                            break
                    if found_path:
                        break
                
                if found_path and found_path.exists():
                    with open(found_path, "rb") as f:
                        file_data = f.read()
                    filename = found_path.name
                    content_type = self._guess_mime_type(filename)
                else:
                    logger.error(f"Could not find local file: {file_path}")
                    return None
            
            elif Path(file_path).exists():
                # Direct file path
                with open(file_path, "rb") as f:
                    file_data = f.read()
                filename = Path(file_path).name
                content_type = self._guess_mime_type(filename)
            
            else:
                logger.error(f"Cannot access file: {file_path}")
                return None
            
            if not file_data:
                return None
            
            # Upload to catbox.moe (free temporary hosting)
            async with aiohttp.ClientSession() as session:
                data = FormData()
                data.add_field('reqtype', 'fileupload')
                data.add_field('fileToUpload', 
                              file_data, 
                              filename=filename,
                              content_type=content_type)
                
                async with session.post('https://catbox.moe/user/api.php', data=data) as response:
                    if response.status == 200:
                        result = await response.text()
                        if result.startswith('https://'):
                            public_url = result.strip()
                            logger.info(f"✅ Uploaded to public URL: {public_url}")
                            return public_url
            
            logger.error("Failed to upload file to temporary host")
            return None
            
        except Exception as e:
            logger.error(f"Failed to create public URL: {e}")
            return None
    
    def _guess_mime_type(self, filename: str) -> str:
        """Guess MIME type from filename."""
        ext = Path(filename).suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
            '.gif': 'image/gif', '.webp': 'image/webp', '.bmp': 'image/bmp',
            '.mp4': 'video/mp4', '.mov': 'video/quicktime', '.avi': 'video/x-msvideo',
            '.webm': 'video/webm', '.mp3': 'audio/mpeg', '.wav': 'audio/wav',
            '.flac': 'audio/flac', '.ogg': 'audio/ogg', '.m4a': 'audio/mp4',
        }
        return mime_types.get(ext, 'application/octet-stream')

    async def call_replicate(
        self,
        model: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a Replicate model and wait for result."""
        import httpx
        
        if not self.api_token:
            raise ValueError("REPLICATE_API_TOKEN not set. Set it in your .env file.")
        
        headers = {
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/json"
        }
        
        self._update_status("api_call", 0.1, "🚀 Sending request to AI model...")
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            # Create prediction
            response = await client.post(
                "https://api.replicate.com/v1/predictions",
                headers=headers,
                json={
                    "version": model.split(":")[-1] if ":" in model else model,
                    "input": input_data
                }
            )
            
            if response.status_code >= 400:
                raise Exception(f"API error ({response.status_code}): {response.text}")
            
            result = response.json()
            self._update_status("queued", 0.2, "⏳ Request queued, waiting for processing...")
            
            # Poll for completion
            prediction_url = result.get("urls", {}).get("get")
            if not prediction_url:
                raise Exception(f"No prediction URL returned: {result}")
            
            max_attempts = 120  # 4 minutes max (2s intervals)
            attempts = 0
            
            while result.get("status") in ["starting", "processing"] and attempts < max_attempts:
                await asyncio.sleep(2)
                poll_response = await client.get(prediction_url, headers=headers)
                result = poll_response.json()
                attempts += 1
                
                # Update progress based on status
                progress = min(0.2 + (attempts / max_attempts) * 0.6, 0.8)
                status = result.get("status", "processing")
                if status == "starting":
                    self._update_status("starting", progress, "🔄 Model is starting up...")
                else:
                    self._update_status("processing", progress, f"⚙️ Processing... ({attempts * 2}s)")
            
            if result.get("status") == "failed":
                raise Exception(f"Model failed: {result.get('error', 'Unknown error')}")
            
            if result.get("status") not in ["succeeded", "completed"]:
                raise Exception(f"Unexpected status: {result.get('status')} after {attempts} attempts")
            
            self._update_status("complete", 1.0, "✅ Processing complete!")
            
            return {
                "success": True,
                "output": result.get("output"),
                "status": result.get("status"),
                "metrics": result.get("metrics", {})
            }
    
    async def call_openai(
        self,
        text: str,
        system_prompt: str,
        instruction: str = ""
    ) -> Dict[str, Any]:
        """Call OpenAI for text processing tasks."""
        if not self.openai_key:
            # Fallback to Anthropic if available
            if self.anthropic_key:
                return await self.call_anthropic(text, system_prompt, instruction)
            raise ValueError("OPENAI_API_KEY not set. Set it in your .env file.")
        
        self._update_status("api_call", 0.2, "🤖 Processing text with AI...")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            user_content = f"{instruction}\n\n{text}" if instruction else text
            
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    "max_tokens": 4096
                }
            )
            
            if response.status_code >= 400:
                raise Exception(f"OpenAI API error: {response.text}")
            
            result = response.json()
            output_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            self._update_status("complete", 1.0, "✅ Text processing complete!")
            
            return {
                "success": True,
                "output": output_text,
                "status": "completed",
                "output_type": "text"
            }
    
    async def call_anthropic(
        self,
        text: str,
        system_prompt: str,
        instruction: str = ""
    ) -> Dict[str, Any]:
        """Call Anthropic Claude for text processing tasks."""
        if not self.anthropic_key:
            raise ValueError("ANTHROPIC_API_KEY not set. Set it in your .env file.")
        
        self._update_status("api_call", 0.2, "🤖 Processing text with Claude...")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            user_content = f"{instruction}\n\n{text}" if instruction else text
            
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.anthropic_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 4096,
                    "system": system_prompt,
                    "messages": [
                        {"role": "user", "content": user_content}
                    ]
                }
            )
            
            if response.status_code >= 400:
                raise Exception(f"Anthropic API error: {response.text}")
            
            result = response.json()
            output_text = result.get("content", [{}])[0].get("text", "")
            
            self._update_status("complete", 1.0, "✅ Text processing complete!")
            
            return {
                "success": True,
                "output": output_text,
                "status": "completed",
                "output_type": "text"
            }
    
    @tool(
        name="universal_edit",
        description="Edit any file (image, video, audio, 3D, text) using AI. Just describe what you want and it figures out how to do it.",
        category="editing"
    )
    async def edit(
        self,
        file_path: str,
        instruction: str,
        output_format: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Universal file editor - works with any media type.
        
        Args:
            file_path: Path or URL to the file to edit
            instruction: Natural language instruction (e.g., "remove background", "upscale 4x", "make slow motion")
            output_format: Optional output format override
            
        Returns:
            Result with output file path and metadata
        """
        logger.info(f"Universal edit: {instruction} on {file_path}")
        self._update_status("analyzing", 0.05, "🔍 Analyzing file and task...")
        
        # Detect media type
        media_type = self.detect_media_type(file_path)
        logger.info(f"Detected media type: {media_type.value}")
        
        # Detect task and get model
        detected_type, task_name, model_info = self.detect_task(instruction, media_type)
        
        if not model_info:
            return {
                "success": False,
                "error": f"Could not determine appropriate model for: {instruction}",
                "media_type": media_type.value,
                "suggestion": "Try being more specific, e.g., 'remove background', 'upscale', 'enhance'"
            }
        
        logger.info(f"Selected task: {task_name}, model: {model_info.get('model', 'unknown')}")
        self._update_status("preparing", 0.1, f"🎯 Task: {task_name.replace('_', ' ').title()}")
        
        # Check if this is an LLM-based text task
        if model_info.get("use_llm"):
            self._update_status("text_processing", 0.15, "📝 Processing text with AI...")
            try:
                # For text tasks, the file_path might contain the text directly or be a file
                text_content = file_path
                
                # If it looks like a file path, try to read it
                if Path(file_path).exists():
                    with open(file_path, "r", encoding="utf-8") as f:
                        text_content = f.read()
                
                system_prompt = model_info.get("system_prompt", "Process the following text:")
                result = await self.call_openai(text_content, system_prompt, instruction)
                
                return {
                    "success": True,
                    "media_type": "text",
                    "task": task_name,
                    "output_text": result.get("output"),
                    "output_url": None,
                    "original": file_path[:100] + "..." if len(file_path) > 100 else file_path,
                    "instruction": instruction,
                    "output_type": "text"
                }
            except Exception as e:
                logger.error(f"Text processing failed: {e}")
                return {"success": False, "error": str(e), "task": task_name}
        
        # Prepare input
        input_key = model_info.get("input_key", "image")
        
        # Handle special cases for text-to-X generation
        if model_info.get("requires_text") and not model_info.get("requires_audio"):
            # Text-to-speech, music generation - use instruction as input
            self._update_status("generating", 0.15, f"🎵 Generating {task_name.replace('_', ' ')}...")
            input_data = {input_key: instruction}
            
            # Add extra params if specified
            if model_info.get("extra_params"):
                input_data.update(model_info["extra_params"])
            
            try:
                result = await self.call_replicate(
                    model=model_info["model"],
                    input_data=input_data
                )
                
                output = result.get("output")
                output_path = self._extract_output_url(output)
                
                return {
                    "success": True,
                    "media_type": detected_type,
                    "task": task_name,
                    "model": model_info["model"],
                    "output_url": output_path,
                    "instruction": instruction,
                    "metrics": result.get("metrics", {})
                }
            except Exception as e:
                logger.error(f"Generation failed: {e}")
                return {"success": False, "error": str(e), "task": task_name}
        
        # Handle URL vs local file path - Replicate needs publicly accessible URLs
        self._update_status("uploading", 0.12, "📤 Preparing file for AI processing...")
        file_url = await self._ensure_public_url(file_path)
        if not file_url:
            return {
                "success": False,
                "error": f"Could not access file: {file_path}",
                "suggestion": "Provide a publicly accessible URL or ensure the local file exists"
            }
        
        input_data = {input_key: file_url}
        
        # Add prompt if task needs it
        if task_name in ["image_to_image", "inpaint", "style_transfer"]:
            input_data["prompt"] = instruction
        
        # Add extra params if specified
        if model_info.get("extra_params"):
            input_data.update(model_info["extra_params"])
        
        try:
            # Call Replicate
            result = await self.call_replicate(
                model=model_info["model"],
                input_data=input_data
            )
            
            # Process output
            output = result.get("output")
            output_path = self._extract_output_url(output)
            
            # Handle special output types
            output_type = model_info.get("output_type")
            
            response = {
                "success": True,
                "media_type": detected_type,
                "task": task_name,
                "model": model_info["model"],
                "output_url": output_path,
                "original": file_path,
                "instruction": instruction,
                "metrics": result.get("metrics", {})
            }
            
            # Handle stems/multi-output
            if output_type == "stems" and isinstance(output, dict):
                response["stems"] = output
                response["output_type"] = "stems"
            elif output_type == "text":
                response["output_text"] = output
                response["output_type"] = "text"
            
            return response
            
        except Exception as e:
            logger.error(f"Edit failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "media_type": detected_type,
                "task": task_name
            }
    
    def _extract_output_url(self, output: Any) -> Optional[str]:
        """Extract URL from various output formats."""
        if output is None:
            return None
        if isinstance(output, str) and output.startswith("http"):
            return output
        if isinstance(output, list) and output:
            first = output[0]
            if isinstance(first, str) and first.startswith("http"):
                return first
            if isinstance(first, dict):
                return first.get("url") or first.get("output")
        if isinstance(output, dict):
            return output.get("url") or output.get("output")
        return None
    
    @tool(
        name="edit_image",
        description="Edit an image with AI - remove background, upscale, enhance, add effects, transform style",
        category="editing"
    )
    async def edit_image(
        self,
        image_url: str,
        instruction: str,
        mask_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Edit an image based on instruction.
        
        Args:
            image_url: URL of image to edit
            instruction: What to do (e.g., "remove background", "upscale 4x", "make cartoon style")
            mask_url: Optional mask for inpainting operations
        """
        _, task_name, model_info = self.detect_task(instruction, MediaType.IMAGE)
        
        if not model_info:
            # Default to image-to-image with SDXL
            model_info = REPLICATE_MODELS["image"]["image_to_image"]
            task_name = "image_to_image"
        
        input_data = {model_info["input_key"]: image_url}
        
        if task_name in ["inpaint", "image_to_image", "style_transfer"]:
            input_data["prompt"] = instruction
        
        if mask_url and task_name == "inpaint":
            input_data["mask"] = mask_url
        
        try:
            result = await self.call_replicate(model_info["model"], input_data)
            
            output = result.get("output")
            if isinstance(output, list):
                output = output[0] if output else None
            
            return {
                "success": True,
                "task": task_name,
                "output_url": output,
                "original": image_url,
                "instruction": instruction
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="edit_video",
        description="Edit a video with AI - animate image, stabilize, slow motion, remove background",
        category="editing"
    )
    async def edit_video(
        self,
        input_url: str,
        instruction: str
    ) -> Dict[str, Any]:
        """
        Edit a video or create video from image.
        
        Args:
            input_url: URL of video or image
            instruction: What to do (e.g., "make slow motion", "animate this image", "stabilize")
        """
        # Detect if input is image or video
        media_type = self.detect_media_type(input_url)
        
        if "animate" in instruction.lower() or media_type == MediaType.IMAGE:
            task_name = "image_to_video"
        else:
            _, task_name, _ = self.detect_task(instruction, MediaType.VIDEO)
        
        model_info = REPLICATE_MODELS["video"].get(task_name)
        if not model_info:
            model_info = REPLICATE_MODELS["video"]["image_to_video"]
            task_name = "image_to_video"
        
        input_data = {model_info["input_key"]: input_url}
        
        try:
            result = await self.call_replicate(model_info["model"], input_data)
            
            return {
                "success": True,
                "task": task_name,
                "output_url": result.get("output"),
                "original": input_url,
                "instruction": instruction
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="edit_audio",
        description="Edit audio with AI - separate vocals, remove noise, change pitch, generate music",
        category="editing"
    )
    async def edit_audio(
        self,
        audio_url: str,
        instruction: str
    ) -> Dict[str, Any]:
        """
        Edit audio file.
        
        Args:
            audio_url: URL of audio file
            instruction: What to do (e.g., "separate vocals", "remove background noise", "extract drums")
        """
        _, task_name, model_info = self.detect_task(instruction, MediaType.AUDIO)
        
        if not model_info:
            model_info = REPLICATE_MODELS["audio"]["separate_vocals"]
            task_name = "separate_vocals"
        
        input_data = {model_info["input_key"]: audio_url}
        
        try:
            result = await self.call_replicate(model_info["model"], input_data)
            
            return {
                "success": True,
                "task": task_name,
                "output": result.get("output"),  # May be dict with stems
                "original": audio_url,
                "instruction": instruction
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="create_3d",
        description="Create or edit 3D models - generate from image or text",
        category="editing"
    )
    async def create_3d(
        self,
        input_source: str,
        instruction: str
    ) -> Dict[str, Any]:
        """
        Create or edit 3D models.
        
        Args:
            input_source: Image URL or text prompt
            instruction: What to create/edit
        """
        if input_source.startswith("http") or Path(input_source).suffix.lower() in ['.jpg', '.png', '.webp']:
            task_name = "image_to_3d"
        else:
            task_name = "text_to_3d"
        
        model_info = REPLICATE_MODELS["3d"].get(task_name)
        if not model_info:
            return {"success": False, "error": "3D generation not available"}
        
        input_data = {model_info["input_key"]: input_source}
        
        if task_name == "text_to_3d":
            input_data["prompt"] = instruction
        
        try:
            result = await self.call_replicate(model_info["model"], input_data)
            
            return {
                "success": True,
                "task": task_name,
                "output_url": result.get("output"),
                "instruction": instruction
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="list_edit_capabilities",
        description="List all available editing capabilities by media type",
        category="editing"
    )
    async def list_capabilities(self, media_type: Optional[str] = None) -> Dict[str, Any]:
        """List available editing capabilities."""
        if media_type and media_type in REPLICATE_MODELS:
            return {
                "media_type": media_type,
                "capabilities": {
                    task: info["description"]
                    for task, info in REPLICATE_MODELS[media_type].items()
                }
            }
        
        return {
            "capabilities": {
                media: {
                    task: info["description"]
                    for task, info in tasks.items()
                }
                for media, tasks in REPLICATE_MODELS.items()
            }
        }


def get_universal_editor() -> UniversalEditor:
    """Get universal editor instance."""
    return UniversalEditor()
