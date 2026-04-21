"""Windows toast notification skill."""

from __future__ import annotations

import asyncio
import subprocess
from typing import ClassVar

from core.models import Intent, RequestContext, SkillResult
from skills.base_skill import BaseSkill


class NotificationSkill(BaseSkill):
    """Send Windows toast notifications."""

    name: ClassVar[str] = "notification"
    description: ClassVar[str] = "Envia notificacoes nativas do Windows."
    triggers: ClassVar[list[str]] = [
        "me lembre",
        "me notifique",
        "notificacao",
        "aviso",
        "lembrete",
    ]

    async def can_handle(self, intent: Intent) -> float:
        lowered_text = intent.raw_text.lower()
        if any(
            token in lowered_text
            for token in ["lembrete", "me lembre", "notifica", "avise", "remind"]
        ):
            return 0.86
        return 0.0

    async def execute(self, intent: Intent, context: RequestContext) -> SkillResult:
        del context
        message = intent.entities.get("message") or _extract_reminder_text(intent.raw_text)
        title = intent.entities.get("title") or "Jarvis"
        try:
            await asyncio.to_thread(self._send_toast, title, message)
            return SkillResult(
                skill_name=self.name,
                success=True,
                message=f"Notificacao enviada: {message}",
                data={"title": title, "message": message},
            )
        except Exception as exc:  # pragma: no cover
            return SkillResult(
                skill_name=self.name,
                success=False,
                message=f"Erro ao enviar notificacao: {exc}",
            )

    def _send_toast(self, title: str, message: str) -> None:
        ps_script = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
$template = @"
<toast>
  <visual>
    <binding template="ToastGeneric">
      <text>{title}</text>
      <text>{message}</text>
    </binding>
  </visual>
</toast>
"@
$xml = [Windows.Data.Xml.Dom.XmlDocument]::new()
$xml.LoadXml($template)
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Jarvis").Show($toast)
"""
        subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True,
            timeout=5,
            check=False,
        )


def _extract_reminder_text(raw_text: str) -> str:
    match = re_sub(
        r"^(me lembre|me notifique|avise|lembrete)\s+(de|que|sobre)?\s*",
        "",
        raw_text,
    )
    return match.strip() or raw_text


def re_sub(pattern: str, repl: str, text: str) -> str:
    import re

    return re.sub(pattern, repl, text, flags=re.IGNORECASE)
