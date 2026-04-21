"""Text-to-speech service contracts for future Piper integration."""

from __future__ import annotations


class TextToSpeechService:
    """Phase 1 placeholder TTS service."""

    async def synthesize(self, text: str) -> bytes:
        """Synthesize speech audio from text."""

        raise NotImplementedError("TTS integration is scheduled for Phase 1.")

