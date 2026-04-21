from __future__ import annotations

from pathlib import Path

from core.config import AppSettings


def test_load_settings_from_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "jarvis.yaml"
    config_path.write_text(
        """
jarvis:
  name: "TestJarvis"
api:
  port: 9999
voice:
  wake_word_mode: "porcupine"
skills:
  volume:
    enabled: false
  notion:
    default_parent_page_id: "page-123"
  clipboard:
    enabled: false
""".strip(),
        encoding="utf-8",
    )

    env_path = tmp_path / ".env"
    env_path.write_text("", encoding="utf-8")

    settings = AppSettings.load(config_path=config_path, env_file=env_path)

    assert settings.jarvis.name == "TestJarvis"
    assert settings.api.port == 9999
    assert settings.voice.wake_word_mode == "porcupine"
    assert settings.skills.volume.enabled is False
    assert settings.skills.clipboard.enabled is False
    assert settings.notion.default_parent_id == "page-123"
