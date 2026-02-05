"""
YouTube Integration Tools
=========================

Tools for YouTube video upload and management.
Requires OAuth2 credentials for upload functionality.
"""

import logging
import aiohttp
import os
from typing import Optional, Dict, Any, List
from pathlib import Path
from .core import tool, ToolBase

logger = logging.getLogger(__name__)


class YouTubeTools(ToolBase):
    """YouTube video management tools."""
    
    def __init__(
        self,
        api_key: str = None,
        client_id: str = None,
        client_secret: str = None,
        refresh_token: str = None
    ):
        """
        Initialize YouTube tools.
        
        For read-only operations (search, get video info): only api_key needed
        For uploads and management: OAuth credentials required (client_id, client_secret, refresh_token)
        """
        self.api_key = api_key
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token = None
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
        logger.info(f"YouTube tools initialized (API key: {bool(api_key)}, OAuth: {bool(client_id and client_secret)})")
    
    async def _get_access_token(self) -> str:
        """Get OAuth access token using refresh token."""
        if self.access_token:
            return self.access_token
        
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            raise Exception("YouTube OAuth credentials not configured. Need client_id, client_secret, and refresh_token for uploads.")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                    "grant_type": "refresh_token"
                }
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"Failed to get YouTube access token: {error}")
                
                data = await response.json()
                self.access_token = data.get("access_token")
                return self.access_token
    
    @tool(
        name="youtube_search",
        description="Search YouTube videos",
        category="youtube"
    )
    async def search_videos(
        self,
        query: str,
        max_results: int = 10,
        order: str = "relevance"  # relevance, date, viewCount, rating
    ) -> Dict[str, Any]:
        """
        Search for YouTube videos.
        
        Args:
            query: Search query
            max_results: Maximum number of results (default 10, max 50)
            order: Sort order - relevance, date, viewCount, rating
            
        Returns:
            Dict with search results
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "YouTube API key not configured",
                "message": "Please add YOUTUBE_API_KEY to your environment variables"
            }
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/search"
                params = {
                    "key": self.api_key,
                    "q": query,
                    "part": "snippet",
                    "type": "video",
                    "maxResults": min(max_results, 50),
                    "order": order
                }
                
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        error = await response.json()
                        return {
                            "success": False,
                            "error": error.get("error", {}).get("message", "Unknown error")
                        }
                    
                    data = await response.json()
                    videos = []
                    
                    for item in data.get("items", []):
                        snippet = item.get("snippet", {})
                        videos.append({
                            "video_id": item.get("id", {}).get("videoId"),
                            "title": snippet.get("title"),
                            "description": snippet.get("description"),
                            "channel": snippet.get("channelTitle"),
                            "published_at": snippet.get("publishedAt"),
                            "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                            "url": f"https://www.youtube.com/watch?v={item.get('id', {}).get('videoId')}"
                        })
                    
                    return {
                        "success": True,
                        "query": query,
                        "total_results": data.get("pageInfo", {}).get("totalResults", 0),
                        "videos": videos
                    }
                    
        except Exception as e:
            logger.error(f"YouTube search failed: {e}")
            return {"success": False, "error": str(e)}
    
    @tool(
        name="youtube_get_video",
        description="Get details of a YouTube video",
        category="youtube"
    )
    async def get_video(self, video_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a YouTube video.
        
        Args:
            video_id: YouTube video ID (e.g., 'dQw4w9WgXcQ')
            
        Returns:
            Dict with video details
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "YouTube API key not configured"
            }
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/videos"
                params = {
                    "key": self.api_key,
                    "id": video_id,
                    "part": "snippet,statistics,contentDetails"
                }
                
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    
                    if not data.get("items"):
                        return {"success": False, "error": "Video not found"}
                    
                    video = data["items"][0]
                    snippet = video.get("snippet", {})
                    stats = video.get("statistics", {})
                    content = video.get("contentDetails", {})
                    
                    return {
                        "success": True,
                        "video_id": video_id,
                        "title": snippet.get("title"),
                        "description": snippet.get("description"),
                        "channel": snippet.get("channelTitle"),
                        "channel_id": snippet.get("channelId"),
                        "published_at": snippet.get("publishedAt"),
                        "tags": snippet.get("tags", []),
                        "thumbnail": snippet.get("thumbnails", {}).get("maxres", {}).get("url") or 
                                    snippet.get("thumbnails", {}).get("high", {}).get("url"),
                        "duration": content.get("duration"),
                        "view_count": int(stats.get("viewCount", 0)),
                        "like_count": int(stats.get("likeCount", 0)),
                        "comment_count": int(stats.get("commentCount", 0)),
                        "url": f"https://www.youtube.com/watch?v={video_id}"
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get video: {e}")
            return {"success": False, "error": str(e)}
    
    @tool(
        name="youtube_upload_video",
        description="Upload a video to YouTube. Requires OAuth credentials.",
        category="youtube"
    )
    async def upload_video(
        self,
        video_path: str,
        title: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        category_id: str = "22",  # 22 = People & Blogs
        privacy_status: str = "private",  # private, public, unlisted
        made_for_kids: bool = False
    ) -> Dict[str, Any]:
        """
        Upload a video to YouTube.
        
        Note: Requires OAuth credentials (client_id, client_secret, refresh_token)
        
        Args:
            video_path: Path to the video file
            title: Video title
            description: Video description
            tags: List of tags
            category_id: YouTube category ID (22 = People & Blogs, 24 = Entertainment, etc.)
            privacy_status: private, public, or unlisted
            made_for_kids: Whether the video is made for kids
            
        Returns:
            Dict with upload result
        """
        # Check OAuth credentials
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            return {
                "success": False,
                "error": "YouTube OAuth credentials not configured",
                "message": "To upload videos, you need to set up OAuth2 credentials:\n" +
                          "1. Go to Google Cloud Console\n" +
                          "2. Create OAuth 2.0 credentials\n" +
                          "3. Set YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, and YOUTUBE_REFRESH_TOKEN\n" +
                          "4. The refresh token requires running the OAuth flow once"
            }
        
        # Check video file exists
        video_file = Path(video_path)
        if not video_file.exists():
            return {
                "success": False,
                "error": f"Video file not found: {video_path}"
            }
        
        try:
            # Get access token
            access_token = await self._get_access_token()
            
            # Prepare video metadata
            metadata = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags or [],
                    "categoryId": category_id
                },
                "status": {
                    "privacyStatus": privacy_status,
                    "selfDeclaredMadeForKids": made_for_kids
                }
            }
            
            # Upload using resumable upload
            async with aiohttp.ClientSession() as session:
                # Step 1: Initialize upload
                init_url = "https://www.googleapis.com/upload/youtube/v3/videos"
                init_params = {"uploadType": "resumable", "part": "snippet,status"}
                
                async with session.post(
                    init_url,
                    params=init_params,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                        "X-Upload-Content-Type": "video/*",
                        "X-Upload-Content-Length": str(video_file.stat().st_size)
                    },
                    json=metadata
                ) as init_response:
                    if init_response.status not in [200, 308]:
                        error = await init_response.text()
                        return {"success": False, "error": f"Upload init failed: {error}"}
                    
                    upload_url = init_response.headers.get("Location")
                
                # Step 2: Upload video content
                with open(video_file, "rb") as f:
                    video_content = f.read()
                
                async with session.put(
                    upload_url,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "video/*"
                    },
                    data=video_content
                ) as upload_response:
                    if upload_response.status not in [200, 201]:
                        error = await upload_response.text()
                        return {"success": False, "error": f"Upload failed: {error}"}
                    
                    result = await upload_response.json()
                    video_id = result.get("id")
                    
                    return {
                        "success": True,
                        "video_id": video_id,
                        "title": title,
                        "privacy_status": privacy_status,
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "studio_url": f"https://studio.youtube.com/video/{video_id}/edit"
                    }
                    
        except Exception as e:
            logger.error(f"YouTube upload failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": "Video upload failed. Check OAuth credentials and API quota."
            }
    
    @tool(
        name="youtube_list_my_videos",
        description="List videos from your YouTube channel. Requires OAuth.",
        category="youtube"
    )
    async def list_my_videos(self, max_results: int = 25) -> Dict[str, Any]:
        """
        List videos from the authenticated user's channel.
        
        Args:
            max_results: Maximum number of videos to return
            
        Returns:
            Dict with list of videos
        """
        try:
            access_token = await self._get_access_token()
            
            async with aiohttp.ClientSession() as session:
                # First get the channel's uploads playlist
                url = f"{self.base_url}/channels"
                params = {
                    "part": "contentDetails",
                    "mine": "true"
                }
                
                async with session.get(
                    url,
                    params=params,
                    headers={"Authorization": f"Bearer {access_token}"}
                ) as response:
                    data = await response.json()
                    
                    if not data.get("items"):
                        return {"success": False, "error": "No channel found"}
                    
                    uploads_playlist = data["items"][0].get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
                
                # Get videos from uploads playlist
                url = f"{self.base_url}/playlistItems"
                params = {
                    "part": "snippet",
                    "playlistId": uploads_playlist,
                    "maxResults": max_results
                }
                
                async with session.get(
                    url,
                    params=params,
                    headers={"Authorization": f"Bearer {access_token}"}
                ) as response:
                    data = await response.json()
                    
                    videos = []
                    for item in data.get("items", []):
                        snippet = item.get("snippet", {})
                        video_id = snippet.get("resourceId", {}).get("videoId")
                        videos.append({
                            "video_id": video_id,
                            "title": snippet.get("title"),
                            "description": snippet.get("description"),
                            "published_at": snippet.get("publishedAt"),
                            "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                            "url": f"https://www.youtube.com/watch?v={video_id}"
                        })
                    
                    return {
                        "success": True,
                        "videos": videos,
                        "count": len(videos)
                    }
                    
        except Exception as e:
            logger.error(f"Failed to list videos: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
_youtube_tools = None

def get_youtube_tools() -> YouTubeTools:
    """Get or create YouTube tools instance."""
    global _youtube_tools
    if _youtube_tools is None:
        from ..utils.config import get_settings
        settings = get_settings()
        _youtube_tools = YouTubeTools(
            api_key=settings.youtube_api_key,
            client_id=settings.youtube_client_id,
            client_secret=settings.youtube_client_secret
        )
    return _youtube_tools
