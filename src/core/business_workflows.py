"""
Otto Universal - Business Workflow Generators
=============================================

Powerful, modular generators for common business workflows.
Built to leverage Otto's tools and ABP integrations.
"""

import logging
from typing import Any, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class WorkflowType(Enum):
    """Supported business workflow types."""
    PRODUCT_LAUNCH = "product_launch"
    MARKETING_CAMPAIGN = "marketing_campaign"
    CONTENT_PIPELINE = "content_pipeline"
    SALES_FUNNEL = "sales_funnel"
    CUSTOMER_ONBOARDING = "customer_onboarding"
    ANALYTICS_DASHBOARD = "analytics_dashboard"
    INVENTORY_MANAGEMENT = "inventory_management"
    EMAIL_SEQUENCE = "email_sequence"


@dataclass
class WorkflowStep:
    """A single step in a business workflow."""
    id: str
    name: str
    description: str
    action: str  # Tool or method to call
    params: Dict[str, Any]
    dependencies: List[str]
    optional: bool = False
    timeout_minutes: int = 30
    retry_on_failure: bool = True


@dataclass
class WorkflowTemplate:
    """Template for a business workflow."""
    type: WorkflowType
    name: str
    description: str
    steps: List[WorkflowStep]
    estimated_duration: str
    kpis: List[str]
    required_integrations: List[str]


class BusinessWorkflowGenerator:
    """
    Generates and executes business workflows.
    
    Provides pre-built templates for common business operations
    and can generate custom workflows based on requirements.
    """
    
    def __init__(self, orchestrator: Any):
        self.orchestrator = orchestrator
        self.templates = self._initialize_templates()
        logger.info("Business Workflow Generator initialized")
    
    def _initialize_templates(self) -> Dict[WorkflowType, WorkflowTemplate]:
        """Initialize workflow templates."""
        return {
            WorkflowType.PRODUCT_LAUNCH: self._create_product_launch_template(),
            WorkflowType.MARKETING_CAMPAIGN: self._create_marketing_campaign_template(),
            WorkflowType.CONTENT_PIPELINE: self._create_content_pipeline_template(),
            WorkflowType.EMAIL_SEQUENCE: self._create_email_sequence_template()
        }
    
    def _create_product_launch_template(self) -> WorkflowTemplate:
        """
        Complete product launch workflow.
        
        Steps:
        1. Market research
        2. Design generation
        3. Product creation (Printify)
        4. Product descriptions & SEO
        5. Social media content
        6. Launch campaign
        7. Analytics setup
        """
        return WorkflowTemplate(
            type=WorkflowType.PRODUCT_LAUNCH,
            name="Complete Product Launch",
            description="End-to-end workflow for launching a new product",
            estimated_duration="45-60 minutes",
            kpis=["products_created", "listings_published", "content_pieces_generated"],
            required_integrations=["printify", "shopify", "replicate"],
            steps=[
                WorkflowStep(
                    id="research",
                    name="Market Research",
                    description="Research target market and trending products",
                    action="research_topic",
                    params={
                        "query": "{product_category} trending products 2026",
                        "depth": "deep"
                    },
                    dependencies=[]
                ),
                WorkflowStep(
                    id="design",
                    name="Generate Product Design",
                    description="Create unique product design using AI",
                    action="generate_image",
                    params={
                        "prompt": "{design_concept}",
                        "model": "flux-pro",
                        "aspect_ratio": "1:1"
                    },
                    dependencies=["research"]
                ),
                WorkflowStep(
                    id="save_design",
                    name="Save Design Image",
                    description="Save the generated design to file storage",
                    action="save_generated_image",
                    params={
                        "image_url": "{design.images[0]}",
                        "filename": "{product_title}_design.png",
                        "category": "generated"
                    },
                    dependencies=["design"]
                ),
                WorkflowStep(
                    id="mockup",
                    name="Create Product Mockup",
                    description="Generate realistic product mockup",
                    action="generate_product_mockup",
                    params={
                        "design_url": "{save_design.url}",
                        "product_type": "{product_type}"
                    },
                    dependencies=["save_design"]
                ),
                WorkflowStep(
                    id="printify_product",
                    name="Create Printify Product",
                    description="Set up product on Printify",
                    action="printify_create_product",
                    params={
                        "title": "{product_title}",
                        "blueprint_id": "{blueprint_id}",
                        "design_url": "{save_design.url}"
                    },
                    dependencies=["save_design", "mockup"]
                ),
                WorkflowStep(
                    id="description",
                    name="Generate Product Description",
                    description="Create SEO-optimized product description",
                    action="generate_product_description",
                    params={
                        "product_name": "{product_title}",
                        "features": "{product_features}",
                        "tone": "engaging"
                    },
                    dependencies=["printify_product"]
                ),
                WorkflowStep(
                    id="social_content",
                    name="Create Social Media Content",
                    description="Generate social media posts for launch",
                    action="generate_social_media_posts",
                    params={
                        "product": "{product_title}",
                        "platforms": ["instagram", "facebook", "twitter"],
                        "count": 5
                    },
                    dependencies=["description", "mockup"]
                ),
                WorkflowStep(
                    id="publish",
                    name="Publish to Shopify",
                    description="Publish product to Shopify store",
                    action="printify_publish_product",
                    params={
                        "product_id": "{printify_product.id}",
                        "shop_id": "{shop_id}"
                    },
                    dependencies=["printify_product", "description"]
                ),
                WorkflowStep(
                    id="analytics",
                    name="Setup Analytics Tracking",
                    description="Configure analytics for product",
                    action="setup_product_analytics",
                    params={
                        "product_id": "{publish.shopify_product_id}",
                        "metrics": ["views", "conversions", "revenue"]
                    },
                    dependencies=["publish"],
                    optional=True
                )
            ]
        )
    
    def _create_marketing_campaign_template(self) -> WorkflowTemplate:
        """
        Complete marketing campaign workflow.
        
        Steps:
        1. Campaign strategy research
        2. Target audience analysis
        3. Content creation (ads, posts, emails)
        4. Creative assets generation
        5. Campaign setup across platforms
        6. Performance tracking
        """
        return WorkflowTemplate(
            type=WorkflowType.MARKETING_CAMPAIGN,
            name="Multi-Channel Marketing Campaign",
            description="Launch a coordinated marketing campaign across channels",
            estimated_duration="30-45 minutes",
            kpis=["ad_copies_created", "creatives_generated", "channels_activated"],
            required_integrations=["replicate"],
            steps=[
                WorkflowStep(
                    id="strategy",
                    name="Campaign Strategy",
                    description="Research and define campaign strategy",
                    action="analyze_competitor",
                    params={
                        "niche": "{campaign_niche}",
                        "goal": "{campaign_goal}"
                    },
                    dependencies=[]
                ),
                WorkflowStep(
                    id="audience",
                    name="Audience Research",
                    description="Identify and analyze target audience",
                    action="research_topic",
                    params={
                        "query": "{target_audience} demographics and interests",
                        "depth": "medium"
                    },
                    dependencies=["strategy"]
                ),
                WorkflowStep(
                    id="ad_copy",
                    name="Generate Ad Copy",
                    description="Create compelling ad copy variations",
                    action="generate_ad_copy",
                    params={
                        "product": "{product_name}",
                        "audience": "{audience.insights}",
                        "variations": 5,
                        "tone": "{brand_tone}"
                    },
                    dependencies=["audience"]
                ),
                WorkflowStep(
                    id="creatives",
                    name="Generate Creative Assets",
                    description="Create visual assets for ads",
                    action="generate_image",
                    params={
                        "prompt": "{creative_brief}",
                        "count": 3,
                        "aspect_ratio": "16:9"
                    },
                    dependencies=["strategy"]
                ),
                WorkflowStep(
                    id="social_posts",
                    name="Social Media Posts",
                    description="Create social media campaign posts",
                    action="generate_social_media_posts",
                    params={
                        "campaign": "{campaign_name}",
                        "platforms": ["instagram", "facebook", "linkedin", "twitter"],
                        "count": 10
                    },
                    dependencies=["ad_copy", "creatives"]
                ),
                WorkflowStep(
                    id="email_campaign",
                    name="Email Campaign",
                    description="Create email marketing sequence",
                    action="generate_email_campaign",
                    params={
                        "campaign_name": "{campaign_name}",
                        "sequence_length": 5,
                        "audience": "{audience.persona}"
                    },
                    dependencies=["ad_copy"]
                ),
                WorkflowStep(
                    id="tracking",
                    name="Setup Campaign Tracking",
                    description="Configure analytics and tracking",
                    action="setup_campaign_tracking",
                    params={
                        "campaign_id": "{campaign_name}",
                        "channels": ["social", "email", "ads"],
                        "kpis": ["clicks", "conversions", "roi"]
                    },
                    dependencies=["social_posts", "email_campaign"],
                    optional=True
                )
            ]
        )
    
    def _create_content_pipeline_template(self) -> WorkflowTemplate:
        """
        Content creation pipeline workflow.
        
        Steps:
        1. Topic research and trending content
        2. Content outline generation
        3. Full article/post writing
        4. SEO optimization
        5. Visual content creation
        6. Multi-platform adaptation
        7. Publishing schedule
        """
        return WorkflowTemplate(
            type=WorkflowType.CONTENT_PIPELINE,
            name="Content Creation Pipeline",
            description="End-to-end content creation and distribution",
            estimated_duration="20-30 minutes per piece",
            kpis=["articles_created", "seo_score", "platforms_published"],
            required_integrations=["replicate"],
            steps=[
                WorkflowStep(
                    id="topics",
                    name="Research Trending Topics",
                    description="Find trending topics in niche",
                    action="get_trending_topics",
                    params={
                        "niche": "{content_niche}",
                        "count": 10
                    },
                    dependencies=[]
                ),
                WorkflowStep(
                    id="outline",
                    name="Create Content Outline",
                    description="Generate detailed content outline",
                    action="generate_content_outline",
                    params={
                        "topic": "{selected_topic}",
                        "format": "{content_format}",
                        "target_length": "{word_count}"
                    },
                    dependencies=["topics"]
                ),
                WorkflowStep(
                    id="article",
                    name="Write Full Article",
                    description="Create complete article from outline",
                    action="generate_blog_post",
                    params={
                        "outline": "{outline.structure}",
                        "tone": "{brand_voice}",
                        "include_examples": True
                    },
                    dependencies=["outline"]
                ),
                WorkflowStep(
                    id="seo",
                    name="SEO Optimization",
                    description="Optimize content for search engines",
                    action="generate_seo_content",
                    params={
                        "content": "{article.text}",
                        "keywords": "{target_keywords}",
                        "meta_description": True
                    },
                    dependencies=["article"]
                ),
                WorkflowStep(
                    id="visuals",
                    name="Create Visual Content",
                    description="Generate featured images and graphics",
                    action="generate_image",
                    params={
                        "prompt": "{article.title} professional blog header",
                        "aspect_ratio": "16:9",
                        "count": 2
                    },
                    dependencies=["article"]
                ),
                WorkflowStep(
                    id="adapt",
                    name="Adapt for Platforms",
                    description="Create platform-specific versions",
                    action="adapt_content_for_platforms",
                    params={
                        "source": "{article.text}",
                        "platforms": ["linkedin", "twitter", "medium"],
                        "include_hashtags": True
                    },
                    dependencies=["article", "seo"]
                ),
                WorkflowStep(
                    id="schedule",
                    name="Create Publishing Schedule",
                    description="Plan content distribution",
                    action="create_publishing_schedule",
                    params={
                        "content": "{article.title}",
                        "platforms": "{adapt.platforms}",
                        "frequency": "optimal"
                    },
                    dependencies=["adapt"],
                    optional=True
                )
            ]
        )
    
    def _create_email_sequence_template(self) -> WorkflowTemplate:
        """
        Automated email sequence workflow.
        
        Steps:
        1. Audience segmentation analysis
        2. Sequence strategy planning
        3. Email copywriting (series)
        4. Subject line optimization
        5. CTA creation
        6. Sequence setup
        """
        return WorkflowTemplate(
            type=WorkflowType.EMAIL_SEQUENCE,
            name="Automated Email Sequence",
            description="Create and setup an automated email sequence",
            estimated_duration="25-35 minutes",
            kpis=["emails_created", "sequence_length", "expected_open_rate"],
            required_integrations=[],
            steps=[
                WorkflowStep(
                    id="segmentation",
                    name="Audience Segmentation",
                    description="Analyze and segment target audience",
                    action="analyze_audience_segments",
                    params={
                        "customer_data": "{customer_list}",
                        "segment_by": ["behavior", "demographics", "interests"]
                    },
                    dependencies=[]
                ),
                WorkflowStep(
                    id="strategy",
                    name="Sequence Strategy",
                    description="Plan email sequence strategy",
                    action="plan_email_sequence",
                    params={
                        "goal": "{sequence_goal}",
                        "audience": "{segmentation.primary_segment}",
                        "length": "{desired_length}"
                    },
                    dependencies=["segmentation"]
                ),
                WorkflowStep(
                    id="emails",
                    name="Write Email Series",
                    description="Create all emails in sequence",
                    action="generate_email_campaign",
                    params={
                        "strategy": "{strategy.plan}",
                        "sequence_length": "{strategy.recommended_length}",
                        "tone": "{brand_voice}",
                        "include_personalization": True
                    },
                    dependencies=["strategy"]
                ),
                WorkflowStep(
                    id="subject_lines",
                    name="Optimize Subject Lines",
                    description="Create compelling subject lines",
                    action="generate_subject_lines",
                    params={
                        "emails": "{emails.series}",
                        "variations_per_email": 3,
                        "optimize_for": "open_rate"
                    },
                    dependencies=["emails"]
                ),
                WorkflowStep(
                    id="ctas",
                    name="Create CTAs",
                    description="Generate effective calls-to-action",
                    action="generate_ctas",
                    params={
                        "goal": "{sequence_goal}",
                        "emails": "{emails.series}",
                        "style": "button"
                    },
                    dependencies=["emails"]
                ),
                WorkflowStep(
                    id="timing",
                    name="Optimize Send Timing",
                    description="Determine best send times",
                    action="optimize_send_timing",
                    params={
                        "audience": "{segmentation.primary_segment}",
                        "sequence": "{emails.series}",
                        "timezone": "{audience_timezone}"
                    },
                    dependencies=["emails"],
                    optional=True
                )
            ]
        )
    
    async def generate_custom_workflow(
        self,
        goal: str,
        constraints: List[str],
        available_tools: List[str]
    ) -> WorkflowTemplate:
        """
        Generate a custom workflow based on business requirements.
        
        Uses AI to create a tailored workflow for specific needs.
        """
        prompt = f"""Create a business workflow for this goal:

GOAL: {goal}

CONSTRAINTS:
{chr(10).join(f"- {c}" for c in constraints)}

AVAILABLE TOOLS:
{', '.join(available_tools)}

Design an efficient workflow with clear steps, dependencies, and success criteria.

Output JSON in this format:
{{
    "name": "Workflow Name",
    "description": "Clear description",
    "estimated_duration": "X-Y minutes",
    "kpis": ["kpi1", "kpi2"],
    "steps": [
        {{
            "id": "step_id",
            "name": "Step Name",
            "description": "What this step does",
            "action": "tool_name",
            "params": {{}},
            "dependencies": [],
            "optional": false
        }}
    ]
}}"""

        # Call orchestrator to generate workflow
        response = await self.orchestrator._call_claude(prompt, max_tokens=3000)
        
        import json
        workflow_data = json.loads(self.orchestrator._extract_json(response))
        
        # Convert to WorkflowTemplate
        steps = [
            WorkflowStep(
                id=step["id"],
                name=step["name"],
                description=step["description"],
                action=step["action"],
                params=step["params"],
                dependencies=step["dependencies"],
                optional=step.get("optional", False)
            )
            for step in workflow_data["steps"]
        ]
        
        return WorkflowTemplate(
            type=WorkflowType.PRODUCT_LAUNCH,  # Custom type
            name=workflow_data["name"],
            description=workflow_data["description"],
            steps=steps,
            estimated_duration=workflow_data["estimated_duration"],
            kpis=workflow_data["kpis"],
            required_integrations=[]
        )
    
    async def execute_workflow(
        self,
        workflow: WorkflowTemplate,
        params: Dict[str, Any],
        callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Execute a complete workflow.
        
        Args:
            workflow: Workflow template to execute
            params: Parameters to fill template placeholders
            callback: Optional callback for progress updates
            
        Returns:
            Workflow execution results
        """
        logger.info(f"Executing workflow: {workflow.name}")
        
        results = {}
        step_outputs = {}
        
        for step in workflow.steps:
            # Skip optional steps if dependencies failed
            if step.optional and any(dep not in step_outputs for dep in step.dependencies):
                logger.info(f"Skipping optional step: {step.name}")
                continue
            
            # Check dependencies
            if not all(dep in step_outputs for dep in step.dependencies):
                error = f"Step {step.id} dependencies not met"
                logger.error(error)
                results[step.id] = {"success": False, "error": error}
                continue
            
            if callback:
                await callback({
                    "type": "workflow_step",
                    "step_id": step.id,
                    "step_name": step.name,
                    "status": "starting"
                })
            
            try:
                # Fill parameter placeholders
                filled_params = self._fill_placeholders(step.params, {**params, **step_outputs})
                
                # Execute step
                tool = self.orchestrator.tool_registry.get_tool(step.action)
                if tool:
                    result = await tool.execute(**filled_params)
                    step_outputs[step.id] = result
                    results[step.id] = {"success": True, "output": result}
                    
                    if callback:
                        await callback({
                            "type": "workflow_step",
                            "step_id": step.id,
                            "step_name": step.name,
                            "status": "completed",
                            "result": result
                        })
                else:
                    error = f"Tool {step.action} not found"
                    logger.error(error)
                    results[step.id] = {"success": False, "error": error}
                    
            except Exception as e:
                logger.error(f"Step {step.id} failed: {e}")
                results[step.id] = {"success": False, "error": str(e)}
                
                if callback:
                    await callback({
                        "type": "workflow_step",
                        "step_id": step.id,
                        "step_name": step.name,
                        "status": "failed",
                        "error": str(e)
                    })
        
        # Calculate success rate
        successful = sum(1 for r in results.values() if r.get("success"))
        total = len(results)
        
        return {
            "workflow": workflow.name,
            "success_rate": successful / total if total > 0 else 0,
            "steps_completed": successful,
            "total_steps": total,
            "results": results,
            "kpis": self._calculate_workflow_kpis(workflow, results)
        }
    
    def _fill_placeholders(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fill template placeholders in parameters."""
        filled = {}
        
        for key, value in params.items():
            if isinstance(value, str) and "{" in value:
                # Simple placeholder replacement
                filled[key] = value.format(**context)
            else:
                filled[key] = value
        
        return filled
    
    def _calculate_workflow_kpis(
        self,
        workflow: WorkflowTemplate,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate KPIs for completed workflow."""
        kpis = {}
        
        # Generic KPIs
        kpis["completion_rate"] = sum(1 for r in results.values() if r.get("success")) / len(results)
        kpis["steps_executed"] = len(results)
        
        # Workflow-specific KPIs
        for kpi_name in workflow.kpis:
            # Extract KPI from results based on workflow type
            kpis[kpi_name] = self._extract_kpi_value(kpi_name, results)
        
        return kpis
    
    def _extract_kpi_value(self, kpi_name: str, results: Dict[str, Any]) -> Any:
        """Extract specific KPI value from results."""
        # Implementation depends on KPI type
        # This is a simplified version
        return len([r for r in results.values() if r.get("success")])
    
    def list_available_workflows(self) -> List[Dict[str, Any]]:
        """List all available workflow templates."""
        return [
            {
                "type": wf.type.value,
                "name": wf.name,
                "description": wf.description,
                "estimated_duration": wf.estimated_duration,
                "kpis": wf.kpis,
                "required_integrations": wf.required_integrations,
                "steps": len(wf.steps)
            }
            for wf in self.templates.values()
        ]
