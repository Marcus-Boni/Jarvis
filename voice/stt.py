"""Speech-to-text service contracts for future faster-whisper integration."""

from __future__ import annotations


class SpeechToTextService:
    """Phase 1 placeholder STT service."""

    async def transcribe(self, audio_bytes: bytes) -> str:
        """Transcribe audio to text."""

        raise NotImplementedError("STT integration is scheduled for Phase 1.")

