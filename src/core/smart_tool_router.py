"""
Smart Tool Router
================

Intelligently routes user requests to optimal tools and chains them
for complex multi-step operations.

Key Capabilities:
- Intent-to-tool mapping
- Automatic tool chaining for complex requests
- Parameter inference from context
- Fallback and alternative tool selection
- Cost/speed optimization
- Cross-tool output passing
"""

import logging
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Callable
from datetime import datetime
from enum import Enum
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    """Categories of tools for routing."""
    IMAGE_GENERATION = "image_generation"
    VIDEO_GENERATION = "video_generation"
    AUDIO_GENERATION = "audio_generation"
    CONTENT_WRITING = "content_writing"
    PRODUCT_CREATION = "product_creation"
    MARKETING = "marketing"
    RESEARCH = "research"
    DATA_ANALYSIS = "data_analysis"
    FILE_OPERATIONS = "file_operations"
    COMMUNICATION = "communication"
    AUTOMATION = "automation"
    UTILITIES = "utilities"


@dataclass
class ToolCapability:
    """Describes a tool's capabilities."""
    tool_name: str
    category: ToolCategory
    description: str
    
    # Input/output types
    input_types: List[str] = field(default_factory=list)  # text, image_url, file, etc.
    output_types: List[str] = field(default_factory=list)
    
    # Keywords that trigger this tool
    trigger_keywords: List[str] = field(default_factory=list)
    
    # Can chain with these tools
    chains_to: List[str] = field(default_factory=list)
    chains_from: List[str] = field(default_factory=list)
    
    # Execution properties
    avg_execution_time_ms: int = 1000
    requires_api_key: Optional[str] = None
    cost_tier: int = 1  # 1-5, higher = more expensive
    
    # Success tracking
    success_rate: float = 0.95
    last_used: Optional[datetime] = None


@dataclass
class ToolChain:
    """A planned chain of tools to execute."""
    chain_id: str
    steps: List[Dict[str, Any]]
    total_estimated_time_ms: int
    requires_user_confirmation: bool = False
    can_parallelize: List[List[int]] = field(default_factory=list)  # Steps that can run in parallel


@dataclass
class RoutingDecision:
    """Result of routing analysis."""
    primary_tool: str
    alternate_tools: List[str]
    confidence: float
    requires_chaining: bool
    chain: Optional[ToolChain] = None
    parameter_suggestions: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""


class SmartToolRouter:
    """
    Intelligently routes requests to optimal tools.
    
    Unlike simple keyword matching, this router:
    - Understands intent, not just keywords
    - Suggests parameter values from context
    - Chains tools automatically for complex requests
    - Learns from usage patterns
    - Handles ambiguity gracefully
    """
    
    def __init__(self, anthropic_client: Anthropic, tool_registry: Any = None):
        self.anthropic = anthropic_client
        self.model = "claude-sonnet-4-20250514"
        self.tool_registry = tool_registry
        
        # Build capability map
        self.tools: Dict[str, ToolCapability] = {}
        self._initialize_tool_capabilities()
        
        # Usage tracking
        self.usage_history: List[Dict[str, Any]] = []
        
        logger.info("Smart Tool Router initialized")
    
    def _initialize_tool_capabilities(self):
        """Initialize known tool capabilities."""
        # Image Generation Tools
        self.register_tool(ToolCapability(
            tool_name="generate_image",
            category=ToolCategory.IMAGE_GENERATION,
            description="Generate AI images from text prompts",
            input_types=["text"],
            output_types=["image_url"],
            trigger_keywords=[
                "image", "picture", "photo", "generate", "create", "design",
                "draw", "illustrate", "visualize", "artwork", "graphic"
            ],
            chains_to=["create_product", "generate_social_media_posts", "edit_image_with_ai"],
            avg_execution_time_ms=5000,
            requires_api_key="REPLICATE_API_TOKEN",
            cost_tier=2
        ))
        
        self.register_tool(ToolCapability(
            tool_name="edit_image_with_ai",
            category=ToolCategory.IMAGE_GENERATION,
            description="Edit images using AI (upscale, remove background, etc.)",
            input_types=["image_url", "text"],
            output_types=["image_url"],
            trigger_keywords=[
                "edit", "modify", "upscale", "enhance", "remove background",
                "change", "adjust", "fix", "improve", "colorize"
            ],
            chains_from=["generate_image"],
            chains_to=["create_product"],
            avg_execution_time_ms=8000,
            cost_tier=3
        ))
        
        # Product Creation Tools
        self.register_tool(ToolCapability(
            tool_name="create_product",
            category=ToolCategory.PRODUCT_CREATION,
            description="Create products on Printify",
            input_types=["image_url", "text"],
            output_types=["product_id", "product_url"],
            trigger_keywords=[
                "product", "merch", "merchandise", "shirt", "mug", "hoodie",
                "sell", "store", "printify", "print on demand", "pod"
            ],
            chains_from=["generate_image", "edit_image_with_ai"],
            chains_to=["publish_product", "generate_social_media_posts"],
            avg_execution_time_ms=3000,
            requires_api_key="PRINTIFY_API_TOKEN",
            cost_tier=1
        ))
        
        self.register_tool(ToolCapability(
            tool_name="publish_product",
            category=ToolCategory.PRODUCT_CREATION,
            description="Publish product to Shopify store",
            input_types=["product_id"],
            output_types=["shopify_url"],
            trigger_keywords=[
                "publish", "list", "go live", "launch", "release"
            ],
            chains_from=["create_product"],
            chains_to=["generate_social_media_posts", "generate_blog_post"],
            avg_execution_time_ms=2000
        ))
        
        # Content Writing Tools
        self.register_tool(ToolCapability(
            tool_name="generate_blog_post",
            category=ToolCategory.CONTENT_WRITING,
            description="Generate SEO-optimized blog posts with AI images",
            input_types=["text"],
            output_types=["html", "text"],
            trigger_keywords=[
                "blog", "article", "post", "write", "content",
                "seo", "marketing content"
            ],
            chains_to=["publish_to_shopify", "generate_social_media_posts"],
            avg_execution_time_ms=15000,
            cost_tier=2
        ))
        
        self.register_tool(ToolCapability(
            tool_name="generate_email_campaign",
            category=ToolCategory.CONTENT_WRITING,
            description="Generate email marketing campaigns",
            input_types=["text"],
            output_types=["html", "text"],
            trigger_keywords=[
                "email", "newsletter", "campaign", "mail", "outreach"
            ],
            chains_to=["send_email", "schedule_email"],
            avg_execution_time_ms=10000,
            cost_tier=2
        ))
        
        self.register_tool(ToolCapability(
            tool_name="generate_social_media_posts",
            category=ToolCategory.MARKETING,
            description="Generate social media content for multiple platforms",
            input_types=["text", "image_url"],
            output_types=["text"],
            trigger_keywords=[
                "social media", "instagram", "twitter", "facebook", "tiktok",
                "post", "caption", "hashtag", "linkedin"
            ],
            chains_from=["generate_image", "create_product", "generate_blog_post"],
            chains_to=["schedule_post", "post_to_platform"],
            avg_execution_time_ms=5000
        ))
        
        # Marketing Tools
        self.register_tool(ToolCapability(
            tool_name="generate_product_ads",
            category=ToolCategory.MARKETING,
            description="Generate professional product advertisements",
            input_types=["image_url", "text"],
            output_types=["image_url"],
            trigger_keywords=[
                "ad", "advertisement", "marketing", "promotion", "campaign",
                "facebook ad", "instagram ad"
            ],
            chains_from=["generate_image", "create_product"],
            avg_execution_time_ms=8000,
            cost_tier=3
        ))
        
        # Research Tools
        self.register_tool(ToolCapability(
            tool_name="web_search",
            category=ToolCategory.RESEARCH,
            description="Search the web for information",
            input_types=["text"],
            output_types=["text", "urls"],
            trigger_keywords=[
                "search", "find", "look up", "research", "google",
                "who is", "what is", "information about"
            ],
            chains_to=["summarize", "generate_blog_post"],
            avg_execution_time_ms=3000
        ))
        
        # Video Tools
        self.register_tool(ToolCapability(
            tool_name="generate_video",
            category=ToolCategory.VIDEO_GENERATION,
            description="Generate AI videos from prompts or images",
            input_types=["text", "image_url"],
            output_types=["video_url"],
            trigger_keywords=[
                "video", "animate", "animation", "motion", "clip",
                "film", "movie"
            ],
            chains_from=["generate_image"],
            chains_to=["add_audio", "upload_to_youtube"],
            avg_execution_time_ms=60000,
            cost_tier=5
        ))
        
        # Audio Tools
        self.register_tool(ToolCapability(
            tool_name="generate_voice",
            category=ToolCategory.AUDIO_GENERATION,
            description="Generate AI voiceover",
            input_types=["text"],
            output_types=["audio_url"],
            trigger_keywords=[
                "voice", "voiceover", "narration", "speak", "audio",
                "text to speech", "tts"
            ],
            chains_to=["compose_video_with_audio"],
            avg_execution_time_ms=5000,
            cost_tier=2
        ))
        
        self.register_tool(ToolCapability(
            tool_name="generate_music",
            category=ToolCategory.AUDIO_GENERATION,
            description="Generate AI music",
            input_types=["text"],
            output_types=["audio_url"],
            trigger_keywords=[
                "music", "song", "soundtrack", "beat", "melody",
                "background music"
            ],
            chains_to=["compose_video_with_audio"],
            avg_execution_time_ms=30000,
            cost_tier=3
        ))
    
    def register_tool(self, capability: ToolCapability):
        """Register a tool capability."""
        self.tools[capability.tool_name] = capability
    
    def route(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None,
        available_outputs: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """
        Route a user request to optimal tools.
        
        Args:
            user_request: The user's natural language request
            context: Optional context (session data, previous actions)
            available_outputs: Outputs from previous tool calls
            
        Returns:
            RoutingDecision with tool(s) and parameters
        """
        request_lower = user_request.lower()
        
        # Score all tools
        tool_scores: Dict[str, float] = {}
        for tool_name, capability in self.tools.items():
            score = self._score_tool(request_lower, capability, context)
            if score > 0:
                tool_scores[tool_name] = score
        
        # If no tools matched, use AI to determine
        if not tool_scores:
            return self._ai_route(user_request, context, available_outputs)
        
        # Get top tools
        sorted_tools = sorted(tool_scores.items(), key=lambda x: x[1], reverse=True)
        primary_tool = sorted_tools[0][0]
        alternates = [t[0] for t in sorted_tools[1:4]]
        
        # Check if chaining is needed
        chain = None
        requires_chaining = self._check_if_chaining_needed(user_request, primary_tool, context)
        
        if requires_chaining:
            chain = self._build_chain(user_request, primary_tool, context, available_outputs)
        
        # Infer parameters
        params = self._infer_parameters(user_request, primary_tool, context, available_outputs)
        
        return RoutingDecision(
            primary_tool=primary_tool,
            alternate_tools=alternates,
            confidence=sorted_tools[0][1],
            requires_chaining=requires_chaining,
            chain=chain,
            parameter_suggestions=params,
            reasoning=f"Matched keywords for {primary_tool}"
        )
    
    def _score_tool(
        self,
        request_lower: str,
        capability: ToolCapability,
        context: Optional[Dict[str, Any]]
    ) -> float:
        """Score how well a tool matches the request."""
        score = 0.0
        
        # Keyword matching
        for keyword in capability.trigger_keywords:
            if keyword in request_lower:
                # Longer keywords are more specific
                score += 0.1 * len(keyword.split())
        
        # Exact phrase bonus
        if capability.tool_name.replace("_", " ") in request_lower:
            score += 0.5
        
        # Context bonus
        if context:
            # If previous output matches input type, boost
            if context.get("last_output_type") in capability.input_types:
                score += 0.3
            
            # If this tool commonly follows the last tool
            if context.get("last_tool") in capability.chains_from:
                score += 0.4
        
        # Usage frequency bonus (learned preference)
        usage_count = sum(
            1 for h in self.usage_history[-50:]
            if h.get("tool") == capability.tool_name
        )
        score += usage_count * 0.02
        
        return min(score, 1.0)
    
    def _check_if_chaining_needed(
        self,
        request: str,
        primary_tool: str,
        context: Optional[Dict[str, Any]]
    ) -> bool:
        """Determine if tool chaining is needed."""
        request_lower = request.lower()
        
        # Explicit chaining words
        chain_indicators = [
            "and then", "after that", "followed by",
            "then", "also", "and also", "additionally"
        ]
        if any(ind in request_lower for ind in chain_indicators):
            return True
        
        # Multi-step requests
        multi_step_patterns = [
            r"create.*and.*publish",
            r"design.*and.*sell",
            r"generate.*and.*post",
            r"make.*and.*upload",
            r"write.*and.*send",
        ]
        if any(re.search(pat, request_lower) for pat in multi_step_patterns):
            return True
        
        return False
    
    def _build_chain(
        self,
        request: str,
        primary_tool: str,
        context: Optional[Dict[str, Any]],
        available_outputs: Optional[Dict[str, Any]]
    ) -> ToolChain:
        """Build a chain of tools to execute."""
        steps = []
        current_tool = self.tools.get(primary_tool)
        
        if not current_tool:
            return ToolChain(
                chain_id=f"chain_{datetime.now().timestamp()}",
                steps=[{"tool": primary_tool, "params": {}}],
                total_estimated_time_ms=5000
            )
        
        # Step 1: Primary tool
        params = self._infer_parameters(request, primary_tool, context, available_outputs)
        steps.append({
            "step": 1,
            "tool": primary_tool,
            "params": params,
            "output_key": f"{primary_tool}_output"
        })
        
        # Find subsequent tools from chain patterns
        request_lower = request.lower()
        total_time = current_tool.avg_execution_time_ms
        
        for chain_to in current_tool.chains_to:
            chain_capability = self.tools.get(chain_to)
            if chain_capability:
                # Check if this tool is mentioned or implied
                if any(kw in request_lower for kw in chain_capability.trigger_keywords):
                    steps.append({
                        "step": len(steps) + 1,
                        "tool": chain_to,
                        "params": {
                            "input_from": f"{primary_tool}_output"
                        },
                        "output_key": f"{chain_to}_output"
                    })
                    total_time += chain_capability.avg_execution_time_ms
        
        return ToolChain(
            chain_id=f"chain_{datetime.now().timestamp()}",
            steps=steps,
            total_estimated_time_ms=total_time,
            requires_user_confirmation=len(steps) > 3
        )
    
    def _infer_parameters(
        self,
        request: str,
        tool_name: str,
        context: Optional[Dict[str, Any]],
        available_outputs: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Infer parameter values from request and context."""
        params = {}
        request_lower = request.lower()
        
        # Common parameter inference patterns
        
        # Style/aesthetic
        styles = [
            "photorealistic", "anime", "cartoon", "minimalist", "vintage",
            "modern", "retro", "elegant", "professional", "casual"
        ]
        for style in styles:
            if style in request_lower:
                params["style"] = style
                break
        
        # Aspect ratio
        if any(w in request_lower for w in ["portrait", "tall", "vertical"]):
            params["aspect_ratio"] = "2:3"
        elif any(w in request_lower for w in ["landscape", "wide", "horizontal"]):
            params["aspect_ratio"] = "16:9"
        elif any(w in request_lower for w in ["square"]):
            params["aspect_ratio"] = "1:1"
        elif any(w in request_lower for w in ["phone", "story", "reels", "tiktok"]):
            params["aspect_ratio"] = "9:16"
        
        # Product type
        product_types = [
            "t-shirt", "shirt", "mug", "hoodie", "poster", "canvas",
            "tote bag", "phone case", "pillow", "blanket"
        ]
        for pt in product_types:
            if pt in request_lower:
                params["product_type"] = pt
                break
        
        # Platform
        platforms = ["instagram", "twitter", "facebook", "linkedin", "tiktok"]
        matched_platforms = [p for p in platforms if p in request_lower]
        if matched_platforms:
            params["platforms"] = matched_platforms
        
        # Number/count
        count_match = re.search(r'(\d+)\s*(images?|products?|posts?|variations?)', request_lower)
        if count_match:
            params["count"] = int(count_match.group(1))
        
        # Use available outputs
        if available_outputs:
            if "image_url" in available_outputs and tool_name in ["create_product", "edit_image_with_ai"]:
                params["image_url"] = available_outputs["image_url"]
            if "product_id" in available_outputs and tool_name in ["publish_product"]:
                params["product_id"] = available_outputs["product_id"]
        
        return params
    
    def _ai_route(
        self,
        request: str,
        context: Optional[Dict[str, Any]],
        available_outputs: Optional[Dict[str, Any]]
    ) -> RoutingDecision:
        """Use AI to route when keyword matching fails."""
        tool_descriptions = "\n".join([
            f"- {name}: {cap.description}"
            for name, cap in self.tools.items()
        ])
        
        system = f"""You are a tool routing expert. Given a user request, determine the best tool(s) to use.

Available tools:
{tool_descriptions}

Respond in JSON:
{{
    "primary_tool": "tool_name",
    "alternates": ["tool2", "tool3"],
    "confidence": 0.0-1.0,
    "reasoning": "why this tool",
    "parameters": {{"param": "value"}}
}}"""
        
        response = self.anthropic.messages.create(
            model=self.model,
            max_tokens=512,
            system=system,
            messages=[{"role": "user", "content": request}]
        )
        
        try:
            result = json.loads(response.content[0].text)
            return RoutingDecision(
                primary_tool=result.get("primary_tool", "generate_image"),
                alternate_tools=result.get("alternates", []),
                confidence=result.get("confidence", 0.5),
                requires_chaining=False,
                parameter_suggestions=result.get("parameters", {}),
                reasoning=result.get("reasoning", "AI routing")
            )
        except (json.JSONDecodeError, KeyError):
            # Fallback
            return RoutingDecision(
                primary_tool="generate_image",
                alternate_tools=[],
                confidence=0.3,
                requires_chaining=False,
                reasoning="Fallback routing"
            )
    
    def record_usage(
        self,
        tool_name: str,
        success: bool,
        execution_time_ms: int
    ):
        """Record tool usage for learning."""
        self.usage_history.append({
            "tool": tool_name,
            "success": success,
            "time_ms": execution_time_ms,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update success rate
        if tool_name in self.tools:
            tool = self.tools[tool_name]
            tool.last_used = datetime.now()
            
            # Rolling success rate from last 20 uses
            recent = [
                h for h in self.usage_history[-100:]
                if h.get("tool") == tool_name
            ][-20:]
            
            if recent:
                tool.success_rate = sum(1 for h in recent if h.get("success")) / len(recent)


def get_smart_router(anthropic_client: Anthropic, tool_registry: Any = None) -> SmartToolRouter:
    """Factory function."""
    return SmartToolRouter(anthropic_client, tool_registry)
