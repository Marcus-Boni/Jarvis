"""Persistent ChromaDB-backed memory store."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import chromadb
from chromadb.config import Settings as ChromaSettings

from core.config import AppSettings
from core.models import ContextDocument
from llm.ollama_client import OllamaClient


class ChromaMemoryStore:
    """ChromaDB-backed memory store using Ollama embeddings."""

    def __init__(self, settings: AppSettings, llm_client: OllamaClient) -> None:
        self._settings = settings
        self._llm_client = llm_client
        persist_directory = Path(settings.memory.persist_directory)
        persist_directory.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=str(persist_directory),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=settings.memory.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    async def add_documents(self, documents: Sequence[ContextDocument]) -> None:
        """Store documents for later retrieval."""

        if not documents:
            return

        embeddings = await asyncio.gather(
            *(self._llm_client.embed(document.content) for document in documents)
        )
        ids = [self._build_id(document.metadata) for document in documents]
        raw_documents = [document.content for document in documents]
        metadatas = [self._build_metadata(document) for document in documents]
        collection = cast(Any, self._collection)
        await asyncio.to_thread(
            lambda: collection.upsert(
                ids=ids,
                documents=raw_documents,
                metadatas=metadatas,
                embeddings=embeddings,
            )
        )

    async def query(self, query_text: str, limit: int) -> list[ContextDocument]:
        """Return top semantic matches from ChromaDB."""

        if not query_text.strip():
            return []

        query_embedding = await self._llm_client.embed(query_text)
        collection = cast(Any, self._collection)
        result = await asyncio.to_thread(
            lambda: collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                include=["documents", "metadatas", "distances"],
            )
        )
        normalized_result = cast(dict[str, Any], result)
        documents = normalized_result.get("documents", [[]])
        metadatas = normalized_result.get("metadatas", [[]])
        distances = normalized_result.get("distances", [[]])
        normalized_results: list[ContextDocument] = []
        for index, content in enumerate(documents[0] if documents else []):
            raw_metadata = (metadatas[0] if metadatas else [])[index] or {}
            distance = float((distances[0] if distances else [0.0])[index])
            metadata_dict = {
                str(key): value for key, value in raw_metadata.items()
            }
            normalized_results.append(
                ContextDocument(
                    source=str(metadata_dict.get("source", "memory")),
                    content=str(content),
                    score=max(0.0, 1.0 - distance),
                    metadata=metadata_dict,
                )
            )
        return normalized_results

    def _build_id(self, metadata: dict[str, Any]) -> str:
        session_id = str(metadata.get("session_id", "memory"))
        return f"{session_id}-{uuid4().hex}"

    def _build_metadata(self, document: ContextDocument) -> dict[str, Any]:
        metadata = {str(key): value for key, value in document.metadata.items()}
        metadata.setdefault("source", document.source)
        metadata.setdefault("stored_at", datetime.now(UTC).isoformat())
        return metadata
