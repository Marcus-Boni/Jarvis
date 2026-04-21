"""Initial Spotify skill scaffold."""

from __future__ import annotations

from core.models import Intent, IntentCategory, RequestContext, SkillResult
from skills.base_skill import BaseSkill


class SpotifySkill(BaseSkill):
    """Scaffold for Spotify control via API."""

    name = "spotify"
    description = "Controla playback e pesquisa no Spotify."
    triggers = ["spotify", "tocar música", "play playlist", "pause spotify"]

    async def can_handle(self, intent: Intent) -> float:
        if intent.category is IntentCategory.SPOTIFY:
            return 0.95
        if "spotify" in intent.raw_text.lower():
            return 0.7
        return 0.0

    async def execute(self, intent: Intent, context: RequestContext) -> SkillResult:
        requested_query = intent.entities.get("query", intent.raw_text)
        return SkillResult(
            skill_name=self.name,
            success=False,
            message=(
                "O fluxo do Spotify já está classificado e roteado, "
                "mas a integração OAuth/Playback entra na Fase 2."
            ),
            data={"phase": "phase_2", "requested_query": requested_query},
            follow_up_required=True,
        )

