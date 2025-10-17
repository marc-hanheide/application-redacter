"""
Ollama LLM provider implementation
"""
import requests
import logging
from typing import Dict, Any
from llm_interface import LLMProvider

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider"""
    
    def __init__(self, base_url: str = "http://ollama:11434", model: str = "llama3.1"):
        """
        Initialize Ollama provider
        
        Args:
            base_url: Base URL for Ollama API
            model: Model identifier to use (must be pulled in Ollama)
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        logger.info(f"Initialized Ollama provider with model: {model} at {base_url}")
    
    def generate_response(self, prompt: str, max_tokens: int = 10000) -> Dict[str, Any]:
        """
        Generate a response from Ollama API
        
        Args:
            prompt: The prompt to send to Ollama
            max_tokens: Maximum tokens in the response (mapped to num_predict)
            
        Returns:
            Dict containing the parsed JSON response
        """
        try:
            logger.info(f"Sending request to Ollama API (model: {self.model}, max_tokens: {max_tokens})")
            
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.1,  # Lower temperature for more consistent structured output
                }
            }
            
            response = requests.post(url, json=payload, timeout=300)
            
            # Handle 404 errors specifically (model not found)
            if response.status_code == 404:
                logger.error(f"Ollama model '{self.model}' not found. Please pull the model first.")
                logger.error(f"Run: docker exec phd-redaction-ollama ollama pull {self.model}")
                raise ValueError(
                    f"Ollama model '{self.model}' not found. "
                    f"Please pull it first: docker exec phd-redaction-ollama ollama pull {self.model}"
                )
            
            response.raise_for_status()
            
            result = response.json()
            response_text = result.get('response', '').strip()
            
            logger.info(f"Received response from Ollama API ({len(response_text)} chars)")
            
            # Log preview for debugging
            preview = response_text[:200].replace('\n', ' ')
            logger.debug(f"Response preview: {preview}...")
            
            # Parse and return JSON
            parsed = self._clean_and_parse_json(response_text)
            logger.info("Successfully parsed JSON response")
            return parsed
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot connect to Ollama at {self.base_url}")
            logger.error(f"Make sure Ollama service is running: docker compose ps ollama")
            raise
        except requests.exceptions.Timeout as e:
            logger.error(f"Ollama request timed out after 300s")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API request error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error processing Ollama response: {str(e)}")
            logger.error(f"Response text that failed to parse: {response_text[:500] if 'response_text' in locals() else 'N/A'}")
            raise
    
    def get_provider_name(self) -> str:
        """Return the name of the provider"""
        return f"Ollama ({self.model})"
