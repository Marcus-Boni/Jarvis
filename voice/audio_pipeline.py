"""Async voice pipeline placeholder."""

from __future__ import annotations

from voice.stt import SpeechToTextService
from voice.tts import TextToSpeechService
from voice.vad import VoiceActivityDetector


class AudioPipeline:
    """Composes VAD, STT, and TTS for future live voice interactions."""

    def __init__(
        self,
        vad: VoiceActivityDetector,
        stt: SpeechToTextService,
        tts: TextToSpeechService,
    ) -> None:
        self._vad = vad
        self._stt = stt
        self._tts = tts

