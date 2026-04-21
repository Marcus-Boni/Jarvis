"""Google Calendar integration skill."""

from __future__ import annotations

import asyncio
import importlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, ClassVar

from core.config import AppSettings
from core.error_telemetry import ErrorTelemetry
from core.models import Intent, IntentCategory, RequestContext, SkillResult
from core.runtime_events import RuntimeEventBroker
from llm.ollama_client import OllamaClient
from skills.base_skill import BaseSkill


class CalendarSkill(BaseSkill):
    """Read and create Google Calendar events."""

    name: ClassVar[str] = "calendar"
    description: ClassVar[str] = "Read and create Google Calendar events."
    triggers: ClassVar[list[str]] = [
        "google calendar",
        "crie um evento",
        "meus eventos",
        "agenda",
    ]

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
        self._service: Any | None = None

    async def can_handle(self, intent: Intent) -> float:
        lowered_text = intent.raw_text.lower()
        if intent.category is IntentCategory.CALENDAR:
            return 0.94
        if "calendar" in lowered_text or "evento" in lowered_text or "agenda" in lowered_text:
            return 0.74
        return 0.0

    async def execute(self, intent: Intent, context: RequestContext) -> SkillResult:
        if not self._settings.env.google_client_secrets_file:
            return SkillResult(
                skill_name=self.name,
                success=False,
                message="GOOGLE_CLIENT_SECRETS_FILE is not configured locally.",
            )

        lowered_text = intent.raw_text.lower()
        try:
            if any(token in lowered_text for token in ["crie", "agende", "marque", "create"]):
                extracted = await self._extract_schedule_payload(intent.raw_text, context.timezone)
                start_dt = _parse_iso_datetime(extracted.get("start_iso"))
                end_dt = _parse_iso_datetime(extracted.get("end_iso")) or (
                    start_dt + timedelta(hours=1) if start_dt else None
                )
                if start_dt is None or end_dt is None:
                    raise ValueError("Could not extract a valid Google Calendar date range.")
                created = await self.create_event(
                    title=str(extracted.get("title", "Jarvis event")),
                    start_dt=start_dt,
                    end_dt=end_dt,
                    description=intent.raw_text,
                    attendees=[str(item) for item in extracted.get("attendees", [])],
                )
                return SkillResult(
                    skill_name=self.name,
                    success=True,
                    message=(
                        "Created the Google Calendar event "
                        f"'{created.get('summary', 'event')}'."
                    ),
                    data={"event": created},
                )

            days = 1 if "amanha" in lowered_text else 7
            events = await self.list_events(days=days)
            return SkillResult(
                skill_name=self.name,
                success=True,
                message=f"Found {len(events)} Google Calendar events.",
                data={"events": events},
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
                message="Google Calendar integration failed safely and was logged.",
            )

    async def list_events(self, days: int = 7) -> list[dict[str, Any]]:
        service = await asyncio.to_thread(self._get_service)
        now = datetime.now(UTC)
        time_max = now + timedelta(days=days)

        def run_list() -> list[dict[str, Any]]:
            response = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=now.isoformat(),
                    timeMax=time_max.isoformat(),
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            return list(response.get("items", []))

        return await asyncio.to_thread(run_list)

    async def create_event(
        self,
        title: str,
        start_dt: datetime,
        end_dt: datetime,
        description: str,
        attendees: list[str],
    ) -> dict[str, Any]:
        service = await asyncio.to_thread(self._get_service)

        def run_insert() -> dict[str, Any]:
            body = {
                "summary": title,
                "description": description,
                "start": {
                    "dateTime": start_dt.isoformat(),
                    "timeZone": self._settings.jarvis.timezone,
                },
                "end": {
                    "dateTime": end_dt.isoformat(),
                    "timeZone": self._settings.jarvis.timezone,
                },
                "attendees": [{"email": attendee} for attendee in attendees],
            }
            response = (
                service.events()
                .insert(calendarId="primary", body=body, sendUpdates="all")
                .execute()
            )
            return dict(response)

        created = await asyncio.to_thread(run_insert)
        await self._event_broker.publish(
            "activity",
            {"component": self.name, "message": f"Created Google event '{title}'."},
        )
        return created

    def _get_service(self) -> Any:
        if self._service is not None:
            return self._service

        requests_module = importlib.import_module("google.auth.transport.requests")
        credentials_module = importlib.import_module("google.oauth2.credentials")
        flow_module = importlib.import_module("google_auth_oauthlib.flow")
        discovery_module = importlib.import_module("googleapiclient.discovery")
        Request = requests_module.Request
        Credentials = credentials_module.Credentials
        InstalledAppFlow = flow_module.InstalledAppFlow
        build = discovery_module.build

        token_path = Path(self._settings.env.google_token_file or self._settings.google.token_path)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        credentials: Any | None = None
        if token_path.exists():
            credentials = Credentials.from_authorized_user_file(
                str(token_path),
                scopes=self._settings.google.scopes,
            )

        if credentials is None or not credentials.valid:
            if credentials is not None and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self._settings.env.google_client_secrets_file,
                    scopes=self._settings.google.scopes,
                )
                credentials = flow.run_local_server(port=0)
            token_path.write_text(credentials.to_json(), encoding="utf-8")

        self._service = build("calendar", "v3", credentials=credentials, cache_discovery=False)
        return self._service

    async def _extract_schedule_payload(self, raw_text: str, timezone: str) -> dict[str, Any]:
        prompt = (
            "Extract scheduling details and return JSON only.\n"
            "Keys: title, start_iso, end_iso, attendees.\n"
            f"Timezone: {timezone}\n"
            f"Request: {raw_text}"
        )
        fallback = {
            "title": "Jarvis event",
            "start_iso": "",
            "end_iso": "",
            "attendees": [],
        }
        return await self._llm_client.complete_json_safe(prompt=prompt, fallback=fallback)


def _parse_iso_datetime(raw_value: Any) -> datetime | None:
    if not raw_value:
        return None
    try:
        return datetime.fromisoformat(str(raw_value).replace("Z", "+00:00"))
    except ValueError:
        return None
