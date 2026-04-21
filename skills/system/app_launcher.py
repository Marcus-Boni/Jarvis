"""Initial application launcher skill scaffold."""

from __future__ import annotations

from core.models import Intent, IntentCategory, RequestContext, SkillResult
from skills.base_skill import BaseSkill


class AppLauncherSkill(BaseSkill):
    """Scaffold for OS application launching and window focusing."""

    name = "app_launcher"
    description = "Abre aplicativos locais e, nas próximas fases, foca janelas existentes."
    triggers = ["abrir aplicativo", "abrir vscode", "abrir spotify", "open app"]

    async def can_handle(self, intent: Intent) -> float:
        if intent.category is IntentCategory.SYSTEM_CONTROL:
            return 0.92
        if any("abr" in action.lower() for action in intent.actions):
            return 0.62
        return 0.0

    async def execute(self, intent: Intent, context: RequestContext) -> SkillResult:
        requested_target = intent.entities.get("app", "aplicativo")
        return SkillResult(
            skill_name=self.name,
            success=False,
            message=(
                f"A skill de abertura de {requested_target} já está roteada, "
                "mas a execução real do sistema operacional entra na Fase 2."
            ),
            data={"phase": "phase_2", "requested_target": requested_target},
            follow_up_required=True,
        )

