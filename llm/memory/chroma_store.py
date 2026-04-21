"""Minimal memory-store facade for future ChromaDB integration."""

from __future__ import annotations

from collections.abc import Sequence

from core.config import AppSettings
from core.models import ContextDocument


class ChromaMemoryStore:
    """Temporary in-process memory store that preserves the ChromaDB interface shape."""

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._documents: list[ContextDocument] = []

    async def add_documents(self, documents: Sequence[ContextDocument]) -> None:
        """Store documents for later retrieval."""

        self._documents.extend(documents)

    async def query(self, query_text: str, limit: int) -> list[ContextDocument]:
        """Return basic string-matching results until ChromaDB wiring lands."""

        lowered_query = query_text.lower()
        matches = [
            document
            for document in self._documents
            if lowered_query in document.content.lower() or lowered_query in document.source.lower()
        ]
        return matches[:limit]

