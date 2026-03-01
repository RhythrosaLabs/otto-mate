"""
Enhanced Printify Client - Robust API Integration

Based on best practices for autonomous agent systems:
- Structured intent representation before API calls
- Modular tool adapters with clean interfaces
- Idempotent execution with retry logic
- Rate limiting and connection health monitoring
- Full catalog search with dynamic blueprint discovery

This module provides production-grade Printify connectivity for
natural-language-driven product creation workflows.
"""

import asyncio
import aiohttp
import hashlib
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable
from functools import wraps

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION & CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

class PrintifyEndpoints:
    """Centralized endpoint management"""
    BASE_URL = "https://api.printify.com/v1"
    
    @classmethod
    def shops(cls) -> str:
        return f"{cls.BASE_URL}/shops.json"
    
    @classmethod
    def shop_products(cls, shop_id: str) -> str:
        return f"{cls.BASE_URL}/shops/{shop_id}/products.json"
    
    @classmethod
    def product(cls, shop_id: str, product_id: str) -> str:
        return f"{cls.BASE_URL}/shops/{shop_id}/products/{product_id}.json"
    
    @classmethod
    def blueprints(cls) -> str:
        return f"{cls.BASE_URL}/catalog/blueprints.json"
    
    @classmethod
    def blueprint(cls, blueprint_id: int) -> str:
        return f"{cls.BASE_URL}/catalog/blueprints/{blueprint_id}.json"
    
    @classmethod
    def blueprint_providers(cls, blueprint_id: int) -> str:
        return f"{cls.BASE_URL}/catalog/blueprints/{blueprint_id}/print_providers.json"
    
    @classmethod
    def provider_variants(cls, blueprint_id: int, provider_id: int) -> str:
        return f"{cls.BASE_URL}/catalog/blueprints/{blueprint_id}/print_providers/{provider_id}/variants.json"
    
    @classmethod
    def publish(cls, shop_id: str, product_id: str) -> str:
        return f"{cls.BASE_URL}/shops/{shop_id}/products/{product_id}/publish.json"
    
    @classmethod
    def uploads(cls) -> str:
        return f"{cls.BASE_URL}/uploads/images.json"


# ═══════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES - Structured Intent Representation (SIR)
# ═══════════════════════════════════════════════════════════════════════════

class ProductCategory(Enum):
    """Standardized product categories for routing"""
    APPAREL = "apparel"
    DRINKWARE = "drinkware"
    ACCESSORIES = "accessories"
    HOME_DECOR = "home_decor"
    WALL_ART = "wall_art"
    STATIONERY = "stationery"
    NOVELTY = "novelty"
    PET = "pet"
    UNKNOWN = "unknown"


@dataclass
class ProductIntent:
    """
    Structured Intent Representation (SIR) for product creation.
    
    This prevents hallucination and limits the attack surface by
    ensuring all product creation flows through a validated schema.
    """
    product_type: str  # e.g., "mug", "t-shirt", "tote bag"
    category: ProductCategory = ProductCategory.UNKNOWN
    style_hint: str = ""  # Design description for AI generation
    requires_image: bool = True
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    price_cents: int = 2499
    raw_input: str = ""  # Original user input for debugging
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_type": self.product_type,
            "category": self.category.value,
            "style_hint": self.style_hint,
            "requires_image": self.requires_image,
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "price_cents": self.price_cents,
            "raw_input": self.raw_input
        }


@dataclass
class ConnectionHealth:
    """Track API connection health metrics"""
    is_healthy: bool = True
    last_check: datetime = field(default_factory=datetime.now)
    consecutive_failures: int = 0
    last_error: Optional[str] = None
    avg_response_ms: float = 0.0
    total_requests: int = 0
    successful_requests: int = 0
    rate_limit_remaining: Optional[int] = None
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    def record_success(self, response_ms: float):
        self.total_requests += 1
        self.successful_requests += 1
        self.consecutive_failures = 0
        self.is_healthy = True
        self.last_check = datetime.now()
        # Moving average
        self.avg_response_ms = (self.avg_response_ms * 0.9) + (response_ms * 0.1)
    
    def record_failure(self, error: str):
        self.total_requests += 1
        self.consecutive_failures += 1
        self.last_error = error
        self.last_check = datetime.now()
        if self.consecutive_failures >= 3:
            self.is_healthy = False


@dataclass
class BlueprintMatch:
    """Represents a matched blueprint from catalog search"""
    blueprint_id: int
    title: str
    description: str
    print_provider_id: int
    provider_name: str
    match_score: float
    category: ProductCategory
    images: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════
# INTENT PARSER - Natural Language → Structured Intent
# ═══════════════════════════════════════════════════════════════════════════

class IntentParser:
    """
    Parse natural language product requests into structured intents.
    
    This is the first step in the agent pipeline - NEVER call APIs
    directly from raw user input. Always extract structured intent first.
    
    Enhanced with comprehensive conversational understanding for:
    - Casual phrasing ("I want a cool shirt")
    - Vague descriptions ("some wall art")
    - Complex requests ("make me a set of playing cards and a puzzle")
    - Follow-ups ("now do that in blue")
    """
    
    # ═══════════════════════════════════════════════════════════════
    # COMPREHENSIVE PRODUCT KEYWORDS → canonical names
    # ═══════════════════════════════════════════════════════════════
    PRODUCT_KEYWORDS = {
        # ── Apparel - Tops ──
        "t-shirt": [
            "tshirt", "t shirt", "tee", "shirt", "graphic tee", "custom shirt",
            "printed tee", "cotton shirt", "casual shirt", "unisex shirt",
            "cool shirt", "fun shirt"
        ],
        "hoodie": [
            "hoody", "hood", "sweatshirt", "pullover", "jumper", "sweat shirt",
            "hooded sweater", "fleece", "cozy hoodie"
        ],
        "tank top": [
            "tank", "tanktop", "sleeveless", "muscle tee", "workout top",
            "gym shirt", "summer top"
        ],
        "long sleeve": [
            "long sleeve shirt", "longsleeve", "long sleeved"
        ],
        "leggings": ["legging", "yoga pants", "gym leggings", "workout pants"],
        "socks": ["sock", "crew socks", "fun socks", "novelty socks", "custom socks"],
        "beanie": [
            "beanie hat", "knit hat", "winter hat", "ski hat", "toboggan",
            "knit cap", "winter cap"
        ],
        
        # ── Drinkware ──
        "mug": [
            "coffee mug", "cup", "tea mug", "ceramic mug", "custom mug",
            "photo mug", "personalized mug", "office mug"
        ],
        "tumbler": [
            "travel tumbler", "insulated cup", "thermos", "insulated tumbler"
        ],
        "water bottle": [
            "waterbottle", "bottle", "sports bottle", "hydration bottle"
        ],
        "travel mug": ["travel cup", "to-go mug", "commuter mug"],
        
        # ── Accessories - Bags ──
        "tote bag": [
            "tote", "shopping bag", "canvas bag", "grocery bag", "market bag",
            "reusable bag", "cotton tote"
        ],
        "backpack": [
            "back pack", "rucksack", "book bag", "school bag", "daypack"
        ],
        "fanny pack": [
            "hip bag", "belt bag", "waist bag", "bum bag"
        ],
        "drawstring bag": ["gym bag", "string bag", "cinch bag"],
        
        # ── Accessories - Cases & Hats ──
        "phone case": [
            "phonecase", "iphone case", "samsung case", "cell phone case",
            "mobile case", "smartphone case", "protective case"
        ],
        "hat": [
            "cap", "baseball cap", "dad hat", "trucker hat", "snapback",
            "fitted hat", "sports cap", "golf hat"
        ],
        
        # ── Home & Decor ──
        "pillow": [
            "throw pillow", "cushion", "decorative pillow", "accent pillow",
            "sofa pillow", "bed pillow"
        ],
        "blanket": [
            "throw blanket", "fleece blanket", "cozy blanket", "bed blanket"
        ],
        "shower curtain": ["bath curtain"],
        "doormat": ["door mat", "welcome mat", "entry mat"],
        "mousepad": ["mouse pad", "desk pad"],
        "clock": ["wall clock", "home clock", "office clock", "timepiece"],
        "coaster": [
            "drink coaster", "cup coaster", "coasters", "coaster set"
        ],
        "cutting board": [
            "cheese board", "chopping board", "kitchen board"
        ],
        "towel": ["beach towel", "bath towel", "hand towel"],
        
        # ── Wall Art ──
        "poster": [
            "print", "art print", "wall poster", "art poster"
        ],
        "canvas": [
            "canvas print", "wall canvas", "gallery wrap", "stretched canvas",
            "wall art", "home decor art"
        ],
        "framed poster": [
            "framed print", "framed art", "picture frame"
        ],
        "metal print": ["aluminum print"],
        "acrylic print": ["acrylic art"],
        "wood print": ["wooden print"],
        
        # ── Stationery ──
        "notebook": [
            "journal", "diary", "spiral notebook", "composition book",
            "writing journal", "lined journal"
        ],
        "sticker": [
            "stickers", "decal", "laptop sticker", "vinyl sticker",
            "car sticker", "bumper sticker"
        ],
        "magnet": ["fridge magnet", "refrigerator magnet"],
        "greeting card": ["card", "birthday card"],
        "postcard": ["post card"],
        
        # ── Novelty & Gifts ──
        "puzzle": [
            "jigsaw", "jigsaw puzzle", "photo puzzle", "picture puzzle",
            "custom puzzle"
        ],
        "playing cards": [
            "card deck", "poker cards", "game cards", "deck of cards",
            "custom cards", "tarot deck"
        ],
        "ornament": [
            "christmas ornament", "xmas ornament", "tree ornament",
            "holiday ornament", "decoration"
        ],
        "flag": [
            "garden flag", "yard flag", "house flag", "outdoor flag",
            "decorative flag"
        ],
        "apron": [
            "kitchen apron", "cooking apron", "chef apron", "bbq apron"
        ],
        "flip flops": ["sandals", "beach sandals", "thongs"],
        
        # ── Pet Products ──
        "pet bandana": [
            "dog bandana", "cat bandana", "pet scarf", "puppy bandana"
        ],
    }
    
    # ═══════════════════════════════════════════════════════════════
    # CONVERSATIONAL INTENT PATTERNS
    # ═══════════════════════════════════════════════════════════════
    # Patterns that indicate product creation even without explicit keywords
    CREATION_PATTERNS = [
        r"(?:i\s+)?(?:want|need|would\s+like)\s+(?:a|an|some)",
        r"(?:can\s+you\s+)?(?:make|create|design|generate)\s+(?:me\s+)?(?:a|an|some)?",
        r"(?:let'?s\s+)?(?:make|create|do|try)\s+(?:a|an|some)?",
        r"give\s+me\s+(?:a|an|some)",
        r"how\s+about\s+(?:a|an|some)?",
        r"(?:i'm\s+)?thinking\s+(?:of|about)\s+(?:a|an)?",
    ]
    
    # Action verbs that indicate desire for product creation
    ACTION_KEYWORDS = [
        "make", "create", "design", "generate", "produce", "print",
        "want", "need", "sell", "list", "put", "add", "build"
    ]
    
    # ═══════════════════════════════════════════════════════════════
    # CATEGORY MAPPINGS - Expanded for all products
    # ═══════════════════════════════════════════════════════════════
    CATEGORY_MAP = {
        # Apparel
        "t-shirt": ProductCategory.APPAREL,
        "hoodie": ProductCategory.APPAREL,
        "tank top": ProductCategory.APPAREL,
        "long sleeve": ProductCategory.APPAREL,
        "leggings": ProductCategory.APPAREL,
        "socks": ProductCategory.APPAREL,
        "beanie": ProductCategory.APPAREL,
        "apron": ProductCategory.APPAREL,
        "flip flops": ProductCategory.APPAREL,
        
        # Drinkware
        "mug": ProductCategory.DRINKWARE,
        "tumbler": ProductCategory.DRINKWARE,
        "water bottle": ProductCategory.DRINKWARE,
        "travel mug": ProductCategory.DRINKWARE,
        
        # Accessories
        "tote bag": ProductCategory.ACCESSORIES,
        "backpack": ProductCategory.ACCESSORIES,
        "fanny pack": ProductCategory.ACCESSORIES,
        "drawstring bag": ProductCategory.ACCESSORIES,
        "phone case": ProductCategory.ACCESSORIES,
        "hat": ProductCategory.ACCESSORIES,
        "pet bandana": ProductCategory.ACCESSORIES,
        
        # Home & Decor
        "pillow": ProductCategory.HOME_DECOR,
        "blanket": ProductCategory.HOME_DECOR,
        "shower curtain": ProductCategory.HOME_DECOR,
        "doormat": ProductCategory.HOME_DECOR,
        "mousepad": ProductCategory.HOME_DECOR,
        "clock": ProductCategory.HOME_DECOR,
        "coaster": ProductCategory.HOME_DECOR,
        "cutting board": ProductCategory.HOME_DECOR,
        "towel": ProductCategory.HOME_DECOR,
        
        # Wall Art
        "poster": ProductCategory.WALL_ART,
        "canvas": ProductCategory.WALL_ART,
        "framed poster": ProductCategory.WALL_ART,
        "metal print": ProductCategory.WALL_ART,
        "acrylic print": ProductCategory.WALL_ART,
        "wood print": ProductCategory.WALL_ART,
        
        # Stationery
        "notebook": ProductCategory.STATIONERY,
        "sticker": ProductCategory.STATIONERY,
        "magnet": ProductCategory.STATIONERY,
        "greeting card": ProductCategory.STATIONERY,
        "postcard": ProductCategory.STATIONERY,
        
        # Novelty
        "puzzle": ProductCategory.NOVELTY,
        "playing cards": ProductCategory.NOVELTY,
        "ornament": ProductCategory.NOVELTY,
        "flag": ProductCategory.NOVELTY,
    }
    
    # ═══════════════════════════════════════════════════════════════
    # DESIGN KEYWORDS - Expanded for conversational understanding
    # ═══════════════════════════════════════════════════════════════
    # These keywords indicate that image/design generation is needed
    DESIGN_KEYWORDS = [
        # Explicit creation verbs
        "design", "create", "make", "generate", "draw", "illustrate",
        "produce", "craft", "build",
        
        # Feature words
        "feature", "featuring", "with", "showing", "depicting",
        "of", "themed", "style", "inspired",
        
        # Descriptive words often preceding design details
        "about", "like", "similar", "based on",
        
        # Visual descriptors
        "colorful", "minimalist", "abstract", "vintage", "modern",
        "retro", "cute", "funny", "artistic", "elegant"
    ]
    
    # Words that modify the design (colors, styles, themes)
    STYLE_MODIFIERS = [
        "cool", "awesome", "epic", "sick", "dope", "fire",
        "cute", "pretty", "beautiful", "elegant", "classy",
        "funny", "hilarious", "quirky", "weird", "wild",
        "minimalist", "simple", "clean", "bold", "vibrant",
        "vintage", "retro", "modern", "futuristic", "classic",
        "abstract", "geometric", "organic", "natural",
    ]
    
    def parse(self, user_input: str) -> ProductIntent:
        """
        Parse natural language input into structured ProductIntent.
        
        Example:
            "Design and sell a tote bag featuring an abstract heart doodle"
            → ProductIntent(product_type="tote bag", style_hint="abstract heart doodle", ...)
        """
        input_lower = user_input.lower().strip()
        
        # 1. Identify product type
        product_type = self._extract_product_type(input_lower)
        
        # 2. Determine category
        category = self.CATEGORY_MAP.get(product_type, ProductCategory.UNKNOWN)
        
        # 3. Check if image generation is needed
        requires_image = any(kw in input_lower for kw in self.DESIGN_KEYWORDS)
        
        # 4. Extract style hint (the design description)
        style_hint = self._extract_style_hint(user_input, product_type)
        
        # 5. Generate default title and tags
        title = self._generate_title(product_type, style_hint)
        tags = self._generate_tags(product_type, style_hint, category)
        
        return ProductIntent(
            product_type=product_type,
            category=category,
            style_hint=style_hint,
            requires_image=requires_image,
            title=title,
            tags=tags,
            raw_input=user_input
        )
    
    def _extract_product_type(self, input_lower: str) -> str:
        """Find the product type mentioned in the input"""
        # Check canonical names first
        for canonical, aliases in self.PRODUCT_KEYWORDS.items():
            if canonical in input_lower:
                return canonical
            for alias in aliases:
                if alias in input_lower:
                    return canonical
        
        # If no match, try to find any product-like word
        # This is a fallback that returns the first noun-like match
        return "custom product"
    
    def _extract_style_hint(self, user_input: str, product_type: str) -> str:
        """Extract the design description from the input"""
        input_lower = user_input.lower()
        
        # Common patterns: "featuring X", "with X", "of X"
        patterns = [
            r"featuring\s+(.+?)(?:\s+on|\s+for|\.|$)",
            r"with\s+(?:a|an)?\s*(.+?)(?:\s+on|\s+for|\.|$)",
            r"showing\s+(.+?)(?:\s+on|\s+for|\.|$)",
            r"depicting\s+(.+?)(?:\s+on|\s+for|\.|$)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, input_lower)
            if match:
                return match.group(1).strip()
        
        # If no pattern matches, remove action words and product type
        # to get the remaining description
        cleaned = input_lower
        for word in ["design", "create", "make", "sell", "and", "a", "an", "the"]:
            cleaned = cleaned.replace(word, " ")
        cleaned = cleaned.replace(product_type, "")
        cleaned = " ".join(cleaned.split())  # Normalize whitespace
        
        return cleaned if cleaned else "custom design"
    
    def _generate_title(self, product_type: str, style_hint: str) -> str:
        """Generate a product title"""
        # Capitalize words properly
        style_words = style_hint.title()
        product_words = product_type.title()
        return f"{style_words} {product_words}"
    
    def _generate_tags(
        self, 
        product_type: str, 
        style_hint: str,
        category: ProductCategory
    ) -> List[str]:
        """Generate relevant tags for the product"""
        tags = [
            product_type.lower(),
            category.value.replace("_", " "),
            "custom",
            "design",
        ]
        
        # Add words from style hint
        style_words = style_hint.lower().split()
        for word in style_words:
            if len(word) > 3 and word not in tags:
                tags.append(word)
        
        return tags[:10]  # Limit to 10 tags


# ═══════════════════════════════════════════════════════════════════════════
# ENHANCED API CLIENT - Robust Connection Handling
# ═══════════════════════════════════════════════════════════════════════════

def with_retry(
    max_retries: int = 3,
    backoff_base: float = 2.0,
    retryable_statuses: tuple = (429, 500, 502, 503, 504)
):
    """
    Decorator for automatic retry with exponential backoff.
    Handles rate limiting and transient failures gracefully.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except aiohttp.ClientResponseError as e:
                    last_error = e
                    if e.status in retryable_statuses:
                        wait_time = backoff_base ** attempt
                        if e.status == 429:
                            # Rate limited - wait longer
                            wait_time = max(wait_time, 5.0)
                            logger.warning(f"Rate limited, waiting {wait_time}s before retry")
                        else:
                            logger.warning(f"Retryable error {e.status}, attempt {attempt + 1}/{max_retries}")
                        await asyncio.sleep(wait_time)
                        continue
                    raise
                except aiohttp.ClientError as e:
                    last_error = e
                    wait_time = backoff_base ** attempt
                    logger.warning(f"Network error: {e}, attempt {attempt + 1}/{max_retries}")
                    await asyncio.sleep(wait_time)
                    continue
            
            raise last_error or Exception("Max retries exceeded")
        return wrapper
    return decorator


class EnhancedPrintifyClient:
    """
    Production-grade Printify API client with:
    - Connection pooling and reuse
    - Automatic retry with exponential backoff
    - Rate limiting awareness
    - Health monitoring
    - Request/response logging
    - Idempotent operations where possible
    """
    
    def __init__(
        self,
        api_token: Optional[str] = None,
        shop_id: Optional[str] = None,
        timeout_seconds: int = 30,
        max_connections: int = 10
    ):
        self.api_token = api_token or os.getenv("PRINTIFY_API_TOKEN")
        self.shop_id = shop_id or os.getenv("PRINTIFY_SHOP_ID")
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self.max_connections = max_connections
        
        # Connection health tracking
        self.health = ConnectionHealth()
        
        # Caching
        self._blueprint_cache: Optional[List[Dict]] = None
        self._blueprint_cache_time: float = 0
        self._cache_ttl: int = 3600  # 1 hour
        
        # Session management
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector: Optional[aiohttp.TCPConnector] = None
        
        # Request tracking for idempotency
        self._request_hashes: Dict[str, datetime] = {}
    
    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "User-Agent": "Otto-Universal/2.0"
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create a persistent session with connection pooling"""
        if self._session is None or self._session.closed:
            self._connector = aiohttp.TCPConnector(
                limit=self.max_connections,
                limit_per_host=self.max_connections,
                ttl_dns_cache=300
            )
            self._session = aiohttp.ClientSession(
                connector=self._connector,
                timeout=self.timeout,
                headers=self.headers
            )
        return self._session
    
    async def close(self):
        """Close the session and release resources"""
        if self._session and not self._session.closed:
            await self._session.close()
        if self._connector:
            await self._connector.close()
    
    def _generate_request_hash(self, method: str, url: str, data: Optional[Dict]) -> str:
        """Generate a hash for idempotency checking"""
        content = f"{method}:{url}:{json.dumps(data, sort_keys=True) if data else ''}"
        return hashlib.md5(content.encode()).hexdigest()
    
    @with_retry(max_retries=3, backoff_base=2.0)
    async def _request(
        self,
        method: str,
        url: str,
        data: Optional[Dict] = None,
        idempotency_check: bool = True
    ) -> Dict[str, Any]:
        """
        Make an API request with full error handling and monitoring.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: Full URL to request
            data: Optional JSON body
            idempotency_check: If True, prevent duplicate POST requests
        
        Returns:
            Parsed JSON response
        
        Raises:
            aiohttp.ClientResponseError: On API errors
            aiohttp.ClientError: On network errors
        """
        # Idempotency check for POST requests
        if idempotency_check and method == "POST" and data:
            request_hash = self._generate_request_hash(method, url, data)
            if request_hash in self._request_hashes:
                last_time = self._request_hashes[request_hash]
                if (datetime.now() - last_time).seconds < 60:
                    logger.warning(f"Duplicate request detected, skipping: {url}")
                    return {"duplicate": True, "message": "Request already processed"}
        
        session = await self._get_session()
        start_time = time.time()
        
        try:
            async with session.request(method, url, json=data) as response:
                response_ms = (time.time() - start_time) * 1000
                
                # Track rate limit headers if present
                if "X-RateLimit-Remaining" in response.headers:
                    self.health.rate_limit_remaining = int(
                        response.headers["X-RateLimit-Remaining"]
                    )
                
                if response.status >= 400:
                    error_text = await response.text()
                    self.health.record_failure(f"{response.status}: {error_text[:200]}")
                    logger.error(f"Printify API error {response.status}: {error_text[:500]}")
                    response.raise_for_status()
                
                result = await response.json()
                self.health.record_success(response_ms)
                
                # Record successful POST for idempotency
                if method == "POST" and data:
                    request_hash = self._generate_request_hash(method, url, data)
                    self._request_hashes[request_hash] = datetime.now()
                
                return result
                
        except aiohttp.ClientError as e:
            self.health.record_failure(str(e))
            raise
    
    # ═══════════════════════════════════════════════════════════════════════
    # HEALTH MONITORING
    # ═══════════════════════════════════════════════════════════════════════
    
    async def check_health(self) -> ConnectionHealth:
        """
        Perform a health check on the Printify API connection.
        Returns current health status with metrics.
        """
        try:
            await self._request("GET", PrintifyEndpoints.shops())
            return self.health
        except Exception as e:
            self.health.record_failure(str(e))
            return self.health
    
    async def get_health_report(self) -> Dict[str, Any]:
        """Get a detailed health report"""
        await self.check_health()
        return {
            "is_healthy": self.health.is_healthy,
            "last_check": self.health.last_check.isoformat(),
            "success_rate": f"{self.health.success_rate * 100:.1f}%",
            "avg_response_ms": f"{self.health.avg_response_ms:.0f}ms",
            "total_requests": self.health.total_requests,
            "consecutive_failures": self.health.consecutive_failures,
            "rate_limit_remaining": self.health.rate_limit_remaining,
            "last_error": self.health.last_error
        }
    
    # ═══════════════════════════════════════════════════════════════════════
    # CATALOG SEARCH - Dynamic Blueprint Discovery
    # ═══════════════════════════════════════════════════════════════════════
    
    async def get_all_blueprints(self, force_refresh: bool = False) -> List[Dict]:
        """
        Fetch all blueprints from Printify catalog with caching.
        
        This is the foundation for dynamic product discovery -
        we search the actual catalog rather than relying on hardcoded IDs.
        """
        current_time = time.time()
        
        # Check cache
        if not force_refresh and self._blueprint_cache:
            cache_age = current_time - self._blueprint_cache_time
            if cache_age < self._cache_ttl:
                logger.debug(f"Using cached blueprints ({len(self._blueprint_cache)} items)")
                return self._blueprint_cache
        
        # Fetch fresh data
        result = await self._request("GET", PrintifyEndpoints.blueprints())
        
        if isinstance(result, list):
            self._blueprint_cache = result
            self._blueprint_cache_time = current_time
            logger.info(f"Fetched {len(result)} blueprints from Printify catalog")
            return result
        
        # Handle unexpected format
        data = result.get("data", []) if isinstance(result, dict) else []
        self._blueprint_cache = data
        self._blueprint_cache_time = current_time
        return data
    
    async def search_catalog(
        self,
        product_type: str,
        limit: int = 5
    ) -> List[BlueprintMatch]:
        """
        Search the Printify catalog for matching blueprints.
        
        Uses fuzzy matching to find relevant products based on
        the product type from the parsed intent.
        
        Args:
            product_type: The type of product to search for (e.g., "mug", "tote bag")
            limit: Maximum number of results to return
        
        Returns:
            List of BlueprintMatch objects sorted by relevance score
        """
        blueprints = await self.get_all_blueprints()
        matches = []
        
        # Normalize search terms
        product_type_lower = product_type.lower().strip()
        search_terms = product_type_lower.split()
        
        # Get aliases for this product type
        aliases = self.PRODUCT_KEYWORDS.get(product_type_lower, [])
        all_terms = [product_type_lower] + list(aliases)
        
        for bp in blueprints:
            title = bp.get("title", "").lower()
            description = bp.get("description", "").lower()
            blueprint_id = bp.get("id")
            
            if not blueprint_id:
                continue
            
            # Calculate match score with improved weighting
            score = 0.0
            
            # CRITICAL: Exact product type match in title - highest priority
            if product_type_lower in title:
                score += 3.0
            
            # Very high score for any alias in title
            for alias in aliases:
                if alias in title:
                    score += 2.5
                    break
            
            # High score for exact product type as title start
            if title.startswith(product_type_lower) or title.startswith(product_type_lower.replace(" ", "")):
                score += 1.0
            
            # Partial term matches in title
            for term in search_terms:
                if len(term) >= 3 and term in title:  # Ignore short words
                    score += 0.5
                if len(term) >= 3 and term in description:
                    score += 0.1
            
            # Penalize items that are clearly different products
            # Avoid matching "t-shirt" when user wants "mug"
            wrong_products = {
                "mug": ["shirt", "hoodie", "poster", "sticker", "tote"],
                "t-shirt": ["mug", "poster", "sticker", "canvas", "pillow"],
                "poster": ["mug", "shirt", "hoodie", "bag"],
                "tote bag": ["mug", "shirt", "poster", "pillow"],
                "hoodie": ["mug", "poster", "sticker", "canvas"],
                "canvas": ["mug", "shirt", "hoodie", "sticker"],
                "sticker": ["mug", "shirt", "hoodie", "canvas", "poster"],
            }
            if product_type_lower in wrong_products:
                for wrong in wrong_products[product_type_lower]:
                    if wrong in title:
                        score -= 2.0
            
            if score > 0:
                # Get first print provider for this blueprint
                providers = await self._get_blueprint_providers(blueprint_id)
                provider_id = providers[0].get("id", 1) if providers else 1
                provider_name = providers[0].get("title", "Default") if providers else "Default"
                
                # Determine category
                category = self._categorize_blueprint(title, description)
                
                matches.append(BlueprintMatch(
                    blueprint_id=blueprint_id,
                    title=bp.get("title", ""),
                    description=bp.get("description", "")[:200],
                    print_provider_id=provider_id,
                    provider_name=provider_name,
                    match_score=score,
                    category=category,
                    images=bp.get("images", [])
                ))
        
        # Sort by score (highest first) and return top matches
        matches.sort(key=lambda x: x.match_score, reverse=True)
        
        # Log top matches for debugging
        if matches:
            logger.info(f"Top blueprint matches for '{product_type}': {[f'{m.title}({m.match_score})' for m in matches[:3]]}")
        
        return matches[:limit]
    
    async def _get_blueprint_providers(self, blueprint_id: int) -> List[Dict]:
        """Get print providers for a blueprint"""
        try:
            result = await self._request(
                "GET",
                PrintifyEndpoints.blueprint_providers(blueprint_id)
            )
            return result if isinstance(result, list) else result.get("data", [])
        except Exception as e:
            logger.warning(f"Failed to get providers for blueprint {blueprint_id}: {e}")
            return []
    
    def _categorize_blueprint(self, title: str, description: str) -> ProductCategory:
        """Categorize a blueprint based on its title and description"""
        text = f"{title} {description}".lower()
        
        if any(w in text for w in ["shirt", "hoodie", "sweatshirt", "tank", "legging"]):
            return ProductCategory.APPAREL
        elif any(w in text for w in ["mug", "tumbler", "bottle", "cup"]):
            return ProductCategory.DRINKWARE
        elif any(w in text for w in ["bag", "case", "hat", "cap", "sock"]):
            return ProductCategory.ACCESSORIES
        elif any(w in text for w in ["poster", "canvas", "print", "art"]):
            return ProductCategory.WALL_ART
        elif any(w in text for w in ["pillow", "blanket", "clock", "coaster"]):
            return ProductCategory.HOME_DECOR
        elif any(w in text for w in ["notebook", "sticker", "magnet"]):
            return ProductCategory.STATIONERY
        elif any(w in text for w in ["puzzle", "card", "ornament"]):
            return ProductCategory.NOVELTY
        elif any(w in text for w in ["pet", "dog", "cat"]):
            return ProductCategory.PET
        
        return ProductCategory.UNKNOWN
    
    # ═══════════════════════════════════════════════════════════════════════
    # PRODUCT CREATION - From Intent to Published Product
    # ═══════════════════════════════════════════════════════════════════════
    
    async def create_product_from_intent(
        self,
        intent: ProductIntent,
        image_url: str,
        blueprint_match: Optional[BlueprintMatch] = None
    ) -> Dict[str, Any]:
        """
        Create a product from a structured intent and design image.
        
        This is the main entry point for autonomous product creation.
        It handles blueprint selection, variant configuration, and publishing.
        
        Args:
            intent: Parsed ProductIntent with all product details
            image_url: URL of the design image (from AI generation or upload)
            blueprint_match: Optional pre-selected blueprint, auto-selects if None
        
        Returns:
            Created product data including ID and status
        """
        # Auto-select blueprint if not provided
        if not blueprint_match:
            matches = await self.search_catalog(intent.product_type)
            if not matches:
                return {
                    "success": False,
                    "error": f"No matching products found for '{intent.product_type}'",
                    "hint": "Try a different product type like 'mug', 'tote bag', or 't-shirt'"
                }
            blueprint_match = matches[0]
            logger.info(f"Auto-selected blueprint: {blueprint_match.title} (score: {blueprint_match.match_score})")
        
        # Upload the image first
        upload_result = await self.upload_image(image_url)
        if not upload_result.get("id"):
            return {
                "success": False,
                "error": "Failed to upload design image",
                "details": upload_result
            }
        
        image_id = upload_result["id"]
        
        # Get variants and placeholders
        variants = await self._get_default_variants(
            blueprint_match.blueprint_id,
            blueprint_match.print_provider_id
        )
        
        placeholders = await self._get_blueprint_placeholders(
            blueprint_match.blueprint_id,
            blueprint_match.print_provider_id
        )
        
        # Build print areas
        print_areas = self._build_print_areas(placeholders, image_id, variants)
        
        # Build product payload
        product_data = {
            "title": intent.title or f"{intent.style_hint} {intent.product_type}".title(),
            "description": intent.description or f"Custom designed {intent.product_type} featuring {intent.style_hint}.",
            "blueprint_id": blueprint_match.blueprint_id,
            "print_provider_id": blueprint_match.print_provider_id,
            "variants": variants,
            "print_areas": print_areas,
            "tags": intent.tags or [intent.product_type, "custom", "design"]
        }
        
        # Create the product
        if not self.shop_id:
            return {
                "success": False,
                "error": "Shop ID not configured"
            }
        
        try:
            result = await self._request(
                "POST",
                PrintifyEndpoints.shop_products(self.shop_id),
                product_data
            )
            
            product_id = result.get("id")
            if product_id:
                # Auto-publish
                try:
                    await self.publish_product(product_id)
                    result["published"] = True
                    logger.info(f"Product {product_id} created and published successfully")
                except Exception as pub_error:
                    result["published"] = False
                    result["publish_error"] = str(pub_error)
                    logger.warning(f"Product created but publish failed: {pub_error}")
            
            result["success"] = True
            result["blueprint_used"] = blueprint_match.title
            return result
            
        except Exception as e:
            logger.error(f"Product creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "intent": intent.to_dict()
            }
    
    async def upload_image(self, image_url: str) -> Dict[str, Any]:
        """Upload an image to Printify"""
        try:
            result = await self._request(
                "POST",
                PrintifyEndpoints.uploads(),
                {"file_name": "design.png", "url": image_url}
            )
            return result
        except Exception as e:
            logger.error(f"Image upload failed: {e}")
            return {"error": str(e)}
    
    async def publish_product(self, product_id: str) -> Dict[str, Any]:
        """Publish a product to connected store (Shopify)"""
        if not self.shop_id:
            return {"error": "Shop ID not configured"}
        
        publish_data = {
            "title": True,
            "description": True,
            "images": True,
            "variants": True,
            "tags": True,
            "keyFeatures": True,
            "shipping_template": True
        }
        
        return await self._request(
            "POST",
            PrintifyEndpoints.publish(self.shop_id, product_id),
            publish_data
        )
    
    async def _get_default_variants(
        self,
        blueprint_id: int,
        provider_id: int
    ) -> List[Dict]:
        """Get default variant configuration for a blueprint"""
        try:
            result = await self._request(
                "GET",
                PrintifyEndpoints.provider_variants(blueprint_id, provider_id)
            )
            
            variants = result.get("variants", result) if isinstance(result, dict) else result
            
            # Configure variants with pricing
            configured = []
            for v in variants[:20]:  # Limit to 20 variants
                configured.append({
                    "id": v.get("id"),
                    "price": 2499,  # $24.99 default
                    "is_enabled": True
                })
            
            return configured
            
        except Exception as e:
            logger.warning(f"Failed to get variants: {e}")
            return []
    
    async def _get_blueprint_placeholders(
        self,
        blueprint_id: int,
        provider_id: int
    ) -> List[Dict]:
        """Get placeholder positions for a blueprint"""
        try:
            bp_result = await self._request(
                "GET",
                PrintifyEndpoints.blueprint(blueprint_id)
            )
            
            return bp_result.get("print_areas", [])
            
        except Exception as e:
            logger.warning(f"Failed to get placeholders: {e}")
            return [{"position": "front", "variant_ids": []}]
    
    def _build_print_areas(
        self,
        placeholders: List[Dict],
        image_id: str,
        variants: List[Dict]
    ) -> List[Dict]:
        """Build print areas configuration"""
        variant_ids = [v.get("id") for v in variants if v.get("is_enabled", True)]
        
        if not placeholders:
            # Default front print area
            return [{
                "variant_ids": variant_ids,
                "placeholders": [{
                    "position": "front",
                    "images": [{
                        "id": image_id,
                        "x": 0.5,
                        "y": 0.5,
                        "scale": 1.0,
                        "angle": 0
                    }]
                }]
            }]
        
        print_areas = []
        for placeholder in placeholders:
            print_areas.append({
                "variant_ids": placeholder.get("variant_ids", variant_ids),
                "placeholders": [{
                    "position": placeholder.get("position", "front"),
                    "images": [{
                        "id": image_id,
                        "x": 0.5,
                        "y": 0.5,
                        "scale": 1.0,
                        "angle": 0
                    }]
                }]
            })
        
        return print_areas


# ═══════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR - Chat-to-Product Pipeline
# ═══════════════════════════════════════════════════════════════════════════

class PrintifyWorkflowOrchestrator:
    """
    Orchestrates the complete chat-to-product workflow:
    
    User Input → Intent Parser → Catalog Search → [Image Gen] → Product Creation → Publish
    
    This implements the agentic workflow pattern where natural language
    is transformed into structured intents, then executed via tool adapters.
    """
    
    def __init__(
        self,
        client: Optional[EnhancedPrintifyClient] = None,
        image_generator: Optional[Callable] = None
    ):
        self.client = client or EnhancedPrintifyClient()
        self.parser = IntentParser()
        self.image_generator = image_generator  # Plug in AI image generation
    
    async def execute(
        self,
        user_input: str,
        pre_generated_image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute the complete workflow from user input to published product.
        
        Args:
            user_input: Natural language product request
            pre_generated_image_url: Optional pre-existing image URL
        
        Returns:
            Workflow result with status and product details
        """
        workflow_start = time.time()
        
        try:
            # Step 1: Parse intent
            logger.info(f"Parsing user intent: {user_input[:100]}...")
            intent = self.parser.parse(user_input)
            logger.info(f"Parsed intent: {intent.product_type} ({intent.category.value})")
            
            # Step 2: Search catalog
            logger.info(f"Searching catalog for: {intent.product_type}")
            matches = await self.client.search_catalog(intent.product_type)
            
            if not matches:
                return {
                    "success": False,
                    "stage": "catalog_search",
                    "error": f"No products found matching '{intent.product_type}'",
                    "suggestions": ["mug", "t-shirt", "tote bag", "poster", "sticker"]
                }
            
            best_match = matches[0]
            logger.info(f"Best match: {best_match.title} (score: {best_match.match_score})")
            
            # Step 3: Generate image if needed
            image_url = pre_generated_image_url
            if not image_url and intent.requires_image:
                if self.image_generator:
                    logger.info(f"Generating image for: {intent.style_hint}")
                    image_url = await self.image_generator(intent.style_hint)
                else:
                    return {
                        "success": False,
                        "stage": "image_generation",
                        "error": "Image generation required but no generator configured",
                        "intent": intent.to_dict()
                    }
            
            if not image_url:
                return {
                    "success": False,
                    "stage": "image_required",
                    "error": "No image URL provided and no generator available",
                    "intent": intent.to_dict()
                }
            
            # Step 4: Create product
            logger.info("Creating Printify product...")
            result = await self.client.create_product_from_intent(
                intent=intent,
                image_url=image_url,
                blueprint_match=best_match
            )
            
            # Add workflow metadata
            result["workflow"] = {
                "total_time_ms": (time.time() - workflow_start) * 1000,
                "stages_completed": ["parse", "search", "create"],
                "intent": intent.to_dict(),
                "blueprint_matched": best_match.title
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                "success": False,
                "stage": "execution",
                "error": str(e),
                "workflow_time_ms": (time.time() - workflow_start) * 1000
            }
    
    async def close(self):
        """Close the client connection"""
        await self.client.close()


# ═══════════════════════════════════════════════════════════════════════════
# API ENDPOINTS - FastAPI Integration
# ═══════════════════════════════════════════════════════════════════════════

def create_printify_router():
    """Create FastAPI router for enhanced Printify endpoints"""
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel
    
    router = APIRouter(prefix="/api/printify/v2", tags=["printify-enhanced"])
    
    # Shared client instance
    _client: Optional[EnhancedPrintifyClient] = None
    _orchestrator: Optional[PrintifyWorkflowOrchestrator] = None
    
    def get_client() -> EnhancedPrintifyClient:
        nonlocal _client
        if _client is None:
            _client = EnhancedPrintifyClient()
        return _client
    
    def get_orchestrator() -> PrintifyWorkflowOrchestrator:
        nonlocal _orchestrator
        if _orchestrator is None:
            _orchestrator = PrintifyWorkflowOrchestrator(get_client())
        return _orchestrator
    
    class ProductRequest(BaseModel):
        prompt: str
        image_url: Optional[str] = None
    
    class IntentRequest(BaseModel):
        prompt: str
    
    @router.get("/health")
    async def health_check():
        """Check Printify API connection health"""
        client = get_client()
        return await client.get_health_report()
    
    @router.post("/parse-intent")
    async def parse_intent(request: IntentRequest):
        """Parse a natural language request into structured intent"""
        parser = IntentParser()
        intent = parser.parse(request.prompt)
        return intent.to_dict()
    
    @router.get("/search/{product_type}")
    async def search_catalog(product_type: str, limit: int = 5):
        """Search the Printify catalog for matching products"""
        client = get_client()
        matches = await client.search_catalog(product_type, limit)
        return [
            {
                "blueprint_id": m.blueprint_id,
                "title": m.title,
                "provider_id": m.print_provider_id,
                "provider_name": m.provider_name,
                "match_score": m.match_score,
                "category": m.category.value
            }
            for m in matches
        ]
    
    @router.post("/create")
    async def create_product(request: ProductRequest):
        """Create a product from natural language prompt"""
        orchestrator = get_orchestrator()
        result = await orchestrator.execute(
            user_input=request.prompt,
            pre_generated_image_url=request.image_url
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result)
        
        return result
    
    @router.get("/blueprints")
    async def list_blueprints(refresh: bool = False):
        """List all available blueprints from catalog"""
        client = get_client()
        blueprints = await client.get_all_blueprints(force_refresh=refresh)
        return {
            "count": len(blueprints),
            "blueprints": [
                {"id": bp.get("id"), "title": bp.get("title")}
                for bp in blueprints[:100]  # Return first 100
            ]
        }
    
    @router.post("/republish/{product_id}")
    async def republish_product(product_id: str):
        """
        Re-publish a product to Shopify with images.
        
        Use this endpoint to fix products that were published before 
        mockup images finished generating, resulting in missing images on Shopify.
        
        The endpoint will:
        1. Wait for mockups to be ready on Printify
        2. Re-publish to Shopify with full image sync
        """
        import os
        from ..tools.printify import PrintifyTools
        
        api_token = os.getenv("PRINTIFY_API_TOKEN")
        shop_id = os.getenv("PRINTIFY_SHOP_ID")
        
        if not api_token or not shop_id:
            raise HTTPException(status_code=500, detail={"error": "PRINTIFY_API_TOKEN or PRINTIFY_SHOP_ID not configured"})
        
        client = PrintifyTools(api_token=api_token, shop_id=shop_id)
        result = await client.republish_product(product_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result)
        
        return result
    
    @router.get("/products/{product_id}/images")
    async def check_product_images(product_id: str):
        """Check if a product has images ready on Printify and Shopify"""
        import os
        from ..tools.printify import PrintifyTools
        
        api_token = os.getenv("PRINTIFY_API_TOKEN")
        shop_id = os.getenv("PRINTIFY_SHOP_ID")
        
        if not api_token or not shop_id:
            raise HTTPException(status_code=500, detail={"error": "PRINTIFY_API_TOKEN or PRINTIFY_SHOP_ID not configured"})
        
        client = PrintifyTools(api_token=api_token, shop_id=shop_id)
        product = await client.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail={"error": "Product not found"})
        
        images = product.get("images", [])
        
        return {
            "product_id": product_id,
            "title": product.get("title", ""),
            "has_images": len(images) > 0,
            "image_count": len(images),
            "images": [
                {"src": img.get("src"), "is_default": img.get("is_default", False)}
                for img in images[:10]
            ],
            "note": "If images are present here but missing on Shopify, call POST /republish/{product_id}"
        }
    
    return router


# ═══════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    "EnhancedPrintifyClient",
    "PrintifyWorkflowOrchestrator", 
    "IntentParser",
    "ProductIntent",
    "ProductCategory",
    "BlueprintMatch",
    "ConnectionHealth",
    "create_printify_router"
]
