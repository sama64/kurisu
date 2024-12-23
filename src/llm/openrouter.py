import httpx
from typing import List, Dict
from config.config import config
import logging

logger = logging.getLogger(__name__)

class OpenRouterClient:
    def __init__(self):
        self.api_key = config.OPENROUTER_API_KEY
        self.model = config.OPENROUTER_MODEL
        self.base_url = "https://openrouter.ai/api/v1"
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is not set in environment variables")
        
    async def generate_response(self, messages: List[Dict], temperature: float = 0.7) -> str:
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://github.com/your-username/kurisu-bot",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
                
        except httpx.TimeoutException:
            logger.error("Request to OpenRouter timed out")
            return "I apologize, but I'm having trouble thinking right now. Could you try again in a moment?"
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error occurred: {e}")
            return "Sorry, I encountered an error while processing your message. Please try again later."
            
        except Exception as e:
            logger.error(f"Unexpected error in generate_response: {e}", exc_info=True)
            return "An unexpected error occurred. Please try again later." 