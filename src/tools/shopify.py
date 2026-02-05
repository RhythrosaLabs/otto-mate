"""
Shopify Integration Tools
=========================

Tools for managing Shopify store operations.
Supports both REST and GraphQL APIs.
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
        api_version: str = "2024-10"  # Updated to latest API version
    ):
        self.shop_url = shop_url.rstrip("/")
        self.access_token = access_token
        self.api_version = api_version
        self.base_url = f"https://{shop_url}/admin/api/{api_version}"
        self.graphql_url = f"https://{shop_url}/admin/api/{api_version}/graphql.json"
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
        """Make API request to Shopify REST API."""
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
    
    async def _graphql_request(
        self,
        query: str,
        variables: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make GraphQL request to Shopify."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.graphql_url,
                headers=self.headers,
                json=payload
            ) as response:
                result = await response.json()
                
                if response.status >= 400:
                    logger.error(f"Shopify GraphQL error: {result}")
                    raise Exception(f"Shopify GraphQL error: {result}")
                
                if "errors" in result:
                    logger.error(f"Shopify GraphQL errors: {result['errors']}")
                    raise Exception(f"GraphQL errors: {result['errors']}")
                
                return result.get("data", {})
    
    @tool(
        name="shopify_list_products",
        description="List products from Shopify store. Returns total_count and summary with product details. IMPORTANT: Check the 'total_count' field for the actual number of products.",
        category="shopify"
    )
    async def list_products(
        self,
        limit: int = 250,
        status: str = "active",
        fields: str = None  # Optional: comma-separated fields like "id,title,status"
    ) -> Dict[str, Any]:
        """List products from store."""
        endpoint = f"/products.json?limit={limit}&status={status}"
        if fields:
            endpoint += f"&fields={fields}"
        result = await self._request("GET", endpoint)
        
        # Add helpful summary - THIS IS THE KEY DATA
        products = result.get("products", [])
        total = len(products)
        
        # Put summary FIRST so AI sees it
        return {
            "total_count": total,
            "summary": f"Found {total} {status} products in your Shopify store",
            "product_titles": [p.get("title", "Untitled") for p in products[:20]] + 
                             ([f"... and {total - 20} more"] if total > 20 else []),
            "products": products  # Full data at the end
        }
    
    @tool(
        name="shopify_get_product_count",
        description="Get the total count of products in the Shopify store. Use this when user asks how many products are listed.",
        category="shopify"
    )
    async def get_product_count(
        self,
        status: str = "active"
    ) -> Dict[str, Any]:
        """Get product count from store."""
        endpoint = f"/products/count.json?status={status}"
        result = await self._request("GET", endpoint)
        count = result.get("count", 0)
        return {
            "count": count,
            "status": status,
            "message": f"Your Shopify store has {count} {status} products"
        }
    
    @tool(
        name="shopify_create_product",
        description="Create a new product on Shopify",
        category="shopify"
    )
    async def create_product(
        self,
        title: str,
        body_html: str = None,
        vendor: str = "",
        product_type: str = "",
        tags: Optional[List[str]] = None,
        variants: Optional[List[str]] = None,
        images: Optional[List[str]] = None,
        price: str = "29.99",
        status: str = "draft",
        # Common aliases
        product_title: str = None,
        description: str = None,
        product_description: str = None,
        image_url: str = None,
        image_urls: List[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new product.
        
        Args:
            title: Product title
            body_html: Product description (HTML or plain text - will be converted)
            vendor: Product vendor
            product_type: Product type
            tags: Product tags
            variants: Variant configurations
            images: List of image URLs
            price: Default price if no variants specified
            status: Product status (draft, active, archived)
            product_title: Alias for title
            description: Alias for body_html
            product_description: Alias for body_html
            image_url: Single image URL (alias)
            image_urls: Alias for images
        """
        # Handle aliases
        title = title or product_title
        body_html = body_html or description or product_description or ""
        
        # Handle image aliases
        if not images:
            if image_urls:
                images = image_urls
            elif image_url:
                images = [image_url]
        
        # Convert plain text to HTML if needed
        if body_html and not body_html.strip().startswith('<'):
            # Simple conversion: replace newlines with <br> and wrap in <p>
            body_html = body_html.replace('\n\n', '</p><p>').replace('\n', '<br>')
            body_html = f'<p>{body_html}</p>'
        
        product_data = {
            "product": {
                "title": title,
                "body_html": body_html or "",
                "vendor": vendor,
                "product_type": product_type,
                "tags": ",".join(tags) if tags else "",
                "status": status,
                "variants": variants or [{"price": price}]
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
        description="Create a blog post on Shopify. Auto-discovers the blog if blog_id is not provided.",
        category="shopify"
    )
    async def create_blog_post(
        self,
        title: str,
        body_html: str,
        blog_id: str = None,
        blog_name: str = None,
        author: str = "",
        tags: Optional[List[str]] = None,
        published: bool = True,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a blog post on Shopify.
        
        This tool will auto-discover the blog if blog_id is not provided.
        It will look for a blog matching blog_name, or use the first available blog.
        
        Args:
            title: Post title (required)
            body_html: Post content in HTML format (required)
            blog_id: ID of the blog to post to (optional - will auto-discover)
            blog_name: Name of the blog to post to (optional - for auto-discovery)
            author: Author name
            tags: Post tags as list
            published: Whether to publish immediately (default True)
            image_url: Featured image URL
        
        Returns:
            Dict with article data or error information
        """
        try:
            blog_handle = None  # Will be set during blog discovery
            
            # Auto-discover blog ID if not provided
            if not blog_id:
                logger.info("Auto-discovering Shopify blog...")
                blogs_response = await self.list_blogs()
                blogs = blogs_response.get("blogs", [])
                
                if not blogs:
                    # Create a default blog if none exists
                    logger.info("No blogs found, creating default 'News' blog...")
                    try:
                        create_blog_result = await self._request("POST", "/blogs.json", {
                            "blog": {
                                "title": "News",
                                "commentable": "moderate"
                            }
                        })
                        blog_id = create_blog_result.get("blog", {}).get("id")
                        blog_handle = create_blog_result.get("blog", {}).get("handle", "news")
                        logger.info(f"Created blog 'News' with ID: {blog_id}, handle: {blog_handle}")
                    except Exception as e:
                        logger.error(f"Failed to create blog: {e}")
                        return {
                            "success": False,
                            "error": "No blogs exist and failed to create one",
                            "message": f"Please create a blog in Shopify admin first, or check API permissions: {e}"
                        }
                else:
                    # Find matching blog by name or use first one
                    if blog_name:
                        for blog in blogs:
                            if blog_name.lower() in blog.get("title", "").lower():
                                blog_id = blog.get("id")
                                blog_handle = blog.get("handle")
                                logger.info(f"Found matching blog: {blog.get('title')} (ID: {blog_id}, handle: {blog_handle})")
                                break
                    
                    if not blog_id:
                        blog_id = blogs[0].get("id")
                        blog_handle = blogs[0].get("handle")
                        logger.info(f"Using first available blog: {blogs[0].get('title')} (ID: {blog_id}, handle: {blog_handle})")
                    else:
                        # blog_id was set but blog_handle wasn't
                        if not blog_handle:
                            for blog in blogs:
                                if blog.get("id") == blog_id:
                                    blog_handle = blog.get("handle")
                                    break
            
            if not blog_id:
                return {
                    "success": False,
                    "error": "Could not find or create a blog",
                    "message": "Please create a blog in Shopify admin first"
                }
            
            # If we still don't have blog_handle, fetch it
            if not blog_handle:
                try:
                    blog_response = await self._request("GET", f"/blogs/{blog_id}.json")
                    blog_handle = blog_response.get("blog", {}).get("handle", str(blog_id))
                except:
                    blog_handle = str(blog_id)  # Fallback to ID
            
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
            result = await self._request("POST", endpoint, article_data)
            
            article = result.get("article", {})
            article_handle = article.get("handle", "")
            
            return {
                "success": True,
                "article_id": article.get("id"),
                "title": article.get("title"),
                "blog_id": blog_id,
                "blog_handle": blog_handle,
                "article_handle": article_handle,
                "url": f"https://{self.shop_url}/blogs/{blog_handle}/{article_handle}",
                "published": article.get("published_at") is not None
            }
            
        except Exception as e:
            logger.error(f"Failed to create blog post: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create blog post: {str(e)}"
            }
    
    @tool(
        name="shopify_list_blogs",
        description="List blogs on Shopify store",
        category="shopify"
    )
    async def list_blogs(self) -> Dict[str, Any]:
        """List all blogs."""
        return await self._request("GET", "/blogs.json")
    
    @tool(
        name="shopify_create_blog_article_graphql",
        description="Create a blog article using GraphQL API (more features). Supports scheduling, summary, SEO handle, and more.",
        category="shopify"
    )
    async def create_blog_article_graphql(
        self,
        title: str,
        body: str,
        blog_id: str = None,
        blog_handle: str = None,
        author_name: str = None,
        summary: str = None,
        tags: Optional[List[str]] = None,
        handle: str = None,
        published: bool = True,
        publish_date: str = None,
        image_url: str = None,
        image_alt_text: str = None
    ) -> Dict[str, Any]:
        """
        Create a blog article using Shopify GraphQL API.
        
        This provides more capabilities than the REST API:
        - Schedule posts for future publication
        - Set custom URL handles for SEO
        - Add summary/excerpt
        - Better image handling with alt text
        
        Args:
            title: Article title (required)
            body: Article content in HTML format (required)
            blog_id: Blog GID (e.g., "gid://shopify/Blog/123456") 
            blog_handle: Blog handle to find blog (alternative to blog_id)
            author_name: Author name
            summary: Article summary/excerpt
            tags: Article tags
            handle: URL handle (auto-generated from title if not provided)
            published: Publish immediately (True) or save as draft (False)
            publish_date: ISO8601 date for scheduled publishing (e.g., "2024-03-15T10:00:00Z")
            image_url: Featured image URL
            image_alt_text: Alt text for image
        
        Returns:
            Dict with article data or error
        """
        try:
            # Find blog if not provided
            if not blog_id:
                blogs_response = await self.list_blogs()
                blogs = blogs_response.get("blogs", [])
                
                if not blogs:
                    return {
                        "success": False,
                        "error": "No blogs found",
                        "message": "Please create a blog in Shopify admin first"
                    }
                
                # Find by handle or use first blog
                target_blog = None
                if blog_handle:
                    for blog in blogs:
                        if blog.get("handle", "").lower() == blog_handle.lower():
                            target_blog = blog
                            break
                
                if not target_blog:
                    target_blog = blogs[0]
                
                blog_id = f"gid://shopify/Blog/{target_blog['id']}"
                logger.info(f"Using blog: {target_blog.get('title')} (ID: {blog_id})")
            
            # Ensure blog_id is in GID format
            if not blog_id.startswith("gid://"):
                blog_id = f"gid://shopify/Blog/{blog_id}"
            
            # Build the mutation
            mutation = """
            mutation articleCreate($article: ArticleCreateInput!) {
                articleCreate(article: $article) {
                    article {
                        id
                        handle
                        title
                        publishedAt
                        blog {
                            id
                            handle
                        }
                    }
                    userErrors {
                        field
                        message
                    }
                }
            }
            """
            
            # Build article input
            article_input = {
                "blogId": blog_id,
                "title": title,
                "body": body,
                "isPublished": published
            }
            
            if author_name:
                article_input["author"] = {"name": author_name}
            if summary:
                article_input["summary"] = summary
            if tags:
                article_input["tags"] = tags
            if handle:
                article_input["handle"] = handle
            if publish_date:
                article_input["publishDate"] = publish_date
            if image_url:
                image_data = {"url": image_url}
                if image_alt_text:
                    image_data["altText"] = image_alt_text
                article_input["image"] = image_data
            
            # Execute mutation
            result = await self._graphql_request(mutation, {"article": article_input})
            
            article_data = result.get("articleCreate", {})
            user_errors = article_data.get("userErrors", [])
            
            if user_errors:
                return {
                    "success": False,
                    "error": user_errors[0].get("message"),
                    "errors": user_errors
                }
            
            article = article_data.get("article", {})
            blog_data = article.get("blog", {})
            
            return {
                "success": True,
                "article_id": article.get("id"),
                "title": title,
                "handle": article.get("handle"),
                "blog_id": blog_data.get("id"),
                "blog_handle": blog_data.get("handle"),
                "url": f"https://{self.shop_url}/blogs/{blog_data.get('handle')}/{article.get('handle')}",
                "published_at": article.get("publishedAt"),
                "published": article.get("publishedAt") is not None
            }
            
        except Exception as e:
            logger.error(f"GraphQL article creation failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create article via GraphQL: {str(e)}"
            }
    
    @tool(
        name="shopify_update_product_price",
        description="Update the price of a Shopify product variant",
        category="shopify"
    )
    async def update_product_price(
        self,
        product_id: str = None,
        variant_id: str = None,
        price: float = None,
        compare_at_price: float = None
    ) -> Dict[str, Any]:
        """
        Update product/variant pricing on Shopify.
        
        Args:
            product_id: Product ID (will update all variants)
            variant_id: Specific variant ID to update
            price: New price (e.g., 29.99)
            compare_at_price: Compare at price for showing discounts
        
        Returns:
            Dict with update status
        """
        try:
            if not price:
                return {"success": False, "error": "Price is required"}
            
            # Convert price to string format
            price_str = f"{price:.2f}"
            compare_str = f"{compare_at_price:.2f}" if compare_at_price else None
            
            if variant_id:
                # Update specific variant
                variant_data = {"variant": {"price": price_str}}
                if compare_str:
                    variant_data["variant"]["compare_at_price"] = compare_str
                
                result = await self._request(
                    "PUT",
                    f"/variants/{variant_id}.json",
                    variant_data
                )
                
                return {
                    "success": True,
                    "variant_id": variant_id,
                    "new_price": price,
                    "compare_at_price": compare_at_price,
                    "variant": result.get("variant", {})
                }
            
            elif product_id:
                # Update all variants of a product
                product = await self._request("GET", f"/products/{product_id}.json")
                variants = product.get("product", {}).get("variants", [])
                
                updated_variants = []
                for variant in variants:
                    variant_data = {"variant": {"price": price_str}}
                    if compare_str:
                        variant_data["variant"]["compare_at_price"] = compare_str
                    
                    result = await self._request(
                        "PUT",
                        f"/variants/{variant['id']}.json",
                        variant_data
                    )
                    updated_variants.append({
                        "id": variant['id'],
                        "title": variant.get("title"),
                        "new_price": price
                    })
                
                return {
                    "success": True,
                    "product_id": product_id,
                    "new_price": price,
                    "compare_at_price": compare_at_price,
                    "variants_updated": len(updated_variants),
                    "variants": updated_variants
                }
            
            else:
                return {"success": False, "error": "Must provide product_id or variant_id"}
                
        except Exception as e:
            logger.error(f"Failed to update price: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to update product price: {str(e)}"
            }
    
    @tool(
        name="shopify_create_blog",
        description="Create a new blog on Shopify store",
        category="shopify"
    )
    async def create_blog(
        self,
        title: str,
        handle: str = None,
        commentable: str = "moderate"
    ) -> Dict[str, Any]:
        """
        Create a new blog.
        
        Args:
            title: Blog title
            handle: URL handle (auto-generated if not provided)
            commentable: Comment policy ("no", "moderate", "yes")
        """
        try:
            blog_data = {
                "blog": {
                    "title": title,
                    "commentable": commentable
                }
            }
            
            if handle:
                blog_data["blog"]["handle"] = handle
            
            result = await self._request("POST", "/blogs.json", blog_data)
            blog = result.get("blog", {})
            
            return {
                "success": True,
                "blog_id": blog.get("id"),
                "title": blog.get("title"),
                "handle": blog.get("handle"),
                "url": f"https://{self.shop_url}/blogs/{blog.get('handle')}"
            }
            
        except Exception as e:
            logger.error(f"Failed to create blog: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create blog: {str(e)}"
            }
    
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
        collection_id: int,
        product_id: int
    ) -> Dict[str, Any]:
        """Add product to collection."""
        # Ensure IDs are integers
        collection_id = int(collection_id) if isinstance(collection_id, str) else collection_id
        product_id = int(product_id) if isinstance(product_id, str) else product_id
        
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
    
    @tool(
        name="shopify_get_top_products",
        description="Get top-selling products with sales data. Analyzes recent orders to determine which products sell best.",
        category="shopify"
    )
    async def get_top_products(
        self,
        limit: int = 10,
        orders_to_analyze: int = 250
    ) -> Dict[str, Any]:
        """
        Analyze orders to determine top-selling products.
        
        Args:
            limit: Number of top products to return
            orders_to_analyze: Number of recent orders to analyze
            
        Returns:
            Dict with top products ranked by sales count, revenue, and details
        """
        try:
            # Get recent orders
            orders_result = await self.list_orders(status="any", limit=orders_to_analyze)
            orders = orders_result.get("orders", [])
            
            # Count sales by product
            product_sales = {}  # product_id -> {title, count, revenue, orders}
            
            for order in orders:
                line_items = order.get("line_items", [])
                
                for item in line_items:
                    product_id = item.get("product_id")
                    if not product_id:
                        continue
                    
                    quantity = int(item.get("quantity", 1))
                    price = float(item.get("price", 0))
                    revenue = quantity * price
                    
                    if product_id not in product_sales:
                        product_sales[product_id] = {
                            "product_id": product_id,
                            "title": item.get("title", "Unknown"),
                            "units_sold": 0,
                            "total_revenue": 0,
                            "order_count": 0
                        }
                    
                    product_sales[product_id]["units_sold"] += quantity
                    product_sales[product_id]["total_revenue"] += revenue
                    product_sales[product_id]["order_count"] += 1
            
            # Sort by units sold
            sorted_products = sorted(
                product_sales.values(),
                key=lambda x: x["units_sold"],
                reverse=True
            )[:limit]
            
            # Calculate additional metrics
            for product in sorted_products:
                product["average_order_value"] = (
                    product["total_revenue"] / product["order_count"]
                    if product["order_count"] > 0 else 0
                )
                product["total_revenue"] = round(product["total_revenue"], 2)
            
            return {
                "top_products": sorted_products,
                "orders_analyzed": len(orders),
                "total_products_found": len(product_sales)
            }
            
        except Exception as e:
            logger.error(f"Failed to get top products: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to analyze top products"
            }
    
    @tool(
        name="shopify_get_product_performance",
        description="Get detailed performance metrics for a specific product including sales, revenue, and order history",
        category="shopify"
    )
    async def get_product_performance(
        self,
        product_id: str,
        orders_to_analyze: int = 250
    ) -> Dict[str, Any]:
        """
        Get detailed performance metrics for a specific product.
        
        Args:
            product_id: The Shopify product ID
            orders_to_analyze: Number of recent orders to analyze
            
        Returns:
            Dict with product performance metrics
        """
        try:
            # Get product details
            product_result = await self._request("GET", f"/products/{product_id}.json")
            product = product_result.get("product", {})
            
            # Get recent orders
            orders_result = await self.list_orders(status="any", limit=orders_to_analyze)
            orders = orders_result.get("orders", [])
            
            # Analyze orders containing this product
            units_sold = 0
            total_revenue = 0
            order_count = 0
            orders_list = []
            
            for order in orders:
                found_product = False
                for item in order.get("line_items", []):
                    if str(item.get("product_id")) == str(product_id):
                        found_product = True
                        quantity = int(item.get("quantity", 1))
                        price = float(item.get("price", 0))
                        
                        units_sold += quantity
                        total_revenue += quantity * price
                        
                if found_product:
                    order_count += 1
                    orders_list.append({
                        "order_id": order.get("id"),
                        "order_number": order.get("order_number"),
                        "created_at": order.get("created_at"),
                        "total_price": order.get("total_price")
                    })
            
            return {
                "product_id": product_id,
                "product_title": product.get("title"),
                "product_type": product.get("product_type"),
                "vendor": product.get("vendor"),
                "units_sold": units_sold,
                "total_revenue": round(total_revenue, 2),
                "order_count": order_count,
                "average_order_value": round(total_revenue / order_count, 2) if order_count > 0 else 0,
                "recent_orders": orders_list[:10],  # Last 10 orders
                "created_at": product.get("created_at"),
                "updated_at": product.get("updated_at")
            }
            
        except Exception as e:
            logger.error(f"Failed to get product performance: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to analyze product {product_id}"
            }
    
    @tool(
        name="shopify_get_sales_summary",
        description="Get comprehensive sales summary including revenue, order statistics, and trends",
        category="shopify"
    )
    async def get_sales_summary(
        self,
        orders_to_analyze: int = 250
    ) -> Dict[str, Any]:
        """
        Get comprehensive sales summary with detailed metrics.
        
        Args:
            orders_to_analyze: Number of recent orders to analyze
            
        Returns:
            Dict with comprehensive sales metrics
        """
        try:
            # Get recent orders
            orders_result = await self.list_orders(status="any", limit=orders_to_analyze)
            orders = orders_result.get("orders", [])
            
            if not orders:
                return {
                    "total_orders": 0,
                    "total_revenue": 0,
                    "message": "No orders found"
                }
            
            # Calculate metrics
            total_revenue = sum(float(o.get("total_price", 0)) for o in orders)
            total_orders = len(orders)
            
            # Get order statuses
            status_counts = {}
            for order in orders:
                status = order.get("financial_status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Get top customers
            customer_orders = {}
            for order in orders:
                customer_id = order.get("customer", {}).get("id")
                if customer_id:
                    if customer_id not in customer_orders:
                        customer_orders[customer_id] = {
                            "email": order.get("customer", {}).get("email", "Unknown"),
                            "order_count": 0,
                            "total_spent": 0
                        }
                    customer_orders[customer_id]["order_count"] += 1
                    customer_orders[customer_id]["total_spent"] += float(order.get("total_price", 0))
            
            top_customers = sorted(
                customer_orders.values(),
                key=lambda x: x["total_spent"],
                reverse=True
            )[:5]
            
            return {
                "total_orders": total_orders,
                "total_revenue": round(total_revenue, 2),
                "average_order_value": round(total_revenue / total_orders, 2),
                "orders_analyzed": orders_to_analyze,
                "status_breakdown": status_counts,
                "top_customers": top_customers,
                "date_range": {
                    "earliest_order": orders[-1].get("created_at") if orders else None,
                    "latest_order": orders[0].get("created_at") if orders else None
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get sales summary: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to generate sales summary"
            }
    
    @tool(
        name="shopify_write_and_publish_blog",
        description="Write a beautiful, SEO-optimized blog post with rich HTML and publish directly to Shopify. All-in-one blog creation and publishing. Pass the topic/title of the blog post.",
        category="shopify"
    )
    async def write_and_publish_blog(
        self,
        topic: str = None,
        title: str = None,  # Alias for topic
        content_brief: str = None,  # Additional context for content
        keywords: Optional[List[str]] = None,
        target_demographic: str = "general",
        style: str = "informative",
        word_count: int = 1200,
        blog_name: str = None,
        author: str = "Team",
        tags: Optional[List[str]] = None,
        published: bool = True,
        include_trending: bool = True,
        include_statistics: bool = True,
        product_links: Optional[List[str]] = None,
        cta_type: str = "product",
        brand_voice: str = "professional yet approachable",
        featured_image_url: Optional[str] = None,
        seo_focused: bool = True  # Alias parameter
    ) -> Dict[str, Any]:
        """
        Write and publish a complete, SEO-optimized blog post directly to Shopify.
        
        This is an all-in-one tool that:
        1. Generates beautiful, rich HTML content
        2. Optimizes for SEO with proper structure
        3. Targets your specific demographic
        4. Includes trending topics and statistics
        5. Publishes directly to your Shopify blog
        
        Args:
            topic: Blog post topic (or use 'title')
            title: Alias for topic - the blog post title/topic
            content_brief: Additional context or instructions for the blog content
            keywords: SEO keywords to include naturally
            target_demographic: Target audience (gen-z, millennials, professionals, parents, entrepreneurs)
            style: Writing style (informative, entertaining, tutorial, listicle, storytelling)
            word_count: Target word count (default 1200 for SEO)
            blog_name: Shopify blog name (auto-discovers if not provided)
            author: Author name
            tags: Post tags for organization
            published: Publish immediately (True) or save as draft (False)
            include_trending: Include current trends and timely references
            include_statistics: Include relevant statistics
            product_links: Product URLs to link within content
            cta_type: CTA type (product, newsletter, social)
            brand_voice: Brand personality description
            featured_image_url: Featured image URL
            seo_focused: Whether to focus on SEO (default True)
        """
        # Handle title as alias for topic
        if topic is None and title is not None:
            topic = title
        
        # Use content_brief to enhance topic if provided
        if content_brief and topic:
            topic = f"{topic} - {content_brief}"
        elif content_brief and not topic:
            topic = content_brief
            
        if not topic:
            return {"success": False, "error": "Please provide a topic or title for the blog post"}
        
        try:
            # Import anthropic for content generation
            from anthropic import Anthropic
            import os
            
            anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            
            # Demographic-specific guidance
            demo_guide = {
                "gen-z": "Use casual language, current slang (appropriately), reference social media trends, TikTok-friendly formatting, short punchy paragraphs, lots of emojis where appropriate",
                "millennials": "Balance nostalgia with current relevance, include pop culture references, relatable humor, value-focused content, authentic voice",
                "professionals": "Data-driven, efficiency-focused, industry insights, actionable takeaways, professional but not stuffy, cite sources",
                "parents": "Time-saving tips, family-focused benefits, relatable struggles, practical solutions, trustworthy tone",
                "entrepreneurs": "ROI-focused, growth strategies, case studies, actionable frameworks, inspiring success stories",
                "general": "Broad appeal, accessible language, universal benefits, diverse examples"
            }
            demographic_guidance = demo_guide.get(target_demographic.lower(), demo_guide["general"])
            
            keywords_text = ", ".join(keywords) if keywords else "relevant terms"
            product_text = f"\\nProducts to link: " + ", ".join(product_links) if product_links else ""
            
            system_prompt = f"""You are an elite content strategist and SEO copywriter.

Brand Voice: {brand_voice}
Target Demographic: {target_demographic}
Writing Guide: {demographic_guidance}

Your content is known for:
- Exceptional readability and engagement
- Natural keyword integration
- Compelling hooks that stop scrollers
- Value-packed content that gets shared
- Perfect SEO structure (H1, H2, H3 hierarchy)
- Beautiful, professional HTML formatting
- Mobile-friendly formatting"""

            user_prompt = f"""Write a {word_count}-word blog post about: {topic}

PRIMARY SEO KEYWORDS (use naturally 3-5 times each): {keywords_text}
{product_text}

OUTPUT AS BEAUTIFUL HTML with these elements:

1. TITLE: Create a powerful headline with primary keyword

2. INTRO (150-200 words): Hook + relevance + preview value

3. BODY SECTIONS (5-7 H2 sections):
   - Use <h2> for main sections, <h3> for subsections
   - Short paragraphs (2-3 sentences max)
   - Include styled call-out boxes:
     * Key insight: <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; color: white; margin: 20px 0;"><strong>💡 Key Insight:</strong> [content]</div>
     * Pro tip: <div style="background: #f0fdf4; border-left: 4px solid #22c55e; padding: 16px; margin: 20px 0;"><strong>✨ Pro Tip:</strong> [content]</div>
   {"- Include 2-3 relevant statistics" if include_statistics else ""}
   {"- Reference current trends" if include_trending else ""}

4. BLOCKQUOTES for impact:
   <blockquote style="font-size: 1.25em; font-style: italic; border-left: 4px solid #8b5cf6; padding-left: 20px; margin: 30px 0; color: #4b5563;">"Quote"</blockquote>

5. CTA SECTION (end):
   <div style="text-align: center; margin: 40px 0; padding: 30px; background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%); border-radius: 16px;">
   <h3 style="margin-bottom: 15px;">Ready to [action]?</h3>
   <p style="margin-bottom: 20px; color: #4b5563;">[Compelling CTA text]</p>
   <a href="#" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 16px 32px; border-radius: 30px; text-decoration: none; font-weight: bold;">🚀 [CTA Button Text]</a>
   </div>

6. FAQ SECTION (good for SEO):
   <h2>Frequently Asked Questions</h2>
   [3-4 relevant Q&As]

OUTPUT ONLY THE HTML BODY CONTENT - NO <html>, <head>, or <body> tags.
Start directly with the content HTML."""

            # Generate content
            response = anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8192,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            
            body_html = response.content[0].text
            
            # Clean up any accidental full HTML structure
            if "<html" in body_html.lower() or "<!doctype" in body_html.lower():
                import re
                body_match = re.search(r'<body[^>]*>(.*?)</body>', body_html, re.DOTALL | re.IGNORECASE)
                if body_match:
                    body_html = body_match.group(1)
            
            # Extract title from content if H1 exists
            import re
            title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', body_html, re.IGNORECASE)
            if title_match:
                extracted_title = title_match.group(1).strip()
                # Remove H1 from body (Shopify uses title separately)
                body_html = re.sub(r'<h1[^>]*>[^<]+</h1>', '', body_html, count=1)
            else:
                extracted_title = topic.title()
            
            # Auto-generate tags from keywords if not provided
            if not tags and keywords:
                tags = keywords[:5]
            
            # Publish to Shopify
            result = await self.create_blog_post(
                title=extracted_title,
                body_html=body_html,
                blog_name=blog_name,
                author=author,
                tags=tags,
                published=published,
                image_url=featured_image_url
            )
            
            if result.get("success"):
                return {
                    "success": True,
                    "message": f"Blog post '{extracted_title}' {'published' if published else 'saved as draft'} to Shopify!",
                    "article_id": result.get("article_id"),
                    "title": extracted_title,
                    "url": result.get("url"),
                    "blog_id": result.get("blog_id"),
                    "word_count": len(body_html.split()),
                    "target_demographic": target_demographic,
                    "keywords_used": keywords,
                    "published": published
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error"),
                    "message": "Content was generated but failed to publish to Shopify",
                    "generated_content": body_html[:500] + "..." if len(body_html) > 500 else body_html
                }
                
        except Exception as e:
            logger.error(f"Failed to write and publish blog: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to write and publish blog: {str(e)}"
            }
