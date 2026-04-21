"""Shared Pydantic models used across Jarvis runtime boundaries."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class IntentCategory(str, Enum):
    """Supported high-level intent categories."""

    SYSTEM_CONTROL = "system_control"
    BROWSER = "browser"
    NOTION = "notion"
    CALENDAR = "calendar"
    SPOTIFY = "spotify"
    EMAIL = "email"
    OUTLOOK = "outlook"
    VOLUME = "volume"
    CONVERSATION = "conversation"
    CODE_HELP = "code_help"
    MEMORY = "memory"
    UNKNOWN = "unknown"


class Intent(BaseModel):
    """Normalized classification result for a user request."""

    raw_text: str
    category: IntentCategory = IntentCategory.UNKNOWN
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    language: str = "pt-BR"
    reasoning: str = ""
    actions: list[str] = Field(default_factory=list)
    skill_hints: list[str] = Field(default_factory=list)
    entities: dict[str, str] = Field(default_factory=dict)

    @property
    def is_compound(self) -> bool:
        """Return whether the intent describes multiple actions."""

        return len(self.actions) > 1


class ConversationMessage(BaseModel):
    """One message inside a conversation transcript."""

    role: str
    content: str


class ContextDocument(BaseModel):
    """Retrieved memory or supporting context document."""

    source: str
    content: str
    score: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class RequestContext(BaseModel):
    """Context that accompanies each orchestration request."""

    session_id: str
    user_id: str = "local-user"
    locale: str = "pt-BR"
    timezone: str = "America/Sao_Paulo"
    trace_id: str = ""
    messages: list[ConversationMessage] = Field(default_factory=list)
    memory_documents: list[ContextDocument] = Field(default_factory=list)
    preferences: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SkillResult(BaseModel):
    """Normalized response returned by skills."""

    skill_name: str
    success: bool
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    follow_up_required: bool = False


class OrchestratorResponse(BaseModel):
    """Top-level response returned to API callers."""

    intent: Intent
    response_text: str
    skill_results: list[SkillResult] = Field(default_factory=list)
    used_fallback_llm: bool = False
