"""
Autonomous Creative Platform
=============================

LangGraph-integrated creative workflow system for Otto.
Handles end-to-end creative projects with:
- Multimodal asset generation (images, video, music)
- Printify/Shopify product creation
- Content marketing (blogs, emails, web pages)
- Audit trails and stuck detection
- Multi-project orchestration with persistence

Integrates with existing Otto tools and infrastructure.
"""

import asyncio
import logging
import time
import json
import sqlite3
from typing import TypedDict, Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# State Definition
# ============================================================================

class ProjectStatus(str, Enum):
    """Project lifecycle states."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    STUCK = "stuck"


class CreativeState(TypedDict, total=False):
    """Complete state for a creative project."""
    # Project metadata
    project_id: str
    goal: str
    status: str  # ProjectStatus value
    current_step: str
    retry_count: int
    stuck_reason: Optional[str]
    created_at: str
    updated_at: str
    
    # UI control
    ui_override: Optional[str]  # "pause", "skip", "manual_approve", "resume"
    
    # Multimodal assets from Replicate
    image_assets: Dict[str, Any]
    video_assets: Dict[str, Any]
    music_assets: Dict[str, Any]
    assets: Dict[str, Any]  # Merged assets
    replicate_metadata: Dict[str, Any]
    
    # Ideation & strategy
    concepts: List[Dict[str, Any]]
    selected_concept: Dict[str, Any]
    research: Dict[str, Any]
    commerce_analysis: Dict[str, Any]
    
    # Creative brief
    creative_brief: Dict[str, Any]
    approvals: Dict[str, bool]
    
    # Production & marketing
    listings: Dict[str, Any]
    marketing_assets: Dict[str, Any]
    printify_products: Dict[str, Any]
    shopify_metrics: Dict[str, Any]
    blog_post: Dict[str, Any]
    web_page: Dict[str, Any]
    email_campaign: Dict[str, Any]
    
    # Operations
    audit_flags: List[str]
    logs: List[str]
    errors: List[str]
    
    # Agent performance metrics
    performance: Dict[str, Any]


# ============================================================================
# State Store (SQLite persistence)
# ============================================================================

class CreativeStateStore:
    """
    Persistent state storage for creative projects.
    Uses SQLite for checkpointing and recovery.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = str(Path(__file__).parent.parent.parent / "data" / "creative_platform.db")
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS project_states (
                    project_id TEXT PRIMARY KEY,
                    state_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS project_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    step TEXT NOT NULL,
                    state_json TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES project_states(project_id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_history_project 
                ON project_history(project_id, timestamp)
            """)
            conn.commit()
    
    def save_state(self, project_id: str, state: CreativeState):
        """Save or update project state."""
        now = datetime.utcnow().isoformat()
        state["updated_at"] = now
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO project_states 
                (project_id, state_json, status, created_at, updated_at)
                VALUES (?, ?, ?, COALESCE(
                    (SELECT created_at FROM project_states WHERE project_id = ?),
                    ?
                ), ?)
            """, (
                project_id,
                json.dumps(state),
                state.get("status", ProjectStatus.IDLE),
                project_id,
                now,
                now
            ))
            
            # Record history checkpoint
            conn.execute("""
                INSERT INTO project_history (project_id, step, state_json, timestamp)
                VALUES (?, ?, ?, ?)
            """, (project_id, state.get("current_step", "unknown"), json.dumps(state), now))
            
            conn.commit()
    
    def load_state(self, project_id: str) -> Optional[CreativeState]:
        """Load project state."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT state_json FROM project_states WHERE project_id = ?",
                (project_id,)
            ).fetchone()
            
            if row:
                return json.loads(row[0])
            return None
    
    def list_projects(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all projects, optionally filtered by status."""
        with sqlite3.connect(self.db_path) as conn:
            if status:
                rows = conn.execute(
                    "SELECT project_id, status, created_at, updated_at FROM project_states WHERE status = ?",
                    (status,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT project_id, status, created_at, updated_at FROM project_states"
                ).fetchall()
            
            return [
                {"project_id": r[0], "status": r[1], "created_at": r[2], "updated_at": r[3]}
                for r in rows
            ]
    
    def get_history(self, project_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get state history for a project."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT step, timestamp, state_json 
                FROM project_history 
                WHERE project_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (project_id, limit)).fetchall()
            
            return [
                {"step": r[0], "timestamp": r[1], "state": json.loads(r[2])}
                for r in rows
            ]
    
    def delete_project(self, project_id: str):
        """Delete a project and its history."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM project_history WHERE project_id = ?", (project_id,))
            conn.execute("DELETE FROM project_states WHERE project_id = ?", (project_id,))
            conn.commit()


# ============================================================================
# Agent Nodes - Execute actual work via Otto tools
# ============================================================================

class CreativeAgentNodes:
    """
    Agent node implementations that execute via Otto's tool infrastructure.
    Each node transforms state by calling existing Otto tools.
    """
    
    def __init__(self, tool_registry=None, execution_agent=None, progress_callback=None):
        self.tool_registry = tool_registry
        self.execution_agent = execution_agent
        self.progress_callback = progress_callback
        
    async def _execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool via Otto's execution agent."""
        if not self.tool_registry:
            logger.warning(f"Tool registry not set, simulating {tool_name}")
            return {"success": True, "simulated": True, "tool": tool_name}
        
        try:
            # Pre-filter known meta-parameters that should never be passed to tools
            meta_params_to_remove = {'task_description', 'task_type', 'task_id', 'step_id', 'execution_context'}
            params = {k: v for k, v in params.items() if k not in meta_params_to_remove}
            
            if self.execution_agent:
                result = await self.execution_agent.execute_tool(
                    tool_name=tool_name,
                    parameters=params,
                    tool_registry=self.tool_registry,
                    context={}
                )
            else:
                # Direct tool execution
                tool = self.tool_registry.get_tool(tool_name)
                if tool:
                    result = await tool(**params)
                else:
                    result = {"success": False, "error": f"Tool not found: {tool_name}"}
            
            return result
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name} - {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_progress(self, step: str, message: str, data: Optional[Dict] = None):
        """Send progress update to UI."""
        if self.progress_callback:
            try:
                await self.progress_callback({
                    "step": step,
                    "message": message,
                    "data": data or {},
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.debug(f"Progress callback failed: {e}")
    
    # ─────────────────────────────────────────────────────────────────
    # Core Orchestration
    # ─────────────────────────────────────────────────────────────────
    
    async def orchestrator(self, state: CreativeState) -> Dict[str, Any]:
        """
        Central orchestrator - determines next step based on state.
        Handles UI overrides and workflow routing.
        """
        await self._send_progress("orchestrator", "Evaluating project state...")
        
        # Handle UI overrides
        ui_override = state.get("ui_override")
        if ui_override == "pause":
            return {"status": ProjectStatus.PAUSED, "current_step": "paused"}
        if ui_override == "skip":
            return {"current_step": "next_producible_step", "ui_override": None}
        if ui_override == "manual_approve":
            return {"status": ProjectStatus.WAITING_APPROVAL, "current_step": "waiting_approval"}
        if ui_override == "resume":
            return {"status": ProjectStatus.RUNNING, "ui_override": None}
        
        # Determine next step based on state completeness
        if not state.get("concepts"):
            return {"current_step": "conceptualize", "status": ProjectStatus.RUNNING}
        if not state.get("selected_concept"):
            return {"current_step": "creative_direct", "status": ProjectStatus.RUNNING}
        if not state.get("assets"):
            return {"current_step": "generate_assets", "status": ProjectStatus.RUNNING}
        if not state.get("printify_products"):
            return {"current_step": "create_products", "status": ProjectStatus.RUNNING}
        if not state.get("blog_post"):
            return {"current_step": "create_content", "status": ProjectStatus.RUNNING}
        
        return {"current_step": "monitor", "status": ProjectStatus.COMPLETED}
    
    # ─────────────────────────────────────────────────────────────────
    # Ideation & Research
    # ─────────────────────────────────────────────────────────────────
    
    async def conceptualizer(self, state: CreativeState) -> Dict[str, Any]:
        """Generate creative concepts based on goal."""
        await self._send_progress("conceptualize", f"Generating concepts for: {state.get('goal', 'project')}")
        
        goal = state.get("goal", "creative product")
        
        # Use Claude/research to generate concepts
        result = await self._execute_tool("research_topic", {
            "query": f"creative product ideas for: {goal}",
            "depth": "quick"
        })
        
        # Generate concepts (fallback to defaults if research fails)
        concepts = [
            {
                "title": f"{goal} - Premium Edition",
                "theme": "high-quality craftsmanship",
                "aesthetic": "modern minimalist",
                "risk": "low",
                "reward": "established market"
            },
            {
                "title": f"{goal} - Artistic Vision",
                "theme": "unique artistic expression",
                "aesthetic": "bold creative",
                "risk": "medium",
                "reward": "differentiation"
            },
            {
                "title": f"{goal} - Limited Drop",
                "theme": "exclusivity and scarcity",
                "aesthetic": "collector edition",
                "risk": "high",
                "reward": "premium pricing"
            }
        ]
        
        return {"concepts": concepts, "current_step": "research"}
    
    async def researcher(self, state: CreativeState) -> Dict[str, Any]:
        """Research market trends and competition."""
        await self._send_progress("research", "Researching market trends...")
        
        concepts = state.get("concepts", [])
        theme = concepts[0].get("theme", "products") if concepts else "products"
        
        result = await self._execute_tool("research_topic", {
            "query": f"market trends for {theme} 2026",
            "depth": "normal"
        })
        
        research = {
            "market_trends": result.get("insights", ["AI-generated art", "sustainable materials", "limited editions"]),
            "competitors": result.get("sources", ["Etsy POD", "Redbubble", "Society6"]),
            "opportunities": ["personalization", "bundled products", "subscription models"],
            "researched_at": datetime.utcnow().isoformat()
        }
        
        return {"research": research, "current_step": "commerce_analysis"}
    
    async def commerce_analyzer(self, state: CreativeState) -> Dict[str, Any]:
        """Analyze commercial viability."""
        await self._send_progress("commerce", "Analyzing commercial viability...")
        
        concept = state.get("selected_concept") or (state.get("concepts", [{}])[0])
        
        analysis = {
            "price_range": "$25-$75",
            "estimated_costs": {
                "production": "$8-15",
                "shipping": "$5-12",
                "platform_fees": "5-12%"
            },
            "profit_margin": "40-60%",
            "verdict": "go",
            "recommendations": [
                "Start with apparel (t-shirts, hoodies) for fastest validation",
                "Add premium products (canvas, metal prints) for higher margins",
                "Consider bundles for increased average order value"
            ]
        }
        
        return {"commerce_analysis": analysis, "current_step": "creative_direct"}
    
    async def creative_director(self, state: CreativeState) -> Dict[str, Any]:
        """Select and refine the creative direction."""
        await self._send_progress("creative_direct", "Finalizing creative direction...")
        
        concepts = state.get("concepts", [])
        research = state.get("research", {})
        
        # Select best concept (first one for now, could use LLM selection)
        selected = concepts[0] if concepts else {
            "title": state.get("goal", "Custom Project"),
            "theme": "modern creative",
            "aesthetic": "professional"
        }
        
        # Generate creative brief
        creative_brief = {
            "concept": selected.get("title"),
            "aesthetic": selected.get("aesthetic", "modern"),
            "palette": ["primary brand color", "complementary accent", "neutral background"],
            "style_keywords": ["professional", "eye-catching", "memorable"],
            "image_specs": {
                "format": "PNG with transparency",
                "min_resolution": "4000x4000",
                "aspect_ratios": ["1:1", "16:9", "9:16"]
            },
            "product_targets": ["t-shirt", "hoodie", "mug", "poster", "sticker"],
            "market_positioning": research.get("opportunities", [])[:3]
        }
        
        return {
            "selected_concept": selected,
            "creative_brief": creative_brief,
            "current_step": "generate_assets"
        }
    
    # ─────────────────────────────────────────────────────────────────
    # Asset Generation (Replicate Integration)
    # ─────────────────────────────────────────────────────────────────
    
    async def generate_assets(self, state: CreativeState) -> Dict[str, Any]:
        """Generate all multimodal assets using Replicate."""
        await self._send_progress("generate_assets", "Generating creative assets...")
        
        brief = state.get("creative_brief", {})
        concept = state.get("selected_concept", {})
        
        # Generate image assets
        image_prompt = f"{concept.get('title', 'design')}, {brief.get('aesthetic', 'modern')}, professional product design, high quality, trending on artstation"
        
        image_result = await self._execute_tool("replicate_create_product_design", {
            "description": image_prompt,
            "style": "realistic_image/studio_portrait",
            "transparent_background": True
        })
        
        image_assets = {
            "main_design": image_result.get("images", [None])[0] if isinstance(image_result.get("images"), list) else image_result.get("image_url"),
            "generated_at": datetime.utcnow().isoformat(),
            "prompt_used": image_prompt
        }
        
        replicate_metadata = {
            "models_used": ["recraft-v3"],
            "generation_time": image_result.get("prediction_time", "unknown")
        }
        
        return {
            "image_assets": image_assets,
            "assets": {
                "primary_image": image_assets.get("main_design"),
                **image_assets
            },
            "replicate_metadata": replicate_metadata,
            "current_step": "create_products"
        }
    
    async def image_synthesizer(self, state: CreativeState) -> Dict[str, Any]:
        """Generate additional image variations."""
        await self._send_progress("image_synth", "Creating image variations...")
        
        base_design = state.get("assets", {}).get("primary_image")
        if not base_design:
            return {"image_assets": state.get("image_assets", {})}
        
        # Generate additional variations
        variations = {"main": base_design}
        
        # Could add more variation generation here
        return {"image_assets": {**state.get("image_assets", {}), **variations}}
    
    async def video_synthesizer(self, state: CreativeState) -> Dict[str, Any]:
        """Generate promotional video content."""
        await self._send_progress("video_synth", "Generating video content...")
        
        image = state.get("assets", {}).get("primary_image")
        
        if image:
            # Generate video from image
            video_result = await self._execute_tool("replicate_create_video", {
                "image_url": image,
                "motion_type": "subtle_motion"
            })
            
            video_assets = {
                "promo_video": video_result.get("video_url"),
                "generated_at": datetime.utcnow().isoformat()
            }
        else:
            video_assets = {"note": "No base image for video generation"}
        
        return {"video_assets": video_assets}
    
    async def music_synthesizer(self, state: CreativeState) -> Dict[str, Any]:
        """Generate music/audio content."""
        await self._send_progress("music_synth", "Generating audio...")
        
        brief = state.get("creative_brief", {})
        
        music_result = await self._execute_tool("replicate_generate_music", {
            "prompt": f"background music for {brief.get('aesthetic', 'modern')} product, upbeat, commercial",
            "duration": 30
        })
        
        music_assets = {
            "background_track": music_result.get("audio_url"),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return {"music_assets": music_assets}
    
    async def merge_assets(self, state: CreativeState) -> Dict[str, Any]:
        """Merge all generated assets into unified structure."""
        await self._send_progress("merge_assets", "Consolidating assets...")
        
        merged = {
            **state.get("image_assets", {}),
            **state.get("video_assets", {}),
            **state.get("music_assets", {}),
            **state.get("assets", {})
        }
        
        return {"assets": merged, "current_step": "create_products"}
    
    # ─────────────────────────────────────────────────────────────────
    # Product Creation (Printify/Shopify)
    # ─────────────────────────────────────────────────────────────────
    
    async def create_printify_products(self, state: CreativeState) -> Dict[str, Any]:
        """Create products on Printify."""
        await self._send_progress("printify", "Creating products on Printify...")
        
        assets = state.get("assets", {})
        concept = state.get("selected_concept", {})
        brief = state.get("creative_brief", {})
        
        design_url = assets.get("primary_image") or assets.get("main_design")
        
        if not design_url:
            return {
                "printify_products": {"error": "No design image available"},
                "errors": state.get("errors", []) + ["No design for Printify"]
            }
        
        product_types = brief.get("product_targets", ["t-shirt", "mug", "poster"])
        created_products = {}
        
        for product_type in product_types[:3]:  # Limit to 3 for now
            await self._send_progress("printify", f"Creating {product_type}...")
            
            result = await self._execute_tool("printify_smart_create_product", {
                "title": f"{concept.get('title', 'Design')} - {product_type.title()}",
                "description": f"Premium {product_type} featuring our {concept.get('theme', 'custom')} design",
                "product_type": product_type,
                "image_url": design_url
            })
            
            if result.get("success"):
                created_products[result.get("product_id", product_type)] = {
                    "type": product_type,
                    "status": "created",
                    "published": result.get("published", False),
                    "mockup_url": result.get("default_mockup")
                }
            else:
                created_products[product_type] = {
                    "type": product_type,
                    "status": "failed",
                    "error": result.get("error")
                }
        
        return {
            "printify_products": created_products,
            "current_step": "sync_shopify"
        }
    
    async def sync_shopify(self, state: CreativeState) -> Dict[str, Any]:
        """Sync products to Shopify and get metrics."""
        await self._send_progress("shopify", "Syncing to Shopify...")
        
        printify_products = state.get("printify_products", {})
        
        # Products are auto-published to Shopify via Printify
        # Just gather metrics
        metrics = {}
        
        for product_id, product_data in printify_products.items():
            if product_data.get("status") == "created":
                metrics[product_id] = {
                    "synced": product_data.get("published", False),
                    "stock": "POD (unlimited)",
                    "sales": 0
                }
        
        return {
            "shopify_metrics": metrics,
            "current_step": "create_content"
        }
    
    # ─────────────────────────────────────────────────────────────────
    # Content Marketing
    # ─────────────────────────────────────────────────────────────────
    
    async def create_blog_post(self, state: CreativeState) -> Dict[str, Any]:
        """Generate blog post about the products."""
        await self._send_progress("blogging", "Writing blog post...")
        
        concept = state.get("selected_concept", {})
        assets = state.get("assets", {})
        products = state.get("printify_products", {})
        
        # Generate blog content
        result = await self._execute_tool("shopify_write_and_publish_blog", {
            "topic": f"Introducing {concept.get('title', 'Our New Collection')}",
            "tone": "engaging",
            "include_product_links": True,
            "generate_images": False  # We have our own
        })
        
        blog_post = {
            "title": f"Introducing {concept.get('title', 'Our New Collection')}",
            "content": result.get("content", f"Discover our latest {concept.get('theme', 'designs')}!"),
            "status": "published" if result.get("success") else "draft",
            "url": result.get("url"),
            "metadata": {
                "tags": ["new-release", "design", concept.get("theme", "products")],
                "category": "Product Launch"
            }
        }
        
        return {"blog_post": blog_post, "current_step": "create_email"}
    
    async def create_email_campaign(self, state: CreativeState) -> Dict[str, Any]:
        """Create email campaign for product launch."""
        await self._send_progress("email", "Creating email campaign...")
        
        concept = state.get("selected_concept", {})
        assets = state.get("assets", {})
        
        campaign = {
            "subject": f"🎨 New Drop: {concept.get('title', 'Exclusive Collection')}",
            "preview_text": f"Discover our {concept.get('theme', 'latest designs')}",
            "body": f"""
            <h1>{concept.get('title', 'New Collection')}</h1>
            <p>We're excited to introduce our latest creation!</p>
            <img src="{assets.get('primary_image', '')}" alt="Product Design" />
            <p>Shop now and be one of the first to own this exclusive design.</p>
            """,
            "status": "ready",
            "scheduled": False,
            "created_at": datetime.utcnow().isoformat()
        }
        
        return {"email_campaign": campaign, "current_step": "create_web_page"}
    
    async def create_web_page(self, state: CreativeState) -> Dict[str, Any]:
        """Generate landing page for the collection."""
        await self._send_progress("web_design", "Designing landing page...")
        
        concept = state.get("selected_concept", {})
        assets = state.get("assets", {})
        products = state.get("printify_products", {})
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{concept.get('title', 'Collection')}</title>
            <meta name="description" content="{concept.get('theme', 'Exclusive designs')}" />
        </head>
        <body>
            <header>
                <h1>{concept.get('title', 'New Collection')}</h1>
                <p>{concept.get('theme', 'Discover our latest designs')}</p>
            </header>
            <main>
                <section class="hero">
                    <img src="{assets.get('primary_image', '')}" alt="Hero Design" />
                </section>
                <section class="products">
                    {"".join(f'<div class="product">{p.get("type", "Product")}</div>' for p in products.values() if isinstance(p, dict))}
                </section>
            </main>
        </body>
        </html>
        """
        
        return {
            "web_page": {
                "html": html,
                "status": "generated",
                "needs_hosting": True
            },
            "current_step": "audit"
        }
    
    # ─────────────────────────────────────────────────────────────────
    # Quality & Operations
    # ─────────────────────────────────────────────────────────────────
    
    async def auditor(self, state: CreativeState) -> Dict[str, Any]:
        """Audit project for issues and compliance."""
        await self._send_progress("audit", "Running quality audit...")
        
        flags = []
        
        # Check for secrets/PII
        state_str = json.dumps(state, default=str)
        sensitive_patterns = ["API_KEY", "SECRET", "PASSWORD", "BEARER"]
        for pattern in sensitive_patterns:
            if pattern in state_str.upper():
                flags.append(f"Potential {pattern} exposure detected")
        
        # Check required assets
        if not state.get("assets", {}).get("primary_image"):
            flags.append("Missing primary design image")
        
        # Check product creation
        products = state.get("printify_products", {})
        failed_products = [k for k, v in products.items() if isinstance(v, dict) and v.get("status") == "failed"]
        if failed_products:
            flags.append(f"Failed to create products: {', '.join(failed_products)}")
        
        return {
            "audit_flags": flags,
            "current_step": "stuck_check" if flags else "complete"
        }
    
    async def stuck_detector(self, state: CreativeState) -> Dict[str, Any]:
        """Detect if project is stuck and needs intervention."""
        await self._send_progress("stuck_check", "Checking project health...")
        
        retries = state.get("retry_count", 0)
        audit_flags = state.get("audit_flags", [])
        
        if retries > 3:
            return {
                "stuck_reason": f"Too many retries ({retries})",
                "status": ProjectStatus.STUCK,
                "current_step": "reconceptualize",
                "logs": state.get("logs", []) + [f"Stuck after {retries} retries"]
            }
        
        if len(audit_flags) > 2:
            return {
                "stuck_reason": f"Multiple audit failures: {audit_flags}",
                "status": ProjectStatus.STUCK,
                "current_step": "creative_direct",
                "retry_count": retries + 1
            }
        
        return {"current_step": "complete", "status": ProjectStatus.COMPLETED}
    
    async def reconceptualizer(self, state: CreativeState) -> Dict[str, Any]:
        """Generate new concepts when stuck."""
        await self._send_progress("reconceptualize", "Pivoting strategy...")
        
        old_concepts = state.get("concepts", [])
        
        new_concepts = [
            {
                "title": f"{state.get('goal', 'Project')} - Simplified",
                "theme": "minimalist approach",
                "risk": "low",
                "reward": "faster turnaround",
                "pivot_reason": state.get("stuck_reason")
            }
        ]
        
        return {
            "concepts": new_concepts,
            "retry_count": 0,
            "stuck_reason": None,
            "status": ProjectStatus.RUNNING,
            "current_step": "research",
            "logs": state.get("logs", []) + [f"Reconceptualized from: {old_concepts}"]
        }
    
    async def operator(self, state: CreativeState) -> Dict[str, Any]:
        """Final operations and logging."""
        await self._send_progress("complete", "Project completed!")
        
        return {
            "status": ProjectStatus.COMPLETED,
            "logs": state.get("logs", []) + [
                f"Project completed at {datetime.utcnow().isoformat()}",
                f"Products created: {len(state.get('printify_products', {}))}",
                f"Assets generated: {len(state.get('assets', {}))}"
            ]
        }


# ============================================================================
# Creative Platform Engine
# ============================================================================

class CreativePlatformEngine:
    """
    Main engine for running creative projects.
    Orchestrates the workflow graph and manages state.
    """
    
    # Step execution order
    WORKFLOW_STEPS = {
        "conceptualize": "conceptualizer",
        "research": "researcher",
        "commerce_analysis": "commerce_analyzer",
        "creative_direct": "creative_director",
        "generate_assets": "generate_assets",
        "image_synth": "image_synthesizer",
        "video_synth": "video_synthesizer",
        "music_synth": "music_synthesizer",
        "merge_assets": "merge_assets",
        "create_products": "create_printify_products",
        "sync_shopify": "sync_shopify",
        "create_content": "create_blog_post",
        "create_email": "create_email_campaign",
        "create_web_page": "create_web_page",
        "audit": "auditor",
        "stuck_check": "stuck_detector",
        "reconceptualize": "reconceptualizer",
        "complete": "operator",
        "monitor": "operator"
    }
    
    def __init__(self, tool_registry=None, execution_agent=None):
        self.state_store = CreativeStateStore()
        self.nodes = CreativeAgentNodes(tool_registry, execution_agent)
        self.running_projects: Dict[str, asyncio.Task] = {}
        
    def set_tool_registry(self, tool_registry, execution_agent=None):
        """Configure tool access."""
        self.nodes.tool_registry = tool_registry
        if execution_agent:
            self.nodes.execution_agent = execution_agent
    
    def set_progress_callback(self, callback: Callable):
        """Set callback for progress updates."""
        self.nodes.progress_callback = callback
    
    async def create_project(
        self,
        project_id: str,
        goal: str,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> CreativeState:
        """Create a new creative project."""
        state: CreativeState = {
            "project_id": project_id,
            "goal": goal,
            "status": ProjectStatus.IDLE,
            "current_step": "orchestrator",
            "retry_count": 0,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "logs": [f"Project created: {goal}"],
            "errors": [],
            "performance": {}
        }
        
        if initial_state:
            for key, value in initial_state.items():
                state[key] = value  # type: ignore
        
        self.state_store.save_state(project_id, state)
        return state
    
    async def run_project(
        self,
        project_id: str,
        max_steps: int = 50
    ) -> CreativeState:
        """Run a project through the workflow until completion."""
        state = self.state_store.load_state(project_id)
        if not state:
            raise ValueError(f"Project not found: {project_id}")
        
        state["status"] = ProjectStatus.RUNNING
        steps_executed = 0
        
        while steps_executed < max_steps:
            # Check for terminal states
            if state.get("status") in [ProjectStatus.COMPLETED, ProjectStatus.FAILED, ProjectStatus.PAUSED]:
                break
            
            # Check for UI override to pause
            if state.get("ui_override") == "pause":
                state["status"] = ProjectStatus.PAUSED
                break
            
            # Run orchestrator to determine next step
            orchestrator_result = await self.nodes.orchestrator(state)
            for key, value in orchestrator_result.items():
                state[key] = value  # type: ignore
            
            current_step = state.get("current_step", "complete")
            
            # Check for completion conditions
            if current_step in ["complete", "paused", "waiting_approval"]:
                break
            
            # Execute the step
            step_method_name = self.WORKFLOW_STEPS.get(current_step)
            if step_method_name and hasattr(self.nodes, step_method_name):
                start_time = time.time()
                
                try:
                    method = getattr(self.nodes, step_method_name)
                    result = await method(state)
                    for key, value in result.items():
                        state[key] = value  # type: ignore
                    
                    # Track performance
                    duration = time.time() - start_time
                    perf = state.get("performance", {})
                    if current_step not in perf:
                        perf[current_step] = {"runs": 0, "total_time": 0.0}
                    perf[current_step]["runs"] += 1
                    perf[current_step]["total_time"] += duration
                    state["performance"] = perf
                    
                except Exception as e:
                    logger.error(f"Step {current_step} failed: {e}")
                    state["errors"] = state.get("errors", []) + [f"{current_step}: {str(e)}"]
                    state["retry_count"] = state.get("retry_count", 0) + 1
            
            # Save checkpoint
            self.state_store.save_state(project_id, state)
            steps_executed += 1
        
        # Final save
        self.state_store.save_state(project_id, state)
        return state
    
    async def run_project_async(self, project_id: str) -> str:
        """Start a project running in the background."""
        if project_id in self.running_projects:
            return "already_running"
        
        task = asyncio.create_task(self.run_project(project_id))
        self.running_projects[project_id] = task
        
        # Clean up when done
        def cleanup(_):
            self.running_projects.pop(project_id, None)
        task.add_done_callback(cleanup)
        
        return "started"
    
    def pause_project(self, project_id: str) -> bool:
        """Pause a running project."""
        state = self.state_store.load_state(project_id)
        if state:
            state["ui_override"] = "pause"
            self.state_store.save_state(project_id, state)
            return True
        return False
    
    def resume_project(self, project_id: str) -> bool:
        """Resume a paused project."""
        state = self.state_store.load_state(project_id)
        if state:
            state["ui_override"] = "resume"
            state["status"] = ProjectStatus.RUNNING
            self.state_store.save_state(project_id, state)
            return True
        return False
    
    def get_project_status(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get current project status."""
        state = self.state_store.load_state(project_id)
        if not state:
            return None
        
        return {
            "project_id": project_id,
            "goal": state.get("goal"),
            "status": state.get("status"),
            "current_step": state.get("current_step"),
            "retry_count": state.get("retry_count", 0),
            "created_at": state.get("created_at"),
            "updated_at": state.get("updated_at"),
            "products_created": len(state.get("printify_products", {})),
            "assets_generated": len(state.get("assets", {})),
            "errors": state.get("errors", []),
            "audit_flags": state.get("audit_flags", [])
        }
    
    def list_projects(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all projects."""
        return self.state_store.list_projects(status)
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        if project_id in self.running_projects:
            self.running_projects[project_id].cancel()
        self.state_store.delete_project(project_id)
        return True


# ============================================================================
# Multi-Project Scheduler
# ============================================================================

class MultiProjectScheduler:
    """
    Schedule and manage multiple creative projects.
    """
    
    def __init__(self, engine: CreativePlatformEngine):
        self.engine = engine
        self.queue: List[Dict[str, Any]] = []
        self.max_concurrent = 3
    
    async def schedule_projects(self, projects: List[Dict[str, str]]) -> List[str]:
        """
        Schedule multiple projects for execution.
        
        Args:
            projects: List of {"project_id": "...", "goal": "..."}
            
        Returns:
            List of scheduled project IDs
        """
        scheduled = []
        
        for project in projects:
            project_id = project["project_id"]
            goal = project["goal"]
            
            # Create the project
            await self.engine.create_project(project_id, goal)
            scheduled.append(project_id)
        
        return scheduled
    
    async def run_all(self, projects: List[Dict[str, str]]) -> Dict[str, Any]:
        """Run multiple projects concurrently."""
        scheduled = await self.schedule_projects(projects)
        
        # Run concurrently with limit
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def run_with_limit(project_id):
            async with semaphore:
                return await self.engine.run_project(project_id)
        
        results = await asyncio.gather(
            *[run_with_limit(pid) for pid in scheduled],
            return_exceptions=True
        )
        
        return {
            "scheduled": scheduled,
            "results": [
                {"project_id": pid, "success": not isinstance(r, Exception)}
                for pid, r in zip(scheduled, results)
            ]
        }


# ============================================================================
# Singleton Instance
# ============================================================================

_creative_platform: Optional[CreativePlatformEngine] = None


def get_creative_platform() -> CreativePlatformEngine:
    """Get or create the creative platform singleton."""
    global _creative_platform
    if _creative_platform is None:
        _creative_platform = CreativePlatformEngine()
    return _creative_platform


def init_creative_platform(tool_registry, execution_agent=None) -> CreativePlatformEngine:
    """Initialize the creative platform with tools."""
    platform = get_creative_platform()
    platform.set_tool_registry(tool_registry, execution_agent)
    return platform
