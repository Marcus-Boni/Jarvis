"""Web search skill with DuckDuckGo and Playwright fallback."""

from __future__ import annotations

import asyncio
import re
from typing import Any, ClassVar

from core.config import AppSettings
from core.error_telemetry import ErrorTelemetry
from core.models import Intent, IntentCategory, RequestContext, SkillResult
from core.runtime_events import RuntimeEventBroker
from llm.ollama_client import OllamaClient
from skills.base_skill import BaseSkill
from skills.browser.playwright_agent import PlaywrightAgent


class BrowserSearchSkill(BaseSkill):
    """Search the web and summarize results with the local LLM."""

    name: ClassVar[str] = "browser_search"
    description: ClassVar[str] = "Search the web, summarize results, and inspect dynamic pages."
    triggers: ClassVar[list[str]] = ["pesquise", "procure", "busque na web", "search the web"]

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
        self._playwright_agent = PlaywrightAgent()
        self._event_broker = event_broker
        self._error_telemetry = error_telemetry

    async def can_handle(self, intent: Intent) -> float:
        lowered_text = intent.raw_text.lower()
        if intent.category is IntentCategory.BROWSER:
            return 0.9
        if any(token in lowered_text for token in ["pesquise", "procure", "search", "busque"]):
            return 0.7
        return 0.0

    async def execute(self, intent: Intent, context: RequestContext) -> SkillResult:
        query = _extract_query(intent=intent)
        if not query:
            return SkillResult(
                skill_name=self.name,
                success=False,
                message="I could not determine the web query to search for.",
            )

        try:
            if _looks_like_url(query):
                page_text = await self._playwright_agent.fetch_page_text(url=query)
                answer = await self._summarize(query=query, snippets=[page_text])
                return SkillResult(
                    skill_name=self.name,
                    success=True,
                    message=answer,
                    data={"query": query, "source": "playwright"},
                )

            results = await search_web(
                query=query,
                max_results=self._settings.browser.max_results,
            )
            snippets = [
                _format_result(result=result)
                for result in results
                if result.get("body") or result.get("title")
            ]
            if not snippets:
                return SkillResult(
                    skill_name=self.name,
                    success=False,
                    message=f"No useful web results were found for '{query}'.",
                )

            if len(" ".join(snippets)) < self._settings.browser.snippet_char_limit and results:
                first_url = str(results[0].get("href", ""))
                if first_url:
                    try:
                        page_text = await self._playwright_agent.fetch_page_text(url=first_url)
                        snippets.append(page_text[: self._settings.browser.snippet_char_limit])
                    except Exception:
                        pass

            summary = await self._summarize(query=query, snippets=snippets)
            await self._event_broker.publish(
                "activity",
                {"component": self.name, "message": f"Searched the web for '{query}'."},
            )
            return SkillResult(
                skill_name=self.name,
                success=True,
                message=summary,
                data={"query": query, "results": results},
            )
        except Exception as exc:  # pragma: no cover
            await self._error_telemetry.record(
                component=self.name,
                error=type(exc).__name__,
                message=str(exc),
                metadata={"query": query},
            )
            return SkillResult(
                skill_name=self.name,
                success=False,
                message="Web search failed safely and the error was logged.",
            )

    async def _summarize(self, query: str, snippets: list[str]) -> str:
        prompt = (
            "Dado os resultados abaixo, responda em pt-BR de forma concisa e pratica.\n"
            f"Pergunta: {query}\n\n"
            "Resultados:\n"
            f"{chr(10).join(snippets[:6])}"
        )
        return await self._llm_client.complete_text(prompt=prompt)


async def search_web(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Run a DuckDuckGo search without blocking the event loop."""

    from duckduckgo_search import DDGS

    def run_search() -> list[dict[str, Any]]:
        with DDGS() as search_client:
            return list(search_client.text(query, max_results=max_results))

    return await asyncio.to_thread(run_search)


def _extract_query(intent: Intent) -> str:
    query = intent.entities.get("query")
    if query:
        return query

    lowered_text = intent.raw_text.strip()
    cleaned_text = re.sub(
        r"^(pesquise|procure|busque|search|look up)\s+(por|sobre)?\s*",
        "",
        lowered_text,
        flags=re.IGNORECASE,
    )
    return cleaned_text.strip()


def _format_result(result: dict[str, Any]) -> str:
    title = str(result.get("title", "")).strip()
    body = str(result.get("body", "")).strip()
    href = str(result.get("href", "")).strip()
    return f"Title: {title}\nSnippet: {body}\nURL: {href}"


def _looks_like_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")

