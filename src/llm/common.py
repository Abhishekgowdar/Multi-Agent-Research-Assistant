"""Shared LLM helpers: request pacing, retry policy, and JSON reply parsing"""

import json
import re
import threading
import time
from collections import deque
from typing import Any, Dict

from loguru import logger
from tenacity import RetryCallState

from src.utils.config import settings

TRANSIENT_STATUS_CODES = {408, 409, 429}


class SlidingWindowLimiter:
    """Blocks callers so the units used in the last window stay under the limit"""

    def __init__(self, limit: float, window_seconds: float = 60.0):
        self.limit = float(limit)
        self.window = window_seconds
        self._events = deque()  # each entry is [timestamp, units]
        self._lock = threading.Lock()

    def acquire(self, units: float = 1.0) -> list:
        """Wait until `units` fit in the window, reserve them, and return the reservation"""
        units = min(float(units), self.limit)
        while True:
            with self._lock:
                now = time.monotonic()
                while self._events and now - self._events[0][0] >= self.window:
                    self._events.popleft()
                used = sum(entry[1] for entry in self._events)
                if used + units <= self.limit:
                    entry = [now, units]
                    self._events.append(entry)
                    return entry
                wait = self.window - (now - self._events[0][0])
            time.sleep(max(wait, 0.05))

    def settle(self, entry: list, units: float) -> None:
        """Replace a reservation with the units actually used"""
        with self._lock:
            entry[1] = float(units)


groq_token_limiter = SlidingWindowLimiter(settings.get('rate_limits.groq_output_tokens_per_minute', 1000))
gemini_request_limiter = SlidingWindowLimiter(settings.get('rate_limits.gemini_requests_per_minute', 15))


def is_transient_error(exc: BaseException) -> bool:
    """True for rate limits, timeouts, connection failures, and server errors"""
    status = getattr(exc, 'status_code', None)
    if not isinstance(status, int):
        status = getattr(exc, 'code', None)
    if isinstance(status, int):
        return status in TRANSIENT_STATUS_CODES or status >= 500
    name = type(exc).__name__.lower()
    return any(word in name for word in ('timeout', 'connection', 'unavailable', 'ratelimit', 'resourceexhausted'))


def wait_for_retry(retry_state: RetryCallState) -> float:
    """Honor a Retry-After header when present, otherwise back off up to one minute"""
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    headers = getattr(getattr(exc, 'response', None), 'headers', None) or {}
    try:
        return min(max(float(headers.get('retry-after', '')), 1.0), 120.0)
    except (TypeError, ValueError):
        return min(2.0 ** retry_state.attempt_number, 60.0)


def parse_json_reply(text: str) -> Dict[str, Any]:
    """Parse the first JSON object in a model reply; returns {} if none can be parsed"""
    body = text
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fenced:
        body = fenced.group(1)
    start, end = body.find("{"), body.rfind("}")
    if start == -1 or end <= start:
        logger.error("No JSON object found in model reply")
        logger.debug(f"Raw response: {text}")
        return {}
    try:
        parsed = json.loads(body[start:end + 1])
    except json.JSONDecodeError as exc:
        logger.error(f"Failed to parse JSON response: {exc}")
        logger.debug(f"Raw response: {text}")
        return {}
    return parsed if isinstance(parsed, dict) else {}
