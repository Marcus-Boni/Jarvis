from voice.stt import _detect_audio_suffix


def test_detect_audio_suffix_for_browser_webm() -> None:
    assert _detect_audio_suffix(b"\x1a\x45\xdf\xa3rest-of-webm") == ".webm"


def test_detect_audio_suffix_for_wav() -> None:
    assert _detect_audio_suffix(b"RIFFrest-of-wav") == ".wav"
