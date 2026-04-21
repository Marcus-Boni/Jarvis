"""Bidirectional WebSocket chat transport."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.service_container import ServiceContainer

websocket_router = APIRouter()


@websocket_router.websocket("/ws/chat")
async def chat_socket(websocket: WebSocket) -> None:
    """Stream Jarvis responses over WebSocket."""

    await websocket.accept()
    container: ServiceContainer = websocket.app.state.container
    try:
        while True:
            payload = await websocket.receive_json()
            session_id = str(payload.get("session_id", "default-session"))
            message = str(payload.get("message", ""))
            locale = str(payload.get("locale", "pt-BR"))

            async for chunk in container.orchestrator.stream_response(
                session_id=session_id,
                message=message,
                locale=locale,
            ):
                await websocket.send_json({"type": "chunk", "text": chunk})
            await websocket.send_json({"type": "done"})
    except WebSocketDisconnect:
        return

