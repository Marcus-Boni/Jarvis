from __future__ import annotations

from core.models import Intent, IntentCategory, RequestContext
from llm.prompt_manager import PromptManager


def test_intent_prompt_contains_expected_categories() -> None:
    prompt_manager = PromptManager(jarvis_name="Jarvis")
    prompt = prompt_manager.build_intent_prompt(user_input="abra o spotify", locale="pt-BR")

    assert "system_control" in prompt
    assert "email" in prompt
    assert "spotify" in prompt
    assert "volume" in prompt
    assert "memory" in prompt


def test_fallback_prompt_contains_recent_context() -> None:
    prompt_manager = PromptManager(jarvis_name="Jarvis")
    prompt = prompt_manager.build_fallback_prompt(
        intent=Intent(raw_text="oi", category=IntentCategory.CONVERSATION),
        context=RequestContext(session_id="session-1"),
    )

    assert "Jarvis" in prompt
    assert "Intent category: conversation" in prompt
    assert "Current local date/time:" in prompt
