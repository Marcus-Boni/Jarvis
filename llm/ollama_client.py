"""Async wrapper around the local Ollama HTTP API."""

from __future__ import annotations

import json
from typing import Any

import httpx

from core.config import AppSettings


class OllamaClient:
    """Small async client for interacting with a local Ollama instance."""

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(
            base_url=settings.llm.base_url,
            timeout=settings.llm.request_timeout_seconds,
        )

    async def complete_text(self, prompt: str, model: str | None = None) -> str:
        """Generate plain text from a prompt."""

        payload = {
            "model": model or self._settings.llm.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self._settings.llm.temperature,
                "num_ctx": self._settings.llm.context_window,
            },
        }
        response = await self._client.post("/api/generate", json=payload)
        response.raise_for_status()
        data = response.json()
        return str(data.get("response", "")).strip()

    async def complete_json(self, prompt: str, model: str | None = None) -> dict[str, Any]:
        """Generate structured JSON from a prompt."""

        payload = {
            "model": model or self._settings.llm.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,
                "num_ctx": self._settings.llm.context_window,
            },
        }
        response = await self._client.post("/api/generate", json=payload)
        response.raise_for_status()
        raw_response = response.json().get("response", "{}")
        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError:
            parsed = {"category": "unknown", "confidence": 0.0, "reasoning": raw_response}
        if isinstance(parsed, dict):
            return parsed
        return {"category": "unknown", "confidence": 0.0, "reasoning": "invalid_json"}

    async def embed(self, text: str) -> list[float]:
        """Return local embeddings for a text string."""

        payload = {
            "model": self._settings.memory.embedding_model,
            "input": text,
        }
        response = await self._client.post("/api/embed", json=payload)
        response.raise_for_status()
        data = response.json()
        embeddings = data.get("embeddings", [[]])
        first_embedding = embeddings[0] if embeddings else []
        return [float(value) for value in first_embedding]

    async def health(self) -> bool:
        """Check whether the Ollama server is reachable."""

        try:
            response = await self._client.get("/api/tags")
            response.raise_for_status()
        except httpx.HTTPError:
            return False
        return True

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""

        await self._client.aclose()

