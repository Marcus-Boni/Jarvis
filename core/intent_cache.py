"""Simple TTL-based intent classification cache."""

from __future__ import annotations

import hashlib
import time
from collections import OrderedDict
from dataclasses import dataclass

from core.models import Intent


@dataclass(slots=True)
class CacheEntry:
    """One cached intent plus its expiration deadline."""

    intent: Intent
    expires_at: float


class IntentCache:
    """In-memory cache for normalized intent classification results."""

    def __init__(self, ttl_seconds: float = 300.0, max_size: int = 128) -> None:
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._store: OrderedDict[str, CacheEntry] = OrderedDict()

    def _key(self, text: str, locale: str) -> str:
        normalized_text = f"{locale}:{text.strip().lower()}"
        return hashlib.md5(normalized_text.encode("utf-8"), usedforsecurity=False).hexdigest()

    def get(self, text: str, locale: str) -> Intent | None:
        key = self._key(text, locale)
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.monotonic() > entry.expires_at:
            del self._store[key]
            return None
        self._store.move_to_end(key)
        return entry.intent.model_copy(deep=True)

    def set(self, text: str, locale: str, intent: Intent) -> None:
        key = self._key(text, locale)
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = CacheEntry(
            intent=intent.model_copy(deep=True),
            expires_at=time.monotonic() + self._ttl,
        )
        while len(self._store) > self._max_size:
            self._store.popitem(last=False)

    def invalidate(self) -> None:
        """Clear all cache entries."""

        self._store.clear()

    @property
    def size(self) -> int:
        """Return the number of live entries currently tracked."""

        return len(self._store)
