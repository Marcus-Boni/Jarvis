from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.dependencies import get_container, require_local_token
from api.routes import memory, webhooks


class FakeMemoryStore:
    def __init__(self) -> None:
        self.cleared = False

    async def query(self, query_text: str, limit: int) -> list[object]:
        del query_text, limit
        return []

    def clear_all(self) -> None:
        self.cleared = True


class FakeIntent:
    def __init__(self) -> None:
        self.category = type("Category", (), {"value": "conversation"})()


class FakeOrchestratorResponse:
    def __init__(self) -> None:
        self.response_text = "ok"
        self.intent = FakeIntent()
        self.used_fallback_llm = False


class FakeOrchestrator:
    async def handle_message(
        self,
        session_id: str,
        message: str,
        locale: str = "pt-BR",
    ) -> FakeOrchestratorResponse:
        del session_id, message, locale
        return FakeOrchestratorResponse()


class FakeContainer:
    def __init__(self) -> None:
        self.memory_store = FakeMemoryStore()
        self.orchestrator = FakeOrchestrator()


def _build_test_client() -> tuple[TestClient, FakeContainer]:
    app = FastAPI()
    container = FakeContainer()
    app.include_router(memory.router)
    app.include_router(webhooks.router)
    app.dependency_overrides[get_container] = lambda: container
    app.dependency_overrides[require_local_token] = lambda: None
    return TestClient(app), container


def test_clear_memory_route() -> None:
    client, container = _build_test_client()

    response = client.post("/api/memory/clear")

    assert response.status_code == 200
    assert response.json() == {"status": "cleared"}
    assert container.memory_store.cleared is True


def test_webhook_command_route() -> None:
    client, _ = _build_test_client()

    response = client.post(
        "/api/webhooks/command",
        json={"session_id": "hook-1", "message": "ola", "locale": "pt-BR"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["response_text"] == "ok"
    assert payload["intent_category"] == "conversation"
