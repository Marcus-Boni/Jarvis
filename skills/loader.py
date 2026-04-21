"""Skill registry and bootstrap loader."""

from __future__ import annotations

from core.config import AppSettings
from core.error_telemetry import ErrorTelemetry
from core.runtime_events import RuntimeEventBroker
from llm.ollama_client import OllamaClient
from skills.base_skill import BaseSkill
from skills.browser.search import BrowserSearchSkill
from skills.media.spotify_skill import SpotifySkill
from skills.productivity.calendar_skill import CalendarSkill
from skills.productivity.notion_skill import NotionSkill
from skills.productivity.outlook_skill import OutlookSkill
from skills.system.app_launcher import AppLauncherSkill
from skills.system.volume_skill import VolumeSkill


class SkillLoader:
    """Manage builtin and future hot-reloaded Jarvis skills."""

    def __init__(
        self,
        settings: AppSettings,
        llm_client: OllamaClient,
        event_broker: RuntimeEventBroker,
        error_telemetry: ErrorTelemetry,
    ) -> None:
        self._settings = settings
        self._llm_client = llm_client
        self._event_broker = event_broker
        self._error_telemetry = error_telemetry
        self._skills: dict[str, BaseSkill] = {}

    async def load_builtin_skills(self) -> None:
        """Instantiate builtin skills."""

        for skill in [
            AppLauncherSkill(
                settings=self._settings,
                event_broker=self._event_broker,
                error_telemetry=self._error_telemetry,
            ),
            BrowserSearchSkill(
                settings=self._settings,
                llm_client=self._llm_client,
                event_broker=self._event_broker,
                error_telemetry=self._error_telemetry,
            ),
            SpotifySkill(
                settings=self._settings,
                event_broker=self._event_broker,
                error_telemetry=self._error_telemetry,
            ),
            NotionSkill(
                settings=self._settings,
                event_broker=self._event_broker,
                error_telemetry=self._error_telemetry,
            ),
            OutlookSkill(
                settings=self._settings,
                llm_client=self._llm_client,
                event_broker=self._event_broker,
                error_telemetry=self._error_telemetry,
            ),
            CalendarSkill(
                settings=self._settings,
                llm_client=self._llm_client,
                event_broker=self._event_broker,
                error_telemetry=self._error_telemetry,
            ),
            VolumeSkill(),
        ]:
            skill.enabled = _is_skill_enabled(settings=self._settings, skill_name=skill.name)
            self._skills[skill.name] = skill

    def list_enabled(self) -> list[BaseSkill]:
        """Return enabled skills."""

        return [skill for skill in self._skills.values() if skill.enabled]

    def list_all(self) -> list[BaseSkill]:
        """Return all loaded skills."""

        return list(self._skills.values())

    def set_enabled(self, skill_name: str, enabled: bool) -> bool:
        """Enable or disable a skill by name."""

        target = self._skills.get(skill_name)
        if target is None:
            return False
        target.enabled = enabled
        return True


def _is_skill_enabled(settings: AppSettings, skill_name: str) -> bool:
    settings_map = {
        "app_launcher": settings.skills.app_launcher.enabled,
        "browser_search": settings.skills.browser_search.enabled,
        "spotify": settings.skills.spotify.enabled,
        "notion": settings.skills.notion.enabled,
        "outlook": settings.skills.outlook.enabled,
        "calendar": settings.skills.calendar.enabled,
        "volume": settings.skills.volume.enabled,
    }
    return settings_map.get(skill_name, True)
