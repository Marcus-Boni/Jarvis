"""Base contract for Jarvis skills."""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.models import Intent, RequestContext, SkillResult


class BaseSkill(ABC):
    """Base class implemented by every Jarvis skill."""

    name: str
    description: str
    triggers: list[str]
    enabled: bool

    def __init__(self) -> None:
        self.enabled = True

    @abstractmethod
    async def can_handle(self, intent: Intent) -> float:
        """Return a confidence score from 0.0 to 1.0."""

    @abstractmethod
    async def execute(self, intent: Intent, context: RequestContext) -> SkillResult:
        """Execute the skill and return a normalized result."""

    def status_payload(self) -> dict[str, object]:
        """Serialize a skill for API responses."""

        return {
            "name": self.name,
            "description": self.description,
            "triggers": self.triggers,
            "enabled": self.enabled,
        }

