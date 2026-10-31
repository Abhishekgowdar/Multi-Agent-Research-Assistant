"""Groq API client wrapper"""

from typing import Dict, List, Any
from tenacity import retry, retry_if_exception, stop_after_attempt
from groq import Groq
from loguru import logger

from src.llm.common import groq_token_limiter, is_transient_error, parse_json_reply, wait_for_retry
from src.utils.config import settings


def _settle_usage(reservation: list, response: Any, max_tokens: int) -> None:
    """Record the completion tokens Groq reports, or the reserved amount if none"""
    used = getattr(getattr(response, 'usage', None), 'completion_tokens', None)
    groq_token_limiter.settle(reservation, used if isinstance(used, (int, float)) else max_tokens)


# Budget reserved before each call; the actual usage is settled afterwards
RESERVE_TOKENS_PER_CALL = settings.get('rate_limits.groq_reserve_tokens_per_call', 800)


class GroqClient:
    """Wrapper for Groq API (FREE and FAST!)"""

    def __init__(self, model_name: str = "qwen/qwen3.8-27b"):
        """Initialize Groq client

        Args:
            model_name: Model to use
                - qwen/qwen3.8-27b (available in your account)
                - openai/gpt-oss-20b (alternative)
                - openai/gpt-oss-120b (larger model)
        """
        self.client = Groq(api_key=settings.groq_api_key, max_retries=0)
        self.model_name = model_name
        self.last_truncated = False

        logger.info(f"Initialized Groq client with model: {model_name}")

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
        max_tokens: int = 400,  # Reduced to 400 to stay within FREE tier limits (1000 OTPM)
        json_mode: bool = False
    ) -> str:
        """Generate text using Groq

        Args:
            prompt: The prompt to send
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            json_mode: Whether to expect JSON output

        Returns:
            Generated text
        """
        messages = [{"role": "user", "content": prompt}]

        # Add JSON instruction if needed
        if json_mode:
            messages[0]["content"] = f"{prompt}\n\nProvide your response in valid JSON format."

        logger.debug(f"Sending prompt to {self.model_name} (length: {len(prompt)} chars)")

        reservation = groq_token_limiter.acquire(min(max_tokens, RESERVE_TOKENS_PER_CALL))
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            groq_token_limiter.settle(reservation, 0)
            logger.error(f"Error generating with Groq: {e}")
            raise

        _settle_usage(reservation, response, max_tokens)
        choice = response.choices[0]
        self.last_truncated = choice.finish_reason == "length"
        if self.last_truncated:
            logger.warning(f"Groq reply hit the {max_tokens}-token limit and was cut off")
        logger.debug(f"Received response (finish reason: {choice.finish_reason})")

        return (choice.message.content or "").strip()

    def generate_json(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 800  # Increased to 800 for complete JSON (still within limits)
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
        max_tokens: int = 400  # Reduced for FREE tier (1000 OTPM limit)
    ) -> str:
        """Multi-turn conversation

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated response
        """
        reservation = groq_token_limiter.acquire(min(max_tokens, RESERVE_TOKENS_PER_CALL))
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            groq_token_limiter.settle(reservation, 0)
            logger.error(f"Error in chat: {e}")
            raise

        _settle_usage(reservation, response, max_tokens)
        return (response.choices[0].message.content or "").strip()

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)

        Args:
            text: Text to estimate

        Returns:
            Approximate token count
        """
        # Rough estimate: ~4 characters per token
        return len(text) // 4
