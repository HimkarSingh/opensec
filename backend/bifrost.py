import os
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import litellm

logger = logging.getLogger(__name__)

# Initialize litellm caching (in-memory simple cache)
litellm.cache = litellm.Cache(type="local")
litellm.success_callback = ["cache_hit"] # Track if it hit cache

bifrost_app = APIRouter()

class BifrostRequest(BaseModel):
    model: str = "glm-5:cloud"  # Default model
    prompt: str
    temperature: float = 0.7

class BifrostGateway:
    """
    Python-native implementation of the Bifrost architectural pattern.
    Provides Unified Routing, Caching, and Failover for LLM requests.
    """
    @staticmethod
    def evaluate(prompt: str, model_name: str = "glm-5:cloud") -> str:
        """
        Route the request to the specified model with automatic fallback
        and semantic caching enabled.
        """
        if model_name == "glm-5:cloud":
            # The environment variable is "http://OLLAMA_HOST/api/generate"
            base_url = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")
            
            # Litellm needs just the host for 'ollama/' prefix
            if base_url.endswith("/api/generate"):
                api_base = base_url.replace("/api/generate", "")
            elif base_url.endswith("/v1"):
                api_base = base_url.replace("/v1", "")
            else:
                api_base = base_url
                
            api_key = os.getenv("OLLAMA_API_KEY", "")
            # Properly tell litellm it's an ollama deployment, appending the custom tag
            model = "ollama/glm-5:cloud"
            
            # Define failover models (The true power of Bifrost)
            # We add `ollama/llama3` as a local fallback in case `glm-5:cloud` fails.
            fallbacks = [{"model": "ollama/llama3", "api_base": api_base}]
            
        elif model_name == "m2.5":
            # Minimax Coding Plan - uses different endpoint and model name
            # Coding Plan uses api.minimax.io (not api.minimax.chat)
            model = "MiniMax-M2.5"
            api_base = "https://api.minimax.io/v1"
            api_key = os.getenv("MINIMAX_API_KEY", "")
            
            fallbacks = [{"model": "ollama/glm-5:cloud", "api_base": "http://localhost:11434"}]
            
        try:
            logger.info(f"[Bifrost Gateway] Routing request to: {model} with base {api_base}")
            print(f"[BIFROST DEBUG] Routing to: {model} at {api_base}")
            # Litellm handles the standardized OpenAI format across all providers
            # caching=True enables exactly what Bifrost offers for identical requests
            response = litellm.completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                api_base=api_base,
                api_key=api_key,
                fallbacks=fallbacks,
                caching=True, 
                temperature=0.7
            )
            print(f"[BIFROST DEBUG] Response received successfully.")
            
            # Check if this was intercepted by the semantic cache
            is_cached = getattr(response, '_hidden_params', {}).get('cache_hit', False)
            if is_cached:
                 logger.info(f"[Bifrost Gateway] ⚡ CACHE HIT (Skipped Provider API)")

            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"[Bifrost Gateway] All routing failed: {e}")
            raise e

@bifrost_app.post("/v1/chat/completions")
async def bifrost_chat_proxy(req: BifrostRequest):
    """
    OpenAI-compatible endpoint that agents can use directly through the Gateway.
    """
    try:
         result = BifrostGateway.evaluate(req.prompt, req.model)
         # Format as OpenAI compatible response for seamless agent use
         return {
             "id": "bifrost-123",
             "object": "chat.completion",
             "model": req.model,
             "choices": [
                 {
                     "index": 0,
                     "message": {
                         "role": "assistant",
                         "content": result
                     },
                     "finish_reason": "stop"
                 }
             ]
         }
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))
