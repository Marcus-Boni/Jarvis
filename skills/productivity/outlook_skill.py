"""Outlook and Microsoft Graph integration."""

from __future__ import annotations

import asyncio
import importlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, ClassVar

import httpx

from core.config import AppSettings
from core.error_telemetry import ErrorTelemetry
from core.models import Intent, IntentCategory, RequestContext, SkillResult
from core.runtime_events import RuntimeEventBroker
from llm.ollama_client import OllamaClient
from skills.base_skill import BaseSkill


class OutlookSkill(BaseSkill):
    """Read emails and manage Outlook calendar via Microsoft Graph."""

    name: ClassVar[str] = "outlook"
    description: ClassVar[str] = "Read mail, send mail, and manage Outlook calendar."
    triggers: ClassVar[list[str]] = [
        "leia meus emails",
        "verifique o email",
        "envie um email",
        "agenda do outlook",
        "reuniao no teams",
        "compromisso",
    ]
    GRAPH_BASE: ClassVar[str] = "https://graph.microsoft.com/v1.0"

    def __init__(
        self,
        settings: AppSettings,
        llm_client: OllamaClient,
        event_broker: RuntimeEventBroker,
        error_telemetry: ErrorTelemetry,
    ) -> None:
        super().__init__()
        self._settings = settings
        self._llm_client = llm_client
        self._event_broker = event_broker
        self._error_telemetry = error_telemetry
        self._http_client = httpx.AsyncClient(timeout=30.0)
        self._token_cache: Any | None = None
        self._msal_app: Any | None = None

    async def can_handle(self, intent: Intent) -> float:
        lowered_text = intent.raw_text.lower()
        if intent.category in {IntentCategory.EMAIL, IntentCategory.OUTLOOK}:
            return 0.95
        if any(token in lowered_text for token in ["email", "outlook", "teams", "compromisso"]):
            return 0.76
        return 0.0

    async def execute(self, intent: Intent, context: RequestContext) -> SkillResult:
        if not self._settings.env.outlook_client_id:
            return SkillResult(
                skill_name=self.name,
                success=False,
                message="OUTLOOK_CLIENT_ID is not configured locally.",
            )

        lowered_text = intent.raw_text.lower()
        try:
            if "email" in lowered_text and any(
                token in lowered_text for token in ["envie", "send"]
            ):
                extracted = await self._extract_schedule_payload(intent.raw_text, context.timezone)
                did_send = await self.send_email(
                    to=str(extracted.get("send_email_to", "")),
                    subject=str(extracted.get("email_subject", "Jarvis email")),
                    body=str(extracted.get("email_body", intent.raw_text)),
                )
                return SkillResult(
                    skill_name=self.name,
                    success=did_send,
                    message="Outlook email sent." if did_send else "Failed to send Outlook email.",
                )

            if any(
                token in lowered_text
                for token in ["reuniao", "meeting", "compromisso", "agenda"]
            ):
                if any(token in lowered_text for token in ["marque", "agende", "create", "crie"]):
                    extracted = await self._extract_schedule_payload(
                        intent.raw_text,
                        context.timezone,
                    )
                    start_dt = _parse_iso_datetime(extracted.get("start_iso"))
                    end_dt = _parse_iso_datetime(extracted.get("end_iso")) or (
                        start_dt + timedelta(hours=1) if start_dt else None
                    )
                    if start_dt is None or end_dt is None:
                        raise ValueError("Could not extract a valid date range for Outlook event.")
                    created = await self.create_calendar_event(
                        title=str(extracted.get("title", "Jarvis meeting")),
                        start=start_dt,
                        end=end_dt,
                        attendees=[str(item) for item in extracted.get("attendees", [])],
                        is_teams_meeting=bool(extracted.get("is_teams_meeting", False)),
                    )
                    return SkillResult(
                        skill_name=self.name,
                        success=True,
                        message=f"Created the Outlook event '{created.get('subject', 'meeting')}'.",
                        data={"event": created},
                    )

                events = await self.list_calendar_events(
                    days_ahead=1 if "amanha" in lowered_text else 7
                )
                return SkillResult(
                    skill_name=self.name,
                    success=True,
                    message=f"Found {len(events)} Outlook calendar events.",
                    data={"events": events},
                )

            emails = await self.list_emails(
                unread_only="nao lidos" in lowered_text or "unread" in lowered_text
            )
            return SkillResult(
                skill_name=self.name,
                success=True,
                message=f"Found {len(emails)} Outlook emails.",
                data={"emails": emails},
            )
        except Exception as exc:  # pragma: no cover
            await self._error_telemetry.record(
                component=self.name,
                error=type(exc).__name__,
                message=str(exc),
            )
            return SkillResult(
                skill_name=self.name,
                success=False,
                message="Outlook integration failed safely and was logged.",
            )

    async def list_emails(self, top: int = 10, unread_only: bool = True) -> list[dict[str, Any]]:
        filter_clause = "&$filter=isRead eq false" if unread_only else ""
        response = await self._graph_request(
            "GET",
            f"/me/messages?$top={top}&$orderby=receivedDateTime desc{filter_clause}",
        )
        return list(response.get("value", []))

    async def send_email(self, to: str, subject: str, body: str) -> bool:
        payload = {
            "message": {
                "subject": subject,
                "body": {"contentType": "Text", "content": body},
                "toRecipients": [{"emailAddress": {"address": to}}],
            },
            "saveToSentItems": True,
        }
        await self._graph_request("POST", "/me/sendMail", json_payload=payload)
        await self._event_broker.publish(
            "activity",
            {"component": self.name, "message": f"Sent Outlook email to {to}."},
        )
        return True

    async def list_calendar_events(self, days_ahead: int = 7) -> list[dict[str, Any]]:
        start_dt = datetime.now(UTC)
        end_dt = start_dt + timedelta(days=days_ahead)
        response = await self._graph_request(
            "GET",
            (
                "/me/calendarview"
                f"?startDateTime={start_dt.isoformat()}"
                f"&endDateTime={end_dt.isoformat()}"
            ),
        )
        return list(response.get("value", []))

    async def create_calendar_event(
        self,
        title: str,
        start: datetime,
        end: datetime,
        attendees: list[str] | None = None,
        is_teams_meeting: bool = False,
    ) -> dict[str, Any]:
        payload = {
            "subject": title,
            "start": {"dateTime": start.isoformat(), "timeZone": self._settings.jarvis.timezone},
            "end": {"dateTime": end.isoformat(), "timeZone": self._settings.jarvis.timezone},
            "attendees": [
                {"emailAddress": {"address": attendee}, "type": "required"}
                for attendee in attendees or []
            ],
            "isOnlineMeeting": is_teams_meeting,
            "onlineMeetingProvider": "teamsForBusiness" if is_teams_meeting else "unknown",
        }
        created = await self._graph_request("POST", "/me/events", json_payload=payload)
        await self._event_broker.publish(
            "activity",
            {"component": self.name, "message": f"Created Outlook event '{title}'."},
        )
        return created

    async def reply_to_email(self, message_id: str, body: str) -> bool:
        await self._graph_request(
            "POST",
            f"/me/messages/{message_id}/reply",
            json_payload={"message": {"body": {"contentType": "Text", "content": body}}},
        )
        return True

    async def _graph_request(
        self,
        method: str,
        path: str,
        json_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        access_token = await self._get_access_token()
        response = await self._http_client.request(
            method,
            f"{self.GRAPH_BASE}{path}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=json_payload,
        )
        response.raise_for_status()
        if response.content:
            payload = response.json()
            return payload if isinstance(payload, dict) else {}
        return {}

    async def _get_access_token(self) -> str:
        msal_app = self._get_msal_app()
        accounts = await asyncio.to_thread(msal_app.get_accounts)
        if accounts:
            silent_result = await asyncio.to_thread(
                msal_app.acquire_token_silent,
                self._settings.outlook.scopes,
                accounts[0],
            )
            if isinstance(silent_result, dict) and "access_token" in silent_result:
                self._save_token_cache()
                return str(silent_result["access_token"])

        flow = await asyncio.to_thread(msal_app.initiate_device_flow, self._settings.outlook.scopes)
        if "user_code" not in flow:
            raise ValueError(f"Failed to create Outlook device flow: {flow}")
        print(flow["message"])
        result = await asyncio.to_thread(msal_app.acquire_token_by_device_flow, flow)
        if "access_token" not in result:
            raise ValueError(str(result.get("error_description") or result))
        self._save_token_cache()
        return str(result["access_token"])

    def _get_msal_app(self) -> Any:
        if self._msal_app is not None:
            return self._msal_app

        msal = importlib.import_module("msal")

        self._token_cache = msal.SerializableTokenCache()
        token_path = Path(
            self._settings.env.outlook_token_file or self._settings.outlook.token_path
        )
        token_path.parent.mkdir(parents=True, exist_ok=True)
        if token_path.exists():
            self._token_cache.deserialize(token_path.read_text(encoding="utf-8"))

        authority = f"https://login.microsoftonline.com/{self._settings.env.outlook_tenant_id}"
        self._msal_app = msal.PublicClientApplication(
            client_id=self._settings.env.outlook_client_id,
            authority=authority,
            token_cache=self._token_cache,
        )
        return self._msal_app

    def _save_token_cache(self) -> None:
        if self._token_cache is None or not self._token_cache.has_state_changed:
            return
        token_path = Path(
            self._settings.env.outlook_token_file or self._settings.outlook.token_path
        )
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(self._token_cache.serialize(), encoding="utf-8")

    async def _extract_schedule_payload(self, raw_text: str, timezone: str) -> dict[str, Any]:
        prompt = (
            "Extract email or meeting data and return JSON only.\n"
            "Keys: title, start_iso, end_iso, attendees, is_teams_meeting, "
            "send_email_to, email_subject, email_body.\n"
            f"Timezone: {timezone}\n"
            f"Request: {raw_text}"
        )
        fallback = {
            "title": "Jarvis event",
            "start_iso": "",
            "end_iso": "",
            "attendees": [],
            "is_teams_meeting": False,
            "send_email_to": "",
            "email_subject": "Jarvis email",
            "email_body": raw_text,
        }
        return await self._llm_client.complete_json_safe(prompt=prompt, fallback=fallback)


def _parse_iso_datetime(raw_value: Any) -> datetime | None:
    if not raw_value:
        return None
    try:
        return datetime.fromisoformat(str(raw_value).replace("Z", "+00:00"))
    except ValueError:
        return None
