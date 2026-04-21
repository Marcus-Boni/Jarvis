"""Voice activity detection contracts for future Silero integration."""

from __future__ import annotations


class VoiceActivityDetector:
    """Phase 1 placeholder VAD service."""

    async def detect(self, audio_frame: bytes) -> bool:
        """Return whether speech is present in an audio frame."""

        raise NotImplementedError("VAD integration is scheduled for Phase 1.")

