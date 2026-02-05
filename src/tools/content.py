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
        description="Generate a beautiful, SEO-optimized blog post with rich HTML formatting, product images, and store links. Ideal for direct Shopify publishing.",
        category="content"
    )
    async def generate_blog_post(
        self,
        topic: str,
        keywords: Optional[List[str]] = None,
        word_count: int = 1200,
        style: str = "informative",
        tone: Optional[str] = None,
        include_outline: bool = False,
        length: Optional[str] = None,
        # Advanced customization
        target_demographic: str = "general",
        industry: Optional[str] = None,
        brand_voice: str = "professional yet approachable",
        include_trending: bool = True,
        include_statistics: bool = True,
        include_quotes: bool = True,
        cta_type: str = "product",
        product_link: Optional[str] = None,
        rich_html: bool = True,
        featured_image_suggestion: bool = True,
        # Product-specific parameters for Shopify integration
        product_name: Optional[str] = None,
        product_image_url: Optional[str] = None,
        product_description: Optional[str] = None,
        product_price: Optional[str] = None,
        shopify_product_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a beautiful, SEO-optimized blog post with rich HTML ready for Shopify.
        
        Args:
            topic: Blog post topic
            keywords: SEO keywords to include naturally
            word_count: Target word count (default 1200 for SEO)
            style: Writing style (informative, entertaining, tutorial, listicle, storytelling, expert-roundup)
            tone: Content tone (informative, engaging, professional, casual, inspiring, authoritative)
            include_outline: Include outline before full post
            length: Content length hint (short: 600, medium: 1200, long-form: 2000, pillar: 3000)
            target_demographic: Target audience (gen-z, millennials, professionals, parents, seniors, entrepreneurs)
            industry: Industry context (fashion, tech, health, finance, lifestyle, etc.)
            brand_voice: Brand personality description
            include_trending: Include current trends and timely references
            include_statistics: Include relevant statistics and data points
            include_quotes: Include expert quotes or testimonials
            cta_type: CTA type (product, newsletter, social, consultation, download)
            product_link: Product/service link for CTA
            rich_html: Output beautiful HTML with styling (default True)
            featured_image_suggestion: Include AI image generation prompt suggestion
            product_name: Name of the product to feature
            product_image_url: URL to product image/mockup to embed in blog
            product_description: Product description for context
            product_price: Product price for purchase CTA
            shopify_product_url: Direct Shopify store link for "Shop Now" button
        """
        # Handle tone as alias for style
        if tone and not style:
            style = tone
        elif tone:
            style = tone
            
        # Handle length hint
        if length:
            length_map = {"short": 600, "medium": 1200, "long-form": 2000, "long": 2000, "pillar": 3000}
            word_count = length_map.get(length.lower(), word_count)
            
        keywords_text = ", ".join(keywords) if keywords else "relevant terms"
        industry_context = f" in the {industry} industry" if industry else ""
        
        # Build product section for blog
        product_section_instruction = ""
        if product_name or product_image_url or shopify_product_url:
            product_section_instruction = f"""

=== PRODUCT FEATURE SECTION ===
Include a prominent product showcase section in the blog with:

PRODUCT DETAILS:
- Product Name: {product_name or 'Featured Product'}
- Product Description: {product_description or 'A great product'}
- Price: {product_price or 'Check store for pricing'}
- Image URL: {product_image_url or '[Product Image]'}
- Shop Link: {shopify_product_url or product_link or '[Shop Link]'}

REQUIRED HTML for product showcase (place prominently in article):
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 16px; margin: 30px 0; text-align: center;">
  <h3 style="color: white; margin-bottom: 15px;">✨ {product_name or 'Featured Product'}</h3>
  {f'<img src="{product_image_url}" alt="{product_name}" style="max-width: 300px; border-radius: 12px; margin: 15px 0; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">' if product_image_url else ''}
  <p style="color: rgba(255,255,255,0.9); margin: 15px 0;">{product_description or 'Check out this amazing product!'}</p>
  {f'<p style="color: white; font-size: 1.5em; font-weight: bold;">{product_price}</p>' if product_price else ''}
  <a href="{shopify_product_url or product_link or '#'}" style="display: inline-block; background: white; color: #667eea; padding: 14px 28px; border-radius: 30px; text-decoration: none; font-weight: bold; margin-top: 10px;">🛒 Shop Now</a>
</div>
"""
        
        # Demographic-specific guidance
        demo_guide = {
            "gen-z": "Use casual language, current slang (appropriately), reference social media trends, TikTok-friendly formatting, short punchy paragraphs",
            "millennials": "Balance nostalgia with current relevance, include pop culture references, relatable humor, value-focused content",
            "professionals": "Data-driven, efficiency-focused, industry insights, actionable takeaways, professional but not stuffy",
            "parents": "Time-saving tips, family-focused benefits, relatable struggles, practical solutions, trustworthy tone",
            "seniors": "Clear and accessible language, established credibility, comprehensive explanations, traditional values with modern relevance",
            "entrepreneurs": "ROI-focused, growth strategies, case studies, actionable frameworks, inspiring success stories",
            "general": "Broad appeal, accessible language, universal benefits, diverse examples"
        }
        demographic_guidance = demo_guide.get(target_demographic.lower(), demo_guide["general"])
        
        # CTA guidance with Shopify link
        cta_link = shopify_product_url or product_link
        cta_guide = {
            "product": f"Drive to product page" + (f": {cta_link}" if cta_link else ""),
            "newsletter": "Email subscription signup",
            "social": "Social media follow/engagement",
            "consultation": "Book a call/consultation",
            "download": "Download a free resource/guide"
        }
        cta_instruction = cta_guide.get(cta_type, cta_guide["product"])
        
        system_prompt = f"""You are an elite content strategist and SEO copywriter{industry_context}.

Brand Voice: {brand_voice}
Target Demographic: {target_demographic}
Demographic Writing Guide: {demographic_guidance}

Your content is known for:
- Exceptional readability (Flesch score 60+)
- Natural keyword integration that doesn't feel forced
- Compelling hooks that stop scrollers
- Value-packed content that gets shared
- Perfect SEO structure (H1, H2, H3 hierarchy)
- Emotional resonance with the target audience
- Mobile-friendly formatting"""

        html_instructions = """

=== RICH HTML OUTPUT FORMAT ===
Output the blog as beautiful, semantic HTML with these elements:

1. STRUCTURE:
   - Use proper heading hierarchy: <h1> for title, <h2> for sections, <h3> for subsections
   - Wrap paragraphs in <p> tags
   - Use <strong> for key phrases, <em> for emphasis
   
2. VISUAL ELEMENTS:
   - Use <blockquote> for quotes with attribution
   - Use styled lists: <ul> and <ol> with engaging content
   - Include <hr> dividers between major sections
   
3. CALL-OUT BOXES (use these div patterns):
   - Key insight: <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; color: white; margin: 20px 0;"><strong>💡 Key Insight:</strong> [content]</div>
   - Pro tip: <div style="background: #f0fdf4; border-left: 4px solid #22c55e; padding: 16px; margin: 20px 0;"><strong>✨ Pro Tip:</strong> [content]</div>
   - Warning/Note: <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 16px; margin: 20px 0;"><strong>⚠️ Note:</strong> [content]</div>
   - Statistics: <div style="background: #eff6ff; border-left: 4px solid #3b82f6; padding: 16px; margin: 20px 0;"><strong>📊 By The Numbers:</strong> [stats]</div>

4. FEATURED QUOTE STYLE:
   <blockquote style="font-size: 1.25em; font-style: italic; border-left: 4px solid #8b5cf6; padding-left: 20px; margin: 30px 0; color: #4b5563;">
   "Quote text here"
   <footer style="font-size: 0.875em; margin-top: 8px; color: #6b7280;">— Attribution</footer>
   </blockquote>

5. CTA BUTTON (end of article):
   <div style="text-align: center; margin: 40px 0;">
   <a href="#" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 16px 32px; border-radius: 30px; text-decoration: none; font-weight: bold; font-size: 1.1em;">🚀 [CTA Text]</a>
   </div>

6. TABLE OF CONTENTS (for long posts):
   <nav style="background: #f8fafc; padding: 20px; border-radius: 12px; margin: 20px 0;">
   <strong>📑 In This Article:</strong>
   <ol style="margin-top: 10px;">...</ol>
   </nav>
""" if rich_html else "\nOutput as clean markdown."
        
        user_prompt = f"""Write a {word_count}-word blog post about: {topic}

PRIMARY SEO KEYWORDS (use naturally 3-5 times each): {keywords_text}

CONTENT REQUIREMENTS:

1. HEADLINE SECTION:
   - One powerful main headline (H1) - use power words, numbers, or questions
   - 2 alternative headlines
   - Meta description (155 characters max, includes primary keyword)
   - Suggested URL slug

2. INTRODUCTION (150-200 words):
   - Hook that creates immediate curiosity or addresses pain point
   - Establish relevance to reader's life
   - Preview the value they'll get
   - Include primary keyword in first 100 words

3. BODY CONTENT:
   - {"Include 5-7 main sections with H2 headings" if word_count > 1000 else "Include 3-4 main sections with H2 headings"}
   - Use H3 for subsections where appropriate
   - Short paragraphs (2-3 sentences max for mobile readability)
   - Bullet points and numbered lists for scanability
   {"- Include 2-3 relevant statistics with sources" if include_statistics else ""}
   {"- Include 1-2 expert quotes or testimonials" if include_quotes else ""}
   {"- Reference current trends and timely examples" if include_trending else ""}
   - Include practical, actionable advice
   - Add 2-3 call-out boxes (tips, insights, warnings)

4. CONCLUSION:
   - Summarize key takeaways
   - Emotional/motivational close
   - Clear CTA: {cta_instruction}

5. BONUS ELEMENTS:
   - FAQ section with 3-4 questions (good for featured snippets)
   - Related internal link suggestions
   {"- Suggested featured image: Describe ideal AI-generated image" if featured_image_suggestion else ""}
{html_instructions}
{product_section_instruction}
{"Start with an outline, then write the full post." if include_outline else ""}"""
        
        content = await self._generate(system_prompt, user_prompt, max_tokens=8192)
        
        # Extract meta information if present
        meta_description = ""
        suggested_slug = ""
        if "meta description" in content.lower():
            import re
            meta_match = re.search(r'meta description[:\s]*["\']?([^"\n]{50,160})["\']?', content, re.IGNORECASE)
            if meta_match:
                meta_description = meta_match.group(1).strip()
        
        return {
            "success": True,
            "topic": topic,
            "content": content,
            "style": style,
            "target_words": word_count,
            "target_demographic": target_demographic,
            "keywords": keywords,
            "meta_description": meta_description,
            "rich_html": rich_html,
            "ready_for_shopify": True,
            "product_name": product_name,
            "product_image_url": product_image_url,
            "shopify_product_url": shopify_product_url
        }
    
    @tool(
        name="generate_social_media_posts",
        description="Generate product-focused social media content with proper product imagery and links for multiple platforms",
        category="content"
    )
    async def generate_social_media_posts(
        self,
        topic: str,
        platforms: Optional[List[str]] = None,
        tone: str = "engaging",
        include_hashtags: bool = True,
        product_link: Optional[str] = None,
        # Product-specific parameters
        product_name: Optional[str] = None,
        product_type: Optional[str] = None,
        product_image_url: Optional[str] = None,
        product_description: Optional[str] = None,
        product_price: Optional[str] = None,
        brand_name: Optional[str] = None,
        target_audience: str = "general",
        include_image_prompts: bool = True
    ) -> Dict[str, Any]:
        """
        Generate product-focused social media posts with proper imagery.
        
        Args:
            topic: Post topic or product to promote
            platforms: List of platforms (instagram, twitter, facebook, tiktok, linkedin)
            tone: Tone of posts
            include_hashtags: Include relevant hashtags
            product_link: Link to product page (Shopify/store URL)
            product_name: Actual product name for featuring
            product_type: Product type (mug, t-shirt, poster, etc.)
            product_image_url: Direct URL to product image/mockup
            product_description: Product description for context
            product_price: Product price for promotional posts
            brand_name: Brand name for attribution
            target_audience: Target demographic
            include_image_prompts: Generate AI image prompts that feature the product
        """
        platforms = platforms or ["instagram", "twitter", "facebook"]
        
        # Build product context for better content
        product_context = ""
        if product_name or product_type:
            product_context = f"""
PRODUCT DETAILS (Feature these prominently!):
- Product Name: {product_name or 'N/A'}
- Product Type: {product_type or 'N/A'}
- Description: {product_description or 'N/A'}
- Price: {product_price or 'N/A'}
- Brand: {brand_name or 'N/A'}
- Product Image/Mockup URL: {product_image_url or 'N/A'}
- Store Link: {product_link or 'N/A'}

CRITICAL: The social posts MUST:
1. Reference the actual product by name
2. Describe the product visually (colors, design, style)
3. Include calls-to-action directing to the product
4. If there's a product image URL, include it in posts that support images
5. Generate image prompts that SHOW THE ACTUAL PRODUCT (not generic lifestyle images)
"""
        
        system_prompt = f"""You are a social media marketing expert specializing in e-commerce and product promotion.
Create {tone}, platform-optimized content that:
- Showcases the ACTUAL PRODUCT (not generic content)
- Describes product features and benefits
- Creates desire and urgency to purchase
- Drives traffic to the product page
- Uses product imagery effectively

Target Audience: {target_audience}
{product_context}"""
        
        platform_specs = """
Platform specifications:
- Instagram: 2200 char max, visual focus, 30 hashtags max. Include [IMAGE: mockup/product photo] placeholder.
- Twitter/X: 280 char max, punchy and direct. Can include image link.
- Facebook: Longer form OK, conversational. Include product image placeholder.
- TikTok: Trendy, casual, hook-focused. Include [VIDEO CONCEPT] describing product showcase.
- LinkedIn: Professional, value-driven. Product in professional context.
"""
        
        image_prompt_instruction = """

FOR EACH PLATFORM, include an AI IMAGE GENERATION PROMPT that:
- Features the ACTUAL PRODUCT prominently (describe it specifically)
- Shows the product in an appealing context
- Matches platform aesthetic (Instagram = lifestyle, Facebook = relatable, etc.)
- Is NOT generic - it must describe THIS specific product

Format: 🖼️ IMAGE PROMPT: [detailed product-focused image description]
""" if include_image_prompts else ""
        
        user_prompt = f"""Create social media posts about: {topic}

Platforms: {', '.join(platforms)}

{platform_specs}

Requirements for each platform:
1. Platform-optimized copy that features the PRODUCT
2. Emoji usage appropriate to platform
{"3. 15-20 highly relevant hashtags including product-specific ones" if include_hashtags else ""}
{"4. Clear CTA directing to: " + product_link if product_link else "4. Clear CTA to shop/learn more"}
{image_prompt_instruction}

IMPORTANT: 
- Do NOT write generic marketing content
- FEATURE the actual product in every post
- If product details provided, USE THEM specifically
- Include product image URL where platforms support it

Format clearly by platform with all elements."""
        
        content = await self._generate(system_prompt, user_prompt, max_tokens=4096)
        
        return {
            "success": True,
            "topic": topic,
            "platforms": platforms,
            "posts": content,
            "product_name": product_name,
            "product_image_url": product_image_url,
            "product_link": product_link,
            "includes_image_prompts": include_image_prompts
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
        description="Generate high-converting advertising copy for any platform with platform-specific optimization",
        category="content"
    )
    async def generate_ad_copy(
        self,
        product: str,
        platform: str = "facebook",
        objective: str = "conversions",
        target_audience: str = "general",
        num_variants: int = 3,
        # Advanced customization
        demographic: str = "general",
        pain_points: Optional[List[str]] = None,
        unique_selling_points: Optional[List[str]] = None,
        competitor_differentiation: Optional[str] = None,
        price_point: Optional[str] = None,
        urgency_type: Optional[str] = None,
        social_proof: Optional[str] = None,
        brand_voice: str = "confident and relatable",
        landing_page_url: Optional[str] = None,
        include_image_prompts: bool = True
    ) -> Dict[str, Any]:
        """
        Generate high-converting ad copy variants for any platform.
        
        Args:
            product: Product or service to advertise
            platform: Ad platform (facebook, google, instagram, tiktok, linkedin, pinterest, youtube, twitter, snapchat)
            objective: Campaign objective (awareness, traffic, conversions, leads, app_installs, video_views)
            target_audience: Target demographic description
            num_variants: Number of ad variants to generate
            demographic: Specific demographic (gen-z, millennials, professionals, parents, etc.)
            pain_points: Customer pain points to address
            unique_selling_points: Key USPs to highlight
            competitor_differentiation: How you're different from competitors
            price_point: Price or price range (for urgency/value messaging)
            urgency_type: Urgency trigger (limited-time, limited-stock, seasonal, none)
            social_proof: Social proof to include (reviews, testimonials, numbers)
            brand_voice: Brand personality for copy tone
            landing_page_url: Destination URL for CTA
            include_image_prompts: Include AI image generation prompts for ad creatives
        """
        system_prompt = f"""You are an elite performance marketing copywriter who has generated $100M+ in ad revenue.

Brand Voice: {brand_voice}
Target Demographic: {demographic}

Your ads are known for:
- Scroll-stopping hooks that grab attention in 0.5 seconds
- Emotional triggers that create immediate action
- Platform-native copy that feels organic
- Clear value propositions that overcome objections
- CTAs that convert browsers into buyers"""
        
        platform_specs = {
            "facebook": {
                "format": "Primary text (125 chars ideal, 500 max), Headline (40 chars), Description (30 chars), CTA button",
                "tips": "Use emotional hooks, ask questions, use emojis strategically, leverage social proof"
            },
            "instagram": {
                "format": "Caption (2200 chars max, first 125 visible), Hashtags (5-10 relevant), Story/Reel hooks",
                "tips": "Visual-first thinking, lifestyle focus, authentic tone, trending audio suggestions"
            },
            "google": {
                "format": "Headlines (30 chars x15), Descriptions (90 chars x4), Display headlines (30 chars x5)",
                "tips": "Keyword-rich, benefit-focused, include numbers and specifics, urgency words"
            },
            "tiktok": {
                "format": "Hook (first 1-3 seconds), Body, CTA. Casual captions with trending language",
                "tips": "Trend-aware, native feel, problem-agitate-solve, user-generated content style"
            },
            "linkedin": {
                "format": "Sponsored content (600 chars), InMail (500 chars), Carousel (10 cards)",
                "tips": "Professional tone, B2B value props, industry insights, career/business benefits"
            },
            "pinterest": {
                "format": "Pin title (100 chars), Description (500 chars), Rich pins format",
                "tips": "Aspirational, how-to focused, seasonal relevance, keyword-rich descriptions"
            },
            "youtube": {
                "format": "Video title (70 chars), Description (5000 chars), Bumper (6 sec script), Pre-roll (15-30 sec)",
                "tips": "Hook in first 5 seconds, pattern interrupt, curiosity gaps, clear CTA"
            },
            "twitter": {
                "format": "Tweet (280 chars), Thread (up to 25 tweets), Card headline (70 chars)",
                "tips": "Punchy and direct, conversation starters, timely hooks, engagement bait"
            },
            "snapchat": {
                "format": "Single image/video (5-6 sec), Story ads (3-5 seconds per), Collection ads",
                "tips": "Instant impact, mobile-first, AR/filter suggestions, youth-focused language"
            }
        }
        
        spec = platform_specs.get(platform, platform_specs['facebook'])
        
        pain_text = f"\\nCustomer Pain Points:\\n" + "\\n".join(f"- {p}" for p in pain_points) if pain_points else ""
        usp_text = f"\\nUnique Selling Points:\\n" + "\\n".join(f"- {u}" for u in unique_selling_points) if unique_selling_points else ""
        
        urgency_text = ""
        if urgency_type:
            urgency_map = {
                "limited-time": "Create FOMO with time-sensitive language (ends soon, last chance, today only)",
                "limited-stock": "Create scarcity (only X left, selling fast, almost gone)",
                "seasonal": "Tie to current season/holiday/event",
                "launch": "New/fresh/first-to-know excitement"
            }
            urgency_text = f"\\nUrgency Strategy: {urgency_map.get(urgency_type, urgency_type)}"
        
        user_prompt = f"""Create {num_variants} high-converting ad variants for: {product}

PLATFORM: {platform.upper()}
FORMAT REQUIREMENTS: {spec['format']}
PLATFORM BEST PRACTICES: {spec['tips']}

CAMPAIGN DETAILS:
- Objective: {objective}
- Target Audience: {target_audience}
{pain_text}
{usp_text}
{f"- Competitor Differentiation: {competitor_differentiation}" if competitor_differentiation else ""}
{f"- Price Point: {price_point}" if price_point else ""}
{urgency_text}
{f"- Social Proof: {social_proof}" if social_proof else ""}
{f"- Landing Page: {landing_page_url}" if landing_page_url else ""}

FOR EACH VARIANT, PROVIDE:
1. 🎯 Angle/Hook Type (e.g., Problem-Solution, Social Proof, FOMO, Aspirational, Educational)
2. 📝 All required copy elements for the platform
3. 🎨 Target emotion (fear, desire, curiosity, belonging, pride)
4. 💡 Why this approach works for the target audience
{"5. 🖼️ AI Image Generation Prompt for creative (describe ideal ad image)" if include_image_prompts else ""}

Make each variant COMPLETELY different in approach and emotional angle.
Include A/B testing recommendations."""
        
        content = await self._generate(system_prompt, user_prompt, max_tokens=4096)
        
        return {
            "success": True,
            "product": product,
            "platform": platform,
            "objective": objective,
            "target_audience": target_audience,
            "num_variants": num_variants,
            "variants": content,
            "includes_image_prompts": include_image_prompts
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
