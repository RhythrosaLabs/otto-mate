"""
Advanced Browser-Use Integration
================================

Properly integrates the browser-use library for:
- Lead generation and extraction
- Form automation
- Website monitoring
- E-commerce intelligence
- Competitive analysis
- Social media scraping
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from .core import tool, ToolBase

logger = logging.getLogger(__name__)

# Try to import browser-use and LLM providers
try:
    from browser_use import Agent, Browser, BrowserConfig
    BROWSER_USE_AVAILABLE = True
except ImportError:
    BROWSER_USE_AVAILABLE = False
    logger.warning("browser-use not installed. Run: pip install browser-use")

try:
    from langchain_anthropic import ChatAnthropic
    from langchain_openai import ChatOpenAI
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


# ==========================================
# DATA MODELS
# ==========================================

@dataclass
class ExtractedLead:
    """Lead extraction result"""
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
    """Competitor analysis data"""
    name: str
    website: str
    pricing: Optional[Dict[str, Any]] = None
    features: List[str] = field(default_factory=list)
    reviews: Optional[Dict[str, Any]] = None
    social_presence: Dict[str, str] = field(default_factory=dict)
    analyzed_at: datetime = field(default_factory=datetime.now)


@dataclass
class WebMonitorResult:
    """Website monitoring result"""
    url: str
    check_type: str
    current_value: Any
    previous_value: Optional[Any] = None
    changed: bool = False
    change_details: Optional[str] = None
    checked_at: datetime = field(default_factory=datetime.now)


class ProductInfo(BaseModel):
    """Product information extraction model"""
    name: str = Field(description="Product name")
    price: Optional[str] = Field(None, description="Current price")
    original_price: Optional[str] = Field(None, description="Original/compare price")
    description: Optional[str] = Field(None, description="Product description")
    availability: Optional[str] = Field(None, description="Stock status")
    rating: Optional[float] = Field(None, description="Product rating")
    review_count: Optional[int] = Field(None, description="Number of reviews")
    images: List[str] = Field(default_factory=list, description="Product image URLs")


class ContactForm(BaseModel):
    """Contact form fields"""
    name: str = Field(description="Full name")
    email: str = Field(description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    company: Optional[str] = Field(None, description="Company name")
    message: str = Field(description="Message content")
    subject: Optional[str] = Field(None, description="Message subject")


# ==========================================
# BROWSER-USE TOOLS CLASS
# ==========================================

class BrowserUseTools(ToolBase):
    """Advanced browser automation using browser-use library."""
    
    def __init__(
        self,
        llm_provider: str = "anthropic",
        model: str = None,
        headless: bool = True,
        results_dir: str = "./data/browser_use_results"
    ):
        self.llm_provider = llm_provider
        self.model = model
        self.headless = headless
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        self._llm = None
        self._browser = None
    
    def _get_llm(self):
        """Get LLM instance based on provider."""
        if self._llm:
            return self._llm
        
        if not LANGCHAIN_AVAILABLE:
            raise RuntimeError("langchain-anthropic or langchain-openai not installed")
        
        if self.llm_provider == "anthropic":
            self._llm = ChatAnthropic(
                model=self.model or "claude-sonnet-4-20250514",
                timeout=120,
                stop=None
            )
        elif self.llm_provider == "openai":
            self._llm = ChatOpenAI(
                model=self.model or "gpt-4o",
                timeout=120
            )
        else:
            # Default to Anthropic
            self._llm = ChatAnthropic(
                model="claude-sonnet-4-20250514",
                timeout=120
            )
        
        return self._llm
    
    async def _ensure_browser(self):
        """Ensure browser is available."""
        if not BROWSER_USE_AVAILABLE:
            raise RuntimeError(
                "browser-use not installed. Run: pip install browser-use"
            )
    
    async def _run_agent(self, task: str, max_steps: int = 25) -> str:
        """Run a browser-use agent with a task."""
        await self._ensure_browser()
        
        llm = self._get_llm()
        
        # Create browser config
        browser_config = BrowserConfig(headless=self.headless)
        
        agent = Agent(
            task=task,
            llm=llm,
            browser_config=browser_config,
            max_actions_per_step=5
        )
        
        try:
            result = await agent.run(max_steps=max_steps)
            
            # Extract final result
            if hasattr(result, 'final_result'):
                return result.final_result
            elif hasattr(result, 'history'):
                # Get last action result
                if result.history:
                    return str(result.history[-1])
            return str(result)
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            raise

    # ==========================================
    # LEAD GENERATION
    # ==========================================
    
    @tool(
        name="browser_extract_leads",
        description="Extract contact information and leads from a webpage using AI",
        category="browser_use"
    )
    async def extract_leads(
        self,
        url: str,
        criteria: str = None,
        max_leads: int = 20
    ) -> Dict[str, Any]:
        """
        Extract leads/contacts from a webpage.
        
        Args:
            url: URL to extract leads from
            criteria: Optional criteria (e.g., "CEOs", "marketing managers")
            max_leads: Maximum number of leads to extract
        """
        criteria_text = f"Focus on finding: {criteria}" if criteria else ""
        
        task = f"""
        Visit {url} and extract contact information for up to {max_leads} people.
        {criteria_text}
        
        For each contact, try to find:
        - Full name
        - Email address
        - Phone number
        - Job title
        - Company name
        - LinkedIn profile URL
        - Location
        
        Navigate through the page, check team/about pages, and look for contact sections.
        Return the data as a JSON array of contacts.
        """
        
        try:
            result = await self._run_agent(task, max_steps=30)
            
            # Try to parse JSON from result
            leads = []
            try:
                if isinstance(result, str):
                    # Try to find JSON in the result
                    import re
                    json_match = re.search(r'\[[\s\S]*\]', result)
                    if json_match:
                        leads = json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.results_dir / f"leads_{timestamp}.json"
            with open(filepath, "w") as f:
                json.dump({
                    "source_url": url,
                    "criteria": criteria,
                    "leads": leads,
                    "raw_result": str(result)[:2000],
                    "extracted_at": timestamp
                }, f, indent=2)
            
            return {
                "success": True,
                "url": url,
                "leads_found": len(leads),
                "leads": leads,
                "saved_to": str(filepath)
            }
            
        except Exception as e:
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }
    
    @tool(
        name="browser_scrape_directory",
        description="Scrape business listings from a directory website",
        category="browser_use"
    )
    async def scrape_directory(
        self,
        url: str,
        category: str = None,
        location: str = None,
        max_listings: int = 50
    ) -> Dict[str, Any]:
        """
        Scrape business listings from a directory.
        
        Args:
            url: Directory URL (Yelp, Google Maps, Yellow Pages, etc.)
            category: Business category to search
            location: Location to filter by
            max_listings: Maximum listings to extract
        """
        search_params = []
        if category:
            search_params.append(f"search for '{category}'")
        if location:
            search_params.append(f"in '{location}'")
        
        search_text = " and ".join(search_params) if search_params else ""
        
        task = f"""
        Go to {url}{' and ' + search_text if search_text else ''}.
        
        Extract up to {max_listings} business listings with:
        - Business name
        - Address
        - Phone number
        - Website
        - Rating
        - Number of reviews
        - Category/type
        - Description (if available)
        
        Scroll through results and extract data. Return as JSON array.
        """
        
        try:
            result = await self._run_agent(task, max_steps=40)
            
            listings = []
            try:
                if isinstance(result, str):
                    import re
                    json_match = re.search(r'\[[\s\S]*\]', result)
                    if json_match:
                        listings = json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.results_dir / f"directory_{timestamp}.json"
            with open(filepath, "w") as f:
                json.dump({
                    "source_url": url,
                    "category": category,
                    "location": location,
                    "listings": listings,
                    "scraped_at": timestamp
                }, f, indent=2)
            
            return {
                "success": True,
                "url": url,
                "listings_found": len(listings),
                "listings": listings[:10],  # Return first 10 in response
                "all_listings_saved_to": str(filepath)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================
    # FORM AUTOMATION
    # ==========================================
    
    @tool(
        name="browser_fill_form",
        description="Fill out and submit a form on a website",
        category="browser_use"
    )
    async def fill_form(
        self,
        url: str,
        form_data: Dict[str, str],
        submit: bool = True
    ) -> Dict[str, Any]:
        """
        Fill out a form with provided data.
        
        Args:
            url: URL of the page with the form
            form_data: Dict of field names/labels to values
            submit: Whether to submit the form
        """
        fields_text = "\n".join([f"- {k}: {v}" for k, v in form_data.items()])
        
        task = f"""
        Go to {url} and fill out the form with this data:
        {fields_text}
        
        Find each field by its label or placeholder text and enter the value.
        {"After filling all fields, click the submit button." if submit else "Do not submit the form."}
        
        Report whether the form was successfully filled and submitted.
        """
        
        try:
            result = await self._run_agent(task, max_steps=20)
            
            return {
                "success": True,
                "url": url,
                "fields_filled": list(form_data.keys()),
                "submitted": submit,
                "result": str(result)[:500]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="browser_submit_contact_form",
        description="Submit a contact/inquiry form on a business website",
        category="browser_use"
    )
    async def submit_contact_form(
        self,
        website_url: str,
        name: str,
        email: str,
        message: str,
        phone: str = None,
        company: str = None,
        subject: str = None
    ) -> Dict[str, Any]:
        """
        Find and submit a contact form on a website.
        
        Args:
            website_url: Business website URL
            name: Your name
            email: Your email
            message: Message to send
            phone: Phone number (optional)
            company: Company name (optional)
            subject: Message subject (optional)
        """
        form_data = {
            "Name": name,
            "Email": email,
            "Message": message
        }
        if phone:
            form_data["Phone"] = phone
        if company:
            form_data["Company"] = company
        if subject:
            form_data["Subject"] = subject
        
        fields_text = "\n".join([f"- {k}: {v}" for k, v in form_data.items()])
        
        task = f"""
        Go to {website_url} and find the contact form. 
        It might be on the homepage, /contact page, or similar.
        
        Fill out the form with:
        {fields_text}
        
        Submit the form and confirm it was successful.
        Look for confirmation messages like "Thank you" or "Message sent".
        """
        
        try:
            result = await self._run_agent(task, max_steps=25)
            
            return {
                "success": True,
                "website": website_url,
                "submitted_to": email,
                "message_sent": message[:100] + "..." if len(message) > 100 else message,
                "confirmation": str(result)[:300]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================
    # COMPETITIVE INTELLIGENCE
    # ==========================================
    
    @tool(
        name="browser_analyze_competitor",
        description="Analyze a competitor's website for pricing, features, and positioning",
        category="browser_use"
    )
    async def analyze_competitor(
        self,
        competitor_url: str,
        analyze_pricing: bool = True,
        analyze_features: bool = True,
        check_reviews: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive competitor analysis.
        
        Args:
            competitor_url: Competitor's website URL
            analyze_pricing: Extract pricing information
            analyze_features: List product features
            check_reviews: Look for reviews/testimonials
        """
        analysis_tasks = []
        if analyze_pricing:
            analysis_tasks.append("pricing plans and costs")
        if analyze_features:
            analysis_tasks.append("product features and capabilities")
        if check_reviews:
            analysis_tasks.append("customer reviews, testimonials, and ratings")
        
        task = f"""
        Analyze the competitor website at {competitor_url}.
        
        Extract the following information:
        - Company name and description
        - {', '.join(analysis_tasks)}
        - Social media links (LinkedIn, Twitter, Facebook, etc.)
        - Key differentiators or unique selling points
        - Target audience/market
        
        Navigate through the site including pricing, features, about, and reviews pages.
        Return structured analysis as JSON.
        """
        
        try:
            result = await self._run_agent(task, max_steps=35)
            
            # Try to parse structured data
            analysis = {}
            try:
                if isinstance(result, str):
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', result)
                    if json_match:
                        analysis = json.loads(json_match.group())
            except json.JSONDecodeError:
                analysis = {"raw_analysis": str(result)[:2000]}
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.results_dir / f"competitor_{timestamp}.json"
            with open(filepath, "w") as f:
                json.dump({
                    "competitor_url": competitor_url,
                    "analysis": analysis,
                    "analyzed_at": timestamp
                }, f, indent=2)
            
            return {
                "success": True,
                "competitor": competitor_url,
                "analysis": analysis,
                "saved_to": str(filepath)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="browser_monitor_price",
        description="Monitor a product page for price changes",
        category="browser_use"
    )
    async def monitor_price(
        self,
        product_url: str,
        save_history: bool = True
    ) -> Dict[str, Any]:
        """
        Check and record current price for a product.
        
        Args:
            product_url: Product page URL
            save_history: Save to price history file
        """
        task = f"""
        Visit {product_url} and extract:
        - Product name
        - Current price
        - Original/compare-at price (if on sale)
        - Stock availability
        - Any current discounts or promotions
        
        Return as JSON object.
        """
        
        try:
            result = await self._run_agent(task, max_steps=15)
            
            price_data = {}
            try:
                if isinstance(result, str):
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', result)
                    if json_match:
                        price_data = json.loads(json_match.group())
            except json.JSONDecodeError:
                price_data = {"raw_result": str(result)[:500]}
            
            price_data["url"] = product_url
            price_data["checked_at"] = datetime.now().isoformat()
            
            if save_history:
                # Append to history file
                history_file = self.results_dir / "price_history.jsonl"
                with open(history_file, "a") as f:
                    f.write(json.dumps(price_data) + "\n")
            
            return {
                "success": True,
                "product_url": product_url,
                "price_data": price_data
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================
    # SOCIAL MEDIA
    # ==========================================
    
    @tool(
        name="browser_find_influencers",
        description="Find influencers in a specific niche on social platforms",
        category="browser_use"
    )
    async def find_influencers(
        self,
        platform: str,
        niche: str,
        min_followers: int = 1000,
        max_results: int = 20
    ) -> Dict[str, Any]:
        """
        Find influencers in a niche.
        
        Args:
            platform: Social platform (instagram, tiktok, twitter, youtube)
            niche: Content niche/category
            min_followers: Minimum follower count
            max_results: Max influencers to find
        """
        platform_urls = {
            "instagram": f"https://www.instagram.com/explore/tags/{niche.replace(' ', '')}",
            "tiktok": f"https://www.tiktok.com/search?q={niche}",
            "twitter": f"https://twitter.com/search?q={niche}",
            "youtube": f"https://www.youtube.com/results?search_query={niche}"
        }
        
        url = platform_urls.get(platform.lower(), platform_urls["instagram"])
        
        task = f"""
        Go to {url} and find up to {max_results} content creators/influencers 
        in the {niche} niche with at least {min_followers} followers.
        
        For each influencer, extract:
        - Username/handle
        - Full name (if visible)
        - Follower count
        - Recent engagement metrics
        - Bio/description
        - Content style/type
        
        Return as JSON array of influencers.
        """
        
        try:
            result = await self._run_agent(task, max_steps=30)
            
            influencers = []
            try:
                if isinstance(result, str):
                    import re
                    json_match = re.search(r'\[[\s\S]*\]', result)
                    if json_match:
                        influencers = json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
            
            return {
                "success": True,
                "platform": platform,
                "niche": niche,
                "influencers_found": len(influencers),
                "influencers": influencers
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================
    # DATA EXTRACTION
    # ==========================================
    
    @tool(
        name="browser_extract_data",
        description="Extract structured data from any webpage using AI",
        category="browser_use"
    )
    async def extract_data(
        self,
        url: str,
        data_description: str,
        output_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Extract specific data from a webpage.
        
        Args:
            url: URL to extract from
            data_description: Description of what data to extract
            output_format: Desired format (json, list, table)
        """
        task = f"""
        Visit {url} and extract: {data_description}
        
        Return the data in {output_format} format.
        Be thorough and capture all relevant information.
        Scroll through the page if needed to find all data.
        """
        
        try:
            result = await self._run_agent(task, max_steps=25)
            
            extracted = result
            if output_format == "json":
                try:
                    if isinstance(result, str):
                        import re
                        json_match = re.search(r'[\[\{][\s\S]*[\]\}]', result)
                        if json_match:
                            extracted = json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            return {
                "success": True,
                "url": url,
                "data_type": data_description,
                "extracted_data": extracted
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="browser_take_screenshot",
        description="Navigate to a URL and take a screenshot",
        category="browser_use"
    )
    async def take_screenshot(
        self,
        url: str,
        full_page: bool = False
    ) -> Dict[str, Any]:
        """
        Take a screenshot of a webpage.
        
        Args:
            url: URL to screenshot
            full_page: Capture full scrollable page
        """
        task = f"""
        Navigate to {url} and take a screenshot.
        {"Capture the full scrollable page." if full_page else "Capture the visible viewport."}
        Save the screenshot.
        """
        
        try:
            result = await self._run_agent(task, max_steps=10)
            
            return {
                "success": True,
                "url": url,
                "full_page": full_page,
                "result": str(result)[:200]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================
    # GENERAL AUTOMATION
    # ==========================================
    
    @tool(
        name="browser_automate_task",
        description="Perform any custom browser automation task described in natural language",
        category="browser_use"
    )
    async def automate_task(
        self,
        task_description: str,
        starting_url: str = None,
        max_steps: int = 30
    ) -> Dict[str, Any]:
        """
        Perform a custom automation task.
        
        Args:
            task_description: Natural language description of what to do
            starting_url: URL to start from (optional)
            max_steps: Maximum actions to take
        """
        full_task = task_description
        if starting_url:
            full_task = f"Start at {starting_url}. Then: {task_description}"
        
        try:
            result = await self._run_agent(full_task, max_steps=max_steps)
            
            return {
                "success": True,
                "task": task_description,
                "starting_url": starting_url,
                "result": str(result)[:2000]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# Factory function
def create_browser_use_tools(
    llm_provider: str = None,
    headless: bool = True
) -> BrowserUseTools:
    """Create BrowserUseTools instance."""
    provider = llm_provider or os.getenv("BROWSER_USE_LLM_PROVIDER", "anthropic")
    
    return BrowserUseTools(
        llm_provider=provider,
        headless=headless
    )
