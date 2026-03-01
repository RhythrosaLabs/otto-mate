"""
Advanced Browser-Use Integration (v0.11.x)
===========================================

AI-powered browser automation using browser-use 0.11.x with:
- Full stealth/anti-detection (BrowserProfile, extensions, proxy)
- Social media bot-bypass capabilities
- Custom tools via @tools.action() registry
- Human-like behavior injection
- Lead generation, form automation, competitive intel

Requires: browser-use>=0.11.0, playwright-stealth (optional)
"""

import asyncio
import json
import logging
import os
import random
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from .core import tool, ToolBase

logger = logging.getLogger(__name__)

# ==========================================
# IMPORTS: browser-use 0.11.x API
# ==========================================

try:
    from browser_use import Agent, Browser, BrowserProfile, Tools, ActionResult
    from browser_use.browser.profile import ProxySettings
    BROWSER_USE_AVAILABLE = True
    BROWSER_USE_VERSION = "0.11"
except ImportError:
    try:
        from browser_use import Agent, Browser, BrowserConfig
        BROWSER_USE_AVAILABLE = True
        BROWSER_USE_VERSION = "0.1"
        BrowserProfile = BrowserConfig
    except ImportError:
        BROWSER_USE_AVAILABLE = False
        BROWSER_USE_VERSION = None
        logger.warning("browser-use not installed. Run: pip install browser-use")

try:
    from langchain_anthropic import ChatAnthropic
    from langchain_openai import ChatOpenAI
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

# browser-use 0.11.x has its own LLM classes
try:
    from browser_use.llm.models import get_llm_by_name
    from browser_use.llm.base import BaseChatModel
    from browser_use.llm.views import ChatInvokeCompletion, ChatInvokeUsage
    from browser_use.llm.messages import UserMessage, SystemMessage, AssistantMessage
    BROWSER_USE_LLM_AVAILABLE = True
except ImportError:
    BROWSER_USE_LLM_AVAILABLE = False
    BaseChatModel = object
    ChatInvokeCompletion = None
    ChatInvokeUsage = None

# Custom Anthropic adapter for browser-use 0.11.x
try:
    import anthropic
    ANTHROPIC_SDK_AVAILABLE = True
except ImportError:
    ANTHROPIC_SDK_AVAILABLE = False

try:
    from .browser_stealth import (
        create_stealth_profile,
        create_social_media_profile,
        find_chrome_path,
        random_delay,
        SOCIAL_PLATFORM_DOMAINS,
    )
    STEALTH_CONFIG_AVAILABLE = True
except ImportError:
    STEALTH_CONFIG_AVAILABLE = False
    logger.info("browser_stealth module not available")


# ==========================================
# CUSTOM ANTHROPIC ADAPTER FOR BROWSER-USE
# ==========================================

class ChatAnthropicAdapter(BaseChatModel if BROWSER_USE_LLM_AVAILABLE else object):
    """
    Custom Anthropic adapter for browser-use 0.11.x.
    
    browser-use 0.11.x doesn't directly support Anthropic API, so we create
    an adapter that conforms to browser-use's BaseChatModel interface.
    """
    
    def __init__(self, model: str = "claude-sonnet-4-20250514", api_key: str = None):
        self.model = model
        self._model_name = model
        self._provider = "anthropic"
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        self._client = None
    
    @property
    def model_name(self) -> str:
        return self._model_name
    
    @property
    def name(self) -> str:
        return f"anthropic/{self.model}"
    
    @property
    def provider(self) -> str:
        return self._provider
    
    def _get_client(self):
        if self._client is None:
            if not ANTHROPIC_SDK_AVAILABLE:
                raise RuntimeError("anthropic package not installed. Run: pip install anthropic")
            self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
        return self._client
    
    async def ainvoke(self, messages, output_format=None, **kwargs):
        """Invoke Anthropic API and return browser-use compatible response."""
        import json
        client = self._get_client()
        
        # Convert browser-use messages to Anthropic format
        anthropic_messages = []
        system_content = None
        
        for msg in messages:
            if hasattr(msg, 'role'):
                role = msg.role
            else:
                role = getattr(msg, '__class__', type(msg)).__name__.lower().replace('message', '')
            
            # Extract content
            if hasattr(msg, 'content'):
                content = msg.content
            elif hasattr(msg, 'text'):
                content = msg.text
            else:
                content = str(msg)
            
            # Handle content that might be a list (images + text)
            if isinstance(content, list):
                anthropic_content = []
                for part in content:
                    if hasattr(part, 'text'):
                        anthropic_content.append({"type": "text", "text": part.text})
                    elif isinstance(part, dict):
                        if 'text' in part:
                            anthropic_content.append({"type": "text", "text": part['text']})
                        elif part.get('type') == 'image':
                            # Handle image parts for vision
                            if 'source' in part:
                                anthropic_content.append(part)
                            elif 'url' in part:
                                # Convert URL to base64 if needed
                                anthropic_content.append({
                                    "type": "image",
                                    "source": {
                                        "type": "url",
                                        "url": part['url']
                                    }
                                })
                    elif isinstance(part, str):
                        anthropic_content.append({"type": "text", "text": part})
                content = anthropic_content if anthropic_content else str(content)
            
            if role == 'system':
                system_content = content if isinstance(content, str) else str(content)
            elif role in ('user', 'assistant'):
                anthropic_messages.append({
                    "role": role,
                    "content": content
                })
        
        # Call Anthropic API
        try:
            response = await client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_content if system_content else "You are a helpful assistant.",
                messages=anthropic_messages
            )
            
            # Extract response content
            response_text = ""
            if response.content:
                for block in response.content:
                    if hasattr(block, 'text'):
                        response_text += block.text
            
            # Parse JSON response if output_format is specified
            completion_value = response_text
            if output_format is not None:
                # Try to parse as JSON and convert to the expected type
                try:
                    # Find JSON in the response (may be wrapped in markdown)
                    json_text = response_text
                    if '```json' in response_text:
                        start = response_text.index('```json') + 7
                        end = response_text.index('```', start)
                        json_text = response_text[start:end].strip()
                    elif '```' in response_text:
                        start = response_text.index('```') + 3
                        end = response_text.index('```', start)
                        json_text = response_text[start:end].strip()
                    
                    # Remove any leading/trailing characters that aren't part of JSON
                    json_text = json_text.strip()
                    if json_text.startswith('{'):
                        parsed = json.loads(json_text)
                        # Create instance of output_format if it's a class
                        if hasattr(output_format, 'model_validate'):
                            completion_value = output_format.model_validate(parsed)
                        elif hasattr(output_format, 'parse_obj'):
                            completion_value = output_format.parse_obj(parsed)
                        else:
                            completion_value = parsed
                except (json.JSONDecodeError, ValueError) as e:
                    # If parsing fails, return the raw text - browser-use will handle the error
                    logger.debug(f"JSON parsing failed: {e}, returning raw text")
                    completion_value = response_text
            
            # Create browser-use compatible response with correct field names
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            usage = ChatInvokeUsage(
                prompt_tokens=input_tokens,
                prompt_cached_tokens=getattr(response.usage, 'cache_read_input_tokens', 0) or 0,
                prompt_cache_creation_tokens=getattr(response.usage, 'cache_creation_input_tokens', 0) or 0,
                prompt_image_tokens=0,  # Anthropic doesn't provide this separately
                completion_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens
            ) if ChatInvokeUsage else None
            
            if ChatInvokeCompletion:
                return ChatInvokeCompletion(
                    completion=completion_value,
                    thinking=None,
                    redacted_thinking=None,
                    usage=usage,
                    stop_reason=response.stop_reason if hasattr(response, 'stop_reason') else None
                )
            else:
                # Fallback if ChatInvokeCompletion not available
                return type('ChatResponse', (), {'content': completion_value, 'usage': usage})()
                
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise


# ==========================================
# DATA MODELS
# ==========================================

@dataclass
class ExtractedLead:
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    linkedin: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    source_url: str = ""
    extracted_at: datetime = field(default_factory=datetime.now)


@dataclass
class CompetitorData:
    name: str
    website: str
    pricing: Optional[Dict[str, Any]] = None
    features: List[str] = field(default_factory=list)
    reviews: Optional[Dict[str, Any]] = None
    social_presence: Dict[str, str] = field(default_factory=dict)
    analyzed_at: datetime = field(default_factory=datetime.now)


class ProductInfo(BaseModel):
    name: str = Field(description="Product name")
    price: Optional[str] = Field(None, description="Current price")
    original_price: Optional[str] = Field(None, description="Original/compare price")
    description: Optional[str] = Field(None, description="Product description")
    availability: Optional[str] = Field(None, description="Stock status")
    rating: Optional[float] = Field(None, description="Product rating")
    review_count: Optional[int] = Field(None, description="Number of reviews")
    images: List[str] = Field(default_factory=list, description="Product image URLs")


# ==========================================
# CUSTOM BROWSER-USE TOOLS (Anti-Bot)
# ==========================================

def create_human_behavior_tools():
    """Create custom browser-use tools for human-like behavior."""
    if BROWSER_USE_VERSION != "0.11":
        return None

    tools = Tools()

    @tools.action("Add random human-like delay between 0.5 and 3 seconds")
    async def human_delay() -> str:
        delay = random.uniform(0.5, 3.0)
        await asyncio.sleep(delay)
        return f"Waited {delay:.1f}s (human-like delay)"

    @tools.action("Scroll the page naturally like a human would")
    async def human_scroll(browser_session) -> str:
        try:
            page = await browser_session.get_current_page()
            scroll_amount = random.randint(100, 500)
            await page.evaluate(f"window.scrollBy({{top: {scroll_amount}, behavior: 'smooth'}})")
            await asyncio.sleep(random.uniform(0.3, 1.0))
            return f"Scrolled {scroll_amount}px smoothly"
        except Exception as e:
            return f"Scroll failed: {e}"

    @tools.action("Move the mouse to a random position to appear human")
    async def human_mouse_move(browser_session) -> str:
        try:
            page = await browser_session.get_current_page()
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            await page.mouse.move(x, y, steps=random.randint(5, 15))
            return f"Mouse moved to ({x}, {y})"
        except Exception as e:
            return f"Mouse move failed: {e}"

    return tools


# ==========================================
# BROWSER-USE TOOLS CLASS
# ==========================================

class BrowserUseTools(ToolBase):
    """Advanced browser automation using browser-use 0.11.x with stealth."""

    _browser_state = {
        "is_active": False,
        "current_task": None,
        "current_url": None,
        "last_screenshot": None,
        "actions": [],
        "browser_use_version": BROWSER_USE_VERSION,
    }

    @classmethod
    def get_state(cls):
        return cls._browser_state.copy()

    @classmethod
    def _update_state(cls, **kwargs):
        cls._browser_state.update(kwargs)
        if "action" in kwargs:
            cls._browser_state["actions"].append({
                "text": kwargs["action"],
                "timestamp": datetime.now().isoformat()
            })
            cls._browser_state["actions"] = cls._browser_state["actions"][-50:]

    def __init__(
        self,
        llm_provider: str = "anthropic",
        model: str = None,
        headless: bool = False,
        chrome_path: str = None,
        stealth_mode: str = "standard",
        proxy_server: str = None,
        proxy_username: str = None,
        proxy_password: str = None,
        results_dir: str = "./data/browser_use_results"
    ):
        self.llm_provider = llm_provider
        self.model = model
        self.headless = headless
        self.stealth_mode = stealth_mode
        self.proxy_server = proxy_server or os.getenv("BROWSER_PROXY_SERVER")
        self.proxy_username = proxy_username or os.getenv("BROWSER_PROXY_USERNAME")
        self.proxy_password = proxy_password or os.getenv("BROWSER_PROXY_PASSWORD")
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        self.chrome_path = chrome_path or os.getenv("CHROME_PATH")
        if not self.chrome_path and STEALTH_CONFIG_AVAILABLE:
            self.chrome_path = find_chrome_path()
        if not self.chrome_path:
            self.chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

        self._llm = None
        self._custom_tools = None

    def _get_llm(self):
        if self._llm:
            return self._llm
        
        # Check for valid API keys
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        openai_key = os.getenv("OPENAI_API_KEY", "")
        
        # Detect placeholder keys
        is_anthropic_valid = anthropic_key and not anthropic_key.startswith("your_") and len(anthropic_key) > 20
        is_openai_valid = openai_key and not openai_key.startswith("your_") and len(openai_key) > 20
        
        # Try Anthropic first if preferred and available
        if self.llm_provider == "anthropic" and is_anthropic_valid and ANTHROPIC_SDK_AVAILABLE:
            try:
                self._llm = ChatAnthropicAdapter(
                    model=self.model or "claude-sonnet-4-20250514",
                    api_key=anthropic_key
                )
                logger.info(f"Using Anthropic adapter for browser-use with model: {self._llm.model}")
                return self._llm
            except Exception as e:
                logger.warning(f"Failed to create Anthropic adapter: {e}, falling back to OpenAI")
        
        # Try OpenAI via browser-use's native support
        if is_openai_valid and BROWSER_USE_LLM_AVAILABLE:
            try:
                model_name = f"openai_{(self.model or 'gpt-4o').replace('-', '_').replace('.', '_')}"
                self._llm = get_llm_by_name(model_name)
                logger.info(f"Using OpenAI via browser-use with model: {model_name}")
                return self._llm
            except Exception as e:
                logger.warning(f"Failed to create OpenAI LLM via browser-use: {e}")
        
        # Last resort: try Anthropic even if llm_provider wasn't set to it
        if is_anthropic_valid and ANTHROPIC_SDK_AVAILABLE:
            try:
                self._llm = ChatAnthropicAdapter(
                    model="claude-sonnet-4-20250514",
                    api_key=anthropic_key
                )
                logger.info("Using Anthropic adapter as fallback for browser-use")
                return self._llm
            except Exception as e:
                logger.error(f"Failed to create Anthropic adapter as fallback: {e}")
        
        # No valid LLM available
        raise RuntimeError(
            "No valid LLM API key found. browser-use requires either:\n"
            "  - ANTHROPIC_API_KEY (for Claude)\n"
            "  - OPENAI_API_KEY (for GPT-4)\n"
            "Please set a valid API key in your .env file."
        )

    def _create_browser_profile(self, mode: str = None):
        effective_mode = mode or self.stealth_mode
        if STEALTH_CONFIG_AVAILABLE:
            return create_stealth_profile(
                mode=effective_mode, headless=self.headless, use_real_chrome=True,
                proxy_server=self.proxy_server, proxy_username=self.proxy_username,
                proxy_password=self.proxy_password,
            )
        profile_kwargs = {"headless": self.headless}
        if BROWSER_USE_VERSION == "0.11":
            profile_kwargs["enable_default_extensions"] = True
            profile_kwargs["minimum_wait_page_load_time"] = 0.5
            profile_kwargs["wait_between_actions"] = 0.3
            if self.chrome_path and Path(self.chrome_path).exists():
                profile_kwargs["executable_path"] = self.chrome_path
            if self.proxy_server:
                pk = {"server": self.proxy_server}
                if self.proxy_username: pk["username"] = self.proxy_username
                if self.proxy_password: pk["password"] = self.proxy_password
                profile_kwargs["proxy"] = ProxySettings(**pk)
            downloads_dir = Path("./data/browser_downloads")
            downloads_dir.mkdir(parents=True, exist_ok=True)
            profile_kwargs["downloads_path"] = str(downloads_dir)
            return BrowserProfile(**profile_kwargs)
        else:
            if self.chrome_path and not self.headless:
                profile_kwargs["chrome_instance_path"] = self.chrome_path
            return BrowserProfile(**profile_kwargs)

    def _get_custom_tools(self):
        if self._custom_tools is None and BROWSER_USE_VERSION == "0.11":
            self._custom_tools = create_human_behavior_tools()
        return self._custom_tools

    async def _ensure_browser(self):
        if not BROWSER_USE_AVAILABLE:
            raise RuntimeError("browser-use not installed. Run: pip install browser-use")

    async def _run_agent(self, task, max_steps=25, stealth_mode=None, use_vision=True, sensitive_data=None):
        """Run a browser-use agent with a task."""
        await self._ensure_browser()
        self._update_state(is_active=True, current_task=task[:100], action=f"Starting: {task[:80]}...")

        llm = self._get_llm()
        profile = self._create_browser_profile(mode=stealth_mode)

        if BROWSER_USE_VERSION == "0.11":
            browser = Browser(browser_profile=profile)
            agent_kwargs = {
                "task": task, "llm": llm, "browser": browser,
                "max_actions_per_step": 3, "use_vision": use_vision,
            }
            custom_tools = self._get_custom_tools()
            if custom_tools:
                agent_kwargs["tools"] = custom_tools
            if sensitive_data:
                agent_kwargs["sensitive_data"] = sensitive_data
            agent = Agent(**agent_kwargs)
        else:
            browser = Browser(config=profile)
            agent = Agent(task=task, llm=llm, browser=browser, max_actions_per_step=5)

        try:
            self._update_state(action="Browser launched, executing task...")
            if BROWSER_USE_VERSION == "0.11":
                history = await agent.run()
                if hasattr(history, 'final_result'):
                    final = history.final_result
                    if callable(final): final = final()
                    if final: return str(final)
                if hasattr(history, 'history') and history.history:
                    for entry in reversed(history.history):
                        if hasattr(entry, 'result') and entry.result:
                            if hasattr(entry.result, 'extracted_content') and entry.result.extracted_content:
                                return str(entry.result.extracted_content)
                return str(history)
            else:
                result = await agent.run(max_steps=max_steps)
                if hasattr(result, 'final_result'):
                    final = result.final_result
                    if callable(final): final = final()
                    if final: return str(final)
                if hasattr(result, 'all_results') and result.all_results:
                    for r in reversed(result.all_results):
                        if hasattr(r, 'extracted_content') and r.extracted_content:
                            return str(r.extracted_content)
                if hasattr(result, 'history') and result.history:
                    return str(result.history[-1])
                return str(result)
        except Exception as e:
            self._update_state(action=f"Error: {str(e)[:100]}")
            logger.error(f"Agent execution failed: {e}")
            raise
        finally:
            try: await browser.close()
            except Exception: pass
            self._update_state(is_active=False, current_task=None)

    # ==========================================
    # SOCIAL MEDIA TOOLS
    # ==========================================

    @tool(
        name="browser_social_media_action",
        description="Perform a social media action (post, like, follow, scrape) with anti-bot stealth. Supports Twitter/X, Instagram, TikTok, Facebook, LinkedIn, Pinterest, Reddit, YouTube, Threads.",
        category="browser_use"
    )
    async def social_media_action(self, platform: str, action: str, content: str = None,
                                   target_url: str = None, image_path: str = None,
                                   video_path: str = None, hashtags: List[str] = None) -> Dict[str, Any]:
        """Perform a social media action with full anti-bot stealth."""
        platform_lower = platform.lower().replace("/", "").replace(" ", "")
        if platform_lower in ("x", "twitterx"): platform_lower = "twitter"

        platform_urls = {
            "twitter": "https://twitter.com", "instagram": "https://www.instagram.com",
            "tiktok": "https://www.tiktok.com", "facebook": "https://www.facebook.com",
            "linkedin": "https://www.linkedin.com", "pinterest": "https://www.pinterest.com",
            "reddit": "https://www.reddit.com", "youtube": "https://www.youtube.com",
            "threads": "https://www.threads.net",
        }
        base_url = target_url or platform_urls.get(platform_lower, "")

        hashtag_text = " ".join(f"#{h}" for h in (hashtags or []))
        media_instruction = ""
        if image_path:
            media_instruction = f'\nUpload this image: "{str(Path(image_path).absolute())}"'
        elif video_path:
            media_instruction = f'\nUpload this video: "{str(Path(video_path).absolute())}"'

        task = f"""SOCIAL MEDIA TASK on {platform.upper()}:
Action: {action}
URL: {base_url}

STEALTH INSTRUCTIONS:
- You should already be logged in via Chrome profile. If not, report it.
- Act naturally - scroll, pause, read content before performing actions.
- Use the human_delay action between operations.
- If you encounter CAPTCHA: wait 5 seconds, try to solve, or report.
- If rate limited or blocked, stop and report.

{"Content: " + content if content else ""}
{hashtag_text}
{media_instruction}

Steps: Navigate to {base_url}, add human delay, perform {action}, verify success, report result."""

        try:
            result = await self._run_agent(task, max_steps=30, stealth_mode="social", use_vision=True)
            return {"success": True, "platform": platform_lower, "action": action,
                    "result": str(result)[:2000], "stealth_mode": "social"}
        except Exception as e:
            return {"success": False, "platform": platform_lower, "action": action,
                    "error": str(e), "hint": "Ensure Chrome is logged in to the platform first."}

    @tool(
        name="browser_scrape_social_profiles",
        description="Scrape social media profiles, posts, and engagement data with anti-bot stealth",
        category="browser_use"
    )
    async def scrape_social_profiles(self, platform: str, search_query: str = None,
                                      profile_urls: List[str] = None, max_profiles: int = 10) -> Dict[str, Any]:
        """Scrape social media profiles with bot-bypass stealth."""
        urls_text = ""
        if profile_urls:
            urls_text = "Visit these profiles:\n" + "\n".join(f"- {u}" for u in profile_urls)
        search_text = f"Search for: {search_query}" if search_query else ""

        task = f"""STEALTH SOCIAL SCRAPING on {platform.upper()}:
{urls_text}
{search_text}

STEALTH: Act like a human, use human_delay between profiles, stop if blocked.

Extract up to {max_profiles} profiles with: username, display name, bio, followers,
following, post count, engagement rate, recent posts (3-5), profile URL.
Return as JSON array."""

        try:
            result = await self._run_agent(task, max_steps=40, stealth_mode="social")
            profiles = []
            try:
                import re
                if isinstance(result, str):
                    m = re.search(r'\[[\s\S]*\]', result)
                    if m: profiles = json.loads(m.group())
            except json.JSONDecodeError: pass

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.results_dir / f"social_{platform}_{timestamp}.json"
            with open(filepath, "w") as f:
                json.dump({"platform": platform, "search_query": search_query,
                           "profiles": profiles, "raw_result": str(result)[:3000],
                           "scraped_at": timestamp}, f, indent=2)
            return {"success": True, "platform": platform, "profiles_found": len(profiles),
                    "profiles": profiles[:10], "saved_to": str(filepath)}
        except Exception as e:
            return {"success": False, "platform": platform, "error": str(e)}

    # ==========================================
    # LEAD GENERATION
    # ==========================================

    @tool(name="browser_extract_leads",
          description="Extract contact information and leads from a webpage using AI browser automation",
          category="browser_use")
    async def extract_leads(self, url: str, criteria: str = None, max_leads: int = 20) -> Dict[str, Any]:
        criteria_text = f"Focus on: {criteria}" if criteria else ""
        task = f"""Visit {url} and extract up to {max_leads} contacts.
{criteria_text}
For each: name, email, phone, title, company, LinkedIn URL, location.
Navigate team/about pages. Return as JSON array."""
        try:
            result = await self._run_agent(task, max_steps=30)
            leads = []
            try:
                import re
                if isinstance(result, str):
                    m = re.search(r'\[[\s\S]*\]', result)
                    if m: leads = json.loads(m.group())
            except json.JSONDecodeError: pass
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.results_dir / f"leads_{timestamp}.json"
            with open(filepath, "w") as f:
                json.dump({"source_url": url, "criteria": criteria, "leads": leads,
                           "raw_result": str(result)[:2000], "extracted_at": timestamp}, f, indent=2)
            return {"success": True, "url": url, "leads_found": len(leads),
                    "leads": leads, "saved_to": str(filepath)}
        except Exception as e:
            return {"success": False, "url": url, "error": str(e)}

    @tool(name="browser_scrape_directory",
          description="Scrape business listings from a directory website",
          category="browser_use")
    async def scrape_directory(self, url: str, category: str = None,
                               location: str = None, max_listings: int = 50) -> Dict[str, Any]:
        search_params = []
        if category: search_params.append(f"search for '{category}'")
        if location: search_params.append(f"in '{location}'")
        search_text = " and ".join(search_params) if search_params else ""
        task = f"""Go to {url}{' and ' + search_text if search_text else ''}.
Extract up to {max_listings} listings: name, address, phone, website, rating, reviews, category, description.
Scroll through results. Return as JSON array."""
        try:
            result = await self._run_agent(task, max_steps=40, stealth_mode="scraping")
            listings = []
            try:
                import re
                if isinstance(result, str):
                    m = re.search(r'\[[\s\S]*\]', result)
                    if m: listings = json.loads(m.group())
            except json.JSONDecodeError: pass
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.results_dir / f"directory_{timestamp}.json"
            with open(filepath, "w") as f:
                json.dump({"source_url": url, "category": category, "location": location,
                           "listings": listings, "scraped_at": timestamp}, f, indent=2)
            return {"success": True, "url": url, "listings_found": len(listings),
                    "listings": listings[:10], "all_listings_saved_to": str(filepath)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================
    # FORM AUTOMATION
    # ==========================================

    @tool(name="browser_fill_form",
          description="Fill out and submit a form on a website using AI",
          category="browser_use")
    async def fill_form(self, url: str, form_data: Dict[str, str], submit: bool = True) -> Dict[str, Any]:
        fields_text = "\n".join([f"- {k}: {v}" for k, v in form_data.items()])
        task = f"""Go to {url} and fill the form:
{fields_text}
{"Submit after filling." if submit else "Do not submit."}"""
        try:
            result = await self._run_agent(task, max_steps=20)
            return {"success": True, "url": url, "fields_filled": list(form_data.keys()),
                    "submitted": submit, "result": str(result)[:500]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @tool(name="browser_submit_contact_form",
          description="Submit a contact form on a business website",
          category="browser_use")
    async def submit_contact_form(self, website_url: str, name: str, email: str,
                                   message: str, phone: str = None, company: str = None,
                                   subject: str = None) -> Dict[str, Any]:
        form_data = {"Name": name, "Email": email, "Message": message}
        if phone: form_data["Phone"] = phone
        if company: form_data["Company"] = company
        if subject: form_data["Subject"] = subject
        fields_text = "\n".join([f"- {k}: {v}" for k, v in form_data.items()])
        sensitive = {"email": email}
        if phone: sensitive["phone"] = phone
        task = f"""Go to {website_url}, find contact form.
Fill: {fields_text}
Submit and confirm success."""
        try:
            result = await self._run_agent(task, max_steps=25,
                sensitive_data=sensitive if BROWSER_USE_VERSION == "0.11" else None)
            return {"success": True, "website": website_url, "submitted_to": email,
                    "confirmation": str(result)[:300]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================
    # COMPETITIVE INTELLIGENCE
    # ==========================================

    @tool(name="browser_analyze_competitor",
          description="Analyze a competitor website for pricing, features, and positioning",
          category="browser_use")
    async def analyze_competitor(self, competitor_url: str, analyze_pricing: bool = True,
                                  analyze_features: bool = True, check_reviews: bool = True) -> Dict[str, Any]:
        tasks = []
        if analyze_pricing: tasks.append("pricing")
        if analyze_features: tasks.append("features")
        if check_reviews: tasks.append("reviews/testimonials")
        task = f"""Analyze {competitor_url}: company info, {', '.join(tasks)},
social links, differentiators, target market. Return as JSON."""
        try:
            result = await self._run_agent(task, max_steps=35, stealth_mode="scraping")
            analysis = {}
            try:
                import re
                if isinstance(result, str):
                    m = re.search(r'\{{[\s\S]*\}}', result)
                    if m: analysis = json.loads(m.group())
            except json.JSONDecodeError:
                analysis = {"raw_analysis": str(result)[:2000]}
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.results_dir / f"competitor_{timestamp}.json"
            with open(filepath, "w") as f:
                json.dump({"competitor_url": competitor_url, "analysis": analysis,
                           "analyzed_at": timestamp}, f, indent=2)
            return {"success": True, "competitor": competitor_url,
                    "analysis": analysis, "saved_to": str(filepath)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @tool(name="browser_monitor_price",
          description="Monitor a product page for price changes",
          category="browser_use")
    async def monitor_price(self, product_url: str, save_history: bool = True) -> Dict[str, Any]:
        task = f"Visit {product_url}, extract: product name, current price, original price, stock, discounts. Return JSON."
        try:
            result = await self._run_agent(task, max_steps=15, stealth_mode="scraping")
            price_data = {}
            try:
                import re
                if isinstance(result, str):
                    m = re.search(r'\{{[\s\S]*\}}', result)
                    if m: price_data = json.loads(m.group())
            except json.JSONDecodeError:
                price_data = {"raw_result": str(result)[:500]}
            price_data["url"] = product_url
            price_data["checked_at"] = datetime.now().isoformat()
            if save_history:
                with open(self.results_dir / "price_history.jsonl", "a") as f:
                    f.write(json.dumps(price_data) + "\n")
            return {"success": True, "product_url": product_url, "price_data": price_data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================
    # INFLUENCER DISCOVERY
    # ==========================================

    @tool(name="browser_find_influencers",
          description="Find influencers in a niche on social platforms with stealth",
          category="browser_use")
    async def find_influencers(self, platform: str = "instagram", niche: str = "lifestyle",
                                min_followers: int = 1000, max_results: int = 20) -> Dict[str, Any]:
        """
        Find influencers with improved authentication and extraction.
        Uses credentials from .env for legitimate platform access.
        """
        platform_lower = platform.lower()
        
        # Get login credentials from environment
        credentials = {}
        if platform_lower == "instagram":
            credentials["username"] = os.getenv("INSTAGRAM_USERNAME")
            credentials["password"] = os.getenv("INSTAGRAM_PASSWORD")
        elif platform_lower == "tiktok":
            credentials["email"] = os.getenv("TIKTOK_EMAIL")
            credentials["password"] = os.getenv("TIKTOK_PASSWORD")
        elif platform_lower == "twitter":
            credentials["username"] = os.getenv("TWITTER_USERNAME")
            credentials["password"] = os.getenv("TWITTER_PASSWORD")
        
        # Platform-specific search strategies
        if platform_lower == "instagram":
            # Use the search page, not hashtag explore
            search_url = f"https://www.instagram.com/"
            task = f"""INSTAGRAM INFLUENCER SEARCH for {niche} creators:

1. Go to {search_url}
2. If you see a login page:
   - Enter username: {credentials.get('username', 'NOT_SET')}
   - Enter password: {credentials.get('password', 'NOT_SET')}
   - Click login
   - Wait for homepage to load
3. Click the search icon (magnifying glass)
4. Type "{niche}" in the search box
5. Click the "Accounts" tab to see creators
6. Scroll through at least {max_results} creator profiles
7. For each creator, click into their profile and extract:
   - username (handle without @)
   - display name
   - follower count (convert K/M to numbers)
   - bio/description
   - profile URL
   - approximate engagement rate (if visible)
8. Return ONLY a valid JSON array like this:
[{{"username": "fitgirl", "name": "Fitness Girl", "followers": 50000, "bio": "...", "url": "https://instagram.com/fitgirl"}}, ...]

Important: Extract REAL data, don't make up numbers. Return empty array [] if login fails."""
        
        elif platform_lower == "tiktok":
            task = f"""TIKTOK INFLUENCER SEARCH for {niche}:
1. Go to https://www.tiktok.com/search/user?q={niche.replace(' ', '%20')}
2. Scroll through search results
3. For each creator with {min_followers}+ followers:
   - Click profile
   - Extract: username, name, followers, likes, bio, URL
   - Go back to search
4. Return JSON array of {max_results} creators"""
        
        elif platform_lower == "twitter":
            task = f"""TWITTER/X INFLUENCER SEARCH for {niche}:
1. Go to https://twitter.com/search?q={niche.replace(' ', '%20')}&f=user
2. Click "People" tab
3. Extract {max_results} accounts with {min_followers}+ followers
4. Return JSON array with: username, name, followers, bio, url"""
        
        elif platform_lower == "youtube":
            task = f"""YOUTUBE CREATOR SEARCH for {niche}:
1. Go to https://www.youtube.com/results?search_query={niche.replace(' ', '+')}
2. Filter by "Channels"
3. Extract {max_results} channels with {min_followers}+ subscribers
4. Return JSON array with: name, subscribers, description, url"""
        
        else:
            return {
                "success": False,
                "error": f"Platform '{platform}' not supported. Use: instagram, tiktok, twitter, or youtube"
            }
        
        logger.info(f"🔍 Starting influencer search: {platform} / {niche} / {max_results} results")
        
        try:
            result = await self._run_agent(task, max_steps=50, stealth_mode="social", use_vision=True)
            logger.info(f"Raw result from agent: {result[:500]}")
            
            influencers = []
            
            # Try multiple parsing strategies
            try:
                import re
                
                # Strategy 1: Find JSON array in result
                if isinstance(result, str):
                    # Look for JSON array
                    json_match = re.search(r'\[\s*\{[\s\S]*\}\s*\]', result)
                    if json_match:
                        try:
                            influencers = json.loads(json_match.group())
                            logger.info(f"✅ Parsed {len(influencers)} influencers from JSON")
                        except json.JSONDecodeError as e:
                            logger.warning(f"JSON parse failed: {e}")
                    
                    # Strategy 2: If no JSON found, try to extract from text
                    if not influencers:
                        logger.warning("No JSON array found, attempting text extraction...")
                        # Look for username patterns
                        usernames = re.findall(r'@?([a-zA-Z0-9_\.]+)', result)
                        if usernames:
                            # Build basic profile list
                            influencers = [{"username": u, "platform": platform} for u in usernames[:max_results]]
                            logger.info(f"📝 Extracted {len(influencers)} usernames from text")
            
            except Exception as parse_error:
                logger.error(f"Parsing error: {parse_error}")
            
            # Filter out invalid entries
            influencers = [inf for inf in influencers if isinstance(inf, dict) and inf.get("username")]
            
            return {
                "success": len(influencers) > 0,
                "platform": platform,
                "niche": niche,
                "influencers_found": len(influencers),
                "influencers": influencers[:max_results],
                "raw_result_preview": result[:300] if isinstance(result, str) else str(result)[:300],
                "note": "Login credentials used from .env" if credentials.get("username") or credentials.get("email") else "No credentials found"
            }
        
        except Exception as e:
            logger.error(f"Influencer search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "platform": platform,
                "niche": niche,
                "note": "Check browser-use logs for details"
            }

    # ==========================================
    # DATA EXTRACTION & GENERAL
    # ==========================================

    @tool(name="browser_extract_data",
          description="Extract structured data from any webpage using AI",
          category="browser_use")
    async def extract_data(self, url: str, data_description: str = "structured data, text content, links, and relevant information",
                            output_format: str = "json") -> Dict[str, Any]:
        task = f"Visit {url} and extract: {data_description}. Return in {output_format} format. Scroll if needed."
        try:
            result = await self._run_agent(task, max_steps=25, stealth_mode="scraping")
            extracted = result
            if output_format == "json":
                try:
                    import re
                    if isinstance(result, str):
                        m = re.search(r'[\[\{{][\s\S]*[\]\}}]', result)
                        if m: extracted = json.loads(m.group())
                except json.JSONDecodeError: pass
            return {"success": True, "url": url, "data_type": data_description, "extracted_data": extracted}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @tool(name="browser_take_screenshot",
          description="Navigate to a URL and take a screenshot",
          category="browser_use")
    async def take_screenshot(self, url: str, full_page: bool = False) -> Dict[str, Any]:
        task = f"Navigate to {url} and take a screenshot.{' Full page.' if full_page else ''}"
        try:
            result = await self._run_agent(task, max_steps=10)
            return {"success": True, "url": url, "result": str(result)[:200]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @tool(name="browser_automate_task",
          description="Perform any custom browser automation task. Supports stealth mode for anti-bot bypass.",
          category="browser_use")
    async def automate_task(self, task_description: str, starting_url: str = None,
                             max_steps: int = 30, stealth_mode: str = "standard") -> Dict[str, Any]:
        full_task = task_description
        if starting_url:
            full_task = f"Start at {starting_url}. Then: {task_description}"
        try:
            result = await self._run_agent(full_task, max_steps=max_steps, stealth_mode=stealth_mode)
            return {"success": True, "task": task_description, "starting_url": starting_url,
                    "stealth_mode": stealth_mode, "result": str(result)[:2000]}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ==========================================
# FACTORY
# ==========================================

def create_browser_use_tools(llm_provider=None, headless=False, chrome_path=None,
                              stealth_mode="standard", proxy_server=None):
    provider = llm_provider or os.getenv("BROWSER_USE_LLM_PROVIDER", "anthropic")
    return BrowserUseTools(llm_provider=provider, headless=headless,
                           chrome_path=chrome_path, stealth_mode=stealth_mode,
                           proxy_server=proxy_server)

# Backwards compat alias
BrowserUseAdvanced = BrowserUseTools
