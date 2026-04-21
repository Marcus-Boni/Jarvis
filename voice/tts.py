"""Piper text-to-speech integration."""

from __future__ import annotations

import asyncio
import shutil
import subprocess
import sys
from pathlib import Path

from core.config import AppSettings


class PiperTTSService:
    """Synthesize raw PCM audio with Piper."""

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    async def synthesize(self, text: str, lang: str) -> bytes:
        """Return raw PCM audio bytes for the given text."""

        if not text.strip():
            return b""
        return await asyncio.to_thread(self._synthesize_sync, text, lang)

    def _synthesize_sync(self, text: str, lang: str) -> bytes:
        model_path = _select_model_path(settings=self._settings, lang=lang)
        if not model_path.exists():
            raise FileNotFoundError(f"Piper model not found at {model_path}")

        binary_path = Path(self._settings.voice.tts.binary_path)
        if binary_path.exists():
            command = [
                str(binary_path),
                "--model",
                str(model_path),
                "--text",
                text,
                "--output-raw",
            ]
        elif shutil.which("piper") is not None:
            command = [
                "piper",
                "--model",
                str(model_path),
                "--text",
                text,
                "--output-raw",
            ]
        else:
            command = [
                sys.executable,
                "-m",
                "piper",
                "-m",
                str(model_path),
                "--output-raw",
                "--",
                text,
            ]

        process = subprocess.run(command, check=True, capture_output=True, text=False)
        return bytes(process.stdout)


def _select_model_path(settings: AppSettings, lang: str) -> Path:
    normalized_lang = lang.lower()
    if normalized_lang.startswith("en"):
        return Path(settings.voice.tts.en_model_path)
    return Path(settings.voice.tts.pt_model_path)
