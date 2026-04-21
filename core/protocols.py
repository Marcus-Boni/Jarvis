"""Structural protocols for orchestrator dependencies."""

from __future__ import annotations

from typing import Protocol

from core.models import Intent, RequestContext
from skills.base_skill import BaseSkill


class IntentClassifierProtocol(Protocol):
    async def classify(self, text: str, locale: str = "pt-BR") -> Intent:
        """Classify a user request."""


class ContextManagerProtocol(Protocol):
    async def build_context(
        self,
        session_id: str,
        prompt: str,
        locale: str = "pt-BR",
    ) -> RequestContext:
        """Build request context."""

    async def persist_exchange(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
        locale: str = "pt-BR",
    ) -> None:
        """Persist a request/response exchange."""


class LlmClientProtocol(Protocol):
    async def complete_text(self, prompt: str, model: str | None = None) -> str:
        """Generate plain text."""


class PromptManagerProtocol(Protocol):
    def build_fallback_prompt(self, intent: Intent, context: RequestContext) -> str:
        """Create fallback prompt text."""


class SkillLoaderProtocol(Protocol):
    def list_enabled(self) -> list[BaseSkill]:
        """Return enabled skills."""

