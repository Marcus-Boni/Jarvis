"""Clipboard read/write skill using pyperclip."""

from __future__ import annotations

import asyncio
import importlib
import re
from typing import ClassVar

from core.models import Intent, RequestContext, SkillResult
from skills.base_skill import BaseSkill


class ClipboardSkill(BaseSkill):
    """Read from or write to the clipboard."""

    name: ClassVar[str] = "clipboard"
    description: ClassVar[str] = "Le e escreve na area de transferencia do Windows."
    triggers: ClassVar[list[str]] = [
        "clipboard",
        "area de transferencia",
        "copie",
        "cole",
        "o que esta na area de transferencia",
    ]

    async def can_handle(self, intent: Intent) -> float:
        lowered_text = intent.raw_text.lower()
        if any(
            token in lowered_text
            for token in ["clipboard", "area de transfer", "copie", "copiar", "colar"]
        ):
            return 0.88
        return 0.0

    async def execute(self, intent: Intent, context: RequestContext) -> SkillResult:
        del context
        pyperclip = importlib.import_module("pyperclip")

        lowered_text = intent.raw_text.lower()
        try:
            if any(token in lowered_text for token in ["leia", "ler", "o que esta", "what is"]):
                content = await asyncio.to_thread(pyperclip.paste)
                return SkillResult(
                    skill_name=self.name,
                    success=True,
                    message=f"Clipboard: {content[:500]}" if content else "Clipboard vazio.",
                    data={"content": content},
                )

            content_to_write = intent.entities.get("content") or ""
            if not content_to_write:
                match = re.search(r"copie\s+(.+)", intent.raw_text, re.IGNORECASE)
                content_to_write = match.group(1).strip() if match else ""

            if content_to_write:
                await asyncio.to_thread(pyperclip.copy, content_to_write)
                return SkillResult(
                    skill_name=self.name,
                    success=True,
                    message=f"Copiado para o clipboard: {content_to_write[:80]}",
                    data={"written": content_to_write},
                )

            return SkillResult(
                skill_name=self.name,
                success=False,
                message="Nao entendi o que fazer com o clipboard.",
            )
        except Exception as exc:  # pragma: no cover
            return SkillResult(
                skill_name=self.name,
                success=False,
                message=f"Erro no clipboard: {exc}",
            )
