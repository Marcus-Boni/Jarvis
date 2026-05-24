"""Bidirectional WebSocket transports for chat, voice, and runtime events."""

from __future__ import annotations

import base64
import io
import json
import wave

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from core.service_container import ServiceContainer

websocket_router = APIRouter()
socket_logger = logger.bind(component="websocket")


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
            try:
                response = await container.orchestrator.handle_message(
                    session_id=session_id,
                    message=message,
                    locale=locale,
                )
                for chunk in _chunk_response(response.response_text):
                    await websocket.send_json({"type": "chunk", "text": chunk})
                await websocket.send_json({"type": "done", "text": response.response_text})
            except Exception as exc:  # pragma: no cover
                socket_logger.warning("chat_socket_failed error={}", exc)
                await container.error_telemetry.record(
                    component="ws_chat",
                    error=type(exc).__name__,
                    message=str(exc),
                )
                error_text = (
                    "Nao consegui responder agora. Tente novamente em alguns segundos."
                )
                await websocket.send_json({"type": "error", "text": error_text})
                await websocket.send_json({"type": "done", "text": error_text})
    except WebSocketDisconnect:
        return


@websocket_router.websocket("/ws/events")
async def events_socket(websocket: WebSocket) -> None:
    """Broadcast runtime activity events to the dashboard."""

    await websocket.accept()
    container: ServiceContainer = websocket.app.state.container
    queue = container.events.subscribe()
    try:
        while True:
            event = await queue.get()
            await websocket.send_json(event)
    except WebSocketDisconnect:
        container.events.unsubscribe(queue)


@websocket_router.websocket("/ws/voice")
async def voice_socket(websocket: WebSocket) -> None:
    """Receive binary audio frames, then respond with transcript and TTS audio."""

    await websocket.accept()
    container: ServiceContainer = websocket.app.state.container
    buffer = bytearray()
    session_id = "voice-session"
    locale = "pt-BR"
    try:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                return
            if "bytes" in message and message["bytes"] is not None:
                buffer.extend(message["bytes"])
                continue

            if "text" not in message or message["text"] is None:
                continue

            payload = json.loads(message["text"])
            if not isinstance(payload, dict):
                continue
            message_type = str(payload.get("type", ""))
            if message_type == "start":
                buffer.clear()
                session_id = str(payload.get("session_id", "voice-session"))
                locale = str(payload.get("locale", "pt-BR"))
                await websocket.send_json({"type": "started"})
                continue

            if message_type != "end":
                continue

            transcript = await container.stt.transcribe(bytes(buffer))
            normalized_transcript = transcript.strip()
            if not normalized_transcript:
                fallback_text = "Nao consegui entender o audio. Fale novamente com mais clareza."
                audio_bytes = await container.tts.synthesize(text=fallback_text, lang=locale)
                wav_bytes = _pcm_to_wav(
                    audio_bytes=audio_bytes,
                    sample_rate=container.settings.voice.tts.sample_rate,
                )
                await websocket.send_json({"type": "error", "text": fallback_text})
                await websocket.send_json(
                    {
                        "type": "audio",
                        "audio_base64": base64.b64encode(wav_bytes).decode("ascii")
                        if wav_bytes
                        else "",
                    }
                )
                await websocket.send_json({"type": "done", "text": fallback_text})
                buffer.clear()
                continue

            response = await container.orchestrator.handle_message(
                session_id=session_id,
                message=normalized_transcript,
                locale=locale,
            )
            audio_bytes = await container.tts.synthesize(text=response.response_text, lang=locale)
            wav_bytes = _pcm_to_wav(
                audio_bytes=audio_bytes,
                sample_rate=container.settings.voice.tts.sample_rate,
            )
            await websocket.send_json({"type": "transcript", "text": normalized_transcript})
            for chunk in _chunk_response(response.response_text):
                await websocket.send_json({"type": "chunk", "text": chunk})
            await websocket.send_json(
                {
                    "type": "audio",
                    "audio_base64": base64.b64encode(wav_bytes).decode("ascii")
                    if wav_bytes
                    else "",
                }
            )
            await websocket.send_json({"type": "done", "text": response.response_text})
            buffer.clear()
    except WebSocketDisconnect:
        return


def _chunk_response(text: str, chunk_size: int = 72) -> list[str]:
    words = text.split()
    chunks: list[str] = []
    current_chunk = ""
    for word in words:
        candidate = word if not current_chunk else f"{current_chunk} {word}"
        if len(candidate) <= chunk_size:
            current_chunk = candidate
            continue
        chunks.append(current_chunk)
        current_chunk = word
    if current_chunk:
        chunks.append(current_chunk)
    return chunks


def _pcm_to_wav(audio_bytes: bytes, sample_rate: int) -> bytes:
    if not audio_bytes:
        return b""

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_bytes)
    return buffer.getvalue()
