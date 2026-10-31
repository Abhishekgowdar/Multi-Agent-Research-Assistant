"""Small SQLite cache with time-based expiry for search and LLM results"""

import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from src.utils.config import settings

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class SQLiteCache:
    """Key/value cache stored in one SQLite file"""

    def __init__(self, path: Path, ttl_seconds: float):
        self.path = Path(path)
        self.ttl_seconds = ttl_seconds
        self.path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.path)
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS cache "
                "(key TEXT PRIMARY KEY, stored_at REAL NOT NULL, value TEXT NOT NULL)"
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def make_key(*parts: Any) -> str:
        """Stable hash of the given parts"""
        raw = json.dumps(parts, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Stored value if present and not expired, else None"""
        conn = sqlite3.connect(self.path)
        try:
            row = conn.execute("SELECT stored_at, value FROM cache WHERE key = ?", (key,)).fetchone()
        finally:
            conn.close()

        if row is None or time.time() - row[0] > self.ttl_seconds:
            return None
        return json.loads(row[1])

    def set(self, key: str, value: Any) -> None:
        """Store a JSON-serializable value"""
        conn = sqlite3.connect(self.path)
        try:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, stored_at, value) VALUES (?, ?, ?)",
                (key, time.time(), json.dumps(value, default=str)),
            )
            conn.commit()
        finally:
            conn.close()


_instance: Optional[SQLiteCache] = None


def get_cache() -> Optional[SQLiteCache]:
    """Shared cache from settings, or None when caching is disabled or unavailable"""
    global _instance
    if not settings.get('cache.enabled', False):
        return None

    if _instance is None:
        path = PROJECT_ROOT / str(settings.get('cache.path', 'data/cache.db'))
        ttl_seconds = float(settings.get('cache.ttl_hours', 168)) * 3600
        try:
            _instance = SQLiteCache(path, ttl_seconds)
        except (OSError, sqlite3.Error) as e:
            logger.warning(f"Cache unavailable, continuing without it: {e}")
            return None
    return _instance
