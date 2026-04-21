"""RAG-style memory retrieval orchestration."""

from __future__ import annotations

from core.config import AppSettings
from core.models import ContextDocument
from llm.memory.chroma_store import ChromaMemoryStore


class MemoryRetriever:
    """Retrieves relevant contextual memory for a prompt."""

    def __init__(
        self,
        settings: AppSettings,
        memory_store: ChromaMemoryStore,
    ) -> None:
        self._settings = settings
        self._memory_store = memory_store

    async def retrieve(self, prompt: str) -> list[ContextDocument]:
        """Fetch the top memory documents relevant to a prompt."""

        return await self._memory_store.query(
            query_text=prompt,
            limit=self._settings.memory.max_context_docs,
        )
