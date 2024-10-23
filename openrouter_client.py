import aiohttp
import json
import logging
from typing import List, Dict, Any, Optional
import backoff
import asyncio
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenRouterClient:
    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    def should_retry(self, e):
        """Determine if we should retry the request based on the error."""
        if isinstance(e, aiohttp.ClientResponseError):
            # Retry on 526 (Invalid SSL) and 5xx errors
            return e.status == 526 or (500 <= e.status < 600)
        return isinstance(e, (aiohttp.ClientError, asyncio.TimeoutError))

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=5,  # Increased from 3 to 5
        max_time=60,  # Increased from 30 to 60
        giveup=lambda e: not OpenRouterClient.should_retry(e)
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
                    timeout=timeout,
                    ssl=True  # Explicitly enable SSL
                ) as response:
                    if response.status == 429:  # Rate limit error
                        retry_after = int(response.headers.get('Retry-After', 1))
                        logger.warning(f"Rate limited. Waiting {retry_after} seconds.")
                        await asyncio.sleep(retry_after)
                        raise aiohttp.ClientError("Rate limited")
                    
                    if response.status == 526:
                        logger.warning("SSL handshake failed (526). Retrying...")
                        raise aiohttp.ClientError("SSL handshake failed")

                    response_text = await response.text()
                    
                    try:
                        result = json.loads(response_text)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON response: {response_text}")
                        raise ValueError(f"Invalid JSON response from API: {response_text[:200]}")

                    # Check for error response
                    if isinstance(result, dict) and 'error' in result:
                        error_msg = result['error'].get('message', 'Unknown error')
                        error_code = result['error'].get('code', 'unknown')
                        logger.error(f"API error {error_code}: {error_msg}")
                        
                        if error_code == 526:
                            # Specific handling for 526 errors
                            logger.warning("SSL error (526) detected. Retrying...")
                            await asyncio.sleep(3)  # Short delay before retry
                            raise aiohttp.ClientError(f"SSL error: {error_msg}")
                        
                        raise ValueError(f"API error {error_code}: {error_msg}")

                    # Log the raw response for debugging
                    logger.debug(f"Raw API response: {result}")
                    
                    # Validate response structure
                    if not isinstance(result, dict):
                        raise ValueError(f"Expected dict response, got {type(result)}")
                    
                    if 'choices' not in result:
                        logger.error(f"Missing 'choices' in response: {result}")
                        raise ValueError("API response missing 'choices' field")
                    
                    if not result['choices'] or not isinstance(result['choices'], list):
                        logger.error(f"Invalid 'choices' format in response: {result}")
                        raise ValueError("Invalid 'choices' format in API response")
                    
                    if 'message' not in result['choices'][0]:
                        logger.error(f"Missing 'message' in first choice: {result['choices'][0]}")
                        raise ValueError("API response missing 'message' in first choice")
                    
                    if 'content' not in result['choices'][0]['message']:
                        logger.error(f"Missing 'content' in message: {result['choices'][0]['message']}")
                        raise ValueError("API response missing 'content' in message")

                    return {
                        'id': result.get('id', ''),
                        'choices': [{
                            'message': {
                                'content': result['choices'][0]['message']['content']
                            }
                        }],
                        'usage': result.get('usage', {})
                    }

            except asyncio.TimeoutError as e:
                logger.error(f"Request timed out after {timeout} seconds")
                raise asyncio.TimeoutError(f"Request timed out after {timeout} seconds") from e
            
            except aiohttp.ClientResponseError as e:
                logger.error(f"HTTP error {e.status}: {e.message}")
                raise
            
            except aiohttp.ClientError as e:
                logger.error(f"Request failed: {str(e)}")
                raise
            
            except (KeyError, ValueError, json.JSONDecodeError) as e:
                logger.error(f"Failed to parse API response: {str(e)}")
                raise ValueError(f"Failed to parse API response: {str(e)}") from e
            
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise

    async def fetch_usage(self, completion_id: str) -> Dict[str, Any]:
        """Fetch usage statistics for a completion."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_url}/usage/{completion_id}",
                    headers=self.headers,
                    ssl=True
                ) as response:
                    response.raise_for_status()
                    return await response.json()
            except Exception as e:
                logger.error(f"Failed to fetch usage stats: {str(e)}")
                raise