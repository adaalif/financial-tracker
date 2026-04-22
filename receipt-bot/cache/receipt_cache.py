"""
In-memory receipt cache with TTL expiration.

Designed as a temporary store bridging the upload → preview → confirm flow.
Structure mirrors future Redis usage so migration will be straightforward:
  key:   "receipt:{uuid}"
  value: ReceiptData dict + metadata
"""

import time
import uuid
from typing import Any, Optional

from utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_TTL_SECONDS = 3600  # 10 minutes


class ReceiptCache:
    """Dict-based in-memory cache with per-entry TTL expiration."""

    def __init__(self, default_ttl: int = DEFAULT_TTL_SECONDS) -> None:
        self._store: dict[str, dict[str, Any]] = {}
        self._default_ttl = default_ttl

    def _make_key(self, receipt_id: str) -> str:
        """Mirrors Redis key format: receipt:{id}"""
        return f"receipt:{receipt_id}"

    def _is_expired(self, entry: dict[str, Any]) -> bool:
        return time.time() > entry["expires_at"]

    def generate_id(self) -> str:
        """Generate a unique receipt ID."""
        return str(uuid.uuid4())

    def set(self, receipt_id: str, data: dict[str, Any], ttl: Optional[int] = None) -> None:
        """Store receipt data with TTL expiration."""
        key = self._make_key(receipt_id)
        self._store[key] = {
            "data": data,
            "created_at": time.time(),
            "expires_at": time.time() + (ttl or self._default_ttl),
        }
        logger.info("Cache SET", receipt_id=receipt_id, ttl=ttl or self._default_ttl)

    def get(self, receipt_id: str) -> Optional[dict[str, Any]]:
        """Retrieve receipt data. Returns None if missing or expired."""
        key = self._make_key(receipt_id)
        entry = self._store.get(key)

        if entry is None:
            logger.debug("Cache MISS", receipt_id=receipt_id)
            return None

        if self._is_expired(entry):
            logger.info("Cache EXPIRED", receipt_id=receipt_id)
            del self._store[key]
            return None

        logger.debug("Cache HIT", receipt_id=receipt_id)
        return entry["data"]

    def delete(self, receipt_id: str) -> bool:
        """Remove a receipt from cache. Returns True if it existed."""
        key = self._make_key(receipt_id)
        if key in self._store:
            del self._store[key]
            logger.info("Cache DELETE", receipt_id=receipt_id)
            return True
        return False

    def cleanup_expired(self) -> int:
        """Remove all expired entries. Returns count of removed items."""
        now = time.time()
        expired_keys = [k for k, v in self._store.items() if now > v["expires_at"]]
        for key in expired_keys:
            del self._store[key]
        if expired_keys:
            logger.info("Cache cleanup", removed_count=len(expired_keys))
        return len(expired_keys)

    @property
    def size(self) -> int:
        """Current number of entries (including possibly expired)."""
        return len(self._store)


# Singleton instance — shared across the application
receipt_cache = ReceiptCache()
