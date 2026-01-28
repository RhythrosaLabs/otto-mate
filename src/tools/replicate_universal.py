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
    
    def __init__(self, api_token: str):
        self.token = api_token
        self.base_url = "https://api.replicate.com/v1"
        self.headers = {
            "Authorization": f"Token {api_token}",
            "Content-Type": "application/json"
        }
        
        # Cache for model schemas (avoid repeated lookups)
        self._model_cache: Dict[str, Dict] = {}
        
        # Popular model shortcuts for common tasks
        self.model_shortcuts = {
            # Image Generation
            "image": "black-forest-labs/flux-schnell",
            "image_pro": "black-forest-labs/flux-1.1-pro",
            "image_fast": "black-forest-labs/flux-schnell",
            "sdxl": "stability-ai/sdxl",
            "sd3": "stability-ai/stable-diffusion-3",
            "ideogram": "ideogram-ai/ideogram-v2",
            "recraft": "recraft-ai/recraft-v3",
            "midjourney": "tstramer/midjourney-diffusion",
            
            # Image Editing
            "remove_bg": "cjwbw/rembg",
            "upscale": "nightmareai/real-esrgan",
            "restore_face": "tencentarc/gfpgan",
            "inpaint": "stability-ai/stable-diffusion-inpainting",
            
            # Video
            "video": "anotherjesse/zeroscope-v2-xl",
            "animate": "stability-ai/stable-video-diffusion",
            "luma": "luma/photon",
            "kling": "kwaivgi/kling-v2.5-turbo-pro",
            "kling_pro": "kwaivgi/kling-v2.6-pro",
            
            # Audio
            "music": "meta/musicgen",
            "speech": "openai/whisper",
            "tts": "cjwbw/bark",
            "voice_clone": "lucataco/xtts-v2",
            
            # Text/Language
            "llm": "meta/llama-2-70b-chat",
            "code": "meta/codellama-34b-instruct",
            "vision": "yorickvp/llava-13b",
            
            # 3D
            "3d": "cjwbw/shap-e",
            "mesh": "adirik/wonder3d",
        }
    
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
        inputs: Dict[str, Any],
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
    
    @tool(
        name="replicate_run_model",
        description="Run ANY Replicate AI model with specified inputs. Use this to generate images, audio, video, text, 3D models, or any other AI task. First use replicate_get_model_info to understand required inputs.",
        category="ai_models"
    )
    async def run_model(
        self,
        model_name: str,
        inputs: Dict[str, Any],
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
    
    @tool(
        name="replicate_smart_generate",
        description="Intelligently generate content using the best available model. Describe what you want and the system will select and configure the optimal model automatically.",
        category="ai_models"
    )
    async def smart_generate(
        self,
        description: str,
        content_type: str = "auto",
        style: Optional[str] = None,
        quality: str = "balanced"
    ) -> Dict[str, Any]:
        """
        Smart content generation - automatically selects best model.
        
        Args:
            description: What to generate (detailed description)
            content_type: Type of content (image, video, audio, 3d, text, auto)
            style: Optional style hints
            quality: Quality preset (fast, balanced, best)
        """
        # Detect content type if auto
        if content_type == "auto":
            desc_lower = description.lower()
            if any(w in desc_lower for w in ["video", "animate", "motion", "clip"]):
                content_type = "video"
            elif any(w in desc_lower for w in ["music", "song", "audio", "sound", "voice", "speech"]):
                content_type = "audio"
            elif any(w in desc_lower for w in ["3d", "mesh", "model", "sculpture"]):
                content_type = "3d"
            elif any(w in desc_lower for w in ["write", "story", "text", "article", "code"]):
                content_type = "text"
            else:
                content_type = "image"
        
        # Select model based on type and quality
        model_map = {
            "image": {
                "fast": "black-forest-labs/flux-schnell",
                "balanced": "black-forest-labs/flux-schnell",
                "best": "black-forest-labs/flux-1.1-pro"
            },
            "video": {
                "fast": "kwaivgi/kling-v2.5-turbo-pro",
                "balanced": "kwaivgi/kling-v2.5-turbo-pro",
                "best": "kwaivgi/kling-v2.6-pro"
            },
            "audio": {
                "fast": "meta/musicgen",
                "balanced": "meta/musicgen",
                "best": "meta/musicgen"
            },
            "3d": {
                "fast": "cjwbw/shap-e",
                "balanced": "cjwbw/shap-e",
                "best": "adirik/wonder3d"
            },
            "text": {
                "fast": "meta/llama-2-13b-chat",
                "balanced": "meta/llama-2-70b-chat",
                "best": "meta/llama-2-70b-chat"
            }
        }
        
        selected_model = model_map.get(content_type, model_map["image"]).get(quality, "balanced")
        
        # Build inputs based on content type
        if content_type == "image":
            prompt = description
            if style:
                prompt = f"{description}, {style} style"
            inputs = {
                "prompt": prompt,
                "num_outputs": 1
            }
            if "flux" in selected_model:
                inputs["aspect_ratio"] = "1:1"
        
        elif content_type == "video":
            inputs = {
                "prompt": description,
                "num_frames": 24
            }
        
        elif content_type == "audio":
            inputs = {
                "prompt": description,
                "duration": 8
            }
        
        elif content_type == "3d":
            inputs = {
                "prompt": description
            }
        
        elif content_type == "text":
            inputs = {
                "prompt": description,
                "max_new_tokens": 1024
            }
        
        else:
            inputs = {"prompt": description}
        
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
