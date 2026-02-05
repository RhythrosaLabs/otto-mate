"""
Replicate Advanced Integration
==============================

Advanced Replicate API features:
- Webhook support for async predictions
- Model chaining for complex pipelines
- Batch processing
- Streaming predictions
- Training/fine-tuning support
- Model search and discovery
"""

import asyncio
import aiohttp
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field

from .core import tool, ToolBase

logger = logging.getLogger(__name__)

# ==========================================
# DATA MODELS
# ==========================================

@dataclass
class PredictionResult:
    """Result from a Replicate prediction"""
    prediction_id: str
    model: str
    status: str
    output: Any = None
    error: Optional[str] = None
    metrics: Optional[Dict] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class ChainStep:
    """A step in a model chain"""
    model: str
    input_mapping: Dict[str, str]  # Maps output from previous step to this input
    params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass
class WebhookConfig:
    """Webhook configuration"""
    url: str
    events: List[str] = field(default_factory=lambda: ["start", "completed"])
    secret: Optional[str] = None


# ==========================================
# REPLICATE ADVANCED TOOLS
# ==========================================

class ReplicateAdvancedTools(ToolBase):
    """Advanced Replicate integration with webhooks, chaining, and batch processing."""
    
    # Common model shortcuts
    MODEL_SHORTCUTS = {
        # Image generation
        "flux": "black-forest-labs/flux-1.1-pro",
        "flux_schnell": "black-forest-labs/flux-schnell",
        "flux_dev": "black-forest-labs/flux-dev",
        "sdxl": "stability-ai/sdxl",
        "ideogram": "ideogram-ai/ideogram-v2",
        "recraft": "recraft-ai/recraft-v3",
        
        # Video generation
        "kling": "kwaivgi/kling-v1.6-pro",
        "minimax": "minimax/video-01",
        "luma": "luma/ray",
        "runway": "runway/gen-3-turbo",
        "hunyuan": "tencent/hunyuan-video",
        "ltx": "lightricks/ltx-video",
        "mochi": "genmo/mochi-preview",
        "wan": "wavymulder/wan-2.1",
        "cogvideox": "thudm/cogvideox-5b",
        "stable_video": "stability-ai/stable-video-diffusion",
        
        # 3D generation
        "trellis": "firtoz/trellis",
        "mvdream": "adirik/mvdream",
        "rodin": "hyper3d/rodin",
        "wonder3d": "adirik/wonder3d",
        "hunyuan3d": "prunaai/hunyuan3d-2",
        "shape": "cjwbw/shap-e",
        
        # Image editing
        "inpaint": "stability-ai/stable-diffusion-inpainting",
        "upscale": "nightmareai/real-esrgan",
        "remove_bg": "cjwbw/rembg",
        "face_restore": "tencentarc/gfpgan",
        
        # Audio
        "musicgen": "meta/musicgen",
        "bark": "suno-ai/bark",
        "whisper": "openai/whisper",
        
        # Text/LLM
        "llama": "meta/meta-llama-3.1-405b-instruct",
        "llama_70b": "meta/meta-llama-3-70b-instruct",
    }
    
    def __init__(
        self,
        api_token: str = None,
        default_webhook_url: str = None,
        results_dir: str = "./data/replicate_results"
    ):
        self.api_token = api_token or os.getenv("REPLICATE_API_TOKEN")
        self.default_webhook_url = default_webhook_url
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        self.base_url = "https://api.replicate.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        # Track active predictions for chaining
        self._active_predictions: Dict[str, PredictionResult] = {}
    
    def _resolve_model(self, model: str) -> str:
        """Resolve model shortcut to full model identifier."""
        return self.MODEL_SHORTCUTS.get(model.lower(), model)
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        headers: Dict = None
    ) -> Dict[str, Any]:
        """Make API request to Replicate."""
        url = f"{self.base_url}{endpoint}"
        req_headers = {**self.headers, **(headers or {})}
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                url,
                headers=req_headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as response:
                result = await response.json()
                
                if response.status >= 400:
                    raise Exception(f"Replicate API error: {result}")
                
                return result
    
    # ==========================================
    # PREDICTIONS WITH WEBHOOKS
    # ==========================================
    
    @tool(
        name="replicate_create_prediction_async",
        description="Create a Replicate prediction with webhook for async notification",
        category="replicate"
    )
    async def create_prediction_async(
        self,
        model: str,
        input_params: Dict[str, Any],
        webhook_url: str = None,
        webhook_events: List[str] = None,
        timeout_minutes: int = None
    ) -> Dict[str, Any]:
        """
        Create a prediction with optional webhook notification.
        
        Args:
            model: Model name or shortcut (e.g., "flux", "kling", "trellis")
            input_params: Model input parameters
            webhook_url: HTTPS URL for webhook notifications
            webhook_events: Events to trigger webhook (start, output, logs, completed)
            timeout_minutes: Max time before auto-cancel
        """
        model = self._resolve_model(model)
        
        # Determine if using official model endpoint or version endpoint
        if "/" in model and ":" not in model:
            # Official model format: owner/model
            endpoint = f"/models/{model}/predictions"
        else:
            # Version format: needs version ID
            endpoint = "/predictions"
        
        payload = {"input": input_params}
        
        # Add webhook if provided
        webhook = webhook_url or self.default_webhook_url
        if webhook:
            payload["webhook"] = webhook
            payload["webhook_events_filter"] = webhook_events or ["start", "completed"]
        
        # Add timeout header
        headers = {}
        if timeout_minutes:
            headers["Cancel-After"] = f"{timeout_minutes}m"
        
        # Add version for non-official models
        if ":" in model:
            payload["version"] = model.split(":")[-1]
        
        try:
            result = await self._request("POST", endpoint, payload, headers)
            
            prediction = PredictionResult(
                prediction_id=result.get("id"),
                model=model,
                status=result.get("status"),
                created_at=result.get("created_at")
            )
            
            self._active_predictions[prediction.prediction_id] = prediction
            
            return {
                "success": True,
                "prediction_id": result.get("id"),
                "model": model,
                "status": result.get("status"),
                "webhook_configured": webhook is not None,
                "get_url": result.get("urls", {}).get("get"),
                "cancel_url": result.get("urls", {}).get("cancel"),
                "stream_url": result.get("urls", {}).get("stream")
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="replicate_get_prediction",
        description="Get the status and output of a prediction",
        category="replicate"
    )
    async def get_prediction(
        self,
        prediction_id: str
    ) -> Dict[str, Any]:
        """
        Get prediction status and output.
        
        Args:
            prediction_id: The prediction ID
        """
        try:
            result = await self._request("GET", f"/predictions/{prediction_id}")
            
            return {
                "prediction_id": result.get("id"),
                "model": result.get("model"),
                "status": result.get("status"),
                "output": result.get("output"),
                "error": result.get("error"),
                "metrics": result.get("metrics"),
                "created_at": result.get("created_at"),
                "completed_at": result.get("completed_at"),
                "logs": result.get("logs", "")[-500:]  # Last 500 chars of logs
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="replicate_wait_for_prediction",
        description="Wait for a prediction to complete and return the result",
        category="replicate"
    )
    async def wait_for_prediction(
        self,
        prediction_id: str,
        timeout_seconds: int = 300,
        poll_interval: int = 2
    ) -> Dict[str, Any]:
        """
        Wait for prediction to complete.
        
        Args:
            prediction_id: The prediction ID
            timeout_seconds: Max seconds to wait
            poll_interval: Seconds between status checks
        """
        start_time = asyncio.get_event_loop().time()
        
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout_seconds:
                return {
                    "success": False,
                    "error": "Timeout waiting for prediction",
                    "prediction_id": prediction_id
                }
            
            result = await self.get_prediction(prediction_id)
            status = result.get("status")
            
            if status == "succeeded":
                return {
                    "success": True,
                    "prediction_id": prediction_id,
                    "output": result.get("output"),
                    "metrics": result.get("metrics"),
                    "elapsed_seconds": elapsed
                }
            
            elif status in ["failed", "canceled"]:
                return {
                    "success": False,
                    "prediction_id": prediction_id,
                    "status": status,
                    "error": result.get("error")
                }
            
            await asyncio.sleep(poll_interval)
    
    @tool(
        name="replicate_cancel_prediction",
        description="Cancel a running prediction",
        category="replicate"
    )
    async def cancel_prediction(
        self,
        prediction_id: str
    ) -> Dict[str, Any]:
        """Cancel a prediction."""
        try:
            result = await self._request(
                "POST",
                f"/predictions/{prediction_id}/cancel"
            )
            return {
                "success": True,
                "prediction_id": prediction_id,
                "status": "canceled"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================
    # MODEL CHAINING
    # ==========================================
    
    @tool(
        name="replicate_run_chain",
        description="Run a chain of models where each output feeds into the next",
        category="replicate"
    )
    async def run_chain(
        self,
        chain: List[Dict[str, Any]],
        initial_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run a chain of models in sequence.
        
        Args:
            chain: List of chain steps, each with:
                - model: Model name/shortcut
                - input_mapping: Dict mapping "previous_output" or specific keys to input params
                - params: Additional fixed parameters
            initial_input: Initial input for first model
            
        Example:
            chain = [
                {"model": "flux", "params": {"prompt": "a cat"}},
                {"model": "upscale", "input_mapping": {"image": "output"}},
                {"model": "remove_bg", "input_mapping": {"image": "output"}}
            ]
        """
        results = []
        current_output = None
        
        for i, step in enumerate(chain):
            model = self._resolve_model(step.get("model"))
            params = step.get("params", {}).copy()
            input_mapping = step.get("input_mapping", {})
            
            # Build input from previous output and mapping
            if i == 0:
                # First step uses initial_input
                params.update(initial_input)
            else:
                # Map previous output to current input
                for target_key, source_key in input_mapping.items():
                    if source_key == "output":
                        # Use entire previous output
                        if isinstance(current_output, str):
                            params[target_key] = current_output
                        elif isinstance(current_output, list) and current_output:
                            params[target_key] = current_output[0]
                        elif isinstance(current_output, dict):
                            params[target_key] = current_output.get("output", current_output)
                    elif source_key.startswith("output."):
                        # Use specific key from output dict
                        key = source_key.split(".", 1)[1]
                        if isinstance(current_output, dict):
                            params[target_key] = current_output.get(key)
            
            logger.info(f"Chain step {i+1}: Running {model}")
            
            # Run prediction and wait
            create_result = await self.create_prediction_async(
                model=model,
                input_params=params
            )
            
            if not create_result.get("success"):
                return {
                    "success": False,
                    "error": f"Chain failed at step {i+1}: {create_result.get('error')}",
                    "completed_steps": results
                }
            
            # Wait for completion
            wait_result = await self.wait_for_prediction(
                create_result["prediction_id"],
                timeout_seconds=600
            )
            
            if not wait_result.get("success"):
                return {
                    "success": False,
                    "error": f"Chain failed at step {i+1}: {wait_result.get('error')}",
                    "completed_steps": results
                }
            
            current_output = wait_result.get("output")
            
            results.append({
                "step": i + 1,
                "model": model,
                "prediction_id": create_result["prediction_id"],
                "output": current_output
            })
        
        return {
            "success": True,
            "chain_length": len(chain),
            "final_output": current_output,
            "all_steps": results
        }
    
    @tool(
        name="replicate_create_pipeline",
        description="Create a reusable model pipeline definition",
        category="replicate"
    )
    async def create_pipeline(
        self,
        name: str,
        description: str,
        steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Save a pipeline definition for reuse.
        
        Args:
            name: Pipeline name
            description: What the pipeline does
            steps: List of pipeline steps
        """
        pipeline = {
            "name": name,
            "description": description,
            "steps": steps,
            "created_at": datetime.now().isoformat()
        }
        
        filepath = self.results_dir / f"pipeline_{name}.json"
        with open(filepath, "w") as f:
            json.dump(pipeline, f, indent=2)
        
        return {
            "success": True,
            "name": name,
            "steps": len(steps),
            "saved_to": str(filepath)
        }

    # ==========================================
    # BATCH PROCESSING
    # ==========================================
    
    @tool(
        name="replicate_batch_predictions",
        description="Run multiple predictions in parallel",
        category="replicate"
    )
    async def batch_predictions(
        self,
        model: str,
        inputs: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """
        Run multiple predictions in parallel.
        
        Args:
            model: Model name/shortcut
            inputs: List of input parameter dicts
            max_concurrent: Max concurrent predictions
        """
        model = self._resolve_model(model)
        
        results = []
        errors = []
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def run_single(idx: int, input_params: Dict):
            async with semaphore:
                try:
                    create_result = await self.create_prediction_async(
                        model=model,
                        input_params=input_params
                    )
                    
                    if not create_result.get("success"):
                        return {"index": idx, "error": create_result.get("error")}
                    
                    wait_result = await self.wait_for_prediction(
                        create_result["prediction_id"],
                        timeout_seconds=600
                    )
                    
                    if wait_result.get("success"):
                        return {
                            "index": idx,
                            "prediction_id": create_result["prediction_id"],
                            "output": wait_result.get("output")
                        }
                    else:
                        return {"index": idx, "error": wait_result.get("error")}
                        
                except Exception as e:
                    return {"index": idx, "error": str(e)}
        
        tasks = [run_single(i, inp) for i, inp in enumerate(inputs)]
        all_results = await asyncio.gather(*tasks)
        
        for res in all_results:
            if "error" in res:
                errors.append(res)
            else:
                results.append(res)
        
        return {
            "success": len(errors) == 0,
            "total": len(inputs),
            "succeeded": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }

    # ==========================================
    # MODEL DISCOVERY
    # ==========================================
    
    @tool(
        name="replicate_search_models",
        description="Search for models on Replicate",
        category="replicate"
    )
    async def search_models(
        self,
        query: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search for models.
        
        Args:
            query: Search query
            limit: Max results
        """
        try:
            result = await self._request(
                "GET",
                f"/search?query={query}&limit={limit}"
            )
            
            models = result.get("models", [])
            
            return {
                "query": query,
                "count": len(models),
                "models": [
                    {
                        "id": m.get("id") or f"{m.get('owner')}/{m.get('name')}",
                        "description": m.get("description", "")[:200],
                        "run_count": m.get("run_count"),
                        "cover_image": m.get("cover_image_url")
                    }
                    for m in models
                ]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="replicate_get_model_info",
        description="Get detailed information about a model",
        category="replicate"
    )
    async def get_model_info(
        self,
        model: str
    ) -> Dict[str, Any]:
        """
        Get model details including input schema.
        
        Args:
            model: Model name (owner/model)
        """
        model = self._resolve_model(model)
        
        try:
            result = await self._request("GET", f"/models/{model}")
            
            latest_version = result.get("latest_version", {})
            schema = latest_version.get("openapi_schema", {})
            input_schema = schema.get("components", {}).get("schemas", {}).get("Input", {})
            
            return {
                "model": model,
                "description": result.get("description"),
                "run_count": result.get("run_count"),
                "url": result.get("url"),
                "latest_version": latest_version.get("id"),
                "input_schema": input_schema.get("properties", {}),
                "required_inputs": input_schema.get("required", [])
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="replicate_list_predictions",
        description="List recent predictions",
        category="replicate"
    )
    async def list_predictions(
        self,
        limit: int = 50
    ) -> Dict[str, Any]:
        """List recent predictions."""
        try:
            result = await self._request("GET", "/predictions")
            
            predictions = result.get("results", [])[:limit]
            
            return {
                "count": len(predictions),
                "predictions": [
                    {
                        "id": p.get("id"),
                        "model": p.get("model"),
                        "status": p.get("status"),
                        "created_at": p.get("created_at"),
                        "completed_at": p.get("completed_at")
                    }
                    for p in predictions
                ]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================
    # TRAINING / FINE-TUNING
    # ==========================================
    
    @tool(
        name="replicate_create_training",
        description="Start a model training/fine-tuning job",
        category="replicate"
    )
    async def create_training(
        self,
        model: str,
        version: str,
        destination: str,
        input_params: Dict[str, Any],
        webhook_url: str = None
    ) -> Dict[str, Any]:
        """
        Start a training job.
        
        Args:
            model: Base model to train (owner/model)
            version: Model version ID
            destination: Destination for trained model (owner/model)
            input_params: Training inputs (train_data URL, etc.)
            webhook_url: Webhook for training completion
        """
        model = self._resolve_model(model)
        
        payload = {
            "destination": destination,
            "input": input_params
        }
        
        if webhook_url:
            payload["webhook"] = webhook_url
        
        try:
            result = await self._request(
                "POST",
                f"/models/{model}/versions/{version}/trainings",
                payload
            )
            
            return {
                "success": True,
                "training_id": result.get("id"),
                "status": result.get("status"),
                "destination": destination,
                "urls": result.get("urls", {})
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @tool(
        name="replicate_get_training",
        description="Get training job status",
        category="replicate"
    )
    async def get_training(
        self,
        training_id: str
    ) -> Dict[str, Any]:
        """Get training status."""
        try:
            result = await self._request("GET", f"/trainings/{training_id}")
            
            return {
                "training_id": result.get("id"),
                "status": result.get("status"),
                "model": result.get("model"),
                "output": result.get("output"),
                "error": result.get("error"),
                "logs": result.get("logs", "")[-1000:],
                "metrics": result.get("metrics"),
                "created_at": result.get("created_at"),
                "completed_at": result.get("completed_at")
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================
    # FILE HANDLING
    # ==========================================
    
    @tool(
        name="replicate_upload_file",
        description="Upload a file to Replicate for use as input",
        category="replicate"
    )
    async def upload_file(
        self,
        file_path: str,
        content_type: str = None
    ) -> Dict[str, Any]:
        """
        Upload a file to Replicate.
        
        Args:
            file_path: Path to local file
            content_type: MIME type (auto-detected if not provided)
        """
        path = Path(file_path)
        if not path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}
        
        # Detect content type
        if not content_type:
            ext = path.suffix.lower()
            content_types = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp",
                ".mp4": "video/mp4",
                ".mp3": "audio/mpeg",
                ".wav": "audio/wav",
                ".zip": "application/zip"
            }
            content_type = content_types.get(ext, "application/octet-stream")
        
        try:
            # Upload using multipart form
            url = f"{self.base_url}/files"
            
            async with aiohttp.ClientSession() as session:
                with open(path, "rb") as f:
                    data = aiohttp.FormData()
                    data.add_field(
                        "content",
                        f,
                        filename=path.name,
                        content_type=content_type
                    )
                    
                    async with session.post(
                        url,
                        headers={"Authorization": f"Bearer {self.api_token}"},
                        data=data
                    ) as response:
                        result = await response.json()
                        
                        if response.status >= 400:
                            return {"success": False, "error": str(result)}
                        
                        return {
                            "success": True,
                            "file_id": result.get("id"),
                            "url": result.get("urls", {}).get("get"),
                            "content_type": content_type
                        }
                        
        except Exception as e:
            return {"success": False, "error": str(e)}


# ==========================================
# WEBHOOK HANDLER (for FastAPI integration)
# ==========================================

class ReplicateWebhookHandler:
    """Handle incoming Replicate webhooks."""
    
    def __init__(self, secret: Optional[str] = None):
        self.secret = secret
        self.callbacks: Dict[str, List[Callable]] = {
            "start": [],
            "output": [],
            "logs": [],
            "completed": []
        }
    
    def on_start(self, callback: Callable):
        """Register callback for prediction start."""
        self.callbacks["start"].append(callback)
    
    def on_output(self, callback: Callable):
        """Register callback for prediction output."""
        self.callbacks["output"].append(callback)
    
    def on_completed(self, callback: Callable):
        """Register callback for prediction completion."""
        self.callbacks["completed"].append(callback)
    
    async def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming webhook payload."""
        prediction_id = payload.get("id")
        status = payload.get("status")
        
        # Determine event type
        if status == "starting":
            event = "start"
        elif status in ["succeeded", "failed", "canceled"]:
            event = "completed"
        elif payload.get("output"):
            event = "output"
        else:
            event = "logs"
        
        # Call registered callbacks
        for callback in self.callbacks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(payload)
                else:
                    callback(payload)
            except Exception as e:
                logger.error(f"Webhook callback error: {e}")
        
        return {
            "received": True,
            "prediction_id": prediction_id,
            "event": event,
            "status": status
        }


# Factory function
def create_replicate_advanced_tools(
    api_token: str = None,
    webhook_url: str = None
) -> ReplicateAdvancedTools:
    """Create ReplicateAdvancedTools instance."""
    return ReplicateAdvancedTools(
        api_token=api_token,
        default_webhook_url=webhook_url
    )
