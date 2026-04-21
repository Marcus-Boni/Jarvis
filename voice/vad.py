"""Silero VAD integration for realtime speech detection."""

from __future__ import annotations

import asyncio
import importlib
from dataclasses import dataclass
from typing import Any

from core.config import AppSettings


@dataclass
class _VadState:
    silence_ms: float = 0.0


class VoiceActivityDetector:
    """Realtime speech detector backed by Silero VAD."""

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._sample_rate = settings.voice.sample_rate
        self._threshold = settings.voice.vad.threshold
        self._min_silence_ms = float(settings.voice.vad.min_silence_ms)
        self._model: Any | None = None
        self._state = _VadState()

    async def detect(self, audio_frame: bytes) -> bool:
        """Return True when the given PCM frame contains speech."""

        if not audio_frame:
            return False

        probability = await asyncio.to_thread(self._compute_probability, audio_frame)
        frame_ms = len(audio_frame) / 2 / self._sample_rate * 1000.0
        if probability >= self._threshold:
            self._state.silence_ms = 0.0
            return True

        self._state.silence_ms += frame_ms
        return self._state.silence_ms < self._min_silence_ms

    def _compute_probability(self, audio_frame: bytes) -> float:
        model = self._get_model()

        import numpy as np

        torch = importlib.import_module("torch")

        pcm = np.frombuffer(audio_frame, dtype=np.int16).astype("float32") / 32768.0
        tensor = torch.from_numpy(pcm)
        if tensor.ndim == 1:
            tensor = tensor.unsqueeze(0)
        probability = float(model(tensor, self._sample_rate).item())
        return probability

    def _get_model(self) -> Any:
        if self._model is not None:
            return self._model

        torch = importlib.import_module("torch")

        torch.set_num_threads(1)
        model, _ = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            onnx=False,
            trust_repo=True,
        )
        self._model = model
        return self._model
