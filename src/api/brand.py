"""
Brand Brain API Router
======================

REST API endpoints for brand asset management and brand-aware content.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, List
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/brand", tags=["brand"])


# Request/Response models
class BrandProfileUpdate(BaseModel):
    brand_name: Optional[str] = None
    tagline: Optional[str] = None
    primary_colors: Optional[List[str]] = None
    secondary_colors: Optional[List[str]] = None
    tone: Optional[List[str]] = None
    avoid: Optional[List[str]] = None
    voice: Optional[str] = None
    hashtags: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    examples: Optional[List[str]] = None


class PromptEnhanceRequest(BaseModel):
    prompt: str
    content_type: str = "social_post"


class ColorGradeRequest(BaseModel):
    image_path: str
    intensity: float = 0.12


class LogoApplyRequest(BaseModel):
    video_path: str
    position: str = "bottom-right"


@router.get("/profile")
async def get_brand_profile():
    """Get the current brand profile."""
    try:
        from src.tools.brand_brain import get_brand_brain
        brain = get_brand_brain()
        profile = brain.load_profile()
        return {"success": True, "profile": profile}
    except Exception as e:
        logger.error(f"Failed to get brand profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profile")
async def update_brand_profile(updates: BrandProfileUpdate):
    """Update the brand profile."""
    try:
        from src.tools.brand_brain import get_brand_brain
        brain = get_brand_brain()
        
        # Convert Pydantic model to dict, filtering None values
        update_dict = {}
        if updates.brand_name:
            update_dict["brand_name"] = updates.brand_name
        if updates.tagline:
            update_dict["tagline"] = updates.tagline
        if updates.primary_colors:
            update_dict.setdefault("visual_identity", {})["primary_colors"] = updates.primary_colors
        if updates.secondary_colors:
            update_dict.setdefault("visual_identity", {})["secondary_colors"] = updates.secondary_colors
        if updates.tone:
            update_dict.setdefault("writing_style", {})["tone"] = updates.tone
        if updates.avoid:
            update_dict.setdefault("writing_style", {})["avoid"] = updates.avoid
        if updates.voice:
            update_dict.setdefault("writing_style", {})["voice"] = updates.voice
        if updates.hashtags:
            update_dict.setdefault("content_guidelines", {})["hashtags"] = updates.hashtags
        if updates.keywords:
            update_dict.setdefault("content_guidelines", {})["keywords"] = updates.keywords
        if updates.examples:
            update_dict.setdefault("writing_style", {})["examples"] = updates.examples
        
        brain.update_profile(update_dict)
        return {"success": True, "message": "Brand profile updated"}
    except Exception as e:
        logger.error(f"Failed to update brand profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context")
async def get_brand_context():
    """Get brand context formatted for AI prompts."""
    try:
        from src.tools.brand_brain import get_brand_brain
        brain = get_brand_brain()
        context = brain.get_brand_context()
        return {"success": True, "context": context}
    except Exception as e:
        logger.error(f"Failed to get brand context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enhance-prompt")
async def enhance_prompt(request: PromptEnhanceRequest):
    """Enhance a prompt with brand context."""
    try:
        from src.tools.brand_brain import get_brand_brain
        brain = get_brand_brain()
        enhanced = brain.enhance_prompt(request.prompt, request.content_type)
        return {"success": True, "enhanced_prompt": enhanced}
    except Exception as e:
        logger.error(f"Failed to enhance prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assets/{category}")
async def list_assets(category: str):
    """List assets in a category (logo, font, guideline)."""
    try:
        from src.tools.brand_brain import get_brand_brain
        brain = get_brand_brain()
        assets = brain.get_assets(category)
        return {
            "success": True,
            "category": category,
            "assets": [{"name": a.name, "path": str(a)} for a in assets]
        }
    except Exception as e:
        logger.error(f"Failed to list assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assets/{category}")
async def upload_asset(
    category: str,
    file: UploadFile = File(...),
    filename: Optional[str] = Form(None)
):
    """Upload a brand asset."""
    try:
        from src.tools.brand_brain import get_brand_brain
        brain = get_brand_brain()
        
        # Read file content
        content = await file.read()
        save_name = filename or file.filename
        
        # Save asset
        path = brain.save_asset_from_bytes(content, save_name, category)
        return {"success": True, "path": path, "filename": save_name}
    except Exception as e:
        logger.error(f"Failed to upload asset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/assets")
async def delete_asset(file_path: str):
    """Delete a brand asset."""
    try:
        from src.tools.brand_brain import get_brand_brain
        brain = get_brand_brain()
        success = brain.delete_asset(file_path)
        return {"success": success}
    except Exception as e:
        logger.error(f"Failed to delete asset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-base")
async def get_knowledge_base():
    """Get the processed brand knowledge base."""
    try:
        from src.tools.brand_brain import get_brand_brain
        brain = get_brand_brain()
        kb = brain.get_knowledge_base()
        return {"success": True, "knowledge_base": kb}
    except Exception as e:
        logger.error(f"Failed to get knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge-base/process")
async def process_knowledge_base():
    """Process all guideline documents into knowledge base."""
    try:
        from src.tools.brand_brain import get_brand_brain
        brain = get_brand_brain()
        kb = brain.process_knowledge_base()
        return {
            "success": True,
            "total_docs": kb.get("total_docs", 0),
            "message": f"Processed {kb.get('total_docs', 0)} documents"
        }
    except Exception as e:
        logger.error(f"Failed to process knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/apply-logo")
async def apply_logo_to_video(request: LogoApplyRequest):
    """Apply logo watermark to a video."""
    try:
        from src.tools.brand_brain import get_brand_brain
        brain = get_brand_brain()
        output = brain.apply_logo_to_video(request.video_path, request.position)
        return {"success": True, "output_path": output}
    except Exception as e:
        logger.error(f"Failed to apply logo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/apply-colors")
async def apply_brand_colors(request: ColorGradeRequest):
    """Apply brand color grading to an image."""
    try:
        from src.tools.brand_brain import get_brand_brain
        brain = get_brand_brain()
        output = brain.apply_brand_colors_to_image(request.image_path, request.intensity)
        return {"success": True, "output_path": output}
    except Exception as e:
        logger.error(f"Failed to apply colors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train")
async def train_from_examples(examples: List[str]):
    """Train brand brain from example posts."""
    try:
        from src.tools.brand_brain import get_brand_brain
        brain = get_brand_brain()
        brain.train_from_examples(examples)
        return {"success": True, "message": f"Added {len(examples)} examples"}
    except Exception as e:
        logger.error(f"Failed to train from examples: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
async def export_brand_kit():
    """Export complete brand kit as zip file info."""
    try:
        from src.tools.brand_brain import get_brand_brain
        brain = get_brand_brain()
        output_path = "data/brand_brain/brand_kit_export.zip"
        brain.export_brand_kit(output_path)
        return {"success": True, "export_path": output_path}
    except Exception as e:
        logger.error(f"Failed to export brand kit: {e}")
        raise HTTPException(status_code=500, detail=str(e))
