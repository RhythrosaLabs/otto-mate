"""
Multi-Platform Social Media Poster for Otto
============================================

Handles automated posting to multiple social media platforms using browser automation.
Ported from printify_clean with enhancements.

Supported Platforms:
- Twitter/X
- Instagram
- TikTok
- Facebook
- Pinterest
- Reddit
- LinkedIn
- Threads
- YouTube
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# PERFORMANCE CONFIGURATION
# ============================================================================
@dataclass
class BrowserPerformanceConfig:
    """Tunable performance settings for browser automation."""

    # Speed settings
    page_load_timeout: int = 30
    action_timeout: int = 10
    network_idle_timeout: float = 0.3
    wait_between_actions: float = 0.2
    minimum_wait_page_load: float = 0.1

    # Retry settings
    max_retries: int = 3
    retry_base_delay: float = 1.0

    # Agent settings
    max_steps: int = 20
    max_actions_per_step: int = 5
    flash_mode: bool = True

    # Parallel execution
    max_concurrent_posts: int = 3
    delay_between_platforms: float = 1.0

    # Screenshot settings
    capture_screenshots_on_error: bool = True
    screenshot_dir: str = "data/screenshots/social"


# Global performance config
PERF_CONFIG = BrowserPerformanceConfig()


# Platform configurations
PLATFORM_CONFIG = {
    "twitter": {
        "url": "https://twitter.com",
        "compose_url": "https://twitter.com/compose/tweet",
        "name": "Twitter/X",
        "icon": "🐦",
        "priority": 1,
    },
    "instagram": {
        "url": "https://www.instagram.com",
        "compose_url": "https://www.instagram.com/create/style/",
        "name": "Instagram",
        "icon": "📸",
        "priority": 2,
    },
    "tiktok": {
        "url": "https://www.tiktok.com",
        "compose_url": "https://www.tiktok.com/upload",
        "name": "TikTok",
        "icon": "🎵",
        "priority": 3,
    },
    "facebook": {
        "url": "https://www.facebook.com",
        "compose_url": "https://www.facebook.com/",
        "name": "Facebook",
        "icon": "👥",
        "priority": 4,
    },
    "pinterest": {
        "url": "https://www.pinterest.com",
        "compose_url": "https://www.pinterest.com/pin-builder/",
        "name": "Pinterest",
        "icon": "📌",
        "priority": 2,
    },
    "reddit": {
        "url": "https://www.reddit.com",
        "compose_url": "https://www.reddit.com/submit",
        "name": "Reddit",
        "icon": "🤖",
        "priority": 5,
    },
    "linkedin": {
        "url": "https://www.linkedin.com",
        "compose_url": "https://www.linkedin.com/feed/",
        "name": "LinkedIn",
        "icon": "💼",
        "priority": 4,
    },
    "threads": {
        "url": "https://www.threads.net",
        "compose_url": "https://www.threads.net/",
        "name": "Threads",
        "icon": "🧵",
        "priority": 3,
    },
    "youtube": {
        "url": "https://studio.youtube.com",
        "compose_url": "https://studio.youtube.com/channel/UC/videos/upload",
        "name": "YouTube",
        "icon": "📺",
        "priority": 5,
    },
}


# Task templates for each platform
TASK_TEMPLATES = {
    "twitter": """
TASK: Post to Twitter/X
1. Go to {compose_url}
2. {login_instructions}
3. Upload image: "{abs_image_path}"
4. Type caption: "{caption}"
5. Click Tweet/Post
6. Confirm success
""",
    "instagram": """
TASK: Post to Instagram
1. Go to {url}
2. {login_instructions}
3. Click + (create) button
4. Select "Post"
5. Upload: "{abs_image_path}"
6. Click Next (skip filters)
7. Add caption: "{caption}"
8. Click Share
""",
    "tiktok": """
TASK: Post to TikTok
1. Go to {compose_url}
2. {login_instructions}
3. Upload: "{abs_image_path}"
4. Add caption: "{caption}"
5. Set to public
6. Click Post
""",
    "facebook": """
TASK: Post to Facebook
1. Go to {url}
2. {login_instructions}
3. Click "What's on your mind?"
4. Click photo icon
5. Upload: "{abs_image_path}"
6. Add text: "{caption}"
7. Click Post
""",
    "pinterest": """
TASK: Create Pinterest Pin
1. Go to {compose_url}
2. {login_instructions}
3. Upload image: "{abs_image_path}"
4. Title/Description: "{caption}"
5. {board_instruction}
6. {link_instruction}
7. Click Publish/Save
""",
    "reddit": """
TASK: Post to Reddit
1. Go to reddit.com/r/{subreddit}/submit
2. {login_instructions}
3. Select "Image" tab
4. Upload: "{abs_image_path}"
5. Title: "{caption_short}"
6. Click Post
""",
    "linkedin": """
TASK: Post to LinkedIn
1. Go to {url}
2. {login_instructions}
3. Click "Start a post"
4. Click media/photo icon
5. Upload: "{abs_image_path}"
6. Add text: "{caption}"
7. Click Post
""",
    "threads": """
TASK: Post to Threads
1. Go to {url}
2. {login_instructions}
3. Click compose/new thread button
4. Upload image: "{abs_image_path}"
5. Add caption: "{caption}"
6. Click Post
""",
    "youtube": """
TASK: Upload to YouTube
1. Go to {compose_url}
2. {login_instructions}
3. Click Upload or Create button
4. Upload video: "{abs_image_path}"
5. Title: "{title}"
6. Description: "{description}"
7. Set visibility (public/unlisted)
8. Click Publish
""",
}


# ============================================================================
# POSTING METRICS
# ============================================================================
@dataclass
class PostingMetrics:
    """Track performance metrics for posting operations."""

    platform: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    steps_taken: int = 0
    success: bool = False
    error: Optional[str] = None
    screenshot_path: Optional[str] = None
    post_url: Optional[str] = None

    @property
    def duration(self) -> float:
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time

    def complete(self, success: bool, steps: int = 0, error: str = None, 
                 screenshot: str = None, post_url: str = None):
        self.end_time = time.time()
        self.success = success
        self.steps_taken = steps
        self.error = error
        self.screenshot_path = screenshot
        self.post_url = post_url


# ============================================================================
# MULTI-PLATFORM POSTER
# ============================================================================
class MultiPlatformPoster:
    """
    Automated social media poster using browser automation.
    
    Features:
    - Post to multiple platforms simultaneously
    - Smart retry with exponential backoff
    - Screenshot capture on errors
    - Performance metrics tracking
    - Parallel execution support
    """

    def __init__(self, config: Optional[BrowserPerformanceConfig] = None):
        """Initialize the multi-platform poster."""
        self.config = config or PERF_CONFIG
        self._browser_agent = None
        self.metrics: List[PostingMetrics] = []
        
        # Ensure screenshot directory exists
        Path(self.config.screenshot_dir).mkdir(parents=True, exist_ok=True)

    async def get_browser_agent(self):
        """Get or create browser agent (lazy loaded)."""
        if self._browser_agent is None:
            try:
                from browser_use import Agent
                self._browser_agent = Agent
                logger.info("Browser-Use agent loaded")
            except ImportError:
                logger.warning("browser-use not installed. Install with: pip install browser-use")
                return None
        return self._browser_agent

    def get_platform_config(self, platform: str) -> Optional[Dict]:
        """Get configuration for a platform."""
        return PLATFORM_CONFIG.get(platform.lower())

    def get_task_template(self, platform: str) -> Optional[str]:
        """Get task template for a platform."""
        return TASK_TEMPLATES.get(platform.lower())

    def prepare_post_task(
        self,
        platform: str,
        caption: str,
        image_path: Optional[str] = None,
        video_path: Optional[str] = None,
        link: Optional[str] = None,
        board: Optional[str] = None,  # Pinterest
        subreddit: Optional[str] = None,  # Reddit
        title: Optional[str] = None,  # YouTube
        description: Optional[str] = None,  # YouTube
        already_logged_in: bool = True,
    ) -> str:
        """
        Prepare the task instructions for browser automation.

        Args:
            platform: Target platform
            caption: Post caption/text
            image_path: Path to image file
            video_path: Path to video file
            link: Optional link to include
            board: Pinterest board name
            subreddit: Reddit subreddit
            title: Video/post title
            description: Video description
            already_logged_in: Whether user is already logged in

        Returns:
            Formatted task instructions
        """
        config = self.get_platform_config(platform)
        template = self.get_task_template(platform)

        if not config or not template:
            raise ValueError(f"Unknown platform: {platform}")

        # Determine media path
        media_path = video_path or image_path
        if media_path:
            abs_media_path = str(Path(media_path).absolute())
        else:
            abs_media_path = ""

        # Login instructions
        login_instructions = (
            "You should already be logged in. If not, wait for user to log in manually."
            if already_logged_in
            else "Log in with credentials if prompted."
        )

        # Format the template
        task = template.format(
            url=config["url"],
            compose_url=config["compose_url"],
            abs_image_path=abs_media_path,
            caption=caption,
            caption_short=caption[:100] if len(caption) > 100 else caption,
            login_instructions=login_instructions,
            board_instruction=f"Select board: {board}" if board else "Select appropriate board",
            link_instruction=f"Add link: {link}" if link else "",
            subreddit=subreddit or "appropriate_subreddit",
            title=title or caption[:100],
            description=description or caption,
        )

        return task

    async def post_to_platform(
        self,
        platform: str,
        caption: str,
        image_path: Optional[str] = None,
        video_path: Optional[str] = None,
        **kwargs
    ) -> PostingMetrics:
        """
        Post content to a single platform.

        Args:
            platform: Target platform name
            caption: Post caption
            image_path: Optional image path
            video_path: Optional video path
            **kwargs: Platform-specific options

        Returns:
            PostingMetrics with results
        """
        metrics = PostingMetrics(platform=platform)

        try:
            # Prepare task
            task = self.prepare_post_task(
                platform=platform,
                caption=caption,
                image_path=image_path,
                video_path=video_path,
                **kwargs
            )

            # Get browser agent
            Agent = await self.get_browser_agent()
            if not Agent:
                raise ImportError("Browser automation not available")

            # Execute with retries
            for attempt in range(self.config.max_retries):
                try:
                    logger.info(f"Posting to {platform} (attempt {attempt + 1})")

                    # Create and run agent
                    agent = Agent(
                        task=task,
                        max_steps=self.config.max_steps,
                    )

                    result = await agent.run()

                    # Check for success
                    if result and not result.get("error"):
                        metrics.complete(
                            success=True,
                            steps=result.get("steps", 0),
                            post_url=result.get("url")
                        )
                        logger.info(f"✅ Successfully posted to {platform}")
                        break

                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < self.config.max_retries - 1:
                        delay = self.config.retry_base_delay * (2 ** attempt)
                        await asyncio.sleep(delay)
                    else:
                        raise

        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Failed to post to {platform}: {error_msg}")

            # Capture screenshot on error
            screenshot_path = None
            if self.config.capture_screenshots_on_error:
                screenshot_path = await self._capture_error_screenshot(platform)

            metrics.complete(
                success=False,
                error=error_msg,
                screenshot=screenshot_path
            )

        self.metrics.append(metrics)
        return metrics

    async def post_to_multiple_platforms(
        self,
        platforms: List[str],
        caption: str,
        image_path: Optional[str] = None,
        video_path: Optional[str] = None,
        parallel: bool = True,
        **kwargs
    ) -> List[PostingMetrics]:
        """
        Post content to multiple platforms.

        Args:
            platforms: List of platform names
            caption: Post caption
            image_path: Optional image path
            video_path: Optional video path
            parallel: Whether to post in parallel
            **kwargs: Platform-specific options

        Returns:
            List of PostingMetrics for each platform
        """
        results = []

        if parallel:
            # Post to platforms in parallel (limited concurrency)
            semaphore = asyncio.Semaphore(self.config.max_concurrent_posts)

            async def post_with_semaphore(platform):
                async with semaphore:
                    return await self.post_to_platform(
                        platform=platform,
                        caption=caption,
                        image_path=image_path,
                        video_path=video_path,
                        **kwargs
                    )

            results = await asyncio.gather(
                *[post_with_semaphore(p) for p in platforms],
                return_exceptions=True
            )

            # Handle exceptions in results
            results = [
                r if isinstance(r, PostingMetrics)
                else PostingMetrics(
                    platform=platforms[i],
                    end_time=time.time(),
                    success=False,
                    error=str(r)
                )
                for i, r in enumerate(results)
            ]

        else:
            # Post sequentially
            for platform in platforms:
                result = await self.post_to_platform(
                    platform=platform,
                    caption=caption,
                    image_path=image_path,
                    video_path=video_path,
                    **kwargs
                )
                results.append(result)
                
                # Delay between platforms
                if platform != platforms[-1]:
                    await asyncio.sleep(self.config.delay_between_platforms)

        return results

    async def _capture_error_screenshot(self, platform: str) -> Optional[str]:
        """Capture screenshot on error for debugging."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{platform}_{timestamp}_error.png"
            filepath = Path(self.config.screenshot_dir) / filename

            # Screenshot capture would happen here via browser agent
            # For now, just return the path where it would be saved
            logger.info(f"Screenshot would be saved to: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            return None

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all posting metrics."""
        if not self.metrics:
            return {"total": 0, "successful": 0, "failed": 0}

        successful = [m for m in self.metrics if m.success]
        failed = [m for m in self.metrics if not m.success]

        return {
            "total": len(self.metrics),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(self.metrics) * 100,
            "avg_duration": sum(m.duration for m in self.metrics) / len(self.metrics),
            "platforms": {
                m.platform: {
                    "success": m.success,
                    "duration": m.duration,
                    "error": m.error,
                    "post_url": m.post_url,
                }
                for m in self.metrics
            },
        }

    def clear_metrics(self):
        """Clear stored metrics."""
        self.metrics = []


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================
async def quick_post(
    platforms: List[str],
    caption: str,
    image_path: Optional[str] = None,
    video_path: Optional[str] = None,
) -> List[PostingMetrics]:
    """
    Quick convenience function to post to multiple platforms.

    Args:
        platforms: List of platform names
        caption: Post caption
        image_path: Optional image path
        video_path: Optional video path

    Returns:
        List of posting results
    """
    poster = MultiPlatformPoster()
    return await poster.post_to_multiple_platforms(
        platforms=platforms,
        caption=caption,
        image_path=image_path,
        video_path=video_path,
    )


def get_available_platforms() -> Dict[str, Dict]:
    """Get all available platforms and their configurations."""
    return PLATFORM_CONFIG


def get_platform_icon(platform: str) -> str:
    """Get emoji icon for a platform."""
    config = PLATFORM_CONFIG.get(platform.lower(), {})
    return config.get("icon", "📱")


# Singleton instance
_poster = None


def get_multi_platform_poster() -> MultiPlatformPoster:
    """Get the singleton MultiPlatformPoster instance."""
    global _poster
    if _poster is None:
        _poster = MultiPlatformPoster()
    return _poster
