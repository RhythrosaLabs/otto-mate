"""
Ollama Local LLM Integration

Provides support for running local LLMs via Ollama.
No API keys needed - runs completely offline!

Installation: https://ollama.ai/download
"""

import os
import json
from typing import Optional, List, Dict, Any, AsyncGenerator
import httpx
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class OllamaModel(BaseModel):
    """Ollama model information."""
    name: str
    size: int
    digest: str
    modified_at: str
    details: Optional[Dict[str, Any]] = None


class OllamaMessage(BaseModel):
    """Chat message for Ollama."""
    role: str  # 'user', 'assistant', or 'system'
    content: str


class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.timeout = httpx.Timeout(120.0, read=300.0)  # Long timeout for model generation
    
    async def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except:
            return False
    
    async def list_models(self) -> List[OllamaModel]:
        """List all installed models."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return [OllamaModel(**model) for model in data.get("models", [])]
        except Exception as e:
            logger.error(f"Error listing Ollama models: {e}")
        return []
    
    async def pull_model(self, model_name: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Pull (download) a model from Ollama library.
        
        Yields progress updates as the model downloads.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/pull",
                    json={"name": model_name}
                ) as response:
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                yield json.loads(line)
                            except json.JSONDecodeError:
                                pass
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {e}")
            yield {"error": str(e)}
    
    async def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> AsyncGenerator[str, None]:
        """
        Generate text with an Ollama model.
        
        Args:
            model: Model name (e.g., 'llama2', 'mistral', 'codellama')
            prompt: The user's prompt
            system: Optional system prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
        
        Yields:
            Generated text chunks if streaming, else full response
        """
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": stream,
                "options": {
                    "temperature": temperature,
                }
            }
            
            if system:
                payload["system"] = system
            
            if max_tokens:
                payload["options"]["num_predict"] = max_tokens
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if stream:
                    async with client.stream(
                        "POST",
                        f"{self.base_url}/api/generate",
                        json=payload
                    ) as response:
                        async for line in response.aiter_lines():
                            if line.strip():
                                try:
                                    data = json.loads(line)
                                    if "response" in data:
                                        yield data["response"]
                                    if data.get("done"):
                                        break
                                except json.JSONDecodeError:
                                    pass
                else:
                    response = await client.post(
                        f"{self.base_url}/api/generate",
                        json=payload
                    )
                    if response.status_code == 200:
                        data = response.json()
                        yield data.get("response", "")
                    else:
                        logger.error(f"Ollama generate error: {response.status_code} - {response.text}")
                        yield f"Error: {response.status_code}"
                        
        except Exception as e:
            logger.error(f"Error generating with Ollama: {e}")
            yield f"Error: {str(e)}"
    
    async def chat(
        self,
        model: str,
        messages: List[OllamaMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> AsyncGenerator[str, None]:
        """
        Chat with an Ollama model using message history.
        
        Args:
            model: Model name
            messages: List of chat messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
        
        Yields:
            Generated text chunks if streaming, else full response
        """
        try:
            payload = {
                "model": model,
                "messages": [msg.dict() for msg in messages],
                "stream": stream,
                "options": {
                    "temperature": temperature,
                }
            }
            
            if max_tokens:
                payload["options"]["num_predict"] = max_tokens
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if stream:
                    async with client.stream(
                        "POST",
                        f"{self.base_url}/api/chat",
                        json=payload
                    ) as response:
                        async for line in response.aiter_lines():
                            if line.strip():
                                try:
                                    data = json.loads(line)
                                    if "message" in data and "content" in data["message"]:
                                        yield data["message"]["content"]
                                    if data.get("done"):
                                        break
                                except json.JSONDecodeError:
                                    pass
                else:
                    response = await client.post(
                        f"{self.base_url}/api/chat",
                        json=payload
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]
                    else:
                        logger.error(f"Ollama chat error: {response.status_code} - {response.text}")
                        yield f"Error: {response.status_code}"
                        
        except Exception as e:
            logger.error(f"Error chatting with Ollama: {e}")
            yield f"Error: {str(e)}"
    
    async def embeddings(self, model: str, text: str) -> List[float]:
        """Generate embeddings for text."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": model, "prompt": text}
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("embedding", [])
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
        return []
    
    async def delete_model(self, model_name: str) -> bool:
        """Delete a model."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.delete(
                    f"{self.base_url}/api/delete",
                    json={"name": model_name}
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Error deleting model: {e}")
        return False


# Recommended models for different use cases
RECOMMENDED_MODELS = {
    "general": {
        "llama2": "Meta's Llama 2 - Good all-around model (7B)",
        "llama2:13b": "Llama 2 13B - Better quality, slower",
        "mistral": "Mistral 7B - Fast and capable",
        "mixtral": "Mixtral 8x7B - Very capable mixture of experts",
    },
    "coding": {
        "codellama": "Code Llama - Specialized for code (7B)",
        "codellama:13b": "Code Llama 13B - Better code generation",
        "deepseek-coder": "DeepSeek Coder - Excellent for coding",
    },
    "creative": {
        "openhermes": "OpenHermes - Creative writing",
        "neural-chat": "Intel Neural Chat - Conversational",
    },
    "fast": {
        "tinyllama": "Tiny Llama - 1.1B, very fast",
        "phi": "Microsoft Phi - 2.7B, efficient",
    }
}


def get_recommended_models() -> Dict[str, Dict[str, str]]:
    """Get dictionary of recommended models by category."""
    return RECOMMENDED_MODELS


# Global client instance
_ollama_client: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    """Get or create the global Ollama client."""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client


async def is_ollama_available() -> bool:
    """Check if Ollama is available on the system."""
    client = get_ollama_client()
    return await client.is_available()
