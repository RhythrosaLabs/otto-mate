"""
Content Generation Tools
========================

Tools for generating various types of content.
"""

import logging
from typing import Optional, Dict, Any, List
from anthropic import Anthropic
from .core import tool, ToolBase

logger = logging.getLogger(__name__)


class ContentTools(ToolBase):
    """AI-powered content generation tools."""
    
    def __init__(self, anthropic_client: Anthropic):
        self.anthropic = anthropic_client
        self.model = "claude-sonnet-4-20250514"
    
    async def _generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2048
    ) -> str:
        """Generate content using Claude."""
        response = self.anthropic.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        return response.content[0].text
    
    @tool(
        name="generate_product_description",
        description="Generate a compelling product description",
        category="content"
    )
    async def generate_product_description(
        self,
        product_name: str,
        product_type: str,
        features: Optional[List[str]] = None,
        target_audience: str = "general",
        tone: str = "professional",
        include_seo: bool = True
    ) -> Dict[str, Any]:
        """
        Generate product description.
        
        Args:
            product_name: Name of the product
            product_type: Type of product (t-shirt, mug, etc.)
            features: Key features to highlight
            target_audience: Target customer demographic
            tone: Writing tone (professional, casual, fun, luxury)
            include_seo: Include SEO-optimized elements
        """
        features_text = "\n".join(f"- {f}" for f in features) if features else "Standard quality"
        
        system_prompt = f"""You are an expert e-commerce copywriter. Write compelling, 
        {tone} product descriptions that convert browsers into buyers. 
        Target audience: {target_audience}"""
        
        user_prompt = f"""Write a product description for:
        
Product: {product_name}
Type: {product_type}
Features:
{features_text}

Include:
1. Attention-grabbing headline
2. Engaging product description (150-200 words)
3. Key benefits bullet points
4. Call to action
{"5. SEO keywords and meta description" if include_seo else ""}

Format the output clearly with sections."""
        
        content = await self._generate(system_prompt, user_prompt)
        
        return {
            "success": True,
            "product_name": product_name,
            "description": content,
            "tone": tone
        }
    
    @tool(
        name="generate_blog_post",
        description="Generate a full blog post",
        category="content"
    )
    async def generate_blog_post(
        self,
        topic: str,
        keywords: Optional[List[str]] = None,
        word_count: int = 800,
        style: str = "informative",
        include_outline: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a blog post.
        
        Args:
            topic: Blog post topic
            keywords: SEO keywords to include
            word_count: Target word count
            style: Writing style (informative, entertaining, tutorial, listicle)
            include_outline: Include outline before full post
        """
        keywords_text = ", ".join(keywords) if keywords else "relevant terms"
        
        system_prompt = f"""You are a skilled content writer specializing in {style} blog posts.
        Write engaging, well-structured content that provides value to readers."""
        
        user_prompt = f"""Write a {word_count}-word blog post about: {topic}

Keywords to naturally incorporate: {keywords_text}

Requirements:
1. Compelling headline (and 2 alternatives)
2. Engaging introduction
3. Well-organized body with subheadings
4. Practical insights or actionable tips
5. Strong conclusion with call to action
6. Meta description (150 characters)

{"Start with an outline, then write the full post." if include_outline else ""}"""
        
        content = await self._generate(system_prompt, user_prompt, max_tokens=4096)
        
        return {
            "success": True,
            "topic": topic,
            "content": content,
            "style": style,
            "target_words": word_count
        }
    
    @tool(
        name="generate_social_media_posts",
        description="Generate social media content for multiple platforms",
        category="content"
    )
    async def generate_social_media_posts(
        self,
        topic: str,
        platforms: Optional[List[str]] = None,
        tone: str = "engaging",
        include_hashtags: bool = True,
        product_link: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate social media posts.
        
        Args:
            topic: Post topic or product to promote
            platforms: List of platforms (instagram, twitter, facebook, tiktok, linkedin)
            tone: Tone of posts
            include_hashtags: Include relevant hashtags
            product_link: Link to include
        """
        platforms = platforms or ["instagram", "twitter", "facebook"]
        
        system_prompt = f"""You are a social media marketing expert. Create {tone}, 
        platform-optimized content that drives engagement and conversions."""
        
        platform_specs = """
Platform specifications:
- Instagram: 2200 char max, visual focus, 30 hashtags max
- Twitter/X: 280 char max, punchy and direct
- Facebook: Longer form OK, conversational
- TikTok: Trendy, casual, hook-focused
- LinkedIn: Professional, value-driven
"""
        
        user_prompt = f"""Create social media posts about: {topic}

Platforms: {', '.join(platforms)}

{platform_specs}

Requirements for each platform:
1. Platform-optimized copy
2. Emoji usage appropriate to platform
{"3. Relevant hashtags" if include_hashtags else ""}
{"4. Include CTA with link: " + product_link if product_link else ""}

Format clearly by platform."""
        
        content = await self._generate(system_prompt, user_prompt)
        
        return {
            "success": True,
            "topic": topic,
            "platforms": platforms,
            "posts": content
        }
    
    @tool(
        name="generate_email_campaign",
        description="Generate email marketing content",
        category="content"
    )
    async def generate_email_campaign(
        self,
        campaign_type: str,
        product_or_topic: str,
        audience: str = "customers",
        num_emails: int = 3,
        include_subject_lines: bool = True
    ) -> Dict[str, Any]:
        """
        Generate email campaign content.
        
        Args:
            campaign_type: Type (welcome, promotional, newsletter, abandoned_cart, launch)
            product_or_topic: What the campaign is about
            audience: Target audience
            num_emails: Number of emails in sequence
            include_subject_lines: Include subject line variants
        """
        system_prompt = """You are an email marketing specialist. Create compelling email 
        sequences that drive opens, clicks, and conversions while maintaining brand voice."""
        
        user_prompt = f"""Create a {num_emails}-email sequence for a {campaign_type} campaign.

Topic/Product: {product_or_topic}
Audience: {audience}

For each email include:
1. {"3 subject line options" if include_subject_lines else "Subject line"}
2. Preview text
3. Email body (with clear structure)
4. Call to action
5. Suggested send timing

Make each email build on the previous while standing alone."""
        
        content = await self._generate(system_prompt, user_prompt, max_tokens=4096)
        
        return {
            "success": True,
            "campaign_type": campaign_type,
            "emails": content,
            "num_emails": num_emails
        }
    
    @tool(
        name="generate_ad_copy",
        description="Generate advertising copy for various platforms",
        category="content"
    )
    async def generate_ad_copy(
        self,
        product: str,
        platform: str = "facebook",
        objective: str = "conversions",
        target_audience: str = "general",
        num_variants: int = 3
    ) -> Dict[str, Any]:
        """
        Generate ad copy variants.
        
        Args:
            product: Product or service to advertise
            platform: Ad platform (facebook, google, instagram, tiktok)
            objective: Campaign objective (awareness, traffic, conversions)
            target_audience: Target demographic
            num_variants: Number of ad variants to generate
        """
        system_prompt = f"""You are a performance marketing expert specializing in {platform} ads.
        Create high-converting ad copy optimized for {objective}."""
        
        platform_specs = {
            "facebook": "Primary text (125 chars), Headline (40 chars), Description (30 chars)",
            "google": "Headlines (30 chars x3), Descriptions (90 chars x2)",
            "instagram": "Caption (2200 chars max), focus on visual hook",
            "tiktok": "Hook (first 3 seconds text), casual tone, trending language"
        }
        
        user_prompt = f"""Create {num_variants} ad variants for: {product}

Platform: {platform}
Objective: {objective}
Target: {target_audience}

Specs: {platform_specs.get(platform, platform_specs['facebook'])}

For each variant include:
1. All required copy elements
2. Target emotion/angle (e.g., FOMO, social proof, problem-solution)
3. Suggested creative direction

Make each variant distinctly different in approach."""
        
        content = await self._generate(system_prompt, user_prompt)
        
        return {
            "success": True,
            "product": product,
            "platform": platform,
            "variants": content
        }
    
    @tool(
        name="improve_text",
        description="Improve or rewrite existing text",
        category="content"
    )
    async def improve_text(
        self,
        text: str,
        goal: str = "clarity",
        maintain_length: bool = True
    ) -> Dict[str, Any]:
        """
        Improve existing text.
        
        Args:
            text: Text to improve
            goal: Improvement goal (clarity, engagement, seo, conversion, tone)
            maintain_length: Keep similar length
        """
        system_prompt = f"""You are an expert editor. Improve text for {goal} 
        while maintaining the original meaning and intent."""
        
        user_prompt = f"""Improve this text for {goal}:

{text}

{"Maintain similar length." if maintain_length else "Length can vary."}

Provide:
1. Improved version
2. Brief explanation of changes made"""
        
        content = await self._generate(system_prompt, user_prompt)
        
        return {
            "success": True,
            "original": text,
            "improved": content,
            "goal": goal
        }
    
    @tool(
        name="generate_seo_content",
        description="Generate SEO-optimized content elements",
        category="content"
    )
    async def generate_seo_content(
        self,
        page_topic: str,
        target_keywords: List[str],
        page_type: str = "product"
    ) -> Dict[str, Any]:
        """
        Generate SEO content elements.
        
        Args:
            page_topic: What the page is about
            target_keywords: Primary and secondary keywords
            page_type: Type of page (product, blog, landing, category)
        """
        system_prompt = """You are an SEO specialist. Create optimized content 
        elements that rank well while maintaining quality and readability."""
        
        user_prompt = f"""Generate SEO elements for a {page_type} page about: {page_topic}

Target keywords: {', '.join(target_keywords)}

Create:
1. Meta title (50-60 chars) - 3 options
2. Meta description (150-160 chars) - 3 options
3. H1 heading
4. H2 subheadings (5-7)
5. URL slug suggestion
6. Image alt text suggestions (5)
7. Internal linking opportunities
8. Schema markup recommendations"""
        
        content = await self._generate(system_prompt, user_prompt)
        
        return {
            "success": True,
            "topic": page_topic,
            "keywords": target_keywords,
            "seo_elements": content
        }
