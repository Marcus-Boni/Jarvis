from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from core.models import Intent, IntentCategory, RequestContext
from skills.system.screenshot_skill import ScreenshotSkill


async def test_screenshot_fullscreen() -> None:
    skill = ScreenshotSkill()
    intent = Intent(raw_text="tire um print da tela", category=IntentCategory.SYSTEM_CONTROL)
    context = RequestContext(session_id="session-1")
    screenshot_path = Path("data/screenshots/jarvis_screen_20260421_120000.png")

    with patch.object(skill, "_capture_fullscreen", return_value=screenshot_path):
        result = await skill.execute(intent=intent, context=context)

    assert result.success
    assert "jarvis_screen_20260421_120000.png" in result.message
