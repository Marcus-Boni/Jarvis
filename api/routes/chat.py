"""Chat routes including JSON and SSE response modes."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from api.dependencies import get_container, require_local_token
from core.service_container import ServiceContainer

router = APIRouter(prefix="/api/chat", tags=["chat"])
ContainerDependency = Annotated[ServiceContainer, Depends(get_container)]


class ChatRequest(BaseModel):
    session_id: str = Field(default="default-session")
    message: str
    locale: str = Field(default="pt-BR")


class ChatResponse(BaseModel):
    session_id: str
    response_text: str
    intent_category: str
    used_fallback_llm: bool


@router.post("", response_model=ChatResponse, dependencies=[Depends(require_local_token)])
async def create_chat_response(
    payload: ChatRequest,
    container: ContainerDependency,
) -> ChatResponse:
    """Return a single-shot chat response."""

    result = await container.orchestrator.handle_message(
        session_id=payload.session_id,
        message=payload.message,
        locale=payload.locale,
    )
    return ChatResponse(
        session_id=payload.session_id,
        response_text=result.response_text,
        intent_category=result.intent.category.value,
        used_fallback_llm=result.used_fallback_llm,
    )


@router.post("/stream", dependencies=[Depends(require_local_token)])
async def stream_chat_response(
    payload: ChatRequest,
    container: ContainerDependency,
) -> StreamingResponse:
    """Stream chat chunks over SSE."""

    async def event_stream() -> AsyncIterator[str]:
        async for chunk in container.orchestrator.stream_response(
            session_id=payload.session_id,
            message=payload.message,
            locale=payload.locale,
        ):
            yield f"event: chunk\ndata: {json.dumps({'text': chunk}, ensure_ascii=False)}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
