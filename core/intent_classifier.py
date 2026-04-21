"""LLM-backed intent classification for Jarvis user requests."""

from __future__ import annotations

from loguru import logger

from core.models import Intent, IntentCategory
from llm.ollama_client import OllamaClient
from llm.prompt_manager import PromptManager


class IntentClassifier:
    """Classifies text into a normalized Jarvis intent."""

    def __init__(self, llm_client: OllamaClient, prompt_manager: PromptManager) -> None:
        self._llm_client = llm_client
        self._prompt_manager = prompt_manager
        self._logger = logger.bind(component="intent_classifier")

    async def classify(self, text: str, locale: str = "pt-BR") -> Intent:
        """Classify a user request into an `Intent`."""

        prompt = self._prompt_manager.build_intent_prompt(user_input=text, locale=locale)
        payload = await self._llm_client.complete_json(prompt=prompt)
        category_value = str(payload.get("category", IntentCategory.UNKNOWN.value)).lower()
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
        self._logger.info("intent_classified category={} confidence={}", intent.category.value, intent.confidence)
        return intent

