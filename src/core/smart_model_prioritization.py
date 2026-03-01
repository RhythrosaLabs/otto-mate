"""
Smart Model Prioritization System - Otto Universal
===================================================

Intelligently selects between local, remote, and Replicate models.

Priority Rules:
1. When remote models are installed and available: USE THEM
2. Never resort to Replicate unless:
   - Explicitly requested by user
   - No local/remote models available for the modality
   - Local/remote models failed after retries
3. Always check what's actually installed before deciding

Key Features:
- Automatic model discovery (local/remote/replicate)
- Smart prioritization based on availability
- User preference respect
- Explicit vs implicit model selection
- Fallback chain management
"""

import logging
import os
import subprocess
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class ModelSource(str, Enum):
    """Where the model comes from."""
    LOCAL = "local"  # Locally installed (Ollama, vLLM, etc.)
    REMOTE = "remote"  # Remote API (OpenAI, Anthropic, etc.)
    REPLICATE = "replicate"  # Replicate platform
    UNKNOWN = "unknown"


class ModelPriority(str, Enum):
    """Priority levels for model selection."""
    EXPLICIT = "explicit"  # User explicitly requested
    HIGH = "high"  # Best quality, use if available
    MEDIUM = "medium"  # Good quality, use as fallback
    LOW = "low"  # Last resort


@dataclass
class InstalledModel:
    """Information about an installed/available model."""
    name: str
    source: ModelSource
    modality: str
    capabilities: List[str]
    endpoint: Optional[str] = None
    api_key_required: bool = False
    api_key_env_var: Optional[str] = None
    is_available: bool = True
    quality_tier: str = "standard"
    speed_tier: str = "medium"
    cost_tier: str = "medium"
    priority: ModelPriority = ModelPriority.MEDIUM


@dataclass
class ModelSelection:
    """Result of model selection."""
    model: InstalledModel
    reason: str
    alternatives: List[InstalledModel] = field(default_factory=list)
    replicate_avoided: bool = False


class SmartModelPrioritization:
    """
    Intelligently prioritize model selection based on:
    - What's actually installed
    - User preferences
    - Explicit vs implicit requests
    - Modality requirements
    
    Key Rule: LOCAL/REMOTE FIRST, Replicate ONLY when necessary
    """
    
    def __init__(self):
        self.installed_models: Dict[str, InstalledModel] = {}
        self.remote_models_enabled = False
        self.local_models_enabled = False
        self.last_scan_time: Optional[float] = None
        
        # Scan for installed models on init
        self._scan_installed_models()
    
    def _scan_installed_models(self):
        """
        Scan for all installed and available models.
        Checks:
        - Local models (Ollama, vLLM, etc.)
        - Remote models (API keys, endpoints)
        - Remote mode settings
        """
        logger.info("Scanning for installed models...")
        
        # Check for remote AI models (Anthropic, OpenAI, etc.)
        self._scan_remote_models()
        
        # Check for local models (Ollama, vLLM, etc.)
        self._scan_local_models()
        
        # Log what we found
        remote_count = sum(1 for m in self.installed_models.values() if m.source == ModelSource.REMOTE)
        local_count = sum(1 for m in self.installed_models.values() if m.source == ModelSource.LOCAL)
        
        logger.info(f"Found {remote_count} remote models, {local_count} local models")
        
        import time
        self.last_scan_time = time.time()
    
    def _scan_remote_models(self):
        """Scan for remote API-only models."""
        # Anthropic/Claude models (API-only - cannot be run locally)
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            logger.info("✓ Anthropic API key found")
            self.remote_models_enabled = True
            
            # Add Claude models
            claude_models = [
                ("claude-sonnet-4-20250514", ["text", "vision", "multimodal"], ["chat", "analysis", "generation"], "ultra"),
                ("claude-opus-4", ["text", "vision", "multimodal"], ["chat", "analysis", "generation"], "ultra"),
                ("claude-3-5-sonnet-20241022", ["text", "vision", "multimodal"], ["chat", "analysis"], "high"),
                ("claude-3-opus-20240229", ["text", "vision", "multimodal"], ["chat", "analysis"], "high"),
                ("claude-3-5-haiku-20241022", ["text"], ["chat", "quick"], "quick"),
            ]
            
            for name, modalities, capabilities, quality in claude_models:
                for modality in modalities:
                    model_key = f"anthropic/{name}/{modality}"
                    self.installed_models[model_key] = InstalledModel(
                        name=name,
                        source=ModelSource.REMOTE,
                        modality=modality,
                        capabilities=capabilities,
                        api_key_required=True,
                        api_key_env_var="ANTHROPIC_API_KEY",
                        is_available=True,
                        quality_tier=quality,
                        priority=ModelPriority.HIGH
                    )
        
        # OpenAI models (API-only - cannot be run locally)
        # NOTE: DALL-E 3, Whisper are API-only services
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            logger.info("✓ OpenAI API key found")
            self.remote_models_enabled = True
            
            openai_models = [
                ("gpt-4o", ["text", "vision", "multimodal"], ["chat", "analysis", "generation"], "high"),
                ("gpt-4o-mini", ["text", "vision"], ["chat", "analysis"], "standard"),
                ("gpt-4-turbo", ["text", "vision"], ["chat", "analysis"], "high"),
                ("dall-e-3", ["image"], ["generation"], "high"),  # API-only, cannot be local
                ("whisper-1", ["audio"], ["transcription"], "high"),  # API-only, cannot be local
            ]
            
            for name, modalities, capabilities, quality in openai_models:
                for modality in modalities:
                    model_key = f"openai/{name}/{modality}"
                    self.installed_models[model_key] = InstalledModel(
                        name=name,
                        source=ModelSource.REMOTE,
                        modality=modality,
                        capabilities=capabilities,
                        api_key_required=True,
                        api_key_env_var="OPENAI_API_KEY",
                        is_available=True,
                        quality_tier=quality,
                        priority=ModelPriority.MEDIUM  # Lower priority than local models
                    )
        
        # ElevenLabs
        elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
        if elevenlabs_key:
            logger.info("✓ ElevenLabs API key found")
            self.remote_models_enabled = True
            
            self.installed_models["elevenlabs/tts/audio"] = InstalledModel(
                name="eleven_multilingual_v2",
                source=ModelSource.REMOTE,
                modality="audio",
                capabilities=["tts", "generation"],
                api_key_required=True,
                api_key_env_var="ELEVENLABS_API_KEY",
                is_available=True,
                quality_tier="high",
                priority=ModelPriority.HIGH
            )
        
        # Add more remote services as needed...
    
    def _scan_local_models(self):
        """
        Scan for locally installed models.
        
        LOCAL MODELS = Models you can run/deploy yourself:
        - Ollama (text models like Llama, Mistral)
        - vLLM (text models)
        - ComfyUI (image models like FLUX, SDXL)
        - Local FLUX deployments
        - Local Stable Diffusion
        
        These take priority over API-only services.
        """
        # Check for Ollama (text models)
        try:
            import subprocess
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.info("✓ Ollama found")
                self.local_models_enabled = True
                
                # Parse Ollama models
                lines = result.stdout.strip().split("\n")[1:]  # Skip header
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if parts:
                            model_name = parts[0]
                            
                            # Detect modality from name
                            if "vision" in model_name.lower() or "llava" in model_name.lower():
                                modality = "multimodal"
                            else:
                                modality = "text"
                            
                            model_key = f"ollama/{model_name}/{modality}"
                            self.installed_models[model_key] = InstalledModel(
                                name=model_name,
                                source=ModelSource.LOCAL,
                                modality=modality,
                                capabilities=["chat", "generation"],
                                endpoint="http://localhost:11434",
                                is_available=True,
                                quality_tier="standard",
                                priority=ModelPriority.HIGH  # Local is highest priority
                            )
        
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.debug("Ollama not found or not responding")
        
        # Check for vLLM (text models)
        vllm_endpoint = os.getenv("VLLM_ENDPOINT")
        if vllm_endpoint:
            logger.info("✓ vLLM endpoint configured")
            self.local_models_enabled = True
            
            self.installed_models["vllm/local/text"] = InstalledModel(
                name="vllm-local",
                source=ModelSource.LOCAL,
                modality="text",
                capabilities=["chat", "generation"],
                endpoint=vllm_endpoint,
                is_available=True,
                quality_tier="standard",
                priority=ModelPriority.HIGH
            )
        
        # Check for ComfyUI (image models like FLUX, SDXL)
        comfyui_endpoint = os.getenv("COMFYUI_ENDPOINT") or os.getenv("COMFYUI_URL")
        if comfyui_endpoint:
            logger.info("✓ ComfyUI endpoint configured")
            self.local_models_enabled = True
            
            # ComfyUI can run FLUX, SDXL, SD, etc.
            self.installed_models["comfyui/flux/image"] = InstalledModel(
                name="flux-local",
                source=ModelSource.LOCAL,
                modality="image",
                capabilities=["generation", "editing"],
                endpoint=comfyui_endpoint,
                is_available=True,
                quality_tier="high",
                priority=ModelPriority.HIGH  # Local FLUX beats remote DALL-E 3
            )
        
        # Check for local FLUX deployment
        flux_endpoint = os.getenv("FLUX_ENDPOINT") or os.getenv("FLUX_LOCAL")
        if flux_endpoint:
            logger.info("✓ Local FLUX endpoint configured")
            self.local_models_enabled = True
            
            self.installed_models["local/flux/image"] = InstalledModel(
                name="flux-local",
                source=ModelSource.LOCAL,
                modality="image",
                capabilities=["generation"],
                endpoint=flux_endpoint,
                is_available=True,
                quality_tier="high",
                priority=ModelPriority.HIGH  # Local FLUX beats remote services
            )
        
        # Check for local Stable Diffusion
        sd_endpoint = os.getenv("SD_ENDPOINT") or os.getenv("AUTOMATIC1111_URL")
        if sd_endpoint:
            logger.info("✓ Local Stable Diffusion endpoint configured")
            self.local_models_enabled = True
            
            self.installed_models["local/sd/image"] = InstalledModel(
                name="stable-diffusion-local",
                source=ModelSource.LOCAL,
                modality="image",
                capabilities=["generation", "editing"],
                endpoint=sd_endpoint,
                is_available=True,
                quality_tier="high",
                priority=ModelPriority.HIGH
            )
    
    def select_model(
        self,
        modality: str,
        capabilities: Optional[List[str]] = None,
        explicit_model: Optional[str] = None,
        explicit_source: Optional[ModelSource] = None,
        prefer_speed: bool = False,
        prefer_cost: bool = False,
        quality_level: str = "standard"
    ) -> ModelSelection:
        """
        Select the best model following priority rules.
        
        Priority:
        1. Explicit user request (always honor)
        2. Remote models (if installed and available)
        3. Local models (if installed and available)
        4. Replicate (ONLY if explicitly requested or nothing else available)
        
        Args:
            modality: Required modality (text, image, video, etc.)
            capabilities: Required capabilities
            explicit_model: User explicitly requested this model
            explicit_source: User explicitly requested this source
            prefer_speed: Prefer faster models
            prefer_cost: Prefer cheaper models
            quality_level: Required quality level
            
        Returns:
            ModelSelection with chosen model and reasoning
        """
        capabilities = capabilities or []
        
        logger.info(f"Selecting model for {modality} with capabilities {capabilities}")
        
        # Handle explicit requests
        if explicit_model:
            logger.info(f"User explicitly requested: {explicit_model}")
            
            # If they explicitly mentioned "replicate", honor it
            if explicit_source == ModelSource.REPLICATE or "replicate" in explicit_model.lower():
                return self._select_replicate_model(modality, capabilities)
            
            # Try to find the requested model in installed models
            for key, model in self.installed_models.items():
                if explicit_model.lower() in model.name.lower():
                    logger.info(f"✓ Found requested model in installed: {model.name}")
                    return ModelSelection(
                        model=model,
                        reason=f"User explicitly requested {explicit_model}",
                        replicate_avoided=True
                    )
            
            # Not found in installed - warn but continue with smart selection
            logger.warning(f"Requested model '{explicit_model}' not found in installed models")
        
        # Get candidates from installed models
        candidates = self._filter_installed_models(
            modality=modality,
            capabilities=capabilities,
            quality_level=quality_level
        )
        
        if not candidates:
            logger.warning(f"No installed models found for {modality}")
            # Last resort: Replicate
            return self._select_replicate_model(modality, capabilities)
        
        # Priority 1: LOCAL models (if enabled) - HIGHEST PRIORITY
        # Local FLUX, local SD, Ollama, etc. beat everything
        local_candidates = [m for m in candidates if m.source == ModelSource.LOCAL]
        if local_candidates and self.local_models_enabled:
            logger.info(f"✓ Using LOCAL model (found {len(local_candidates)} options)")
            best = self._rank_models(local_candidates, prefer_speed, prefer_cost)[0]
            return ModelSelection(
                model=best,
                reason="Local model available - highest priority (local FLUX beats remote DALL-E)",
                alternatives=local_candidates[1:],
                replicate_avoided=True
            )
        
        # Priority 2: REMOTE API models (if enabled)
        # DALL-E 3, Claude, GPT-4, etc.
        remote_candidates = [m for m in candidates if m.source == ModelSource.REMOTE]
        if remote_candidates and self.remote_models_enabled:
            logger.info(f"✓ Using remote API model (found {len(remote_candidates)} options)")
            best = self._rank_models(remote_candidates, prefer_speed, prefer_cost)[0]
            return ModelSelection(
                model=best,
                reason="Remote API model available (DALL-E 3, Claude, etc.)",
                alternatives=remote_candidates[1:],
                replicate_avoided=True
            )
        
        # Priority 3: Last resort - Replicate
        logger.warning("No local or remote models available, falling back to Replicate")
        return self._select_replicate_model(modality, capabilities)
    
    def _filter_installed_models(
        self,
        modality: str,
        capabilities: List[str],
        quality_level: str
    ) -> List[InstalledModel]:
        """Filter installed models by criteria."""
        candidates = []
        
        for model in self.installed_models.values():
            # Check if available
            if not model.is_available:
                continue
            
            # Check modality match
            if model.modality != modality and model.modality != "multimodal":
                # Multimodal can handle any modality
                if modality not in ["text", "vision", "image"]:  # Multimodal covers these
                    continue
            
            # Check capabilities
            if capabilities:
                if not any(cap in model.capabilities for cap in capabilities):
                    continue
            
            # Check quality level
            quality_levels = ["quick", "standard", "high", "ultra"]
            if quality_level in quality_levels:
                required_idx = quality_levels.index(quality_level)
                model_idx = quality_levels.index(model.quality_tier)
                if model_idx < required_idx:
                    continue
            
            candidates.append(model)
        
        return candidates
    
    def _rank_models(
        self,
        models: List[InstalledModel],
        prefer_speed: bool = False,
        prefer_cost: bool = False
    ) -> List[InstalledModel]:
        """Rank models by preference."""
        if not models:
            return []
        
        # Score each model
        scored = []
        for model in models:
            score = 0
            
            # Priority score
            priority_scores = {
                ModelPriority.EXPLICIT: 100,
                ModelPriority.HIGH: 50,
                ModelPriority.MEDIUM: 25,
                ModelPriority.LOW: 10
            }
            score += priority_scores.get(model.priority, 0)
            
            # Quality score
            quality_scores = {"quick": 10, "standard": 20, "high": 30, "ultra": 40}
            score += quality_scores.get(model.quality_tier, 0)
            
            # Speed preference
            if prefer_speed:
                speed_scores = {"fast": 30, "medium": 15, "slow": 5}
                score += speed_scores.get(model.speed_tier, 0)
            
            # Cost preference
            if prefer_cost:
                cost_scores = {"free": 30, "low": 20, "medium": 10, "high": 5}
                score += cost_scores.get(model.cost_tier, 0)
            
            scored.append((score, model))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        
        return [model for score, model in scored]
    
    def _select_replicate_model(
        self,
        modality: str,
        capabilities: List[str]
    ) -> ModelSelection:
        """
        Select a Replicate model as last resort.
        
        This should only be called when:
        - User explicitly requested Replicate
        - No local/remote models available
        """
        logger.info("Selecting Replicate model (last resort or explicit request)")
        
        # Create a placeholder for Replicate
        # The actual model will be determined by the Replicate registry
        replicate_model = InstalledModel(
            name="replicate-auto",
            source=ModelSource.REPLICATE,
            modality=modality,
            capabilities=capabilities,
            api_key_required=True,
            api_key_env_var="REPLICATE_API_TOKEN",
            is_available=True,
            quality_tier="standard",
            priority=ModelPriority.LOW
        )
        
        return ModelSelection(
            model=replicate_model,
            reason="No local/remote models available, using Replicate as fallback",
            replicate_avoided=False
        )
    
    def force_rescan(self):
        """Force a rescan of installed models."""
        logger.info("Forcing model rescan...")
        self.installed_models.clear()
        self._scan_installed_models()
    
    def is_replicate_explicit(self, user_input: str) -> bool:
        """Check if user explicitly requested Replicate."""
        user_lower = user_input.lower()
        replicate_keywords = [
            "replicate",
            "use replicate",
            "with replicate",
            "via replicate",
            "on replicate"
        ]
        return any(kw in user_lower for kw in replicate_keywords)
    
    def get_available_models(
        self,
        modality: Optional[str] = None,
        source: Optional[ModelSource] = None
    ) -> List[InstalledModel]:
        """Get list of available models, optionally filtered."""
        models = list(self.installed_models.values())
        
        if modality:
            models = [m for m in models if m.modality == modality or m.modality == "multimodal"]
        
        if source:
            models = [m for m in models if m.source == source]
        
        return models
    
    def get_stats(self) -> Dict[str, Any]:
        """Get prioritization system stats."""
        from collections import Counter
        
        sources = Counter(m.source.value for m in self.installed_models.values())
        modalities = Counter(m.modality for m in self.installed_models.values())
        
        return {
            "total_models": len(self.installed_models),
            "remote_models_enabled": self.remote_models_enabled,
            "local_models_enabled": self.local_models_enabled,
            "by_source": dict(sources),
            "by_modality": dict(modalities),
            "replicate_is_fallback": True,  # Always true by design
        }


# =============================================================================
# Singleton Access
# =============================================================================

_prioritization_system: Optional[SmartModelPrioritization] = None


def get_prioritization_system() -> SmartModelPrioritization:
    """Get or create the model prioritization system singleton."""
    global _prioritization_system
    if _prioritization_system is None:
        _prioritization_system = SmartModelPrioritization()
    return _prioritization_system
