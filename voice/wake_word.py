"""Porcupine-based wake word detector for Jarvis."""

from __future__ import annotations

import asyncio
import importlib
import os
import struct
from typing import Any

from loguru import logger

from core.config import AppSettings


class WakeWordDetector:
    """Detect the configured wake word using pvporcupine when available."""

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._logger = logger.bind(component="wake_word")
        self._porcupine: Any | None = None
        self._access_key = os.environ.get("PORCUPINE_ACCESS_KEY", "")

    @property
    def mode(self) -> str:
        """Return the configured wake word mode."""

        return self._settings.voice.wake_word_mode.lower()

    @property
    def uses_porcupine(self) -> bool:
        """Return whether Porcupine should be used for wake word detection."""

        return self.mode == "porcupine" and bool(self._access_key)

    async def is_wake_word(self, audio_frame: bytes) -> bool:
        """Return True when the wake word is detected in the PCM frame."""

        if not self.uses_porcupine:
            return False
        return await asyncio.to_thread(self._check_frame, audio_frame)

    def _check_frame(self, audio_frame: bytes) -> bool:
        porcupine = self._get_porcupine()
        frame_length = int(porcupine.frame_length)
        required_bytes = frame_length * 2
        if len(audio_frame) < required_bytes:
            return False
        samples = struct.unpack_from(f"{frame_length}h", audio_frame[:required_bytes])
        result = int(porcupine.process(list(samples)))
        return result >= 0

    def _get_porcupine(self) -> Any:
        if self._porcupine is not None:
            return self._porcupine
        pvporcupine = importlib.import_module("pvporcupine")
        self._porcupine = pvporcupine.create(
            access_key=self._access_key,
            keywords=[self._settings.jarvis.wake_word.lower()],
        )
        return self._porcupine

    def cleanup(self) -> None:
        """Release any allocated Porcupine resources."""

        if self._porcupine is None:
            return
        try:
            self._porcupine.delete()
        except Exception as exc:  # pragma: no cover
            self._logger.warning("wake_word_cleanup_failed error={}", exc)
        self._porcupine = None
