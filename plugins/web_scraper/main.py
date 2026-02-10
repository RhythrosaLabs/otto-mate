"""
Web Scraper Plugin
==================

Scrape web pages and extract structured data.

Example usage:
    >>> result = await plugin.scrape_page("https://example.com")
    >>> print(result["title"], result["text"][:100])
"""

import re
from typing import Dict, Any, List
from urllib.parse import urljoin, urlparse

try:
    import aiohttp
    from bs4 import BeautifulSoup
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

from src.core.plugin_system import ToolPlugin


class WebScraperPlugin(ToolPlugin):
    """Plugin for web scraping and data extraction."""
    
    async def initialize(self) -> None:
        """Initialize the plugin and register tools."""
        
        if not HAS_DEPS:
            # Register a fallback tool that explains missing deps
            self.register_tool(
                name="scrape_page",
                func=self._missing_deps,
                description="[Requires: pip install aiohttp beautifulsoup4]",
                parameters={"url": {"type": "string", "required": True}}
            )
            return
        
        # Get settings
        self.user_agent = self.settings.get("user_agent", "Otto Web Scraper/1.0")
        self.timeout = self.settings.get("timeout", 30)
        
        # Register scraping tools
        self.register_tool(
            name="scrape_page",
            func=self.scrape_page,
            description="Scrape a web page and extract title, text, and metadata",
            parameters={
                "url": {
                    "type": "string",
                    "required": True,
                    "description": "URL of the page to scrape"
                },
                "include_html": {
                    "type": "boolean",
                    "required": False,
                    "description": "Include raw HTML in response (default: false)"
                }
            }
        )
        
        self.register_tool(
            name="extract_links",
            func=self.extract_links,
            description="Extract all links from a web page",
            parameters={
                "url": {
                    "type": "string",
                    "required": True,
                    "description": "URL of the page"
                },
                "filter_domain": {
                    "type": "string",
                    "required": False,
                    "description": "Only return links matching this domain"
                }
            }
        )
        
        self.register_tool(
            name="extract_tables",
            func=self.extract_tables,
            description="Extract HTML tables as structured data",
            parameters={
                "url": {
                    "type": "string",
                    "required": True,
                    "description": "URL of the page"
                }
            }
        )
        
        self.register_tool(
            name="search_page",
            func=self.search_page,
            description="Search for text or patterns in a web page",
            parameters={
                "url": {
                    "type": "string",
                    "required": True,
                    "description": "URL of the page"
                },
                "query": {
                    "type": "string",
                    "required": True,
                    "description": "Text or regex pattern to search for"
                },
                "use_regex": {
                    "type": "boolean",
                    "required": False,
                    "description": "Treat query as regex pattern (default: false)"
                }
            }
        )
    
    async def _missing_deps(self, **kwargs) -> dict:
        """Return error for missing dependencies."""
        return {
            "success": False,
            "error": "Missing dependencies. Install with: pip install aiohttp beautifulsoup4"
        }
    
    async def _fetch_page(self, url: str) -> tuple:
        """Fetch a page and return (html, status_code)."""
        headers = {"User-Agent": self.user_agent}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, 
                headers=headers, 
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                html = await response.text()
                return html, response.status
    
    async def scrape_page(
        self, 
        url: str, 
        include_html: bool = False
    ) -> Dict[str, Any]:
        """Scrape a web page and extract content."""
        try:
            html, status = await self._fetch_page(url)
            
            if status != 200:
                return {
                    "success": False,
                    "error": f"HTTP {status}",
                    "url": url
                }
            
            soup = BeautifulSoup(html, "html.parser")
            
            # Remove script and style elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()
            
            # Extract data
            title = soup.title.string if soup.title else ""
            
            # Get meta description
            meta_desc = ""
            meta_tag = soup.find("meta", {"name": "description"})
            if meta_tag:
                meta_desc = meta_tag.get("content", "")
            
            # Get main text
            text = soup.get_text(separator="\n", strip=True)
            # Clean up multiple newlines
            text = re.sub(r'\n{3,}', '\n\n', text)
            
            # Count elements
            links = len(soup.find_all("a"))
            images = len(soup.find_all("img"))
            
            result = {
                "success": True,
                "url": url,
                "title": title.strip() if title else "",
                "description": meta_desc,
                "text": text[:5000],  # Limit text length
                "text_length": len(text),
                "link_count": links,
                "image_count": images
            }
            
            if include_html:
                result["html"] = html[:10000]
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "url": url
            }
    
    async def extract_links(
        self, 
        url: str, 
        filter_domain: str = None
    ) -> Dict[str, Any]:
        """Extract all links from a page."""
        try:
            html, status = await self._fetch_page(url)
            
            if status != 200:
                return {"success": False, "error": f"HTTP {status}"}
            
            soup = BeautifulSoup(html, "html.parser")
            base_url = "{uri.scheme}://{uri.netloc}".format(uri=urlparse(url))
            
            links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                
                # Make absolute URL
                if href.startswith("/"):
                    href = urljoin(base_url, href)
                elif not href.startswith("http"):
                    continue
                
                # Filter by domain
                if filter_domain:
                    if filter_domain not in urlparse(href).netloc:
                        continue
                
                link_text = a.get_text(strip=True)[:100] or "[No text]"
                links.append({
                    "url": href,
                    "text": link_text
                })
            
            # Deduplicate
            seen = set()
            unique_links = []
            for link in links:
                if link["url"] not in seen:
                    seen.add(link["url"])
                    unique_links.append(link)
            
            return {
                "success": True,
                "url": url,
                "link_count": len(unique_links),
                "links": unique_links[:100]  # Limit to 100 links
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def extract_tables(self, url: str) -> Dict[str, Any]:
        """Extract HTML tables as structured data."""
        try:
            html, status = await self._fetch_page(url)
            
            if status != 200:
                return {"success": False, "error": f"HTTP {status}"}
            
            soup = BeautifulSoup(html, "html.parser")
            tables = []
            
            for i, table in enumerate(soup.find_all("table")):
                rows = []
                headers = []
                
                # Get headers
                header_row = table.find("thead")
                if header_row:
                    headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]
                
                # Get data rows
                for tr in table.find_all("tr"):
                    cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                    if cells and cells != headers:  # Skip empty or header rows
                        rows.append(cells)
                
                if rows:
                    tables.append({
                        "index": i,
                        "headers": headers,
                        "rows": rows[:50],  # Limit rows
                        "row_count": len(rows)
                    })
            
            return {
                "success": True,
                "url": url,
                "table_count": len(tables),
                "tables": tables
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def search_page(
        self, 
        url: str, 
        query: str, 
        use_regex: bool = False
    ) -> Dict[str, Any]:
        """Search for text or patterns in a page."""
        try:
            html, status = await self._fetch_page(url)
            
            if status != 200:
                return {"success": False, "error": f"HTTP {status}"}
            
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(separator=" ", strip=True)
            
            matches = []
            
            if use_regex:
                pattern = re.compile(query, re.IGNORECASE)
                for match in pattern.finditer(text):
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end]
                    matches.append({
                        "match": match.group(),
                        "context": f"...{context}...",
                        "position": match.start()
                    })
            else:
                # Simple text search
                query_lower = query.lower()
                text_lower = text.lower()
                pos = 0
                
                while True:
                    idx = text_lower.find(query_lower, pos)
                    if idx == -1:
                        break
                    
                    start = max(0, idx - 50)
                    end = min(len(text), idx + len(query) + 50)
                    context = text[start:end]
                    
                    matches.append({
                        "match": text[idx:idx + len(query)],
                        "context": f"...{context}...",
                        "position": idx
                    })
                    
                    pos = idx + 1
                    if len(matches) >= 20:  # Limit matches
                        break
            
            return {
                "success": True,
                "url": url,
                "query": query,
                "match_count": len(matches),
                "matches": matches[:20]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
