"""
Research & Web Tools
====================

Tools for web research, searching, and data gathering.
"""

import logging
import aiohttp
import asyncio
from typing import Optional, Dict, Any, List
from urllib.parse import quote_plus
from .core import tool, ToolBase

logger = logging.getLogger(__name__)


class ResearchTools(ToolBase):
    """Web research and information gathering tools."""
    
    def __init__(self, config: Optional[Dict[str, str]] = None):
        self.config = config or {}
        self.serper_key = self.config.get("serper_api_key")
        self.brave_key = self.config.get("brave_api_key")
    
    @tool(
        name="search_web",
        description="Search the web for information",
        category="research"
    )
    async def search_web(
        self,
        query: str,
        num_results: int = 10
    ) -> Dict[str, Any]:
        """
        Search the web using multiple providers.
        
        Args:
            query: Search query
            num_results: Number of results to return
        """
        # Try DuckDuckGo (no API key needed)
        try:
            return await self._search_duckduckgo(query, num_results)
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {e}")
        
        # Fallback to Serper if available
        if self.serper_key:
            try:
                return await self._search_serper(query, num_results)
            except Exception as e:
                logger.warning(f"Serper search failed: {e}")
        
        return {
            "success": False,
            "error": "No search providers available",
            "results": []
        }
    
    async def _search_duckduckgo(
        self,
        query: str,
        num_results: int
    ) -> Dict[str, Any]:
        """Search using DuckDuckGo HTML."""
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"}
            ) as response:
                html = await response.text()
        
        # Parse results (basic extraction)
        results = []
        # This is a simplified parser - in production use BeautifulSoup
        import re
        
        # Find result blocks
        links = re.findall(r'class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)', html)
        snippets = re.findall(r'class="result__snippet"[^>]*>([^<]+)', html)
        
        for i, (link, title) in enumerate(links[:num_results]):
            result = {
                "title": title.strip(),
                "url": link,
                "snippet": snippets[i].strip() if i < len(snippets) else ""
            }
            results.append(result)
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "source": "duckduckgo"
        }
    
    async def _search_serper(
        self,
        query: str,
        num_results: int
    ) -> Dict[str, Any]:
        """Search using Serper API."""
        url = "https://google.serper.dev/search"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers={
                    "X-API-KEY": self.serper_key,
                    "Content-Type": "application/json"
                },
                json={"q": query, "num": num_results}
            ) as response:
                data = await response.json()
        
        results = []
        for item in data.get("organic", []):
            results.append({
                "title": item.get("title"),
                "url": item.get("link"),
                "snippet": item.get("snippet")
            })
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "source": "serper"
        }
    
    @tool(
        name="browse_url",
        description="Fetch and extract content from a URL",
        category="research"
    )
    async def browse_url(
        self,
        url: str,
        extract_type: str = "text"
    ) -> Dict[str, Any]:
        """
        Fetch content from a URL.
        
        Args:
            url: URL to fetch
            extract_type: What to extract (text, links, images, all)
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; OttoBot/1.0)"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status >= 400:
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}",
                            "url": url
                        }
                    
                    html = await response.text()
            
            # Basic text extraction
            import re
            
            # Remove scripts and styles
            clean = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.DOTALL | re.IGNORECASE)
            
            # Extract text
            text = re.sub(r'<[^>]+>', ' ', clean)
            text = re.sub(r'\s+', ' ', text).strip()
            
            result = {
                "success": True,
                "url": url,
                "text": text[:10000]  # Limit text length
            }
            
            if extract_type in ["links", "all"]:
                links = re.findall(r'href="(https?://[^"]+)"', html)
                result["links"] = list(set(links))[:50]
            
            if extract_type in ["images", "all"]:
                images = re.findall(r'src="(https?://[^"]+\.(jpg|jpeg|png|gif|webp))"', html, re.IGNORECASE)
                result["images"] = list(set(img[0] for img in images))[:20]
            
            # Extract title
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
            if title_match:
                result["title"] = title_match.group(1).strip()
            
            return result
            
        except Exception as e:
            logger.error(f"Browse error: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url
            }
    
    @tool(
        name="search_images",
        description="Search for images on the web",
        category="research"
    )
    async def search_images(
        self,
        query: str,
        num_results: int = 10
    ) -> Dict[str, Any]:
        """
        Search for images.
        
        Args:
            query: Image search query
            num_results: Number of results
        """
        # Use Serper image search if available
        if self.serper_key:
            url = "https://google.serper.dev/images"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers={
                        "X-API-KEY": self.serper_key,
                        "Content-Type": "application/json"
                    },
                    json={"q": query, "num": num_results}
                ) as response:
                    data = await response.json()
            
            images = []
            for item in data.get("images", []):
                images.append({
                    "url": item.get("imageUrl"),
                    "title": item.get("title"),
                    "source": item.get("link"),
                    "thumbnail": item.get("thumbnailUrl")
                })
            
            return {
                "success": True,
                "query": query,
                "images": images
            }
        
        return {
            "success": False,
            "error": "No image search provider available"
        }
    
    @tool(
        name="get_trending_topics",
        description="Get trending topics and news",
        category="research"
    )
    async def get_trending_topics(
        self,
        category: str = "general"
    ) -> Dict[str, Any]:
        """
        Get trending topics.
        
        Args:
            category: Topic category (general, tech, business, entertainment)
        """
        # Search for trending topics
        queries = {
            "general": "trending topics today",
            "tech": "trending technology news",
            "business": "trending business news",
            "entertainment": "trending entertainment news",
            "fashion": "trending fashion trends"
        }
        
        query = queries.get(category, queries["general"])
        return await self.search_web(query, num_results=15)
    
    @tool(
        name="analyze_competitor",
        description="Analyze a competitor website or product",
        category="research"
    )
    async def analyze_competitor(
        self,
        url: str
    ) -> Dict[str, Any]:
        """
        Analyze a competitor's website.
        
        Args:
            url: Competitor website URL
        """
        # Fetch main page
        main_page = await self.browse_url(url, extract_type="all")
        
        if not main_page["success"]:
            return main_page
        
        # Search for reviews
        domain = url.split("//")[-1].split("/")[0]
        reviews = await self.search_web(f"{domain} reviews", num_results=5)
        
        return {
            "success": True,
            "url": url,
            "title": main_page.get("title", ""),
            "content_preview": main_page.get("text", "")[:2000],
            "internal_links": len(main_page.get("links", [])),
            "images_found": len(main_page.get("images", [])),
            "reviews": reviews.get("results", [])
        }
    
    @tool(
        name="research_topic",
        description="Comprehensive research on a topic",
        category="research"
    )
    async def research_topic(
        self,
        topic: str,
        depth: str = "standard"
    ) -> Dict[str, Any]:
        """
        Comprehensive research on a topic.
        
        Args:
            topic: Topic to research
            depth: Research depth (quick, standard, deep)
        """
        results = {
            "topic": topic,
            "search_results": [],
            "key_sources": [],
            "summary_points": []
        }
        
        # Main search
        num_results = {"quick": 5, "standard": 10, "deep": 20}.get(depth, 10)
        search = await self.search_web(topic, num_results=num_results)
        results["search_results"] = search.get("results", [])
        
        # Deep research: fetch top sources
        if depth in ["standard", "deep"]:
            for result in results["search_results"][:3]:
                try:
                    content = await self.browse_url(result["url"])
                    if content["success"]:
                        results["key_sources"].append({
                            "url": result["url"],
                            "title": result["title"],
                            "content": content.get("text", "")[:3000]
                        })
                except Exception:
                    pass
        
        return {
            "success": True,
            **results
        }
