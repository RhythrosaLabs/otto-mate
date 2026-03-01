"""
Ollama API Endpoints

Manage and use local LLM models via Ollama.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import logging
import json

from ..core.ollama_client import (
    get_ollama_client,
    OllamaMessage,
    OllamaModel,
    get_recommended_models,
    is_ollama_available
)
from ..core.model_recommendations import (
    RECOMMENDED_MODELS,
    ModelInfo,
    UseCase,
    ModelSize,
    get_featured_models,
    get_models_by_use_case,
    get_models_by_size,
    recommend_model,
    get_starter_pack,
    get_comparison,
    MODELS_BY_NAME
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ollama", tags=["Ollama"])


# Request/Response Models
class GenerateRequest(BaseModel):
    """Request to generate text."""
    model: str
    prompt: str
    system: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False


class ChatRequest(BaseModel):
    """Request for chat completion."""
    model: str
    messages: List[dict]  # {role: str, content: str}
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False


class PullRequest(BaseModel):
    """Request to pull/download a model."""
    model: str


class OllamaStatus(BaseModel):
    """Ollama service status."""
    available: bool
    base_url: str
    models_installed: int
    recommended_models: dict


@router.get("/status")
async def get_status() -> OllamaStatus:
    """Get Ollama service status."""
    client = get_ollama_client()
    available = await client.is_available()
    
    models = []
    if available:
        models = await client.list_models()
    
    return OllamaStatus(
        available=available,
        base_url=client.base_url,
        models_installed=len(models),
        recommended_models=get_recommended_models()
    )


@router.get("/models")
async def list_models() -> List[OllamaModel]:
    """List all installed Ollama models."""
    client = get_ollama_client()
    
    if not await client.is_available():
        raise HTTPException(503, "Ollama is not running. Install from https://ollama.ai")
    
    models = await client.list_models()
    return models


@router.post("/models/pull")
async def pull_model(request: PullRequest):
    """
    Pull (download) a model from Ollama library.
    
    This streams progress updates as the model downloads.
    """
    client = get_ollama_client()
    
    if not await client.is_available():
        raise HTTPException(503, "Ollama is not running")
    
    async def generate_progress():
        async for progress in client.pull_model(request.model):
            yield f"data: {json.dumps(progress)}\n\n"
        yield "data: {\"done\": true}\n\n"
    
    return StreamingResponse(
        generate_progress(),
        media_type="text/event-stream"
    )


@router.delete("/models/{model_name}")
async def delete_model(model_name: str):
    """Delete an installed model."""
    client = get_ollama_client()
    
    if not await client.is_available():
        raise HTTPException(503, "Ollama is not running")
    
    success = await client.delete_model(model_name)
    if success:
        return {"success": True, "message": f"Model {model_name} deleted"}
    raise HTTPException(500, "Failed to delete model")


@router.post("/generate")
async def generate_text(request: GenerateRequest):
    """
    Generate text with an Ollama model.
    
    Supports streaming for real-time generation.
    """
    client = get_ollama_client()
    
    if not await client.is_available():
        raise HTTPException(503, "Ollama is not running. Install from https://ollama.ai")
    
    if request.stream:
        async def generate_stream():
            async for chunk in client.generate(
                model=request.model,
                prompt=request.prompt,
                system=request.system,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=True
            ):
                yield chunk
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain"
        )
    else:
        # Non-streaming response
        full_response = ""
        async for chunk in client.generate(
            model=request.model,
            prompt=request.prompt,
            system=request.system,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=False
        ):
            full_response += chunk
        
        return {
            "model": request.model,
            "response": full_response
        }


@router.post("/chat")
async def chat_completion(request: ChatRequest):
    """
    Chat with an Ollama model using message history.
    
    Supports streaming for real-time responses.
    """
    client = get_ollama_client()
    
    if not await client.is_available():
        raise HTTPException(503, "Ollama is not running. Install from https://ollama.ai")
    
    # Convert dict messages to OllamaMessage objects
    messages = [OllamaMessage(**msg) for msg in request.messages]
    
    if request.stream:
        async def generate_stream():
            async for chunk in client.chat(
                model=request.model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=True
            ):
                yield chunk
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain"
        )
    else:
        # Non-streaming response
        full_response = ""
        async for chunk in client.chat(
            model=request.model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=False
        ):
            full_response += chunk
        
        return {
            "model": request.model,
            "response": full_response,
            "message": {
                "role": "assistant",
                "content": full_response
            }
        }


@router.get("/setup-guide")
async def ollama_setup_guide():
    """Get instructions for setting up Ollama."""
    return {
        "name": "Ollama - Run LLMs Locally",
        "description": "Run powerful AI models on your own computer - no API keys needed!",
        "benefits": [
            "100% private - your data never leaves your machine",
            "No API costs - unlimited usage",
            "Works offline",
            "Fast responses on good hardware"
        ],
        "requirements": {
            "ram": "8GB minimum (16GB+ recommended)",
            "disk": "4GB+ per model",
            "gpu": "Optional but recommended (NVIDIA, AMD, or Apple Silicon)"
        },
        "steps": [
            {
                "step": 1,
                "title": "Install Ollama",
                "description": "Download and install Ollama for your platform",
                "urls": {
                    "mac": "https://ollama.ai/download/mac",
                    "windows": "https://ollama.ai/download/windows",
                    "linux": "https://ollama.ai/download/linux"
                }
            },
            {
                "step": 2,
                "title": "Verify Installation",
                "description": "Open terminal and run: ollama --version",
                "expected": "You should see the version number"
            },
            {
                "step": 3,
                "title": "Pull a Model",
                "description": "Download your first model (e.g., Llama 2 7B)",
                "command": "ollama pull llama2",
                "note": "This will download ~4GB"
            },
            {
                "step": 4,
                "title": "Test It",
                "description": "Try it out in the terminal",
                "command": "ollama run llama2 'What is the capital of France?'"
            },
            {
                "step": 5,
                "title": "Use with Otto",
                "description": "Otto will automatically detect Ollama if it's running",
                "note": "Check status at /api/ollama/status"
            }
        ],
        "recommended_first_models": {
            "llama2": "General purpose, 4GB",
            "mistral": "Fast and capable, 4GB",
            "codellama": "For coding tasks, 4GB",
            "tinyllama": "Fastest, 638MB"
        },
        "api_docs": "https://github.com/ollama/ollama/blob/main/docs/api.md"
    }


# ===== MODEL RECOMMENDATIONS =====

@router.get("/recommendations")
async def get_model_recommendations():
    """Get curated list of recommended models with details."""
    return {
        "featured": [
            {
                "name": m.name,
                "display_name": m.display_name,
                "description": m.description,
                "size_gb": m.size_gb,
                "parameter_count": m.parameter_count,
                "use_cases": [uc.value for uc in m.use_cases],
                "size_category": m.size_category.value,
                "pros": m.pros,
                "cons": m.cons,
                "recommended_for": m.recommended_for,
                "speed_rating": m.speed_rating,
                "quality_rating": m.quality_rating,
                "memory_gb": m.memory_gb,
                "tags": m.tags
            }
            for m in get_featured_models()
        ],
        "all_models": [
            {
                "name": m.name,
                "display_name": m.display_name,
                "description": m.description,
                "size_gb": m.size_gb,
                "parameter_count": m.parameter_count,
                "use_cases": [uc.value for uc in m.use_cases],
                "speed_rating": m.speed_rating,
                "quality_rating": m.quality_rating,
                "memory_gb": m.memory_gb,
                "featured": m.featured
            }
            for m in RECOMMENDED_MODELS
        ],
        "use_cases": [uc.value for uc in UseCase],
        "size_categories": [size.value for size in ModelSize]
    }


@router.get("/recommendations/featured")
async def get_featured():
    """Get only featured/recommended models."""
    return {
        "models": [
            {
                "name": m.name,
                "display_name": m.display_name,
                "description": m.description,
                "size_gb": m.size_gb,
                "use_cases": [uc.value for uc in m.use_cases],
                "speed_rating": m.speed_rating,
                "quality_rating": m.quality_rating
            }
            for m in get_featured_models()
        ]
    }


@router.get("/recommendations/use-case/{use_case}")
async def get_by_use_case(use_case: str):
    """Get models recommended for a specific use case."""
    try:
        uc = UseCase(use_case)
        models = get_models_by_use_case(uc)
        return {
            "use_case": use_case,
            "models": [
                {
                    "name": m.name,
                    "display_name": m.display_name,
                    "description": m.description,
                    "size_gb": m.size_gb,
                    "speed_rating": m.speed_rating,
                    "quality_rating": m.quality_rating
                }
                for m in models
            ]
        }
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid use case: {use_case}")


@router.get("/recommendations/starter-pack")
async def get_starter_pack_info():
    """Get recommended starter pack for new users."""
    starter_models = get_starter_pack()
    return {
        "description": "Essential models to get started with local LLMs",
        "total_size_gb": sum(MODELS_BY_NAME[m].size_gb for m in starter_models if m in MODELS_BY_NAME),
        "models": [
            {
                "name": m,
                "display_name": MODELS_BY_NAME[m].display_name,
                "description": MODELS_BY_NAME[m].description,
                "size_gb": MODELS_BY_NAME[m].size_gb,
                "why": MODELS_BY_NAME[m].recommended_for[0] if MODELS_BY_NAME[m].recommended_for else ""
            }
            for m in starter_models if m in MODELS_BY_NAME
        ],
        "install_command": f"ollama pull {' && ollama pull '.join(starter_models)}"
    }


@router.post("/recommendations/starter-pack/install")
async def install_starter_pack():
    """Download and install the recommended starter pack."""
    if not is_ollama_available():
        raise HTTPException(status_code=503, detail="Ollama not available")
    
    client = get_ollama_client()
    starter_models = get_starter_pack()
    results = []
    
    for model_name in starter_models:
        try:
            logger.info(f"Pulling model: {model_name}")
            await client.pull_model(model_name)
            results.append({
                "model": model_name,
                "status": "success",
                "message": f"Successfully downloaded {model_name}"
            })
        except Exception as e:
            logger.error(f"Failed to pull {model_name}: {e}")
            results.append({
                "model": model_name,
                "status": "error",
                "message": str(e)
            })
    
    return {
        "status": "completed",
        "results": results,
        "successful": len([r for r in results if r["status"] == "success"]),
        "failed": len([r for r in results if r["status"] == "error"])
    }


@router.get("/recommendations/compare/{model1}/{model2}")
async def compare_models(model1: str, model2: str):
    """Compare two models side by side."""
    comparison = get_comparison(model1, model2)
    if "error" in comparison:
        raise HTTPException(status_code=404, detail=comparison["error"])
    return comparison


@router.post("/recommendations/suggest")
async def suggest_models(
    use_case: Optional[str] = None,
    max_size_gb: Optional[float] = None,
    max_memory_gb: Optional[int] = None,
    min_speed: Optional[int] = None,
    min_quality: Optional[int] = None
):
    """Get personalized model recommendations based on constraints."""
    uc = UseCase(use_case) if use_case else None
    
    models = recommend_model(
        use_case=uc,
        max_size_gb=max_size_gb,
        max_memory_gb=max_memory_gb,
        min_speed=min_speed,
        min_quality=min_quality
    )
    
    return {
        "constraints": {
            "use_case": use_case,
            "max_size_gb": max_size_gb,
            "max_memory_gb": max_memory_gb,
            "min_speed": min_speed,
            "min_quality": min_quality
        },
        "recommended": [
            {
                "name": m.name,
                "display_name": m.display_name,
                "description": m.description,
                "size_gb": m.size_gb,
                "memory_gb": m.memory_gb,
                "speed_rating": m.speed_rating,
                "quality_rating": m.quality_rating,
                "use_cases": [uc.value for uc in m.use_cases],
                "why_recommended": m.recommended_for[0] if m.recommended_for else ""
            }
            for m in models[:5]  # Top 5 recommendations
        ]
    }


@router.get("/model-info/{model_name}")
async def get_model_info_detailed(model_name: str):
    """Get detailed information about a specific model."""
    model = MODELS_BY_NAME.get(model_name)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found in recommendations")
    
    return {
        "name": model.name,
        "display_name": model.display_name,
        "description": model.description,
        "size_gb": model.size_gb,
        "parameter_count": model.parameter_count,
        "use_cases": [uc.value for uc in model.use_cases],
        "size_category": model.size_category.value,
        "pros": model.pros,
        "cons": model.cons,
        "recommended_for": model.recommended_for,
        "speed_rating": model.speed_rating,
        "quality_rating": model.quality_rating,
        "memory_gb": model.memory_gb,
        "tags": model.tags,
        "featured": model.featured
    }
