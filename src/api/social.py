"""
Social Media Posting API Router
================================

REST API endpoints for multi-platform social media posting.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, List, Dict
from pydantic import BaseModel
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/social", tags=["social"])


# Request/Response models
class PostRequest(BaseModel):
    platforms: List[str]
    caption: str
    image_path: Optional[str] = None
    video_path: Optional[str] = None
    link: Optional[str] = None
    board: Optional[str] = None  # Pinterest
    subreddit: Optional[str] = None  # Reddit
    title: Optional[str] = None  # YouTube
    description: Optional[str] = None  # YouTube
    parallel: bool = True


class SinglePostRequest(BaseModel):
    platform: str
    caption: str
    image_path: Optional[str] = None
    video_path: Optional[str] = None
    link: Optional[str] = None
    board: Optional[str] = None
    subreddit: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None


@router.get("/platforms")
async def get_platforms():
    """Get all available social media platforms."""
    try:
        from src.tools.social_poster import get_available_platforms
        platforms = get_available_platforms()
        return {
            "success": True,
            "platforms": [
                {
                    "id": pid,
                    "name": pconfig["name"],
                    "icon": pconfig["icon"],
                    "url": pconfig["url"],
                }
                for pid, pconfig in platforms.items()
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get platforms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/post")
async def post_to_platforms(request: PostRequest, background_tasks: BackgroundTasks):
    """
    Post content to multiple social media platforms.
    
    Supports: twitter, instagram, tiktok, facebook, pinterest, reddit, linkedin, threads, youtube
    """
    try:
        from src.tools.social_poster import get_multi_platform_poster
        poster = get_multi_platform_poster()
        
        # Validate platforms
        valid_platforms = ["twitter", "instagram", "tiktok", "facebook", 
                         "pinterest", "reddit", "linkedin", "threads", "youtube"]
        for p in request.platforms:
            if p.lower() not in valid_platforms:
                raise HTTPException(status_code=400, detail=f"Invalid platform: {p}")
        
        # Post to platforms
        results = await poster.post_to_multiple_platforms(
            platforms=request.platforms,
            caption=request.caption,
            image_path=request.image_path,
            video_path=request.video_path,
            link=request.link,
            board=request.board,
            subreddit=request.subreddit,
            title=request.title,
            description=request.description,
            parallel=request.parallel,
        )
        
        # Format results
        formatted_results = []
        for r in results:
            formatted_results.append({
                "platform": r.platform,
                "success": r.success,
                "duration": r.duration,
                "error": r.error,
                "post_url": r.post_url,
            })
        
        success_count = sum(1 for r in results if r.success)
        
        return {
            "success": True,
            "total": len(results),
            "successful": success_count,
            "failed": len(results) - success_count,
            "results": formatted_results,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to post to platforms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/post/{platform}")
async def post_to_single_platform(platform: str, request: SinglePostRequest):
    """Post content to a single social media platform."""
    try:
        from src.tools.social_poster import get_multi_platform_poster
        poster = get_multi_platform_poster()
        
        result = await poster.post_to_platform(
            platform=platform,
            caption=request.caption,
            image_path=request.image_path,
            video_path=request.video_path,
            link=request.link,
            board=request.board,
            subreddit=request.subreddit,
            title=request.title,
            description=request.description,
        )
        
        return {
            "success": result.success,
            "platform": result.platform,
            "duration": result.duration,
            "error": result.error,
            "post_url": result.post_url,
        }
        
    except Exception as e:
        logger.error(f"Failed to post to {platform}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_posting_metrics():
    """Get posting metrics summary."""
    try:
        from src.tools.social_poster import get_multi_platform_poster
        poster = get_multi_platform_poster()
        summary = poster.get_metrics_summary()
        return {"success": True, "metrics": summary}
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/metrics")
async def clear_posting_metrics():
    """Clear posting metrics."""
    try:
        from src.tools.social_poster import get_multi_platform_poster
        poster = get_multi_platform_poster()
        poster.clear_metrics()
        return {"success": True, "message": "Metrics cleared"}
    except Exception as e:
        logger.error(f"Failed to clear metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task-template/{platform}")
async def get_task_template(platform: str):
    """Get the browser automation task template for a platform."""
    try:
        from src.tools.social_poster import get_multi_platform_poster, TASK_TEMPLATES
        
        template = TASK_TEMPLATES.get(platform.lower())
        if not template:
            raise HTTPException(status_code=404, detail=f"No template for platform: {platform}")
        
        return {
            "success": True,
            "platform": platform,
            "template": template,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task template: {e}")
        raise HTTPException(status_code=500, detail=str(e))
