"""Prompt builders for classification, fallback chat, and extraction tasks."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from core.models import Intent, RequestContext


class PromptManager:
    """Own structured prompt templates used across the system."""

    def __init__(self, jarvis_name: str) -> None:
        self._jarvis_name = jarvis_name

    def build_intent_prompt(self, user_input: str, locale: str) -> str:
        """Return a prompt that instructs the LLM to classify intent as JSON."""

        return (
            "You are an intent classifier for a local AI assistant.\n"
            "Return JSON only with keys: category, confidence, language, reasoning, "
            "actions, skill_hints, entities.\n"
            "Allowed categories: system_control, browser, notion, calendar, email, spotify, "
            "volume, conversation, code_help, memory, unknown.\n"
            f"Locale: {locale}\n"
            f"User input: {user_input}\n"
            "Examples:\n"
            '- "abra o spotify e toque lofi" -> {"category":"spotify","confidence":0.93,'
            '"language":"pt-BR","reasoning":"music request","actions":["abrir spotify",'
            '"tocar lofi"],"skill_hints":["spotify"],"entities":{"query":"lofi"}}\n'
            '- "aumente o volume em 15" -> {"category":"volume","confidence":0.9,'
            '"language":"pt-BR","reasoning":"system audio request",'
            '"actions":["aumentar volume"],"skill_hints":["volume"],'
            '"entities":{"amount":"15"}}\n'
            '- "o que eu disse ontem sobre embedding?" -> {"category":"memory",'
            '"confidence":0.89,"language":"pt-BR","reasoning":"memory recall request",'
            '"actions":["consultar memoria"],"skill_hints":["memory"],'
            '"entities":{"topic":"embedding"}}\n'
            '- "me ajuda com um componente react" -> {"category":"code_help",'
            '"confidence":0.91,"language":"pt-BR","reasoning":"coding help",'
            '"actions":["responder pergunta tecnica"],"skill_hints":[],' 
            '"entities":{"stack":"react"}}\n'
            '- "quais sao meus emails nao lidos?" -> {"category":"email",'
            '"confidence":0.88,"language":"pt-BR","reasoning":"mail request",'
            '"actions":["listar emails"],"skill_hints":["outlook"],'
            '"entities":{"unread_only":"true"}}\n'
        )

    def build_fallback_prompt(self, intent: Intent, context: RequestContext) -> str:
        """Return a context-aware fallback prompt for direct LLM responses."""

        transcript = "\n".join(
            f"{message.role}: {message.content}" for message in context.messages[-6:]
        ) or "no previous conversation"
        memory = "\n".join(document.content for document in context.memory_documents) or "no memory"
        now = _current_local_datetime(context.timezone)
        return (
            f"You are {self._jarvis_name}, a local-first personal AI assistant.\n"
            f"Respond in {context.locale} unless the user clearly asks otherwise.\n"
            "Be concise, safe, and practical.\n"
            f"Intent category: {intent.category.value}\n"
            f"Current local date/time: {now}\n"
            f"Recent transcript:\n{transcript}\n"
            f"Relevant memory:\n{memory}\n"
            f"User preferences: {context.preferences}\n"
            f"Latest user request: {intent.raw_text}\n"
        )

    def build_schedule_extraction_prompt(self, user_input: str, timezone: str) -> str:
        """Return a JSON prompt for extracting scheduling details."""

        return (
            "Extract schedule details and return JSON only.\n"
            "Keys: title, start_iso, end_iso, attendees, is_teams_meeting, "
            "send_email_to, email_subject, email_body.\n"
            f"Timezone: {timezone}\n"
            f"Request: {user_input}\n"
        )


def _current_local_datetime(timezone_name: str) -> str:
    try:
        now = datetime.now(ZoneInfo(timezone_name))
    except ZoneInfoNotFoundError:
        now = datetime.now()
    return now.isoformat()
