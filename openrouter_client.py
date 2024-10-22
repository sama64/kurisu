import aiohttp
import json
from typing import List, Dict, Any, Optional
import backoff
import asyncio
from datetime import datetime

class OpenRouterClient:
    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            # "HTTP-Referer": "https://your-site.com",  
            # "X-Title": "Your-App-Name",  # Replace with your app name
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=3,
        max_time=30
    )
    async def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 150,
        frequency_penalty: float = 0.4,
        presence_penalty: float = 0.3,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """
        Create a chat completion using OpenRouter API with retry logic and timeout.
        """
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "frequency_penalty": frequency_penalty,
                "presence_penalty": presence_penalty
            }

            try:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=timeout
                ) as response:
                    if response.status == 429:  # Rate limit error
                        retry_after = int(response.headers.get('Retry-After', 1))
                        await asyncio.sleep(retry_after)
                        raise aiohttp.ClientError("Rate limited")
                    
                    response.raise_for_status()
                    result = await response.json()
                    
                    return {
                        'id': result.get('id'),
                        'choices': [{
                            'message': {
                                'content': result['choices'][0]['message']['content']
                            }
                        }],
                        'usage': result.get('usage', {})
                    }

            except asyncio.TimeoutError:
                raise asyncio.TimeoutError("Request timed out")
            
            except aiohttp.ClientError as e:
                raise aiohttp.ClientError(f"Request failed: {str(e)}")

    async def fetch_usage(self, completion_id: str) -> Dict[str, Any]:
        """Fetch usage statistics for a completion."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/usage/{completion_id}",
                headers=self.headers
            ) as response:
                response.raise_for_status()
                return await response.json()