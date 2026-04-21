"""Notion integration skill."""

from __future__ import annotations

from typing import Any, ClassVar

from core.config import AppSettings
from core.error_telemetry import ErrorTelemetry
from core.models import Intent, IntentCategory, RequestContext, SkillResult
from core.runtime_events import RuntimeEventBroker
from skills.base_skill import BaseSkill


class NotionSkill(BaseSkill):
    """Create pages, append blocks, and search the Notion workspace."""

    name: ClassVar[str] = "notion"
    description: ClassVar[str] = "Create notes, pages, and search the Notion workspace."
    triggers: ClassVar[list[str]] = [
        "anote",
        "crie uma nota",
        "adicione ao notion",
        "pesquise no notion",
    ]

    def __init__(
        self,
        settings: AppSettings,
        event_broker: RuntimeEventBroker,
        error_telemetry: ErrorTelemetry,
    ) -> None:
        super().__init__()
        self._settings = settings
        self._event_broker = event_broker
        self._error_telemetry = error_telemetry
        self._client: Any | None = None

    async def can_handle(self, intent: Intent) -> float:
        lowered_text = intent.raw_text.lower()
        if intent.category is IntentCategory.NOTION:
            return 0.95
        if "notion" in lowered_text or "nota" in lowered_text:
            return 0.72
        return 0.0

    async def execute(self, intent: Intent, context: RequestContext) -> SkillResult:
        if not self._settings.env.notion_token:
            return SkillResult(
                skill_name=self.name,
                success=False,
                message="NOTION_TOKEN is not configured locally.",
            )

        try:
            self._get_client()
            lowered_text = intent.raw_text.lower()
            if "pesquise" in lowered_text or "search" in lowered_text:
                query = intent.entities.get("query", intent.raw_text)
                results = await self.search(query=query)
                return SkillResult(
                    skill_name=self.name,
                    success=True,
                    message=f"Found {len(results)} matching Notion items.",
                    data={"results": results},
                )

            title = intent.entities.get("title") or _build_title_from_text(intent.raw_text)
            content = intent.entities.get("content") or intent.raw_text
            page = await self.create_page(title=title, content=content, parent_id=None)
            await self._event_broker.publish(
                "activity",
                {"component": self.name, "message": f"Created Notion page '{title}'."},
            )
            return SkillResult(
                skill_name=self.name,
                success=True,
                message=f"Created the Notion page '{title}'.",
                data={"page": page},
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
                message="Notion integration failed safely and was logged.",
            )

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client

        from notion_client import AsyncClient

        self._client = AsyncClient(auth=self._settings.env.notion_token)
        return self._client

    async def create_page(
        self,
        title: str,
        content: str,
        parent_id: str | None,
    ) -> dict[str, Any]:
        parent_payload = _build_notion_parent(
            parent_id=parent_id or self._settings.notion.default_parent_id,
            parent_type=self._settings.notion.default_parent_type,
        )
        if parent_payload is None:
            raise ValueError("No default Notion parent is configured.")

        page = await self._get_client().pages.create(
            parent=parent_payload,
            properties={
                "title": {
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": title},
                        }
                    ]
                }
            },
            children=_markdown_to_notion_blocks(content),
        )
        return dict(page)

    async def append_to_page(self, page_id: str, blocks: list[dict[str, Any]]) -> dict[str, Any]:
        response = await self._get_client().blocks.children.append(
            block_id=page_id,
            children=blocks,
        )
        return dict(response)

    async def search(self, query: str) -> list[dict[str, Any]]:
        response = await self._get_client().search(query=query)
        return [dict(item) for item in response.get("results", [])]


def _build_notion_parent(parent_id: str, parent_type: str) -> dict[str, str] | None:
    if not parent_id:
        return None
    if parent_type == "database_id":
        return {"database_id": parent_id}
    return {"page_id": parent_id}


def _build_title_from_text(raw_text: str) -> str:
    cleaned = raw_text.replace("anote", "").replace("notion", "").strip(" :-")
    return (cleaned[:80] or "Jarvis note").strip()


def _markdown_to_notion_blocks(content: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("- "):
            blocks.append(
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                    },
                }
            )
            continue
        blocks.append(
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": line}}],
                },
            }
        )
    return blocks
