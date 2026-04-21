from __future__ import annotations

from unittest.mock import patch

from core.models import Intent, IntentCategory, RequestContext
from skills.system.clipboard_skill import ClipboardSkill


async def test_clipboard_read() -> None:
    skill = ClipboardSkill()
    intent = Intent(raw_text="leia o clipboard", category=IntentCategory.SYSTEM_CONTROL)
    context = RequestContext(session_id="session-1")

    with patch("pyperclip.paste", return_value="hello world"):
        result = await skill.execute(intent=intent, context=context)

    assert result.success
    assert "hello world" in result.message


async def test_clipboard_write() -> None:
    skill = ClipboardSkill()
    intent = Intent(
        raw_text="copie este texto",
        category=IntentCategory.SYSTEM_CONTROL,
        entities={"content": "texto para copiar"},
    )
    context = RequestContext(session_id="session-1")

    with patch("pyperclip.copy") as mock_copy:
        result = await skill.execute(intent=intent, context=context)

    mock_copy.assert_called_once_with("texto para copiar")
    assert result.success
