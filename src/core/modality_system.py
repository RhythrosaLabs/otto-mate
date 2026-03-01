"""
Modality-First System - Otto Universal
=======================================

Enforces MODALITY → MODEL selection instead of MODEL → MODALITY inference.

This module determines what TYPE of output/processing is needed first,
then selects the appropriate AI model for that modality.

Modalities:
- TEXT: Text generation, chat, reasoning
- IMAGE: Image generation, editing, analysis
- VIDEO: Video generation, editing, analysis  
- AUDIO: Audio generation, speech, music
- CODE: Code generation, analysis, execution
- VISION: Visual understanding, OCR, scene analysis
- MULTIMODAL: Combined modalities
- 3D: 3D rendering, modeling
- DATA: Data analysis, structured output

Key Principle: Determine WHAT is needed before selecting HOW to create it.

Enhanced Features:
- Smart model prioritization (local/remote first, Replicate last)
- Dynamic Replicate model discovery
- Intelligent retry with failure analysis
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from anthropic import Anthropic

logger = logging.getLogger(__name__)

# Import new systems
try:
    from .smart_model_prioritization import (
        get_prioritization_system, 
        ModelSource,
        SmartModelPrioritization
    )
    PRIORITIZATION_AVAILABLE = True
except ImportError:
    PRIORITIZATION_AVAILABLE = False
    logger.warning("Smart prioritization not available")

try:
    from .replicate_model_registry import (
        get_replicate_registry,
        ReplicateModality,
        ModelSearchCriteria
    )
    REPLICATE_REGISTRY_AVAILABLE = True
except ImportError:
    REPLICATE_REGISTRY_AVAILABLE = False
    logger.warning("Replicate registry not available")

try:
    from .intelligent_retry_system import get_retry_system
    RETRY_SYSTEM_AVAILABLE = True
except ImportError:
    RETRY_SYSTEM_AVAILABLE = False
    logger.warning("Intelligent retry not available")


class Modality(str, Enum):
    """Types of content modalities Otto can work with."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    CODE = "code"
    VISION = "vision"  # Understanding visual content
    MULTIMODAL = "multimodal"  # Multiple modalities
    THREE_D = "3d"
    DATA = "data"  # Structured data, analysis
    DOCUMENT = "document"  # PDFs, complex documents


class ModalityComplexity(str, Enum):
    """Complexity level of modality requirements."""
    SIMPLE = "simple"  # Single modality, straightforward
    MODERATE = "moderate"  # Single modality, complex requirements
    COMPLEX = "complex"  # Multiple modalities, dependencies
    ORCHESTRATED = "orchestrated"  # Requires workflow coordination


@dataclass
class ModalityRequirement:
    """A specific modality requirement extracted from user intent."""
    modality: Modality
    description: str
    priority: int = 1  # 1 = highest
    dependencies: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    quality_level: str = "standard"  # quick, standard, high, ultra
    
    def __repr__(self):
        return f"ModalityRequirement({self.modality.value}, priority={self.priority})"


@dataclass
class ModelCapability:
    """Defines what a model can do."""
    model_id: str
    display_name: str
    modalities: List[Modality]
    strengths: List[str]
    weaknesses: List[str]
    cost_tier: str  # free, low, medium, high
    speed_tier: str  # fast, medium, slow
    quality_tier: str  # good, great, excellent
    max_tokens: int
    supports_streaming: bool = True
    supports_tools: bool = True
    
    def can_handle(self, modality: Modality) -> bool:
        """Check if this model can handle the given modality."""
        return modality in self.modalities


# ============================================================================
# Model Capability Definitions
# ============================================================================

MODEL_CAPABILITIES: Dict[str, ModelCapability] = {
    # Text models
    "claude-sonnet-4": ModelCapability(
        model_id="claude-sonnet-4-20250514",
        display_name="Claude Sonnet 4",
        modalities=[Modality.TEXT, Modality.CODE, Modality.DATA, Modality.VISION],
        strengths=["reasoning", "code", "analysis", "extended thinking", "vision"],
        weaknesses=["cost"],
        cost_tier="high",
        speed_tier="medium",
        quality_tier="excellent",
        max_tokens=8192,
        supports_streaming=True,
        supports_tools=True
    ),
    
    "claude-opus-4": ModelCapability(
        model_id="claude-opus-4-20250514",
        display_name="Claude Opus 4",
        modalities=[Modality.TEXT, Modality.CODE, Modality.DATA, Modality.VISION],
        strengths=["complex reasoning", "creative writing", "deep analysis"],
        weaknesses=["cost", "speed"],
        cost_tier="high",
        speed_tier="slow",
        quality_tier="excellent",
        max_tokens=8192,
        supports_streaming=True,
        supports_tools=True
    ),
    
    "claude-haiku": ModelCapability(
        model_id="claude-3-haiku-20240307",
        display_name="Claude Haiku",
        modalities=[Modality.TEXT, Modality.CODE],
        strengths=["speed", "cost-effective", "simple tasks"],
        weaknesses=["complex reasoning", "creativity"],
        cost_tier="low",
        speed_tier="fast",
        quality_tier="good",
        max_tokens=4096,
        supports_streaming=True,
        supports_tools=True
    ),
    
    "gpt-4o": ModelCapability(
        model_id="gpt-4o",
        display_name="GPT-4o",
        modalities=[Modality.TEXT, Modality.CODE, Modality.VISION, Modality.AUDIO],
        strengths=["multimodal", "vision", "audio", "fast"],
        weaknesses=["cost"],
        cost_tier="high",
        speed_tier="fast",
        quality_tier="excellent",
        max_tokens=4096,
        supports_streaming=True,
        supports_tools=True
    ),
    
    "gpt-4-turbo": ModelCapability(
        model_id="gpt-4-turbo-preview",
        display_name="GPT-4 Turbo",
        modalities=[Modality.TEXT, Modality.CODE, Modality.VISION],
        strengths=["reasoning", "large context", "vision"],
        weaknesses=["cost"],
        cost_tier="high",
        speed_tier="medium",
        quality_tier="excellent",
        max_tokens=8192,
        supports_streaming=True,
        supports_tools=True
    ),
    
    # Image generation models
    "flux-pro": ModelCapability(
        model_id="black-forest-labs/flux-1.1-pro",
        display_name="FLUX Pro",
        modalities=[Modality.IMAGE],
        strengths=["photorealism", "quality", "prompt following"],
        weaknesses=["cost", "speed"],
        cost_tier="high",
        speed_tier="slow",
        quality_tier="excellent",
        max_tokens=0,
        supports_streaming=False,
        supports_tools=False
    ),
    
    "flux-dev": ModelCapability(
        model_id="black-forest-labs/flux-dev",
        display_name="FLUX Dev",
        modalities=[Modality.IMAGE],
        strengths=["quality", "flexibility", "balance"],
        weaknesses=["speed"],
        cost_tier="medium",
        speed_tier="medium",
        quality_tier="great",
        max_tokens=0,
        supports_streaming=False,
        supports_tools=False
    ),
    
    "dall-e-3": ModelCapability(
        model_id="dall-e-3",
        display_name="DALL-E 3",
        modalities=[Modality.IMAGE],
        strengths=["ease of use", "safety", "consistency"],
        weaknesses=["flexibility", "cost"],
        cost_tier="high",
        speed_tier="medium",
        quality_tier="great",
        max_tokens=0,
        supports_streaming=False,
        supports_tools=False
    ),
    
    "stable-diffusion-xl": ModelCapability(
        model_id="stability-ai/sdxl",
        display_name="Stable Diffusion XL",
        modalities=[Modality.IMAGE],
        strengths=["cost-effective", "flexibility", "open source"],
        weaknesses=["quality vs FLUX"],
        cost_tier="low",
        speed_tier="fast",
        quality_tier="good",
        max_tokens=0,
        supports_streaming=False,
        supports_tools=False
    ),
    
    # Video models
    "runway-gen3": ModelCapability(
        model_id="runway/gen3",
        display_name="Runway Gen-3",
        modalities=[Modality.VIDEO],
        strengths=["quality", "motion", "realism"],
        weaknesses=["cost", "speed"],
        cost_tier="high",
        speed_tier="slow",
        quality_tier="excellent",
        max_tokens=0,
        supports_streaming=False,
        supports_tools=False
    ),
    
    "luma-dream-machine": ModelCapability(
        model_id="lumalabs/dream-machine",
        display_name="Luma Dream Machine",
        modalities=[Modality.VIDEO],
        strengths=["quality", "camera control"],
        weaknesses=["cost"],
        cost_tier="high",
        speed_tier="slow",
        quality_tier="excellent",
        max_tokens=0,
        supports_streaming=False,
        supports_tools=False
    ),
    
    # Audio models
    "elevenlabs": ModelCapability(
        model_id="elevenlabs/tts",
        display_name="ElevenLabs TTS",
        modalities=[Modality.AUDIO],
        strengths=["voice quality", "emotions", "cloning"],
        weaknesses=["cost"],
        cost_tier="medium",
        speed_tier="fast",
        quality_tier="excellent",
        max_tokens=0,
        supports_streaming=True,
        supports_tools=False
    ),
    
    "whisper": ModelCapability(
        model_id="openai/whisper",
        display_name="Whisper",
        modalities=[Modality.AUDIO],
        strengths=["transcription", "multilingual", "accuracy"],
        weaknesses=["generation"],
        cost_tier="low",
        speed_tier="fast",
        quality_tier="excellent",
        max_tokens=0,
        supports_streaming=False,
        supports_tools=False
    ),
    
    # 3D models
    "meshy": ModelCapability(
        model_id="meshy/3d-generator",
        display_name="Meshy 3D",
        modalities=[Modality.THREE_D],
        strengths=["text-to-3d", "quality", "ease"],
        weaknesses=["cost", "speed"],
        cost_tier="high",
        speed_tier="slow",
        quality_tier="great",
        max_tokens=0,
        supports_streaming=False,
        supports_tools=False
    ),
}


# ============================================================================
# Modality Detection
# ============================================================================

class ModalityDetector:
    """
    Detects required modalities from user intent.
    
    Uses strict prompt engineering to extract WHAT is needed
    before determining HOW to create it.
    """
    
    def __init__(self, anthropic_client: Anthropic):
        self.anthropic = anthropic_client
        
        # Keyword patterns for quick detection
        self.modality_keywords = {
            Modality.IMAGE: [
                "image", "picture", "photo", "graphic", "illustration", 
                "logo", "icon", "mockup", "design", "visual", "artwork"
            ],
            Modality.VIDEO: [
                "video", "animation", "clip", "movie", "commercial", 
                "ad video", "promo video", "motion", "footage"
            ],
            Modality.AUDIO: [
                "audio", "sound", "music", "voice", "song", "speech",
                "podcast", "voiceover", "narration", "tts"
            ],
            Modality.CODE: [
                "code", "program", "script", "function", "api", "debug",
                "software", "algorithm", "implement", "develop"
            ],
            Modality.VISION: [
                "analyze image", "what's in", "describe image", "ocr",
                "read text from", "understand image", "identify"
            ],
            Modality.THREE_D: [
                "3d", "three dimensional", "3d model", "render", "mesh",
                "obj file", "stl", "3d print"
            ],
            Modality.DATA: [
                "analyze data", "chart", "graph", "statistics", "csv",
                "spreadsheet", "calculate", "metrics", "report"
            ],
            Modality.DOCUMENT: [
                "pdf", "document", "report", "contract", "form", 
                "template", "presentation", "slides"
            ],
        }
    
    async def detect_modalities(
        self, 
        user_request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[ModalityRequirement]:
        """
        Detect all required modalities from user request.
        
        Returns list of modality requirements in priority order.
        """
        logger.info(f"Detecting modalities for: {user_request[:100]}...")
        
        # Quick keyword-based detection
        quick_modalities = self._quick_detect(user_request)
        
        # AI-powered deep analysis for complex requests
        if len(quick_modalities) == 0 or self._is_complex_request(user_request):
            ai_modalities = await self._ai_detect(user_request, context)
            # Merge and deduplicate
            all_modalities = self._merge_modalities(quick_modalities, ai_modalities)
        else:
            all_modalities = quick_modalities
        
        logger.info(f"Detected modalities: {[m.modality.value for m in all_modalities]}")
        return all_modalities
    
    def _quick_detect(self, text: str) -> List[ModalityRequirement]:
        """Fast keyword-based modality detection."""
        text_lower = text.lower()
        detected = []
        
        for modality, keywords in self.modality_keywords.items():
            if any(kw in text_lower for kw in keywords):
                # Extract priority based on position (earlier = higher priority)
                first_match = min(
                    (text_lower.find(kw) for kw in keywords if kw in text_lower),
                    default=1000
                )
                priority = 1 if first_match < 50 else 2
                
                detected.append(ModalityRequirement(
                    modality=modality,
                    description=f"{modality.value} generation/processing",
                    priority=priority
                ))
        
        # Default to TEXT if nothing detected
        if not detected:
            detected.append(ModalityRequirement(
                modality=Modality.TEXT,
                description="Text generation and reasoning",
                priority=1
            ))
        
        return sorted(detected, key=lambda x: x.priority)
    
    def _is_complex_request(self, text: str) -> bool:
        """Determine if request requires deep AI analysis."""
        complexity_indicators = [
            "and then", "after that", "workflow", "campaign",
            "end to end", "complete solution", "multiple", "various"
        ]
        return any(ind in text.lower() for ind in complexity_indicators)
    
    async def _ai_detect(
        self, 
        user_request: str, 
        context: Optional[Dict[str, Any]]
    ) -> List[ModalityRequirement]:
        """Use AI to detect modalities with deep understanding."""
        
        prompt = f"""Analyze this user request and identify ALL required content modalities.

User Request: {user_request}

Available Modalities:
- TEXT: Text generation, writing, reasoning, chat
- IMAGE: Image generation, editing, design, graphics
- VIDEO: Video creation, editing, animation
- AUDIO: Audio generation, music, speech, voiceover
- CODE: Code generation, programming, development
- VISION: Visual understanding, image analysis, OCR
- MULTIMODAL: Tasks requiring multiple modalities together
- 3D: 3D modeling, rendering, printing
- DATA: Data analysis, charts, structured output
- DOCUMENT: PDF generation, documents, reports

For EACH modality needed, provide:
1. Modality type
2. Brief description of what's needed
3. Priority (1=primary, 2=secondary, 3=optional)
4. Quality level (quick/standard/high/ultra)

Return JSON array:
[
  {{
    "modality": "IMAGE",
    "description": "Product mockup design",
    "priority": 1,
    "quality_level": "high"
  }},
  ...
]

Important: Return ONLY the JSON array, no other text."""

        try:
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            import json
            result_text = response.content[0].text.strip()
            
            # Extract JSON if wrapped in markdown
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            modalities_data = json.loads(result_text)
            
            requirements = []
            for item in modalities_data:
                try:
                    requirements.append(ModalityRequirement(
                        modality=Modality(item["modality"].lower()),
                        description=item["description"],
                        priority=item.get("priority", 1),
                        quality_level=item.get("quality_level", "standard")
                    ))
                except (KeyError, ValueError) as e:
                    logger.warning(f"Skipping invalid modality item: {e}")
                    continue
            
            return sorted(requirements, key=lambda x: x.priority)
            
        except Exception as e:
            logger.error(f"AI modality detection failed: {e}")
            return []
    
    def _merge_modalities(
        self, 
        quick: List[ModalityRequirement],
        ai: List[ModalityRequirement]
    ) -> List[ModalityRequirement]:
        """Merge quick and AI detections, preferring AI results."""
        merged = {m.modality: m for m in quick}
        for m in ai:
            merged[m.modality] = m  # AI overrides quick
        return sorted(merged.values(), key=lambda x: x.priority)


# ============================================================================
# Modality to Model Mapper
# ============================================================================

class ModalityToModelMapper:
    """
    Maps modality requirements to appropriate AI models.
    
    This enforces MODALITY → MODEL selection with smart prioritization:
    1. Local/Remote models (if installed)
    2. Replicate models (only if explicitly requested or nothing else available)
    
    Enhanced with:
    - Smart model prioritization
    - Dynamic Replicate discovery
    - Intelligent retry support
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.model_capabilities = MODEL_CAPABILITIES
        
        # Initialize smart systems
        self.prioritization = get_prioritization_system() if PRIORITIZATION_AVAILABLE else None
        self.replicate_registry = get_replicate_registry() if REPLICATE_REGISTRY_AVAILABLE else None
        
        if self.prioritization:
            logger.info("✓ Smart model prioritization enabled")
        if self.replicate_registry:
            logger.info("✓ Dynamic Replicate model discovery enabled")
    
    def select_model(
        self, 
        modality: Modality, 
        quality_level: str = "standard",
        prefer_speed: bool = False,
        prefer_cost: bool = False,
        explicit_model: Optional[str] = None,
        user_input: Optional[str] = None
    ) -> str:
        """
        Select the best model for a given modality and constraints.
        
        PRIORITY RULES:
        1. If remote/local models installed → USE THEM
        2. If user explicitly requests Replicate → USE REPLICATE
        3. If no remote/local available → USE REPLICATE as fallback
        
        Args:
            modality: Required modality
            quality_level: Desired quality (quick/standard/high/ultra)
            prefer_speed: Prioritize speed over quality
            prefer_cost: Prioritize cost over quality
            explicit_model: User explicitly requested this model
            user_input: Original user input (to check for "replicate" mention)
            
        Returns:
            Model ID to use
        """
        # Use smart prioritization if available
        if self.prioritization and PRIORITIZATION_AVAILABLE:
            # Check if user explicitly mentioned Replicate
            explicit_replicate = False
            if user_input and self.prioritization.is_replicate_explicit(user_input):
                explicit_replicate = True
                logger.info("User explicitly requested Replicate")
            
            # Get model selection from prioritization system
            selection = self.prioritization.select_model(
                modality=modality.value,
                capabilities=[],
                explicit_model=explicit_model,
                explicit_source=ModelSource.REPLICATE if explicit_replicate else None,
                prefer_speed=prefer_speed,
                prefer_cost=prefer_cost,
                quality_level=quality_level
            )
            
            if selection.replicate_avoided:
                logger.info(f"✓ Using {selection.model.source.value} model: {selection.model.name}")
            else:
                logger.info(f"⚠️ Using Replicate as fallback")
            
            # If it's a Replicate model, try to find the best one dynamically
            if selection.model.source == ModelSource.REPLICATE and self.replicate_registry:
                return self._select_replicate_model(modality, quality_level, prefer_speed, prefer_cost)
            
            return selection.model.name
        
        # Fallback to original logic if prioritization not available
        logger.info("Smart prioritization not available, using fallback logic")
        return self._select_model_fallback(modality, quality_level, prefer_speed, prefer_cost)
    
    def _select_replicate_model(
        self,
        modality: Modality,
        quality_level: str,
        prefer_speed: bool,
        prefer_cost: bool
    ) -> str:
        """
        Select a Replicate model dynamically.
        
        This discovers what's available on Replicate in real-time.
        """
        if not self.replicate_registry or not REPLICATE_REGISTRY_AVAILABLE:
            logger.warning("Replicate registry not available")
            return self._select_model_fallback(modality, quality_level, prefer_speed, prefer_cost)
        
        # Map to Replicate modality
        modality_map = {
            Modality.TEXT: ReplicateModality.TEXT,
            Modality.IMAGE: ReplicateModality.IMAGE,
            Modality.VIDEO: ReplicateModality.VIDEO,
            Modality.AUDIO: ReplicateModality.AUDIO,
            Modality.CODE: ReplicateModality.CODE,
            Modality.THREE_D: ReplicateModality.THREE_D,
            Modality.MULTIMODAL: ReplicateModality.MULTIMODAL,
        }
        
        replicate_modality = modality_map.get(modality, ReplicateModality.TEXT)
        
        try:
            # Discover best model asynchronously (run sync for now)
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            best_model = loop.run_until_complete(
                self.replicate_registry.get_best_model_for_task(
                    modality=replicate_modality,
                    capabilities=None,
                    prefer_speed=prefer_speed,
                    prefer_cost=prefer_cost
                )
            )
            
            if best_model:
                logger.info(f"✓ Discovered Replicate model: {best_model.full_name}")
                return best_model.full_name
            else:
                logger.warning("No Replicate models found, using fallback")
                return self._select_model_fallback(modality, quality_level, prefer_speed, prefer_cost)
                
        except Exception as e:
            logger.error(f"Error discovering Replicate model: {e}")
            return self._select_model_fallback(modality, quality_level, prefer_speed, prefer_cost)
    
    def _select_model_fallback(
        self,
        modality: Modality,
        quality_level: str,
        prefer_speed: bool,
        prefer_cost: bool
    ) -> str:
        """Original model selection logic as fallback."""
        # Filter models that can handle this modality
        capable_models = [
            (model_id, cap) for model_id, cap in self.model_capabilities.items()
            if cap.can_handle(modality)
        ]
        
        if not capable_models:
            logger.warning(f"No models found for modality {modality}, defaulting to TEXT")
            return "claude-sonnet-4-20250514"
        
        # Score models based on preferences
        scored_models = []
        for model_id, cap in capable_models:
            score = 0
            
            # Quality scoring
            quality_scores = {"good": 3, "great": 4, "excellent": 5}
            score += quality_scores.get(cap.quality_tier, 3) * 2
            
            # Speed preference
            if prefer_speed:
                speed_scores = {"fast": 5, "medium": 3, "slow": 1}
                score += speed_scores.get(cap.speed_tier, 3) * 3
            
            # Cost preference  
            if prefer_cost:
                cost_scores = {"free": 5, "low": 4, "medium": 3, "high": 1}
                score += cost_scores.get(cap.cost_tier, 3) * 2
            
            # Quality level adjustment
            if quality_level == "ultra" and cap.quality_tier == "excellent":
                score += 5
            elif quality_level == "quick" and cap.speed_tier == "fast":
                score += 5
            
            scored_models.append((model_id, cap, score))
        
        # Select highest scoring model
        best_model = max(scored_models, key=lambda x: x[2])
        
        logger.info(f"Selected {best_model[1].display_name} for {modality.value} "
                   f"(score: {best_model[2]})")
        
        return best_model[0]
    
    def select_models_for_requirements(
        self,
        requirements: List[ModalityRequirement],
        context: Optional[Dict[str, Any]] = None,
        user_input: Optional[str] = None
    ) -> Dict[Modality, str]:
        """
        Select appropriate models for all modality requirements.
        
        Returns mapping of modality to model ID.
        """
        context = context or {}
        prefer_speed = context.get("prefer_speed", False)
        prefer_cost = context.get("prefer_cost", False)
        explicit_model = context.get("explicit_model")
        
        model_mapping = {}
        for req in requirements:
            model_id = self.select_model(
                modality=req.modality,
                quality_level=req.quality_level,
                prefer_speed=prefer_speed,
                prefer_cost=prefer_cost,
                explicit_model=explicit_model,
                user_input=user_input
            )
            model_mapping[req.modality] = model_id
        
        return model_mapping


# ============================================================================
# Singleton Access
# ============================================================================

_detector: Optional[ModalityDetector] = None
_mapper: Optional[ModalityToModelMapper] = None


def get_modality_detector(anthropic_client: Anthropic) -> ModalityDetector:
    """Get or create the modality detector singleton."""
    global _detector
    if _detector is None:
        _detector = ModalityDetector(anthropic_client)
    return _detector


def get_modality_mapper(config: Optional[Dict[str, Any]] = None) -> ModalityToModelMapper:
    """Get or create the modality mapper singleton."""
    global _mapper
    if _mapper is None:
        _mapper = ModalityToModelMapper(config)
    return _mapper
