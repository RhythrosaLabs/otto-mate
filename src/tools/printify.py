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
        data: Optional[Dict] = None,
        retry_count: int = 3
    ) -> Dict[str, Any]:
        """Make API request to Printify with retry logic."""
        import asyncio
        
        url = f"{self.BASE_URL}{endpoint}"
        last_error = None
        
        for attempt in range(retry_count):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method,
                        url,
                        headers=self.headers,
                        json=data,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        result = await response.json()
                        
                        if response.status >= 400:
                            logger.error(f"Printify API error (attempt {attempt + 1}): {result}")
                            last_error = Exception(f"Printify API error: {result}")
                            if attempt < retry_count - 1:
                                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                                continue
                            raise last_error
                        
                        return result
            except aiohttp.ClientError as e:
                logger.error(f"Network error (attempt {attempt + 1}): {e}")
                last_error = e
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
        
        raise last_error or Exception("Request failed after retries")
    
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
        description="Upload an image to Printify from a URL",
        category="printify"
    )
    async def upload_image(
        self,
        image_url: str = None,
        filename: str = "design.png",
        file_name: str = None,  # Alias for filename (accepts both)
        image_path: str = None,  # Alias for image_url
        design_url: str = None,  # Alias for image_url
        design_image_url: str = None,  # Alias for image_url (accepts both)
        url: str = None  # Another alias for image_url
    ) -> Dict[str, Any]:
        """
        Upload an image to Printify.
        
        First downloads the image from the URL, then uploads the base64-encoded
        content to Printify. This approach works with both public URLs and 
        local/authenticated URLs.
        
        Args:
            image_url: URL of the image to upload
            filename: Name for the file on Printify
            file_name: Alias for filename (accepts both parameter names)
            image_path: Alias for image_url (accepts image_path parameter)
            url: Alias for image_url
            
        Returns:
            Dict with upload ID
        """
        # Handle aliases - resolve the actual image URL
        actual_url = image_url or image_path or design_url or design_image_url or url
        if not actual_url:
            raise ValueError("Must provide image_url, image_path, or url parameter")
        
        # Handle filename alias
        if file_name:
            filename = file_name
        import base64
        
        endpoint = "/uploads/images.json"
        
        # Download the image first
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(actual_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status != 200:
                        # Fallback: try URL-based upload if download fails
                        logger.warning(f"Could not download image (status {response.status}), trying URL upload")
                        data = {
                            "file_name": filename,
                            "url": actual_url
                        }
                        return await self._request("POST", endpoint, data)
                    
                    image_data = await response.read()
            except Exception as e:
                # Fallback: try URL-based upload if download fails
                logger.warning(f"Could not download image ({e}), trying URL upload")
                data = {
                    "file_name": filename,
                    "url": actual_url
                }
                return await self._request("POST", endpoint, data)
        
        # Base64 encode the image data
        encoded = base64.b64encode(image_data).decode("utf-8")
        
        # Upload using contents (base64) - this is more reliable than URL
        data = {
            "file_name": filename,
            "contents": encoded
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
    
    # Default fallbacks for common product types
    BLUEPRINT_DEFAULTS = {
        6: {"name": "Unisex Heavy Cotton Tee", "provider_id": 99, "provider_name": "Monster Digital"},  # Gildan 5000
        145: {"name": "Unisex Softstyle T-Shirt", "provider_id": 99, "provider_name": "Monster Digital"},  # Gildan 64000
        12: {"name": "Ceramic Mug 11oz", "provider_id": 28, "provider_name": "Duplium"},
        380: {"name": "Unisex Hoodie", "provider_id": 99, "provider_name": "Monster Digital"},
    }
    
    @tool(
        name="printify_get_print_providers",
        description="Get print providers for a blueprint",
        category="printify"
    )
    async def get_print_providers(self, blueprint_id: int) -> Dict[str, Any]:
        """Get print providers for a blueprint."""
        # Handle invalid blueprint_id (e.g., passed as string 'from_previous_step')
        if not isinstance(blueprint_id, int):
            try:
                blueprint_id = int(blueprint_id)
            except (ValueError, TypeError):
                # Default to Unisex Heavy Cotton Tee
                blueprint_id = 6
                logger.warning(f"Invalid blueprint_id, defaulting to {blueprint_id}")
        
        endpoint = f"/catalog/blueprints/{blueprint_id}/print_providers.json"
        try:
            return await self._request("GET", endpoint)
        except Exception as e:
            # Fallback to defaults if API fails
            if blueprint_id in self.BLUEPRINT_DEFAULTS:
                fallback = self.BLUEPRINT_DEFAULTS[blueprint_id]
                logger.warning(f"Print provider lookup failed, using fallback: {fallback}")
                return [{"id": fallback["provider_id"], "title": fallback["provider_name"]}]
            raise e
    
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

    @tool(
        name="printify_create_tshirt",
        description="Create a t-shirt product on Printify with a design image. This is a simplified helper that handles all the complexity automatically.",
        category="printify"
    )
    async def create_tshirt(
        self,
        title: str,
        description: str,
        image_url: str = None,
        image_path: str = None,  # Alias for image_url
        design_url: str = None,  # Alias for image_url
        design_image_url: str = None,  # Alias for image_url
        price_cents: int = 2499,
        blueprint_id: int = 6,  # Gildan 5000 by default
        print_provider_id: int = 99  # Monster Digital by default
    ) -> Dict[str, Any]:
        """
        Create a t-shirt product on Printify - simplified helper.
        
        This method handles all the complexity of:
        1. Uploading the image
        2. Getting variants
        3. Setting up print areas
        4. Creating the product
        
        Args:
            title: Product title
            description: Product description
            image_url: URL of the design image
            image_path: Alias for image_url
            price_cents: Price in cents (default 2499 = $24.99)
            blueprint_id: Blueprint ID (default 6 = Gildan 5000 Heavy Cotton Tee)
            print_provider_id: Provider ID (default 99 = Monster Digital)
            
        Returns:
            Dict with created product info
        """
        # Handle image_url alias
        actual_url = image_url or image_path or design_url or design_image_url
        if not actual_url:
            raise ValueError("Must provide image_url or image_path parameter")
        
        try:
            # Step 1: Upload the image
            logger.info(f"Uploading design image: {actual_url}")
            upload_result = await self.upload_image(actual_url, f"{title.replace(' ', '_')}.png")
            image_id = upload_result.get("id")
            
            if not image_id:
                raise Exception("Failed to upload image to Printify")
            
            logger.info(f"Image uploaded successfully: {image_id}")
            
            # Step 2: Get variants and placeholders
            variants_result = await self.get_variants(blueprint_id, print_provider_id)
            variants = variants_result.get("variants", [])
            
            if not variants:
                raise Exception("No variants available for this product")
            
            # Build variant list with pricing
            variant_list = []
            variant_ids = []
            for variant in variants:
                variant_list.append({
                    "id": variant["id"],
                    "price": price_cents,
                    "is_enabled": True
                })
                variant_ids.append(variant["id"])
            
            # Step 3: Build print areas
            print_areas = [{
                "variant_ids": variant_ids,
                "placeholders": [{
                    "position": "front",
                    "images": [{
                        "id": image_id,
                        "x": 0.5,
                        "y": 0.5,
                        "scale": 1.0,
                        "angle": 0
                    }]
                }]
            }]
            
            # Step 4: Create the product
            product_data = {
                "title": title,
                "description": description,
                "blueprint_id": blueprint_id,
                "print_provider_id": print_provider_id,
                "variants": variant_list,
                "print_areas": print_areas
            }
            
            endpoint = f"/shops/{self.shop_id}/products.json"
            result = await self._request("POST", endpoint, product_data)
            
            logger.info(f"T-shirt created successfully: {result.get('id')}")
            return {
                "success": True,
                "product_id": result.get("id"),
                "title": title,
                "image_id": image_id,
                "variants_count": len(variant_list),
                "product_url": f"https://printify.com/app/products/{result.get('id')}"
            }
            
        except Exception as e:
            logger.error(f"Failed to create t-shirt: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @tool(
        name="printify_create_mug",
        description="Create a mug product on Printify with a design image. This is a simplified helper that handles all the complexity automatically.",
        category="printify"
    )
    async def create_mug(
        self,
        title: str,
        description: str,
        image_url: str = None,
        image_path: str = None,  # Alias for image_url
        design_url: str = None,  # Alias for image_url
        design_image_url: str = None,  # Alias for image_url
        price_cents: int = 1499,
        blueprint_id: int = 12,  # Ceramic Mug 11oz by default
        print_provider_id: int = 28  # Duplium by default
    ) -> Dict[str, Any]:
        """
        Create a mug product on Printify - simplified helper.
        
        This method handles all the complexity of:
        1. Uploading the image
        2. Getting variants
        3. Setting up print areas
        4. Creating the product
        
        Args:
            title: Product title
            description: Product description
            image_url: URL of the design image
            image_path: Alias for image_url
            price_cents: Price in cents (default 1499 = $14.99)
            blueprint_id: Blueprint ID (default 12 = Ceramic Mug 11oz)
            print_provider_id: Provider ID (default 28 = Duplium)
            
        Returns:
            Dict with created product info
        """
        # Handle image_url alias
        actual_url = image_url or image_path or design_url or design_image_url
        if not actual_url:
            raise ValueError("Must provide image_url or image_path parameter")
        
        try:
            # Step 1: Upload the image
            logger.info(f"Uploading design image: {actual_url}")
            upload_result = await self.upload_image(actual_url, f"{title.replace(' ', '_')}_mug.png")
            image_id = upload_result.get("id")
            
            if not image_id:
                raise Exception("Failed to upload image to Printify")
            
            logger.info(f"Image uploaded successfully: {image_id}")
            
            # Step 2: Get variants and placeholders
            variants_result = await self.get_variants(blueprint_id, print_provider_id)
            variants = variants_result.get("variants", [])
            
            if not variants:
                raise Exception("No variants available for this product")
            
            # Build variant list with pricing
            variant_list = []
            variant_ids = []
            for variant in variants:
                variant_list.append({
                    "id": variant["id"],
                    "price": price_cents,
                    "is_enabled": True
                })
                variant_ids.append(variant["id"])
            
            # Step 3: Build print areas (mugs typically have "front" area)
            print_areas = [{
                "variant_ids": variant_ids,
                "placeholders": [{
                    "position": "front",
                    "images": [{
                        "id": image_id,
                        "x": 0.5,
                        "y": 0.5,
                        "scale": 1.0,
                        "angle": 0
                    }]
                }]
            }]
            
            # Step 4: Create the product
            product_data = {
                "title": title,
                "description": description,
                "blueprint_id": blueprint_id,
                "print_provider_id": print_provider_id,
                "variants": variant_list,
                "print_areas": print_areas
            }
            
            endpoint = f"/shops/{self.shop_id}/products.json"
            result = await self._request("POST", endpoint, product_data)
            
            logger.info(f"Mug created successfully: {result.get('id')}")
            return {
                "success": True,
                "product_id": result.get("id"),
                "title": title,
                "image_id": image_id,
                "variants_count": len(variant_list),
                "product_url": f"https://printify.com/app/products/{result.get('id')}"
            }
            
        except Exception as e:
            logger.error(f"Failed to create mug: {e}")
            return {
                "success": False,
                "error": str(e)
            }