"""Skill registry and bootstrap loader."""

from __future__ import annotations

from collections.abc import Iterable

from skills.base_skill import BaseSkill
from skills.browser.search import BrowserSearchSkill
from skills.media.spotify_skill import SpotifySkill
from skills.system.app_launcher import AppLauncherSkill


class SkillLoader:
    """Manages builtin and future hot-reloaded Jarvis skills."""

    def __init__(self) -> None:
        self._skills: dict[str, BaseSkill] = {}

    async def load_builtin_skills(self) -> None:
        """Instantiate builtin skills."""

        for skill in [AppLauncherSkill(), BrowserSearchSkill(), SpotifySkill()]:
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

