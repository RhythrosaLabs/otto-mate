"""
Creative Platform Tools
========================

Tools for interacting with the autonomous creative platform from chat.
These tools allow the agent to create and manage creative projects.
"""

import uuid
import logging
from typing import Any, Dict, List, Optional
from functools import wraps

logger = logging.getLogger(__name__)


def _make_tool(name: str, description: str, parameters: Dict[str, Any], category: str = "creative_platform"):
    """Decorator to mark a function as a tool compatible with ToolRegistry."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        wrapper._is_tool = True  # type: ignore
        wrapper._tool_info = {  # type: ignore
            "name": name,
            "description": description,
            "parameters": parameters,
            "category": category,
            "tags": ["creative", "automation", "products"],
            "function": func.__name__,
            "module": func.__module__
        }
        return wrapper
    return decorator


class CreativePlatformTools:
    """Tools for managing autonomous creative projects."""
    
    @_make_tool(
        name="creative_start_project",
        description="Start a new autonomous creative project. Creates concepts, generates AI art, makes products on Printify, syncs to Shopify, and creates marketing content.",
        parameters={
            "goal": {"type": "string", "description": "What to create (e.g., 'vintage car t-shirt collection')", "required": True},
            "product_types": {"type": "array", "description": "Product types to create (e.g., ['t-shirt', 'hoodie'])"},
            "run_immediately": {"type": "boolean", "description": "Start running right away", "default": True}
        }
    )
    async def creative_start_project(
        self,
        goal: str,
        product_types: Optional[List[str]] = None,
        run_immediately: bool = True
    ) -> Dict[str, Any]:
        """Start a new autonomous creative project."""
        try:
            from ..core.creative_platform import get_creative_platform
            
            platform = get_creative_platform()
            project_id = f"proj-{uuid.uuid4().hex[:8]}"
            
            initial_state = {}
            if product_types:
                initial_state["creative_brief"] = {"product_targets": product_types}
            
            await platform.create_project(project_id, goal, initial_state)
            
            result = {
                "success": True,
                "project_id": project_id,
                "goal": goal,
                "message": f"Created creative project: {goal}"
            }
            
            if run_immediately:
                await platform.run_project_async(project_id)
                result["status"] = "running"
                result["message"] = f"Started creative project: {goal}"
            else:
                result["status"] = "created"
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to start creative project: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to start project: {e}"
            }
    
    @_make_tool(
        name="creative_check_status",
        description="Check the status of a creative project - see progress, products created, and any errors.",
        parameters={
            "project_id": {"type": "string", "description": "The project ID to check", "required": True}
        }
    )
    async def creative_check_status(self, project_id: str) -> Dict[str, Any]:
        """Check the status of a creative project."""
        try:
            from ..core.creative_platform import get_creative_platform
            
            platform = get_creative_platform()
            status = platform.get_project_status(project_id)
            
            if not status:
                return {
                    "success": False,
                    "error": f"Project not found: {project_id}"
                }
            
            return {
                "success": True,
                **status
            }
            
        except Exception as e:
            logger.error(f"Failed to check project status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @_make_tool(
        name="creative_list_projects",
        description="List all creative projects, optionally filtered by status.",
        parameters={
            "status_filter": {"type": "string", "description": "Filter by status (running, completed, paused, failed)"}
        }
    )
    async def creative_list_projects(self, status_filter: Optional[str] = None) -> Dict[str, Any]:
        """List all creative projects."""
        try:
            from ..core.creative_platform import get_creative_platform
            
            platform = get_creative_platform()
            projects = platform.list_projects(status_filter)
            
            return {
                "success": True,
                "count": len(projects),
                "projects": projects
            }
            
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @_make_tool(
        name="creative_pause_project",
        description="Pause a running creative project.",
        parameters={
            "project_id": {"type": "string", "description": "Project to pause", "required": True}
        }
    )
    async def creative_pause_project(self, project_id: str) -> Dict[str, Any]:
        """Pause a running creative project."""
        try:
            from ..core.creative_platform import get_creative_platform
            
            platform = get_creative_platform()
            success = platform.pause_project(project_id)
            
            if success:
                return {
                    "success": True,
                    "message": f"Project {project_id} paused"
                }
            else:
                return {
                    "success": False,
                    "error": f"Project not found: {project_id}"
                }
            
        except Exception as e:
            logger.error(f"Failed to pause project: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @_make_tool(
        name="creative_resume_project",
        description="Resume a paused creative project.",
        parameters={
            "project_id": {"type": "string", "description": "Project to resume", "required": True}
        }
    )
    async def creative_resume_project(self, project_id: str) -> Dict[str, Any]:
        """Resume a paused creative project."""
        try:
            from ..core.creative_platform import get_creative_platform
            
            platform = get_creative_platform()
            success = platform.resume_project(project_id)
            
            if success:
                await platform.run_project_async(project_id)
                return {
                    "success": True,
                    "message": f"Project {project_id} resumed"
                }
            else:
                return {
                    "success": False,
                    "error": f"Project not found: {project_id}"
                }
            
        except Exception as e:
            logger.error(f"Failed to resume project: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @_make_tool(
        name="creative_get_assets",
        description="Get all generated assets (images, videos, music) for a project.",
        parameters={
            "project_id": {"type": "string", "description": "Project ID", "required": True}
        }
    )
    async def creative_get_assets(self, project_id: str) -> Dict[str, Any]:
        """Get all generated assets for a project."""
        try:
            from ..core.creative_platform import get_creative_platform
            
            platform = get_creative_platform()
            state = platform.state_store.load_state(project_id)
            
            if not state:
                return {
                    "success": False,
                    "error": f"Project not found: {project_id}"
                }
            
            return {
                "success": True,
                "project_id": project_id,
                "assets": state.get("assets", {}),
                "image_assets": state.get("image_assets", {}),
                "video_assets": state.get("video_assets", {}),
                "music_assets": state.get("music_assets", {})
            }
            
        except Exception as e:
            logger.error(f"Failed to get assets: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @_make_tool(
        name="creative_get_products",
        description="Get all Printify products created for a project.",
        parameters={
            "project_id": {"type": "string", "description": "Project ID", "required": True}
        }
    )
    async def creative_get_products(self, project_id: str) -> Dict[str, Any]:
        """Get all created products for a project."""
        try:
            from ..core.creative_platform import get_creative_platform
            
            platform = get_creative_platform()
            state = platform.state_store.load_state(project_id)
            
            if not state:
                return {
                    "success": False,
                    "error": f"Project not found: {project_id}"
                }
            
            return {
                "success": True,
                "project_id": project_id,
                "products": state.get("printify_products", {}),
                "shopify_metrics": state.get("shopify_metrics", {})
            }
            
        except Exception as e:
            logger.error(f"Failed to get products: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @_make_tool(
        name="creative_quick_product",
        description="Quickly create a single product with AI-generated design. Faster than full creative project.",
        parameters={
            "description": {"type": "string", "description": "Design description (e.g., 'cyberpunk cat')", "required": True},
            "product_type": {"type": "string", "description": "Product type (t-shirt, hoodie, mug)", "default": "t-shirt"},
            "style": {"type": "string", "description": "Art style (modern, vintage, minimalist)", "default": "modern"}
        }
    )
    async def creative_quick_product(
        self,
        description: str,
        product_type: str = "t-shirt",
        style: str = "modern"
    ) -> Dict[str, Any]:
        """Quickly create a single product with AI-generated design."""
        try:
            from ..core.creative_platform import get_creative_platform
            
            platform = get_creative_platform()
            project_id = f"quick-{uuid.uuid4().hex[:6]}"
            
            initial_state = {
                "selected_concept": {
                    "title": description,
                    "aesthetic": style
                },
                "creative_brief": {
                    "concept": description,
                    "aesthetic": style,
                    "product_targets": [product_type]
                }
            }
            
            await platform.create_project(project_id, f"Quick: {description}", initial_state)
            
            # Start at asset generation step
            state = platform.state_store.load_state(project_id)
            if state:
                state["current_step"] = "generate_assets"
                platform.state_store.save_state(project_id, state)
            
            final_state = await platform.run_project(project_id, max_steps=15)
            
            return {
                "success": True,
                "project_id": project_id,
                "description": description,
                "product_type": product_type,
                "assets": final_state.get("assets", {}),
                "products": final_state.get("printify_products", {}),
                "status": final_state.get("status")
            }
            
        except Exception as e:
            logger.error(f"Quick product creation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @_make_tool(
        name="creative_batch_create",
        description="Create multiple products in batch from a list of themes.",
        parameters={
            "themes": {"type": "array", "description": "List of themes/descriptions for products", "required": True},
            "product_types": {"type": "array", "description": "Product types to create for each theme"}
        }
    )
    async def creative_batch_create(
        self,
        themes: List[str],
        product_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create multiple products in batch."""
        try:
            from ..core.creative_platform import get_creative_platform, MultiProjectScheduler
            
            platform = get_creative_platform()
            scheduler = MultiProjectScheduler(platform)
            
            projects = [
                {
                    "project_id": f"batch-{uuid.uuid4().hex[:6]}",
                    "goal": theme
                }
                for theme in themes
            ]
            
            scheduled = await scheduler.schedule_projects(projects)
            
            # Set product types if specified
            if product_types:
                for pid in scheduled:
                    state = platform.state_store.load_state(pid)
                    if state:
                        state["creative_brief"] = {"product_targets": product_types}
                        platform.state_store.save_state(pid, state)
            
            # Start them all
            results = await scheduler.run_all(projects)
            
            return {
                "success": True,
                "themes": themes,
                "scheduled": scheduled,
                "results": results.get("results", [])
            }
            
        except Exception as e:
            logger.error(f"Batch creation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @_make_tool(
        name="creative_delete_project",
        description="Delete a creative project and all its data.",
        parameters={
            "project_id": {"type": "string", "description": "Project to delete", "required": True}
        }
    )
    async def creative_delete_project(self, project_id: str) -> Dict[str, Any]:
        """Delete a creative project."""
        try:
            from ..core.creative_platform import get_creative_platform
            
            platform = get_creative_platform()
            platform.delete_project(project_id)
            
            return {
                "success": True,
                "message": f"Project {project_id} deleted"
            }
            
        except Exception as e:
            logger.error(f"Failed to delete project: {e}")
            return {
                "success": False,
                "error": str(e)
            }


def register_creative_platform_tools(registry):
    """Register creative platform tools with the tool registry."""
    tools = CreativePlatformTools()
    registry.register_tool_class(tools)
    logger.info("Registered Creative Platform tools")
    return tools
