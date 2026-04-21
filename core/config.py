"""Configuration loading for Jarvis using YAML plus environment variables."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class JarvisIdentityConfig(BaseModel):
    name: str = "Jarvis"
    language: str = "pt-BR"
    wake_word: str = "jarvis"
    timezone: str = "UTC"


class LlmConfig(BaseModel):
    provider: str = "ollama"
    model: str = "mistral-nemo:12b-instruct-2407-q4_K_M"
    fallback_model: str = "phi3:mini"
    base_url: str = "http://localhost:11434"
    context_window: int = 8192
    temperature: float = 0.4
    stream: bool = True
    request_timeout_seconds: float = 90.0


class SttConfig(BaseModel):
    model: str = "large-v3"
    device: str = "cuda"
    compute_type: str = "float16"
    language: str = "pt"


class TtsConfig(BaseModel):
    model: str = "pt_BR-faber-medium"
    speed: float = 1.0


class VadConfig(BaseModel):
    threshold: float = 0.5
    min_silence_ms: int = 500


class VoiceConfig(BaseModel):
    enabled: bool = False
    stt: SttConfig = Field(default_factory=SttConfig)
    tts: TtsConfig = Field(default_factory=TtsConfig)
    vad: VadConfig = Field(default_factory=VadConfig)


class MemoryConfig(BaseModel):
    provider: str = "chromadb"
    persist_directory: str = "./data/chroma"
    conversations_directory: str = "./data/conversations"
    embedding_model: str = "nomic-embed-text"
    max_context_docs: int = 5


class ApiConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    cors_origins: list[str] = Field(default_factory=list)


class DashboardConfig(BaseModel):
    origin: str = "http://localhost:3000"


class EnvironmentSecrets(BaseSettings):
    """Secrets and local overrides that should not live in YAML."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    jarvis_auth_token: str = ""
    notion_token: str = ""
    spotify_client_id: str = ""
    spotify_redirect_uri: str = "http://localhost:8000/api/oauth/spotify/callback"
    google_client_secrets_file: str = ""
    google_token_file: str = ""


class AppSettings(BaseModel):
    """Validated application settings used across the runtime."""

    jarvis: JarvisIdentityConfig = Field(default_factory=JarvisIdentityConfig)
    llm: LlmConfig = Field(default_factory=LlmConfig)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)
    dashboard: DashboardConfig = Field(default_factory=DashboardConfig)
    env: EnvironmentSecrets = Field(default_factory=EnvironmentSecrets)

    @classmethod
    def load(
        cls,
        config_path: str | Path = "config/jarvis.yaml",
        env_file: str | Path = ".env",
    ) -> "AppSettings":
        """Load settings from YAML and environment."""

        yaml_payload = _read_yaml(config_path)
        env_settings = EnvironmentSecrets(_env_file=Path(env_file))
        return cls.model_validate({**yaml_payload, "env": env_settings.model_dump()})


def _read_yaml(config_path: str | Path) -> dict[str, Any]:
    """Read a YAML config file if present."""

    config_file = Path(config_path)
    if not config_file.exists():
        return {}

    with config_file.open("r", encoding="utf-8") as file_handle:
        raw_data = yaml.safe_load(file_handle) or {}

    if not isinstance(raw_data, dict):
        return {}

    return raw_data
