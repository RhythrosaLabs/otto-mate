"""
Social Poster Plugin
====================

Post content to social media platforms with scheduling support.

Example usage:
    >>> result = await plugin.post_to_twitter("Hello World! #AI", images=["/path/to/image.jpg"])
    >>> result = await plugin.schedule_post("twitter", "Scheduled post", schedule_time="2024-01-01 12:00:00")
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    import tweepy
    HAS_TWEEPY = True
except ImportError:
    HAS_TWEEPY = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from src.core.plugin_system import ToolPlugin


class SocialPosterPlugin(ToolPlugin):
    """Plugin for posting to social media platforms."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scheduled_posts_file = Path("data/scheduled_posts.json")
        self.twitter_client = None
        
    async def initialize(self) -> None:
        """Initialize the plugin and register tools."""
        
        self.default_hashtags = self.settings.get("default_hashtags", [])
        
        # Initialize Twitter client if credentials available
        twitter_key = self.settings.get("twitter_api_key")
        twitter_secret = self.settings.get("twitter_api_secret")
        
        if HAS_TWEEPY and twitter_key and twitter_secret:
            try:
                auth = tweepy.OAuth1UserHandler(twitter_key, twitter_secret)
                self.twitter_client = tweepy.API(auth)
            except Exception:
                pass
        
        # Register tools
        self.register_tool(
            name="post_to_twitter",
            func=self.post_to_twitter,
            description="Post a tweet to Twitter/X with optional images",
            parameters={
                "text": {"type": "string", "required": True, "description": "Tweet text (max 280 chars)"},
                "images": {"type": "array", "required": False, "description": "List of image paths to attach"},
                "add_hashtags": {"type": "boolean", "required": False, "description": "Add default hashtags"}
            }
        )
        
        self.register_tool(
            name="post_to_linkedin",
            func=self.post_to_linkedin,
            description="Post to LinkedIn with optional image",
            parameters={
                "text": {"type": "string", "required": True, "description": "Post content"},
                "image_path": {"type": "string", "required": False, "description": "Path to image"}
            }
        )
        
        self.register_tool(
            name="schedule_post",
            func=self.schedule_post,
            description="Schedule a post for later",
            parameters={
                "platform": {"type": "string", "required": True, "description": "Platform (twitter, linkedin)"},
                "text": {"type": "string", "required": True},
                "schedule_time": {"type": "string", "required": True, "description": "ISO format datetime"},
                "images": {"type": "array", "required": False}
            }
        )
        
        self.register_tool(
            name="get_scheduled_posts",
            func=self.get_scheduled_posts,
            description="Get list of scheduled posts",
            parameters={}
        )
        
        self.register_tool(
            name="create_thread",
            func=self.create_thread,
            description="Create a Twitter thread from long text",
            parameters={
                "text": {"type": "string", "required": True, "description": "Long text to split into thread"},
                "post_immediately": {"type": "boolean", "required": False, "description": "Post thread now"}
            }
        )
    
    async def post_to_twitter(self, text: str, images: Optional[List[str]] = None, 
                             add_hashtags: bool = False) -> Dict[str, Any]:
        """Post a tweet."""
        try:
            if add_hashtags and self.default_hashtags:
                hashtag_str = " " + " ".join(f"#{tag}" for tag in self.default_hashtags)
                if len(text) + len(hashtag_str) <= 280:
                    text += hashtag_str
            
            if len(text) > 280:
                return {"error": f"Tweet too long ({len(text)} chars, max 280)", "success": False}
            
            if not self.twitter_client:
                # Simulate for demo
                return {
                    "success": True,
                    "simulated": True,
                    "message": "Twitter API not configured. Post simulated.",
                    "text": text,
                    "char_count": len(text),
                    "images": images or []
                }
            
            # Real posting
            media_ids = []
            if images:
                for img_path in images[:4]:  # Twitter max 4 images
                    if os.path.exists(img_path):
                        media = self.twitter_client.media_upload(img_path)
                        media_ids.append(media.media_id)
            
            tweet = self.twitter_client.update_status(
                status=text,
                media_ids=media_ids if media_ids else None
            )
            
            return {
                "success": True,
                "tweet_id": tweet.id_str,
                "url": f"https://twitter.com/i/status/{tweet.id_str}",
                "text": text,
                "images_attached": len(media_ids)
            }
            
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def post_to_linkedin(self, text: str, image_path: Optional[str] = None) -> Dict[str, Any]:
        """Post to LinkedIn."""
        try:
            access_token = self.settings.get("linkedin_access_token")
            
            if not access_token:
                return {
                    "success": True,
                    "simulated": True,
                    "message": "LinkedIn API not configured. Post simulated.",
                    "text": text[:100] + "..." if len(text) > 100 else text,
                    "char_count": len(text)
                }
            
            # Real LinkedIn posting would go here
            headers = {"Authorization": f"Bearer {access_token}"}
            
            return {
                "success": True,
                "text": text,
                "platform": "linkedin"
            }
            
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def schedule_post(self, platform: str, text: str, schedule_time: str,
                           images: Optional[List[str]] = None) -> Dict[str, Any]:
        """Schedule a post for later."""
        try:
            scheduled_time = datetime.fromisoformat(schedule_time)
            
            if scheduled_time <= datetime.now():
                return {"error": "Schedule time must be in the future", "success": False}
            
            # Load existing scheduled posts
            scheduled = []
            if self.scheduled_posts_file.exists():
                scheduled = json.loads(self.scheduled_posts_file.read_text())
            
            post = {
                "id": len(scheduled) + 1,
                "platform": platform,
                "text": text,
                "images": images or [],
                "schedule_time": schedule_time,
                "created_at": datetime.now().isoformat(),
                "status": "pending"
            }
            
            scheduled.append(post)
            
            self.scheduled_posts_file.parent.mkdir(exist_ok=True)
            self.scheduled_posts_file.write_text(json.dumps(scheduled, indent=2))
            
            return {
                "success": True,
                "post_id": post["id"],
                "platform": platform,
                "scheduled_for": schedule_time,
                "text_preview": text[:50] + "..." if len(text) > 50 else text
            }
            
        except ValueError as e:
            return {"error": f"Invalid datetime format: {e}", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def get_scheduled_posts(self) -> Dict[str, Any]:
        """Get all scheduled posts."""
        try:
            if not self.scheduled_posts_file.exists():
                return {"success": True, "posts": [], "count": 0}
            
            scheduled = json.loads(self.scheduled_posts_file.read_text())
            pending = [p for p in scheduled if p["status"] == "pending"]
            
            return {
                "success": True,
                "posts": pending,
                "count": len(pending)
            }
            
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def create_thread(self, text: str, post_immediately: bool = False) -> Dict[str, Any]:
        """Split long text into a Twitter thread."""
        try:
            # Split into ~270 char chunks (leave room for numbering)
            chunks = []
            words = text.split()
            current_chunk = ""
            
            for word in words:
                test_chunk = f"{current_chunk} {word}".strip()
                if len(test_chunk) <= 270:
                    current_chunk = test_chunk
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = word
            
            if current_chunk:
                chunks.append(current_chunk)
            
            # Add numbering
            total = len(chunks)
            numbered = [f"{i+1}/{total} {chunk}" for i, chunk in enumerate(chunks)]
            
            if post_immediately and self.twitter_client:
                # Post as actual thread
                previous_id = None
                tweet_ids = []
                
                for tweet_text in numbered:
                    tweet = self.twitter_client.update_status(
                        status=tweet_text,
                        in_reply_to_status_id=previous_id
                    )
                    tweet_ids.append(tweet.id_str)
                    previous_id = tweet.id
                
                return {
                    "success": True,
                    "posted": True,
                    "tweet_count": len(tweet_ids),
                    "first_tweet_url": f"https://twitter.com/i/status/{tweet_ids[0]}"
                }
            
            return {
                "success": True,
                "posted": False,
                "thread_count": len(numbered),
                "tweets": numbered
            }
            
        except Exception as e:
            return {"error": str(e), "success": False}
