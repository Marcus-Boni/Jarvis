"""Conversation context assembly and lightweight preference extraction."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from core.config import AppSettings
from core.models import ContextDocument, ConversationMessage, RequestContext
from llm.memory.chroma_store import ChromaMemoryStore
from llm.memory.conversation import ConversationStore
from llm.memory.rag_retriever import MemoryRetriever


class ContextManager:
    """Build enriched request context and persist durable memory."""

    def __init__(
        self,
        settings: AppSettings,
        conversation_store: ConversationStore,
        memory_store: ChromaMemoryStore,
        memory_retriever: MemoryRetriever,
    ) -> None:
        self._settings = settings
        self._conversation_store = conversation_store
        self._memory_store = memory_store
        self._memory_retriever = memory_retriever

    async def build_context(
        self,
        session_id: str,
        prompt: str,
        locale: str = "pt-BR",
        trace_id: str = "",
    ) -> RequestContext:
        """Return request context enriched with conversation history and memory."""

        transcript = await self._conversation_store.load_messages(session_id=session_id)
        memory_documents = await self._memory_retriever.retrieve(prompt=prompt)
        preferences = _extract_preferences(transcript=transcript)
        return RequestContext(
            session_id=session_id,
            locale=locale,
            timezone=self._settings.jarvis.timezone,
            trace_id=trace_id,
            messages=transcript,
            memory_documents=memory_documents,
            preferences=preferences,
        )

    async def persist_exchange(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
        locale: str = "pt-BR",
    ) -> None:
        """Persist a user/assistant exchange and store it in long-term memory."""

        timestamp = datetime.now(UTC).isoformat()
        await self._conversation_store.append_messages(
            session_id=session_id,
            messages=[
                ConversationMessage(role="user", content=user_message),
                ConversationMessage(role="assistant", content=assistant_message),
            ],
        )
        await self._memory_store.add_documents(
            [
                ContextDocument(
                    source="conversation",
                    content=user_message,
                    metadata={
                        "session_id": session_id,
                        "role": "user",
                        "locale": locale,
                        "timestamp": timestamp,
                    },
                ),
                ContextDocument(
                    source="conversation",
                    content=assistant_message,
                    metadata={
                        "session_id": session_id,
                        "role": "assistant",
                        "locale": locale,
                        "timestamp": timestamp,
                    },
                ),
                *_extract_fact_documents(
                    session_id=session_id,
                    locale=locale,
                    user_message=user_message,
                    timestamp=timestamp,
                ),
            ]
        )


def _extract_preferences(transcript: Sequence[ConversationMessage]) -> dict[str, str]:
    """Extract lightweight user preferences from conversation text."""

    preferences: dict[str, str] = {}
    for message in transcript[-12:]:
        lowered_content = message.content.lower()
        if "frontend" in lowered_content:
            preferences["specialty"] = "frontend"
        if "pt-br" in lowered_content or "portugues" in lowered_content:
            preferences["preferred_language"] = "pt-BR"
    return preferences


def _extract_fact_documents(
    session_id: str,
    locale: str,
    user_message: str,
    timestamp: str,
) -> list[ContextDocument]:
    """Create durable memory notes for explicit preference/fact statements."""

    lowered_message = user_message.lower()
    fact_markers = ["meu projeto", "prefiro", "eu uso", "trabalho com", "meu app"]
    if not any(marker in lowered_message for marker in fact_markers):
        return []

    return [
        ContextDocument(
            source="user_fact",
            content=user_message,
            metadata={
                "session_id": session_id,
                "locale": locale,
                "timestamp": timestamp,
            },
        )
    ]
