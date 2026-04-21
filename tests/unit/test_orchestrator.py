from __future__ import annotations

from core.models import Intent, IntentCategory, OrchestratorResponse, RequestContext, SkillResult
from core.orchestrator import Orchestrator


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

    async def build_context(self, session_id: str, prompt: str, locale: str = "pt-BR") -> RequestContext:
        return RequestContext(session_id=session_id, locale=locale)

    async def persist_exchange(self, session_id: str, user_message: str, assistant_message: str) -> None:
        self.persisted.append((session_id, user_message, assistant_message))


class FakeLlmClient:
    async def complete_text(self, prompt: str) -> str:
        return "fallback response"


class FakePromptManager:
    def build_fallback_prompt(self, intent: Intent, context: RequestContext) -> str:
        return "fallback prompt"


class FakeSkillLoader:
    def __init__(self, skills: list[object]) -> None:
        self._skills = skills

    def list_enabled(self) -> list[object]:
        return self._skills


class HelpfulSkill:
    name = "helpful"

    async def can_handle(self, intent: Intent) -> float:
        return 0.91

    async def execute(self, intent: Intent, context: RequestContext) -> SkillResult:
        return SkillResult(skill_name="helpful", success=True, message="skill response")


async def test_orchestrator_uses_fallback_when_no_skill_matches() -> None:
    context_manager = FakeContextManager()
    orchestrator = Orchestrator(
        classifier=FakeClassifier(),
        context_manager=context_manager,
        llm_client=FakeLlmClient(),
        prompt_manager=FakePromptManager(),
        skill_loader=FakeSkillLoader(skills=[]),
    )

    response = await orchestrator.handle_message(session_id="s1", message="olá")

    assert response.response_text == "fallback response"
    assert response.used_fallback_llm is True
    assert context_manager.persisted[0][2] == "fallback response"


async def test_orchestrator_executes_matching_skill() -> None:
    context_manager = FakeContextManager()
    orchestrator = Orchestrator(
        classifier=FakeClassifier(),
        context_manager=context_manager,
        llm_client=FakeLlmClient(),
        prompt_manager=FakePromptManager(),
        skill_loader=FakeSkillLoader(skills=[HelpfulSkill()]),
    )

    response = await orchestrator.handle_message(session_id="s1", message="olá")

    assert response.response_text == "skill response"
    assert response.used_fallback_llm is False
    assert response.skill_results[0].skill_name == "helpful"

