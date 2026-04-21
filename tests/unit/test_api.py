from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app


def test_healthcheck() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "ollama_reachable" in payload
    assert "loaded_skills" in payload
