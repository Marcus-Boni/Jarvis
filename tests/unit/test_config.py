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
""".strip(),
        encoding="utf-8",
    )

    env_path = tmp_path / ".env"
    env_path.write_text("", encoding="utf-8")

    settings = AppSettings.load(config_path=config_path, env_file=env_path)

    assert settings.jarvis.name == "TestJarvis"
    assert settings.api.port == 9999

