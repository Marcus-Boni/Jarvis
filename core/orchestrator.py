"""Central request router for Jarvis."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from loguru import logger

from core.error_telemetry import ErrorTelemetry
from core.models import Intent, IntentCategory, OrchestratorResponse, RequestContext, SkillResult
from core.protocols import (
    ContextManagerProtocol,
    IntentClassifierProtocol,
    LlmClientProtocol,
    PromptManagerProtocol,
    SkillLoaderProtocol,
)
from core.runtime_events import RuntimeEventBroker
from llm.memory.auto_memory import AutoMemoryExtractor
from skills.base_skill import BaseSkill


class Orchestrator:
    """Route user requests to skills or fallback LLM responses."""

    def __init__(
        self,
        classifier: IntentClassifierProtocol,
        context_manager: ContextManagerProtocol,
        llm_client: LlmClientProtocol,
        prompt_manager: PromptManagerProtocol,
        skill_loader: SkillLoaderProtocol,
        event_broker: RuntimeEventBroker,
        error_telemetry: ErrorTelemetry,
        auto_memory: AutoMemoryExtractor | None = None,
    ) -> None:
        self._classifier = classifier
        self._context_manager = context_manager
        self._llm_client = llm_client
        self._prompt_manager = prompt_manager
        self._skill_loader = skill_loader
        self._event_broker = event_broker
        self._error_telemetry = error_telemetry
        self._auto_memory = auto_memory
        self._logger = logger.bind(component="orchestrator")

    async def handle_message(
        self,
        session_id: str,
        message: str,
        locale: str = "pt-BR",
    ) -> OrchestratorResponse:
        """Process a user message end-to-end."""

        context = await self._context_manager.build_context(
            session_id=session_id,
            prompt=message,
            locale=locale,
        )

        local_response = _build_local_conversation_response(
            message=message,
            locale=locale,
            timezone=context.timezone,
        )
        if local_response is not None:
            intent = Intent(
                raw_text=message,
                category=IntentCategory.UNKNOWN,
                confidence=1.0,
                language=locale,
                actions=[message],
            )
            response_text = local_response
            skill_results = []
            used_fallback_llm = False
        else:
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
            locale=locale,
        )
        self._schedule_auto_memory(
            session_id=session_id,
            user_message=message,
            assistant_message=response_text,
        )
        await self._event_broker.publish(
            "chat",
            {
                "session_id": session_id,
                "intent": intent.category.value,
                "used_fallback_llm": used_fallback_llm,
            },
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

    async def stream_response(
        self,
        session_id: str,
        message: str,
        locale: str = "pt-BR",
    ) -> AsyncIterator[str]:
        """Yield a response in small chunks suitable for SSE/WebSocket streaming."""

        response = await self.handle_message(
            session_id=session_id,
            message=message,
            locale=locale,
        )
        for chunk in _chunk_response(response.response_text):
            yield chunk

    async def _execute_skills(self, intent: Intent, context: RequestContext) -> list[SkillResult]:
        """Select and execute matching skills, in parallel for compound intents."""

        enabled_skills = self._skill_loader.list_enabled()
        if not enabled_skills:
            return []

        candidate_scores: list[tuple[BaseSkill, float]] = []
        score_tasks = [skill.can_handle(intent) for skill in enabled_skills]
        scores = await asyncio.gather(*score_tasks, return_exceptions=True)

        for skill, score in zip(enabled_skills, scores, strict=True):
            if isinstance(score, BaseException):
                self._logger.warning("skill_can_handle_failed skill={} error={}", skill.name, score)
                continue
            score_value = float(score)
            if score_value >= 0.55:
                candidate_scores.append((skill, score_value))

        if not candidate_scores:
            return []

        ordered_candidates = sorted(candidate_scores, key=lambda item: item[1], reverse=True)
        if intent.is_compound:
            selected_skills = [skill for skill, _ in ordered_candidates[:2]]
        else:
            selected_skills = [ordered_candidates[0][0]]

        results = await asyncio.gather(
            *(self._safe_execute_skill(skill=skill, intent=intent, context=context) for skill in selected_skills)
        )
        return [result for result in results if result is not None]

    async def _respond_with_fallback_llm(self, intent: Intent, context: RequestContext) -> str:
        """Generate a direct assistant response when no skill handles the request."""

        local_response = _build_local_conversation_response(
            message=intent.raw_text,
            locale=context.locale,
            timezone=context.timezone,
        )
        if local_response is not None:
            return local_response

        prompt = self._prompt_manager.build_fallback_prompt(intent=intent, context=context)
        try:
            response_text = await self._llm_client.complete_text(prompt=prompt)
        except Exception as exc:  # pragma: no cover
            self._logger.warning("fallback_llm_failed error={}", exc)
            await self._error_telemetry.record(
                component="fallback_llm",
                error=type(exc).__name__,
                message=str(exc),
            )
            return _fallback_error_response(context.locale)

        if _looks_like_placeholder_response(response_text):
            return _fallback_error_response(context.locale)
        return response_text

    async def _safe_execute_skill(
        self,
        skill: BaseSkill,
        intent: Intent,
        context: RequestContext,
    ) -> SkillResult | None:
        try:
            result = await skill.execute(intent=intent, context=context)
            await self._event_broker.publish(
                "skill",
                {"skill_name": skill.name, "success": result.success},
            )
            return result
        except Exception as exc:  # pragma: no cover
            self._logger.exception("skill_failed skill={} error={}", skill.name, exc)
            await self._error_telemetry.record(
                component=skill.name,
                error=type(exc).__name__,
                message=str(exc),
            )
            return SkillResult(
                skill_name=skill.name,
                success=False,
                message=f"Skill {skill.name} falhou com seguranca: {type(exc).__name__}",
            )

    def _schedule_auto_memory(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
    ) -> None:
        if self._auto_memory is None:
            return

        task = asyncio.create_task(
            self._auto_memory.extract_and_store(
                session_id=session_id,
                user_message=user_message,
                assistant_message=assistant_message,
            )
        )
        task.add_done_callback(self._handle_background_task_completion)

    def _handle_background_task_completion(self, task: asyncio.Task[int]) -> None:
        try:
            task.result()
        except Exception as exc:  # pragma: no cover
            self._logger.warning("background_task_failed error={}", exc)


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


def _build_local_conversation_response(
    message: str,
    locale: str,
    timezone: str,
    now: datetime | None = None,
) -> str | None:
    lowered_message = message.lower().strip()
    if not lowered_message:
        return _empty_request_response(locale)

    current_time = _resolve_now(timezone=timezone, now=now)
    date_response = None
    time_response = None

    if any(
        token in lowered_message
        for token in ["que dia e hoje", "que dia é hoje", "data de hoje", "qual a data de hoje"]
    ):
        date_response = _format_date_response(current_time=current_time, locale=locale)

    if any(
        token in lowered_message
        for token in ["que horas sao", "que horas são", "hora agora", "horario atual", "horário atual"]
    ):
        time_response = _format_time_response(current_time=current_time, locale=locale)

    if date_response and time_response:
        return f"{date_response} {time_response}"
    if date_response:
        return date_response
    if time_response:
        return time_response

    return None


def _resolve_now(timezone: str, now: datetime | None) -> datetime:
    if now is not None:
        return now
    try:
        return datetime.now(ZoneInfo(timezone))
    except ZoneInfoNotFoundError:
        return datetime.now()


def _format_date_response(current_time: datetime, locale: str) -> str:
    if locale.lower().startswith("pt"):
        weekdays = [
            "segunda-feira",
            "terca-feira",
            "quarta-feira",
            "quinta-feira",
            "sexta-feira",
            "sabado",
            "domingo",
        ]
        months = [
            "janeiro",
            "fevereiro",
            "marco",
            "abril",
            "maio",
            "junho",
            "julho",
            "agosto",
            "setembro",
            "outubro",
            "novembro",
            "dezembro",
        ]
        weekday = weekdays[current_time.weekday()]
        month = months[current_time.month - 1]
        return f"Hoje e {weekday}, {current_time.day} de {month} de {current_time.year}."

    return current_time.strftime("Today is %A, %B %d, %Y.")


def _format_time_response(current_time: datetime, locale: str) -> str:
    if locale.lower().startswith("pt"):
        return f"Agora sao {current_time.strftime('%H:%M')}."
    return f"It is now {current_time.strftime('%H:%M')}."


def _looks_like_placeholder_response(response_text: str) -> bool:
    normalized_text = response_text.strip()
    if not normalized_text:
        return True
    return normalized_text in {"...", "..", ".", "…"}


def _fallback_error_response(locale: str) -> str:
    if locale.lower().startswith("pt"):
        return (
            "Nao consegui gerar uma resposta util do modelo local agora. "
            "Tente novamente em alguns segundos."
        )
    return "I could not get a useful reply from the local model right now. Please try again."


def _empty_request_response(locale: str) -> str:
    if locale.lower().startswith("pt"):
        return "Nao consegui entender o pedido. Tente falar ou escrever novamente."
    return "I could not understand the request. Please try again."
