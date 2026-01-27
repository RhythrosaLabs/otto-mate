"""
Shopify Integration Tools
=========================

Tools for managing Shopify store operations.
"""

import logging
import aiohttp
import base64
from typing import Optional, Dict, Any, List
from .core import tool, ToolBase

logger = logging.getLogger(__name__)


class ShopifyTools(ToolBase):
    """Shopify store management tools."""
    
    def __init__(
        self,
        shop_url: str,
        access_token: str,
        api_version: str = "2024-01"
    ):
        self.shop_url = shop_url.rstrip("/")
        self.access_token = access_token
        self.api_version = api_version
        self.base_url = f"https://{shop_url}/admin/api/{api_version}"
        self.headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json"
        }
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make API request to Shopify."""
        url = f"{self.base_url}{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                url,
                headers=self.headers,
                json=data
            ) as response:
                result = await response.json()
                
                if response.status >= 400:
                    logger.error(f"Shopify API error: {result}")
                    raise Exception(f"Shopify API error: {result}")
                
                return result
    
    @tool(
        name="shopify_list_products",
        description="List products from Shopify store",
        category="shopify"
    )
    async def list_products(
        self,
        limit: int = 50,
        status: str = "active"
    ) -> Dict[str, Any]:
        """List products from store."""
        endpoint = f"/products.json?limit={limit}&status={status}"
        return await self._request("GET", endpoint)
    
    @tool(
        name="shopify_create_product",
        description="Create a new product on Shopify",
        category="shopify"
    )
    async def create_product(
        self,
        title: str,
        body_html: str,
        vendor: str = "",
        product_type: str = "",
        tags: Optional[List[str]] = None,
        variants: Optional[List[Dict]] = None,
        images: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new product.
        
        Args:
            title: Product title
            body_html: Product description (HTML)
            vendor: Product vendor
            product_type: Product type
            tags: Product tags
            variants: Variant configurations
            images: List of image URLs
        """
        product_data = {
            "product": {
                "title": title,
                "body_html": body_html,
                "vendor": vendor,
                "product_type": product_type,
                "tags": ",".join(tags) if tags else "",
                "variants": variants or [{"price": "29.99"}]
            }
        }
        
        if images:
            product_data["product"]["images"] = [
                {"src": url} for url in images
            ]
        
        return await self._request("POST", "/products.json", product_data)
    
    @tool(
        name="shopify_update_product",
        description="Update an existing Shopify product",
        category="shopify"
    )
    async def update_product(
        self,
        product_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a product."""
        endpoint = f"/products/{product_id}.json"
        return await self._request("PUT", endpoint, {"product": updates})
    
    @tool(
        name="shopify_delete_product",
        description="Delete a product from Shopify",
        category="shopify"
    )
    async def delete_product(self, product_id: str) -> Dict[str, Any]:
        """Delete a product."""
        endpoint = f"/products/{product_id}.json"
        return await self._request("DELETE", endpoint)
    
    @tool(
        name="shopify_list_orders",
        description="List orders from Shopify store",
        category="shopify"
    )
    async def list_orders(
        self,
        status: str = "any",
        limit: int = 50
    ) -> Dict[str, Any]:
        """List orders."""
        endpoint = f"/orders.json?status={status}&limit={limit}"
        return await self._request("GET", endpoint)
    
    @tool(
        name="shopify_get_order",
        description="Get details of a specific order",
        category="shopify"
    )
    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get order details."""
        endpoint = f"/orders/{order_id}.json"
        return await self._request("GET", endpoint)
    
    @tool(
        name="shopify_create_blog_post",
        description="Create a blog post on Shopify",
        category="shopify"
    )
    async def create_blog_post(
        self,
        blog_id: str,
        title: str,
        body_html: str,
        author: str = "",
        tags: Optional[List[str]] = None,
        published: bool = True,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a blog post.
        
        Args:
            blog_id: ID of the blog to post to
            title: Post title
            body_html: Post content (HTML)
            author: Author name
            tags: Post tags
            published: Whether to publish immediately
            image_url: Featured image URL
        """
        article_data = {
            "article": {
                "title": title,
                "body_html": body_html,
                "author": author,
                "tags": ",".join(tags) if tags else "",
                "published": published
            }
        }
        
        if image_url:
            article_data["article"]["image"] = {"src": image_url}
        
        endpoint = f"/blogs/{blog_id}/articles.json"
        return await self._request("POST", endpoint, article_data)
    
    @tool(
        name="shopify_list_blogs",
        description="List blogs on Shopify store",
        category="shopify"
    )
    async def list_blogs(self) -> Dict[str, Any]:
        """List all blogs."""
        return await self._request("GET", "/blogs.json")
    
    @tool(
        name="shopify_list_collections",
        description="List product collections",
        category="shopify"
    )
    async def list_collections(self) -> Dict[str, Any]:
        """List collections."""
        custom = await self._request("GET", "/custom_collections.json")
        smart = await self._request("GET", "/smart_collections.json")
        
        return {
            "custom_collections": custom.get("custom_collections", []),
            "smart_collections": smart.get("smart_collections", [])
        }
    
    @tool(
        name="shopify_add_to_collection",
        description="Add a product to a collection",
        category="shopify"
    )
    async def add_to_collection(
        self,
        collection_id: str,
        product_id: str
    ) -> Dict[str, Any]:
        """Add product to collection."""
        data = {
            "collect": {
                "product_id": product_id,
                "collection_id": collection_id
            }
        }
        return await self._request("POST", "/collects.json", data)
    
    @tool(
        name="shopify_get_analytics",
        description="Get store analytics overview",
        category="shopify"
    )
    async def get_analytics(self) -> Dict[str, Any]:
        """Get basic store analytics."""
        # Get recent orders
        orders = await self.list_orders(limit=50)
        
        # Calculate basic stats
        total_revenue = sum(
            float(o.get("total_price", 0))
            for o in orders.get("orders", [])
        )
        
        order_count = len(orders.get("orders", []))
        
        # Get product count
        products = await self.list_products(limit=250)
        product_count = len(products.get("products", []))
        
        return {
            "total_orders_recent": order_count,
            "total_revenue_recent": total_revenue,
            "average_order_value": total_revenue / order_count if order_count > 0 else 0,
            "total_products": product_count
        }
    
    @tool(
        name="shopify_update_inventory",
        description="Update inventory levels for a product",
        category="shopify"
    )
    async def update_inventory(
        self,
        inventory_item_id: str,
        location_id: str,
        available: int
    ) -> Dict[str, Any]:
        """Update inventory quantity."""
        data = {
            "location_id": location_id,
            "inventory_item_id": inventory_item_id,
            "available": available
        }
        return await self._request("POST", "/inventory_levels/set.json", data)
