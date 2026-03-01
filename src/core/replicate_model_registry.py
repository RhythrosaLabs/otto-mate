"""
Dynamic Replicate Model Registry - Otto Universal
==================================================

Discovers and manages ALL Replicate models dynamically.
No hardcoded model list - discovers what's available in real-time.

Key Features:
- Dynamic model discovery
- Capability detection
- Automatic model categorization
- Version management
- Cost tracking
- Performance metrics
"""

import logging
import asyncio
import os
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)

try:
    import replicate
    REPLICATE_AVAILABLE = True
except ImportError:
    REPLICATE_AVAILABLE = False
    logger.warning("Replicate not installed - pip install replicate")


class ReplicateModality(str, Enum):
    """Modalities supported by Replicate models."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    MULTIMODAL = "multimodal"
    CODE = "code"
    THREE_D = "3d"
    EMBEDDING = "embedding"
    UNKNOWN = "unknown"


@dataclass
class ReplicateModel:
    """Information about a Replicate model."""
    owner: str
    name: str
    version: Optional[str] = None
    full_name: str = ""  # owner/name:version
    modality: ReplicateModality = ReplicateModality.UNKNOWN
    capabilities: List[str] = field(default_factory=list)
    description: str = ""
    tags: List[str] = field(default_factory=list)
    inputs_schema: Dict[str, Any] = field(default_factory=dict)
    outputs_schema: Dict[str, Any] = field(default_factory=dict)
    cost_per_run: Optional[float] = None
    avg_runtime: Optional[float] = None
    runs_count: int = 0
    popularity_score: float = 0.0
    last_updated: Optional[datetime] = None
    supports_streaming: bool = False
    
    def __post_init__(self):
        if not self.full_name:
            self.full_name = f"{self.owner}/{self.name}"
            if self.version:
                self.full_name += f":{self.version}"


@dataclass
class ModelSearchCriteria:
    """Criteria for searching models."""
    modality: Optional[ReplicateModality] = None
    capabilities: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    max_cost: Optional[float] = None
    max_runtime: Optional[float] = None
    min_popularity: float = 0.0
    keywords: List[str] = field(default_factory=list)
    owner: Optional[str] = None


class ReplicateModelRegistry:
    """
    Dynamic registry for ALL Replicate models.
    
    Features:
    - Discovers models on-demand
    - Caches model information
    - Automatic capability detection
    - Smart search and filtering
    - Version management
    """
    
    def __init__(
        self,
        api_token: Optional[str] = None,
        cache_duration: int = 3600  # Cache for 1 hour
    ):
        self.api_token = api_token or os.getenv("REPLICATE_API_TOKEN")
        self.cache_duration = cache_duration
        
        # Model caches
        self.models_cache: Dict[str, ReplicateModel] = {}
        self.cache_timestamp: Optional[datetime] = None
        
        # Popular/featured models cache
        self.featured_models: Dict[ReplicateModality, List[ReplicateModel]] = {}
        
        # Modality detection patterns
        self.modality_patterns = {
            ReplicateModality.TEXT: [
                "llm", "language", "text", "chat", "gpt", "llama", 
                "mistral", "gemma", "falcon", "mpt", "claude"
            ],
            ReplicateModality.IMAGE: [
                "image", "photo", "picture", "diffusion", "stable-diffusion",
                "sdxl", "midjourney", "dalle", "flux", "img", "pic"
            ],
            ReplicateModality.VIDEO: [
                "video", "animation", "movie", "clip", "motion", "gif",
                "animatediff", "gen-3", "runway"
            ],
            ReplicateModality.AUDIO: [
                "audio", "music", "sound", "voice", "tts", "speech",
                "musicgen", "audiocraft", "whisper", "eleven"
            ],
            ReplicateModality.MULTIMODAL: [
                "multimodal", "vision", "vlm", "gpt-4v", "llava",
                "cogvlm", "fuyu", "blip"
            ],
            ReplicateModality.CODE: [
                "code", "programming", "codegen", "coder", "starcoder"
            ],
            ReplicateModality.THREE_D: [
                "3d", "mesh", "shape", "model", "obj", "point-cloud"
            ],
            ReplicateModality.EMBEDDING: [
                "embedding", "encoder", "feature", "vector"
            ]
        }
        
        # Capability detection patterns
        self.capability_patterns = {
            "generation": ["generate", "create", "synthesis", "produce"],
            "editing": ["edit", "modify", "transform", "alter", "inpaint"],
            "upscaling": ["upscale", "super-resolution", "enhance", "improve"],
            "style_transfer": ["style", "transfer", "artistic"],
            "segmentation": ["segment", "mask", "detect", "localize"],
            "classification": ["classify", "categorize", "predict", "recognize"],
            "translation": ["translate", "convert", "transform"],
            "summarization": ["summarize", "condense", "brief"],
            "qa": ["question", "answer", "qa"],
            "chat": ["chat", "conversation", "dialogue"],
            "analysis": ["analyze", "understand", "interpret"],
        }
        
    async def discover_models(
        self,
        criteria: Optional[ModelSearchCriteria] = None,
        force_refresh: bool = False
    ) -> List[ReplicateModel]:
        """
        Discover Replicate models matching criteria.
        
        Args:
            criteria: Search criteria
            force_refresh: Force cache refresh
            
        Returns:
            List of matching models
        """
        if not REPLICATE_AVAILABLE:
            logger.error("Replicate not available")
            return []
        
        if not self.api_token:
            logger.error("REPLICATE_API_TOKEN not set")
            return []
        
        # Check cache
        if not force_refresh and self._is_cache_valid():
            logger.info("Using cached model list")
            return self._filter_models(list(self.models_cache.values()), criteria)
        
        logger.info("Discovering Replicate models...")
        
        try:
            # Set API token
            os.environ["REPLICATE_API_TOKEN"] = self.api_token
            
            # Get popular models across different modalities
            discovered_models = []
            
            # Method 1: Search by modality keywords
            if criteria and criteria.modality:
                modality_models = await self._search_by_modality(criteria.modality)
                discovered_models.extend(modality_models)
            else:
                # Search all modalities
                for modality in ReplicateModality:
                    if modality == ReplicateModality.UNKNOWN:
                        continue
                    modality_models = await self._search_by_modality(modality)
                    discovered_models.extend(modality_models)
            
            # Method 2: Get featured/popular models
            featured = await self._get_featured_models()
            discovered_models.extend(featured)
            
            # Deduplicate by full_name
            unique_models = {m.full_name: m for m in discovered_models}
            
            # Update cache
            self.models_cache = unique_models
            self.cache_timestamp = datetime.now()
            
            logger.info(f"Discovered {len(unique_models)} unique models")
            
            # Filter and return
            result = self._filter_models(list(unique_models.values()), criteria)
            logger.info(f"Found {len(result)} models matching criteria")
            
            return result
            
        except Exception as e:
            logger.error(f"Error discovering models: {e}")
            # Return cached models if available
            if self.models_cache:
                logger.info("Returning cached models after error")
                return self._filter_models(list(self.models_cache.values()), criteria)
            return []
    
    async def _search_by_modality(
        self,
        modality: ReplicateModality
    ) -> List[ReplicateModel]:
        """Search for models by modality."""
        models = []
        keywords = self.modality_patterns.get(modality, [])
        
        for keyword in keywords[:5]:  # Limit searches per modality
            try:
                # Search using Replicate API
                # Note: Replicate's search is limited, so we use collections
                collection_models = await self._search_collection(keyword)
                models.extend(collection_models)
                
                # Small delay to avoid rate limits
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.warning(f"Error searching for '{keyword}': {e}")
                continue
        
        return models
    
    async def _search_collection(self, keyword: str) -> List[ReplicateModel]:
        """Search for models in a collection."""
        try:
            # Try to find collection by keyword
            collections_to_try = [
                keyword,
                f"{keyword}-models",
                f"text-to-{keyword}",
                f"{keyword}-generation"
            ]
            
            models = []
            
            for collection_name in collections_to_try:
                try:
                    # Get collection
                    collection = replicate.collections.get(collection_name)
                    
                    # Get models from collection
                    for model_ref in collection.models[:10]:  # Limit per collection
                        model = await self._get_model_info(model_ref)
                        if model:
                            models.append(model)
                    
                    if models:
                        break  # Found models in this collection
                        
                except Exception:
                    continue
            
            return models
            
        except Exception as e:
            logger.debug(f"Could not search collection '{keyword}': {e}")
            return []
    
    async def _get_featured_models(self) -> List[ReplicateModel]:
        """Get featured/popular models."""
        featured = []
        
        # Hardcoded list of known popular models as fallback
        popular_models = [
            # Text
            "meta/llama-2-70b-chat",
            "mistralai/mixtral-8x7b-instruct-v0.1",
            "meta/llama-2-13b-chat",
            
            # Image
            "stability-ai/sdxl",
            "black-forest-labs/flux-1-dev",
            "black-forest-labs/flux-1-schnell",
            "bytedance/sdxl-lightning-4step",
            "stability-ai/stable-diffusion",
            
            # Video
            "stability-ai/stable-video-diffusion",
            "ali-vilab/i2vgen-xl",
            
            # Audio
            "meta/musicgen",
            "openai/whisper",
            
            # Multimodal
            "yorickvp/llava-13b",
            "salesforce/blip",
        ]
        
        for model_name in popular_models:
            try:
                model = await self._get_model_info(model_name)
                if model:
                    featured.append(model)
            except Exception as e:
                logger.debug(f"Could not get featured model {model_name}: {e}")
                continue
        
        return featured
    
    async def _get_model_info(
        self,
        model_ref: str
    ) -> Optional[ReplicateModel]:
        """Get detailed information about a model."""
        try:
            # Parse model reference
            parts = model_ref.split("/")
            if len(parts) != 2:
                return None
            
            owner, name_version = parts
            name = name_version.split(":")[0]
            version = name_version.split(":")[1] if ":" in name_version else None
            
            # Get model from Replicate
            model = replicate.models.get(f"{owner}/{name}")
            
            # Get latest version if not specified
            if not version and hasattr(model, 'latest_version'):
                version_obj = model.latest_version
            else:
                version_obj = None
            
            # Detect modality from description and name
            model_text = f"{name} {model.description or ''}".lower()
            modality = self._detect_modality(model_text)
            
            # Detect capabilities
            capabilities = self._detect_capabilities(model_text)
            
            # Extract schema if available
            inputs_schema = {}
            outputs_schema = {}
            
            if version_obj and hasattr(version_obj, 'openapi_schema'):
                schema = version_obj.openapi_schema
                inputs_schema = schema.get("components", {}).get("schemas", {}).get("Input", {})
                outputs_schema = schema.get("components", {}).get("schemas", {}).get("Output", {})
            
            return ReplicateModel(
                owner=owner,
                name=name,
                version=version,
                modality=modality,
                capabilities=capabilities,
                description=model.description or "",
                tags=[],  # Replicate doesn't provide tags directly
                inputs_schema=inputs_schema,
                outputs_schema=outputs_schema,
                last_updated=datetime.now(),
                runs_count=getattr(model, 'run_count', 0),
                popularity_score=self._calculate_popularity(model)
            )
            
        except Exception as e:
            logger.debug(f"Error getting model info for {model_ref}: {e}")
            return None
    
    def _detect_modality(self, text: str) -> ReplicateModality:
        """Detect modality from model name/description."""
        text = text.lower()
        
        # Count matches for each modality
        scores = {}
        for modality, patterns in self.modality_patterns.items():
            score = sum(1 for pattern in patterns if pattern in text)
            if score > 0:
                scores[modality] = score
        
        if not scores:
            return ReplicateModality.UNKNOWN
        
        # Return modality with highest score
        return max(scores.items(), key=lambda x: x[1])[0]
    
    def _detect_capabilities(self, text: str) -> List[str]:
        """Detect capabilities from model name/description."""
        text = text.lower()
        capabilities = []
        
        for capability, patterns in self.capability_patterns.items():
            if any(pattern in text for pattern in patterns):
                capabilities.append(capability)
        
        return capabilities
    
    def _calculate_popularity(self, model: Any) -> float:
        """Calculate popularity score for a model."""
        score = 0.0
        
        # Run count
        if hasattr(model, 'run_count'):
            score += min(model.run_count / 100000, 1.0) * 50
        
        # GitHub stars if available
        if hasattr(model, 'github_url') and hasattr(model, 'github_stars'):
            score += min(model.github_stars / 1000, 1.0) * 30
        
        # Recency
        if hasattr(model, 'latest_version') and hasattr(model.latest_version, 'created_at'):
            days_old = (datetime.now() - model.latest_version.created_at).days
            recency_score = max(0, 20 - (days_old / 30))
            score += recency_score
        
        return score
    
    def _filter_models(
        self,
        models: List[ReplicateModel],
        criteria: Optional[ModelSearchCriteria]
    ) -> List[ReplicateModel]:
        """Filter models by criteria."""
        if not criteria:
            return models
        
        filtered = models
        
        # Filter by modality
        if criteria.modality:
            filtered = [m for m in filtered if m.modality == criteria.modality]
        
        # Filter by capabilities
        if criteria.capabilities:
            filtered = [
                m for m in filtered 
                if any(cap in m.capabilities for cap in criteria.capabilities)
            ]
        
        # Filter by owner
        if criteria.owner:
            filtered = [m for m in filtered if m.owner == criteria.owner]
        
        # Filter by cost
        if criteria.max_cost and criteria.max_cost > 0:
            filtered = [
                m for m in filtered 
                if m.cost_per_run is None or m.cost_per_run <= criteria.max_cost
            ]
        
        # Filter by runtime
        if criteria.max_runtime and criteria.max_runtime > 0:
            filtered = [
                m for m in filtered 
                if m.avg_runtime is None or m.avg_runtime <= criteria.max_runtime
            ]
        
        # Filter by popularity
        if criteria.min_popularity > 0:
            filtered = [m for m in filtered if m.popularity_score >= criteria.min_popularity]
        
        # Filter by keywords
        if criteria.keywords:
            filtered = [
                m for m in filtered
                if any(
                    kw.lower() in m.name.lower() or 
                    kw.lower() in m.description.lower()
                    for kw in criteria.keywords
                )
            ]
        
        # Sort by popularity
        filtered.sort(key=lambda m: m.popularity_score, reverse=True)
        
        return filtered
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if not self.cache_timestamp or not self.models_cache:
            return False
        
        age = (datetime.now() - self.cache_timestamp).seconds
        return age < self.cache_duration
    
    async def get_model(self, model_name: str) -> Optional[ReplicateModel]:
        """Get specific model by name."""
        # Check cache first
        if model_name in self.models_cache:
            return self.models_cache[model_name]
        
        # Try to fetch it
        model = await self._get_model_info(model_name)
        if model:
            self.models_cache[model_name] = model
        
        return model
    
    async def get_best_model_for_task(
        self,
        modality: ReplicateModality,
        capabilities: Optional[List[str]] = None,
        prefer_speed: bool = False,
        prefer_cost: bool = False
    ) -> Optional[ReplicateModel]:
        """Get the best model for a specific task."""
        criteria = ModelSearchCriteria(
            modality=modality,
            capabilities=capabilities or [],
            min_popularity=10.0 if not (prefer_speed or prefer_cost) else 0.0
        )
        
        models = await self.discover_models(criteria)
        
        if not models:
            return None
        
        # Sort by preferences
        if prefer_speed:
            # Prefer models with lower runtime
            models.sort(key=lambda m: m.avg_runtime or 999)
        elif prefer_cost:
            # Prefer models with lower cost
            models.sort(key=lambda m: m.cost_per_run or 999)
        else:
            # Already sorted by popularity
            pass
        
        return models[0] if models else None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        if not self.models_cache:
            return {"total_models": 0}
        
        from collections import Counter
        
        modalities = Counter(m.modality.value for m in self.models_cache.values())
        owners = Counter(m.owner for m in self.models_cache.values())
        
        return {
            "total_models": len(self.models_cache),
            "by_modality": dict(modalities),
            "top_owners": dict(owners.most_common(10)),
            "cache_age_seconds": (
                (datetime.now() - self.cache_timestamp).seconds
                if self.cache_timestamp else None
            )
        }


# =============================================================================
# Singleton Access
# =============================================================================

_replicate_registry: Optional[ReplicateModelRegistry] = None


def get_replicate_registry(
    api_token: Optional[str] = None,
    cache_duration: int = 3600
) -> ReplicateModelRegistry:
    """Get or create the Replicate model registry singleton."""
    global _replicate_registry
    if _replicate_registry is None:
        _replicate_registry = ReplicateModelRegistry(
            api_token=api_token,
            cache_duration=cache_duration
        )
    return _replicate_registry
