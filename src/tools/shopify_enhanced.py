"""
Enhanced Shopify Integration Tools
==================================

Extended Shopify capabilities for Otto:
- Full product sync and pull operations
- Smart product editing with natural language
- One-click publishing workflows
- Analytics and insights
- Smart inventory management
- SEO optimization tools
- Store health monitoring
"""

import logging
import aiohttp
import json
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from .core import tool, ToolBase

logger = logging.getLogger(__name__)


@dataclass
class ProductInsights:
    """Insights about a product's performance"""
    product_id: str
    title: str
    views: int = 0
    orders: int = 0
    revenue: float = 0.0
    conversion_rate: float = 0.0
    avg_rating: float = 0.0
    review_count: int = 0
    stock_status: str = "in_stock"
    recommendations: List[str] = field(default_factory=list)


class ShopifyEnhancedTools(ToolBase):
    """Enhanced Shopify integration with intelligent operations."""
    
    def __init__(
        self,
        shop_url: str,
        access_token: str,
        api_version: str = "2024-10"
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
        data: Optional[Dict] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Make API request with retry logic."""
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method,
                        url,
                        headers=self.headers,
                        json=data,
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as response:
                        
                        if response.status == 429:
                            retry_after = int(response.headers.get("Retry-After", 2))
                            await asyncio.sleep(retry_after)
                            continue
                        
                        result = await response.json()
                        
                        if response.status >= 400:
                            raise Exception(f"Shopify API error: {result}")
                        
                        return result
                        
            except asyncio.TimeoutError:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
                
        raise Exception(f"Max retries exceeded for {endpoint}")
    
    async def _graphql_request(
        self,
        query: str,
        variables: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make GraphQL request."""
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
                
                if "errors" in result:
                    raise Exception(f"GraphQL errors: {result['errors']}")
                
                return result.get("data", {})

    # ==========================================
    # SMART PULL OPERATIONS
    # ==========================================
    
    @tool(
        name="shopify_pull_all_data",
        description="Pull comprehensive store data including products, collections, inventory, and recent orders",
        category="shopify"
    )
    async def pull_all_data(
        self,
        include_orders: bool = True,
        include_customers: bool = False,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Pull comprehensive store data for analysis.
        
        Args:
            include_orders: Include recent orders data
            include_customers: Include customer data
            days_back: Days of order history to include
        """
        data = {
            "pulled_at": datetime.now().isoformat(),
            "store": self.shop_url
        }
        
        # Get products
        try:
            products_result = await self._request("GET", "/products.json?limit=250")
            products = products_result.get("products", [])
            data["products"] = {
                "count": len(products),
                "by_status": {},
                "by_type": {},
                "items": []
            }
            
            for p in products:
                status = p.get("status", "unknown")
                ptype = p.get("product_type", "Other") or "Other"
                
                data["products"]["by_status"][status] = data["products"]["by_status"].get(status, 0) + 1
                data["products"]["by_type"][ptype] = data["products"]["by_type"].get(ptype, 0) + 1
                
                data["products"]["items"].append({
                    "id": p.get("id"),
                    "title": p.get("title"),
                    "status": status,
                    "product_type": ptype,
                    "vendor": p.get("vendor"),
                    "tags": p.get("tags"),
                    "variants_count": len(p.get("variants", [])),
                    "price_range": self._get_price_range(p.get("variants", [])),
                    "has_images": len(p.get("images", [])) > 0,
                    "created_at": p.get("created_at"),
                    "updated_at": p.get("updated_at")
                })
                
        except Exception as e:
            data["products"] = {"error": str(e)}
        
        # Get collections
        try:
            collections_result = await self._request("GET", "/custom_collections.json")
            smart_collections = await self._request("GET", "/smart_collections.json")
            
            all_collections = (
                collections_result.get("custom_collections", []) + 
                smart_collections.get("smart_collections", [])
            )
            
            data["collections"] = {
                "count": len(all_collections),
                "items": [
                    {
                        "id": c.get("id"),
                        "title": c.get("title"),
                        "type": "smart" if "rules" in c else "custom"
                    }
                    for c in all_collections
                ]
            }
        except Exception as e:
            data["collections"] = {"error": str(e)}
        
        # Get orders if requested
        if include_orders:
            try:
                since_date = (datetime.now() - timedelta(days=days_back)).isoformat()
                orders_result = await self._request(
                    "GET", 
                    f"/orders.json?status=any&created_at_min={since_date}&limit=250"
                )
                orders = orders_result.get("orders", [])
                
                total_revenue = sum(float(o.get("total_price", 0)) for o in orders)
                
                data["orders"] = {
                    "count": len(orders),
                    "total_revenue": round(total_revenue, 2),
                    "average_order_value": round(total_revenue / len(orders), 2) if orders else 0,
                    "by_status": {},
                    "top_products": self._get_top_products(orders)
                }
                
                for o in orders:
                    status = o.get("financial_status", "unknown")
                    data["orders"]["by_status"][status] = data["orders"]["by_status"].get(status, 0) + 1
                    
            except Exception as e:
                data["orders"] = {"error": str(e)}
        
        # Get customers if requested
        if include_customers:
            try:
                customers_result = await self._request("GET", "/customers.json?limit=250")
                customers = customers_result.get("customers", [])
                
                data["customers"] = {
                    "count": len(customers),
                    "with_orders": len([c for c in customers if c.get("orders_count", 0) > 0]),
                    "total_spent": sum(float(c.get("total_spent", 0)) for c in customers)
                }
            except Exception as e:
                data["customers"] = {"error": str(e)}
        
        # Generate summary
        data["summary"] = self._generate_store_summary(data)
        
        return data
    
    def _get_price_range(self, variants: List[Dict]) -> Dict[str, float]:
        """Get price range from variants."""
        prices = [float(v.get("price", 0)) for v in variants if v.get("price")]
        if not prices:
            return {"min": 0, "max": 0}
        return {"min": min(prices), "max": max(prices)}
    
    def _get_top_products(self, orders: List[Dict], limit: int = 10) -> List[Dict]:
        """Get top selling products from orders."""
        product_sales = {}
        
        for order in orders:
            for item in order.get("line_items", []):
                product_id = item.get("product_id")
                title = item.get("title", "Unknown")
                quantity = item.get("quantity", 0)
                
                if product_id:
                    if product_id not in product_sales:
                        product_sales[product_id] = {
                            "product_id": product_id,
                            "title": title,
                            "units_sold": 0,
                            "order_count": 0
                        }
                    product_sales[product_id]["units_sold"] += quantity
                    product_sales[product_id]["order_count"] += 1
        
        sorted_products = sorted(
            product_sales.values(), 
            key=lambda x: x["units_sold"], 
            reverse=True
        )
        
        return sorted_products[:limit]
    
    def _generate_store_summary(self, data: Dict) -> str:
        """Generate natural language summary of store data."""
        parts = []
        
        if "products" in data and "count" in data["products"]:
            parts.append(f"📦 {data['products']['count']} products")
            
            by_status = data["products"].get("by_status", {})
            if by_status:
                status_parts = [f"{count} {status}" for status, count in by_status.items()]
                parts.append(f"   Status: {', '.join(status_parts)}")
        
        if "orders" in data and "count" in data["orders"]:
            parts.append(f"🛒 {data['orders']['count']} orders (${data['orders'].get('total_revenue', 0):,.2f} revenue)")
            parts.append(f"   AOV: ${data['orders'].get('average_order_value', 0):,.2f}")
        
        if "collections" in data and "count" in data["collections"]:
            parts.append(f"📂 {data['collections']['count']} collections")
        
        if "customers" in data and "count" in data["customers"]:
            parts.append(f"👥 {data['customers']['count']} customers")
        
        return "\n".join(parts)

    @tool(
        name="shopify_get_product_details",
        description="Get detailed information about a specific product including variants, images, SEO, and inventory",
        category="shopify"
    )
    async def get_product_details(
        self,
        product_id: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive product details.
        
        Args:
            product_id: Shopify product ID
        """
        try:
            result = await self._request("GET", f"/products/{product_id}.json")
            product = result.get("product", {})
            
            # Get inventory levels for each variant
            inventory_data = []
            for variant in product.get("variants", []):
                inventory_item_id = variant.get("inventory_item_id")
                if inventory_item_id:
                    try:
                        inv_result = await self._request(
                            "GET", 
                            f"/inventory_levels.json?inventory_item_ids={inventory_item_id}"
                        )
                        inventory_data.extend(inv_result.get("inventory_levels", []))
                    except:
                        pass
            
            return {
                "product": {
                    "id": product.get("id"),
                    "title": product.get("title"),
                    "description": product.get("body_html"),
                    "status": product.get("status"),
                    "product_type": product.get("product_type"),
                    "vendor": product.get("vendor"),
                    "tags": product.get("tags"),
                    "handle": product.get("handle"),
                    "created_at": product.get("created_at"),
                    "updated_at": product.get("updated_at"),
                    "published_at": product.get("published_at"),
                    "seo": {
                        "title": product.get("seo_title") or product.get("title"),
                        "description": product.get("seo_description") or (product.get("body_html", "")[:160] if product.get("body_html") else "")
                    }
                },
                "variants": [
                    {
                        "id": v.get("id"),
                        "title": v.get("title"),
                        "price": v.get("price"),
                        "compare_at_price": v.get("compare_at_price"),
                        "sku": v.get("sku"),
                        "inventory_quantity": v.get("inventory_quantity"),
                        "weight": v.get("weight"),
                        "option1": v.get("option1"),
                        "option2": v.get("option2"),
                        "option3": v.get("option3")
                    }
                    for v in product.get("variants", [])
                ],
                "images": [
                    {
                        "id": img.get("id"),
                        "src": img.get("src"),
                        "alt": img.get("alt"),
                        "position": img.get("position")
                    }
                    for img in product.get("images", [])
                ],
                "inventory": inventory_data,
                "options": product.get("options", [])
            }
            
        except Exception as e:
            return {"error": str(e)}

    # ==========================================
    # SMART EDIT OPERATIONS
    # ==========================================
    
    @tool(
        name="shopify_smart_edit_product",
        description="Edit a product using natural language instructions. Automatically handles multiple field updates.",
        category="shopify"
    )
    async def smart_edit_product(
        self,
        product_id: str,
        instructions: str
    ) -> Dict[str, Any]:
        """
        Edit a product based on natural language instructions.
        
        Args:
            product_id: Shopify product ID
            instructions: Natural language edit instructions like:
                - "Change price to $29.99"
                - "Update title to Summer Collection Tee"
                - "Add tags: sale, featured, summer"
                - "Set compare at price to $39.99 and mark as on sale"
        """
        # Parse instructions into fields
        updates = self._parse_edit_instructions(instructions)
        
        if not updates:
            return {
                "success": False,
                "error": "Could not parse edit instructions",
                "instructions": instructions
            }
        
        # Apply updates
        try:
            # Separate variant updates from product updates
            variant_updates = {}
            product_updates = {}
            
            for key, value in updates.items():
                if key in ["price", "compare_at_price", "sku", "inventory_quantity"]:
                    variant_updates[key] = value
                else:
                    product_updates[key] = value
            
            results = []
            
            # Update product fields
            if product_updates:
                result = await self._request(
                    "PUT",
                    f"/products/{product_id}.json",
                    {"product": product_updates}
                )
                results.append({"product_update": "success", "fields": list(product_updates.keys())})
            
            # Update variant fields (apply to all variants)
            if variant_updates:
                # Get current product to find variants
                product_result = await self._request("GET", f"/products/{product_id}.json")
                variants = product_result.get("product", {}).get("variants", [])
                
                for variant in variants:
                    variant_id = variant.get("id")
                    await self._request(
                        "PUT",
                        f"/variants/{variant_id}.json",
                        {"variant": variant_updates}
                    )
                
                results.append({
                    "variant_update": "success", 
                    "variants_updated": len(variants),
                    "fields": list(variant_updates.keys())
                })
            
            return {
                "success": True,
                "product_id": product_id,
                "applied_updates": updates,
                "results": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "product_id": product_id
            }
    
    def _parse_edit_instructions(self, instructions: str) -> Dict[str, Any]:
        """Parse natural language instructions into field updates."""
        updates = {}
        instructions_lower = instructions.lower()
        
        import re
        
        # Price patterns
        price_match = re.search(r'(?:price|cost)\s*(?:to|=|:)?\s*\$?(\d+(?:\.\d{2})?)', instructions_lower)
        if price_match:
            updates["price"] = price_match.group(1)
        
        # Compare at price
        compare_match = re.search(r'compare\s*(?:at)?\s*price\s*(?:to|=|:)?\s*\$?(\d+(?:\.\d{2})?)', instructions_lower)
        if compare_match:
            updates["compare_at_price"] = compare_match.group(1)
        
        # Title
        title_match = re.search(r'title\s*(?:to|=|:)?\s*["\']?([^"\']+)["\']?', instructions, re.IGNORECASE)
        if title_match:
            updates["title"] = title_match.group(1).strip()
        
        # Tags
        tags_match = re.search(r'(?:add\s*)?tags?\s*(?:to|=|:)?\s*["\']?([^"\']+)["\']?', instructions, re.IGNORECASE)
        if tags_match:
            updates["tags"] = tags_match.group(1).strip()
        
        # Status
        if any(word in instructions_lower for word in ["activate", "publish", "make active", "set active"]):
            updates["status"] = "active"
        elif any(word in instructions_lower for word in ["draft", "unpublish", "deactivate", "hide"]):
            updates["status"] = "draft"
        
        # Product type
        type_match = re.search(r'(?:product\s*)?type\s*(?:to|=|:)?\s*["\']?([^"\']+)["\']?', instructions, re.IGNORECASE)
        if type_match:
            updates["product_type"] = type_match.group(1).strip()
        
        # Vendor
        vendor_match = re.search(r'vendor\s*(?:to|=|:)?\s*["\']?([^"\']+)["\']?', instructions, re.IGNORECASE)
        if vendor_match:
            updates["vendor"] = vendor_match.group(1).strip()
        
        return updates

    @tool(
        name="shopify_bulk_edit_by_filter",
        description="Bulk edit multiple products matching a filter criteria",
        category="shopify"
    )
    async def bulk_edit_by_filter(
        self,
        filter_type: str = None,
        filter_value: str = None,
        filter_tags: str = None,
        updates: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Bulk edit products matching a filter.
        
        Args:
            filter_type: Product type to filter by
            filter_value: Value to filter by  
            filter_tags: Tags to filter by (comma-separated)
            updates: Fields to update on matching products
        """
        if not updates:
            return {"error": "No updates specified"}
        
        # Build query
        query_parts = []
        if filter_type:
            query_parts.append(f"product_type={filter_type}")
        if filter_tags:
            query_parts.append(f"tags={filter_tags}")
        
        query = "&".join(query_parts) if query_parts else ""
        endpoint = f"/products.json?limit=250{('&' + query) if query else ''}"
        
        try:
            result = await self._request("GET", endpoint)
            products = result.get("products", [])
            
            # Apply filter_value if specified
            if filter_value:
                products = [
                    p for p in products 
                    if filter_value.lower() in (p.get("title", "") + p.get("product_type", "")).lower()
                ]
            
            if not products:
                return {
                    "success": False,
                    "error": "No products matched the filter",
                    "filter": {"type": filter_type, "value": filter_value, "tags": filter_tags}
                }
            
            # Update each product
            updated = []
            errors = []
            
            for product in products:
                try:
                    await self._request(
                        "PUT",
                        f"/products/{product['id']}.json",
                        {"product": updates}
                    )
                    updated.append({
                        "id": product["id"],
                        "title": product.get("title")
                    })
                except Exception as e:
                    errors.append({
                        "id": product["id"],
                        "title": product.get("title"),
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "total_matched": len(products),
                "updated_count": len(updated),
                "error_count": len(errors),
                "updated": updated[:20],  # Limit response size
                "errors": errors[:10]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================
    # PUBLISH OPERATIONS
    # ==========================================
    
    @tool(
        name="shopify_publish_product",
        description="Publish a product to make it visible on the store",
        category="shopify"
    )
    async def publish_product(
        self,
        product_id: str,
        channels: List[str] = None
    ) -> Dict[str, Any]:
        """
        Publish a product to the online store.
        
        Args:
            product_id: Shopify product ID
            channels: List of channels to publish to (default: online_store)
        """
        try:
            # Update product status to active
            result = await self._request(
                "PUT",
                f"/products/{product_id}.json",
                {
                    "product": {
                        "id": product_id,
                        "status": "active",
                        "published": True,
                        "published_at": datetime.now().isoformat()
                    }
                }
            )
            
            product = result.get("product", {})
            
            return {
                "success": True,
                "product_id": product_id,
                "title": product.get("title"),
                "status": "active",
                "published_at": product.get("published_at"),
                "handle": product.get("handle"),
                "url": f"https://{self.shop_url}/products/{product.get('handle')}"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="shopify_unpublish_product",
        description="Unpublish a product (set to draft) to hide it from the store",
        category="shopify"
    )
    async def unpublish_product(
        self,
        product_id: str
    ) -> Dict[str, Any]:
        """
        Unpublish a product (set to draft).
        
        Args:
            product_id: Shopify product ID
        """
        try:
            result = await self._request(
                "PUT",
                f"/products/{product_id}.json",
                {
                    "product": {
                        "id": product_id,
                        "status": "draft"
                    }
                }
            )
            
            return {
                "success": True,
                "product_id": product_id,
                "title": result.get("product", {}).get("title"),
                "status": "draft"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="shopify_bulk_publish",
        description="Publish multiple products at once by product type, tags, or list of IDs",
        category="shopify"
    )
    async def bulk_publish(
        self,
        product_ids: List[str] = None,
        product_type: str = None,
        tags: str = None
    ) -> Dict[str, Any]:
        """
        Bulk publish products.
        
        Args:
            product_ids: List of product IDs to publish
            product_type: Publish all products of this type
            tags: Publish all products with these tags
        """
        products_to_publish = []
        
        if product_ids:
            products_to_publish = product_ids
        else:
            # Fetch by filter
            query_parts = ["status=draft"]
            if product_type:
                query_parts.append(f"product_type={product_type}")
            
            endpoint = f"/products.json?{('&'.join(query_parts))}&limit=250"
            result = await self._request("GET", endpoint)
            
            products = result.get("products", [])
            
            if tags:
                tag_list = [t.strip().lower() for t in tags.split(",")]
                products = [
                    p for p in products 
                    if any(tag in (p.get("tags", "") or "").lower() for tag in tag_list)
                ]
            
            products_to_publish = [p["id"] for p in products]
        
        if not products_to_publish:
            return {
                "success": False,
                "error": "No products to publish"
            }
        
        published = []
        errors = []
        
        for product_id in products_to_publish:
            try:
                result = await self.publish_product(str(product_id))
                if result.get("success"):
                    published.append({
                        "id": product_id,
                        "title": result.get("title"),
                        "url": result.get("url")
                    })
                else:
                    errors.append({"id": product_id, "error": result.get("error")})
            except Exception as e:
                errors.append({"id": product_id, "error": str(e)})
        
        return {
            "success": True,
            "published_count": len(published),
            "error_count": len(errors),
            "published": published[:20],
            "errors": errors[:10]
        }

    # ==========================================
    # SEO OPTIMIZATION
    # ==========================================
    
    @tool(
        name="shopify_optimize_seo",
        description="Optimize product SEO with auto-generated title, description, and metadata",
        category="shopify"
    )
    async def optimize_seo(
        self,
        product_id: str,
        seo_title: str = None,
        seo_description: str = None,
        auto_generate: bool = False
    ) -> Dict[str, Any]:
        """
        Optimize product SEO.
        
        Args:
            product_id: Shopify product ID
            seo_title: Custom SEO title
            seo_description: Custom SEO description
            auto_generate: Auto-generate from product data
        """
        try:
            # Get current product
            result = await self._request("GET", f"/products/{product_id}.json")
            product = result.get("product", {})
            
            updates = {}
            
            if auto_generate:
                title = product.get("title", "")
                description = product.get("body_html", "")
                product_type = product.get("product_type", "")
                
                # Generate SEO title (max 60 chars)
                if not seo_title:
                    seo_title = f"{title} | {product_type}" if product_type else title
                    if len(seo_title) > 60:
                        seo_title = seo_title[:57] + "..."
                
                # Generate SEO description (max 160 chars)
                if not seo_description:
                    import re
                    clean_desc = re.sub(r'<[^>]+>', '', description or "")
                    seo_description = clean_desc[:157] + "..." if len(clean_desc) > 160 else clean_desc
            
            if seo_title:
                updates["metafields_global_title_tag"] = seo_title
            if seo_description:
                updates["metafields_global_description_tag"] = seo_description
            
            # Add schema markup suggestion
            schema_suggestion = {
                "@type": "Product",
                "name": product.get("title"),
                "description": seo_description,
                "brand": product.get("vendor"),
                "offers": {
                    "@type": "Offer",
                    "price": product.get("variants", [{}])[0].get("price", "0"),
                    "priceCurrency": "USD"
                }
            }
            
            if updates:
                await self._request(
                    "PUT",
                    f"/products/{product_id}.json",
                    {"product": updates}
                )
            
            return {
                "success": True,
                "product_id": product_id,
                "title": product.get("title"),
                "seo_updates": {
                    "title": seo_title,
                    "description": seo_description
                },
                "schema_suggestion": schema_suggestion,
                "recommendations": [
                    "Add high-quality images with alt text",
                    "Include target keywords in product description",
                    "Use structured data for rich snippets",
                    "Optimize URL handle",
                    "Add internal links from related products"
                ]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================
    # STORE HEALTH CHECK
    # ==========================================
    
    @tool(
        name="shopify_store_health_check",
        description="Check store health including product issues, SEO problems, and inventory warnings",
        category="shopify"
    )
    async def store_health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive store health check.
        """
        issues = []
        warnings = []
        stats = {}
        
        try:
            # Get products
            result = await self._request("GET", "/products.json?limit=250")
            products = result.get("products", [])
            
            stats["total_products"] = len(products)
            
            products_without_images = []
            products_without_description = []
            products_low_stock = []
            products_no_price = []
            products_draft = []
            
            for p in products:
                # Check for images
                if not p.get("images"):
                    products_without_images.append(p.get("title"))
                
                # Check for description
                if not p.get("body_html") or len(p.get("body_html", "")) < 50:
                    products_without_description.append(p.get("title"))
                
                # Check inventory
                for variant in p.get("variants", []):
                    if variant.get("inventory_quantity", 0) <= 5:
                        products_low_stock.append({
                            "title": p.get("title"),
                            "variant": variant.get("title"),
                            "quantity": variant.get("inventory_quantity")
                        })
                    
                    if not variant.get("price") or float(variant.get("price", 0)) == 0:
                        products_no_price.append(p.get("title"))
                
                # Check status
                if p.get("status") == "draft":
                    products_draft.append(p.get("title"))
            
            # Generate issues
            if products_without_images:
                issues.append({
                    "type": "missing_images",
                    "severity": "high",
                    "count": len(products_without_images),
                    "products": products_without_images[:10]
                })
            
            if products_without_description:
                warnings.append({
                    "type": "missing_description",
                    "severity": "medium",
                    "count": len(products_without_description),
                    "products": products_without_description[:10]
                })
            
            if products_low_stock:
                warnings.append({
                    "type": "low_stock",
                    "severity": "medium",
                    "count": len(products_low_stock),
                    "products": products_low_stock[:10]
                })
            
            if products_no_price:
                issues.append({
                    "type": "missing_price",
                    "severity": "critical",
                    "count": len(products_no_price),
                    "products": products_no_price[:10]
                })
            
            stats["draft_products"] = len(products_draft)
            stats["published_products"] = len(products) - len(products_draft)
            stats["products_with_images"] = len(products) - len(products_without_images)
            
            # Calculate health score
            health_score = 100
            health_score -= len(issues) * 10
            health_score -= len(warnings) * 5
            health_score = max(0, health_score)
            
            return {
                "success": True,
                "health_score": health_score,
                "status": "healthy" if health_score >= 80 else "needs_attention" if health_score >= 50 else "critical",
                "stats": stats,
                "issues": issues,
                "warnings": warnings,
                "recommendations": [
                    "Add images to all products",
                    "Write detailed descriptions (100+ words)",
                    "Restock low inventory items",
                    "Publish draft products when ready",
                    "Optimize product titles for SEO"
                ][:3] if health_score < 100 else []
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# Factory function
def create_shopify_enhanced_tools(
    shop_url: str = None,
    access_token: str = None
) -> ShopifyEnhancedTools:
    """Create ShopifyEnhancedTools instance."""
    import os
    
    shop_url = shop_url or os.getenv("SHOPIFY_STORE_URL")
    access_token = access_token or os.getenv("SHOPIFY_ACCESS_TOKEN")
    
    if not shop_url or not access_token:
        raise ValueError("SHOPIFY_STORE_URL and SHOPIFY_ACCESS_TOKEN required")
    
    return ShopifyEnhancedTools(shop_url, access_token)


__all__ = ["ShopifyEnhancedTools", "create_shopify_enhanced_tools"]
