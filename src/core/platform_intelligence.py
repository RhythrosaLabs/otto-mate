"""
Platform Intelligence Module
============================

Comprehensive knowledge base derived from research on 18+ leading platforms:
- n8n, Zapier (workflow automation)
- browser-use, Claude Computer Use (browser/desktop automation)
- Quivr, CrewAI, AutoGPT (AI agents & multi-agent systems)
- Canva, Adobe Firefly, Stability AI (creative tools)
- Replicate (model marketplace)
- GitHub Copilot (code assistance)
- ComfyUI (node-based workflows)
- Lovable, Replit, Bolt (AI app builders)

This module enhances Otto's conversational intelligence with:
1. Rich intent patterns for diverse task types
2. Workflow templates for common automation scenarios
3. Model selection intelligence
4. Creative tool knowledge
5. Integration patterns
6. Multi-agent collaboration strategies
"""

import re
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# ENHANCED INTENT CATEGORIES (Expanded from research)
# ============================================================================

class EnhancedIntentCategory(Enum):
    """Rich intent categories covering all researched platform capabilities."""
    
    # Creative (from Canva, Firefly, Stability, ComfyUI)
    IMAGE_GENERATION = "image_generation"
    IMAGE_EDITING = "image_editing"
    VIDEO_GENERATION = "video_generation"
    VIDEO_EDITING = "video_editing"
    AUDIO_GENERATION = "audio_generation"
    DESIGN_CREATION = "design_creation"
    BACKGROUND_REMOVAL = "background_removal"
    UPSCALING = "upscaling"
    STYLE_TRANSFER = "style_transfer"
    
    # Content (from Quivr, general)
    CONTENT_WRITING = "content_writing"
    COPYWRITING = "copywriting"
    SOCIAL_MEDIA = "social_media"
    EMAIL_MARKETING = "email_marketing"
    
    # Automation (from n8n, Zapier)
    WORKFLOW_AUTOMATION = "workflow_automation"
    DATA_SYNC = "data_sync"
    TRIGGER_ACTION = "trigger_action"
    SCHEDULED_TASK = "scheduled_task"
    MULTI_STEP_WORKFLOW = "multi_step_workflow"
    
    # Browser/Desktop (from browser-use, Claude Computer Use)
    WEB_SCRAPING = "web_scraping"
    FORM_AUTOMATION = "form_automation"
    BROWSER_NAVIGATION = "browser_navigation"
    DATA_EXTRACTION = "data_extraction"
    SCREENSHOT_ANALYSIS = "screenshot_analysis"
    
    # Support/CRM (from Quivr)
    TICKET_HANDLING = "ticket_handling"
    CUSTOMER_SUPPORT = "customer_support"
    DRAFT_RESPONSE = "draft_response"
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    
    # E-commerce (from Printify, Shopify patterns)
    PRODUCT_CREATION = "product_creation"
    INVENTORY_MANAGEMENT = "inventory_management"
    ORDER_PROCESSING = "order_processing"
    PRICING_OPTIMIZATION = "pricing_optimization"
    
    # Research & Analysis
    MARKET_RESEARCH = "market_research"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    TREND_ANALYSIS = "trend_analysis"
    DATA_ANALYSIS = "data_analysis"
    
    # Code & Technical (from GitHub Copilot, Replit)
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    DEBUGGING = "debugging"
    API_INTEGRATION = "api_integration"
    
    # General
    QUESTION_ANSWERING = "question_answering"
    CONVERSATION = "conversation"
    FILE_MANAGEMENT = "file_management"
    SETTINGS = "settings"


# ============================================================================
# COMPREHENSIVE INTENT PATTERNS (from all researched platforms)
# ============================================================================

INTENT_PATTERN_DATABASE = {
    # ═══════════════════════════════════════════════════════════════════════
    # CREATIVE INTENTS (Canva, Firefly, Stability, ComfyUI patterns)
    # ═══════════════════════════════════════════════════════════════════════
    
    EnhancedIntentCategory.IMAGE_GENERATION: [
        r"(generat|creat|mak|produc|render|design).*(image|picture|photo|art|illustration|graphic|visual)",
        r"(text|prompt)\s*(to|→|->)\s*(image|picture|art)",
        r"(draw|paint|visualize|imagine|dream\s*up)",
        r"(flux|sdxl|dall-?e|midjourney|stable\s*diffusion)",
        r"(concept\s*art|digital\s*art|ai\s*art)",
    ],
    
    EnhancedIntentCategory.IMAGE_EDITING: [
        # From Canva Magic features
        r"(edit|modif|chang|transform|alter|adjust|tweak).*(image|photo|picture)",
        r"magic\s*(edit|eraser|expand|resize|grab)",
        r"(add|remove|delete|erase).*(object|element|person|thing)",
        r"(replace|swap|change).*(background|sky|face)",
        r"(retouch|enhance|fix|correct|improve).*(photo|image)",
        r"(crop|rotate|flip|straighten)",
        r"(filter|effect|preset|lut)",
        # Color adjustments
        r"(brighten|darken|saturate|desaturate|contrast|vibran)",
        r"(color\s*correct|white\s*balance|exposure)",
    ],
    
    EnhancedIntentCategory.BACKGROUND_REMOVAL: [
        r"(remove|delete|erase|cut\s*out).*(background|bg)",
        r"(transparent|isolate|extract).*(background|subject)",
        r"background\s*(remov|delet|eras)",
        r"(cutout|cut-out|cut out)",
        r"(mask|segment).*(subject|person|object)",
    ],
    
    EnhancedIntentCategory.UPSCALING: [
        r"(upscal|enhanc|increas|improv).*(resolution|quality|size|detail)",
        r"(super|hyper|ultra).*(resolution|res|scale)",
        r"(2x|4x|8x)\s*(upscal|enhanc|scale)",
        r"(ai\s*)?upscal",
        r"(higher|better)\s*(resolution|quality)",
        r"(enlarg|scale\s*up|blow\s*up)",
    ],
    
    EnhancedIntentCategory.STYLE_TRANSFER: [
        r"(style|stylize|restyl|transfer).*(to|as|like|into)",
        r"(ghibli|anime|cartoon|sketch|watercolor|oil\s*paint)",
        r"make.*(look\s*like|style\s*of)",
        r"(apply|add).*(style|filter|effect)",
        r"(turn|convert|transform).*(into|to).*(style|art)",
    ],
    
    EnhancedIntentCategory.VIDEO_GENERATION: [
        r"(generat|creat|mak|produc).*(video|animation|motion|clip)",
        r"(text|image|prompt)\s*(to|→|->)\s*video",
        r"(animat|bring\s*to\s*life|make.*move)",
        r"(kling|luma|runway|pika|stable\s*video|sora)",
        r"(promo|commercial|ad|advertisement)\s*video",
        r"(talking\s*head|avatar|character)\s*video",
    ],
    
    EnhancedIntentCategory.VIDEO_EDITING: [
        r"(edit|cut|trim|splice).*(video|clip|footage)",
        r"(add|insert).*(caption|subtitle|text|overlay).*(video)",
        r"(merge|combine|concatenate|join).*(video|clip)",
        r"(speed\s*up|slow\s*down|reverse).*(video)",
        r"(video|clip).*(transition|effect|filter)",
    ],
    
    EnhancedIntentCategory.AUDIO_GENERATION: [
        r"(generat|creat|mak|produc|compos).*(music|audio|sound|track|song)",
        r"(text|prompt)\s*(to|→|->)\s*(speech|audio|music)",
        r"(voiceover|narration|tts|text-to-speech)",
        r"(sound\s*effect|sfx|foley)",
        r"(clone|mimic|replicate).*voice",
    ],
    
    EnhancedIntentCategory.DESIGN_CREATION: [
        # From Canva patterns
        r"(design|creat|mak).*(logo|banner|flyer|poster|brochure|card)",
        r"(brand|identity|branding).*(kit|guideline|asset)",
        r"(social\s*media|instagram|facebook|twitter).*(template|post|story)",
        r"(presentation|slide|deck|pitch)",
        r"(infographic|data\s*viz|chart|graph)",
        r"(mockup|mock-up|prototype)",
    ],
    
    # ═══════════════════════════════════════════════════════════════════════
    # AUTOMATION INTENTS (n8n, Zapier patterns)
    # ═══════════════════════════════════════════════════════════════════════
    
    EnhancedIntentCategory.WORKFLOW_AUTOMATION: [
        r"(automat|workflow|flow|pipeline|chain)",
        r"(when|whenever|if|trigger).*(then|do|execute|run)",
        r"(set\s*up|creat|build).*(automation|workflow|integration)",
        r"(connect|link|sync).*(app|service|tool|platform)",
        r"(n8n|zapier|make|integromat|ifttt)",
        r"(no-?code|low-?code).*(automation|workflow)",
    ],
    
    EnhancedIntentCategory.DATA_SYNC: [
        r"(sync|synchroniz|mirror|replicate).*(data|record|contact|lead)",
        r"(two-?way|bidirectional)\s*sync",
        r"(keep|maintain).*(in\s*sync|updated|synchronized)",
        r"(push|pull|transfer).*(data|record)",
    ],
    
    EnhancedIntentCategory.TRIGGER_ACTION: [
        r"(when|whenever|if|on).*(new|created|updated|changed|received)",
        r"(trigger|fire|execute).*(when|on|after)",
        r"(webhook|event|signal).*(trigger|fire|call)",
        r"(on|upon).*(form\s*submit|email|message|event)",
    ],
    
    EnhancedIntentCategory.SCHEDULED_TASK: [
        r"(every|each|daily|weekly|monthly|hourly)",
        r"(schedule|cron|recurring|periodic)",
        r"(at|on).*(time|date|day|hour|minute)",
        r"(run|execute).*(automatically|periodically|regularly)",
    ],
    
    EnhancedIntentCategory.MULTI_STEP_WORKFLOW: [
        r"(then|after\s*that|next|followed\s*by)",
        r"(multi-?step|chain|sequence|pipeline)",
        r"(first|second|third|finally|lastly)",
        r"(step\s*\d|phase\s*\d|stage\s*\d)",
        r"(and\s*then|,\s*then|>\s*then)",
    ],
    
    # ═══════════════════════════════════════════════════════════════════════
    # BROWSER/DESKTOP INTENTS (browser-use, Claude Computer Use patterns)
    # ═══════════════════════════════════════════════════════════════════════
    
    EnhancedIntentCategory.WEB_SCRAPING: [
        r"(scrap|extract|collect|gather|harvest).*(data|info|content|text)",
        r"(get|fetch|retrieve|pull).*(from|off)\s*(website|page|url|site)",
        r"(monitor|track|watch).*(website|page|price|stock|change)",
        r"(crawl|spider|bot).*(website|page|site)",
    ],
    
    EnhancedIntentCategory.FORM_AUTOMATION: [
        r"(fill|complet|submit).*(form|application|survey)",
        r"(automat|auto-?fill).*(form|field|input)",
        r"(enter|input|type).*(data|info).*(form|field)",
    ],
    
    EnhancedIntentCategory.BROWSER_NAVIGATION: [
        r"(go\s*to|visit|navigate|open|browse).*(website|url|page|site)",
        r"(click|press|tap).*(button|link|element)",
        r"(scroll|swipe|drag).*(down|up|page)",
        r"(search|find).*(on|in)\s*(google|website|page)",
        r"(login|log\s*in|sign\s*in).*(to|into)",
    ],
    
    EnhancedIntentCategory.DATA_EXTRACTION: [
        r"(extract|get|find|locate).*(email|phone|contact|lead|address)",
        r"(list|table|data).*(from|on)\s*(page|website)",
        r"(parse|read|interpret).*(html|page|content)",
        r"(find\s*all|get\s*all|extract\s*all)",
    ],
    
    EnhancedIntentCategory.SCREENSHOT_ANALYSIS: [
        r"(screenshot|screen\s*cap|capture).*(page|screen|website)",
        r"(look\s*at|see|view|check).*(screen|page|what.*see)",
        r"(analyze|understand|interpret).*(screen|interface|ui)",
    ],
    
    # ═══════════════════════════════════════════════════════════════════════
    # SUPPORT/CRM INTENTS (Quivr patterns)
    # ═══════════════════════════════════════════════════════════════════════
    
    EnhancedIntentCategory.TICKET_HANDLING: [
        r"(ticket|support\s*request|issue|case).*(handl|process|resolv|respond)",
        r"(customer|user|client).*(complaint|inquiry|question)",
        r"(route|assign|escalate|prioritize).*(ticket|issue|case)",
        r"(helpdesk|zendesk|intercom|freshdesk|gorgias)",
    ],
    
    EnhancedIntentCategory.CUSTOMER_SUPPORT: [
        r"(customer|user|client).*(support|service|help|assist)",
        r"(answer|respond|reply).*(customer|user|inquiry|question)",
        r"(refund|return|exchange|cancel)",
        r"(where.*order|track.*shipment|delivery\s*status)",
    ],
    
    EnhancedIntentCategory.DRAFT_RESPONSE: [
        r"(draft|write|compose).*(response|reply|email|message)",
        r"(respond|reply).*(to|for).*(email|message|inquiry)",
        r"(suggest|generate).*(response|reply|answer)",
    ],
    
    EnhancedIntentCategory.KNOWLEDGE_RETRIEVAL: [
        r"(find|search|look\s*up).*(in|from).*(knowledge|docs|documentation|wiki)",
        r"(help\s*article|faq|documentation).*(about|for|on)",
        r"(what.*policy|how.*process|where.*info)",
    ],
    
    EnhancedIntentCategory.SENTIMENT_ANALYSIS: [
        r"(sentiment|emotion|feeling|tone).*(analy|detect|measur)",
        r"(angry|happy|frustrated|satisfied).*(customer|user|message)",
        r"(positive|negative|neutral).*(feedback|review|comment)",
    ],
    
    # ═══════════════════════════════════════════════════════════════════════
    # E-COMMERCE INTENTS
    # ═══════════════════════════════════════════════════════════════════════
    
    EnhancedIntentCategory.PRODUCT_CREATION: [
        r"(creat|add|list|publish).*(product|item|listing)",
        r"(t-?shirt|hoodie|mug|poster|sticker|merch)",
        r"(printify|shopify|etsy|amazon).*(product|listing)",
        r"(sell|offer).*(on|through).*(store|shop|marketplace)",
    ],
    
    EnhancedIntentCategory.INVENTORY_MANAGEMENT: [
        r"(inventory|stock).*(manag|track|updat|check)",
        r"(quantity|level|count).*(product|item|sku)",
        r"(low\s*stock|out\s*of\s*stock|reorder)",
    ],
    
    EnhancedIntentCategory.ORDER_PROCESSING: [
        r"(order|purchase|transaction).*(process|fulfill|ship)",
        r"(confirm|track|status).*(order|shipment)",
        r"(packing|shipping|delivery)",
    ],
    
    EnhancedIntentCategory.PRICING_OPTIMIZATION: [
        r"(price|pricing).*(set|adjust|optimiz|compet)",
        r"(margin|profit|cost).*(calculat|analyz)",
        r"(discount|sale|promotion|deal)",
    ],
    
    # ═══════════════════════════════════════════════════════════════════════
    # RESEARCH & ANALYSIS INTENTS
    # ═══════════════════════════════════════════════════════════════════════
    
    EnhancedIntentCategory.MARKET_RESEARCH: [
        r"(market|industry).*(research|analysis|study|report)",
        r"(target|audience|demographic).*(research|analysis|identify)",
        r"(opportunity|potential|demand).*(assess|evaluat|analyz)",
    ],
    
    EnhancedIntentCategory.COMPETITOR_ANALYSIS: [
        r"(competitor|competition|rival).*(analyz|research|study|monitor)",
        r"(compare|benchmark|versus|vs).*(competitor|alternative)",
        r"(competitive\s*landscape|market\s*position)",
    ],
    
    EnhancedIntentCategory.TREND_ANALYSIS: [
        r"(trend|trending|popular|viral).*(analyz|find|identify|track)",
        r"(what.*trending|latest\s*trend|emerging\s*trend)",
        r"(hashtag|topic|keyword).*(trending|popular|hot)",
    ],
    
    EnhancedIntentCategory.DATA_ANALYSIS: [
        r"(data|metrics|stats|analytics).*(analyz|process|interpret)",
        r"(insight|pattern|correlation).*(find|identify|discover)",
        r"(report|dashboard|visualization).*(creat|generat|build)",
    ],
    
    # ═══════════════════════════════════════════════════════════════════════
    # CODE & TECHNICAL INTENTS (GitHub Copilot, Replit patterns)
    # ═══════════════════════════════════════════════════════════════════════
    
    EnhancedIntentCategory.CODE_GENERATION: [
        r"(write|creat|generat|build).*(code|function|script|program|app)",
        r"(implement|develop|code).*(feature|functionality|logic)",
        r"(python|javascript|typescript|java|react|node)",
        r"(api|endpoint|route|controller)",
    ],
    
    EnhancedIntentCategory.CODE_REVIEW: [
        r"(review|check|audit).*(code|implementation|pr|pull\s*request)",
        r"(improve|refactor|optimize).*(code|performance)",
        r"(best\s*practice|clean\s*code|code\s*quality)",
    ],
    
    EnhancedIntentCategory.DEBUGGING: [
        r"(debug|fix|solve|troubleshoot).*(error|bug|issue|problem)",
        r"(why.*not\s*work|what.*wrong|error.*message)",
        r"(trace|diagnose|investigate).*(issue|problem|bug)",
    ],
    
    EnhancedIntentCategory.API_INTEGRATION: [
        r"(integrat|connect|call).*(api|service|endpoint)",
        r"(webhook|callback|rest|graphql)",
        r"(oauth|authentication|authorization)",
    ],
    
    # ═══════════════════════════════════════════════════════════════════════
    # CONTENT CREATION INTENTS
    # ═══════════════════════════════════════════════════════════════════════
    
    EnhancedIntentCategory.CONTENT_WRITING: [
        r"(write|creat|generat|compose).*(article|blog|post|content|copy)",
        r"(draft|outline|structure).*(article|content|piece)",
        r"(seo|keyword|organic).*(content|article|post)",
    ],
    
    EnhancedIntentCategory.COPYWRITING: [
        r"(write|creat|generat).*(copy|headline|tagline|slogan)",
        r"(marketing|sales|ad|advertisement).*(copy|text|message)",
        r"(persuasive|compelling|converting).*(copy|text)",
        r"(cta|call-?to-?action|hook)",
    ],
    
    EnhancedIntentCategory.SOCIAL_MEDIA: [
        r"(social\s*media|instagram|twitter|x|facebook|linkedin|tiktok)",
        r"(post|share|publish).*(social|platform)",
        r"(caption|hashtag|engagement)",
        r"(content\s*calendar|scheduling|planning)",
    ],
    
    EnhancedIntentCategory.EMAIL_MARKETING: [
        r"(email|newsletter|campaign).*(write|creat|send)",
        r"(subject\s*line|open\s*rate|click\s*rate)",
        r"(drip|sequence|autoresponder)",
        r"(mailchimp|sendgrid|convertkit|klaviyo)",
    ],
    
    # ═══════════════════════════════════════════════════════════════════════
    # GENERAL INTENTS
    # ═══════════════════════════════════════════════════════════════════════
    
    EnhancedIntentCategory.QUESTION_ANSWERING: [
        r"^(what|who|where|when|why|how|which|can\s*you)\s",
        r"(explain|tell\s*me|describe|define|help\s*me\s*understand)",
        r"(difference\s*between|compared\s*to|versus|vs)",
    ],
    
    EnhancedIntentCategory.FILE_MANAGEMENT: [
        r"(save|store|upload|download|export|import).*(file|image|video|document)",
        r"(list|show|find).*(files|documents|uploads)",
        r"(organize|rename|move|delete).*(file|folder)",
    ],
}


# ============================================================================
# WORKFLOW TEMPLATES (from n8n, Zapier, Quivr patterns)
# ============================================================================

WORKFLOW_TEMPLATES = {
    "content_with_visuals": {
        "description": "Create content with accompanying images",
        "triggers": ["blog", "article", "email", "newsletter", "content"],
        "excludes": ["only text", "no image", "text only"],
        "steps": [
            {"action": "generate_header_image", "parallel": True},
            {"action": "write_content", "parallel": True},
            {"action": "generate_inline_images", "depends_on": "write_content"},
            {"action": "combine_content_with_images"}
        ]
    },
    
    "product_to_video": {
        "description": "Create product and promotional video",
        "triggers": ["video ad", "promo video", "product video", "commercial"],
        "requires": ["product", "design", "shirt", "mug"],
        "steps": [
            {"action": "generate_design"},
            {"action": "create_product", "depends_on": "generate_design"},
            {"action": "get_mockup", "depends_on": "create_product"},
            {"action": "generate_voiceover", "parallel": True},
            {"action": "create_video", "depends_on": ["get_mockup", "generate_voiceover"]}
        ]
    },
    
    "customer_support_response": {
        "description": "Analyze and respond to customer inquiry",
        "triggers": ["respond to", "reply to", "answer", "customer", "ticket"],
        "steps": [
            {"action": "analyze_sentiment"},
            {"action": "retrieve_knowledge"},
            {"action": "draft_response", "depends_on": ["analyze_sentiment", "retrieve_knowledge"]},
            {"action": "review_and_send"}
        ]
    },
    
    "competitor_research": {
        "description": "Research and analyze competitors",
        "triggers": ["competitor", "competition", "market research", "analyze"],
        "steps": [
            {"action": "identify_competitors"},
            {"action": "scrape_competitor_data", "parallel": True},
            {"action": "analyze_pricing", "parallel": True},
            {"action": "analyze_features", "parallel": True},
            {"action": "generate_report", "depends_on": ["analyze_pricing", "analyze_features"]}
        ]
    },
    
    "social_media_campaign": {
        "description": "Create multi-platform social media campaign",
        "triggers": ["social media campaign", "social campaign", "post everywhere"],
        "steps": [
            {"action": "generate_visuals"},
            {"action": "write_captions_per_platform", "depends_on": "generate_visuals"},
            {"action": "schedule_posts"}
        ]
    },
    
    "data_sync_workflow": {
        "description": "Sync data between platforms",
        "triggers": ["sync", "synchronize", "connect", "integrate"],
        "steps": [
            {"action": "fetch_source_data"},
            {"action": "transform_data"},
            {"action": "push_to_destination"},
            {"action": "verify_sync"}
        ]
    },
    
    "lead_extraction": {
        "description": "Extract and process leads from websites",
        "triggers": ["extract leads", "find contacts", "scrape emails", "get leads"],
        "steps": [
            {"action": "navigate_to_source"},
            {"action": "extract_contact_data"},
            {"action": "validate_emails", "parallel": True},
            {"action": "enrich_data", "parallel": True},
            {"action": "export_to_crm"}
        ]
    }
}


# ============================================================================
# MODEL INTELLIGENCE (from Replicate, Stability, ComfyUI research)
# ============================================================================

MODEL_KNOWLEDGE = {
    # Image Generation Models - comprehensive from Replicate
    "image_generation": {
        "flux-pro": {
            "quality": 0.98, "speed": 0.5, "cost": "high",
            "best_for": ["commercial", "ultra-quality", "detailed"],
            "supports": ["text2img", "inpainting", "controlnet"]
        },
        "flux-dev": {
            "quality": 0.95, "speed": 0.6, "cost": "medium",
            "best_for": ["artistic", "creative", "high-quality"],
            "supports": ["text2img", "lora"]
        },
        "flux-schnell": {
            "quality": 0.85, "speed": 0.95, "cost": "low",
            "best_for": ["fast", "prototyping", "iterations"],
            "supports": ["text2img"]
        },
        "ideogram": {
            "quality": 0.92, "speed": 0.7, "cost": "medium",
            "best_for": ["logos", "text-rendering", "typography"],
            "supports": ["text2img", "text-in-image"]
        },
        "sdxl": {
            "quality": 0.90, "speed": 0.7, "cost": "medium",
            "best_for": ["versatile", "controlnet", "fine-tuning"],
            "supports": ["text2img", "img2img", "controlnet", "lora"]
        },
        "dalle3": {
            "quality": 0.94, "speed": 0.6, "cost": "high",
            "best_for": ["creative", "artistic", "detailed"],
            "supports": ["text2img"]
        },
        "nano-banana": {
            "quality": 0.96, "speed": 0.7, "cost": "medium",
            "best_for": ["google", "photorealistic", "editing"],
            "supports": ["text2img", "editing"]
        }
    },
    
    # Video Generation Models
    "video_generation": {
        "kling-v2.6": {
            "quality": 0.94, "speed": 0.25, "cost": "high",
            "best_for": ["cinematic", "realistic", "audio-included"],
            "supports": ["text2video", "img2video", "audio"]
        },
        "veo-3.1": {
            "quality": 0.95, "speed": 0.3, "cost": "high",
            "best_for": ["google", "high-quality", "fast"],
            "supports": ["text2video", "img2video"]
        },
        "luma-dream-machine": {
            "quality": 0.88, "speed": 0.4, "cost": "medium",
            "best_for": ["cinematic", "creative", "camera-control"],
            "supports": ["text2video", "img2video"]
        },
        "minimax": {
            "quality": 0.90, "speed": 0.3, "cost": "medium",
            "best_for": ["high-quality", "long-duration"],
            "supports": ["text2video", "img2video"]
        },
        "runway-gen3": {
            "quality": 0.92, "speed": 0.35, "cost": "high",
            "best_for": ["professional", "editing", "motion"],
            "supports": ["text2video", "img2video", "video2video"]
        }
    },
    
    # Audio/Speech Models
    "audio_generation": {
        "elevenlabs-music": {
            "quality": 0.95, "speed": 0.5, "cost": "high",
            "best_for": ["songs", "composed-music", "vocals"],
            "supports": ["text2music", "composition"]
        },
        "stable-audio-2.5": {
            "quality": 0.92, "speed": 0.6, "cost": "medium",
            "best_for": ["background-music", "sound-effects", "loops"],
            "supports": ["text2music", "sound-effects"]
        },
        "minimax-speech": {
            "quality": 0.94, "speed": 0.75, "cost": "medium",
            "best_for": ["voiceover", "narration", "voice-clone"],
            "supports": ["tts", "voice-clone", "multilingual"]
        },
        "qwen3-tts": {
            "quality": 0.92, "speed": 0.8, "cost": "low",
            "best_for": ["tts", "voice-design", "multilingual"],
            "supports": ["tts", "voice-clone", "voice-design"]
        }
    },
    
    # Image Editing Models
    "image_editing": {
        "rembg": {
            "quality": 0.90, "speed": 0.95, "cost": "free",
            "best_for": ["background-removal", "fast"],
            "supports": ["bg-removal"]
        },
        "real-esrgan": {
            "quality": 0.92, "speed": 0.85, "cost": "low",
            "best_for": ["upscaling", "enhancement"],
            "supports": ["upscale", "4x", "8x"]
        },
        "instruct-pix2pix": {
            "quality": 0.85, "speed": 0.7, "cost": "medium",
            "best_for": ["instruction-based-edit", "style-change"],
            "supports": ["edit"]
        }
    },
    
    # LLM Models
    "language_models": {
        "claude-opus-4": {
            "quality": 0.99, "speed": 0.4, "cost": "very-high",
            "best_for": ["complex-reasoning", "coding", "agentic"],
            "context": 200000
        },
        "claude-sonnet-4": {
            "quality": 0.95, "speed": 0.7, "cost": "medium",
            "best_for": ["balanced", "general", "fast"],
            "context": 200000
        },
        "gpt-5": {
            "quality": 0.95, "speed": 0.6, "cost": "high",
            "best_for": ["general", "creative", "reasoning"],
            "context": 128000
        },
        "gemini-3-flash": {
            "quality": 0.92, "speed": 0.9, "cost": "low",
            "best_for": ["fast", "multimodal", "grounded"],
            "context": 1000000
        }
    }
}


# ============================================================================
# CREATIVE TOOL KNOWLEDGE (from Canva, Firefly, Stability patterns)
# ============================================================================

CREATIVE_TOOL_MAPPING = {
    # One-click actions (from Canva)
    "background_removal": {
        "keywords": ["remove background", "transparent", "cutout", "isolate"],
        "tool": "remove_background",
        "parameters": {"mode": "auto"}
    },
    "magic_resize": {
        "keywords": ["resize", "adapt", "different size", "social media sizes"],
        "platforms": {
            "instagram_post": "1080x1080",
            "instagram_story": "1080x1920",
            "facebook_cover": "1640x924",
            "twitter_header": "1500x500",
            "youtube_thumbnail": "1280x720",
            "pinterest_pin": "1000x1500",
            "linkedin_banner": "1584x396"
        }
    },
    "magic_eraser": {
        "keywords": ["remove object", "erase", "delete element", "clean up"],
        "tool": "inpaint",
        "parameters": {"mode": "remove"}
    },
    "magic_write": {
        "keywords": ["write copy", "generate text", "content", "caption"],
        "tool": "generate_text",
        "parameters": {"style": "professional"}
    },
    "magic_expand": {
        "keywords": ["expand image", "extend canvas", "outpaint", "uncrop"],
        "tool": "outpaint",
        "parameters": {"mode": "expand"}
    },
    "enhance_photo": {
        "keywords": ["enhance", "improve photo", "better quality", "auto enhance"],
        "tool": "auto_enhance",
        "adjustments": ["brightness", "contrast", "saturation", "sharpness"]
    },
    
    # AI Generations (from Firefly, Stability)
    "generate_from_prompt": {
        "keywords": ["imagine", "create", "generate", "dream up"],
        "tool": "text_to_image",
        "default_model": "flux-schnell"
    },
    "style_reference": {
        "keywords": ["in the style of", "like this", "match style", "similar to"],
        "tool": "image_to_image",
        "parameters": {"preserve_content": True, "style_strength": 0.7}
    },
    "generative_fill": {
        "keywords": ["fill", "replace with", "put a", "add a"],
        "tool": "inpaint",
        "parameters": {"mode": "fill"}
    }
}


# ============================================================================
# INTEGRATION PATTERNS (from n8n, Zapier, Quivr)
# ============================================================================

INTEGRATION_KNOWLEDGE = {
    # Helpdesk Systems (from Quivr)
    "helpdesk": {
        "zendesk": {"actions": ["create_ticket", "update_ticket", "get_tickets", "add_comment"]},
        "intercom": {"actions": ["send_message", "create_conversation", "get_users"]},
        "freshdesk": {"actions": ["create_ticket", "update_ticket", "get_tickets"]},
        "gorgias": {"actions": ["create_ticket", "get_tickets", "send_message"]}
    },
    
    # E-commerce (from existing + research)
    "ecommerce": {
        "shopify": {"actions": ["create_product", "update_inventory", "get_orders", "create_collection"]},
        "printify": {"actions": ["create_product", "publish_product", "get_mockups", "list_blueprints"]},
        "woocommerce": {"actions": ["create_product", "update_product", "get_orders"]},
        "etsy": {"actions": ["create_listing", "update_listing", "get_orders"]}
    },
    
    # CRM (from Quivr)
    "crm": {
        "salesforce": {"actions": ["create_lead", "update_contact", "create_opportunity"]},
        "hubspot": {"actions": ["create_contact", "update_deal", "create_ticket"]},
        "zoho": {"actions": ["create_lead", "update_contact", "create_deal"]},
        "airtable": {"actions": ["create_record", "update_record", "get_records"]}
    },
    
    # Communication (from n8n, Zapier)
    "communication": {
        "slack": {"actions": ["send_message", "create_channel", "post_file"]},
        "teams": {"actions": ["send_message", "create_meeting", "post_channel"]},
        "discord": {"actions": ["send_message", "create_webhook", "post_channel"]},
        "email": {"actions": ["send_email", "create_draft", "schedule_email"]}
    },
    
    # Storage & Docs (from Quivr)
    "storage": {
        "google_drive": {"actions": ["upload_file", "create_folder", "share_file"]},
        "dropbox": {"actions": ["upload_file", "share_link", "create_folder"]},
        "notion": {"actions": ["create_page", "update_database", "add_block"]},
        "google_docs": {"actions": ["create_document", "update_document", "share_document"]}
    },
    
    # Payment (from Quivr)
    "payment": {
        "stripe": {"actions": ["create_payment", "refund", "get_transactions"]},
        "paypal": {"actions": ["create_payment", "refund", "get_balance"]},
        "square": {"actions": ["create_payment", "refund", "get_transactions"]}
    }
}


# ============================================================================
# AGENT PERSONAS (from Quivr's specialized agents)
# ============================================================================

AGENT_PERSONAS = {
    "kelly": {
        "name": "Kelly",
        "role": "Draft Composer",
        "description": "Expert at writing responses that match your tone and brand voice",
        "capabilities": ["smart_drafts", "translation", "knowledge_retrieval"],
        "system_prompt": "You are Kelly, a skilled draft composer. You write responses that perfectly match the user's tone and brand voice. Be professional yet personable.",
        "triggers": ["draft", "write response", "compose", "reply to"]
    },
    "michael": {
        "name": "Michael",
        "role": "Action Executor",
        "description": "Takes action - refunds, account updates, workflow execution",
        "capabilities": ["refunds", "account_updates", "workflow_execution"],
        "system_prompt": "You are Michael, an action-oriented executor. You get things done efficiently - processing refunds, updating accounts, executing workflows. Be direct and effective.",
        "triggers": ["refund", "process", "update account", "execute"]
    },
    "steven": {
        "name": "Steven",
        "role": "Ticket Router",
        "description": "Routes, tags, and prioritizes incoming requests",
        "capabilities": ["instant_routing", "smart_tagging", "metadata_enrichment"],
        "system_prompt": "You are Steven, a routing specialist. You analyze incoming requests and route them to the right place with accurate tags and priority levels.",
        "triggers": ["route", "categorize", "prioritize", "triage"]
    },
    "joana": {
        "name": "Joana",
        "role": "Engagement Agent",
        "description": "Engages visitors, optimizes conversions, manages chatbots",
        "capabilities": ["chatbot_management", "conversion_optimization", "visitor_engagement"],
        "system_prompt": "You are Joana, an engagement specialist. You know how to engage visitors and guide them toward conversion. Be friendly and helpful.",
        "triggers": ["engage", "convert", "chat", "greet"]
    },
    "lily": {
        "name": "Lily",
        "role": "Insight Analyzer",
        "description": "Analyzes data for insights - process mining, sentiment, trends",
        "capabilities": ["process_mining", "topic_clustering", "sentiment_analysis"],
        "system_prompt": "You are Lily, a data analyst. You find patterns and insights in data that others miss. Be analytical and thorough.",
        "triggers": ["analyze", "insight", "sentiment", "pattern", "trend"]
    },
    "dan": {
        "name": "Dan",
        "role": "Knowledge Manager",
        "description": "Maintains documentation, syncs knowledge, ensures accuracy",
        "capabilities": ["auto_documentation", "knowledge_sync", "content_accuracy"],
        "system_prompt": "You are Dan, a knowledge manager. You keep documentation up to date and ensure information accuracy. Be meticulous and organized.",
        "triggers": ["document", "update docs", "knowledge", "help article"]
    },
    
    # Creative personas (extensions)
    "aria": {
        "name": "Aria",
        "role": "Creative Director",
        "description": "Designs visuals, generates images, creates brand assets",
        "capabilities": ["image_generation", "brand_design", "visual_identity"],
        "system_prompt": "You are Aria, a creative director. You create stunning visuals and maintain brand consistency. Be creative yet strategic.",
        "triggers": ["design", "create image", "visual", "logo", "brand"]
    },
    "max": {
        "name": "Max",
        "role": "Video Producer",
        "description": "Creates videos, animations, and motion content",
        "capabilities": ["video_generation", "animation", "editing"],
        "system_prompt": "You are Max, a video producer. You create engaging video content that captivates audiences. Be dynamic and creative.",
        "triggers": ["video", "animation", "motion", "commercial", "ad"]
    },
    "nova": {
        "name": "Nova",
        "role": "Research Specialist",
        "description": "Deep research, competitive analysis, market intelligence",
        "capabilities": ["web_research", "competitor_analysis", "market_research"],
        "system_prompt": "You are Nova, a research specialist. You dig deep to find valuable insights and competitive intelligence. Be thorough and insightful.",
        "triggers": ["research", "find", "competitor", "market", "analyze"]
    },
    "echo": {
        "name": "Echo",
        "role": "Content Writer",
        "description": "Creates compelling content - blogs, copy, social posts",
        "capabilities": ["copywriting", "blog_writing", "social_media"],
        "system_prompt": "You are Echo, a content writer. You craft compelling content that resonates with audiences. Be engaging and persuasive.",
        "triggers": ["write", "blog", "article", "copy", "content", "post"]
    }
}


# ============================================================================
# CONVERSATIONAL INTELLIGENCE
# ============================================================================

class PlatformIntelligence:
    """
    Central intelligence module that provides:
    - Enhanced intent detection
    - Workflow template matching
    - Model selection guidance
    - Tool recommendations
    - Agent persona matching
    """
    
    def __init__(self):
        self.intent_patterns = INTENT_PATTERN_DATABASE
        self.workflow_templates = WORKFLOW_TEMPLATES
        self.model_knowledge = MODEL_KNOWLEDGE
        self.creative_tools = CREATIVE_TOOL_MAPPING
        self.agent_personas = AGENT_PERSONAS
        
    def detect_intents(self, message: str) -> List[Tuple[EnhancedIntentCategory, float]]:
        """
        Detect all matching intents with confidence scores.
        Returns list of (category, confidence) tuples sorted by confidence.
        """
        message_lower = message.lower()
        intents = []
        
        for category, patterns in self.intent_patterns.items():
            max_confidence = 0.0
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    # Base confidence from pattern match
                    confidence = 0.75
                    
                    # Boost for more specific patterns
                    if len(pattern) > 30:
                        confidence += 0.1
                    
                    # Boost for exact keyword matches
                    keywords = re.findall(r'\w+', pattern)
                    keyword_matches = sum(1 for k in keywords if k in message_lower)
                    confidence += min(0.15, keyword_matches * 0.03)
                    
                    max_confidence = max(max_confidence, confidence)
            
            if max_confidence > 0:
                intents.append((category, min(1.0, max_confidence)))
        
        # Sort by confidence descending
        return sorted(intents, key=lambda x: x[1], reverse=True)
    
    def match_workflow_template(self, message: str) -> Optional[Dict]:
        """Find matching workflow template for the message."""
        message_lower = message.lower()
        
        for name, template in self.workflow_templates.items():
            # Check triggers
            trigger_match = any(t in message_lower for t in template.get("triggers", []))
            
            # Check exclusions
            excluded = any(e in message_lower for e in template.get("excludes", []))
            
            # Check requirements
            required = template.get("requires", [])
            has_required = not required or any(r in message_lower for r in required)
            
            if trigger_match and not excluded and has_required:
                return {"name": name, **template}
        
        return None
    
    def recommend_model(self, task_type: str, requirements: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Recommend best model for a task based on requirements."""
        requirements = requirements or {}
        
        models = self.model_knowledge.get(task_type, {})
        if not models:
            return None
        
        # Default priorities
        priority = requirements.get("priority", "balanced")  # fast, quality, cheap, balanced
        
        if priority == "fast":
            return max(models.items(), key=lambda x: x[1].get("speed", 0))[0]
        elif priority == "quality":
            return max(models.items(), key=lambda x: x[1].get("quality", 0))[0]
        elif priority == "cheap":
            cost_order = {"free": 4, "low": 3, "medium": 2, "high": 1, "very-high": 0}
            return max(models.items(), key=lambda x: cost_order.get(x[1].get("cost", "high"), 0))[0]
        else:
            # Balanced: weight quality and speed equally
            return max(models.items(), 
                      key=lambda x: x[1].get("quality", 0) * 0.5 + x[1].get("speed", 0) * 0.5)[0]
    
    def find_creative_tool(self, message: str) -> Optional[Dict]:
        """Find matching creative tool action."""
        message_lower = message.lower()
        
        for tool_name, tool_info in self.creative_tools.items():
            if any(kw in message_lower for kw in tool_info.get("keywords", [])):
                return {"name": tool_name, **tool_info}
        
        return None
    
    def match_agent_persona(self, message: str) -> Optional[Dict]:
        """Find the best matching agent persona for a task."""
        message_lower = message.lower()
        
        best_match = None
        best_score = 0
        
        for persona_id, persona in self.agent_personas.items():
            score = 0
            for trigger in persona.get("triggers", []):
                if trigger in message_lower:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = {"id": persona_id, **persona}
        
        return best_match if best_score > 0 else None
    
    def get_task_context(self, message: str) -> Dict[str, Any]:
        """
        Get comprehensive context for a task including:
        - Detected intents
        - Matched workflow
        - Recommended models
        - Suggested tools
        - Agent persona
        """
        intents = self.detect_intents(message)
        workflow = self.match_workflow_template(message)
        creative_tool = self.find_creative_tool(message)
        persona = self.match_agent_persona(message)
        
        # Determine primary task type for model recommendation
        primary_intent = intents[0] if intents else None
        model_category = None
        recommended_model = None
        
        if primary_intent:
            category = primary_intent[0]
            if category in [EnhancedIntentCategory.IMAGE_GENERATION, EnhancedIntentCategory.DESIGN_CREATION]:
                model_category = "image_generation"
            elif category in [EnhancedIntentCategory.VIDEO_GENERATION, EnhancedIntentCategory.VIDEO_EDITING]:
                model_category = "video_generation"
            elif category in [EnhancedIntentCategory.AUDIO_GENERATION]:
                model_category = "audio_generation"
            elif category in [EnhancedIntentCategory.IMAGE_EDITING, EnhancedIntentCategory.BACKGROUND_REMOVAL, EnhancedIntentCategory.UPSCALING]:
                model_category = "image_editing"
            
            if model_category:
                recommended_model = self.recommend_model(model_category)
        
        return {
            "intents": [(i[0].value, i[1]) for i in intents],
            "primary_intent": primary_intent[0].value if primary_intent else None,
            "confidence": primary_intent[1] if primary_intent else 0,
            "workflow": workflow,
            "creative_tool": creative_tool,
            "recommended_model": recommended_model,
            "model_category": model_category,
            "agent_persona": persona,
            "is_multi_step": workflow is not None or len(intents) > 1
        }
    
    def enhance_system_prompt(self, base_prompt: str) -> str:
        """Add platform intelligence to system prompt."""
        intelligence_section = """

## PLATFORM INTELLIGENCE (Enhanced Capabilities)

### Creative Operations (Canva/Firefly-style)
- **Background Removal**: "remove background", "make transparent", "cutout subject"
- **Magic Resize**: Auto-adapt designs for different social platforms
- **Magic Eraser**: Remove unwanted objects from images
- **Style Transfer**: Apply artistic styles to existing images
- **Generative Expand**: Extend image canvas with AI
- **Auto Enhance**: One-click photo improvements

### Workflow Automation (n8n/Zapier-style)
- **Trigger → Action**: "When X happens, do Y"
- **Multi-step Chains**: "First... then... finally..."
- **Data Sync**: Keep data synchronized between platforms
- **Scheduled Tasks**: "Every day at 9am..."
- **Parallel Execution**: Run independent tasks simultaneously

### Browser Intelligence (browser-use-style)
- **Stealth Browsing**: Navigate sites without detection
- **Data Extraction**: Pull structured data from any webpage
- **Form Automation**: Fill and submit forms automatically
- **Price Monitoring**: Track prices on e-commerce sites
- **Lead Generation**: Extract contacts from websites

### Support Operations (Quivr-style)
- **Draft Responses**: Create reply drafts matching user's tone
- **Ticket Routing**: Categorize and prioritize incoming requests
- **Knowledge Retrieval**: Find answers in documentation
- **Sentiment Analysis**: Understand customer emotions
- **Action Execution**: Process refunds, update accounts

### Model Selection Intelligence
When generating content, automatically select optimal models:
- Fast prototyping → flux-schnell (seconds, low cost)
- High quality → flux-pro (best quality, higher cost)
- Text rendering → ideogram (logos, typography)
- Videos → kling-v2.6 (cinematic), luma (creative)
- Audio/Music → elevenlabs (songs), minimax-speech (voice)

### Agent Personas Available
- **Kelly** (Draft Composer): Response writing, translation
- **Michael** (Action Executor): Refunds, updates, workflows
- **Steven** (Ticket Router): Categorization, prioritization
- **Lily** (Insight Analyzer): Data analysis, patterns
- **Aria** (Creative Director): Visual design, branding
- **Max** (Video Producer): Video creation, animation
- **Nova** (Research Specialist): Deep research, analysis
- **Echo** (Content Writer): Blogs, copy, social posts

"""
        return base_prompt + intelligence_section


# Singleton instance
_platform_intelligence = None

def get_platform_intelligence() -> PlatformIntelligence:
    """Get the singleton PlatformIntelligence instance."""
    global _platform_intelligence
    if _platform_intelligence is None:
        _platform_intelligence = PlatformIntelligence()
    return _platform_intelligence
