"""
Model Recommendations and Management
Curated list of recommended models for different use cases
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class UseCase(str, Enum):
    """Model use case categories"""
    CHAT = "chat"
    CODE = "code"
    VISION = "vision"
    EMBEDDING = "embedding"
    CREATIVE = "creative"
    REASONING = "reasoning"
    FAST = "fast"
    MULTILINGUAL = "multilingual"

class ModelSize(str, Enum):
    """Model size categories"""
    TINY = "tiny"      # < 1GB
    SMALL = "small"    # 1-3GB
    MEDIUM = "medium"  # 3-10GB
    LARGE = "large"    # 10-30GB
    XLARGE = "xlarge"  # > 30GB

@dataclass
class ModelInfo:
    """Information about a recommended model"""
    name: str
    display_name: str
    description: str
    size_gb: float
    parameter_count: str
    use_cases: List[UseCase]
    size_category: ModelSize
    pros: List[str]
    cons: List[str]
    recommended_for: List[str]
    speed_rating: int  # 1-5, 5 being fastest
    quality_rating: int  # 1-5, 5 being best quality
    memory_gb: int  # Minimum RAM needed
    tags: List[str]
    official: bool = True
    featured: bool = False

# Curated model recommendations
RECOMMENDED_MODELS = [
    # TINY MODELS - Ultra fast, low resource
    ModelInfo(
        name="llama3.2:1b",
        display_name="Llama 3.2 1B",
        description="Lightning-fast tiny model for basic chat and quick responses",
        size_gb=1.3,
        parameter_count="1.2B",
        use_cases=[UseCase.CHAT, UseCase.FAST],
        size_category=ModelSize.TINY,
        pros=[
            "Extremely fast responses",
            "Minimal memory usage (2GB RAM)",
            "Good for API rate limiting scenarios",
            "Can run on older hardware"
        ],
        cons=[
            "Limited reasoning capabilities",
            "May struggle with complex tasks",
            "Smaller context window"
        ],
        recommended_for=[
            "Quick Q&A chatbots",
            "Simple automation tasks",
            "Resource-constrained environments",
            "Testing and development"
        ],
        speed_rating=5,
        quality_rating=2,
        memory_gb=2,
        tags=["beginner-friendly", "fast", "low-resource"],
        featured=True
    ),
    
    # SMALL MODELS - Balanced performance
    ModelInfo(
        name="llama3.2:3b",
        display_name="Llama 3.2 3B",
        description="Excellent balance of speed and capability for most tasks",
        size_gb=2.0,
        parameter_count="3.2B",
        use_cases=[UseCase.CHAT, UseCase.CODE, UseCase.FAST, UseCase.REASONING],
        size_category=ModelSize.SMALL,
        pros=[
            "Fast inference speed",
            "Good reasoning abilities",
            "Runs on 4GB RAM comfortably",
            "Handles most daily tasks well"
        ],
        cons=[
            "Not ideal for very complex reasoning",
            "Limited specialized knowledge"
        ],
        recommended_for=[
            "Daily assistant tasks",
            "Code completion and simple debugging",
            "Content drafting",
            "General purpose chatbot"
        ],
        speed_rating=5,
        quality_rating=3,
        memory_gb=4,
        tags=["recommended", "balanced", "beginner-friendly"],
        featured=True
    ),
    
    ModelInfo(
        name="phi3:mini",
        display_name="Phi-3 Mini",
        description="Microsoft's powerful small model with strong reasoning",
        size_gb=2.3,
        parameter_count="3.8B",
        use_cases=[UseCase.CHAT, UseCase.CODE, UseCase.REASONING],
        size_category=ModelSize.SMALL,
        pros=[
            "Excellent reasoning for size",
            "Strong at math and logic",
            "Good code understanding",
            "Efficient memory usage"
        ],
        cons=[
            "Can be verbose",
            "Less creative than larger models"
        ],
        recommended_for=[
            "Logic puzzles and reasoning",
            "Educational content",
            "Code analysis",
            "Technical documentation"
        ],
        speed_rating=4,
        quality_rating=4,
        memory_gb=4,
        tags=["reasoning", "microsoft", "code"],
        featured=True
    ),
    
    # MEDIUM MODELS - High quality
    ModelInfo(
        name="llama3.1:8b",
        display_name="Llama 3.1 8B",
        description="Meta's flagship small model with excellent all-around performance",
        size_gb=4.7,
        parameter_count="8B",
        use_cases=[UseCase.CHAT, UseCase.CODE, UseCase.REASONING, UseCase.CREATIVE],
        size_category=ModelSize.MEDIUM,
        pros=[
            "High quality responses",
            "Strong reasoning capabilities",
            "Good at following instructions",
            "Multilingual support",
            "128k context window"
        ],
        cons=[
            "Slower than smaller models",
            "Requires 8GB+ RAM"
        ],
        recommended_for=[
            "Professional writing assistant",
            "Code review and debugging",
            "Complex reasoning tasks",
            "Content creation"
        ],
        speed_rating=3,
        quality_rating=4,
        memory_gb=8,
        tags=["popular", "meta", "versatile"],
        featured=True
    ),
    
    ModelInfo(
        name="mistral:7b",
        display_name="Mistral 7B",
        description="High-performance European model known for accuracy",
        size_gb=4.1,
        parameter_count="7.2B",
        use_cases=[UseCase.CHAT, UseCase.CODE, UseCase.REASONING],
        size_category=ModelSize.MEDIUM,
        pros=[
            "Very accurate responses",
            "Excellent instruction following",
            "Strong at technical tasks",
            "Well-balanced performance"
        ],
        cons=[
            "Can be overly formal",
            "Requires 8GB RAM"
        ],
        recommended_for=[
            "Technical documentation",
            "Professional communications",
            "Code generation",
            "Fact-based Q&A"
        ],
        speed_rating=3,
        quality_rating=4,
        memory_gb=8,
        tags=["accurate", "technical", "european"],
        featured=True
    ),
    
    ModelInfo(
        name="codellama:7b",
        display_name="Code Llama 7B",
        description="Specialized for code generation and programming tasks",
        size_gb=3.8,
        parameter_count="7B",
        use_cases=[UseCase.CODE],
        size_category=ModelSize.MEDIUM,
        pros=[
            "Excellent code generation",
            "Understands many languages",
            "Good at code completion",
            "Infilling support"
        ],
        cons=[
            "Not great for general chat",
            "Requires 8GB RAM"
        ],
        recommended_for=[
            "Code generation",
            "Bug fixing",
            "Code completion IDE",
            "Programming tutorials"
        ],
        speed_rating=3,
        quality_rating=5,
        memory_gb=8,
        tags=["code", "specialized", "meta"],
        featured=True
    ),
    
    # VISION MODELS
    ModelInfo(
        name="llava:7b",
        display_name="LLaVA 7B",
        description="Multimodal model that can understand images and text",
        size_gb=4.7,
        parameter_count="7B",
        use_cases=[UseCase.VISION, UseCase.CHAT],
        size_category=ModelSize.MEDIUM,
        pros=[
            "Can analyze images",
            "Describes visual content",
            "Good for OCR tasks",
            "Understands charts/diagrams"
        ],
        cons=[
            "Slower inference",
            "Requires 8GB+ RAM",
            "Less accurate than GPT-4V"
        ],
        recommended_for=[
            "Image analysis",
            "Document OCR",
            "Chart interpretation",
            "Visual Q&A"
        ],
        speed_rating=2,
        quality_rating=3,
        memory_gb=8,
        tags=["vision", "multimodal", "ocr"],
        featured=False
    ),
    
    ModelInfo(
        name="llava:13b",
        display_name="LLaVA 13B",
        description="Larger vision model with better image understanding",
        size_gb=8.0,
        parameter_count="13B",
        use_cases=[UseCase.VISION, UseCase.CHAT],
        size_category=ModelSize.MEDIUM,
        pros=[
            "Better image understanding",
            "More detailed descriptions",
            "Good at complex visuals"
        ],
        cons=[
            "Slow inference",
            "Requires 16GB RAM",
            "Large download"
        ],
        recommended_for=[
            "Professional image analysis",
            "Medical/scientific imaging",
            "Detailed OCR",
            "Art analysis"
        ],
        speed_rating=1,
        quality_rating=4,
        memory_gb=16,
        tags=["vision", "multimodal", "advanced"],
        featured=False
    ),
    
    # LARGE MODELS - Maximum quality
    ModelInfo(
        name="llama3.1:70b",
        display_name="Llama 3.1 70B",
        description="Meta's most capable model, near GPT-4 performance",
        size_gb=40.0,
        parameter_count="70B",
        use_cases=[UseCase.CHAT, UseCase.CODE, UseCase.REASONING, UseCase.CREATIVE],
        size_category=ModelSize.XLARGE,
        pros=[
            "Exceptional quality",
            "Advanced reasoning",
            "Great at complex tasks",
            "128k context window"
        ],
        cons=[
            "Very slow (10-30 sec/response)",
            "Requires 64GB+ RAM",
            "40GB download"
        ],
        recommended_for=[
            "Complex reasoning problems",
            "High-quality content creation",
            "Advanced code generation",
            "Research and analysis"
        ],
        speed_rating=1,
        quality_rating=5,
        memory_gb=64,
        tags=["advanced", "slow", "high-quality"],
        featured=False
    ),
    
    # MULTILINGUAL
    ModelInfo(
        name="aya:8b",
        display_name="Aya 8B",
        description="Multilingual model supporting 100+ languages",
        size_gb=4.8,
        parameter_count="8B",
        use_cases=[UseCase.CHAT, UseCase.MULTILINGUAL],
        size_category=ModelSize.MEDIUM,
        pros=[
            "Supports 100+ languages",
            "Good translation",
            "Cultural awareness",
            "Non-English content"
        ],
        cons=[
            "English performance lower than specialized models",
            "Requires 8GB RAM"
        ],
        recommended_for=[
            "International chatbots",
            "Translation services",
            "Multilingual support",
            "Non-English content"
        ],
        speed_rating=3,
        quality_rating=3,
        memory_gb=8,
        tags=["multilingual", "translation", "global"],
        featured=False
    ),
    
    # EMBEDDINGS
    ModelInfo(
        name="nomic-embed-text",
        display_name="Nomic Embed Text",
        description="High-quality text embeddings for semantic search",
        size_gb=0.3,
        parameter_count="137M",
        use_cases=[UseCase.EMBEDDING],
        size_category=ModelSize.TINY,
        pros=[
            "Excellent embeddings",
            "Very fast",
            "Tiny model size",
            "Production-ready"
        ],
        cons=[
            "Only generates embeddings",
            "No text generation"
        ],
        recommended_for=[
            "Semantic search",
            "Document similarity",
            "RAG systems",
            "Clustering"
        ],
        speed_rating=5,
        quality_rating=5,
        memory_gb=2,
        tags=["embeddings", "rag", "search"],
        featured=True
    ),
]

# Create lookup dictionaries
MODELS_BY_NAME = {model.name: model for model in RECOMMENDED_MODELS}
MODELS_BY_USE_CASE = {}
for model in RECOMMENDED_MODELS:
    for use_case in model.use_cases:
        if use_case not in MODELS_BY_USE_CASE:
            MODELS_BY_USE_CASE[use_case] = []
        MODELS_BY_USE_CASE[use_case].append(model)

def get_featured_models() -> List[ModelInfo]:
    """Get featured/recommended models"""
    return [m for m in RECOMMENDED_MODELS if m.featured]

def get_models_by_use_case(use_case: UseCase) -> List[ModelInfo]:
    """Get models suitable for a specific use case"""
    return MODELS_BY_USE_CASE.get(use_case, [])

def get_models_by_size(size: ModelSize) -> List[ModelInfo]:
    """Get models in a specific size category"""
    return [m for m in RECOMMENDED_MODELS if m.size_category == size]

def recommend_model(
    use_case: Optional[UseCase] = None,
    max_size_gb: Optional[float] = None,
    max_memory_gb: Optional[int] = None,
    min_speed: Optional[int] = None,
    min_quality: Optional[int] = None
) -> List[ModelInfo]:
    """
    Recommend models based on constraints
    
    Args:
        use_case: Desired use case
        max_size_gb: Maximum model size in GB
        max_memory_gb: Maximum RAM available in GB
        min_speed: Minimum speed rating (1-5)
        min_quality: Minimum quality rating (1-5)
    
    Returns:
        List of matching models sorted by relevance
    """
    results = list(RECOMMENDED_MODELS)
    
    # Filter by use case
    if use_case:
        results = [m for m in results if use_case in m.use_cases]
    
    # Filter by size
    if max_size_gb:
        results = [m for m in results if m.size_gb <= max_size_gb]
    
    # Filter by memory
    if max_memory_gb:
        results = [m for m in results if m.memory_gb <= max_memory_gb]
    
    # Filter by speed
    if min_speed:
        results = [m for m in results if m.speed_rating >= min_speed]
    
    # Filter by quality
    if min_quality:
        results = [m for m in results if m.quality_rating >= min_quality]
    
    # Sort by featured, then quality, then speed
    results.sort(key=lambda m: (not m.featured, -m.quality_rating, -m.speed_rating))
    
    return results

def get_starter_pack() -> List[str]:
    """Get recommended starter pack of models for new users"""
    return [
        "llama3.2:3b",        # General purpose, fast
        "nomic-embed-text",   # Embeddings for RAG
        "codellama:7b",       # Code generation
    ]

def get_comparison(model1: str, model2: str) -> Dict:
    """Compare two models side by side"""
    m1 = MODELS_BY_NAME.get(model1)
    m2 = MODELS_BY_NAME.get(model2)
    
    if not m1 or not m2:
        return {"error": "Model not found"}
    
    return {
        "models": [
            {
                "name": m1.name,
                "display_name": m1.display_name,
                "size_gb": m1.size_gb,
                "memory_gb": m1.memory_gb,
                "speed_rating": m1.speed_rating,
                "quality_rating": m1.quality_rating,
                "use_cases": [uc.value for uc in m1.use_cases]
            },
            {
                "name": m2.name,
                "display_name": m2.display_name,
                "size_gb": m2.size_gb,
                "memory_gb": m2.memory_gb,
                "speed_rating": m2.speed_rating,
                "quality_rating": m2.quality_rating,
                "use_cases": [uc.value for uc in m2.use_cases]
            }
        ],
        "winner": {
            "size": m1.name if m1.size_gb < m2.size_gb else m2.name,
            "speed": m1.name if m1.speed_rating > m2.speed_rating else m2.name,
            "quality": m1.name if m1.quality_rating > m2.quality_rating else m2.name,
            "memory": m1.name if m1.memory_gb < m2.memory_gb else m2.name,
        }
    }
