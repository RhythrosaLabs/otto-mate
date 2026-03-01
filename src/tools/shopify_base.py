"""
Shopify Base Client
===================

Shared HTTP client and utilities for Shopify API interactions.
Consolidates common code from shopify.py, shopify_enhanced.py, shopify_advanced.py.
"""

import logging
import aiohttp
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ShopifyBaseClient:
    """
    Base client for Shopify REST and GraphQL APIs.
    
    Provides common connection handling, authentication, and request methods.
    Extend this class for specific Shopify tool implementations.
    """
    
    def __init__(
        self,
        shop_url: str,
        access_token: str,
        api_version: str = "2024-10"  # Current stable API version
    ):
        """
        Initialize Shopify client.
        
        Args:
            shop_url: Your Shopify store URL (e.g., 'mystore.myshopify.com')
            access_token: Shopify Admin API access token
            api_version: API version to use (default: 2024-10)
        """
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
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make API request to Shopify REST API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path (e.g., '/products.json')
            data: Request body data (for POST/PUT)
            params: Query parameters
            
        Returns:
            API response as dictionary
            
        Raises:
            Exception: On API error
        """
        url = f"{self.base_url}{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                url,
                headers=self.headers,
                json=data,
                params=params
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
        """
        Make GraphQL request to Shopify.
        
        Args:
            query: GraphQL query string
            variables: Optional query variables
            
        Returns:
            Query data from response
            
        Raises:
            Exception: On API or GraphQL error
        """
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
    
    async def _paginated_request(
        self,
        endpoint: str,
        key: str,
        params: Optional[Dict] = None,
        max_pages: int = 10
    ) -> list:
        """
        Fetch all pages of a paginated REST endpoint.
        
        Args:
            endpoint: API endpoint path
            key: Response key containing items (e.g., 'products')
            params: Query parameters
            max_pages: Maximum pages to fetch
            
        Returns:
            Combined list of all items
        """
        all_items = []
        url = f"{self.base_url}{endpoint}"
        page_info = None
        
        for page in range(max_pages):
            request_params = params or {}
            if page_info:
                request_params["page_info"] = page_info
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=self.headers,
                    params=request_params
                ) as response:
                    if response.status >= 400:
                        break
                    
                    result = await response.json()
                    items = result.get(key, [])
                    all_items.extend(items)
                    
                    # Check for next page
                    link = response.headers.get("Link", "")
                    if 'rel="next"' not in link:
                        break
                    
                    # Extract page_info from Link header
                    for part in link.split(","):
                        if 'rel="next"' in part:
                            page_info = part.split("page_info=")[1].split(">")[0]
                            break
        
        return all_items
    
    def get_admin_url(self, resource_type: str, resource_id: str) -> str:
        """
        Get the admin URL for a resource.
        
        Args:
            resource_type: Type of resource (products, orders, customers, etc.)
            resource_id: Resource ID
            
        Returns:
            Full admin URL for the resource
        """
        return f"https://{self.shop_url}/admin/{resource_type}/{resource_id}"
