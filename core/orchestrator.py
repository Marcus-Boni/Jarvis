"""Central request router for Jarvis."""

from __future__ import annotations

from collections.abc import AsyncIterator

from loguru import logger

from core.context_manager import ContextManager
from core.intent_classifier import IntentClassifier
from core.models import Intent, OrchestratorResponse, RequestContext, SkillResult
from llm.ollama_client import OllamaClient
from llm.prompt_manager import PromptManager
from skills.base_skill import BaseSkill
from skills.loader import SkillLoader


class Orchestrator:
    """Routes user requests to skills or fallback LLM responses."""

    def __init__(
        self,
        classifier: IntentClassifier,
        context_manager: ContextManager,
        llm_client: OllamaClient,
        prompt_manager: PromptManager,
        skill_loader: SkillLoader,
    ) -> None:
        self._classifier = classifier
        self._context_manager = context_manager
        self._llm_client = llm_client
        self._prompt_manager = prompt_manager
        self._skill_loader = skill_loader
        self._logger = logger.bind(component="orchestrator")

    async def handle_message(self, session_id: str, message: str, locale: str = "pt-BR") -> OrchestratorResponse:
        """Process a user message end-to-end."""

        context = await self._context_manager.build_context(session_id=session_id, prompt=message, locale=locale)
        intent = await self._classifier.classify(text=message, locale=locale)
        skill_results = await self._execute_skills(intent=intent, context=context)

        if skill_results:
            response_text = "\n".join(result.message for result in skill_results)
            used_fallback_llm = False
        else:
            response_text = await self._respond_with_fallback_llm(intent=intent, context=context)
            used_fallback_llm = True

        await self._context_manager.persist_exchange(
            session_id=session_id,
            user_message=message,
            assistant_message=response_text,
        )
        self._logger.info(
            "message_handled category={} used_fallback={} skill_count={}",
            intent.category.value,
            used_fallback_llm,
            len(skill_results),
        )
        return OrchestratorResponse(
            intent=intent,
            response_text=response_text,
            skill_results=skill_results,
            used_fallback_llm=used_fallback_llm,
        )

    async def stream_response(self, session_id: str, message: str, locale: str = "pt-BR") -> AsyncIterator[str]:
        """Yield a response in small chunks suitable for SSE/WebSocket streaming."""

        response = await self.handle_message(session_id=session_id, message=message, locale=locale)
        for chunk in _chunk_response(response.response_text):
            yield chunk

    async def _execute_skills(self, intent: Intent, context: RequestContext) -> list[SkillResult]:
        """Select and execute the best matching skills for an intent."""

        candidate_scores: list[tuple[BaseSkill, float]] = []
        for skill in self._skill_loader.list_enabled():
            score = await skill.can_handle(intent)
            if score >= 0.55:
                candidate_scores.append((skill, score))

        if not candidate_scores:
            return []

        ordered_candidates = sorted(candidate_scores, key=lambda item: item[1], reverse=True)
        selected_skills = [ordered_candidates[0][0]]
        if intent.is_compound and len(ordered_candidates) > 1:
            selected_skills.append(ordered_candidates[1][0])

        results: list[SkillResult] = []
        for skill in selected_skills:
            try:
                results.append(await skill.execute(intent=intent, context=context))
            except Exception as exc:  # pragma: no cover - defensive runtime guard
                self._logger.exception("skill_execution_failed skill={} error={}", skill.name, exc)
                results.append(
                    SkillResult(
                        skill_name=skill.name,
                        success=False,
                        message=f"A skill {skill.name} falhou de forma segura e foi registrada para análise.",
                    )
                )
        return results

    async def _respond_with_fallback_llm(self, intent: Intent, context: RequestContext) -> str:
        """Generate a direct assistant response when no skill handles the request."""

        prompt = self._prompt_manager.build_fallback_prompt(intent=intent, context=context)
        return await self._llm_client.complete_text(prompt=prompt)


def _chunk_response(text: str, chunk_size: int = 72) -> list[str]:
    """Split text into deterministic chunks for streaming UX."""

    words = text.split()
    chunks: list[str] = []
    current_chunk = ""
    for word in words:
        candidate = word if not current_chunk else f"{current_chunk} {word}"
        if len(candidate) <= chunk_size:
            current_chunk = candidate
            continue
        chunks.append(current_chunk)
        current_chunk = word
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

