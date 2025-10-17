"""
Anthropic Claude LLM provider implementation
"""
import anthropic
import logging
from typing import Dict, Any
from llm_interface import LLMProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider"""
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize Anthropic provider
        
        Args:
            api_key: Anthropic API key
            model: Model identifier to use
        """
        if not api_key:
            raise ValueError("Anthropic API key is required")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        logger.info(f"Initialized Anthropic provider with model: {model}")
    
    def generate_response(self, prompt: str, max_tokens: int = 10000) -> Dict[str, Any]:
        """
        Generate a response from Claude API
        
        Args:
            prompt: The prompt to send to Claude
            max_tokens: Maximum tokens in the response
            
        Returns:
            Dict containing the parsed JSON response
        """
        try:
            logger.info(f"Sending request to Claude API (model: {self.model}, max_tokens: {max_tokens})")
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text.strip()
            logger.info(f"Received response from Claude API ({len(response_text)} chars)")
            
            # Log the first part of the response for debugging
            preview = response_text[:200].replace('\n', ' ')
            logger.debug(f"Response preview: {preview}...")
            
            # Parse and return JSON
            result = self._clean_and_parse_json(response_text)
            logger.info("Successfully parsed JSON response")
            return result
            
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e.status_code} - {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error processing Anthropic response: {str(e)}")
            logger.error(f"Response text that failed to parse: {response_text[:500] if 'response_text' in locals() else 'N/A'}")
            raise
    
    def get_provider_name(self) -> str:
        """Return the name of the provider"""
        return f"Anthropic Claude ({self.model})"
