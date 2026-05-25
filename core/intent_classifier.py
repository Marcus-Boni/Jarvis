"""LLM-backed intent classification for Jarvis user requests."""

from __future__ import annotations

from loguru import logger

from core.intent_cache import IntentCache
from core.models import Intent, IntentCategory
from llm.ollama_client import OllamaClient
from llm.prompt_manager import PromptManager


class IntentClassifier:
    """Classify text into a normalized Jarvis intent."""

    def __init__(self, llm_client: OllamaClient, prompt_manager: PromptManager) -> None:
        self._llm_client = llm_client
        self._prompt_manager = prompt_manager
        self._logger = logger.bind(component="intent_classifier")
        self._cache = IntentCache(ttl_seconds=300.0, max_size=128)

    async def classify(self, text: str, locale: str = "pt-BR") -> Intent:
        """Classify a user request into an `Intent`."""

        cached_intent = self._cache.get(text, locale)
        if cached_intent is not None:
            self._logger.debug("intent_cache_hit text_len={}", len(text))
            return cached_intent

        rule_based_intent = _classify_with_rules(text=text, locale=locale)
        if rule_based_intent is not None:
            self._cache.set(text, locale, rule_based_intent)
            return rule_based_intent

        intent = await self._classify_from_llm(text=text, locale=locale)
        self._cache.set(text, locale, intent)
        return intent

    async def _classify_from_llm(self, text: str, locale: str) -> Intent:
        prompt = self._prompt_manager.build_intent_prompt(user_input=text, locale=locale)
        payload = await self._llm_client.complete_json(prompt=prompt)
        category_value = _normalize_category_value(
            str(payload.get("category", IntentCategory.UNKNOWN.value)).lower()
        )
        actions = payload.get("actions", [text])
        if not isinstance(actions, list):
            actions = [text]

        try:
            category = IntentCategory(category_value)
        except ValueError:
            category = IntentCategory.UNKNOWN

        intent = Intent(
            raw_text=text,
            category=category,
            confidence=float(payload.get("confidence", 0.0)),
            language=str(payload.get("language", locale)),
            reasoning=str(payload.get("reasoning", "")),
            actions=[str(action) for action in actions],
            skill_hints=[str(item) for item in payload.get("skill_hints", [])],
            entities={str(key): str(value) for key, value in payload.get("entities", {}).items()},
        )
        self._logger.info(
            "intent_classified category={} confidence={}",
            intent.category.value,
            intent.confidence,
        )
        return intent


def _classify_with_rules(text: str, locale: str) -> Intent | None:
    lowered_text = text.lower().strip()
    if any(
        token in lowered_text
        for token in [
            "que dia é hoje", "que dia e hoje", "data de hoje", "qual a data de hoje",
            "que horas são", "que horas sao", "hora agora", "horario atual", "horário atual",
        ]
    ):
        return Intent(
            raw_text=text,
            category=IntentCategory.UNKNOWN,
            confidence=0.95,
            language=locale,
            actions=[text],
        )
    if any(token in lowered_text for token in ["abra ", "abre ", "open ", "launch "]):
        return Intent(
            raw_text=text,
            category=IntentCategory.SYSTEM_CONTROL,
            confidence=0.79,
            language=locale,
            actions=[text],
        )
    if any(token in lowered_text for token in ["spotify", "pause", "pausa", "proxima", "next"]):
        return Intent(
            raw_text=text,
            category=IntentCategory.SPOTIFY,
            confidence=0.86,
            language=locale,
            actions=[text],
        )
    if any(token in lowered_text for token in ["email", "outlook", "meeting", "reuniao"]):
        return Intent(
            raw_text=text,
            category=IntentCategory.EMAIL,
            confidence=0.8,
            language=locale,
            actions=[text],
        )
    if any(
        token in lowered_text
        for token in ["volume", "som", "mute", "silenc", "play", "pause", "proxima faixa"]
    ):
        return Intent(
            raw_text=text,
            category=IntentCategory.VOLUME,
            confidence=0.82,
            language=locale,
            actions=[text],
        )
    if any(token in lowered_text for token in ["google calendar", "evento", "agenda"]):
        return Intent(
            raw_text=text,
            category=IntentCategory.CALENDAR,
            confidence=0.78,
            language=locale,
            actions=[text],
        )
    if any(token in lowered_text for token in ["notion", "anote", "nota"]):
        return Intent(
            raw_text=text,
            category=IntentCategory.NOTION,
            confidence=0.82,
            language=locale,
            actions=[text],
        )
    if any(token in lowered_text for token in ["pesquise", "procure", "search", "busque"]):
        return Intent(
            raw_text=text,
            category=IntentCategory.BROWSER,
            confidence=0.76,
            language=locale,
            actions=[text],
        )
    return None


def _normalize_category_value(raw_value: str) -> str:
    if raw_value == IntentCategory.OUTLOOK.value:
        return IntentCategory.EMAIL.value
    return raw_value
