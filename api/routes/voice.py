"""Voice processing routes backed by the realtime audio pipeline."""

from __future__ import annotations

import base64
import io
import wave
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel

from api.dependencies import get_container, require_local_token
from core.service_container import ServiceContainer

router = APIRouter(prefix="/api/voice", tags=["voice"])
ContainerDependency = Annotated[ServiceContainer, Depends(get_container)]
audio_file_field = File(...)
session_id_form = Form(default="voice-session")
locale_form = Form(default="pt-BR")


class VoiceProcessResponse(BaseModel):
    transcript: str
    response_text: str
    audio_base64: str = ""
    used_fallback_llm: bool


@router.post(
    "/stream",
    response_model=VoiceProcessResponse,
    dependencies=[Depends(require_local_token)],
)
async def process_voice_stream(
    container: ContainerDependency,
    audio_file: UploadFile = audio_file_field,
    session_id: str = session_id_form,
    locale: str = locale_form,
) -> VoiceProcessResponse:
    """Receive uploaded audio, transcribe it, process it, and synthesize a reply."""

    del audio_file.filename
    raw_audio = await audio_file.read()
    transcript = await container.stt.transcribe(raw_audio)
    response = await container.orchestrator.handle_message(
        session_id=session_id,
        message=transcript,
        locale=locale,
    )
    audio_bytes = await container.tts.synthesize(text=response.response_text, lang=locale)
    wav_bytes = _pcm_to_wav(
        audio_bytes=audio_bytes,
        sample_rate=container.settings.voice.tts.sample_rate,
    )
    return VoiceProcessResponse(
        transcript=transcript,
        response_text=response.response_text,
        audio_base64=base64.b64encode(wav_bytes).decode("ascii") if wav_bytes else "",
        used_fallback_llm=response.used_fallback_llm,
    )


@router.get("/status", dependencies=[Depends(require_local_token)])
async def voice_status(container: ContainerDependency) -> dict[str, object]:
    """Return current realtime voice pipeline status."""

    return {
        "enabled": container.settings.voice.enabled,
        "active": container.audio_pipeline.is_active,
        "sample_rate": container.settings.voice.sample_rate,
        "wake_word_enabled": container.settings.voice.wake_word_enabled,
    }


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
