"""
Enhanced Agent Delegation System
================================

A sophisticated task routing and agent specialization system that:
- Analyzes tasks to determine optimal agent assignment
- Manages specialized agent crews for different domains
- Enables intelligent delegation with context passing
- Supports multi-agent collaboration on complex tasks
- Provides detailed progress tracking and result aggregation

This creates a powerful subagent system where each agent has deep expertise.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import re

logger = logging.getLogger(__name__)


# ============================================================================
# Specialized Agent Definitions
# ============================================================================

class AgentSpecialization(Enum):
    """Highly specialized agent types with clear expertise areas."""
    
    # Creative & Content
    CONTENT_WRITER = "content_writer"
    COPYWRITER = "copywriter"
    SOCIAL_MEDIA_MANAGER = "social_media_manager"
    SEO_SPECIALIST = "seo_specialist"
    BRAND_STRATEGIST = "brand_strategist"
    
    # Visual & Design
    IMAGE_CREATOR = "image_creator"
    VIDEO_PRODUCER = "video_producer"
    UI_DESIGNER = "ui_designer"
    GRAPHIC_DESIGNER = "graphic_designer"
    
    # Technical
    CODE_DEVELOPER = "code_developer"
    CODE_REVIEWER = "code_reviewer"
    SYSTEM_ARCHITECT = "system_architect"
    DATA_ANALYST = "data_analyst"
    API_INTEGRATOR = "api_integrator"
    
    # Research & Analysis
    MARKET_RESEARCHER = "market_researcher"
    COMPETITOR_ANALYST = "competitor_analyst"
    TREND_SPOTTER = "trend_spotter"
    DATA_MINER = "data_miner"
    DEEP_RESEARCHER = "deep_researcher"  # AI-powered research without browser
    
    # Business & Operations  
    PROJECT_MANAGER = "project_manager"
    PRODUCT_STRATEGIST = "product_strategist"
    MARKETING_SPECIALIST = "marketing_specialist"
    ECOMMERCE_EXPERT = "ecommerce_expert"
    AUTOMATION_ENGINEER = "automation_engineer"
    
    # Specialized Tools
    BROWSER_OPERATOR = "browser_operator"
    FILE_MANAGER = "file_manager"
    COMMUNICATIONS_AGENT = "communications_agent"
    CALENDAR_SCHEDULER = "calendar_scheduler"
    
    # Meta/Orchestration
    TASK_ORCHESTRATOR = "task_orchestrator"
    QUALITY_ASSURER = "quality_assurer"
    CONTEXT_GATHERER = "context_gatherer"


@dataclass
class SpecializedAgentProfile:
    """Profile defining a specialized agent's capabilities."""
    specialization: AgentSpecialization
    name: str
    description: str
    expertise_keywords: List[str]
    capabilities: List[str]
    preferred_tools: List[str]
    system_prompt: str
    temperature: float = 0.7
    max_iterations: int = 5
    can_delegate_to: List[AgentSpecialization] = field(default_factory=list)
    requires_human_approval: bool = False
    
    def matches_task(self, task_text: str) -> float:
        """Calculate how well this agent matches a task (0-1 score)."""
        task_lower = task_text.lower()
        matches = 0
        total_keywords = len(self.expertise_keywords)
        
        if total_keywords == 0:
            return 0.0
            
        for keyword in self.expertise_keywords:
            if keyword.lower() in task_lower:
                matches += 1
                
        # Additional capability matching
        for capability in self.capabilities:
            if capability.lower() in task_lower:
                matches += 0.5
                
        return min(1.0, matches / total_keywords)


# ============================================================================
# Pre-configured Specialized Agents
# ============================================================================

SPECIALIZED_AGENTS: Dict[AgentSpecialization, SpecializedAgentProfile] = {
    
    AgentSpecialization.CONTENT_WRITER: SpecializedAgentProfile(
        specialization=AgentSpecialization.CONTENT_WRITER,
        name="Alex the Content Writer",
        description="Expert at creating compelling written content for any purpose",
        expertise_keywords=[
            "write", "article", "blog", "content", "story", "essay", 
            "description", "copy", "text", "narrative", "document"
        ],
        capabilities=[
            "Long-form articles", "Blog posts", "Product descriptions",
            "Email sequences", "Landing page copy", "Documentation"
        ],
        preferred_tools=["create_content", "brand_voice_generate", "seo_content"],
        system_prompt="""You are Alex, an expert content writer with 15+ years of experience.
You craft compelling, engaging content that resonates with target audiences.
Your writing is clear, persuasive, and optimized for the intended platform.
Always consider the brand voice, audience, and purpose when writing.""",
        temperature=0.8,
        can_delegate_to=[AgentSpecialization.SEO_SPECIALIST, AgentSpecialization.COPYWRITER]
    ),
    
    AgentSpecialization.COPYWRITER: SpecializedAgentProfile(
        specialization=AgentSpecialization.COPYWRITER,
        name="Maya the Copywriter",
        description="Specialist in persuasive marketing copy that converts",
        expertise_keywords=[
            "headline", "tagline", "ad copy", "marketing", "persuasive",
            "conversion", "cta", "call to action", "slogan", "hook"
        ],
        capabilities=[
            "Headlines", "Ad copy", "Email subjects", "CTAs",
            "Product taglines", "Marketing messages"
        ],
        preferred_tools=["create_content", "generate_ad_copy"],
        system_prompt="""You are Maya, a world-class copywriter specializing in conversion.
Every word you write is designed to persuade and convert.
You understand psychology, urgency, and the art of the hook.
Your copy is punchy, memorable, and drives action.""",
        temperature=0.9
    ),
    
    AgentSpecialization.SOCIAL_MEDIA_MANAGER: SpecializedAgentProfile(
        specialization=AgentSpecialization.SOCIAL_MEDIA_MANAGER,
        name="Jordan the Social Media Manager",
        description="Expert at creating and managing social media content",
        expertise_keywords=[
            "social media", "instagram", "twitter", "tiktok", "facebook",
            "linkedin", "post", "hashtag", "engagement", "viral", "reel"
        ],
        capabilities=[
            "Social posts", "Content calendars", "Hashtag strategies",
            "Engagement tactics", "Cross-platform content", "Trend riding"
        ],
        preferred_tools=["social_media_post", "content_calendar", "schedule_post"],
        system_prompt="""You are Jordan, a social media expert who knows every platform intimately.
You create content that stops the scroll and drives engagement.
You understand algorithms, trends, and what makes content shareable.
Always optimize for the specific platform and audience.""",
        temperature=0.85,
        can_delegate_to=[AgentSpecialization.IMAGE_CREATOR, AgentSpecialization.VIDEO_PRODUCER]
    ),
    
    AgentSpecialization.IMAGE_CREATOR: SpecializedAgentProfile(
        specialization=AgentSpecialization.IMAGE_CREATOR,
        name="Pixel the Image Creator",
        description="Expert at generating and editing images using AI",
        expertise_keywords=[
            "image", "photo", "picture", "generate image", "create image",
            "visual", "graphic", "illustration", "render", "design image"
        ],
        capabilities=[
            "AI image generation", "Photo editing", "Style transfer",
            "Background removal", "Image upscaling", "Visual concepts"
        ],
        preferred_tools=[
            "generate_image", "smart_image_generation", "replicate_smart_generate",
            "edit_image", "upscale_image", "remove_background"
        ],
        system_prompt="""You are Pixel, an AI art director and image generation specialist.
You craft precise prompts that create stunning visuals.
You understand composition, color theory, and aesthetic styles.
Always consider the end use when creating images.""",
        temperature=0.85
    ),
    
    AgentSpecialization.VIDEO_PRODUCER: SpecializedAgentProfile(
        specialization=AgentSpecialization.VIDEO_PRODUCER,
        name="Reel the Video Producer",
        description="Expert at creating and editing videos using AI",
        expertise_keywords=[
            "video", "clip", "movie", "animation", "generate video",
            "film", "footage", "motion", "reel", "create video"
        ],
        capabilities=[
            "AI video generation", "Video editing", "Animation",
            "Motion graphics", "Video from image", "Lip sync"
        ],
        preferred_tools=[
            "generate_ai_video", "image_to_video", "generate_video",
            "animate_image", "create_lipsync_video"
        ],
        system_prompt="""You are Reel, a video production specialist with AI expertise.
You create compelling video content using cutting-edge AI tools.
You understand cinematography, pacing, and visual storytelling.
Always select the right model for the specific video need.""",
        temperature=0.7
    ),
    
    AgentSpecialization.CODE_DEVELOPER: SpecializedAgentProfile(
        specialization=AgentSpecialization.CODE_DEVELOPER,
        name="Dev the Code Developer",
        description="Expert software developer for all programming needs",
        expertise_keywords=[
            "code", "program", "script", "function", "develop", "implement",
            "build", "create app", "api", "database", "backend", "frontend"
        ],
        capabilities=[
            "Full-stack development", "API integration", "Database design",
            "Automation scripts", "Bug fixes", "Code optimization"
        ],
        preferred_tools=["execute_code", "create_file", "modify_file"],
        system_prompt="""You are Dev, a senior full-stack developer with expertise in all languages.
You write clean, efficient, well-documented code.
You follow best practices and consider security, performance, and maintainability.
Always explain your code and design decisions.""",
        temperature=0.5,
        can_delegate_to=[AgentSpecialization.CODE_REVIEWER]
    ),
    
    AgentSpecialization.DATA_ANALYST: SpecializedAgentProfile(
        specialization=AgentSpecialization.DATA_ANALYST,
        name="Dana the Data Analyst",
        description="Expert at analyzing data and extracting insights",
        expertise_keywords=[
            "analyze", "data", "statistics", "metrics", "report", "insight",
            "trend", "pattern", "dashboard", "numbers", "performance"
        ],
        capabilities=[
            "Data analysis", "Statistical analysis", "Trend identification",
            "Report generation", "Visualization recommendations", "KPI tracking"
        ],
        preferred_tools=["analyze_file", "execute_code", "create_chart"],
        system_prompt="""You are Dana, a data analyst who turns numbers into actionable insights.
You excel at finding patterns and trends in complex data.
You communicate findings clearly with appropriate visualizations.
Always provide context and actionable recommendations.""",
        temperature=0.4
    ),
    
    AgentSpecialization.MARKET_RESEARCHER: SpecializedAgentProfile(
        specialization=AgentSpecialization.MARKET_RESEARCHER,
        name="Marco the Market Researcher",
        description="Expert at market analysis and competitive intelligence",
        expertise_keywords=[
            "market", "research", "competitor", "industry", "consumer",
            "audience", "demographic", "segment", "opportunity", "survey"
        ],
        capabilities=[
            "Market analysis", "Competitor research", "Consumer insights",
            "Industry trends", "SWOT analysis", "Market sizing"
        ],
        preferred_tools=["web_search", "browse_website", "analyze_data"],
        system_prompt="""You are Marco, a market research expert with deep analytical skills.
You uncover market opportunities and competitive insights.
You understand consumer behavior and industry dynamics.
Always provide evidence-based recommendations.""",
        temperature=0.5,
        can_delegate_to=[AgentSpecialization.BROWSER_OPERATOR, AgentSpecialization.DATA_ANALYST]
    ),
    
    AgentSpecialization.DEEP_RESEARCHER: SpecializedAgentProfile(
        specialization=AgentSpecialization.DEEP_RESEARCHER,
        name="Sage the Deep Researcher",
        description="AI-powered research expert that gathers information WITHOUT browser automation",
        expertise_keywords=[
            "research", "investigate", "study", "analyze", "explore",
            "find out", "learn about", "discover", "examine", "summarize",
            "explain", "describe", "history of", "background", "overview",
            "best practices", "strategies", "recommendations", "guide"
        ],
        capabilities=[
            "Deep topic research", "Information synthesis", "Knowledge questions",
            "Trend analysis", "Comparative analysis", "Report generation",
            "Historical research", "Best practice compilation", "Strategy research"
        ],
        preferred_tools=["search_web", "create_content", "analyze_data"],
        system_prompt="""You are Sage, expert at deep research and information synthesis.
You answer complex questions by reasoning through available knowledge.
You use web search APIs (not browser automation) to gather current information.
You synthesize multiple sources into clear, comprehensive answers.
KEY: You do NOT need to actually visit websites - use search APIs and AI reasoning.
For factual questions, knowledge research, and analysis - you are the right choice.
For interactive website tasks (login, forms, clicks) - delegate to Browser Operator.""",
        temperature=0.4,
        can_delegate_to=[AgentSpecialization.MARKET_RESEARCHER, AgentSpecialization.DATA_ANALYST]
    ),
    
    AgentSpecialization.ECOMMERCE_EXPERT: SpecializedAgentProfile(
        specialization=AgentSpecialization.ECOMMERCE_EXPERT,
        name="Echo the E-commerce Expert",
        description="Expert in e-commerce, product listing, and online sales",
        expertise_keywords=[
            "product", "listing", "store", "shop", "sell", "ecommerce",
            "printify", "shopify", "etsy", "amazon", "inventory", "pricing"
        ],
        capabilities=[
            "Product listings", "Store management", "Pricing optimization",
            "Inventory management", "Sales analytics", "Marketplace integration"
        ],
        preferred_tools=[
            "printify_create_product", "create_product_listing", 
            "optimize_product", "manage_inventory"
        ],
        system_prompt="""You are Echo, an e-commerce expert who maximizes online sales.
You understand marketplace algorithms and consumer buying behavior.
You create compelling product listings that convert.
Always optimize for both search visibility and conversion.""",
        temperature=0.6,
        can_delegate_to=[AgentSpecialization.IMAGE_CREATOR, AgentSpecialization.COPYWRITER]
    ),
    
    AgentSpecialization.BROWSER_OPERATOR: SpecializedAgentProfile(
        specialization=AgentSpecialization.BROWSER_OPERATOR,
        name="Web the Browser Operator",
        description="Expert at DIRECT website interaction requiring browser automation",
        expertise_keywords=[
            "go to", "navigate to", "click", "fill form", "login to",
            "screenshot", "scrape", "submit form", "add to cart",
            "interact with", "automate website", "download from"
        ],
        capabilities=[
            "Web navigation", "Form filling and submission", "Button clicking",
            "Screenshot capture", "Login/authentication", "E-commerce actions",
            "Data scraping from pages", "Multi-step web workflows"
        ],
        preferred_tools=[
            "browse_website", "take_screenshot", "extract_page_data",
            "click_element", "fill_form", "browser_task"
        ],
        system_prompt="""You are Web, an expert browser automation agent.
You ONLY activate for tasks that REQUIRE direct website interaction:
- Clicking buttons/links on a page
- Filling out and submitting forms
- Logging into websites
- Taking screenshots of specific pages
- Scraping data from JavaScript-rendered pages
- Multi-step navigation workflows

You DO NOT activate for:
- General research questions (use Deep Researcher)
- Information gathering via search APIs (use web_search tool)
- Knowledge questions about topics
- Analysis tasks that don't need live website data

Only use browser automation when truly necessary - it's slower and more expensive.""",
        temperature=0.3,
        can_delegate_to=[AgentSpecialization.DEEP_RESEARCHER]
    ),
    
    AgentSpecialization.PROJECT_MANAGER: SpecializedAgentProfile(
        specialization=AgentSpecialization.PROJECT_MANAGER,
        name="Pax the Project Manager",
        description="Expert at planning and coordinating complex projects",
        expertise_keywords=[
            "project", "plan", "schedule", "timeline", "milestone", "task",
            "coordinate", "manage", "deadline", "priority", "workflow"
        ],
        capabilities=[
            "Project planning", "Task breakdown", "Timeline management",
            "Resource allocation", "Progress tracking", "Risk assessment"
        ],
        preferred_tools=[
            "create_project", "add_task", "schedule_task", "track_progress"
        ],
        system_prompt="""You are Pax, an expert project manager who delivers results.
You break complex projects into manageable tasks.
You anticipate blockers and manage dependencies effectively.
Always consider timelines, resources, and realistic expectations.""",
        temperature=0.5,
        can_delegate_to=[AgentSpecialization.TASK_ORCHESTRATOR]
    ),
    
    AgentSpecialization.AUTOMATION_ENGINEER: SpecializedAgentProfile(
        specialization=AgentSpecialization.AUTOMATION_ENGINEER,
        name="Auto the Automation Engineer",
        description="Expert at creating automated workflows and processes",
        expertise_keywords=[
            "automate", "workflow", "automation", "trigger", "schedule",
            "recurring", "batch", "process", "integrate", "pipeline"
        ],
        capabilities=[
            "Workflow creation", "Task automation", "Integration setup",
            "Scheduled tasks", "Trigger configuration", "Process optimization"
        ],
        preferred_tools=[
            "create_workflow", "schedule_task", "create_automation",
            "configure_trigger"
        ],
        system_prompt="""You are Auto, an automation engineer who eliminates manual work.
You design efficient workflows that run reliably.
You integrate systems and create seamless automations.
Always consider error handling and edge cases.""",
        temperature=0.4
    ),
    
    AgentSpecialization.TASK_ORCHESTRATOR: SpecializedAgentProfile(
        specialization=AgentSpecialization.TASK_ORCHESTRATOR,
        name="Maestro the Orchestrator",
        description="Master coordinator that delegates to specialized agents",
        expertise_keywords=[
            "complex", "multi-step", "coordinate", "orchestrate", "delegate",
            "combine", "comprehensive", "full", "end-to-end"
        ],
        capabilities=[
            "Task decomposition", "Agent coordination", "Result aggregation",
            "Cross-domain tasks", "Complex workflows", "Quality assurance"
        ],
        preferred_tools=["delegate_task", "coordinate_agents", "aggregate_results"],
        system_prompt="""You are Maestro, the master orchestrator of specialized agents.
You decompose complex tasks into subtasks for specialized agents.
You coordinate their work and aggregate their results.
Always ensure quality and coherence in the final output.""",
        temperature=0.5,
        can_delegate_to=[spec for spec in AgentSpecialization if spec != AgentSpecialization.TASK_ORCHESTRATOR]
    ),
    
    AgentSpecialization.QUALITY_ASSURER: SpecializedAgentProfile(
        specialization=AgentSpecialization.QUALITY_ASSURER,
        name="Quinn the Quality Assurer",
        description="Expert at reviewing and improving work quality",
        expertise_keywords=[
            "review", "check", "verify", "quality", "improve", "refine",
            "proofread", "validate", "test", "feedback"
        ],
        capabilities=[
            "Quality review", "Proofreading", "Fact checking",
            "Improvement suggestions", "Consistency checks", "Error detection"
        ],
        preferred_tools=["review_content", "verify_facts", "suggest_improvements"],
        system_prompt="""You are Quinn, a quality assurance expert with an eye for detail.
You catch errors that others miss and suggest improvements.
You ensure consistency, accuracy, and high standards.
Always provide constructive feedback and specific suggestions.""",
        temperature=0.3
    ),
    
    AgentSpecialization.SEO_SPECIALIST: SpecializedAgentProfile(
        specialization=AgentSpecialization.SEO_SPECIALIST,
        name="Sierra the SEO Specialist",
        description="Expert at search engine optimization and organic growth",
        expertise_keywords=[
            "seo", "search", "keywords", "ranking", "organic", "backlinks",
            "meta tags", "optimization", "serp", "google", "visibility"
        ],
        capabilities=[
            "Keyword research", "On-page SEO", "Meta optimization",
            "Content optimization", "Link building", "SEO audits"
        ],
        preferred_tools=["seo_content", "keyword_research", "analyze_seo"],
        system_prompt="""You are Sierra, an SEO expert who drives organic traffic.
You understand search engine algorithms and ranking factors.
You optimize content for both users and search engines.
Always balance SEO best practices with user experience.""",
        temperature=0.5
    ),
    
    AgentSpecialization.BRAND_STRATEGIST: SpecializedAgentProfile(
        specialization=AgentSpecialization.BRAND_STRATEGIST,
        name="Blake the Brand Strategist",
        description="Expert at brand development and strategic positioning",
        expertise_keywords=[
            "brand", "strategy", "positioning", "identity", "voice", "values",
            "mission", "vision", "guidelines", "tone", "personality"
        ],
        capabilities=[
            "Brand strategy", "Voice development", "Positioning",
            "Brand guidelines", "Message architecture", "Brand audits"
        ],
        preferred_tools=["brand_analysis", "voice_development", "create_guidelines"],
        system_prompt="""You are Blake, a brand strategist who builds memorable brands.
You understand what makes brands resonate with audiences.
You develop consistent brand identities and messaging frameworks.
Always think long-term about brand equity and recognition.""",
        temperature=0.7
    ),
    
    AgentSpecialization.UI_DESIGNER: SpecializedAgentProfile(
        specialization=AgentSpecialization.UI_DESIGNER,
        name="Uma the UI Designer",
        description="Expert at user interface design and user experience",
        expertise_keywords=[
            "ui", "ux", "design", "interface", "layout", "wireframe",
            "prototype", "mockup", "usability", "accessibility"
        ],
        capabilities=[
            "UI design", "UX analysis", "Wireframing", "Prototyping",
            "Design systems", "Accessibility reviews"
        ],
        preferred_tools=["generate_image", "create_mockup", "design_review"],
        system_prompt="""You are Uma, a UI/UX designer who creates intuitive interfaces.
You understand human-computer interaction and visual hierarchy.
You design for accessibility and delight.
Always prioritize user needs and usability.""",
        temperature=0.7
    ),
    
    AgentSpecialization.GRAPHIC_DESIGNER: SpecializedAgentProfile(
        specialization=AgentSpecialization.GRAPHIC_DESIGNER,
        name="Grace the Graphic Designer",
        description="Expert at visual design for print and digital media",
        expertise_keywords=[
            "graphic design", "poster", "flyer", "banner", "brochure",
            "print", "layout", "typography", "infographic", "visual"
        ],
        capabilities=[
            "Print design", "Digital graphics", "Infographics",
            "Marketing materials", "Typography", "Visual identity"
        ],
        preferred_tools=[
            "generate_image", "smart_image_generation", "create_layout"
        ],
        system_prompt="""You are Grace, a graphic designer with an eye for composition.
You create visually stunning designs for all media types.
You understand color theory, typography, and visual hierarchy.
Always design with purpose and brand consistency.""",
        temperature=0.8
    ),
    
    AgentSpecialization.CODE_REVIEWER: SpecializedAgentProfile(
        specialization=AgentSpecialization.CODE_REVIEWER,
        name="Rex the Code Reviewer",
        description="Expert at code review and quality assurance",
        expertise_keywords=[
            "review code", "code review", "pull request", "pr", "lint",
            "standards", "refactor", "optimization", "security review"
        ],
        capabilities=[
            "Code review", "Security audit", "Performance analysis",
            "Best practices", "Refactoring suggestions", "Documentation review"
        ],
        preferred_tools=["review_code", "analyze_code", "security_scan"],
        system_prompt="""You are Rex, a senior code reviewer with deep expertise.
You identify bugs, security issues, and optimization opportunities.
You enforce coding standards and best practices.
Always provide constructive feedback with clear explanations.""",
        temperature=0.3
    ),
    
    AgentSpecialization.API_INTEGRATOR: SpecializedAgentProfile(
        specialization=AgentSpecialization.API_INTEGRATOR,
        name="Apollo the API Integrator",
        description="Expert at API integration and third-party services",
        expertise_keywords=[
            "api", "integration", "webhook", "oauth", "rest", "graphql",
            "connect", "endpoint", "authentication", "third-party"
        ],
        capabilities=[
            "API integration", "Webhook setup", "OAuth implementation",
            "Data sync", "Error handling", "Rate limiting"
        ],
        preferred_tools=["api_request", "configure_webhook", "test_integration"],
        system_prompt="""You are Apollo, an API integration specialist.
You connect systems seamlessly with reliable integrations.
You handle authentication, error cases, and edge cases.
Always implement proper error handling and logging.""",
        temperature=0.4,
        can_delegate_to=[AgentSpecialization.CODE_DEVELOPER]
    ),
    
    AgentSpecialization.COMMUNICATIONS_AGENT: SpecializedAgentProfile(
        specialization=AgentSpecialization.COMMUNICATIONS_AGENT,
        name="Chris the Communications Agent",
        description="Expert at email, messaging, and professional communications",
        expertise_keywords=[
            "email", "message", "communication", "outreach", "correspondence",
            "reply", "follow-up", "newsletter", "notification"
        ],
        capabilities=[
            "Email composition", "Response drafting", "Newsletter creation",
            "Template design", "Tone matching", "Multi-channel messaging"
        ],
        preferred_tools=["send_email", "draft_email", "create_newsletter"],
        system_prompt="""You are Chris, a communications expert who crafts perfect messages.
You adapt tone and style for any professional context.
You write clear, engaging, and action-oriented communications.
Always consider the recipient's perspective and desired outcome.""",
        temperature=0.6
    ),
    
    AgentSpecialization.CALENDAR_SCHEDULER: SpecializedAgentProfile(
        specialization=AgentSpecialization.CALENDAR_SCHEDULER,
        name="Cal the Calendar Scheduler",
        description="Expert at scheduling and calendar management",
        expertise_keywords=[
            "schedule", "calendar", "meeting", "appointment", "reminder",
            "availability", "time zone", "recurring", "booking"
        ],
        capabilities=[
            "Schedule management", "Meeting coordination", "Time optimization",
            "Recurring events", "Time zone handling", "Availability checking"
        ],
        preferred_tools=["schedule_event", "check_availability", "set_reminder"],
        system_prompt="""You are Cal, a scheduling expert who optimizes time.
You coordinate complex schedules across time zones.
You prevent conflicts and maximize productivity.
Always consider buffer times and realistic time estimates.""",
        temperature=0.3
    ),
    
    AgentSpecialization.FILE_MANAGER: SpecializedAgentProfile(
        specialization=AgentSpecialization.FILE_MANAGER,
        name="Finn the File Manager",
        description="Expert at file organization and document management",
        expertise_keywords=[
            "file", "document", "folder", "organize", "storage", "upload",
            "download", "archive", "backup", "convert"
        ],
        capabilities=[
            "File organization", "Document management", "Format conversion",
            "Archiving", "Search optimization", "Version control"
        ],
        preferred_tools=["organize_files", "convert_file", "search_files"],
        system_prompt="""You are Finn, a file management expert who brings order to chaos.
You organize files logically and maintain clean structures.
You handle conversions, backups, and retrievals efficiently.
Always maintain clear naming conventions and organization.""",
        temperature=0.3
    ),
    
    AgentSpecialization.TREND_SPOTTER: SpecializedAgentProfile(
        specialization=AgentSpecialization.TREND_SPOTTER,
        name="Tara the Trend Spotter",
        description="Expert at identifying emerging trends and opportunities",
        expertise_keywords=[
            "trend", "trending", "viral", "emerging", "popular", "buzz",
            "hot", "rising", "fashion", "culture"
        ],
        capabilities=[
            "Trend identification", "Cultural analysis", "Predictive insights",
            "Social listening", "Opportunity spotting", "Zeitgeist tracking"
        ],
        preferred_tools=["web_search", "social_analysis", "trend_report"],
        system_prompt="""You are Tara, a trend spotter with cultural intelligence.
You identify emerging trends before they go mainstream.
You understand what captures public attention.
Always provide context for why trends are emerging.""",
        temperature=0.8,
        can_delegate_to=[AgentSpecialization.MARKET_RESEARCHER]
    ),
    
    AgentSpecialization.PRODUCT_STRATEGIST: SpecializedAgentProfile(
        specialization=AgentSpecialization.PRODUCT_STRATEGIST,
        name="Pat the Product Strategist",
        description="Expert at product development and go-to-market strategy",
        expertise_keywords=[
            "product", "launch", "roadmap", "feature", "mvp", "strategy",
            "user story", "requirements", "specification"
        ],
        capabilities=[
            "Product strategy", "Feature prioritization", "Roadmapping",
            "User stories", "Market fit analysis", "Launch planning"
        ],
        preferred_tools=["create_roadmap", "prioritize_features", "market_analysis"],
        system_prompt="""You are Pat, a product strategist who builds winning products.
You balance user needs, business goals, and technical feasibility.
You prioritize ruthlessly and deliver value incrementally.
Always focus on solving real user problems.""",
        temperature=0.6,
        can_delegate_to=[AgentSpecialization.MARKET_RESEARCHER, AgentSpecialization.DATA_ANALYST]
    ),
    
    AgentSpecialization.MARKETING_SPECIALIST: SpecializedAgentProfile(
        specialization=AgentSpecialization.MARKETING_SPECIALIST,
        name="Max the Marketing Specialist",
        description="Expert at marketing campaigns and growth strategies",
        expertise_keywords=[
            "marketing", "campaign", "advertising", "promotion", "growth",
            "acquisition", "retention", "funnel", "conversion"
        ],
        capabilities=[
            "Campaign strategy", "Ad management", "Growth hacking",
            "Funnel optimization", "Attribution", "Performance marketing"
        ],
        preferred_tools=["create_campaign", "analyze_metrics", "optimize_funnel"],
        system_prompt="""You are Max, a marketing specialist who drives growth.
You create compelling campaigns that convert.
You understand the full marketing funnel.
Always measure results and optimize for ROI.""",
        temperature=0.7,
        can_delegate_to=[AgentSpecialization.COPYWRITER, AgentSpecialization.IMAGE_CREATOR]
    ),
}


# ============================================================================
# Task Analysis and Routing
# ============================================================================

@dataclass
class TaskAnalysis:
    """Analysis of a task for routing purposes."""
    task_text: str
    task_type: str
    complexity: str  # simple, moderate, complex
    domains: List[str]
    required_capabilities: List[str]
    suggested_agents: List[Tuple[AgentSpecialization, float]]  # (agent, score)
    requires_collaboration: bool
    estimated_steps: int
    # NEW: Browser vs Deep Research routing
    needs_browser: bool = False  # True if task requires browser automation
    research_method: str = "ai_reasoning"  # browser_automation, deep_research, web_search_api, ai_reasoning
    
    def get_best_agent(self) -> Optional[AgentSpecialization]:
        """Get the best-matching agent for this task."""
        if not self.suggested_agents:
            return None
        return self.suggested_agents[0][0]
    
    def get_collaboration_team(self, max_agents: int = 3) -> List[AgentSpecialization]:
        """Get a team of agents for collaboration."""
        return [agent for agent, _ in self.suggested_agents[:max_agents]]


class TaskAnalyzer:
    """Analyzes tasks to determine optimal routing."""
    
    def __init__(self):
        self.domain_keywords = {
            "creative": ["write", "create", "design", "content", "story", "art"],
            "visual": ["image", "video", "photo", "visual", "graphic", "animation"],
            "technical": ["code", "api", "database", "script", "program", "develop"],
            "research": ["research", "analyze", "find", "investigate", "study", "data"],
            "marketing": ["market", "advertise", "promote", "campaign", "brand", "seo"],
            "ecommerce": ["product", "listing", "store", "sell", "shop", "inventory"],
            "automation": ["automate", "workflow", "schedule", "trigger", "recurring"],
            "browser_interaction": ["click", "fill form", "login to", "navigate to", "screenshot", "scrape"]
        }
        
        # Patterns that REQUIRE browser interaction (direct website control)
        self.browser_required_patterns = [
            # Navigation and interaction
            "go to", "navigate to", "open website", "visit the site",
            "click on", "click the", "press button", "tap on",
            "fill out", "fill in", "fill form", "submit form",
            # Authentication
            "login to", "log in to", "sign in to", "authenticate",
            "create account on", "register on",
            # E-commerce actions
            "add to cart", "checkout on", "buy on", "purchase on", "place order on",
            # Screenshots and captures
            "take screenshot", "screenshot of", "capture page",
            # Scraping and extraction (various forms)
            "scrape website", "scrape page", "scrape from", "scrape the",
            "scrape data", "scrape product", "scrape price",
            "extract from website", "extract from page",
            # Interactive automation
            "automate the website", "interact with", "on the website"
        ]
        
        # Patterns for deep research (AI + search APIs, NO browser needed)
        self.deep_research_patterns = [
            # Research verbs
            "research", "investigate", "study", "examine", "explore",
            "learn about", "find out about", "discover",
            # Information queries
            "what is", "who is", "how does", "why do", "explain",
            "tell me about", "describe", "summarize", "overview",
            # Analysis
            "analyze", "compare", "contrast", "evaluate", "assess",
            "market analysis", "competitor analysis", "trend analysis",
            # Knowledge gathering
            "find information", "gather data", "look up",
            "best practices", "recommendations", "strategies", "tips for"
        ]
        
        self.complexity_indicators = {
            "complex": [
                "comprehensive", "full", "complete", "end-to-end", "multi-step",
                "detailed", "thorough", "all", "everything", "entire"
            ],
            "moderate": [
                "several", "few", "some", "multiple", "various"
            ],
            "simple": [
                "quick", "simple", "single", "one", "just", "only"
            ]
        }
    
    def analyze(self, task_text: str) -> TaskAnalysis:
        """Analyze a task and return routing recommendations."""
        task_lower = task_text.lower()
        
        # Determine domains
        domains = []
        for domain, keywords in self.domain_keywords.items():
            if any(kw in task_lower for kw in keywords):
                domains.append(domain)
        
        if not domains:
            domains = ["general"]
        
        # ========================================
        # ENHANCED: Browser vs Deep Research Detection
        # ========================================
        browser_required = any(pattern in task_lower for pattern in self.browser_required_patterns)
        deep_research = any(pattern in task_lower for pattern in self.deep_research_patterns)
        
        # Check for URL patterns that suggest browser interaction
        has_url = any(x in task_lower for x in ['http://', 'https://', 'www.'])
        has_site_action = any(x in task_lower for x in [
            'on amazon', 'on ebay', 'on twitter', 'on facebook', 
            'on the website', 'on this page', 'on linkedin'
        ])
        
        # Determine research method
        if browser_required and not deep_research:
            research_method = "browser_automation"
            needs_browser = True
        elif deep_research and not browser_required:
            research_method = "deep_research"
            needs_browser = False
        elif browser_required and deep_research:
            # Both patterns - use context to decide
            needs_browser = has_url or has_site_action
            research_method = "browser_automation" if needs_browser else "deep_research"
        else:
            # Default: favor deep research (faster, cheaper)
            needs_browser = has_url and has_site_action
            research_method = "browser_automation" if needs_browser else "ai_reasoning"
        
        # Determine complexity
        complexity = "moderate"  # default
        for level, indicators in self.complexity_indicators.items():
            if any(ind in task_lower for ind in indicators):
                complexity = level
                break
        
        # Score agents with browser/research bias
        agent_scores: List[Tuple[AgentSpecialization, float]] = []
        for spec, profile in SPECIALIZED_AGENTS.items():
            score = profile.matches_task(task_text)
            
            # Apply bias based on detected research method
            if needs_browser and spec == AgentSpecialization.BROWSER_OPERATOR:
                score *= 1.5  # Boost browser operator for browser tasks
            elif not needs_browser and spec == AgentSpecialization.DEEP_RESEARCHER:
                score *= 1.5  # Boost deep researcher for research tasks
            elif not needs_browser and spec == AgentSpecialization.BROWSER_OPERATOR:
                score *= 0.3  # Penalize browser operator for non-browser tasks
            
            if score > 0:
                agent_scores.append((spec, score))
        
        # Sort by score descending
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Determine if collaboration needed
        requires_collaboration = (
            complexity == "complex" or 
            len(domains) > 1 or
            (len(agent_scores) > 1 and agent_scores[0][1] < 0.6)
        )
        
        # Estimate steps
        if complexity == "simple":
            estimated_steps = 2
        elif complexity == "moderate":
            estimated_steps = 5
        else:
            estimated_steps = 10
        
        # Determine task type with research method consideration
        if needs_browser:
            task_type = "browser_interaction"
        elif any(d in domains for d in ["visual", "creative"]):
            task_type = "creative"
        elif "technical" in domains:
            task_type = "technical"
        elif "research" in domains or research_method == "deep_research":
            task_type = "research"
        elif "ecommerce" in domains:
            task_type = "commerce"
        else:
            task_type = "general"
        
        # Extract required capabilities
        required_capabilities = []
        for spec, profile in SPECIALIZED_AGENTS.items():
            for cap in profile.capabilities:
                if cap.lower() in task_lower:
                    required_capabilities.append(cap)
        
        return TaskAnalysis(
            task_text=task_text,
            task_type=task_type,
            complexity=complexity,
            domains=domains,
            required_capabilities=list(set(required_capabilities)),
            suggested_agents=agent_scores[:5],
            requires_collaboration=requires_collaboration,
            estimated_steps=estimated_steps,
            # New fields for browser/research routing
            needs_browser=needs_browser,
            research_method=research_method
        )


# ============================================================================
# Enhanced Delegation Manager
# ============================================================================

@dataclass
class DelegationResult:
    """Result from a delegated task."""
    success: bool
    agent: AgentSpecialization
    result: Any
    duration_seconds: float
    steps_taken: int
    delegated_to: List[AgentSpecialization] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "agent": self.agent.value,
            "result": self.result,
            "duration_seconds": self.duration_seconds,
            "steps_taken": self.steps_taken,
            "delegated_to": [a.value for a in self.delegated_to],
            "errors": self.errors
        }


class EnhancedDelegationManager:
    """
    Manages intelligent task delegation to specialized agents.
    """
    
    def __init__(
        self,
        anthropic_client: Any = None,
        tool_registry: Any = None,
        on_status: Optional[Callable] = None
    ):
        self.anthropic = anthropic_client
        self.tool_registry = tool_registry
        self.task_analyzer = TaskAnalyzer()
        self.on_status = on_status or (lambda x: None)
        self.active_delegations: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Enhanced Delegation Manager initialized")
    
    async def delegate(
        self,
        task_text: str,
        context: Optional[Dict[str, Any]] = None,
        preferred_agent: Optional[AgentSpecialization] = None,
        allow_collaboration: bool = True
    ) -> DelegationResult:
        """
        Delegate a task to the most appropriate specialized agent(s).
        """
        start_time = datetime.now()
        
        # Analyze the task
        analysis = self.task_analyzer.analyze(task_text)
        
        self.on_status({
            "type": "delegation_started",
            "task": task_text[:100],
            "analysis": {
                "complexity": analysis.complexity,
                "domains": analysis.domains,
                "suggested_agents": [(a.value, s) for a, s in analysis.suggested_agents[:3]]
            }
        })
        
        # Determine which agent(s) to use
        if preferred_agent:
            primary_agent = preferred_agent
        else:
            best_agent = analysis.get_best_agent()
            if best_agent:
                primary_agent = best_agent
            else:
                primary_agent = AgentSpecialization.TASK_ORCHESTRATOR
        
        profile = SPECIALIZED_AGENTS.get(primary_agent)
        if not profile:
            primary_agent = AgentSpecialization.TASK_ORCHESTRATOR
            profile = SPECIALIZED_AGENTS[AgentSpecialization.TASK_ORCHESTRATOR]
        
        self.on_status({
            "type": "agent_selected",
            "agent": primary_agent.value,
            "agent_name": profile.name,
            "match_score": next((s for a, s in analysis.suggested_agents if a == primary_agent), 0)
        })
        
        # Execute task with agent
        try:
            if analysis.requires_collaboration and allow_collaboration:
                result = await self._execute_collaborative(
                    task_text=task_text,
                    analysis=analysis,
                    context=context
                )
            else:
                result = await self._execute_with_agent(
                    task_text=task_text,
                    agent=primary_agent,
                    profile=profile,
                    context=context
                )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return DelegationResult(
                success=True,
                agent=primary_agent,
                result=result,
                duration_seconds=duration,
                steps_taken=result.get("steps", 1) if isinstance(result, dict) else 1,
                delegated_to=result.get("delegated_to", []) if isinstance(result, dict) else []
            )
            
        except Exception as e:
            logger.error(f"Delegation failed: {e}", exc_info=True)
            duration = (datetime.now() - start_time).total_seconds()
            
            return DelegationResult(
                success=False,
                agent=primary_agent,
                result=None,
                duration_seconds=duration,
                steps_taken=0,
                errors=[str(e)]
            )
    
    async def _execute_with_agent(
        self,
        task_text: str,
        agent: AgentSpecialization,
        profile: SpecializedAgentProfile,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a task with a specific specialized agent."""
        
        self.on_status({
            "type": "agent_working",
            "agent": profile.name,
            "task": task_text[:100]
        })
        
        # Build the agent's prompt
        context_str = json.dumps(context, indent=2) if context else "None"
        
        prompt = f"""{profile.system_prompt}

## Your Task
{task_text}

## Available Context
{context_str}

## Your Available Tools
{', '.join(profile.preferred_tools)}

## Instructions
1. Analyze the task carefully
2. Create a plan to accomplish it
3. Execute the plan step by step
4. Verify your results
5. Provide a clear summary of what you accomplished

Think through this step by step and provide your complete response."""

        # If we have an Anthropic client, use it
        if self.anthropic:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.anthropic.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    temperature=profile.temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
            )
            
            result_text = response.content[0].text
            
            return {
                "agent": agent.value,
                "agent_name": profile.name,
                "result": result_text,
                "steps": 1
            }
        else:
            # Mock response for testing
            return {
                "agent": agent.value,
                "agent_name": profile.name,
                "result": f"[{profile.name}] would execute: {task_text}",
                "steps": 1
            }
    
    async def _execute_collaborative(
        self,
        task_text: str,
        analysis: TaskAnalysis,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a complex task with multiple collaborating agents."""
        
        team = analysis.get_collaboration_team(max_agents=3)
        
        self.on_status({
            "type": "team_assembled",
            "team": [a.value for a in team],
            "task_complexity": analysis.complexity
        })
        
        results = []
        
        # Orchestrator first breaks down the task
        orchestrator_profile = SPECIALIZED_AGENTS[AgentSpecialization.TASK_ORCHESTRATOR]
        
        decomposition_prompt = f"""As the orchestrator, break down this complex task into subtasks for specialists:

Task: {task_text}

Available specialists:
{chr(10).join(f'- {SPECIALIZED_AGENTS[a].name}: {SPECIALIZED_AGENTS[a].description}' for a in team)}

Create a plan that assigns specific subtasks to each specialist.
Format as JSON with structure: {{"subtasks": [{{"agent": "agent_name", "task": "specific subtask"}}]}}"""

        if self.anthropic:
            decomp_response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.anthropic.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=2048,
                    temperature=0.5,
                    messages=[{"role": "user", "content": decomposition_prompt}]
                )
            )
            
            # Parse subtasks (simplified - would need proper JSON extraction)
            decomp_text = decomp_response.content[0].text
            
            # Execute with each team member
            for agent_spec in team:
                profile = SPECIALIZED_AGENTS[agent_spec]
                
                self.on_status({
                    "type": "agent_contributing",
                    "agent": profile.name
                })
                
                result = await self._execute_with_agent(
                    task_text=f"As part of the team task '{task_text}', contribute your expertise.",
                    agent=agent_spec,
                    profile=profile,
                    context=context
                )
                results.append(result)
        
        # Aggregate results
        self.on_status({
            "type": "aggregating_results",
            "num_results": len(results)
        })
        
        return {
            "collaborative": True,
            "team": [a.value for a in team],
            "results": results,
            "delegated_to": team,
            "steps": len(team) + 2  # decomposition + each agent + aggregation
        }
    
    def get_available_agents(self) -> List[Dict[str, Any]]:
        """Get list of all available specialized agents."""
        return [
            {
                "id": spec.value,
                "name": profile.name,
                "description": profile.description,
                "capabilities": profile.capabilities,
                "expertise": profile.expertise_keywords[:5]
            }
            for spec, profile in SPECIALIZED_AGENTS.items()
        ]
    
    def get_agent_for_task(self, task_text: str) -> Dict[str, Any]:
        """Get the recommended agent for a task."""
        analysis = self.task_analyzer.analyze(task_text)
        best = analysis.get_best_agent()
        
        if best:
            profile = SPECIALIZED_AGENTS[best]
            return {
                "agent_id": best.value,
                "agent_name": profile.name,
                "match_score": analysis.suggested_agents[0][1] if analysis.suggested_agents else 0,
                "requires_collaboration": analysis.requires_collaboration,
                "complexity": analysis.complexity
            }
        
        return {
            "agent_id": "task_orchestrator",
            "agent_name": "Maestro the Orchestrator",
            "match_score": 0,
            "requires_collaboration": True,
            "complexity": analysis.complexity
        }


# ============================================================================
# Singleton Instance
# ============================================================================

_delegation_manager: Optional[EnhancedDelegationManager] = None

def get_delegation_manager(
    anthropic_client: Any = None,
    tool_registry: Any = None,
    on_status: Optional[Callable] = None
) -> EnhancedDelegationManager:
    """Get or create the delegation manager singleton."""
    global _delegation_manager
    
    if _delegation_manager is None:
        _delegation_manager = EnhancedDelegationManager(
            anthropic_client=anthropic_client,
            tool_registry=tool_registry,
            on_status=on_status
        )
    
    return _delegation_manager


def reset_delegation_manager():
    """Reset the delegation manager (for testing)."""
    global _delegation_manager
    _delegation_manager = None
