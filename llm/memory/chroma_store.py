"""Persistent ChromaDB-backed memory store with in-memory fallback."""

from __future__ import annotations

import asyncio
import math
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger

from core.config import AppSettings
from core.models import ContextDocument
from llm.ollama_client import OllamaClient


class ChromaMemoryStore:
    """Persistent vector memory store backed by ChromaDB and Ollama embeddings."""

    def __init__(self, settings: AppSettings, llm_client: OllamaClient) -> None:
        self._settings = settings
        self._llm_client = llm_client
        self._logger = logger.bind(component="memory_store")
        self._fallback_store = ChromaMemoryStoreFallback(llm_client=llm_client)
        self._collection: Any | None = None
        persist_directory = Path(settings.memory.persist_directory)
        try:
            persist_directory.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=str(persist_directory),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection(
                name=settings.memory.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as exc:  # pragma: no cover
            self._logger.warning("chromadb_startup_failed fallback=in_memory error={}", exc)
            self._collection = None

    async def add_documents(self, documents: Sequence[ContextDocument]) -> None:
        """Store documents for later retrieval."""

        if not documents:
            return
        if self._collection is None:
            await self._fallback_store.add_documents(documents)
            return

        try:
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
        except Exception as exc:  # pragma: no cover
            self._logger.warning("chromadb_add_failed fallback=in_memory error={}", exc)
            await self._fallback_store.add_documents(documents)

    async def query(self, query_text: str, limit: int) -> list[ContextDocument]:
        """Return top semantic matches from ChromaDB."""

        if not query_text.strip():
            return []
        if self._collection is None:
            return await self._fallback_store.query(query_text=query_text, limit=limit)

        try:
            total_documents = await self.count()
            if total_documents == 0:
                return []

            query_embedding = await self._llm_client.embed(query_text)
            collection = cast(Any, self._collection)
            result = await asyncio.to_thread(
                lambda: collection.query(
                    query_embeddings=[query_embedding],
                    n_results=min(limit, total_documents),
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
                metadata_dict = {str(key): value for key, value in raw_metadata.items()}
                normalized_results.append(
                    ContextDocument(
                        source=str(metadata_dict.get("source", "memory")),
                        content=str(content),
                        score=max(0.0, 1.0 - distance),
                        metadata=metadata_dict,
                    )
                )
            return normalized_results
        except Exception as exc:  # pragma: no cover
            self._logger.warning("chromadb_query_failed fallback=in_memory error={}", exc)
            return await self._fallback_store.query(query_text=query_text, limit=limit)

    async def count(self) -> int:
        """Return the number of stored documents."""

        if self._collection is None:
            return await self._fallback_store.count()
        collection = cast(Any, self._collection)
        return cast(int, await asyncio.to_thread(collection.count))

    def _build_id(self, metadata: dict[str, Any]) -> str:
        session_id = str(metadata.get("session_id", "memory"))
        return f"{session_id}-{uuid4().hex}"

    def _build_metadata(self, document: ContextDocument) -> dict[str, Any]:
        metadata = {str(key): value for key, value in document.metadata.items()}
        metadata.setdefault("source", document.source)
        metadata.setdefault("stored_at", datetime.now(UTC).isoformat())
        return metadata


class ChromaMemoryStoreFallback:
    """Simple in-process vector store used when ChromaDB is unavailable."""

    def __init__(self, llm_client: OllamaClient) -> None:
        self._llm_client = llm_client
        self._logger = logger.bind(component="memory_store_fallback")
        self._documents: list[ContextDocument] = []
        self._embeddings: list[list[float]] = []

    async def add_documents(self, documents: Sequence[ContextDocument]) -> None:
        if not documents:
            return
        try:
            embeddings = await asyncio.gather(
                *(self._llm_client.embed(document.content) for document in documents)
            )
        except Exception as exc:  # pragma: no cover
            self._logger.warning("fallback_embedding_failed error={}", exc)
            return

        for document, embedding in zip(documents, embeddings, strict=True):
            metadata = {str(key): value for key, value in document.metadata.items()}
            metadata.setdefault("source", document.source)
            metadata.setdefault("stored_at", datetime.now(UTC).isoformat())
            self._documents.append(document.model_copy(update={"metadata": metadata}))
            self._embeddings.append([float(value) for value in embedding])

    async def query(self, query_text: str, limit: int) -> list[ContextDocument]:
        if not self._documents:
            return []
        try:
            query_embedding = await self._llm_client.embed(query_text)
        except Exception as exc:  # pragma: no cover
            self._logger.warning("fallback_query_embedding_failed error={}", exc)
            return []

        scored_results = sorted(
            (
                (
                    _cosine_similarity(query_embedding, embedding),
                    document,
                )
                for document, embedding in zip(self._documents, self._embeddings, strict=True)
            ),
            key=lambda item: item[0],
            reverse=True,
        )
        return [
            document.model_copy(update={"score": max(0.0, score)})
            for score, document in scored_results[:limit]
        ]

    async def count(self) -> int:
        return len(self._documents)


def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if not left or not right:
        return 0.0
    numerator = sum(lhs * rhs for lhs, rhs in zip(left, right, strict=False))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return numerator / (left_norm * right_norm)
