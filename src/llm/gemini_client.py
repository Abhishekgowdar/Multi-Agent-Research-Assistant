"""Google Gemini API client wrapper"""

import time
from typing import Dict, List, Optional, Any
from tenacity import retry, retry_if_exception, stop_after_attempt
import google.generativeai as genai
from loguru import logger

from src.llm.common import gemini_request_limiter, is_transient_error, parse_json_reply, wait_for_retry
from src.utils.config import settings


def _hit_token_limit(response: Any) -> bool:
    """True if Gemini stopped because it reached the output token limit"""
    try:
        reason = response.candidates[0].finish_reason
    except (AttributeError, IndexError, TypeError):
        return False
    return str(getattr(reason, "name", reason)).upper().endswith("MAX_TOKENS")


class GeminiClient:
    """Wrapper for Google Gemini API"""

    def __init__(self, model_name: str = "gemini-1.5-flash"):
        """Initialize Gemini client

        Args:
            model_name: Model to use (gemini-1.5-flash or gemini-1.5-pro)
        """
        genai.configure(api_key=settings.gemini_api_key)

        # Map to ACTUAL available models from the user's API key
        model_mapping = {
            "gemini-1.5-flash": "gemini-flash-latest",
            "gemini-1.5-pro": "gemini-pro-latest",
            "gemini-pro": "gemini-pro-latest",
            "gemini-2.5-flash": "gemini-2.5-flash",
            "gemini-2.5-pro": "gemini-2.5-pro"
        }

        # Default to gemini-flash-latest (most compatible)
        self.model_name = model_mapping.get(model_name, "gemini-flash-latest")
        self.model = genai.GenerativeModel(self.model_name)
        self.last_truncated = False

        # Safety settings for research content
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]

        logger.info(f"Initialized Gemini client with model: {model_name}")

    @retry(
        retry=retry_if_exception(is_transient_error),
        stop=stop_after_attempt(5),
        wait=wait_for_retry,
        reraise=True
    )
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False
    ) -> str:
        """Generate text using Gemini

        Args:
            prompt: The prompt to send
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            json_mode: Whether to expect JSON output

        Returns:
            Generated text
        """
        try:
            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )

            # Add JSON instruction if needed
            if json_mode:
                prompt = f"{prompt}\n\nProvide your response in valid JSON format."

            logger.debug(f"Sending prompt to {self.model_name} (length: {len(prompt)} chars)")

            gemini_request_limiter.acquire(1)
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=self.safety_settings
            )
            self.last_truncated = _hit_token_limit(response)
            if self.last_truncated:
                logger.warning("Gemini reply hit the output token limit and was cut off")

            if not response.text:
                logger.warning("Empty response from Gemini")
                return ""

            result = response.text.strip()
            logger.debug(f"Received response (length: {len(result)} chars)")

            return result

        except Exception as e:
            logger.error(f"Error generating with Gemini: {e}")
            raise

    def generate_json(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Generate JSON response

        Args:
            prompt: The prompt to send
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Parsed JSON response
        """
        response = self.generate(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True
        )

        return parse_json_reply(response)

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """Multi-turn conversation

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated response
        """
        # Convert messages to single prompt for now
        # (Gemini chat API is slightly different, this is simplified)
        prompt_parts = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'system':
                prompt_parts.append(f"System: {content}")
            elif role == 'user':
                prompt_parts.append(f"User: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")

        prompt = "\n\n".join(prompt_parts)
        return self.generate(prompt, temperature, max_tokens)

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)

        Args:
            text: Text to estimate

        Returns:
            Approximate token count
        """
        # Rough estimate: ~4 characters per token
        return len(text) // 4
