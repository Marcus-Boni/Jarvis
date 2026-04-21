"""Webhook routes for external Jarvis command ingestion."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.dependencies import get_container, require_local_token
from core.service_container import ServiceContainer

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])
ContainerDependency = Annotated[ServiceContainer, Depends(get_container)]


class WebhookCommandRequest(BaseModel):
    session_id: str = Field(default="webhook-session")
    message: str
    locale: str = Field(default="pt-BR")
    source: str = Field(default="external-automation")


@router.post("/command", dependencies=[Depends(require_local_token)])
async def receive_command(
    payload: WebhookCommandRequest,
    container: ContainerDependency,
) -> dict[str, object]:
    """Receive an external command and route it through the orchestrator."""

    result = await container.orchestrator.handle_message(
        session_id=payload.session_id,
        message=payload.message,
        locale=payload.locale,
    )
    return {
        "session_id": payload.session_id,
        "source": payload.source,
        "response_text": result.response_text,
        "intent_category": result.intent.category.value,
        "used_fallback_llm": result.used_fallback_llm,
    }
