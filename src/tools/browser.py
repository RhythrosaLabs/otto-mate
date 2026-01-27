"""
Browser Automation Tools
========================

Tools for browser automation using Playwright.
"""

import logging
import asyncio
import base64
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import playwright
try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed. Browser tools will be limited.")

from .core import tool, ToolBase


class BrowserTools(ToolBase):
    """Browser automation tools using Playwright."""
    
    def __init__(
        self,
        headless: bool = True,
        screenshot_dir: str = "./data/screenshots"
    ):
        self.headless = headless
        self.screenshot_dir = Path(screenshot_dir)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None
    
    async def _ensure_browser(self):
        """Ensure browser is initialized."""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright not installed. Run: pip install playwright && playwright install")
        
        if not self._browser:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=self.headless)
        
        if not self._page:
            self._page = await self._browser.new_page()
    
    async def close(self):
        """Close browser."""
        if self._page:
            await self._page.close()
            self._page = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
    
    @tool(
        name="browser_navigate",
        description="Navigate to a URL in the browser",
        category="browser"
    )
    async def navigate(self, url: str) -> Dict[str, Any]:
        """
        Navigate to a URL.
        
        Args:
            url: URL to navigate to
        """
        await self._ensure_browser()
        
        try:
            response = await self._page.goto(url, wait_until="networkidle")
            
            return {
                "success": True,
                "url": self._page.url,
                "title": await self._page.title(),
                "status": response.status if response else None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @tool(
        name="browser_screenshot",
        description="Take a screenshot of the current page",
        category="browser"
    )
    async def screenshot(
        self,
        full_page: bool = False,
        selector: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Take a screenshot.
        
        Args:
            full_page: Capture full scrollable page
            selector: CSS selector of element to screenshot
        """
        await self._ensure_browser()
        
        try:
            import uuid
            filename = f"{uuid.uuid4().hex[:8]}.png"
            filepath = self.screenshot_dir / filename
            
            if selector:
                element = await self._page.query_selector(selector)
                if element:
                    await element.screenshot(path=str(filepath))
                else:
                    return {"success": False, "error": f"Element not found: {selector}"}
            else:
                await self._page.screenshot(path=str(filepath), full_page=full_page)
            
            # Also get base64
            with open(filepath, "rb") as f:
                image_base64 = base64.b64encode(f.read()).decode()
            
            return {
                "success": True,
                "path": str(filepath),
                "image_base64": image_base64,
                "url": self._page.url
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="browser_click",
        description="Click an element on the page",
        category="browser"
    )
    async def click(
        self,
        selector: str,
        timeout: int = 5000
    ) -> Dict[str, Any]:
        """
        Click an element.
        
        Args:
            selector: CSS selector or text to click
            timeout: Timeout in milliseconds
        """
        await self._ensure_browser()
        
        try:
            # Try CSS selector first
            try:
                await self._page.click(selector, timeout=timeout)
            except:
                # Try text content
                await self._page.click(f"text={selector}", timeout=timeout)
            
            await self._page.wait_for_load_state("networkidle")
            
            return {
                "success": True,
                "clicked": selector,
                "current_url": self._page.url
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="browser_type",
        description="Type text into an input field",
        category="browser"
    )
    async def type_text(
        self,
        selector: str,
        text: str,
        clear_first: bool = True
    ) -> Dict[str, Any]:
        """
        Type text into an element.
        
        Args:
            selector: CSS selector of input
            text: Text to type
            clear_first: Clear existing text first
        """
        await self._ensure_browser()
        
        try:
            if clear_first:
                await self._page.fill(selector, text)
            else:
                await self._page.type(selector, text)
            
            return {
                "success": True,
                "selector": selector,
                "typed": text
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="browser_get_text",
        description="Get text content from an element",
        category="browser"
    )
    async def get_text(
        self,
        selector: str
    ) -> Dict[str, Any]:
        """
        Get text content of an element.
        
        Args:
            selector: CSS selector
        """
        await self._ensure_browser()
        
        try:
            element = await self._page.query_selector(selector)
            if element:
                text = await element.text_content()
                return {
                    "success": True,
                    "text": text.strip() if text else "",
                    "selector": selector
                }
            return {"success": False, "error": "Element not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="browser_get_page_content",
        description="Get the full text content of the current page",
        category="browser"
    )
    async def get_page_content(self) -> Dict[str, Any]:
        """Get full page text content."""
        await self._ensure_browser()
        
        try:
            # Get all text
            text = await self._page.evaluate("() => document.body.innerText")
            
            # Get links
            links = await self._page.evaluate("""
                () => Array.from(document.querySelectorAll('a'))
                    .map(a => ({text: a.innerText, href: a.href}))
                    .filter(l => l.href && l.text)
                    .slice(0, 50)
            """)
            
            return {
                "success": True,
                "url": self._page.url,
                "title": await self._page.title(),
                "text": text[:10000],
                "links": links
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="browser_scroll",
        description="Scroll the page",
        category="browser"
    )
    async def scroll(
        self,
        direction: str = "down",
        amount: int = 500
    ) -> Dict[str, Any]:
        """
        Scroll the page.
        
        Args:
            direction: Scroll direction (up, down)
            amount: Pixels to scroll
        """
        await self._ensure_browser()
        
        try:
            if direction == "down":
                await self._page.evaluate(f"window.scrollBy(0, {amount})")
            else:
                await self._page.evaluate(f"window.scrollBy(0, -{amount})")
            
            await asyncio.sleep(0.5)  # Wait for scroll
            
            return {
                "success": True,
                "direction": direction,
                "amount": amount
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="browser_wait",
        description="Wait for an element or condition",
        category="browser"
    )
    async def wait_for(
        self,
        selector: str,
        state: str = "visible",
        timeout: int = 10000
    ) -> Dict[str, Any]:
        """
        Wait for an element.
        
        Args:
            selector: CSS selector
            state: State to wait for (visible, hidden, attached, detached)
            timeout: Timeout in milliseconds
        """
        await self._ensure_browser()
        
        try:
            await self._page.wait_for_selector(selector, state=state, timeout=timeout)
            return {
                "success": True,
                "selector": selector,
                "state": state
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="browser_fill_form",
        description="Fill out a form with multiple fields",
        category="browser"
    )
    async def fill_form(
        self,
        fields: Dict[str, str],
        submit_selector: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fill out a form.
        
        Args:
            fields: Dict of selector -> value pairs
            submit_selector: Optional submit button selector
        """
        await self._ensure_browser()
        
        try:
            for selector, value in fields.items():
                await self._page.fill(selector, value)
            
            if submit_selector:
                await self._page.click(submit_selector)
                await self._page.wait_for_load_state("networkidle")
            
            return {
                "success": True,
                "fields_filled": len(fields),
                "submitted": submit_selector is not None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="browser_execute_script",
        description="Execute JavaScript on the page",
        category="browser"
    )
    async def execute_script(self, script: str) -> Dict[str, Any]:
        """
        Execute JavaScript.
        
        Args:
            script: JavaScript code to execute
        """
        await self._ensure_browser()
        
        try:
            result = await self._page.evaluate(script)
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="browser_social_post",
        description="Post content to a social media platform (requires logged in session)",
        category="browser"
    )
    async def social_post(
        self,
        platform: str,
        content: str,
        image_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Post to social media.
        
        Args:
            platform: Platform name (twitter, instagram, facebook)
            content: Post content
            image_path: Optional path to image
        """
        await self._ensure_browser()
        
        try:
            if platform == "twitter":
                # Navigate to compose
                await self._page.goto("https://twitter.com/compose/tweet")
                await asyncio.sleep(2)
                
                # Type content
                await self._page.fill('[data-testid="tweetTextarea_0"]', content)
                
                # Optionally add image
                if image_path:
                    await self._page.set_input_files('input[type="file"]', image_path)
                    await asyncio.sleep(2)
                
                # Click post
                await self._page.click('[data-testid="tweetButton"]')
                await asyncio.sleep(2)
                
                return {
                    "success": True,
                    "platform": platform,
                    "content": content
                }
            
            return {
                "success": False,
                "error": f"Platform {platform} not yet supported"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
