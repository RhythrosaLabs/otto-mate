"""
Advanced Shopify Integration Tools
==================================

Enhanced Shopify integration with:
- Bulk operations (mass product updates, imports)
- Metafields management
- Discount codes and promotions
- Webhook management
- Inventory sync
- Customer management
- Theme customization
- Abandoned cart recovery
"""

import logging
import aiohttp
import json
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from .core import tool, ToolBase

logger = logging.getLogger(__name__)


class ShopifyAdvancedTools(ToolBase):
    """Advanced Shopify integration with bulk operations and automation."""
    
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
                        
                        # Handle rate limiting
                        if response.status == 429:
                            retry_after = int(response.headers.get("Retry-After", 2))
                            logger.warning(f"Rate limited. Waiting {retry_after}s...")
                            await asyncio.sleep(retry_after)
                            continue
                        
                        result = await response.json()
                        
                        if response.status >= 400:
                            logger.error(f"Shopify API error: {result}")
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
                    raise Exception(f"Shopify GraphQL error: {result}")
                
                if "errors" in result:
                    raise Exception(f"GraphQL errors: {result['errors']}")
                
                return result.get("data", {})

    # ==========================================
    # BULK OPERATIONS
    # ==========================================
    
    @tool(
        name="shopify_bulk_update_products",
        description="Bulk update multiple products at once (price, inventory, status, tags)",
        category="shopify"
    )
    async def bulk_update_products(
        self,
        updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Bulk update multiple products.
        
        Args:
            updates: List of dicts with product_id and fields to update:
                [{"product_id": "123", "price": "29.99", "status": "active"}, ...]
        
        Supported fields: price, compare_at_price, status, tags, title, vendor
        """
        results = []
        errors = []
        
        for update in updates:
            product_id = update.pop("product_id", None)
            if not product_id:
                errors.append({"error": "Missing product_id", "update": update})
                continue
            
            try:
                # Handle price updates specially (affects variants)
                if "price" in update:
                    price = update.pop("price")
                    product = await self._request("GET", f"/products/{product_id}.json")
                    variants = product.get("product", {}).get("variants", [])
                    
                    for variant in variants:
                        await self._request(
                            "PUT",
                            f"/variants/{variant['id']}.json",
                            {"variant": {"price": str(price)}}
                        )
                
                # Update other product fields
                if update:
                    await self._request(
                        "PUT",
                        f"/products/{product_id}.json",
                        {"product": update}
                    )
                
                results.append({"product_id": product_id, "success": True})
                
            except Exception as e:
                errors.append({"product_id": product_id, "error": str(e)})
        
        return {
            "success": len(errors) == 0,
            "updated": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }
    
    @tool(
        name="shopify_bulk_import_products",
        description="Import multiple products at once from a list",
        category="shopify"
    )
    async def bulk_import_products(
        self,
        products: List[Dict[str, Any]],
        status: str = "draft"
    ) -> Dict[str, Any]:
        """
        Bulk import multiple products.
        
        Args:
            products: List of product data dicts with title, description, price, images, etc.
            status: Status for imported products (draft/active)
        """
        results = []
        errors = []
        
        for product_data in products:
            try:
                product = {
                    "title": product_data.get("title"),
                    "body_html": product_data.get("description", product_data.get("body_html", "")),
                    "vendor": product_data.get("vendor", ""),
                    "product_type": product_data.get("product_type", ""),
                    "tags": product_data.get("tags", ""),
                    "status": status,
                    "variants": [{"price": str(product_data.get("price", "0.00"))}]
                }
                
                if product_data.get("images"):
                    product["images"] = [{"src": url} for url in product_data["images"]]
                
                result = await self._request("POST", "/products.json", {"product": product})
                
                results.append({
                    "title": product_data.get("title"),
                    "product_id": result.get("product", {}).get("id"),
                    "success": True
                })
                
            except Exception as e:
                errors.append({
                    "title": product_data.get("title"),
                    "error": str(e)
                })
        
        return {
            "success": len(errors) == 0,
            "imported": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }

    # ==========================================
    # METAFIELDS
    # ==========================================
    
    @tool(
        name="shopify_set_metafield",
        description="Set a metafield on a product, collection, or store",
        category="shopify"
    )
    async def set_metafield(
        self,
        resource_type: str,
        resource_id: str,
        namespace: str,
        key: str,
        value: str,
        value_type: str = "single_line_text_field"
    ) -> Dict[str, Any]:
        """
        Set a metafield on a resource.
        
        Args:
            resource_type: Type (product, variant, collection, customer, order, shop)
            resource_id: ID of the resource (use "shop" for shop-level)
            namespace: Metafield namespace
            key: Metafield key
            value: Value to set
            value_type: Type (single_line_text_field, multi_line_text_field, number_integer, 
                       number_decimal, boolean, json, date, datetime, url)
        """
        metafield_data = {
            "metafield": {
                "namespace": namespace,
                "key": key,
                "value": value,
                "type": value_type
            }
        }
        
        if resource_id == "shop" or resource_type == "shop":
            endpoint = "/metafields.json"
        else:
            endpoint = f"/{resource_type}s/{resource_id}/metafields.json"
        
        result = await self._request("POST", endpoint, metafield_data)
        
        return {
            "success": True,
            "metafield_id": result.get("metafield", {}).get("id"),
            "namespace": namespace,
            "key": key,
            "value": value
        }
    
    @tool(
        name="shopify_get_metafields",
        description="Get all metafields for a resource",
        category="shopify"
    )
    async def get_metafields(
        self,
        resource_type: str,
        resource_id: str
    ) -> Dict[str, Any]:
        """Get metafields for a resource."""
        if resource_id == "shop" or resource_type == "shop":
            endpoint = "/metafields.json"
        else:
            endpoint = f"/{resource_type}s/{resource_id}/metafields.json"
        
        result = await self._request("GET", endpoint)
        
        return {
            "metafields": result.get("metafields", []),
            "count": len(result.get("metafields", []))
        }

    # ==========================================
    # DISCOUNTS AND PROMOTIONS
    # ==========================================
    
    @tool(
        name="shopify_create_discount_code",
        description="Create a discount code for your store",
        category="shopify"
    )
    async def create_discount_code(
        self,
        code: str,
        discount_type: str = "percentage",
        value: float = 10,
        starts_at: str = None,
        ends_at: str = None,
        usage_limit: int = None,
        minimum_order_amount: float = None,
        applies_to: str = "all",  # all, specific_products, specific_collections
        product_ids: List[str] = None,
        collection_ids: List[str] = None,
        once_per_customer: bool = False
    ) -> Dict[str, Any]:
        """
        Create a discount code.
        
        Args:
            code: The discount code (e.g., "SAVE20")
            discount_type: Type (percentage, fixed_amount, free_shipping)
            value: Discount value (e.g., 10 for 10% or $10)
            starts_at: ISO8601 start date
            ends_at: ISO8601 end date
            usage_limit: Total usage limit
            minimum_order_amount: Minimum order value
            applies_to: What discount applies to
            product_ids: Specific product IDs if applies_to is specific_products
            collection_ids: Specific collection IDs if applies_to is specific_collections
            once_per_customer: Limit to one use per customer
        """
        # First create a price rule
        price_rule = {
            "title": code,
            "target_type": "line_item",
            "target_selection": "all" if applies_to == "all" else "entitled",
            "allocation_method": "across",
            "customer_selection": "all",
            "starts_at": starts_at or datetime.utcnow().isoformat() + "Z",
            "once_per_customer": once_per_customer
        }
        
        if discount_type == "percentage":
            price_rule["value_type"] = "percentage"
            price_rule["value"] = str(-value)  # Negative for discount
        elif discount_type == "fixed_amount":
            price_rule["value_type"] = "fixed_amount"
            price_rule["value"] = str(-value)
        elif discount_type == "free_shipping":
            price_rule["target_type"] = "shipping_line"
            price_rule["value_type"] = "percentage"
            price_rule["value"] = "-100.0"
        
        if ends_at:
            price_rule["ends_at"] = ends_at
        
        if usage_limit:
            price_rule["usage_limit"] = usage_limit
        
        if minimum_order_amount:
            price_rule["prerequisite_subtotal_range"] = {
                "greater_than_or_equal_to": str(minimum_order_amount)
            }
        
        if product_ids and applies_to == "specific_products":
            price_rule["entitled_product_ids"] = [int(pid) for pid in product_ids]
        
        if collection_ids and applies_to == "specific_collections":
            price_rule["entitled_collection_ids"] = [int(cid) for cid in collection_ids]
        
        # Create the price rule
        rule_result = await self._request(
            "POST",
            "/price_rules.json",
            {"price_rule": price_rule}
        )
        
        price_rule_id = rule_result.get("price_rule", {}).get("id")
        
        if not price_rule_id:
            return {"success": False, "error": "Failed to create price rule"}
        
        # Create the discount code
        code_result = await self._request(
            "POST",
            f"/price_rules/{price_rule_id}/discount_codes.json",
            {"discount_code": {"code": code}}
        )
        
        discount_code = code_result.get("discount_code", {})
        
        return {
            "success": True,
            "code": code,
            "discount_code_id": discount_code.get("id"),
            "price_rule_id": price_rule_id,
            "type": discount_type,
            "value": value,
            "starts_at": starts_at,
            "ends_at": ends_at,
            "usage_limit": usage_limit,
            "minimum_order": minimum_order_amount
        }
    
    @tool(
        name="shopify_list_discount_codes",
        description="List all discount codes",
        category="shopify"
    )
    async def list_discount_codes(self) -> Dict[str, Any]:
        """List all discount codes."""
        # Get price rules first
        rules = await self._request("GET", "/price_rules.json")
        
        all_codes = []
        for rule in rules.get("price_rules", []):
            codes = await self._request(
                "GET",
                f"/price_rules/{rule['id']}/discount_codes.json"
            )
            for code in codes.get("discount_codes", []):
                all_codes.append({
                    "code": code.get("code"),
                    "id": code.get("id"),
                    "price_rule_id": rule.get("id"),
                    "title": rule.get("title"),
                    "value": rule.get("value"),
                    "value_type": rule.get("value_type"),
                    "usage_count": code.get("usage_count", 0),
                    "starts_at": rule.get("starts_at"),
                    "ends_at": rule.get("ends_at")
                })
        
        return {
            "discount_codes": all_codes,
            "count": len(all_codes)
        }

    # ==========================================
    # WEBHOOKS
    # ==========================================
    
    @tool(
        name="shopify_create_webhook",
        description="Create a webhook to receive notifications for store events",
        category="shopify"
    )
    async def create_webhook(
        self,
        topic: str,
        address: str,
        format: str = "json"
    ) -> Dict[str, Any]:
        """
        Create a webhook subscription.
        
        Args:
            topic: Event topic (orders/create, orders/paid, products/create, 
                   products/update, customers/create, carts/create, checkouts/create,
                   inventory_levels/update, fulfillments/create, refunds/create)
            address: HTTPS URL to receive webhook
            format: Data format (json or xml)
        """
        webhook_data = {
            "webhook": {
                "topic": topic,
                "address": address,
                "format": format
            }
        }
        
        result = await self._request("POST", "/webhooks.json", webhook_data)
        webhook = result.get("webhook", {})
        
        return {
            "success": True,
            "webhook_id": webhook.get("id"),
            "topic": topic,
            "address": address,
            "created_at": webhook.get("created_at")
        }
    
    @tool(
        name="shopify_list_webhooks",
        description="List all registered webhooks",
        category="shopify"
    )
    async def list_webhooks(self) -> Dict[str, Any]:
        """List all webhooks."""
        result = await self._request("GET", "/webhooks.json")
        
        return {
            "webhooks": result.get("webhooks", []),
            "count": len(result.get("webhooks", []))
        }
    
    @tool(
        name="shopify_delete_webhook",
        description="Delete a webhook",
        category="shopify"
    )
    async def delete_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Delete a webhook."""
        await self._request("DELETE", f"/webhooks/{webhook_id}.json")
        return {"success": True, "deleted_webhook_id": webhook_id}

    # ==========================================
    # CUSTOMERS
    # ==========================================
    
    @tool(
        name="shopify_list_customers",
        description="List customers with optional filters",
        category="shopify"
    )
    async def list_customers(
        self,
        limit: int = 50,
        created_at_min: str = None,
        email: str = None,
        tags: str = None
    ) -> Dict[str, Any]:
        """
        List customers with filters.
        
        Args:
            limit: Max customers to return
            created_at_min: ISO8601 date - only customers created after
            email: Filter by email
            tags: Filter by tags
        """
        params = [f"limit={limit}"]
        if created_at_min:
            params.append(f"created_at_min={created_at_min}")
        if email:
            params.append(f"email={email}")
        if tags:
            params.append(f"tags={tags}")
        
        endpoint = f"/customers.json?{'&'.join(params)}"
        result = await self._request("GET", endpoint)
        
        customers = result.get("customers", [])
        
        return {
            "customers": customers,
            "count": len(customers),
            "summary": [
                {
                    "id": c.get("id"),
                    "email": c.get("email"),
                    "name": f"{c.get('first_name', '')} {c.get('last_name', '')}".strip(),
                    "orders_count": c.get("orders_count"),
                    "total_spent": c.get("total_spent"),
                    "created_at": c.get("created_at")
                }
                for c in customers
            ]
        }
    
    @tool(
        name="shopify_get_customer_details",
        description="Get detailed customer information including order history",
        category="shopify"
    )
    async def get_customer_details(
        self,
        customer_id: str
    ) -> Dict[str, Any]:
        """Get detailed customer info."""
        customer = await self._request("GET", f"/customers/{customer_id}.json")
        orders = await self._request("GET", f"/customers/{customer_id}/orders.json")
        
        cust = customer.get("customer", {})
        
        return {
            "customer": {
                "id": cust.get("id"),
                "email": cust.get("email"),
                "first_name": cust.get("first_name"),
                "last_name": cust.get("last_name"),
                "phone": cust.get("phone"),
                "orders_count": cust.get("orders_count"),
                "total_spent": cust.get("total_spent"),
                "tags": cust.get("tags"),
                "note": cust.get("note"),
                "verified_email": cust.get("verified_email"),
                "tax_exempt": cust.get("tax_exempt"),
                "created_at": cust.get("created_at"),
                "default_address": cust.get("default_address")
            },
            "orders": orders.get("orders", []),
            "orders_count": len(orders.get("orders", []))
        }
    
    @tool(
        name="shopify_tag_customer",
        description="Add tags to a customer for segmentation",
        category="shopify"
    )
    async def tag_customer(
        self,
        customer_id: str,
        tags: List[str]
    ) -> Dict[str, Any]:
        """Add tags to a customer."""
        # Get current tags
        customer = await self._request("GET", f"/customers/{customer_id}.json")
        current_tags = customer.get("customer", {}).get("tags", "")
        
        # Merge tags
        all_tags = set(current_tags.split(", ")) if current_tags else set()
        all_tags.update(tags)
        
        # Update
        result = await self._request(
            "PUT",
            f"/customers/{customer_id}.json",
            {"customer": {"tags": ", ".join(all_tags)}}
        )
        
        return {
            "success": True,
            "customer_id": customer_id,
            "tags": list(all_tags)
        }

    # ==========================================
    # ABANDONED CART RECOVERY
    # ==========================================
    
    @tool(
        name="shopify_get_abandoned_checkouts",
        description="Get abandoned checkouts for cart recovery",
        category="shopify"
    )
    async def get_abandoned_checkouts(
        self,
        limit: int = 50,
        created_at_min: str = None
    ) -> Dict[str, Any]:
        """
        Get abandoned checkouts.
        
        Args:
            limit: Max checkouts to return
            created_at_min: ISO8601 date - only checkouts after this date
        """
        params = [f"limit={limit}"]
        if created_at_min:
            params.append(f"created_at_min={created_at_min}")
        
        endpoint = f"/checkouts.json?{'&'.join(params)}"
        result = await self._request("GET", endpoint)
        
        checkouts = result.get("checkouts", [])
        
        # Process for useful info
        abandoned = []
        for checkout in checkouts:
            if not checkout.get("completed_at"):  # Not completed = abandoned
                abandoned.append({
                    "checkout_id": checkout.get("id"),
                    "email": checkout.get("email"),
                    "cart_value": checkout.get("total_price"),
                    "currency": checkout.get("currency"),
                    "created_at": checkout.get("created_at"),
                    "abandoned_url": checkout.get("abandoned_checkout_url"),
                    "line_items": [
                        {
                            "title": item.get("title"),
                            "quantity": item.get("quantity"),
                            "price": item.get("price")
                        }
                        for item in checkout.get("line_items", [])
                    ]
                })
        
        return {
            "abandoned_checkouts": abandoned,
            "count": len(abandoned),
            "total_potential_revenue": sum(
                float(c.get("cart_value", 0)) for c in abandoned
            )
        }

    # ==========================================
    # INVENTORY MANAGEMENT
    # ==========================================
    
    @tool(
        name="shopify_get_inventory_levels",
        description="Get inventory levels for products across locations",
        category="shopify"
    )
    async def get_inventory_levels(
        self,
        location_id: str = None,
        limit: int = 250
    ) -> Dict[str, Any]:
        """
        Get inventory levels.
        
        Args:
            location_id: Specific location ID (optional)
            limit: Max items to return
        """
        # Get locations first if not specified
        if not location_id:
            locations = await self._request("GET", "/locations.json")
            loc_list = locations.get("locations", [])
            if loc_list:
                location_id = loc_list[0].get("id")
        
        if not location_id:
            return {"error": "No locations found"}
        
        result = await self._request(
            "GET",
            f"/inventory_levels.json?location_ids={location_id}&limit={limit}"
        )
        
        levels = result.get("inventory_levels", [])
        
        # Enrich with product info
        low_stock = []
        out_of_stock = []
        
        for level in levels:
            available = level.get("available", 0)
            if available <= 0:
                out_of_stock.append(level)
            elif available < 10:
                low_stock.append(level)
        
        return {
            "inventory_levels": levels,
            "total_items": len(levels),
            "low_stock_count": len(low_stock),
            "out_of_stock_count": len(out_of_stock),
            "low_stock_items": low_stock,
            "out_of_stock_items": out_of_stock
        }
    
    @tool(
        name="shopify_adjust_inventory",
        description="Adjust inventory for a product variant",
        category="shopify"
    )
    async def adjust_inventory(
        self,
        inventory_item_id: str,
        location_id: str,
        adjustment: int
    ) -> Dict[str, Any]:
        """
        Adjust inventory by a delta amount.
        
        Args:
            inventory_item_id: The inventory item ID
            location_id: Location ID
            adjustment: Amount to add (positive) or subtract (negative)
        """
        result = await self._request(
            "POST",
            "/inventory_levels/adjust.json",
            {
                "location_id": int(location_id),
                "inventory_item_id": int(inventory_item_id),
                "available_adjustment": adjustment
            }
        )
        
        level = result.get("inventory_level", {})
        
        return {
            "success": True,
            "inventory_item_id": inventory_item_id,
            "location_id": location_id,
            "adjustment": adjustment,
            "new_available": level.get("available")
        }

    # ==========================================
    # FULFILLMENT
    # ==========================================
    
    @tool(
        name="shopify_create_fulfillment",
        description="Create a fulfillment for an order",
        category="shopify"
    )
    async def create_fulfillment(
        self,
        order_id: str,
        tracking_number: str = None,
        tracking_company: str = None,
        tracking_url: str = None,
        notify_customer: bool = True,
        line_items: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create fulfillment for an order.
        
        Args:
            order_id: Order ID to fulfill
            tracking_number: Shipping tracking number
            tracking_company: Carrier name (USPS, UPS, FedEx, etc.)
            tracking_url: Tracking URL
            notify_customer: Send notification email
            line_items: Specific items to fulfill [{"id": item_id, "quantity": 1}]
        """
        # Get fulfillment orders for this order
        fulfillment_orders = await self._request(
            "GET",
            f"/orders/{order_id}/fulfillment_orders.json"
        )
        
        fo_list = fulfillment_orders.get("fulfillment_orders", [])
        if not fo_list:
            return {"success": False, "error": "No fulfillment orders found"}
        
        # Build fulfillment data
        fulfillment_data = {
            "fulfillment": {
                "notify_customer": notify_customer,
                "line_items_by_fulfillment_order": [
                    {
                        "fulfillment_order_id": fo_list[0].get("id")
                    }
                ]
            }
        }
        
        if tracking_number:
            fulfillment_data["fulfillment"]["tracking_info"] = {
                "number": tracking_number
            }
            if tracking_company:
                fulfillment_data["fulfillment"]["tracking_info"]["company"] = tracking_company
            if tracking_url:
                fulfillment_data["fulfillment"]["tracking_info"]["url"] = tracking_url
        
        result = await self._request(
            "POST",
            "/fulfillments.json",
            fulfillment_data
        )
        
        fulfillment = result.get("fulfillment", {})
        
        return {
            "success": True,
            "fulfillment_id": fulfillment.get("id"),
            "order_id": order_id,
            "status": fulfillment.get("status"),
            "tracking_number": tracking_number,
            "tracking_company": tracking_company
        }

    # ==========================================
    # STORE SETTINGS & THEMES
    # ==========================================
    
    @tool(
        name="shopify_get_shop_info",
        description="Get detailed shop information and settings",
        category="shopify"
    )
    async def get_shop_info(self) -> Dict[str, Any]:
        """Get shop information."""
        result = await self._request("GET", "/shop.json")
        shop = result.get("shop", {})
        
        return {
            "name": shop.get("name"),
            "email": shop.get("email"),
            "domain": shop.get("domain"),
            "myshopify_domain": shop.get("myshopify_domain"),
            "plan_name": shop.get("plan_name"),
            "currency": shop.get("currency"),
            "timezone": shop.get("timezone"),
            "country": shop.get("country_name"),
            "address": {
                "address1": shop.get("address1"),
                "city": shop.get("city"),
                "province": shop.get("province"),
                "zip": shop.get("zip"),
                "country": shop.get("country")
            },
            "phone": shop.get("phone"),
            "created_at": shop.get("created_at"),
            "weight_unit": shop.get("weight_unit"),
            "money_format": shop.get("money_format"),
            "enabled_presentment_currencies": shop.get("enabled_presentment_currencies", [])
        }
    
    @tool(
        name="shopify_get_themes",
        description="List all themes on the store",
        category="shopify"
    )
    async def get_themes(self) -> Dict[str, Any]:
        """Get all themes."""
        result = await self._request("GET", "/themes.json")
        themes = result.get("themes", [])
        
        active_theme = None
        for theme in themes:
            if theme.get("role") == "main":
                active_theme = theme
                break
        
        return {
            "themes": themes,
            "count": len(themes),
            "active_theme": {
                "id": active_theme.get("id") if active_theme else None,
                "name": active_theme.get("name") if active_theme else None
            }
        }


# Factory function
def create_shopify_advanced_tools(
    shop_url: str = None,
    access_token: str = None
) -> ShopifyAdvancedTools:
    """Create ShopifyAdvancedTools instance."""
    import os
    
    shop_url = shop_url or os.getenv("SHOPIFY_SHOP_URL")
    access_token = access_token or os.getenv("SHOPIFY_ACCESS_TOKEN")
    
    if not shop_url or not access_token:
        raise ValueError("SHOPIFY_SHOP_URL and SHOPIFY_ACCESS_TOKEN required")
    
    return ShopifyAdvancedTools(shop_url, access_token)
