"""Configuration loading for Jarvis using YAML plus environment variables."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class JarvisIdentityConfig(BaseModel):
    name: str = "Jarvis"
    language: str = "pt-BR"
    wake_word: str = "jarvis"
    timezone: str = "UTC"


class LlmConfig(BaseModel):
    provider: str = "ollama"
    model: str = "qwen2.5:7b"
    fallback_model: str = "qwen2.5:1.5b"
    base_url: str = "http://localhost:11434"
    context_window: int = 8192
    temperature: float = 0.4
    stream: bool = True
    request_timeout_seconds: float = 90.0


class SttConfig(BaseModel):
    model: str = "medium"
    device: str = "cuda"
    compute_type: str = "float16"
    language: str = "pt"


class TtsConfig(BaseModel):
    model: str = "pt_BR-faber-medium"
    fallback_model: str = "en_US-ryan-high"
    binary_path: str = "./bin/piper/piper.exe"
    pt_model_path: str = "./models/piper/pt_BR-faber-medium.onnx"
    en_model_path: str = "./models/piper/en_US-ryan-high.onnx"
    sample_rate: int = 22050
    speed: float = 1.0


class VadConfig(BaseModel):
    threshold: float = 0.5
    min_silence_ms: int = 500


class VoiceConfig(BaseModel):
    enabled: bool = False
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 512
    wake_word_enabled: bool = True
    wake_word_mode: str = "text"
    stt: SttConfig = Field(default_factory=SttConfig)
    tts: TtsConfig = Field(default_factory=TtsConfig)
    vad: VadConfig = Field(default_factory=VadConfig)


class MemoryConfig(BaseModel):
    provider: str = "chromadb"
    persist_directory: str = "./data/chroma"
    conversations_directory: str = "./data/conversations"
    embedding_model: str = "nomic-embed-text"
    max_context_docs: int = 5
    collection_name: str = "jarvis_memory"


class BrowserConfig(BaseModel):
    mode: str = "system_default"
    headless_for_scraping: bool = True
    search_engine: str = "duckduckgo"
    max_results: int = 5
    snippet_char_limit: int = 2200


class SkillToggleConfig(BaseModel):
    enabled: bool = True


class AppLauncherSkillConfig(SkillToggleConfig):
    focus_existing: bool = True


class BrowserSearchSkillConfig(SkillToggleConfig):
    open_for_user_threshold: float = 0.7


class NotionSkillSettings(SkillToggleConfig):
    default_parent_page_id: str = ""


class AutoMemorySkillConfig(SkillToggleConfig):
    min_exchange_length: int = 20


class SkillsConfig(BaseModel):
    app_launcher: AppLauncherSkillConfig = Field(default_factory=AppLauncherSkillConfig)
    browser_search: BrowserSearchSkillConfig = Field(
        default_factory=BrowserSearchSkillConfig
    )
    clipboard: SkillToggleConfig = Field(default_factory=SkillToggleConfig)
    file_manager: SkillToggleConfig = Field(default_factory=SkillToggleConfig)
    screenshot: SkillToggleConfig = Field(default_factory=SkillToggleConfig)
    notification: SkillToggleConfig = Field(default_factory=SkillToggleConfig)
    spotify: SkillToggleConfig = Field(default_factory=SkillToggleConfig)
    notion: NotionSkillSettings = Field(default_factory=NotionSkillSettings)
    outlook: SkillToggleConfig = Field(default_factory=SkillToggleConfig)
    calendar: SkillToggleConfig = Field(default_factory=SkillToggleConfig)
    volume: SkillToggleConfig = Field(default_factory=SkillToggleConfig)
    auto_memory: AutoMemorySkillConfig = Field(default_factory=AutoMemorySkillConfig)


class SpotifyConfig(BaseModel):
    token_path: str = "./data/spotify_token.json"
    scopes: list[str] = Field(
        default_factory=lambda: [
            "user-read-playback-state",
            "user-modify-playback-state",
            "user-read-currently-playing",
        ]
    )


class NotionConfig(BaseModel):
    default_parent_id: str = ""
    default_parent_type: str = "page_id"


class OutlookConfig(BaseModel):
    token_path: str = "./data/outlook_token.json"
    scopes: list[str] = Field(
        default_factory=lambda: ["Mail.Read", "Mail.Send", "Calendars.ReadWrite"]
    )


class GoogleConfig(BaseModel):
    token_path: str = "./data/google_token.json"
    scopes: list[str] = Field(
        default_factory=lambda: [
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/calendar.events",
        ]
    )


class TelemetryConfig(BaseModel):
    error_log_path: str = "./data/logs/errors.jsonl"


class ApiConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    cors_origins: list[str] = Field(default_factory=list)


class DashboardConfig(BaseModel):
    origin: str = "http://localhost:3000"


class EnvironmentSecrets(BaseModel):
    """Secrets and local overrides that should not live in YAML."""

    jarvis_auth_token: str = ""
    notion_token: str = ""
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = "http://127.0.0.1:8000/api/oauth/spotify/callback"
    google_client_secrets_file: str = ""
    google_token_file: str = "data/google_token.json"
    outlook_client_id: str = ""
    outlook_tenant_id: str = "common"
    outlook_token_file: str = "data/outlook_token.json"


class AppSettings(BaseModel):
    """Validated application settings used across the runtime."""

    jarvis: JarvisIdentityConfig = Field(default_factory=JarvisIdentityConfig)
    llm: LlmConfig = Field(default_factory=LlmConfig)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    skills: SkillsConfig = Field(default_factory=SkillsConfig)
    spotify: SpotifyConfig = Field(default_factory=SpotifyConfig)
    notion: NotionConfig = Field(default_factory=NotionConfig)
    outlook: OutlookConfig = Field(default_factory=OutlookConfig)
    google: GoogleConfig = Field(default_factory=GoogleConfig)
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)
    dashboard: DashboardConfig = Field(default_factory=DashboardConfig)
    env: EnvironmentSecrets = Field(default_factory=EnvironmentSecrets)

    @classmethod
    def load(
        cls,
        config_path: str | Path = "config/jarvis.yaml",
        env_file: str | Path = ".env",
    ) -> AppSettings:
        """Load settings from YAML and environment."""

        yaml_payload = _read_yaml(config_path)
        env_settings = EnvironmentSecrets.model_validate(_read_env_file(env_file))
        settings = cls.model_validate(
            {**yaml_payload, "env": env_settings.model_dump()}
        )
        if (
            not settings.notion.default_parent_id
            and settings.skills.notion.default_parent_page_id
        ):
            settings.notion.default_parent_id = (
                settings.skills.notion.default_parent_page_id
            )
        return settings


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


def _read_env_file(env_file: str | Path) -> dict[str, str]:
    """Read .env-style values and merge them over process environment defaults."""

    payload: dict[str, str] = {}
    target_file = Path(env_file)
    if target_file.exists():
        for raw_line in target_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            payload[key.strip().lower()] = value.strip().strip("\"'")

    merged_payload = {
        "jarvis_auth_token": os.getenv(
            "JARVIS_AUTH_TOKEN", payload.get("jarvis_auth_token", "")
        ),
        "notion_token": os.getenv("NOTION_TOKEN", payload.get("notion_token", "")),
        "spotify_client_id": os.getenv(
            "SPOTIFY_CLIENT_ID", payload.get("spotify_client_id", "")
        ),
        "spotify_client_secret": os.getenv(
            "SPOTIFY_CLIENT_SECRET", payload.get("spotify_client_secret", "")
        ),
        "spotify_redirect_uri": os.getenv(
            "SPOTIFY_REDIRECT_URI",
            payload.get(
                "spotify_redirect_uri",
                "http://127.0.0.1:8000/api/oauth/spotify/callback",
            ),
        ),
        "google_client_secrets_file": os.getenv(
            "GOOGLE_CLIENT_SECRETS_FILE", payload.get("google_client_secrets_file", "")
        ),
        "google_token_file": os.getenv(
            "GOOGLE_TOKEN_FILE",
            payload.get("google_token_file", "data/google_token.json"),
        ),
        "outlook_client_id": os.getenv(
            "OUTLOOK_CLIENT_ID", payload.get("outlook_client_id", "")
        ),
        "outlook_tenant_id": os.getenv(
            "OUTLOOK_TENANT_ID", payload.get("outlook_tenant_id", "common")
        ),
        "outlook_token_file": os.getenv(
            "OUTLOOK_TOKEN_FILE",
            payload.get("outlook_token_file", "data/outlook_token.json"),
        ),
    }
    return merged_payload
