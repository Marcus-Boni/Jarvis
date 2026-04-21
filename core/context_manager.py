"""Conversation context assembly and lightweight preference extraction."""

from __future__ import annotations

from collections.abc import Sequence

from core.models import ContextDocument, ConversationMessage, RequestContext
from llm.memory.conversation import ConversationStore
from llm.memory.rag_retriever import MemoryRetriever


class ContextManager:
    """Builds enriched request context for orchestration."""

    def __init__(
        self,
        conversation_store: ConversationStore,
        memory_retriever: MemoryRetriever,
    ) -> None:
        self._conversation_store = conversation_store
        self._memory_retriever = memory_retriever

    async def build_context(self, session_id: str, prompt: str, locale: str = "pt-BR") -> RequestContext:
        """Return request context enriched with conversation history and memory."""

        transcript = await self._conversation_store.load_messages(session_id=session_id)
        memory_documents = await self._memory_retriever.retrieve(prompt=prompt)
        preferences = _extract_preferences(transcript=transcript)
        return RequestContext(
            session_id=session_id,
            locale=locale,
            messages=transcript,
            memory_documents=memory_documents,
            preferences=preferences,
        )

    async def persist_exchange(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
    ) -> None:
        """Persist a user/assistant exchange."""

        await self._conversation_store.append_messages(
            session_id=session_id,
            messages=[
                ConversationMessage(role="user", content=user_message),
                ConversationMessage(role="assistant", content=assistant_message),
            ],
        )


def _extract_preferences(transcript: Sequence[ConversationMessage]) -> dict[str, str]:
    """Extract lightweight user preferences from conversation text."""

    preferences: dict[str, str] = {}
    for message in transcript[-12:]:
        if "frontend" in message.content.lower():
            preferences["specialty"] = "frontend"
        if "pt-br" in message.content.lower() or "português" in message.content.lower():
            preferences["preferred_language"] = "pt-BR"
    return preferences

