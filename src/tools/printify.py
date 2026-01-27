"""
Printify Integration Tools
==========================

Tools for managing products on Printify.
"""

import logging
import aiohttp
from typing import Optional, Dict, Any, List
from .core import tool, ToolBase

logger = logging.getLogger(__name__)


class PrintifyTools(ToolBase):
    """Printify API integration tools."""
    
    BASE_URL = "https://api.printify.com/v1"
    
    def __init__(self, api_token: str, shop_id: str):
        self.api_token = api_token
        self.shop_id = shop_id
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make API request to Printify."""
        url = f"{self.BASE_URL}{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                url,
                headers=self.headers,
                json=data
            ) as response:
                result = await response.json()
                
                if response.status >= 400:
                    logger.error(f"Printify API error: {result}")
                    raise Exception(f"Printify API error: {result}")
                
                return result
    
    @tool(
        name="printify_list_products",
        description="List all products in the Printify shop",
        category="printify"
    )
    async def list_products(self, limit: int = 50, page: int = 1) -> Dict[str, Any]:
        """List products from Printify shop."""
        endpoint = f"/shops/{self.shop_id}/products.json?limit={limit}&page={page}"
        return await self._request("GET", endpoint)
    
    @tool(
        name="printify_get_product",
        description="Get details of a specific product",
        category="printify"
    )
    async def get_product(self, product_id: str) -> Dict[str, Any]:
        """Get a specific product."""
        endpoint = f"/shops/{self.shop_id}/products/{product_id}.json"
        return await self._request("GET", endpoint)
    
    @tool(
        name="printify_create_product",
        description="Create a new product on Printify with design",
        category="printify"
    )
    async def create_product(
        self,
        title: str,
        description: str,
        blueprint_id: int,
        print_provider_id: int,
        image_url: str,
        variants: Optional[List[Dict]] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new product on Printify.
        
        Args:
            title: Product title
            description: Product description
            blueprint_id: Printify blueprint ID (e.g., 6 for t-shirt)
            print_provider_id: Print provider ID
            image_url: URL of the design image
            variants: List of variant configurations
            tags: Product tags
        """
        # First, upload the image
        upload_result = await self.upload_image(image_url)
        image_id = upload_result.get("id")
        
        if not image_id:
            raise Exception("Failed to upload image to Printify")
        
        # Get blueprint placeholders
        placeholders = await self._get_blueprint_placeholders(
            blueprint_id,
            print_provider_id
        )
        
        # Build print areas
        print_areas = []
        for placeholder in placeholders:
            print_areas.append({
                "variant_ids": placeholder.get("variant_ids", []),
                "placeholders": [{
                    "position": placeholder.get("position", "front"),
                    "images": [{
                        "id": image_id,
                        "x": 0.5,
                        "y": 0.5,
                        "scale": 1.0,
                        "angle": 0
                    }]
                }]
            })
        
        # Build product data
        product_data = {
            "title": title,
            "description": description,
            "blueprint_id": blueprint_id,
            "print_provider_id": print_provider_id,
            "variants": variants or await self._get_default_variants(
                blueprint_id,
                print_provider_id
            ),
            "print_areas": print_areas
        }
        
        if tags:
            product_data["tags"] = tags
        
        endpoint = f"/shops/{self.shop_id}/products.json"
        return await self._request("POST", endpoint, product_data)
    
    @tool(
        name="printify_upload_image",
        description="Upload an image to Printify",
        category="printify"
    )
    async def upload_image(self, image_url: str, filename: str = "design.png") -> Dict[str, Any]:
        """Upload an image to Printify via URL."""
        endpoint = "/uploads/images.json"
        data = {
            "file_name": filename,
            "url": image_url
        }
        return await self._request("POST", endpoint, data)
    
    @tool(
        name="printify_publish_product",
        description="Publish a product to connected sales channels",
        category="printify"
    )
    async def publish_product(
        self,
        product_id: str,
        title: bool = True,
        description: bool = True,
        images: bool = True,
        variants: bool = True,
        tags: bool = True
    ) -> Dict[str, Any]:
        """Publish product to connected stores."""
        endpoint = f"/shops/{self.shop_id}/products/{product_id}/publish.json"
        data = {
            "title": title,
            "description": description,
            "images": images,
            "variants": variants,
            "tags": tags
        }
        return await self._request("POST", endpoint, data)
    
    @tool(
        name="printify_list_blueprints",
        description="List available product blueprints (t-shirts, mugs, etc.)",
        category="printify"
    )
    async def list_blueprints(self) -> Dict[str, Any]:
        """Get available blueprints."""
        return await self._request("GET", "/catalog/blueprints.json")
    
    @tool(
        name="printify_get_print_providers",
        description="Get print providers for a blueprint",
        category="printify"
    )
    async def get_print_providers(self, blueprint_id: int) -> Dict[str, Any]:
        """Get print providers for a blueprint."""
        endpoint = f"/catalog/blueprints/{blueprint_id}/print_providers.json"
        return await self._request("GET", endpoint)
    
    @tool(
        name="printify_get_variants",
        description="Get variants (sizes, colors) for a blueprint/provider",
        category="printify"
    )
    async def get_variants(
        self,
        blueprint_id: int,
        print_provider_id: int
    ) -> Dict[str, Any]:
        """Get variants for blueprint and provider."""
        endpoint = f"/catalog/blueprints/{blueprint_id}/print_providers/{print_provider_id}/variants.json"
        return await self._request("GET", endpoint)
    
    @tool(
        name="printify_delete_product",
        description="Delete a product from Printify",
        category="printify"
    )
    async def delete_product(self, product_id: str) -> Dict[str, Any]:
        """Delete a product."""
        endpoint = f"/shops/{self.shop_id}/products/{product_id}.json"
        return await self._request("DELETE", endpoint)
    
    @tool(
        name="printify_list_orders",
        description="List orders from Printify",
        category="printify"
    )
    async def list_orders(self, limit: int = 50, page: int = 1) -> Dict[str, Any]:
        """List orders."""
        endpoint = f"/shops/{self.shop_id}/orders.json?limit={limit}&page={page}"
        return await self._request("GET", endpoint)
    
    async def _get_blueprint_placeholders(
        self,
        blueprint_id: int,
        print_provider_id: int
    ) -> List[Dict]:
        """Get placeholder info for blueprint."""
        endpoint = f"/catalog/blueprints/{blueprint_id}/print_providers/{print_provider_id}/variants.json"
        result = await self._request("GET", endpoint)
        
        # Extract unique placeholders
        placeholders = {}
        for variant in result.get("variants", []):
            for placeholder in variant.get("placeholders", []):
                pos = placeholder.get("position", "front")
                if pos not in placeholders:
                    placeholders[pos] = {
                        "position": pos,
                        "variant_ids": []
                    }
                placeholders[pos]["variant_ids"].append(variant["id"])
        
        return list(placeholders.values())
    
    async def _get_default_variants(
        self,
        blueprint_id: int,
        print_provider_id: int
    ) -> List[Dict]:
        """Get default variant configuration."""
        result = await self.get_variants(blueprint_id, print_provider_id)
        
        variants = []
        for variant in result.get("variants", []):
            variants.append({
                "id": variant["id"],
                "price": 2999,  # $29.99 default
                "is_enabled": True
            })
        
        return variants
