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
    
    def __init__(self, replicate_token: str):
        self.token = replicate_token
        self.base_url = "https://api.replicate.com/v1"
        self.headers = {
            "Authorization": f"Token {replicate_token}",
            "Content-Type": "application/json"
        }
        
        # Model versions - all with explicit version hashes for reliability
        self.models = {
            "flux_schnell": "black-forest-labs/flux-schnell:c846a69991daf4c0e5d016514849d14ee5b2e6846ce6b9d6f21369e564cfe51e",
            "flux_pro": "black-forest-labs/flux-1.1-pro",
            "sdxl": "stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc",
            "stable_diffusion_3": "stability-ai/stable-diffusion-3",
            "ideogram": "ideogram-ai/ideogram-v2",
            "recraft": "recraft-ai/recraft-v3:9507e61ddace8b3a238371b17a61be203747c5081ea6070fecd3c40d27318922"
        }
    
    async def _run_model(
        self,
        model: str,
        input_data: Dict[str, Any],
        wait: bool = True
    ) -> Dict[str, Any]:
        """Run a Replicate model."""
        url = f"{self.base_url}/predictions"
        
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
        
        async with aiohttp.ClientSession() as session:
            # Start prediction
            async with session.post(url, headers=self.headers, json=data) as response:
                if response.status >= 400:
                    error = await response.text()
                    raise Exception(f"Replicate API error: {error}")
                result = await response.json()
            
            if not wait:
                return result
            
            # Poll for completion
            prediction_url = result.get("urls", {}).get("get") or f"{url}/{result['id']}"
            
            while result.get("status") in ["starting", "processing"]:
                await asyncio.sleep(1)
                async with session.get(prediction_url, headers=self.headers) as response:
                    result = await response.json()
            
            if result.get("status") == "failed":
                raise Exception(f"Prediction failed: {result.get('error')}")
            
            return result
    
    @tool(
        name="generate_image",
        description="Generate an image from a text prompt using AI",
        category="ai_models"
    )
    async def generate_image(
        self,
        prompt: str,
        model: str = "flux_schnell",
        width: int = 1024,
        height: int = 1024,
        num_outputs: int = 1,
        negative_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate an image from text.
        
        Args:
            prompt: Text description of the image
            model: Model to use (flux_schnell, flux_pro, sdxl, stable_diffusion_3)
            width: Image width
            height: Image height
            num_outputs: Number of images to generate
            negative_prompt: What to avoid in the image
        """
        model_id = self.models.get(model, model)
        
        input_data = {
            "prompt": prompt,
            "width": width,
            "height": height,
            "num_outputs": num_outputs
        }
        
        if negative_prompt:
            input_data["negative_prompt"] = negative_prompt
        
        # Model-specific adjustments
        if "flux" in model.lower():
            input_data["aspect_ratio"] = f"{width}:{height}"
            input_data.pop("width", None)
            input_data.pop("height", None)
        
        result = await self._run_model(model_id, input_data)
        
        output = result.get("output", [])
        if isinstance(output, str):
            output = [output]
        
        return {
            "success": True,
            "images": output,
            "model": model,
            "prompt": prompt,
            "prediction_id": result.get("id")
        }
    
    @tool(
        name="generate_tshirt_design",
        description="Generate a t-shirt ready design with transparent background",
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
            model: Model to use (recraft recommended)
        """
        # Enhanced prompt for t-shirt designs
        enhanced_prompt = f"{prompt}, {style} art style, clean design, suitable for t-shirt print, high contrast, no background, centered composition"
        
        if model == "recraft":
            model_id = self.models["recraft"]
            # Map user-friendly style names to valid Recraft styles
            style_map = {
                "vector": "digital_illustration/2d_art_poster",
                "illustration": "digital_illustration",
                "hand_drawn": "digital_illustration/hand_drawn",
                "poster": "digital_illustration/2d_art_poster_2",
                "realistic": "realistic_image",
                "minimalist": "digital_illustration/hand_drawn_outline",
            }
            recraft_style = style_map.get(style, "digital_illustration/2d_art_poster")
            input_data = {
                "prompt": enhanced_prompt,
                "style": recraft_style,
                "size": "1024x1024"
            }
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
        style: str = "photorealistic"
    ) -> Dict[str, Any]:
        """
        Generate a lifestyle scene for product marketing.
        
        Args:
            product_description: Description of the product
            scene_type: Type of scene (outdoor, indoor, studio, urban, nature)
            style: Style (photorealistic, artistic, minimal)
        """
        scene_prompts = {
            "outdoor": "outdoor setting, natural lighting, scenic background",
            "indoor": "cozy indoor setting, warm lighting, modern interior",
            "studio": "professional studio photography, clean background, soft lighting",
            "urban": "urban street scene, city background, dynamic composition",
            "nature": "natural environment, forest or beach, peaceful atmosphere"
        }
        
        scene = scene_prompts.get(scene_type, scene_prompts["outdoor"])
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
        product_type: str,
        design_description: str,
        background: str = "white"
    ) -> Dict[str, Any]:
        """
        Generate a product mockup.
        
        Args:
            product_type: Type of product (tshirt, hoodie, mug, poster)
            design_description: Description of the design on the product
            background: Background color/style
        """
        mockup_prompts = {
            "tshirt": "professional product photography of a t-shirt mockup",
            "hoodie": "professional product photography of a hoodie mockup",
            "mug": "professional product photography of a ceramic mug mockup",
            "poster": "professional product photography of a framed poster mockup",
            "phone_case": "professional product photography of a phone case mockup"
        }
        
        base_prompt = mockup_prompts.get(product_type, mockup_prompts["tshirt"])
        prompt = f"{base_prompt} with {design_description} design, {background} background, studio lighting, high resolution, commercial quality"
        
        return await self.generate_image(
            prompt=prompt,
            model="flux_pro",
            width=1024,
            height=1024
        )
