"""
Browser Stealth Configuration
==============================

Centralized stealth/anti-detection configuration for browser-use.
Provides BrowserProfile presets for different use cases:
- General browsing (standard stealth)
- Social media (aggressive anti-bot bypass)
- Scraping (headless-optimized)

Uses browser-use 0.11.x BrowserProfile with:
- Auto-detection evasion (navigator.webdriver, automation flags)
- Default extensions (uBlock Origin, cookie handler, ClearURLs)
- Proxy support with rotation
- Real Chrome profile reuse for session persistence
- playwright-stealth integration for additional JS evasions
"""

import logging
import os
import platform
import random
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Try to import browser-use stealth components
try:
    from browser_use import BrowserProfile
    from browser_use.browser.profile import ProxySettings
    BROWSER_USE_AVAILABLE = True
except ImportError:
    BROWSER_USE_AVAILABLE = False
    logger.warning("browser-use not installed. Run: pip install browser-use")

# Try to import playwright-stealth
try:
    from playwright_stealth import Stealth
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False
    logger.info("playwright-stealth not installed. Run: pip install playwright-stealth")


# ============================================================================
# USER AGENT POOLS
# ============================================================================

# Realistic user agents for different platforms
DESKTOP_USER_AGENTS = [
    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    # Chrome on Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

MOBILE_USER_AGENTS = [
    # Chrome on Android
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
]


# ============================================================================
# CHROME PATH DETECTION
# ============================================================================

def find_chrome_path() -> Optional[str]:
    """Find the system Chrome binary path."""
    system = platform.system()
    
    paths = {
        "Darwin": [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ],
        "Linux": [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
        ],
        "Windows": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ],
    }
    
    for path in paths.get(system, []):
        if Path(path).exists():
            return path
    
    # Check env var
    return os.getenv("CHROME_PATH")


def find_chrome_profile_dir() -> Optional[str]:
    """Find the default Chrome user data directory."""
    system = platform.system()
    home = Path.home()
    
    dirs = {
        "Darwin": home / "Library" / "Application Support" / "Google" / "Chrome",
        "Linux": home / ".config" / "google-chrome",
        "Windows": home / "AppData" / "Local" / "Google" / "Chrome" / "User Data",
    }
    
    path = dirs.get(system)
    if path and path.exists():
        return str(path)
    return None


# ============================================================================
# STEALTH PROFILE PRESETS
# ============================================================================

def create_stealth_profile(
    mode: str = "standard",
    headless: bool = False,
    use_real_chrome: bool = True,
    use_real_profile: bool = False,
    proxy_server: Optional[str] = None,
    proxy_username: Optional[str] = None,
    proxy_password: Optional[str] = None,
    user_agent: Optional[str] = None,
    allowed_domains: Optional[list] = None,
    keep_alive: bool = False,
    extra_args: Optional[list] = None,
) -> "BrowserProfile":
    """
    Create a stealth BrowserProfile with anti-detection features.
    
    Modes:
        standard:    Default stealth - extensions + automation masking
        social:      Aggressive stealth for social media (headed, real Chrome, random delays)
        scraping:    Optimized for data extraction (headless-safe, proxy-ready)
        maximum:     All stealth features enabled (real Chrome + profile + proxy + extensions)
    
    Args:
        mode: Stealth preset - 'standard', 'social', 'scraping', 'maximum'
        headless: Run headless (False is less detectable)
        use_real_chrome: Use system Chrome instead of Playwright's Chromium
        use_real_profile: Use Chrome's real profile (has cookies/logins)
        proxy_server: Proxy URL (e.g., 'http://host:8080' or 'socks5://host:1080')
        proxy_username: Proxy auth username
        proxy_password: Proxy auth password
        user_agent: Custom user agent string (random if None)
        allowed_domains: Restrict navigation to these domains
        keep_alive: Keep browser open after agent finishes
        extra_args: Additional Chrome CLI arguments
    
    Returns:
        Configured BrowserProfile with anti-detection features
    """
    if not BROWSER_USE_AVAILABLE:
        raise RuntimeError("browser-use not installed. Run: pip install browser-use")
    
    # Base configuration
    profile_kwargs: Dict[str, Any] = {
        "headless": headless,
        "enable_default_extensions": True,  # uBlock, cookie handler, ClearURLs
        "highlight_elements": True,
        "minimum_wait_page_load_time": 0.5,
        "wait_between_actions": 0.3,
    }
    
    # Mode-specific overrides
    if mode == "social":
        # Social media: headed, real Chrome, more human-like timing
        profile_kwargs.update({
            "headless": False,  # Always headed for social media
            "minimum_wait_page_load_time": 1.0,
            "wait_between_actions": 0.5,  # More human-like delays
            "keep_alive": True,  # Keep session for multi-step social interactions
        })
        use_real_chrome = True
        
    elif mode == "scraping":
        # Scraping: can be headless, faster timing
        profile_kwargs.update({
            "headless": headless,
            "minimum_wait_page_load_time": 0.25,
            "wait_between_actions": 0.1,
        })
        
    elif mode == "maximum":
        # Maximum stealth: everything enabled
        profile_kwargs.update({
            "headless": False,
            "minimum_wait_page_load_time": 1.5,
            "wait_between_actions": 0.8,
            "keep_alive": True,
        })
        use_real_chrome = True
        use_real_profile = True
    
    # Real Chrome binary
    if use_real_chrome:
        chrome_path = find_chrome_path()
        if chrome_path:
            profile_kwargs["executable_path"] = chrome_path
            logger.info(f"Using real Chrome at: {chrome_path}")
        else:
            logger.warning("System Chrome not found, falling back to Playwright Chromium")
    
    # Real Chrome profile (reuse existing cookies/sessions)
    if use_real_profile:
        profile_dir = find_chrome_profile_dir()
        if profile_dir:
            # Use a dedicated sub-profile to avoid conflicts with user sessions
            otto_profile_dir = Path(profile_dir).parent / "Otto-Browser-Profile"
            otto_profile_dir.mkdir(parents=True, exist_ok=True)
            profile_kwargs["user_data_dir"] = str(otto_profile_dir)
            profile_kwargs["profile_directory"] = "Default"
            logger.info(f"Using Chrome profile: {otto_profile_dir}")
    
    # Proxy configuration
    if proxy_server:
        proxy_kwargs = {"server": proxy_server}
        if proxy_username:
            proxy_kwargs["username"] = proxy_username
        if proxy_password:
            proxy_kwargs["password"] = proxy_password
        profile_kwargs["proxy"] = ProxySettings(**proxy_kwargs)
        logger.info(f"Using proxy: {proxy_server}")
    else:
        # Check env vars for proxy
        env_proxy = os.getenv("BROWSER_PROXY_SERVER")
        if env_proxy:
            proxy_kwargs = {"server": env_proxy}
            env_user = os.getenv("BROWSER_PROXY_USERNAME")
            env_pass = os.getenv("BROWSER_PROXY_PASSWORD")
            if env_user:
                proxy_kwargs["username"] = env_user
            if env_pass:
                proxy_kwargs["password"] = env_pass
            profile_kwargs["proxy"] = ProxySettings(**proxy_kwargs)
            logger.info(f"Using proxy from env: {env_proxy}")
    
    # User agent
    if user_agent:
        profile_kwargs["user_agent"] = user_agent
    elif mode in ("social", "maximum"):
        profile_kwargs["user_agent"] = random.choice(DESKTOP_USER_AGENTS)
    
    # Domain restrictions
    if allowed_domains:
        profile_kwargs["allowed_domains"] = allowed_domains
    
    # Keep alive override
    if keep_alive:
        profile_kwargs["keep_alive"] = True
    
    # Extra Chrome args for stealth
    stealth_args = []
    
    # Additional anti-detection args beyond browser-use defaults
    if mode in ("social", "maximum"):
        stealth_args.extend([
            "--disable-features=IsolateOrigins,site-per-process",
            "--flag-switches-begin",
            "--flag-switches-end",
        ])
    
    if extra_args:
        stealth_args.extend(extra_args)
    
    if stealth_args:
        profile_kwargs["args"] = stealth_args
    
    # Create downloads directory
    downloads_dir = Path("./data/browser_downloads")
    downloads_dir.mkdir(parents=True, exist_ok=True)
    profile_kwargs["downloads_path"] = str(downloads_dir)
    
    return BrowserProfile(**profile_kwargs)


# ============================================================================
# SOCIAL MEDIA STEALTH HELPERS
# ============================================================================

# Platform-specific stealth configurations
SOCIAL_PLATFORM_DOMAINS = {
    "twitter": ["*.twitter.com", "*.x.com", "*.twimg.com"],
    "instagram": ["*.instagram.com", "*.cdninstagram.com", "*.fbcdn.net"],
    "tiktok": ["*.tiktok.com", "*.tiktokcdn.com"],
    "facebook": ["*.facebook.com", "*.fbcdn.net", "*.fb.com"],
    "linkedin": ["*.linkedin.com", "*.licdn.com"],
    "pinterest": ["*.pinterest.com", "*.pinimg.com"],
    "reddit": ["*.reddit.com", "*.redd.it", "*.redditstatic.com"],
    "youtube": ["*.youtube.com", "*.googlevideo.com", "*.ytimg.com"],
    "threads": ["*.threads.net", "*.cdninstagram.com"],
}


def create_social_media_profile(
    platform: str,
    proxy_server: Optional[str] = None,
    proxy_username: Optional[str] = None,
    proxy_password: Optional[str] = None,
    use_real_profile: bool = False,
) -> "BrowserProfile":
    """
    Create a stealth profile optimized for a specific social media platform.
    
    Uses 'social' mode with platform-appropriate domain restrictions and
    anti-detection features optimized for that platform's bot detection.
    
    Args:
        platform: Platform name (twitter, instagram, tiktok, etc.)
        proxy_server: Proxy URL (residential proxies recommended for social media)
        proxy_username: Proxy auth username
        proxy_password: Proxy auth password
        use_real_profile: Use Chrome's real profile (has cookies/logins)
    
    Returns:
        BrowserProfile configured for the specific platform
    """
    platform_lower = platform.lower()
    domains = SOCIAL_PLATFORM_DOMAINS.get(platform_lower)
    
    return create_stealth_profile(
        mode="social",
        headless=False,  # Always headed for social
        use_real_chrome=True,
        use_real_profile=use_real_profile,
        proxy_server=proxy_server,
        proxy_username=proxy_username,
        proxy_password=proxy_password,
        allowed_domains=domains,  # Restrict to platform domains
        keep_alive=True,
    )


# ============================================================================
# HUMAN-LIKE BEHAVIOR HELPERS  
# ============================================================================

async def random_delay(min_sec: float = 0.5, max_sec: float = 3.0):
    """Add a random human-like delay."""
    import asyncio
    delay = random.uniform(min_sec, max_sec)
    await asyncio.sleep(delay)
    return delay
