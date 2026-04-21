"""Initial browser search skill scaffold."""

from __future__ import annotations

from core.models import Intent, IntentCategory, RequestContext, SkillResult
from skills.base_skill import BaseSkill


class BrowserSearchSkill(BaseSkill):
    """Scaffold for web search and summarization."""

    name = "browser_search"
    description = "Pesquisa web com fallback para navegação assistida."
    triggers = ["pesquise", "procure", "busque na web", "search the web"]

    async def can_handle(self, intent: Intent) -> float:
        if intent.category is IntentCategory.BROWSER:
            return 0.9
        if "pesquis" in intent.raw_text.lower():
            return 0.58
        return 0.0

    async def execute(self, intent: Intent, context: RequestContext) -> SkillResult:
        return SkillResult(
            skill_name=self.name,
            success=False,
            message=(
                "A skill de pesquisa já está registrada no orquestrador, "
                "mas a coleta DuckDuckGo/Playwright será ligada na Fase 2."
            ),
            data={"phase": "phase_2"},
            follow_up_required=True,
        )

