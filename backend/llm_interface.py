"""
Abstract interface for LLM providers
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
import json


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def generate_response(self, prompt: str, max_tokens: int = 10000) -> Dict[str, Any]:
        """
        Generate a response from the LLM
        
        Args:
            prompt: The prompt to send to the LLM
            max_tokens: Maximum tokens in the response
            
        Returns:
            Dict containing the parsed JSON response from the LLM
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the name of the provider"""
        pass
    
    def _clean_and_parse_json(self, response_text: str) -> Dict[str, Any]:
        """
        Clean up and parse JSON response from LLM
        
        Args:
            response_text: Raw text response from LLM
            
        Returns:
            Parsed JSON dictionary
        """
        # Clean up common JSON formatting issues
        cleaned = response_text.strip()
        
        # Check if response looks like an error (HTML, etc.)
        if cleaned.startswith('<'):
            raise ValueError(f"Received HTML/XML instead of JSON. Response starts with: {cleaned[:100]}")
        
        # Remove markdown code blocks
        if '```json' in cleaned:
            # Extract content between ```json and ```
            parts = cleaned.split('```json')
            if len(parts) > 1:
                json_part = parts[1].split('```')[0]
                cleaned = json_part
        elif '```' in cleaned:
            # Extract content between ``` and ```
            parts = cleaned.split('```')
            if len(parts) >= 3:
                # Take the content between first ``` and second ```
                cleaned = parts[1]
        
        cleaned = cleaned.strip()
        
        # Validate it looks like JSON before parsing
        if not (cleaned.startswith('{') or cleaned.startswith('[')):
            raise ValueError(f"Response does not appear to be JSON. Starts with: {cleaned[:100]}")
        
        # Parse JSON
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON: {str(e)}. Content preview: {cleaned[:200]}")
