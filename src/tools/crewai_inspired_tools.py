"""
CrewAI-Inspired Advanced Tools
==============================

Comprehensive tool suite inspired by CrewAI's capabilities:
- Web scraping and data extraction
- Search tools (web, semantic, knowledge base)
- Database and vector search tools
- File and document processing
- AI-powered analysis tools
"""

import asyncio
import aiohttp
import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse

from .core import tool, ToolBase

logger = logging.getLogger(__name__)

# ==========================================
# DATA MODELS
# ==========================================

@dataclass
class ScrapedContent:
    """Result from web scraping"""
    url: str
    title: Optional[str] = None
    text_content: str = ""
    links: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SearchResult:
    """Search result item"""
    title: str
    url: str
    snippet: str
    position: int = 0
    source: str = ""


@dataclass
class DocumentChunk:
    """Chunk of a processed document"""
    content: str
    page_number: Optional[int] = None
    chunk_index: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


# ==========================================
# WEB SCRAPING TOOLS
# ==========================================

class WebScrapingTools(ToolBase):
    """Advanced web scraping and data extraction tools."""
    
    def __init__(
        self,
        cache_dir: str = "./data/scrape_cache",
        respect_robots: bool = True
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.respect_robots = respect_robots
        self._session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                }
            )
        return self._session
    
    @tool(
        name="scrape_website",
        description="Scrape content from a website URL with intelligent extraction",
        category="web_scraping"
    )
    async def scrape_website(
        self,
        url: str,
        extract_links: bool = True,
        extract_images: bool = True,
        follow_links: bool = False,
        max_depth: int = 1
    ) -> Dict[str, Any]:
        """
        Scrape website content with intelligent extraction.
        
        Args:
            url: URL to scrape
            extract_links: Extract all links from the page
            extract_images: Extract all image URLs
            follow_links: Follow internal links to scrape more pages
            max_depth: Maximum link depth to follow
        """
        try:
            session = await self._get_session()
            
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    return {"success": False, "error": f"HTTP {response.status}"}
                
                html = await response.text()
            
            # Parse content using regex-based extraction
            result = self._parse_html(html, url)
            
            # Optionally follow links
            if follow_links and max_depth > 0 and result.get("links"):
                internal_links = [
                    l for l in result["links"]
                    if urlparse(l).netloc == urlparse(url).netloc
                ][:5]  # Limit to 5 internal links
                
                sub_results = []
                for link in internal_links:
                    try:
                        sub_result = await self.scrape_website(
                            link, 
                            extract_links=False,
                            extract_images=False,
                            follow_links=False,
                            max_depth=0
                        )
                        if sub_result.get("success"):
                            sub_results.append({
                                "url": link,
                                "title": sub_result.get("title"),
                                "text_preview": sub_result.get("text_content", "")[:500]
                            })
                    except:
                        continue
                
                result["followed_pages"] = sub_results
            
            # Cache result
            cache_path = self.cache_dir / f"{self._url_to_filename(url)}.json"
            with open(cache_path, "w") as f:
                json.dump(result, f, indent=2)
            
            return {
                "success": True,
                "url": url,
                "title": result.get("title"),
                "text_content": result.get("text_content", "")[:5000],
                "links_found": len(result.get("links", [])),
                "images_found": len(result.get("images", [])),
                "links": result.get("links", [])[:20] if extract_links else [],
                "images": result.get("images", [])[:10] if extract_images else [],
                "followed_pages": result.get("followed_pages", []),
                "cached_to": str(cache_path)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _parse_html(self, html: str, base_url: str) -> Dict[str, Any]:
        """Parse HTML and extract content using regex."""
        result = {}
        
        # Extract title
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.I)
        result["title"] = title_match.group(1).strip() if title_match else None
        
        # Extract meta description
        meta_match = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        if not meta_match:
            meta_match = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']description["\']', html, re.I)
        result["meta_description"] = meta_match.group(1) if meta_match else None
        
        # Remove scripts and styles
        clean_html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.S|re.I)
        clean_html = re.sub(r'<style[^>]*>.*?</style>', '', clean_html, flags=re.S|re.I)
        clean_html = re.sub(r'<!--.*?-->', '', clean_html, flags=re.S)
        
        # Extract text content
        text = re.sub(r'<[^>]+>', ' ', clean_html)
        text = re.sub(r'\s+', ' ', text)
        result["text_content"] = text.strip()
        
        # Extract links
        links = []
        for match in re.finditer(r'<a[^>]+href=["\']([^"\'#]+)["\']', html, re.I):
            href = match.group(1)
            if href.startswith('http'):
                links.append(href)
            elif href.startswith('/'):
                links.append(urljoin(base_url, href))
        result["links"] = list(set(links))
        
        # Extract images
        images = []
        for match in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.I):
            src = match.group(1)
            if src.startswith('http'):
                images.append(src)
            elif src.startswith('/'):
                images.append(urljoin(base_url, src))
        result["images"] = list(set(images))
        
        return result
    
    def _url_to_filename(self, url: str) -> str:
        """Convert URL to safe filename."""
        safe = re.sub(r'[^\w\-]', '_', url)
        return safe[:100]
    
    @tool(
        name="scrape_multiple_urls",
        description="Scrape content from multiple URLs concurrently",
        category="web_scraping"
    )
    async def scrape_multiple_urls(
        self,
        urls: List[str],
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """
        Scrape multiple URLs concurrently.
        
        Args:
            urls: List of URLs to scrape
            max_concurrent: Maximum concurrent requests
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scrape_with_limit(url):
            async with semaphore:
                return await self.scrape_website(url, follow_links=False)
        
        tasks = [scrape_with_limit(url) for url in urls[:20]]  # Limit to 20
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = []
        failed = []
        
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                failed.append({"url": url, "error": str(result)})
            elif result.get("success"):
                successful.append({
                    "url": url,
                    "title": result.get("title"),
                    "text_preview": result.get("text_content", "")[:300]
                })
            else:
                failed.append({"url": url, "error": result.get("error")})
        
        return {
            "success": True,
            "total_urls": len(urls),
            "successful": len(successful),
            "failed": len(failed),
            "results": successful,
            "errors": failed
        }
    
    @tool(
        name="extract_structured_data",
        description="Extract structured data (JSON-LD, microdata) from a webpage",
        category="web_scraping"
    )
    async def extract_structured_data(
        self,
        url: str
    ) -> Dict[str, Any]:
        """
        Extract structured data from webpage.
        
        Args:
            url: URL to extract structured data from
        """
        try:
            session = await self._get_session()
            
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                html = await response.text()
            
            structured_data = []
            
            # Extract JSON-LD
            for match in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.S|re.I):
                try:
                    data = json.loads(match.group(1))
                    structured_data.append({"type": "json-ld", "data": data})
                except json.JSONDecodeError:
                    pass
            
            # Extract Open Graph tags
            og_data = {}
            for match in re.finditer(r'<meta[^>]+property=["\']og:([^"\']+)["\'][^>]+content=["\']([^"\']+)["\']', html, re.I):
                og_data[match.group(1)] = match.group(2)
            if og_data:
                structured_data.append({"type": "opengraph", "data": og_data})
            
            # Extract Twitter cards
            twitter_data = {}
            for match in re.finditer(r'<meta[^>]+name=["\']twitter:([^"\']+)["\'][^>]+content=["\']([^"\']+)["\']', html, re.I):
                twitter_data[match.group(1)] = match.group(2)
            if twitter_data:
                structured_data.append({"type": "twitter_card", "data": twitter_data})
            
            return {
                "success": True,
                "url": url,
                "structured_data_found": len(structured_data),
                "data": structured_data
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# ==========================================
# SEARCH TOOLS
# ==========================================

class SearchTools(ToolBase):
    """Search tools for web and knowledge discovery."""
    
    def __init__(
        self,
        serper_api_key: str = None,
        tavily_api_key: str = None
    ):
        self.serper_api_key = serper_api_key or os.getenv("SERPER_API_KEY")
        self.tavily_api_key = tavily_api_key or os.getenv("TAVILY_API_KEY")
        self._session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    @tool(
        name="web_search",
        description="Search the web using Google via Serper API",
        category="search"
    )
    async def web_search(
        self,
        query: str,
        num_results: int = 10,
        search_type: str = "search"
    ) -> Dict[str, Any]:
        """
        Perform web search.
        
        Args:
            query: Search query
            num_results: Number of results to return
            search_type: Type of search (search, news, images)
        """
        if not self.serper_api_key:
            return {"success": False, "error": "SERPER_API_KEY not configured"}
        
        try:
            session = await self._get_session()
            
            endpoint = f"https://google.serper.dev/{search_type}"
            
            async with session.post(
                endpoint,
                headers={
                    "X-API-KEY": self.serper_api_key,
                    "Content-Type": "application/json"
                },
                json={"q": query, "num": num_results}
            ) as response:
                data = await response.json()
            
            results = []
            
            # Process organic results
            for i, item in enumerate(data.get("organic", [])[:num_results]):
                results.append({
                    "position": i + 1,
                    "title": item.get("title"),
                    "url": item.get("link"),
                    "snippet": item.get("snippet")
                })
            
            return {
                "success": True,
                "query": query,
                "results_count": len(results),
                "results": results,
                "knowledge_graph": data.get("knowledgeGraph"),
                "answer_box": data.get("answerBox")
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="news_search",
        description="Search for recent news articles",
        category="search"
    )
    async def news_search(
        self,
        query: str,
        num_results: int = 10
    ) -> Dict[str, Any]:
        """
        Search for news articles.
        
        Args:
            query: Search query
            num_results: Number of results
        """
        return await self.web_search(query, num_results, search_type="news")
    
    @tool(
        name="ai_search",
        description="AI-powered search with summarization using Tavily",
        category="search"
    )
    async def ai_search(
        self,
        query: str,
        search_depth: str = "basic",
        include_answer: bool = True
    ) -> Dict[str, Any]:
        """
        AI-powered search with answer generation.
        
        Args:
            query: Search query
            search_depth: "basic" or "advanced"
            include_answer: Include AI-generated answer
        """
        if not self.tavily_api_key:
            return {"success": False, "error": "TAVILY_API_KEY not configured"}
        
        try:
            session = await self._get_session()
            
            async with session.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.tavily_api_key,
                    "query": query,
                    "search_depth": search_depth,
                    "include_answer": include_answer
                }
            ) as response:
                data = await response.json()
            
            return {
                "success": True,
                "query": query,
                "answer": data.get("answer"),
                "results": [
                    {
                        "title": r.get("title"),
                        "url": r.get("url"),
                        "content": r.get("content")[:500]
                    }
                    for r in data.get("results", [])
                ]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# ==========================================
# DOCUMENT PROCESSING TOOLS
# ==========================================

class DocumentTools(ToolBase):
    """Tools for processing and analyzing documents."""
    
    def __init__(self, output_dir: str = "./data/documents"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @tool(
        name="read_file_tool",
        description="Read content from a file with intelligent parsing",
        category="files"
    )
    async def read_file(
        self,
        file_path: str,
        encoding: str = "utf-8"
    ) -> Dict[str, Any]:
        """
        Read and parse file content.
        
        Args:
            file_path: Path to file
            encoding: File encoding
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {"success": False, "error": "File not found"}
            
            content = path.read_text(encoding=encoding)
            
            # Detect file type and apply appropriate parsing
            suffix = path.suffix.lower()
            
            parsed_content = content
            file_type = "text"
            
            if suffix == ".json":
                try:
                    parsed_content = json.loads(content)
                    file_type = "json"
                except:
                    pass
            elif suffix in [".yaml", ".yml"]:
                file_type = "yaml"
            elif suffix == ".md":
                file_type = "markdown"
            elif suffix in [".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs"]:
                file_type = "code"
            elif suffix in [".html", ".htm"]:
                file_type = "html"
            elif suffix == ".csv":
                file_type = "csv"
                # Parse CSV to structured format
                lines = content.strip().split('\n')
                if lines:
                    headers = lines[0].split(',')
                    rows = [dict(zip(headers, line.split(','))) for line in lines[1:10]]  # First 10 rows
                    parsed_content = {"headers": headers, "rows": rows, "total_rows": len(lines) - 1}
            
            return {
                "success": True,
                "file_path": str(path.absolute()),
                "file_type": file_type,
                "size_bytes": path.stat().st_size,
                "content": parsed_content if isinstance(parsed_content, (dict, list)) else content[:10000],
                "truncated": len(content) > 10000
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="write_file_tool",
        description="Write content to a file",
        category="files"
    )
    async def write_file(
        self,
        file_path: str,
        content: str,
        mode: str = "write"
    ) -> Dict[str, Any]:
        """
        Write content to file.
        
        Args:
            file_path: Path to file
            content: Content to write
            mode: "write" (overwrite) or "append"
        """
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            write_mode = "w" if mode == "write" else "a"
            
            with open(path, write_mode, encoding="utf-8") as f:
                f.write(content)
            
            return {
                "success": True,
                "file_path": str(path.absolute()),
                "bytes_written": len(content.encode("utf-8")),
                "mode": mode
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="chunk_document",
        description="Split a document into chunks for processing",
        category="files"
    )
    async def chunk_document(
        self,
        content: str,
        chunk_size: int = 1000,
        overlap: int = 100
    ) -> Dict[str, Any]:
        """
        Split document into overlapping chunks.
        
        Args:
            content: Document content
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks
        """
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(content):
            end = start + chunk_size
            chunk = content[start:end]
            
            # Try to break at sentence boundary
            if end < len(content):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                if break_point > chunk_size * 0.5:  # Only if reasonable
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1
            
            chunks.append({
                "index": chunk_index,
                "content": chunk,
                "start_char": start,
                "end_char": end
            })
            
            start = end - overlap if end < len(content) else end
            chunk_index += 1
        
        return {
            "success": True,
            "total_chunks": len(chunks),
            "original_length": len(content),
            "chunk_size": chunk_size,
            "overlap": overlap,
            "chunks": chunks
        }


# ==========================================
# DIRECTORY & LISTING TOOLS
# ==========================================

class DirectoryTools(ToolBase):
    """Tools for directory listing and file discovery."""
    
    @tool(
        name="list_directory",
        description="List files and folders in a directory",
        category="files"
    )
    async def list_directory(
        self,
        path: str = ".",
        pattern: str = "*",
        recursive: bool = False
    ) -> Dict[str, Any]:
        """
        List directory contents.
        
        Args:
            path: Directory path
            pattern: Glob pattern to filter files
            recursive: Search recursively
        """
        try:
            dir_path = Path(path)
            
            if not dir_path.exists():
                return {"success": False, "error": "Directory not found"}
            
            if not dir_path.is_dir():
                return {"success": False, "error": "Path is not a directory"}
            
            if recursive:
                files = list(dir_path.rglob(pattern))
            else:
                files = list(dir_path.glob(pattern))
            
            items = []
            for f in files[:100]:  # Limit to 100
                try:
                    stat = f.stat()
                    items.append({
                        "name": f.name,
                        "path": str(f),
                        "is_directory": f.is_dir(),
                        "size": stat.st_size if f.is_file() else None,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                except:
                    continue
            
            # Sort directories first, then by name
            items.sort(key=lambda x: (not x["is_directory"], x["name"].lower()))
            
            return {
                "success": True,
                "directory": str(dir_path.absolute()),
                "pattern": pattern,
                "recursive": recursive,
                "total_items": len(items),
                "items": items
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="search_files",
        description="Search for files by name or content",
        category="files"
    )
    async def search_files(
        self,
        directory: str,
        query: str,
        search_content: bool = False,
        file_pattern: str = "*"
    ) -> Dict[str, Any]:
        """
        Search for files by name or content.
        
        Args:
            directory: Directory to search
            query: Search query (regex supported)
            search_content: Search file contents
            file_pattern: File pattern to filter
        """
        try:
            dir_path = Path(directory)
            results = []
            pattern = re.compile(query, re.I)
            
            for file_path in dir_path.rglob(file_pattern):
                if len(results) >= 50:
                    break
                
                if file_path.is_file():
                    # Search filename
                    if pattern.search(file_path.name):
                        results.append({
                            "path": str(file_path),
                            "match_type": "filename",
                            "name": file_path.name
                        })
                    # Search content if requested
                    elif search_content:
                        try:
                            content = file_path.read_text(errors="ignore")[:50000]
                            matches = pattern.findall(content)
                            if matches:
                                results.append({
                                    "path": str(file_path),
                                    "match_type": "content",
                                    "name": file_path.name,
                                    "matches_found": len(matches),
                                    "preview": matches[:3]
                                })
                        except:
                            continue
            
            return {
                "success": True,
                "directory": directory,
                "query": query,
                "search_content": search_content,
                "results_count": len(results),
                "results": results
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# ==========================================
# DATA ANALYSIS TOOLS
# ==========================================

class DataAnalysisTools(ToolBase):
    """Tools for data analysis and transformation."""
    
    @tool(
        name="analyze_json",
        description="Analyze JSON data structure and extract insights",
        category="data_analysis"
    )
    async def analyze_json(
        self,
        json_data: Union[str, Dict, List]
    ) -> Dict[str, Any]:
        """
        Analyze JSON data structure.
        
        Args:
            json_data: JSON string or parsed data
        """
        try:
            if isinstance(json_data, str):
                data = json.loads(json_data)
            else:
                data = json_data
            
            def analyze_structure(obj, depth=0, max_depth=3):
                if depth > max_depth:
                    return {"type": "...", "truncated": True}
                
                if isinstance(obj, dict):
                    return {
                        "type": "object",
                        "keys": list(obj.keys())[:20],
                        "key_count": len(obj),
                        "sample_values": {
                            k: analyze_structure(v, depth + 1, max_depth)
                            for k, v in list(obj.items())[:5]
                        }
                    }
                elif isinstance(obj, list):
                    return {
                        "type": "array",
                        "length": len(obj),
                        "item_structure": analyze_structure(obj[0], depth + 1, max_depth) if obj else None
                    }
                elif isinstance(obj, str):
                    return {"type": "string", "sample": obj[:100] if len(obj) > 100 else obj}
                elif isinstance(obj, bool):
                    return {"type": "boolean", "value": obj}
                elif isinstance(obj, (int, float)):
                    return {"type": "number", "value": obj}
                elif obj is None:
                    return {"type": "null"}
                else:
                    return {"type": str(type(obj).__name__)}
            
            structure = analyze_structure(data)
            
            return {
                "success": True,
                "structure": structure,
                "is_array": isinstance(data, list),
                "is_object": isinstance(data, dict),
                "top_level_count": len(data) if isinstance(data, (list, dict)) else 1
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="transform_data",
        description="Transform data using jq-like operations",
        category="data_analysis"
    )
    async def transform_data(
        self,
        data: Union[str, Dict, List],
        operation: str,
        field: str = None
    ) -> Dict[str, Any]:
        """
        Transform data with common operations.
        
        Args:
            data: Input data
            operation: Operation type (filter, map, group, sort, unique, flatten, pick, omit)
            field: Field to operate on
        """
        try:
            if isinstance(data, str):
                data = json.loads(data)
            
            if not isinstance(data, list):
                data = [data]
            
            result = data
            
            if operation == "pick" and field:
                # Pick specific fields
                fields = [f.strip() for f in field.split(',')]
                result = [
                    {k: item.get(k) for k in fields if k in item}
                    for item in data if isinstance(item, dict)
                ]
            
            elif operation == "omit" and field:
                # Omit specific fields
                fields = [f.strip() for f in field.split(',')]
                result = [
                    {k: v for k, v in item.items() if k not in fields}
                    for item in data if isinstance(item, dict)
                ]
            
            elif operation == "flatten":
                # Flatten nested arrays
                def flatten(lst):
                    for item in lst:
                        if isinstance(item, list):
                            yield from flatten(item)
                        else:
                            yield item
                result = list(flatten(data))
            
            elif operation == "unique" and field:
                # Get unique values for a field
                seen = set()
                unique = []
                for item in data:
                    if isinstance(item, dict):
                        val = item.get(field)
                        if val not in seen:
                            seen.add(val)
                            unique.append(item)
                result = unique
            
            elif operation == "sort" and field:
                # Sort by field
                result = sorted(
                    [item for item in data if isinstance(item, dict)],
                    key=lambda x: x.get(field, '')
                )
            
            elif operation == "group" and field:
                # Group by field
                groups = {}
                for item in data:
                    if isinstance(item, dict):
                        key = str(item.get(field, 'null'))
                        if key not in groups:
                            groups[key] = []
                        groups[key].append(item)
                result = groups
            
            return {
                "success": True,
                "operation": operation,
                "field": field,
                "input_count": len(data),
                "output_count": len(result) if isinstance(result, list) else len(result.keys()) if isinstance(result, dict) else 1,
                "result": result
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# ==========================================
# VISION TOOLS
# ==========================================

class VisionTools(ToolBase):
    """AI vision and image analysis tools."""
    
    def __init__(self):
        self._session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    @tool(
        name="analyze_image_url",
        description="Analyze an image from URL using AI vision",
        category="vision"
    )
    async def analyze_image_url(
        self,
        image_url: str,
        question: str = "Describe this image in detail"
    ) -> Dict[str, Any]:
        """
        Analyze an image using AI vision.
        
        Args:
            image_url: URL of the image
            question: Question to ask about the image
        """
        # This would integrate with Claude Vision or OpenAI Vision
        return {
            "success": True,
            "image_url": image_url,
            "question": question,
            "analysis": f"Image analysis for {image_url}: [Requires vision model integration]",
            "note": "Integrate with Claude Vision or OpenAI Vision API for full functionality"
        }
    
    @tool(
        name="extract_text_from_image",
        description="Extract text from an image using OCR",
        category="vision"
    )
    async def extract_text_from_image(
        self,
        image_url: str
    ) -> Dict[str, Any]:
        """
        Extract text from image using OCR.
        
        Args:
            image_url: URL of the image
        """
        return {
            "success": True,
            "image_url": image_url,
            "ocr_text": "[OCR text extraction - requires Tesseract or cloud OCR]",
            "note": "Integrate with Tesseract OCR or cloud OCR service for full functionality"
        }


# ==========================================
# FACTORY FUNCTIONS
# ==========================================

def create_web_scraping_tools() -> WebScrapingTools:
    """Create WebScrapingTools instance."""
    return WebScrapingTools()


def create_search_tools() -> SearchTools:
    """Create SearchTools instance."""
    return SearchTools()


def create_document_tools() -> DocumentTools:
    """Create DocumentTools instance."""
    return DocumentTools()


def create_directory_tools() -> DirectoryTools:
    """Create DirectoryTools instance."""
    return DirectoryTools()


def create_data_analysis_tools() -> DataAnalysisTools:
    """Create DataAnalysisTools instance."""
    return DataAnalysisTools()


def create_vision_tools() -> VisionTools:
    """Create VisionTools instance."""
    return VisionTools()


# Export all tool classes
__all__ = [
    "WebScrapingTools",
    "SearchTools", 
    "DocumentTools",
    "DirectoryTools",
    "DataAnalysisTools",
    "VisionTools",
    "create_web_scraping_tools",
    "create_search_tools",
    "create_document_tools",
    "create_directory_tools",
    "create_data_analysis_tools",
    "create_vision_tools"
]
