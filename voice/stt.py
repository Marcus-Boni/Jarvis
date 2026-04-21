"""faster-whisper transcription service."""

from __future__ import annotations

import asyncio
import tempfile
import wave
from pathlib import Path
from typing import Any

from core.config import AppSettings


class WhisperTranscriber:
    """Transcribe audio with faster-whisper without blocking the event loop."""

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._model: Any | None = None
        self._model_device = settings.voice.stt.device
        self._compute_type = settings.voice.stt.compute_type

    async def transcribe(self, audio_bytes: bytes) -> str:
        """Return a transcription for WAV or raw PCM input bytes."""

        if not audio_bytes:
            return ""
        return await asyncio.to_thread(self._transcribe_sync, audio_bytes)

    def _transcribe_sync(self, audio_bytes: bytes) -> str:
        model = self._get_model()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            wav_bytes = audio_bytes if audio_bytes[:4] == b"RIFF" else _pcm_to_wav_bytes(
                audio_bytes,
                sample_rate=self._settings.voice.sample_rate,
                channels=self._settings.voice.channels,
            )
            temp_file.write(wav_bytes)

        try:
            segments, _ = model.transcribe(
                str(temp_path),
                beam_size=5,
                language=self._settings.voice.stt.language,
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": self._settings.voice.vad.min_silence_ms},
            )
            text = " ".join(segment.text.strip() for segment in list(segments)).strip()
            return text
        finally:
            temp_path.unlink(missing_ok=True)

    def _get_model(self) -> Any:
        if self._model is not None:
            return self._model

        from faster_whisper import WhisperModel  # type: ignore[import-untyped]

        try:
            self._model = WhisperModel(
                self._settings.voice.stt.model,
                device=self._model_device,
                compute_type=self._compute_type,
            )
        except Exception:
            self._model = WhisperModel(
                self._settings.voice.stt.model,
                device="cpu",
                compute_type="int8",
            )
        return self._model


def _pcm_to_wav_bytes(audio_bytes: bytes, sample_rate: int, channels: int) -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        with wave.open(str(temp_path), "wb") as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_bytes)
        return temp_path.read_bytes()
    finally:
        temp_path.unlink(missing_ok=True)

