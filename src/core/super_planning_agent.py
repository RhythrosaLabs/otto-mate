"""
Super Planning Agent - Hyper-Intelligent Autonomous Task Parsing & Delegation
==============================================================================

An ultra-intelligent agent that automatically parses complex requests,
breaks them into optimal subtasks, identifies parallelizable work,
and delegates to the right tools with zero user intervention.

ENHANCED with Platform Intelligence from research on:
- n8n, Zapier (workflow automation patterns)
- Canva, Firefly, Stability AI (creative tool patterns)
- Quivr, CrewAI (multi-agent patterns)
- browser-use, Claude Computer Use (browser automation)
- Replicate (model selection intelligence)
"""

import asyncio
import logging
import json
import re
from typing import Any, Dict, List, Optional
from anthropic import Anthropic

logger = logging.getLogger(__name__)

# Import platform intelligence for enhanced planning
try:
    from .platform_intelligence import get_platform_intelligence, WORKFLOW_TEMPLATES as PLATFORM_WORKFLOWS
    PLATFORM_INTEL_AVAILABLE = True
except ImportError:
    PLATFORM_INTEL_AVAILABLE = False
    PLATFORM_WORKFLOWS = {}


# ============================================================================
# WORKFLOW TYPE DETECTION - Based on printify_clean/orchestrator.py
# ============================================================================

WORKFLOW_TYPES = {
    "full_campaign_with_video": {
        "keywords": ["campaign", "video", "commercial", "promo", "advertisement"],
        "requires_product": True,
        "steps_template": ["design", "description", "video_script", "video", "social_posts", "summary"]
    },
    "product_campaign": {
        "keywords": ["t-shirt", "tshirt", "hoodie", "mug", "poster", "product", "merch", "merchandise"],
        "requires_product": True,
        "steps_template": ["design", "product_copy", "tags", "marketing_copy"]
    },
    "video_production": {
        "keywords": ["video", "commercial", "animation", "clip", "promo video"],
        "requires_product": False,
        "steps_template": ["video_script", "thumbnail", "video"]
    },
    "content_creation": {
        "keywords": ["blog", "article", "content", "write", "copy", "post", "email", "newsletter"],
        "requires_product": False,
        "steps_template": ["research", "outline", "full_content", "header_image"]
    },
    "social_media": {
        "keywords": ["social", "twitter", "instagram", "facebook", "tiktok", "linkedin", "post"],
        "requires_product": False,
        "steps_template": ["social_posts", "hashtags", "schedule"]
    },
    "research": {
        "keywords": ["research", "analyze", "trend", "market", "competitor", "find", "search"],
        "requires_product": False,
        "steps_template": ["research", "summarize", "report"]
    },
    "image_creation": {
        "keywords": ["image", "design", "illustration", "logo", "artwork", "generate", "create"],
        "requires_product": False,
        "steps_template": ["image_generation"]
    }
}

# ============================================================================
# INTENT PATTERNS - Based on printify_clean/ultra_smart_executor.py
# ============================================================================

INTENT_PATTERNS = {
    # Image generation intents
    r"(generat|creat|mak|produc|render).*(image|picture|photo|art|illustration|design)": "image_generation",
    r"(text|prompt)\s*to\s*(image|picture)": "image_generation",
    r"(draw|paint|design|visualize)": "image_generation",
    
    # Image editing intents
    r"(edit|modif|chang|transform|alter|adjust).*(image|photo|picture)": "image_editing",
    r"(style|filter|effect|enhance)": "image_editing",
    r"(remove|delete|erase).*(background|object|element)": "background_removal",
    r"(inpaint|fill|replace).*(area|region|object)": "inpainting",
    
    # Upscaling intents
    r"(upscal|enhanc|improv|increas).*(quality|resolution|size|detail)": "upscaling",
    r"(super|hyper).*(resolution)": "upscaling",
    r"(2x|4x|8x)": "upscaling",
    
    # Video intents
    r"(generat|creat|mak|produc).*(video|animation|clip|motion)": "video_generation",
    r"(animat|move|motion)": "video_generation",
    r"(text|prompt)\s*to\s*video": "video_generation",
    
    # Audio intents
    r"(generat|creat|mak|produc).*(music|audio|sound|track)": "music_generation",
    r"(speak|voice|narrat|tts|text.to.speech)": "speech_generation",
    
    # Content intents
    r"(writ|creat|generat).*(blog|article|post|content|email|newsletter)": "content_creation",
    r"(writ|creat|generat).*(script|copy|description)": "content_creation",
    
    # Product intents
    r"(sell|list|publish).*(product|shirt|mug|hoodie)": "product_creation",
    r"(creat|mak).*(product|merchandise|merch)": "product_creation",
    
    # Social media intents
    r"(post|share|publish).*(twitter|x\.com|instagram|facebook|linkedin|tiktok)": "social_posting",
    r"(social|media|marketing)": "social_posting",
    
    # Research intents
    r"(research|find|search|look|discover)": "research",
    r"(analyz|investigat|stud)": "research",
}

# ============================================================================
# MODEL CAPABILITY REGISTRY - Based on printify_clean patterns
# ============================================================================

MODEL_CAPABILITIES = {
    # Image Generation Models
    "flux-schnell": {"capabilities": ["text2img", "fast", "artistic"], "quality": 0.85, "speed": 0.95},
    "flux-dev": {"capabilities": ["text2img", "high_quality", "artistic"], "quality": 0.95, "speed": 0.6},
    "flux-pro": {"capabilities": ["text2img", "ultra_quality", "commercial"], "quality": 0.98, "speed": 0.5},
    "ideogram": {"capabilities": ["text2img", "text_render", "logo"], "quality": 0.92, "speed": 0.7},
    "sdxl": {"capabilities": ["text2img", "versatile", "controlnet"], "quality": 0.90, "speed": 0.7},
    
    # Video Generation Models
    "kling": {"capabilities": ["text2video", "img2video", "realistic"], "quality": 0.92, "speed": 0.25},
    "luma": {"capabilities": ["text2video", "img2video", "cinematic"], "quality": 0.88, "speed": 0.4},
    "minimax": {"capabilities": ["text2video", "img2video", "high_quality"], "quality": 0.90, "speed": 0.3},
    "ken_burns": {"capabilities": ["img2video", "local", "free"], "quality": 0.80, "speed": 1.0},
    
    # Audio/Music Models
    "musicgen": {"capabilities": ["text2music", "instrumental"], "quality": 0.90, "speed": 0.6},
    "minimax-speech": {"capabilities": ["tts", "voice_clone"], "quality": 0.92, "speed": 0.75},
    
    # Image Editing Models
    "rembg": {"capabilities": ["background_removal", "fast"], "quality": 0.90, "speed": 0.95},
    "real-esrgan": {"capabilities": ["upscale", "enhance"], "quality": 0.92, "speed": 0.85},
}


class SuperPlanningAgent:
    """
    Hyper-intelligent planning agent with:
    - Automatic multi-task parsing (detects multiple goals in one request)
    - Smart dependency analysis (what can run in parallel vs sequential)
    - Intelligent task delegation (matches tasks to optimal tools)
    - Context-aware defaults (uses previous outputs automatically)
    - Failure recovery with automatic retries and alternatives
    - Workflow type detection (from printify_clean orchestrator)
    - Intent pattern matching (from printify_clean ultra_smart_executor)
    """
    
    def __init__(self, anthropic_client: Anthropic):
        self.anthropic = anthropic_client
        self.skills_registry = None  # Will be injected
        
        # System capabilities description - AUTONOMOUS EXECUTION MODE
        self.capabilities_prompt = """You are Otto's HYPER-INTELLIGENT Task Parser & Delegator.

🧠 YOUR CORE INTELLIGENCE:
You automatically detect, parse, and delegate complex multi-step requests. When a user makes a complex request, you:
1. DETECT all distinct tasks/goals in the request (even implicit ones)
2. ANALYZE dependencies between tasks
3. OPTIMIZE execution order (parallelize when possible)
4. DELEGATE each task to the optimal tool
5. CHAIN outputs between dependent steps automatically

🖼️ IMAGE DIMENSION & ASPECT RATIO DETECTION:
**CRITICAL**: ALWAYS include aspect_ratio parameter in generate_image when user mentions ANY size/dimension/orientation:
- "portrait", "tall", "vertical", "portrait-sized" → aspect_ratio: "2:3"
- "landscape", "wide", "horizontal", "landscape-sized" → aspect_ratio: "3:2"  
- "cinematic", "widescreen", "movie", "film" → aspect_ratio: "16:9"
- "phone", "story", "tiktok", "reels", "mobile" → aspect_ratio: "9:16"
- "square" or no mention → aspect_ratio: "1:1"
- "ultrawide", "panoramic", "banner" → aspect_ratio: "21:9"

⚠️ MANDATORY: If user mentions "wide", "landscape", "cinematic", "portrait", "tall", "phone", etc., you MUST include the aspect_ratio parameter. Never omit it.

Example: "5 portrait dimension designs" → each generate_image should have aspect_ratio: "2:3"
Example: "wide landscape banner" → aspect_ratio: "16:9" or "21:9"
Example: "cinematic mountain scene" → aspect_ratio: "16:9"
Example: "portrait sized cat" → aspect_ratio: "2:3"

🎨 IMAGE STYLE DETECTION:
When user mentions art styles, include style parameter in generate_image:
- "photorealistic", "realistic photo", "photograph" → style: "photorealistic"
- "cinematic", "movie still", "film" → style: "cinematic"
- "anime", "manga", "japanese animation" → style: "anime"
- "digital art", "concept art", "artstation" → style: "digital_art"
- "oil painting", "classical", "renaissance" → style: "oil_painting"
- "watercolor", "aquarelle" → style: "watercolor"
- "sketch", "pencil drawing", "hand drawn" → style: "sketch"
- "vector", "flat design", "svg" → style: "vector"
- "3d render", "cgi", "octane", "blender" → style: "3d_render"
- "pixel art", "8-bit", "retro game" → style: "pixel_art"
- "minimalist", "minimal", "simple" → style: "minimalist"
- "pop art", "warhol", "comic" → style: "pop_art"
- "cyberpunk", "neon", "synthwave" → style: "cyberpunk"
- "fantasy", "magical", "d&d" → style: "fantasy"
- "vintage", "retro", "nostalgic" → style: "vintage"

Example: "anime style cat" → generate_image with style: "anime"
Example: "photorealistic mountain landscape" → style: "photorealistic", aspect_ratio: "3:2"

✂️ IMAGE EDITING & ADJUSTMENT DETECTION:
When user wants to modify an existing image, use:
1. adjust_image for simple adjustments:
   - "brighter", "lighten" → brightness: 30
   - "darker", "darken" → brightness: -30
   - "more contrast", "punchier" → contrast: 30
   - "less contrast", "flatter" → contrast: -30
   - "more saturated", "vibrant", "colorful" → saturation: 40
   - "desaturated", "muted" → saturation: -40
   - "warmer", "golden" → warmth: 40
   - "cooler", "blue" → warmth: -40
   - "sharper", "crisp" → sharpness: 50
   - "blur", "soften" → sharpness: -50

2. edit_image_with_ai for complex edits:
   - "remove the background" → edit_image_with_ai
   - "upscale", "higher resolution" → edit_image_with_ai
   - "colorize", "add color" → edit_image_with_ai
   - "change the sky", "replace the..." → edit_image_with_ai
   - "add a hat", "put glasses on" → edit_image_with_ai
   - "remove the car", "delete the..." → edit_image_with_ai

Example: "make this image brighter and more contrasty" → adjust_image with brightness: 30, contrast: 30
Example: "remove the background from this" → edit_image_with_ai with instruction: "remove background"

🔍 AUTOMATIC TASK DETECTION RULES:
- "and" / "then" / "," = Multiple sequential tasks
- "5 designs" / "multiple" / "several" = Loop/batch operations
- "each" / "all" / "every" = Apply action to all previous outputs
- "sell" / "publish" / "list" = Product creation (ALWAYS triggers Printify)
- "research" + "create" = Research informs creation parameters
- "analyze" + "recommend" = Analysis drives recommendations

📊 DEPENDENCY ANALYSIS:
- Tasks that need previous output = SEQUENTIAL (depends_on previous step)
- Independent tasks = CAN BE PARALLEL (no depends_on)
- "Use that image" / "same design" = Reference previous step output
- "For each design" = Loop over previous step's array output

🚀 DELEGATION PRIORITY (use FIRST available):
0. SPECIALIZED AGENTS - For complex/multi-domain tasks, delegate to specialist agents:
   - delegate_to_specialist with preferred_specialist for domain-specific work
   - Content Writer → articles, blogs, descriptions, documentation
   - Copywriter → headlines, ads, marketing copy, CTAs
   - Social Media Manager → social posts, engagement, content calendars
   - Image Creator → AI image generation, photo editing
   - Video Producer → AI video creation, animation
   - Code Developer → programming, scripts, automation
   - Data Analyst → analysis, insights, reporting
   - Market Researcher → research, competitor analysis
   - E-commerce Expert → product listings, store management
   - Browser Operator → web scraping, form filling, automation
   - Project Manager → planning, coordination, timelines
   - Automation Engineer → workflows, integrations
   - run_collaborative_task when multiple domains needed
1. SPECIALIZED TOOLS - Use dedicated tools when they exist
   - generate_image / generate_tshirt_design for images
   - printify_create_* for products
   - printify_get_mockup_urls to get product mockups for videos
   - create_product_promo_video for complete video ad creation
   - replicate_create_video for simple videos
   - shopify_* for store operations
   - search_web / browse_url for research
2. AI MODELS - Use replicate_smart_generate for specialized AI tasks
3. CODE - Use execute_python ONLY for computation/data processing

🤖 AGENT DELEGATION RULES:
- Complex research + create tasks → Use delegate_to_specialist or run_collaborative_task
- "Write me a detailed article about..." → delegate_to_specialist with content_writer
- "Create marketing copy for..." → delegate_to_specialist with copywriter
- "Analyze this data and give insights" → delegate_to_specialist with data_analyst
- "Build a complete marketing campaign" → run_collaborative_task (uses multiple specialists)
- Simple single-tool tasks → Use the direct tool (don't over-delegate)

🎬 VIDEO WORKFLOW - For product videos:
When user asks for "video ad", "promo video", "product video", "marketing video":
1. If Printify product exists → use printify_get_mockup_urls to get the mockup image
2. THEN create video using the mockup as input image
3. For complete promo videos → use create_product_promo_video (includes voiceover + music)
4. For simple videos → use replicate_create_video with image_url parameter

CRITICAL VIDEO CHAIN:
printify_create_* → printify_get_mockup_urls → create_product_promo_video
The mockup URL from step 2 MUST be passed as image_url to step 3!

� BROWSER AUTOMATION WORKFLOW:
When user explicitly asks to use browser tools or mentions browser-related tasks:
- "Use browser_extract_leads" → browser_extract_leads tool
- "Use browser_monitor_price" → browser_monitor_price tool
- "Use browser_analyze_competitor" → browser_analyze_competitor tool
- "Use browser_find_influencers" → browser_find_influencers tool (ALWAYS include niche param!)
- "Use browser_fill_form" → browser_fill_form tool
- "Use browser_scrape" or "browser_extract_data" → browser_extract_data tool

These browser_* tools launch a REAL BROWSER with AI automation to:
- Extract leads and contacts from any website
- Monitor prices on e-commerce sites
- Analyze competitor websites deeply
- Find influencers on social platforms
- Fill out forms automatically
- Scrape structured data from websites
- Take screenshots of pages

🎯 BROWSER TOOL PRIORITY:
- When user says "Use browser_*" → Use that EXACT browser tool (not search_web or browse_url)
- browser_extract_leads = AI browser to collect contact info from a page
- browser_monitor_price = AI browser to track prices on commerce sites
- browser_analyze_competitor = AI browser for deep competitor analysis with interactions
- browser_find_influencers = AI browser to find influencers on social platforms
- These are DIFFERENT from search_web (just web search) and browse_url (just HTML fetch)

⚠️ BROWSER TOOL REQUIRED PARAMETERS:
- browser_find_influencers: ALWAYS set niche (e.g., "fitness", "beauty", "tech", "gaming") - default to "lifestyle" if unclear
- browser_find_influencers: ALWAYS set platform (e.g., "tiktok", "instagram", "youtube") - infer from user request
- browser_extract_data: ALWAYS set data_description (what to extract from the page)
- If user doesn't specify a niche for influencer search, ASK them or default to "lifestyle"

🎯 SMART PARAMETER INFERENCE:
When user is vague, infer optimal parameters:
- "nice design" → professional, clean, modern aesthetic
- "sell it" → determine product type from image content
- "video ad" → 10-15 second promo video with voiceover and music
- Price not specified → use market-appropriate defaults ($24.99 shirts, $19.99 mugs, $49.99 wall art)
- Title not specified → generate from design description
- Multiple items → generate variations, not duplicates
- "find TikTok influencers" → platform="tiktok", infer niche from context or use "lifestyle"
- "search Reddit for X" → url="https://reddit.com", data_description="subreddits, posts about X"

📝 CONTENT CREATION WORKFLOWS - ALWAYS INCLUDE IMAGES:
When user requests blog posts, emails, or articles, ALWAYS generate accompanying images:

"Write a blog post about sustainable fashion"
→ Steps: 1) Generate 2-3 header/illustration images, 2) Write blog content with image placeholders, 3) Combine into final output
→ CRITICAL: NEVER write content without also generating relevant images

"Create an email campaign for our new product"
→ Steps: 1) Generate product banner image, 2) Write email copy, 3) Include image in email template
→ Images should match brand and content theme

"Write marketing content for XYZ"
→ Steps: 1) Research topic briefly, 2) Generate header image, 3) Write content, 4) Return content + image
→ Every piece of marketing content needs visual assets

Image generation prompts for content should be descriptive:
- Blog header: "Professional blog header illustration about [topic], clean modern design, no text"
- Email banner: "Marketing email banner for [product/topic], vibrant, commercial style"
- Social: "Social media post image for [topic], engaging, Instagram-style"

⚡ PARALLEL EXECUTION DETECTION:
Identify steps that can run simultaneously:
- Multiple independent image generations → PARALLEL
- Research + unrelated image generation → PARALLEL  
- Product creation for DIFFERENT products → PARALLEL
- Same image to multiple product types → PARALLEL after image is ready
- Voiceover + background music → PARALLEL (during video generation)

🔄 AUTOMATIC OUTPUT CHAINING:
- {{step_N_output}} = Use output from step N
- {{step_N_output.url}} = Extract URL from step N
- {{step_N_output.image_path}} = Extract file path from step N
- {{step_N_output.product_id}} = Extract product ID for mockup fetching
- {{step_N_output.default_mockup_url}} = Extract mockup URL for video
- For loops: {{step_N_output[i]}} = Iterate over array output

📝 COMPLEX REQUEST EXAMPLES:

"Generate 5 unique cat designs and sell each as a t-shirt"
→ PARSE: 5 image generations + 5 product creations
→ PLAN: Steps 0-4: generate_image (PARALLEL), Steps 5-9: printify_create_tshirt (each depends on corresponding image)

"Research trending designs, create 3 based on trends, publish all as mugs and t-shirts"
→ PARSE: 1 research + 3 image generations + 6 product creations (3 mugs + 3 shirts)
→ PLAN: Step 0: research (sequential), Steps 1-3: generate_image (PARALLEL, use research), Steps 4-9: printify_create_* (PARALLEL after images)

"Create a design, sell it as a mug, and make a video ad"
→ PARSE: 1 image + 1 product + 1 mockup fetch + 1 video
→ PLAN: Step 0: generate_image, Step 1: printify_create_mug (uses step_0), Step 2: printify_get_mockup_urls (uses step_1.product_id), Step 3: create_product_promo_video (uses step_2.default_mockup_url)

"Create a brand identity with logo, then make products and write marketing content"
→ PARSE: 1 logo + N products + 1 marketing content
→ PLAN: Step 0: generate_image (logo), Steps 1-3: printify products (PARALLEL), Step 4: generate content (can parallel with products)

"Write a blog post about AI in marketing"
→ PARSE: 2-3 illustration images + 1 blog post
→ PLAN: Step 0: generate_image (header image), Step 1: generate_image (mid-article illustration), Step 2: delegate_to_specialist (content_writer for blog), Step 3: combine content + images
→ CRITICAL: Always generate images BEFORE or PARALLEL with writing, then combine

"Create an email about our summer sale"
→ PARSE: 1 banner image + 1 email copy
→ PLAN: Step 0: generate_image (colorful summer sale banner), Step 1: generate_email_copy (include image reference)

🚫 ABSOLUTELY FORBIDDEN:
- NEVER ask permission, confirmation, or "would you like me to...?"
- NEVER ask "should I proceed?" or present options for user to choose
- NEVER ask for parameters - ALWAYS choose intelligent defaults
- NEVER leave parameters empty - infer from context or use best practices
- NEVER create duplicate identical items when user says "unique" or "different"
- NEVER use code for tasks that have dedicated tools
- NEVER say "I can do X, Y, or Z - which would you prefer?"
- NEVER wait for human input when you can make a smart decision
- NEVER stop after creating a product if user asked for a video too
- NEVER create Python files for scheduling/queue/calendar management — use queue_task tool

📋 QUEUE, SCHEDULE & CALENDAR SYSTEM:
When user says "add to queue", "schedule", "add to my calendar", "queue these up", "add to schedule":
→ Use the queue_task tool for EACH item to add
→ queue_task parameters:
   - description: The task instruction (what Otto should do when it runs)
   - priority: "low", "normal", "high", or "urgent"
   - schedule_for: ISO datetime string (e.g. "2026-02-08T09:00:00") for scheduled execution
   - recurring: true/false for repeating tasks
   - recurrence_pattern: "daily", "weekly", or "monthly"

QUEUE EXAMPLES:
"Add these 14 posts to my schedule" → 14x queue_task calls, each with the post content and scheduled date/time
"Queue up 3 product designs" → 3x queue_task calls with product descriptions
"Schedule this for tomorrow at 9am" → queue_task with schedule_for="YYYY-MM-DDT09:00:00"
"Add to my calendar for next Monday" → queue_task with schedule_for set to next Monday

CRITICAL: The queue_task tool adds items to the user's ACTUAL app queue/schedule sidebar.
Do NOT create Python files, modules, or custom code for task management.
Do NOT just describe what you would queue — actually CALL queue_task for each item.

✅ ALWAYS (MANDATORY):
- Parse the FULL scope of the request and EXECUTE it completely
- Identify ALL implicit tasks (user says "sell" → product + publish)
- For video requests: ALWAYS fetch mockup first, THEN create video
- Make decisions autonomously using context clues
- Chain outputs between dependent steps
- Maximize parallel execution where possible
- Use specific, descriptive prompts for image generation
- Choose the BEST option automatically, don't list options
- If user is vague, pick the most sensible interpretation
- Include verification steps for critical operations

🧠 SMART DEFAULTS (use when not specified):
- Price: T-shirts $24.99, Mugs $19.99, Wall Art $49.99, Hoodies $39.99
- Image size: 1024x1024 for general, 1024x1792 for portraits, 1792x1024 for landscapes
- Video duration: 10 seconds for product ads, 15 seconds for full promo videos
- Style: Modern, professional, high-quality unless context suggests otherwise
- Quantity: 1 unless user says "multiple", "several", "some" (then use 3)
- Product type: If image has text → T-shirt, If artistic → Wall Art, If cute → Mug
- File format: PNG for images with transparency, JPEG for photos
- Code language: Python unless context suggests otherwise

📹 VIDEO WORKFLOW (MANDATORY for video from products):
1. Create images/products FIRST (step_0, step_1, etc.)
2. For product videos: use printify_get_mockup_urls to fetch product mockups
3. Create video using replicate_create_video with:
   - description: "Your video description"
   - image_url: "{{{{step_N_output}}}}" (N = mockup step)
   - duration: 5 or 10
4. ALWAYS use {{{{step_N_output}}}} format - NEVER custom names

🔗 TEMPLATE SYNTAX (CRITICAL):
- Format: {{{{step_N_output}}}} where N is the step number (0, 1, 2...)
- Examples: {{{{step_0_output}}}}, {{{{step_1_output}}}}, {{{{step_2_output}}}}
- FORBIDDEN: {{{{design_url}}}}, {{{{image_1}}}}, {{{{my_result}}}} - these will NOT resolve
- For specific properties: {{{{step_N_output.property_name}}}}"""

    async def create_plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a hyper-intelligent execution plan with automatic task parsing.
        ENHANCED with Platform Intelligence for smarter planning.
        """
        message = context["message"]
        available_tools = context.get("available_tools", [])
        memories = context.get("memories", [])
        enhanced_context = context.get("enhanced_context", "")  # From Intelligence System
        task_suggestions = context.get("task_suggestions", [])  # Past learnings
        request_type = context.get("request_type", {})  # Action detection from orchestrator
        platform_intelligence = context.get("platform_intelligence", {})  # NEW: Platform context
        
        # Extract recent context for better understanding
        recent_context = self._extract_recent_context(memories)
        
        # Pre-analyze the request for complexity
        complexity_analysis = self._analyze_request_complexity(message)
        
        # Detect workflow type and intent patterns
        workflow_type = self._detect_workflow_type(message)
        intent_patterns = self._analyze_intent_patterns(message)
        workflow_template = self._get_workflow_steps_template(workflow_type)
        
        # ========================================
        # PLATFORM INTELLIGENCE ENHANCED CONTEXT
        # ========================================
        platform_context = ""
        if platform_intelligence:
            pi = platform_intelligence
            platform_context = "\n=== PLATFORM INTELLIGENCE ===\n"
            
            # Primary intent detection
            if pi.get("primary_intent"):
                platform_context += f"Primary Intent: {pi['primary_intent']} (confidence: {pi.get('confidence', 0):.0%})\n"
            
            # All detected intents
            all_intents = pi.get("all_intents", [])
            if all_intents:
                intent_str = ", ".join([f"{i[0]}({i[1]:.0%})" for i in all_intents[:3]])
                platform_context += f"All Intents: {intent_str}\n"
            
            # Recommended model
            if pi.get("recommended_model"):
                platform_context += f"Recommended Model: {pi['recommended_model']} (for {pi.get('model_category', 'unknown')})\n"
            
            # Matched workflow template
            if pi.get("workflow_template"):
                wf = pi["workflow_template"]
                platform_context += f"Workflow Template: {wf.get('name', 'unknown')}\n"
                platform_context += f"  Description: {wf.get('description', '')}\n"
                steps = wf.get("steps", [])
                if steps:
                    step_names = [s.get("action", "step") for s in steps[:5]]
                    platform_context += f"  Suggested Flow: {' → '.join(step_names)}\n"
            
            # Creative tool match
            if pi.get("creative_tool"):
                ct = pi["creative_tool"]
                platform_context += f"Creative Tool Match: {ct.get('name', 'unknown')} → use {ct.get('tool', 'unknown')}\n"
            
            # Agent persona suggestion
            if pi.get("agent_persona"):
                ap = pi["agent_persona"]
                platform_context += f"Agent Persona: {ap.get('name', 'Otto')} the {ap.get('role', 'Assistant')}\n"
            
            # Multi-step indicator
            if pi.get("is_multi_step"):
                platform_context += "Multi-step Workflow: YES - plan multiple sequential steps\n"
        
        # Build workflow context for the LLM
        workflow_context = f"\n=== WORKFLOW ANALYSIS ===\n"
        workflow_context += f"Detected Workflow Type: {workflow_type}\n"
        workflow_context += f"Intent Patterns: {', '.join([k for k, v in intent_patterns.items() if v])}\n"
        if workflow_template:
            # Handle both dict and string templates
            steps = []
            for step in workflow_template:
                if isinstance(step, dict):
                    steps.append(f"{step.get('agent', 'agent')}:{step.get('action', 'action')}")
                else:
                    steps.append(str(step))
            workflow_context += f"Suggested Steps Template: {' → '.join(steps)}\n"
        if request_type:
            workflow_context += f"Action Type: {request_type.get('action_type', 'general')}\n"
        
        # Check if we have relevant Skills
        skill_context = ""
        if self.skills_registry:
            recommended_skill = self.skills_registry.recommend_skill(message)
            if recommended_skill:
                skill_context = f"\n\n=== RECOMMENDED SKILL: {recommended_skill.name} ===\n"
                skill_context += f"Description: {recommended_skill.description}\n"
                skill_context += f"Capabilities: {', '.join(recommended_skill.capabilities[:5])}\n"
        
        # Format intelligence enhancements
        intelligence_section = ""
        if enhanced_context:
            intelligence_section += f"\n{enhanced_context}\n"
        if task_suggestions:
            intelligence_section += "\n=== LEARNINGS FROM PAST EXECUTIONS ===\n"
            for suggestion in task_suggestions[:5]:
                intelligence_section += f"• {suggestion}\n"
        
        # Categorize tools
        tools_by_category = self._categorize_tools(available_tools)
        tools_description = self._format_tools_enhanced(available_tools, tools_by_category)
        memory_context = self._format_memories(memories)
        
        prompt = f"""{self.capabilities_prompt}

=== REQUEST TO PARSE ===
User Message: {message}

=== PRE-ANALYSIS ===
{complexity_analysis}
{workflow_context}
{platform_context}

=== CONTEXT FROM CONVERSATION ===
{recent_context}
{skill_context}
{intelligence_section}

=== AVAILABLE TOOLS ===
{tools_description}

=== RECENT CONVERSATION ===
{memory_context}

=== YOUR TASK ===
Parse this request and create an optimal execution plan.

STEP 1 - TASK DETECTION:
- List ALL distinct tasks in the request (explicit and implicit)
- Note quantities (e.g., "5 designs" = 5 separate generation tasks)
- Identify implicit tasks (e.g., "sell" implies create + publish)

STEP 2 - DEPENDENCY MAPPING:
- Which tasks need outputs from other tasks?
- Which tasks are independent and can run in parallel?
- Mark dependencies with step numbers

STEP 3 - TOOL ASSIGNMENT:
- Assign the optimal tool to each task
- Fill in ALL parameters with intelligent defaults
- Use {{{{step_N_output}}}} for cross-step references (EXACTLY this format, N=step number)
- NEVER use custom variable names like {{{{design_1_url}}}} - ONLY {{{{step_N_output}}}}
- For video from images: use image_url parameter with {{{{step_N_output}}}} from image generation step

STEP 4 - OPTIMIZATION:
- Reorder for maximum parallelization
- Group related operations
- Add verification for critical steps

=== RESPONSE FORMAT (JSON) ===

🔄 FOLLOW-UP REQUEST HANDLING:
When the user says short things like "change the name", "try again", "use a different one", "yes do that":
1. ALWAYS check the CONTEXT FROM CONVERSATION section above
2. Look for what the user previously requested or what failed
3. Understand what they're referring to and complete THAT task with modifications

EXAMPLES of follow-up understanding:
- Previous: "tried to create script.py but it exists" + User says: "change the name" 
  → Create the SAME script with a DIFFERENT name (script2.py, my_script.py, etc.)
- Previous: "created image of cat" + User says: "make it blue"
  → Regenerate the image with blue color
- Previous: "file already exists" + User says: "overwrite it"
  → Create the file with overwrite=true

IMPORTANT: For simple conversational messages (greetings, acknowledgments, corrections, questions that don't require tools), return:
{{
    "intent": "User is expressing/asking something conversational",
    "requires_tools": false,
    "steps": [],
    "conversational": true,
    "note": "This is a conversational response - no tools needed"
}}

For requests that need tools:
{{
    "intent": "High-level description of what user wants to accomplish",
    "parsed_tasks": [
        "Task 1: ...",
        "Task 2: ...",
        "etc"
    ],
    "approach": "Execution strategy with parallelization notes",
    "requires_tools": true,
    "parallel_groups": [
        [0, 1, 2],  // Steps that can run in parallel
        [3, 4]      // Next parallel group after previous completes
    ],
    "steps": [
        {{
            "step_id": 0,
            "tool": "tool_name",
            "description": "Clear description of what this accomplishes",
            "parameters": {{
                "param1": "value",
                "param2": "{{{{step_0_output}}}}"
            }},
            "depends_on": [],
            "can_parallel": true,
            "fallback": "Alternative approach if this fails",
            "critical": true
        }}
    ],
    "verification": "How to confirm overall success",
    "estimated_time": "Total time estimate",
    "success_criteria": "What defines complete success"
}}

=== DETAILED EXAMPLES ===

Example 0: "that's wrong" or "thanks!" or "hello"
{{
    "intent": "User is providing feedback/greeting",
    "requires_tools": false,
    "steps": [],
    "conversational": true
}}

Example 1: "Generate 3 unique space designs and sell each as a t-shirt and mug"
{{
    "intent": "Create 3 space-themed designs and turn each into t-shirt and mug products (6 products total)",
    "parsed_tasks": [
        "Generate space design #1 (unique style)",
        "Generate space design #2 (unique style)",
        "Generate space design #3 (unique style)",
        "Create t-shirt product from design #1",
        "Create mug product from design #1",
        "Create t-shirt product from design #2",
        "Create mug product from design #2",
        "Create t-shirt product from design #3",
        "Create mug product from design #3"
    ],
    "approach": "Generate all 3 designs in parallel, then create all 6 products in parallel",
    "requires_tools": true,
    "parallel_groups": [[0, 1, 2], [3, 4, 5, 6, 7, 8]],
    "steps": [
        {{
            "step_id": 0,
            "tool": "generate_image",
            "description": "Generate unique space design #1",
            "parameters": {{
                "prompt": "Cosmic galaxy illustration with swirling nebulas, vibrant purples and blues, vector art style, t-shirt ready design",
                "aspect_ratio": "1:1",
                "style": "digital_art"
            }},
            "depends_on": [],
            "can_parallel": true
        }},
        {{
            "step_id": 1,
            "tool": "generate_image", 
            "description": "Generate unique space design #2",
            "parameters": {{
                "prompt": "Retro astronaut floating in space, vintage 80s style, bold colors, geometric shapes, apparel design",
                "aspect_ratio": "1:1",
                "style": "vintage"
            }},
            "depends_on": [],
            "can_parallel": true
        }},
        {{
            "step_id": 2,
            "tool": "generate_image",
            "description": "Generate unique space design #3", 
            "parameters": {{
                "prompt": "Minimalist solar system planets alignment, clean line art, monochrome with accent color, modern design",
                "aspect_ratio": "1:1",
                "style": "minimalist"
            }},
            "depends_on": [],
            "can_parallel": true
        }},
        {{
            "step_id": 3,
            "tool": "printify_create_tshirt",
            "description": "Create t-shirt with galaxy design (from step 0)",
            "parameters": {{
                "title": "Cosmic Galaxy T-Shirt",
                "description": "Stunning cosmic galaxy design with vibrant nebula colors",
                "design_url": "{{{{step_0_output}}}}",
                "price": 24.99
            }},
            "depends_on": [0],
            "can_parallel": true
        }},
        {{
            "step_id": 4,
            "tool": "printify_create_mug",
            "description": "Create mug with galaxy design (from step 0)",
            "parameters": {{
                "title": "Cosmic Galaxy Mug",
                "description": "Start your day with the cosmos - stunning nebula design",
                "design_url": "{{{{step_0_output}}}}",
                "price": 19.99
            }},
            "depends_on": [0],
            "can_parallel": true
        }},
        {{
            "step_id": 5,
            "tool": "printify_create_tshirt",
            "description": "Create t-shirt with astronaut design (from step 1)",
            "parameters": {{
                "title": "Retro Astronaut T-Shirt",
                "description": "Vintage 80s astronaut design with bold colors",
                "design_url": "{{{{step_1_output}}}}",
                "price": 24.99
            }},
            "depends_on": [1],
            "can_parallel": true
        }},
        {{
            "step_id": 6,
            "tool": "printify_create_mug",
            "description": "Create mug with astronaut design (from step 1)",
            "parameters": {{
                "title": "Retro Astronaut Mug",
                "description": "Vintage astronaut design for your morning coffee",
                "design_url": "{{{{step_1_output}}}}",
                "price": 19.99
            }},
            "depends_on": [1],
            "can_parallel": true
        }},
        {{
            "step_id": 7,
            "tool": "printify_create_tshirt",
            "description": "Create t-shirt with solar system design (from step 2)",
            "parameters": {{
                "title": "Solar System T-Shirt",
                "description": "Minimalist planets alignment design",
                "design_url": "{{{{step_2_output}}}}",
                "price": 24.99
            }},
            "depends_on": [2],
            "can_parallel": true
        }},
        {{
            "step_id": 8,
            "tool": "printify_create_mug",
            "description": "Create mug with solar system design (from step 2)",
            "parameters": {{
                "title": "Solar System Mug",
                "description": "Modern minimalist planets design",
                "design_url": "{{{{step_2_output}}}}",
                "price": 19.99
            }},
            "depends_on": [2],
            "can_parallel": true
        }}
    ]
}}

⚠️ CRITICAL - CORRECT STEP OUTPUT REFERENCING:
When creating MULTIPLE designs and MULTIPLE products:
- Design 1 (step 0) → Products use {{{{step_0_output}}}}
- Design 2 (step 1) → Products use {{{{step_1_output}}}}
- Design 3 (step 2) → Products use {{{{step_2_output}}}}
NEVER use {{{{step_0_output}}}} for ALL products if each product should use a DIFFERENT design!

Example 2: "Research AI art trends, create designs based on top 3 trends, and write blog post"
{{
    "intent": "Research trends, create trend-based designs, and generate marketing content",
    "parsed_tasks": [
        "Research current AI art trends",
        "Generate design based on trend #1",
        "Generate design based on trend #2", 
        "Generate design based on trend #3",
        "Write comprehensive blog post about the collection"
    ],
    "approach": "Research first (sequential), then generate 3 designs in parallel using research insights, finally write blog",
    "parallel_groups": [[0], [1, 2, 3], [4]],
    "steps": [
        {{
            "step_id": 0,
            "tool": "search_web",
            "description": "Research current AI art and design trends",
            "parameters": {{
                "query": "AI art trends 2026 popular styles digital design"
            }},
            "depends_on": [],
            "can_parallel": false
        }},
        {{
            "step_id": 1,
            "tool": "generate_image",
            "description": "Create design based on top trend from research",
            "parameters": {{
                "prompt": "Based on research: {{{{step_0_output.trend_1}}}}, create modern digital art design",
                "aspect_ratio": "1:1",
                "style": "digital_art"
            }},
            "depends_on": [0],
            "can_parallel": true
        }}
        // ... continues
    ]
}}

Example 3: "Create a cinematic wide landscape of mountains and sell it as framed art"
{{
    "intent": "Generate a wide cinematic mountain landscape image and create a framed poster product",
    "parsed_tasks": [
        "Generate cinematic wide landscape mountain image",
        "Create framed art/poster product from the image"
    ],
    "approach": "Generate image with 16:9 cinematic aspect ratio, then create framed poster product",
    "requires_tools": true,
    "parallel_groups": [[0], [1]],
    "steps": [
        {{
            "step_id": 0,
            "tool": "generate_image",
            "description": "Generate cinematic wide mountain landscape",
            "parameters": {{
                "prompt": "Majestic mountain landscape with dramatic lighting, sweeping vista, golden hour, epic scale",
                "aspect_ratio": "16:9",
                "style": "cinematic"
            }},
            "depends_on": [],
            "can_parallel": false
        }},
        {{
            "step_id": 1,
            "tool": "printify_create_product",
            "description": "Create framed art product from the landscape",
            "parameters": {{
                "title": "Cinematic Mountain Vista - Framed Art",
                "description": "Breathtaking mountain landscape with dramatic cinematic lighting",
                "design_url": "{{{{step_0_output}}}}",
                "product_type": "framed poster",
                "price": 49.99
            }},
            "depends_on": [0],
            "can_parallel": false
        }}
    ]
}}

Example 4: "Generate 3 portrait-sized minimalist phone wallpapers"
{{
    "intent": "Create 3 portrait/phone-sized minimalist wallpaper designs",
    "parsed_tasks": [
        "Generate portrait minimalist wallpaper #1",
        "Generate portrait minimalist wallpaper #2",
        "Generate portrait minimalist wallpaper #3"
    ],
    "approach": "Generate all 3 images in parallel with 9:16 portrait aspect ratio and minimalist style",
    "requires_tools": true,
    "parallel_groups": [[0, 1, 2]],
    "steps": [
        {{
            "step_id": 0,
            "tool": "generate_image",
            "description": "Generate minimalist phone wallpaper #1",
            "parameters": {{
                "prompt": "Minimalist abstract geometric shapes, soft gradients, calming colors, phone wallpaper",
                "aspect_ratio": "9:16",
                "style": "minimalist"
            }},
            "depends_on": [],
            "can_parallel": true
        }},
        {{
            "step_id": 1,
            "tool": "generate_image",
            "description": "Generate minimalist phone wallpaper #2",
            "parameters": {{
                "prompt": "Minimalist mountain silhouette, pastel sky, serene landscape, phone wallpaper",
                "aspect_ratio": "9:16",
                "style": "minimalist"
            }},
            "depends_on": [],
            "can_parallel": true
        }},
        {{
            "step_id": 2,
            "tool": "generate_image",
            "description": "Generate minimalist phone wallpaper #3",
            "parameters": {{
                "prompt": "Minimalist ocean waves, clean lines, zen aesthetic, phone wallpaper",
                "aspect_ratio": "9:16",
                "style": "minimalist"
            }},
            "depends_on": [],
            "can_parallel": true
        }}
    ]
}}

Now parse and create the optimal plan for: "{message}"

Return ONLY valid JSON."""

        try:
            response = await asyncio.to_thread(
                self.anthropic.messages.create,
                model="claude-sonnet-4-20250514",
                max_tokens=8192,  # Increased for complex plans
                temperature=0.3,  # Slightly lower for more consistent parsing
                messages=[{"role": "user", "content": prompt}]
            )
            
            plan_text = response.content[0].text
            plan = self._parse_json_response(plan_text)
            
            # Validate and enhance plan
            plan = self._validate_plan(plan, available_tools)
            
            # Ensure content creation plans always include images (printify_clean pattern)
            plan = self._ensure_content_has_images(plan, message)
            
            # Proactively expand plan with helpful additional tasks
            plan = self._expand_plan_proactively(plan, message)
            
            # Log parsed complexity
            num_steps = len(plan.get("steps", []))
            parallel_groups = plan.get("parallel_groups", [])
            logger.info(f"Created hyper-intelligent plan: {plan.get('intent', 'unknown')} | {num_steps} steps | {len(parallel_groups)} parallel groups")
            
            return plan
            
        except Exception as e:
            logger.error(f"Planning failed: {e}", exc_info=True)
            return self._create_fallback_plan(message, str(e))
    
    def _analyze_request_complexity(self, message: str) -> str:
        """Pre-analyze the request to help with planning."""
        analysis = []
        message_lower = message.lower()
        
        # Detect quantities
        quantity_patterns = [
            (r'\b(\d+)\s+(?:unique |different )?(designs?|images?|products?|variations?)', 'quantity'),
            (r'\b(multiple|several|various|many)\b', 'multiple'),
            (r'\b(each|every|all)\b', 'iteration'),
        ]
        
        for pattern, ptype in quantity_patterns:
            matches = re.findall(pattern, message_lower)
            if matches:
                if ptype == 'quantity':
                    analysis.append(f"BATCH OPERATION DETECTED: {matches[0][0]} {matches[0][1]}")
                elif ptype == 'multiple':
                    analysis.append("MULTIPLE ITEMS REQUESTED (unspecified quantity)")
                elif ptype == 'iteration':
                    analysis.append("ITERATION KEYWORD DETECTED - apply action to all items")
        
        # Detect multi-step indicators
        if ' and ' in message_lower or ' then ' in message_lower:
            parts = re.split(r'\s+(?:and|then)\s+', message_lower)
            analysis.append(f"MULTI-TASK REQUEST: {len(parts)} distinct operations detected")
        
        # Detect product creation
        if any(word in message_lower for word in ['sell', 'publish', 'list', 'product', 'printify', 'shopify']):
            analysis.append("PRODUCT CREATION DETECTED - will use Printify/Shopify")
            
            # Detect product types
            product_types = []
            if any(w in message_lower for w in ['shirt', 'tshirt', 't-shirt', 'apparel']):
                product_types.append('t-shirt')
            if any(w in message_lower for w in ['mug', 'cup']):
                product_types.append('mug')
            if any(w in message_lower for w in ['canvas', 'wall art', 'print', 'poster', 'frame', 'metal']):
                product_types.append('wall art')
            
            if product_types:
                analysis.append(f"PRODUCT TYPES: {', '.join(product_types)}")
            else:
                analysis.append("PRODUCT TYPE: will infer from design content")
        
        # Detect research/analysis
        if any(word in message_lower for word in ['research', 'analyze', 'find', 'search', 'trending', 'competitors']):
            analysis.append("RESEARCH/ANALYSIS PHASE DETECTED - should run before creation")
        
        # Detect content creation
        if any(word in message_lower for word in ['blog', 'post', 'email', 'social media', 'marketing', 'caption', 'description']):
            analysis.append("CONTENT CREATION DETECTED - will generate text content")
        
        return "\n".join(analysis) if analysis else "Simple single-task request"
    
    def _detect_workflow_type(self, message: str) -> str:
        """
        Detect workflow type from message using keyword matching.
        Based on printify_clean/modules/orchestrator.py pattern.
        
        Returns: workflow type string (e.g., 'product_campaign', 'content_creation')
        """
        message_lower = message.lower()
        
        # Check for combinations first (more specific)
        if any(kw in message_lower for kw in ["campaign", "t-shirt", "tshirt", "hoodie", "product"]):
            if any(kw in message_lower for kw in ["video", "commercial", "promo"]):
                return "full_campaign_with_video"
            return "product_campaign"
        
        # Video workflow
        if any(kw in message_lower for kw in ["video", "commercial", "animation", "clip"]):
            return "video_production"
        
        # Content workflow (blog, email, etc.) - ALWAYS with images
        if any(kw in message_lower for kw in ["blog", "article", "content", "write", "copy", "email", "newsletter"]):
            return "content_creation"
        
        # Social media workflow
        if any(kw in message_lower for kw in ["social", "post", "twitter", "instagram", "facebook", "tiktok", "linkedin"]):
            return "social_media"
        
        # Research workflow
        if any(kw in message_lower for kw in ["research", "analyze", "trend", "market", "competitor", "find out"]):
            return "research"
        
        # Image creation workflow
        if any(kw in message_lower for kw in ["image", "design", "illustration", "logo", "artwork", "generate", "create"]):
            return "image_creation"
        
        return "general"
    
    def _analyze_intent_patterns(self, message: str) -> Dict[str, Any]:
        """
        Analyze message using intent patterns from printify_clean/ultra_smart_executor.py.
        
        Returns: dict with detected intents and their strengths
        """
        message_lower = message.lower()
        detected_intents = {}
        
        for pattern, intent_type in INTENT_PATTERNS.items():
            if re.search(pattern, message_lower, re.IGNORECASE):
                if intent_type not in detected_intents:
                    detected_intents[intent_type] = 0
                detected_intents[intent_type] += 1
        
        # Sort by frequency
        sorted_intents = sorted(detected_intents.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "primary_intent": sorted_intents[0][0] if sorted_intents else "general",
            "all_intents": [i[0] for i in sorted_intents],
            "intent_strengths": dict(sorted_intents)
        }
    
    def _get_workflow_steps_template(self, workflow_type: str) -> List[Dict[str, Any]]:
        """
        Get the recommended step template for a workflow type.
        Based on printify_clean/modules/orchestrator.py patterns.
        """
        templates = {
            "full_campaign_with_video": [
                {"agent": "designer", "action": "generate_design", "critical": True},
                {"agent": "writer", "action": "product_description", "critical": True},
                {"agent": "writer", "action": "video_script", "critical": True},
                {"agent": "video", "action": "generate_promo_video", "critical": True},
                {"agent": "marketer", "action": "social_posts", "critical": False},
                {"agent": "analyst", "action": "summarize", "critical": False},
            ],
            "product_campaign": [
                {"agent": "designer", "action": "generate_design", "critical": True},
                {"agent": "writer", "action": "product_description", "critical": True},
                {"agent": "writer", "action": "generate_tags", "critical": False},
                {"agent": "marketer", "action": "marketing_copy", "critical": False},
            ],
            "video_production": [
                {"agent": "writer", "action": "video_script", "critical": True},
                {"agent": "designer", "action": "thumbnail", "critical": False},
                {"agent": "video", "action": "generate_video", "critical": True},
            ],
            "content_creation": [
                {"agent": "designer", "action": "header_image", "critical": True},  # ALWAYS generate images for content
                {"agent": "researcher", "action": "research", "critical": False},
                {"agent": "writer", "action": "outline", "critical": False},
                {"agent": "writer", "action": "full_content", "critical": True},
            ],
            "social_media": [
                {"agent": "designer", "action": "social_graphics", "critical": False},
                {"agent": "marketer", "action": "social_posts", "critical": True},
                {"agent": "scheduler", "action": "schedule_posts", "critical": False},
            ],
            "research": [
                {"agent": "researcher", "action": "research", "critical": True},
                {"agent": "analyst", "action": "summarize", "critical": True},
            ],
            "image_creation": [
                {"agent": "designer", "action": "generate_design", "critical": True},
            ],
            "general": [
                {"agent": "assistant", "action": "process_request", "critical": True},
            ]
        }
        return templates.get(workflow_type, templates["general"])
    
    def _select_best_model(self, capability_needed: str) -> str:
        """
        Select the best model for a capability based on quality/speed tradeoffs.
        Based on printify_clean/ultra_smart_executor.py MODEL_REGISTRY.
        """
        best_model = None
        best_score = 0
        
        for model_name, model_info in MODEL_CAPABILITIES.items():
            if capability_needed in model_info.get("capabilities", []):
                # Score = quality * 0.7 + speed * 0.3 (favor quality)
                score = model_info.get("quality", 0.5) * 0.7 + model_info.get("speed", 0.5) * 0.3
                if score > best_score:
                    best_score = score
                    best_model = model_name
        
        return best_model or "flux-schnell"  # Default fallback
    
    async def adapt_plan(
        self,
        original_plan: Dict[str, Any],
        failed_step: int,
        error: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Adapt a plan after a step fails.
        """
        prompt = f"""A step in the execution plan failed. Create an adapted plan to still achieve the goal.

Original Intent: {original_plan.get('intent', 'unknown')}

Failed Step #{failed_step}: {original_plan.get('steps', [{}])[failed_step] if failed_step < len(original_plan.get('steps', [])) else 'unknown'}

Error: {error}

Available Tools: {[t['name'] for t in context.get('available_tools', [])[:30]]}

Create a NEW plan that:
1. Works around the failed step
2. Uses alternative approaches
3. Still achieves the user's goal

Return valid JSON with same format as original plan."""

        try:
            response = await asyncio.to_thread(
                self.anthropic.messages.create,
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return self._parse_json_response(response.content[0].text)
            
        except Exception as e:
            logger.error(f"Plan adaptation failed: {e}")
            return {"requires_tools": False, "error": str(e)}
    
    def _categorize_tools(self, tools: List[Dict]) -> Dict[str, List[str]]:
        """Categorize tools by type."""
        categories = {}
        for tool in tools:
            cat = tool.get("category", "other")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(tool["name"])
        return categories
    
    def _format_tools_enhanced(self, tools: List[Dict], by_category: Dict) -> str:
        """Format tools in a more useful way for the AI."""
        output = []
        
        for category, tool_names in by_category.items():
            output.append(f"\n### {category.upper()}")
            for tool in tools:
                if tool["name"] in tool_names:
                    desc = tool.get("description", "No description")[:100]
                    output.append(f"  - {tool['name']}: {desc}")
        
        # Highlight key capabilities
        output.append("\n### KEY CAPABILITIES")
        output.append("  - replicate_*: Search/run ANY AI model on Replicate")
        output.append("  - execute_python: Run any Python code")
        output.append("  - execute_shell: Run any shell command")
        output.append("  - create_file/read_file: File operations")
        output.append("  - search_web/browse_url: Web research")
        
        return "\n".join(output)
    
    def _format_memories(self, memories: List[Dict]) -> str:
        """Format memories for context with full conversation flow."""
        if not memories:
            return "No previous context"
        
        formatted = []
        for i, m in enumerate(memories[-10:]):  # Last 10 messages for better context
            role = m.get('role', 'unknown').upper()
            content = m.get('content', '')[:500]  # More content for context
            
            # Mark important context clues
            if "already exists" in content.lower():
                content = f"⚠️ {content}"
            if "couldn't" in content.lower() or "failed" in content.lower():
                content = f"❌ {content}"
            
            formatted.append(f"[{role}]: {content}")
        
        return "\n".join(formatted)
    
    def _parse_json_response(self, text: str) -> Dict:
        """Parse JSON from AI response, handling markdown formatting."""
        # Try to extract JSON from various formats
        text = text.strip()
        
        # Remove markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            parts = text.split("```")
            if len(parts) >= 2:
                text = parts[1]
        
        # Find JSON object
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            text = match.group()
        
        return json.loads(text.strip())
    
    def _validate_plan(self, plan: Dict, available_tools: List[Dict]) -> Dict:
        """Validate, enhance, and optimize the plan."""
        tool_names = {t["name"] for t in available_tools}
        
        # Ensure required fields
        plan.setdefault("requires_tools", bool(plan.get("steps")))
        plan.setdefault("intent", "Execute user request")
        plan.setdefault("steps", [])
        plan.setdefault("parsed_tasks", [])
        plan.setdefault("parallel_groups", [])
        
        # Validate steps reference existing tools
        valid_steps = []
        for i, step in enumerate(plan.get("steps", [])):
            tool_name = step.get("tool", "")
            step.setdefault("step_id", i)
            step.setdefault("depends_on", [])
            step.setdefault("can_parallel", len(step.get("depends_on", [])) == 0)
            
            if tool_name and tool_name not in tool_names:
                # Try to find similar tool
                similar = [t for t in tool_names if tool_name.split("_")[0] in t]
                if similar:
                    step["tool"] = similar[0]
                    step["note"] = f"Mapped from '{tool_name}' to '{similar[0]}'"
                else:
                    step["note"] = f"Tool '{tool_name}' not found, may need fallback"
            
            valid_steps.append(step)
        
        plan["steps"] = valid_steps
        
        # Auto-generate parallel groups if not provided
        if not plan.get("parallel_groups") and valid_steps:
            plan["parallel_groups"] = self._calculate_parallel_groups(valid_steps)
        
        return plan
    
    def _calculate_parallel_groups(self, steps: List[Dict]) -> List[List[int]]:
        """Calculate which steps can run in parallel based on dependencies."""
        groups = []
        completed = set()
        remaining = set(range(len(steps)))
        
        while remaining:
            # Find steps whose dependencies are all completed
            can_run = []
            for i in remaining:
                deps = set(steps[i].get("depends_on", []))
                if deps.issubset(completed):
                    can_run.append(i)
            
            if not can_run:
                # Circular dependency or error - just add remaining sequentially
                groups.append(list(remaining))
                break
            
            groups.append(can_run)
            completed.update(can_run)
            remaining -= set(can_run)
        
        return groups
    
    def _create_fallback_plan(self, message: str, error: str) -> Dict:
        """Create a fallback plan when planning fails."""
        return {
            "intent": message,
            "requires_tools": False,
            "error": f"Planning failed: {error}",
            "fallback_response": True,
            "steps": []
        }
    
    def _extract_recent_context(self, memories: List[Dict]) -> str:
        """Extract relevant recent context like product types, file IDs, design details, and failed operations."""
        if not memories:
            return "No recent conversation."
        
        context_parts = []
        
        # Look for product types (mug, t-shirt, etc)
        product_mentions = []
        file_mentions = []
        failed_operations = []
        pending_tasks = []
        
        # Track image generation preferences (CRITICAL for context preservation)
        image_preferences = {
            "aspect_ratio": None,
            "style": None,
            "model": None
        }
        
        for i, mem in enumerate(memories[-10:]):  # Last 10 messages for better context
            content = mem.get("content", "")
            role = mem.get("role", "")
            
            # Track failed operations (file exists, couldn't complete, etc.)
            lower_content = content.lower()
            if "already exists" in lower_content:
                # Extract what file exists
                file_match = re.search(r'(\w+\.\w+)\s+already exists', lower_content)
                if file_match:
                    failed_operations.append(f"File '{file_match.group(1)}' already exists")
                else:
                    failed_operations.append("A file already exists")
            
            if "couldn't complete" in lower_content or "couldn't create" in lower_content:
                failed_operations.append(f"Previous operation failed: {content[:100]}")
            
            # Track pending/requested tasks that weren't completed
            if role == "user":
                if "write" in lower_content and ("script" in lower_content or "code" in lower_content or "python" in lower_content):
                    pending_tasks.append("User requested: Write code/script")
                if "create" in lower_content and "file" in lower_content:
                    pending_tasks.append("User requested: Create a file")
            
            # Extract product types
            if "mug" in lower_content:
                product_mentions.append("mug")
            if "t-shirt" in lower_content or "tshirt" in lower_content:
                product_mentions.append("t-shirt")
            
            # CRITICAL: Extract image generation preferences for context preservation
            # Aspect ratio preferences
            if any(kw in lower_content for kw in ["portrait", "tall", "vertical"]):
                image_preferences["aspect_ratio"] = "portrait (2:3)"
            elif any(kw in lower_content for kw in ["landscape", "wide", "horizontal"]):
                image_preferences["aspect_ratio"] = "landscape (3:2)"
            elif any(kw in lower_content for kw in ["cinematic", "widescreen", "movie"]):
                image_preferences["aspect_ratio"] = "cinematic (16:9)"
            elif any(kw in lower_content for kw in ["phone", "story", "tiktok"]):
                image_preferences["aspect_ratio"] = "phone (9:16)"
            
            # Model preferences
            if "flux" in lower_content:
                image_preferences["model"] = "flux_pro"
            elif "sdxl" in lower_content:
                image_preferences["model"] = "sdxl"
            elif "ideogram" in lower_content:
                image_preferences["model"] = "ideogram"
            elif "recraft" in lower_content:
                image_preferences["model"] = "recraft"
            
            # Style preferences
            style_map = {
                "photorealistic": "photorealistic", "realistic": "photorealistic",
                "anime": "anime", "manga": "anime",
                "digital art": "digital_art", "concept art": "digital_art",
                "oil painting": "oil_painting", "watercolor": "watercolor",
                "sketch": "sketch", "vector": "vector", "3d": "3d_render",
                "pixel art": "pixel_art", "minimalist": "minimalist",
                "cyberpunk": "cyberpunk", "fantasy": "fantasy", "vintage": "vintage"
            }
            for kw, style in style_map.items():
                if kw in lower_content:
                    image_preferences["style"] = style
                    break
            
            # Extract file references (paths that were generated)
            file_paths = re.findall(r'/files/[a-f0-9\-]+', content)
            if file_paths:
                file_mentions.extend(file_paths)
            
            # Extract full paths
            full_paths = re.findall(r'/Users/[\w/]+/data/files/[\w/\-\.]+', content)
            if full_paths:
                file_mentions.extend(full_paths)
            
            # Extract workspace file paths
            workspace_paths = re.findall(r'workspace/[\w\.\-/]+', content)
            if workspace_paths:
                file_mentions.extend(workspace_paths)
        
        # Build context summary
        if failed_operations:
            context_parts.append(f"⚠️ PREVIOUS ISSUES: {'; '.join(failed_operations[-2:])}")
        
        if pending_tasks:
            context_parts.append(f"📋 PENDING FROM USER: {'; '.join(pending_tasks[-2:])}")
        
        if product_mentions:
            most_recent_product = product_mentions[-1]
            context_parts.append(f"Recent product type: {most_recent_product}")
        
        if file_mentions:
            recent_files = list(dict.fromkeys(file_mentions))[-3:]  # Last 3 unique files
            context_parts.append(f"Recent files: {', '.join(recent_files)}")
        
        # CRITICAL: Include image generation preferences for context preservation
        active_preferences = []
        if image_preferences["aspect_ratio"]:
            active_preferences.append(f"aspect_ratio: {image_preferences['aspect_ratio']}")
        if image_preferences["model"]:
            active_preferences.append(f"model: {image_preferences['model']}")
        if image_preferences["style"]:
            active_preferences.append(f"style: {image_preferences['style']}")
        
        if active_preferences:
            context_parts.append(f"🎨 USER'S IMAGE PREFERENCES (maintain these for follow-up requests): {', '.join(active_preferences)}")
        
        return " | ".join(context_parts) if context_parts else "No specific context."

    def _ensure_content_has_images(self, plan: Dict[str, Any], message: str) -> Dict[str, Any]:
        """
        Ensure content creation plans ALWAYS include image generation.
        Based on printify_clean pattern: blogs/emails/articles always get images.
        """
        if not plan.get("steps"):
            return plan
        
        steps = plan.get("steps", [])
        
        # Content creation tools that should have images
        content_tools = ["write_blog", "create_blog", "write_email", "create_email", 
                         "write_article", "create_article", "write_newsletter",
                         "generate_blog", "generate_email", "generate_newsletter",
                         "write_content", "create_content"]
        
        # Image generation tools
        image_tools = ["generate_image", "generate_tshirt_design", "create_image",
                       "generate_design", "dall_e", "midjourney", "ideogram"]
        
        # Check if plan has content creation but no images
        has_content_creation = any(
            step.get("tool", "") in content_tools or
            any(ct in step.get("tool", "").lower() for ct in ["blog", "email", "article", "newsletter", "content"])
            for step in steps
        )
        
        has_image_generation = any(
            step.get("tool", "") in image_tools or
            any(it in step.get("tool", "").lower() for it in ["image", "design", "photo", "picture"])
            for step in steps
        )
        
        # If creating content without images, inject image generation step
        if has_content_creation and not has_image_generation:
            # Extract topic from message or plan intent
            topic = plan.get("intent", message)[:100]
            
            # Find the content creation step to get its step_id
            content_step_id = None
            for step in steps:
                tool = step.get("tool", "").lower()
                if any(ct in tool for ct in ["blog", "email", "article", "newsletter", "content"]):
                    content_step_id = step.get("step_id", 0)
                    break
            
            # Create image generation step to go BEFORE content
            image_step = {
                "step_id": 0,
                "tool": "generate_image",
                "description": "Generate professional header image for content",
                "parameters": {
                    "prompt": f"Professional, clean, modern illustration for: {topic}. High quality, suitable for blog header or email banner. No text overlay, vibrant colors, professional design.",
                    "aspect_ratio": "16:9",
                    "style": "professional"
                },
                "depends_on": [],
                "can_parallel": True,
                "auto_injected": True
            }
            
            # Renumber all existing steps
            for step in steps:
                step["step_id"] = step.get("step_id", 0) + 1
                # Update depends_on references
                if step.get("depends_on"):
                    step["depends_on"] = [d + 1 for d in step["depends_on"]]
            
            # Add image step reference to content steps
            for step in steps:
                tool = step.get("tool", "").lower()
                if any(ct in tool for ct in ["blog", "email", "article", "newsletter", "content"]):
                    # Add image reference to parameters
                    if "parameters" not in step:
                        step["parameters"] = {}
                    step["parameters"]["header_image"] = "{{step_0_output}}"
                    step["depends_on"] = [0] + step.get("depends_on", [])
            
            # Insert image step at beginning
            steps.insert(0, image_step)
            plan["steps"] = steps
            
            # Add note about auto-injected images
            if "proactive_additions" not in plan:
                plan["proactive_additions"] = []
            plan["proactive_additions"].append("Auto-generating professional image for your content")
            
            logger.info("Auto-injected image generation step for content creation")
        
        return plan
    
    def _expand_plan_proactively(self, plan: Dict[str, Any], message: str) -> Dict[str, Any]:
        """
        Proactively expand the plan with helpful additional tasks.
        This makes Otto more autonomous by anticipating user needs.
        """
        if not plan.get("steps"):
            return plan
        
        message_lower = message.lower()
        steps = plan.get("steps", [])
        expanded_steps = []
        proactive_note = []
        
        for step in steps:
            expanded_steps.append(step)
            tool = step.get("tool", "")
            
            # If creating an image design, proactively suggest products
            if tool in ["generate_image", "generate_tshirt_design"] and "design" in message_lower:
                # Check if product creation isn't already in the plan
                has_product_step = any(
                    s.get("tool", "").startswith("printify_") 
                    for s in steps
                )
                if not has_product_step and any(w in message_lower for w in ["sell", "product", "store", "shop"]):
                    # Add product creation steps automatically
                    step_id = step.get("step_id", 0)
                    proactive_note.append("Also creating products from your design")
                    
            # If creating a t-shirt, proactively create related products
            if tool == "printify_create_tshirt":
                # Check if user might want related products
                if "and mug" not in message_lower and "only" not in message_lower:
                    # Could add mug variant later if there's demand
                    pass
            
            # If writing code, proactively add documentation
            if tool in ["create_file", "execute_python"] and any(
                ext in str(step.get("parameters", {}))
                for ext in [".py", ".js", ".ts"]
            ):
                proactive_note.append("Adding inline documentation to code")
            
            # If researching, proactively summarize findings
            if tool in ["search_web", "browse_url"]:
                proactive_note.append("Will summarize key findings")
        
        plan["steps"] = expanded_steps
        
        if proactive_note:
            plan["proactive_additions"] = list(set(proactive_note))
            logger.info(f"Proactively expanded plan: {proactive_note}")
        
        return plan

# Enhanced Planning Agent export (replaces old one)
PlanningAgent = SuperPlanningAgent
