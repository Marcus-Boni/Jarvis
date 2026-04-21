"""Tests for IntentCache."""

from core.intent_cache import IntentCache
from core.models import Intent, IntentCategory


def test_cache_hit_returns_same_intent() -> None:
    cache = IntentCache(ttl_seconds=60.0)
    intent = Intent(raw_text="abra o spotify", category=IntentCategory.SPOTIFY)
    cache.set("abra o spotify", "pt-BR", intent)

    result = cache.get("abra o spotify", "pt-BR")

    assert result is not None
    assert result.category == IntentCategory.SPOTIFY


def test_cache_miss_returns_none() -> None:
    cache = IntentCache(ttl_seconds=60.0)

    assert cache.get("nao cacheado", "pt-BR") is None


def test_cache_evicts_oldest_on_overflow() -> None:
    cache = IntentCache(ttl_seconds=60.0, max_size=2)
    for index in range(3):
        intent = Intent(raw_text=f"msg {index}", category=IntentCategory.CONVERSATION)
        cache.set(f"msg {index}", "pt-BR", intent)

    assert cache.size <= 2
