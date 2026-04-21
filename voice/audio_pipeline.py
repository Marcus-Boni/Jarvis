"""Async microphone capture, VAD gating, STT, and TTS playback."""

from __future__ import annotations

import asyncio
import importlib
import tempfile
import wave
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from core.config import AppSettings
from voice.stt import WhisperTranscriber
from voice.tts import PiperTTSService
from voice.vad import VoiceActivityDetector


class AudioPipeline:
    """Compose VAD, STT, and TTS into a realtime voice service."""

    def __init__(
        self,
        settings: AppSettings,
        vad: VoiceActivityDetector,
        stt: WhisperTranscriber,
        tts: PiperTTSService,
    ) -> None:
        self._settings = settings
        self._vad = vad
        self._stt = stt
        self._tts = tts
        self._frame_queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=200)
        self._input_stream: Any | None = None
        self._is_active = False

    @property
    def is_active(self) -> bool:
        """Return whether the microphone stream is currently active."""

        return self._is_active

    async def start_listening(self) -> AsyncIterator[str]:
        """Yield transcribed utterances from the microphone stream."""

        if not self._is_active:
            await self._open_input_stream()

        captured_frames: list[bytes] = []
        while self._is_active:
            frame = await self._frame_queue.get()
            has_speech = await self._vad.detect(frame)
            if has_speech:
                captured_frames.append(frame)
                continue

            if not captured_frames:
                continue

            audio_bytes = b"".join(captured_frames)
            captured_frames.clear()
            transcript = await self._stt.transcribe(
                _pcm_to_wav_bytes(
                    audio_bytes=audio_bytes,
                    sample_rate=self._settings.voice.sample_rate,
                    channels=self._settings.voice.channels,
                )
            )
            normalized_transcript = transcript.strip()
            if not normalized_transcript:
                continue

            if self._settings.voice.wake_word_enabled:
                wake_word = self._settings.jarvis.wake_word.lower()
                if wake_word not in normalized_transcript.lower():
                    continue
            yield normalized_transcript

    async def speak(self, text: str, locale: str) -> None:
        """Synthesize and play audio through the default output device."""

        audio_bytes = await self._tts.synthesize(text=text, lang=locale)
        if not audio_bytes:
            return
        await asyncio.to_thread(self._play_audio_sync, audio_bytes)

    async def stop(self) -> None:
        """Stop any live microphone stream."""

        self._is_active = False
        if self._input_stream is not None:
            await asyncio.to_thread(self._input_stream.stop)
            await asyncio.to_thread(self._input_stream.close)
            self._input_stream = None

    async def _open_input_stream(self) -> None:
        sd = importlib.import_module("sounddevice")

        loop = asyncio.get_running_loop()

        def callback(indata: bytes, frames: int, time_info: object, status: object) -> None:
            del frames, time_info, status
            loop.call_soon_threadsafe(self._enqueue_frame, bytes(indata))

        self._input_stream = sd.RawInputStream(
            samplerate=self._settings.voice.sample_rate,
            blocksize=self._settings.voice.chunk_size,
            channels=self._settings.voice.channels,
            dtype="int16",
            callback=callback,
        )
        assert self._input_stream is not None
        input_stream = self._input_stream
        await asyncio.to_thread(input_stream.start)
        self._is_active = True

    def _enqueue_frame(self, frame: bytes) -> None:
        try:
            self._frame_queue.put_nowait(frame)
        except asyncio.QueueFull:
            return

    def _play_audio_sync(self, audio_bytes: bytes) -> None:
        sd = importlib.import_module("sounddevice")

        with sd.RawOutputStream(
            samplerate=self._settings.voice.tts.sample_rate,
            channels=1,
            dtype="int16",
        ) as output_stream:
            output_stream.write(audio_bytes)


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
