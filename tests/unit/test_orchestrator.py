from __future__ import annotations

from typing import ClassVar

from core.error_telemetry import ErrorTelemetry
from core.models import Intent, IntentCategory, RequestContext, SkillResult
from datetime import datetime

from core.orchestrator import Orchestrator, _build_local_conversation_response
from core.runtime_events import RuntimeEventBroker
from skills.base_skill import BaseSkill


class FakeClassifier:
    async def classify(self, text: str, locale: str = "pt-BR") -> Intent:
        return Intent(
            raw_text=text,
            category=IntentCategory.CONVERSATION,
            confidence=0.9,
            language=locale,
            actions=[text],
        )


class FakeContextManager:
    def __init__(self) -> None:
        self.persisted: list[tuple[str, str, str]] = []

    async def build_context(
        self,
        session_id: str,
        prompt: str,
        locale: str = "pt-BR",
    ) -> RequestContext:
        del prompt
        return RequestContext(session_id=session_id, locale=locale)

    async def persist_exchange(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
        locale: str = "pt-BR",
    ) -> None:
        del locale
        self.persisted.append((session_id, user_message, assistant_message))


class FakeLlmClient:
    async def complete_text(self, prompt: str, model: str | None = None) -> str:
        del prompt, model
        return "fallback response"


class FakePromptManager:
    def build_fallback_prompt(self, intent: Intent, context: RequestContext) -> str:
        del intent, context
        return "fallback prompt"


class FakeSkillLoader:
    def __init__(self, skills: list[BaseSkill]) -> None:
        self._skills = skills

    def list_enabled(self) -> list[BaseSkill]:
        return self._skills


class HelpfulSkill(BaseSkill):
    name: ClassVar[str] = "helpful"
    description: ClassVar[str] = "helpful test skill"
    triggers: ClassVar[list[str]] = ["help"]

    async def can_handle(self, intent: Intent) -> float:
        del intent
        return 0.91

    async def execute(self, intent: Intent, context: RequestContext) -> SkillResult:
        del intent, context
        return SkillResult(skill_name="helpful", success=True, message="skill response")


def _build_orchestrator(
    context_manager: FakeContextManager,
    skills: list[BaseSkill],
) -> Orchestrator:
    return Orchestrator(
        classifier=FakeClassifier(),
        context_manager=context_manager,
        llm_client=FakeLlmClient(),
        prompt_manager=FakePromptManager(),
        skill_loader=FakeSkillLoader(skills=skills),
        event_broker=RuntimeEventBroker(),
        error_telemetry=ErrorTelemetry("data/logs/test-errors.jsonl"),
    )


async def test_orchestrator_uses_fallback_when_no_skill_matches() -> None:
    context_manager = FakeContextManager()
    orchestrator = _build_orchestrator(context_manager=context_manager, skills=[])

    response = await orchestrator.handle_message(session_id="s1", message="ola")

    assert response.response_text == "fallback response"
    assert response.used_fallback_llm is True
    assert context_manager.persisted[0][2] == "fallback response"


async def test_orchestrator_executes_matching_skill() -> None:
    context_manager = FakeContextManager()
    orchestrator = _build_orchestrator(
        context_manager=context_manager,
        skills=[HelpfulSkill()],
    )

    response = await orchestrator.handle_message(session_id="s1", message="ola")

    assert response.response_text == "skill response"
    assert response.used_fallback_llm is False
    assert response.skill_results[0].skill_name == "helpful"


def test_local_conversation_response_answers_current_date() -> None:
    response = _build_local_conversation_response(
        message="Boa noite, que dia e hoje?",
        locale="pt-BR",
        timezone="America/Sao_Paulo",
        now=datetime(2026, 4, 22, 21, 15),
    )

    assert response == "Hoje e quarta-feira, 22 de abril de 2026."
