"""
Social Media Ad Generation Tools
=================================

Professional-grade ad generation using Replicate's advertising pipelines.
Ported from printify_clean's SocialMediaAdService with Otto-specific enhancements.

Key Capabilities:
- Generate product ads with professional styling
- Create animated video advertisements
- High-quality static brand ads
- Logo placement in contextual scenes
- Complete social media campaign orchestration
"""

import logging
import os
import asyncio
import aiohttp
from pathlib import Path
from typing import Optional, Dict, Any, List

from .core import tool, ToolBase

logger = logging.getLogger(__name__)


class SocialMediaAdsTools(ToolBase):
    """
    Professional ad generation service using Replicate's advertising pipelines.
    
    Key Features:
    - Generate multiple ad variations from product images
    - Create animated video ads from static products
    - Professional static ads with brand styling
    - Logo placement in contextual product scenes
    - Complete campaign orchestration
    """
    
    def __init__(self, api_token: str):
        self.token = api_token
        self.base_url = "https://api.replicate.com/v1"
        self.headers = {
            "Authorization": f"Token {api_token}",
            "Content-Type": "application/json",
            "Accept-Encoding": "identity, gzip, deflate"
        }
        
        # Professional ad generation models
        self.ad_models = {
            "product_ads": "pipeline-examples/ads-for-products",
            "video_ads": "pipeline-examples/video-ads", 
            "static_ads": "loolau/flux-static-ads",
            "logo_context": "subhash25rawat/logo-in-context",
            "flux_fast": "prunaai/flux-fast",
            "flux_pro": "black-forest-labs/flux-1.1-pro",
        }
        
        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 0.5  # 500ms between requests
        
        logger.info("✅ Social Media Ads Tools initialized")
    
    async def _rate_limit(self):
        """Ensure minimum interval between requests."""
        import time
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            await asyncio.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    async def _run_model(
        self,
        model: str,
        input_data: Dict[str, Any],
        wait_for_result: bool = True
    ) -> Dict[str, Any]:
        """Run a Replicate model with input data."""
        await self._rate_limit()
        
        url = f"{self.base_url}/predictions"
        
        payload = {
            "version": model if "/" in model else self.ad_models.get(model, model),
            "input": input_data
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=self.headers) as response:
                if response.status != 201:
                    error_text = await response.text()
                    logger.error(f"Model run failed: {error_text}")
                    return {"error": error_text}
                
                result = await response.json()
                
                if not wait_for_result:
                    return result
                
                # Poll for completion
                prediction_id = result.get("id")
                get_url = f"{self.base_url}/predictions/{prediction_id}"
                
                for _ in range(120):  # Max 2 minutes
                    await asyncio.sleep(1)
                    async with session.get(get_url, headers=self.headers) as poll_response:
                        poll_result = await poll_response.json()
                        status = poll_result.get("status")
                        
                        if status == "succeeded":
                            return poll_result
                        elif status in ("failed", "canceled"):
                            return {"error": poll_result.get("error", "Prediction failed")}
                
                return {"error": "Timeout waiting for prediction"}
    
    @tool(
        name="generate_product_ads",
        description="""Generate professional static ads from a product image.
        
Uses Replicate's ads-for-products pipeline to create stunning product advertisements.
Great for: Instagram product shots, Facebook ads, e-commerce banners.

Example: generate_product_ads(product_image_url="https://example.com/product.jpg", 
                              product_description="Premium wireless headphones",
                              target_audience="young professionals",
                              ad_style="minimalist")""",
        category="social_media"
    )
    async def generate_product_ads(
        self,
        product_image_url: str,
        num_variations: int = 3,
        product_description: str = "",
        target_audience: str = "general consumers",
        ad_style: str = "modern and clean"
    ) -> Dict[str, Any]:
        """
        Generate professional static ads from a product image.
        
        Args:
            product_image_url: URL to product image (must be publicly accessible)
            num_variations: Number of ad variations (1-10)
            product_description: Product description for better prompts
            target_audience: Target audience (e.g., 'young professionals', 'fitness enthusiasts')
            ad_style: Style preference (e.g., 'minimalist', 'vibrant', 'luxury', 'modern')
        
        Returns:
            Dictionary with list of ad URLs and metadata
        """
        logger.info(f"🎨 Generating {num_variations} product ads (style: {ad_style})...")
        
        try:
            result = await self._run_model(
                self.ad_models["product_ads"],
                {
                    "product_image": product_image_url,
                    "num_prompts": min(max(num_variations, 1), 10),
                    "product_description": product_description,
                    "target_audience": target_audience,
                    "ad_style": ad_style,
                }
            )
            
            if "error" in result:
                return {"success": False, "error": result["error"]}
            
            output = result.get("output", [])
            ad_urls = list(output) if hasattr(output, "__iter__") and not isinstance(output, str) else [output]
            
            logger.info(f"✅ Generated {len(ad_urls)} product ads")
            
            return {
                "success": True,
                "ad_urls": ad_urls,
                "count": len(ad_urls),
                "product_description": product_description,
                "target_audience": target_audience,
                "ad_style": ad_style,
                "ad_type": "static_product"
            }
            
        except Exception as e:
            logger.error(f"❌ Product ad generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    @tool(
        name="generate_video_ads",
        description="""Generate animated video ads from a product image.
        
Creates short video advertisements from static product images.
Perfect for: TikTok, Instagram Reels, YouTube Shorts.

Example: generate_video_ads(product_image_url="https://example.com/product.jpg",
                            product_description="Stylish sneakers",
                            video_duration=5,
                            ad_style="vibrant and energetic")""",
        category="social_media"
    )
    async def generate_video_ads(
        self,
        product_image_url: str,
        num_variations: int = 2,
        product_description: str = "",
        target_audience: str = "general consumers",
        ad_style: str = "modern and clean",
        video_duration: int = 5
    ) -> Dict[str, Any]:
        """
        Generate animated video ads from a product image.
        
        Args:
            product_image_url: URL to product image
            num_variations: Number of video variations (1-10)
            product_description: Product description
            target_audience: Target audience
            ad_style: Style preference
            video_duration: Duration in seconds (default: 5)
        
        Returns:
            Dictionary with video ad URLs
        """
        logger.info(f"🎥 Generating {num_variations} video ads ({video_duration}s each)...")
        
        try:
            result = await self._run_model(
                self.ad_models["video_ads"],
                {
                    "product_image": product_image_url,
                    "num_prompts": min(max(num_variations, 1), 10),
                    "product_description": product_description,
                    "target_audience": target_audience,
                    "ad_style": ad_style,
                    "video_duration": video_duration,
                }
            )
            
            if "error" in result:
                return {"success": False, "error": result["error"]}
            
            output = result.get("output", [])
            video_urls = list(output) if hasattr(output, "__iter__") and not isinstance(output, str) else [output]
            
            logger.info(f"✅ Generated {len(video_urls)} video ads")
            
            return {
                "success": True,
                "video_urls": video_urls,
                "count": len(video_urls),
                "duration_seconds": video_duration,
                "ad_type": "video"
            }
            
        except Exception as e:
            logger.error(f"❌ Video ad generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    @tool(
        name="generate_brand_ads",
        description="""Generate high-quality static ads for a brand using Flux.
        
Creates professional brand advertisements without requiring product images.
Great for: Brand awareness campaigns, coming soon ads, generic marketing.

Example: generate_brand_ads(brand_name="TechFlow",
                            brand_description="Premium tech accessories",
                            ad_concept="Futuristic minimalist aesthetic")""",
        category="social_media"
    )
    async def generate_brand_ads(
        self,
        brand_name: str,
        brand_description: str,
        ad_concept: str,
        num_variations: int = 3,
        aspect_ratio: str = "1:1"
    ) -> Dict[str, Any]:
        """
        Generate high-quality static ads for a brand.
        
        Args:
            brand_name: Name of the brand
            brand_description: Description of brand identity
            ad_concept: Concept/theme for the ad
            num_variations: Number of variations to generate
            aspect_ratio: Output aspect ratio (1:1, 16:9, 9:16, 4:5)
        
        Returns:
            Dictionary with brand ad URLs
        """
        logger.info(f"🏢 Generating {num_variations} brand ads for {brand_name}...")
        
        try:
            ad_urls = []
            
            for i in range(num_variations):
                prompt = f"{brand_name} advertisement: {ad_concept}. {brand_description}. Professional, high-quality, commercial ad design, studio lighting, 8k quality"
                
                result = await self._run_model(
                    self.ad_models["flux_pro"],
                    {
                        "prompt": prompt,
                        "aspect_ratio": aspect_ratio,
                        "output_format": "png",
                        "output_quality": 95,
                        "safety_tolerance": 2,
                    }
                )
                
                if "error" not in result:
                    output = result.get("output", [])
                    if isinstance(output, list):
                        ad_urls.extend(output)
                    elif output:
                        ad_urls.append(output)
                
                await asyncio.sleep(0.5)  # Rate limiting
            
            logger.info(f"✅ Generated {len(ad_urls)} brand ads")
            
            return {
                "success": True,
                "ad_urls": ad_urls,
                "count": len(ad_urls),
                "brand_name": brand_name,
                "ad_concept": ad_concept,
                "ad_type": "static_brand"
            }
            
        except Exception as e:
            logger.error(f"❌ Brand ad generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    @tool(
        name="place_logo_in_context",
        description="""Place company logo on objects in contextual scenes.
        
Creates marketing materials with logos on products, packaging, office items.
Great for: Mockups, branded merchandise previews, social content.

Example: place_logo_in_context(logo_image_url="https://example.com/logo.png",
                               context_description="coffee mug on office desk")""",
        category="social_media"
    )
    async def place_logo_in_context(
        self,
        logo_image_url: str,
        context_description: str,
        num_variations: int = 3
    ) -> Dict[str, Any]:
        """
        Place company logo on objects in contextual scenes.
        
        Args:
            logo_image_url: URL to logo image
            context_description: Context description (e.g., "coffee mug on desk", "t-shirt on model")
            num_variations: Number of variations to generate
        
        Returns:
            Dictionary with logo-in-context image URLs
        """
        logger.info(f"🎯 Placing logo in context: {context_description}...")
        
        try:
            logo_urls = []
            
            for i in range(num_variations):
                result = await self._run_model(
                    self.ad_models["logo_context"],
                    {
                        "logo": logo_image_url,
                        "prompt": context_description,
                        "num_inference_steps": 50,
                    }
                )
                
                if "error" not in result:
                    output = result.get("output", [])
                    if isinstance(output, list):
                        logo_urls.extend(output)
                    elif output:
                        logo_urls.append(output)
                
                await asyncio.sleep(0.5)
            
            logger.info(f"✅ Generated {len(logo_urls)} logo-in-context images")
            
            return {
                "success": True,
                "image_urls": logo_urls,
                "count": len(logo_urls),
                "context": context_description,
                "ad_type": "logo_context"
            }
            
        except Exception as e:
            logger.error(f"❌ Logo-in-context generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    @tool(
        name="generate_social_media_campaign",
        description="""Generate a complete social media campaign with enhanced visuals.
        
Creates a full set of marketing materials including:
- 3 static product ads
- 2 video ads (optional)
- 3 branded context images (if logo provided)

Perfect for: Product launches, marketing campaigns, brand promotions.

Example: generate_social_media_campaign(product_image_url="https://example.com/product.jpg",
                                        product_name="Premium Wireless Headphones",
                                        target_audience="young professionals",
                                        include_video=True)""",
        category="social_media"
    )
    async def generate_social_media_campaign(
        self,
        product_image_url: str,
        product_name: str,
        target_audience: str = "general consumers",
        include_video: bool = True,
        logo_image_url: Optional[str] = None,
        ad_style: str = "modern and clean"
    ) -> Dict[str, Any]:
        """
        Generate a complete social media campaign with enhanced visuals.
        
        Args:
            product_image_url: URL to main product image
            product_name: Name/description of product
            target_audience: Target audience description
            include_video: Whether to generate video ads (default: True)
            logo_image_url: Optional logo URL for branded content
            ad_style: Overall style for the campaign
        
        Returns:
            Dictionary with 'static_ads', 'video_ads', 'logo_content' lists
        """
        logger.info(f"🚀 Launching social media campaign for: {product_name}")
        
        results = {
            "success": True,
            "product_name": product_name,
            "target_audience": target_audience,
            "static_ads": [],
            "video_ads": [],
            "logo_content": [],
            "total_assets": 0
        }
        
        # 1. Generate professional product ads (3 variations)
        logger.info("📸 Step 1/3: Generating static product ads...")
        static_result = await self.generate_product_ads(
            product_image_url=product_image_url,
            num_variations=3,
            product_description=product_name,
            target_audience=target_audience,
            ad_style=ad_style
        )
        if static_result.get("success"):
            results["static_ads"] = static_result.get("ad_urls", [])
        
        # 2. Generate video ads if requested
        if include_video:
            logger.info("🎬 Step 2/3: Generating video ads...")
            video_result = await self.generate_video_ads(
                product_image_url=product_image_url,
                num_variations=2,
                product_description=product_name,
                target_audience=target_audience,
                ad_style="vibrant and energetic",
                video_duration=5
            )
            if video_result.get("success"):
                results["video_ads"] = video_result.get("video_urls", [])
        
        # 3. Generate branded content with logo if provided
        if logo_image_url:
            logger.info("🎯 Step 3/3: Creating logo-in-context content...")
            contexts = [
                f"{product_name} on white background, studio lighting",
                f"{product_name} in lifestyle setting, natural lighting",
                f"{product_name} with elegant packaging",
            ]
            for context in contexts:
                logo_result = await self.place_logo_in_context(
                    logo_image_url=logo_image_url,
                    context_description=context,
                    num_variations=1
                )
                if logo_result.get("success"):
                    results["logo_content"].extend(logo_result.get("image_urls", []))
        
        results["total_assets"] = (
            len(results["static_ads"]) + 
            len(results["video_ads"]) + 
            len(results["logo_content"])
        )
        
        logger.info("✅ Social media campaign complete!")
        logger.info(f"   → {len(results['static_ads'])} static ads")
        logger.info(f"   → {len(results['video_ads'])} video ads")
        logger.info(f"   → {len(results['logo_content'])} branded assets")
        
        return results
    
    @tool(
        name="generate_platform_optimized_ads",
        description="""Generate ads optimized for specific social media platforms.
        
Creates ads with correct aspect ratios and styles for each platform:
- Instagram: 1:1 (feed), 4:5 (portrait), 9:16 (stories/reels)
- Facebook: 1:1 (feed), 16:9 (link preview)
- TikTok: 9:16 (vertical video)
- LinkedIn: 1.91:1 (landscape)
- Pinterest: 2:3 (pins)

Example: generate_platform_optimized_ads(product_description="Artisan coffee beans",
                                          platforms=["instagram", "tiktok", "pinterest"],
                                          brand_style="warm and cozy")""",
        category="social_media"
    )
    async def generate_platform_optimized_ads(
        self,
        product_description: str,
        platforms: Optional[List[str]] = None,
        brand_style: str = "modern and professional",
        include_text_overlay: bool = True,
        headline: Optional[str] = None,
        call_to_action: str = "Shop Now"
    ) -> Dict[str, Any]:
        """
        Generate ads optimized for specific social media platforms.
        
        Args:
            product_description: Description of product/service
            platforms: List of platforms (instagram, facebook, tiktok, linkedin, pinterest, twitter)
            brand_style: Brand aesthetic style
            include_text_overlay: Include text overlay suggestions
            headline: Optional headline for ads
            call_to_action: CTA text
        
        Returns:
            Dictionary with platform-specific ad URLs and recommendations
        """
        platforms = platforms or ["instagram", "facebook", "tiktok"]
        
        # Platform aspect ratio mappings
        platform_specs = {
            "instagram": [
                {"name": "feed", "ratio": "1:1", "size": "1080x1080"},
                {"name": "portrait", "ratio": "4:5", "size": "1080x1350"},
                {"name": "stories", "ratio": "9:16", "size": "1080x1920"}
            ],
            "facebook": [
                {"name": "feed", "ratio": "1:1", "size": "1080x1080"},
                {"name": "link", "ratio": "16:9", "size": "1200x628"}
            ],
            "tiktok": [
                {"name": "video", "ratio": "9:16", "size": "1080x1920"}
            ],
            "linkedin": [
                {"name": "post", "ratio": "1:1", "size": "1200x1200"},
                {"name": "link", "ratio": "1.91:1", "size": "1200x627"}
            ],
            "pinterest": [
                {"name": "pin", "ratio": "2:3", "size": "1000x1500"}
            ],
            "twitter": [
                {"name": "post", "ratio": "16:9", "size": "1200x675"}
            ]
        }
        
        results = {
            "success": True,
            "platforms": {},
            "total_ads": 0
        }
        
        for platform in platforms:
            if platform.lower() not in platform_specs:
                continue
                
            specs = platform_specs[platform.lower()]
            results["platforms"][platform] = []
            
            for spec in specs:
                prompt = f"{product_description}. {brand_style} style. Perfect for {platform} {spec['name']}. Professional advertising photography, studio quality"
                
                if include_text_overlay and headline:
                    prompt += f". Space for headline: '{headline}' and CTA: '{call_to_action}'"
                
                result = await self._run_model(
                    self.ad_models["flux_pro"],
                    {
                        "prompt": prompt,
                        "aspect_ratio": spec["ratio"],
                        "output_format": "png",
                        "output_quality": 95,
                    }
                )
                
                if "error" not in result:
                    output = result.get("output", [])
                    ad_url = output[0] if isinstance(output, list) and output else output
                    
                    if ad_url:
                        results["platforms"][platform].append({
                            "format": spec["name"],
                            "aspect_ratio": spec["ratio"],
                            "recommended_size": spec["size"],
                            "url": ad_url,
                            "text_overlay": {
                                "headline": headline,
                                "cta": call_to_action
                            } if include_text_overlay else None
                        })
                        results["total_ads"] += 1
                
                await asyncio.sleep(0.5)
        
        logger.info(f"✅ Generated {results['total_ads']} platform-optimized ads")
        return results


def create_social_media_ads_tools(api_token: str) -> SocialMediaAdsTools:
    """Factory function to create SocialMediaAdsTools instance."""
    return SocialMediaAdsTools(api_token)
