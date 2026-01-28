"""
Otto Universal - Intent Parser
==============================

Smart intent parsing that understands natural language requests
and extracts structured information for execution.

Inspired by the sophisticated intent parsing from ABP systems.
"""

import re
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class IntentCategory(Enum):
    """High-level intent categories."""
    GENERATION = "generation"          # Create images, videos, designs
    PRODUCT = "product"                # Product creation, management
    CONTENT = "content"                # Writing, social media
    RESEARCH = "research"              # Search, analysis
    AUTOMATION = "automation"          # Workflows, scheduling
    DATA = "data"                      # Analysis, processing
    CONVERSATION = "conversation"      # Chat, questions
    SETTINGS = "settings"              # Configuration
    FILES = "files"                    # File management
    UNKNOWN = "unknown"


@dataclass
class ParsedIntent:
    """Structured representation of parsed user intent."""
    raw_message: str
    category: IntentCategory
    action: str
    confidence: float
    entities: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    context_hints: List[str] = field(default_factory=list)
    suggested_tools: List[str] = field(default_factory=list)
    requires_confirmation: bool = False
    is_multi_step: bool = False
    sub_intents: List['ParsedIntent'] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_message": self.raw_message,
            "category": self.category.value,
            "action": self.action,
            "confidence": self.confidence,
            "entities": self.entities,
            "parameters": self.parameters,
            "context_hints": self.context_hints,
            "suggested_tools": self.suggested_tools,
            "requires_confirmation": self.requires_confirmation,
            "is_multi_step": self.is_multi_step,
            "sub_intents": [s.to_dict() for s in self.sub_intents]
        }


class IntentParser:
    """
    Intelligent intent parser that understands user requests.
    
    Uses a combination of:
    - Pattern matching for common requests
    - Entity extraction for parameters
    - AI-powered understanding for complex cases
    """
    
    # Pattern matchers for common intents
    INTENT_PATTERNS = {
        IntentCategory.GENERATION: [
            r"(?:create|generate|make|design|draw|produce)\s+(?:a|an|the)?\s*(?:image|picture|design|graphic|art|illustration|logo)",
            r"(?:create|generate|make)\s+(?:a|an)?\s*(?:video|animation|clip)",
            r"(?:generate|write)\s+(?:some)?\s*(?:music|audio|sound)",
        ],
        IntentCategory.PRODUCT: [
            r"(?:create|make|design|add)\s+(?:a|an)?\s*(?:product|t-?shirt|mug|hoodie|poster|sticker)",
            r"(?:upload|publish|list)\s+(?:to|on)\s*(?:printify|shopify|etsy)",
            r"(?:print|sell)\s+(?:this|the|a)\s*(?:design|product)",
        ],
        IntentCategory.CONTENT: [
            r"(?:write|create|generate)\s+(?:a|an|some)?\s*(?:post|caption|description|copy|blog|article)",
            r"(?:social\s*media|instagram|twitter|facebook|tiktok)\s+(?:post|content)",
            r"(?:email|newsletter)\s+(?:campaign|sequence|copy)",
        ],
        IntentCategory.RESEARCH: [
            r"(?:search|find|look\s*up|research)\s+(?:for)?\s*",
            r"(?:what|who|where|when|why|how)\s+",
            r"(?:analyze|compare|review)\s+",
        ],
        IntentCategory.AUTOMATION: [
            r"(?:automate|schedule|run)\s+(?:a|the)?\s*(?:workflow|task|campaign)",
            r"(?:set\s*up|configure)\s+(?:a|an)?\s*(?:automation|workflow|schedule)",
            r"every\s+(?:day|week|month|hour)",
        ],
        IntentCategory.DATA: [
            r"(?:analyze|process|transform|convert)\s+(?:the|this|my)?\s*(?:data|csv|json|file)",
            r"(?:create|make|generate)\s+(?:a|an)?\s*(?:chart|graph|report|dashboard)",
            r"(?:export|import)\s+(?:to|from)\s*",
        ],
        IntentCategory.FILES: [
            r"(?:save|store|upload|download)\s+(?:this|the|a)?\s*(?:file|image|video)",
            r"(?:show|list|find)\s+(?:my)?\s*files",
        ],
        IntentCategory.SETTINGS: [
            r"(?:change|update|set|configure)\s+(?:my|the)?\s*(?:settings|config|api\s*key)",
            r"(?:connect|link|integrate)\s+(?:to|with)?\s*",
        ],
    }
    
    # Entity extraction patterns
    ENTITY_PATTERNS = {
        "product_type": r"(?:t-?shirt|mug|hoodie|poster|sticker|canvas|tote\s*bag|phone\s*case)",
        "platform": r"(?:printify|shopify|etsy|amazon|instagram|twitter|facebook|tiktok|youtube)",
        "style": r"(?:minimalist|vintage|modern|retro|abstract|realistic|cartoon|anime|watercolor|geometric)",
        "color": r"(?:black|white|red|blue|green|yellow|purple|pink|orange|brown|gray|grey)",
        "quantity": r"(?:(\d+)\s*(?:designs?|images?|products?|posts?|pieces?))",
        "size": r"(?:small|medium|large|xl|xxl|\d+x\d+|\d+\s*(?:px|pixels?))",
        "topic": r"(?:about|regarding|on|for)\s+['\"]?([^'\"]+?)['\"]?(?:\s|$|,)",
    }
    
    # Tool suggestions by category
    CATEGORY_TOOLS = {
        IntentCategory.GENERATION: [
            "replicate_smart_generate", "generate_image", "flux_schnell", "flux_pro",
            "generate_video", "generate_music"
        ],
        IntentCategory.PRODUCT: [
            "printify_create_product", "printify_create_tshirt", "printify_create_mug",
            "printify_upload_image", "shopify_create_product", "printify_publish_product"
        ],
        IntentCategory.CONTENT: [
            "generate_social_media_posts", "write_content", "generate_product_description",
            "create_blog_post", "generate_email"
        ],
        IntentCategory.RESEARCH: [
            "search_web", "browse_url", "research_topic", "analyze_trends"
        ],
        IntentCategory.AUTOMATION: [
            "execute_workflow", "schedule_task", "run_campaign"
        ],
        IntentCategory.DATA: [
            "execute_python", "process_json", "convert_format", "analyze_data"
        ],
        IntentCategory.FILES: [
            "save_file", "save_image_from_url", "list_files", "get_file"
        ],
    }
    
    def __init__(self, anthropic_client: Optional[Anthropic] = None):
        self.anthropic = anthropic_client
    
    def parse(self, message: str, context: Optional[Dict[str, Any]] = None) -> ParsedIntent:
        """
        Parse a user message into structured intent.
        
        Args:
            message: Raw user message
            context: Optional context from conversation
            
        Returns:
            ParsedIntent with extracted information
        """
        message_lower = message.lower().strip()
        
        # 1. Pattern-based category detection
        category, pattern_confidence = self._detect_category(message_lower)
        
        # 2. Extract entities
        entities = self._extract_entities(message_lower)
        
        # 3. Determine action from message
        action = self._extract_action(message_lower, category)
        
        # 4. Check for multi-step indicators
        is_multi_step = self._is_multi_step(message_lower)
        
        # 5. Get suggested tools
        suggested_tools = self.CATEGORY_TOOLS.get(category, [])
        
        # 6. Build parameters from entities
        parameters = self._build_parameters(message, entities, category)
        
        # 7. Determine if confirmation needed (destructive or expensive actions)
        requires_confirmation = self._needs_confirmation(category, action)
        
        # 8. Extract context hints
        context_hints = self._extract_context_hints(message_lower, context)
        
        return ParsedIntent(
            raw_message=message,
            category=category,
            action=action,
            confidence=pattern_confidence,
            entities=entities,
            parameters=parameters,
            context_hints=context_hints,
            suggested_tools=suggested_tools,
            requires_confirmation=requires_confirmation,
            is_multi_step=is_multi_step
        )
    
    async def parse_with_ai(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        available_tools: Optional[List[Dict]] = None
    ) -> ParsedIntent:
        """
        Use AI for more sophisticated intent parsing.
        Falls back to pattern-based if AI unavailable.
        """
        # First do pattern-based parsing
        basic_intent = self.parse(message, context)
        
        # If confidence is high enough, return without AI
        if basic_intent.confidence >= 0.85 or not self.anthropic:
            return basic_intent
        
        # Use AI for enhancement
        try:
            tools_desc = ""
            if available_tools:
                tools_desc = "\n".join([
                    f"- {t['name']}: {t.get('description', '')[:80]}"
                    for t in available_tools[:30]
                ])
            
            prompt = f"""Analyze this user request and extract structured intent information.

User Message: "{message}"

Available Tools:
{tools_desc or "General assistant capabilities"}

Previous Analysis (may be incomplete):
- Category: {basic_intent.category.value}
- Action: {basic_intent.action}
- Entities found: {basic_intent.entities}

Return JSON with:
{{
    "category": "generation|product|content|research|automation|data|files|settings|conversation",
    "action": "specific action verb",
    "confidence": 0.0-1.0,
    "entities": {{"entity_name": "value"}},
    "parameters": {{"param_name": "value"}},
    "suggested_tools": ["tool1", "tool2"],
    "is_multi_step": true/false,
    "requires_confirmation": true/false
}}"""

            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse AI response
            import json
            text = response.content[0].text
            
            # Extract JSON
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                ai_result = json.loads(match.group())
                
                # Merge AI results with pattern-based
                return ParsedIntent(
                    raw_message=message,
                    category=IntentCategory(ai_result.get("category", basic_intent.category.value)),
                    action=ai_result.get("action", basic_intent.action),
                    confidence=ai_result.get("confidence", basic_intent.confidence),
                    entities={**basic_intent.entities, **ai_result.get("entities", {})},
                    parameters={**basic_intent.parameters, **ai_result.get("parameters", {})},
                    context_hints=basic_intent.context_hints,
                    suggested_tools=ai_result.get("suggested_tools", basic_intent.suggested_tools),
                    requires_confirmation=ai_result.get("requires_confirmation", basic_intent.requires_confirmation),
                    is_multi_step=ai_result.get("is_multi_step", basic_intent.is_multi_step)
                )
                
        except Exception as e:
            logger.warning(f"AI parsing failed, using pattern-based: {e}")
        
        return basic_intent
    
    def _detect_category(self, message: str) -> Tuple[IntentCategory, float]:
        """Detect intent category using pattern matching."""
        for category, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    return category, 0.8
        
        # Fallback to conversation
        return IntentCategory.CONVERSATION, 0.5
    
    def _extract_entities(self, message: str) -> Dict[str, Any]:
        """Extract named entities from message."""
        entities = {}
        
        for entity_type, pattern in self.ENTITY_PATTERNS.items():
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                # Use the captured group if available, otherwise the full match
                value = match.group(1) if match.lastindex else match.group(0)
                entities[entity_type] = value.strip()
        
        return entities
    
    def _extract_action(self, message: str, category: IntentCategory) -> str:
        """Extract the primary action verb."""
        action_verbs = [
            "create", "generate", "make", "design", "write", "build",
            "search", "find", "analyze", "research", "look up",
            "upload", "publish", "post", "share", "send",
            "save", "store", "download", "export", "import",
            "update", "change", "modify", "edit", "delete",
            "schedule", "automate", "run", "execute"
        ]
        
        message_lower = message.lower()
        for verb in action_verbs:
            if verb in message_lower:
                return verb
        
        # Default actions by category
        category_defaults = {
            IntentCategory.GENERATION: "generate",
            IntentCategory.PRODUCT: "create",
            IntentCategory.CONTENT: "write",
            IntentCategory.RESEARCH: "search",
            IntentCategory.DATA: "analyze",
            IntentCategory.FILES: "manage",
            IntentCategory.AUTOMATION: "execute",
        }
        
        return category_defaults.get(category, "process")
    
    def _is_multi_step(self, message: str) -> bool:
        """Detect if request requires multiple steps."""
        multi_step_indicators = [
            r"and\s+(?:then|also|after)",
            r"first.*then",
            r"complete\s+(?:workflow|campaign|process)",
            r"(?:full|entire|whole)\s+(?:campaign|workflow|pipeline)",
            r"end.?to.?end",
            r"multiple|several|batch",
        ]
        
        for pattern in multi_step_indicators:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        return False
    
    def _build_parameters(
        self,
        message: str,
        entities: Dict[str, Any],
        category: IntentCategory
    ) -> Dict[str, Any]:
        """Build tool parameters from extracted information."""
        params = {}
        
        # Map entities to common parameter names
        entity_to_param = {
            "product_type": "product_type",
            "platform": "platform",
            "style": "style",
            "color": "color",
            "quantity": "count",
            "topic": "topic",
        }
        
        for entity, param_name in entity_to_param.items():
            if entity in entities:
                params[param_name] = entities[entity]
        
        # Add the original message as a description/prompt
        if category == IntentCategory.GENERATION:
            params["prompt"] = message
        elif category == IntentCategory.CONTENT:
            params["topic"] = message
        
        return params
    
    def _needs_confirmation(self, category: IntentCategory, action: str) -> bool:
        """Determine if action requires user confirmation."""
        # Actions that could cost money or be destructive
        confirm_actions = {"publish", "delete", "send", "post", "purchase", "buy"}
        confirm_categories = {IntentCategory.PRODUCT, IntentCategory.AUTOMATION}
        
        return action in confirm_actions or category in confirm_categories
    
    def _extract_context_hints(
        self,
        message: str,
        context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Extract hints about what context might be relevant."""
        hints = []
        
        # References to previous conversation
        if re.search(r"(?:that|the|this|it|those|these)\s+(?:one|image|design|product)", message):
            hints.append("references_previous_output")
        
        # Time references
        if re.search(r"(?:today|tomorrow|yesterday|last|next|this)\s+(?:week|month|year)", message):
            hints.append("time_sensitive")
        
        # Quantity/batch indicators
        if re.search(r"(?:all|every|each|multiple|several|batch)", message):
            hints.append("batch_operation")
        
        return hints


# Convenience function for quick parsing
def parse_intent(message: str, context: Optional[Dict] = None) -> ParsedIntent:
    """Quick intent parsing without AI."""
    parser = IntentParser()
    return parser.parse(message, context)
