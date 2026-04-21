"""Web search skill with DuckDuckGo summary and user-visible browser handoff."""

from __future__ import annotations

import asyncio
import re
from typing import Any, ClassVar
from urllib.parse import quote_plus

from core.config import AppSettings
from core.error_telemetry import ErrorTelemetry
from core.models import Intent, IntentCategory, RequestContext, SkillResult
from core.runtime_events import RuntimeEventBroker
from llm.ollama_client import OllamaClient
from skills.base_skill import BaseSkill
from skills.browser.playwright_agent import PlaywrightAgent
from skills.browser.windows_browser import get_default_browser_name


class BrowserSearchSkill(BaseSkill):
    """Search the web, summarize results, or hand off to the visible browser."""

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
        del context
        query = _extract_query(intent=intent)
        if not query:
            return SkillResult(
                skill_name=self.name,
                success=False,
                message="Nao consegui determinar o que deve ser pesquisado.",
            )

        try:
            if _looks_like_url(query):
                if await self._should_open_for_user(intent):
                    opened = await self._playwright_agent.open_for_user(query)
                    return _browser_open_result(
                        opened=opened,
                        query=query,
                        skill_name=self.name,
                        source="system_default_browser",
                    )

                page_text = await self._playwright_agent.fetch_page_text(url=query)
                answer = await self._summarize(query=query, snippets=[page_text])
                return SkillResult(
                    skill_name=self.name,
                    success=True,
                    message=answer,
                    data={"query": query, "source": "playwright_headless"},
                )

            if await self._should_open_for_user(intent):
                search_url = _build_search_url(
                    query=query,
                    search_engine=self._settings.browser.search_engine,
                )
                opened = await self._playwright_agent.open_for_user(search_url)
                return _browser_open_result(
                    opened=opened,
                    query=query,
                    skill_name=self.name,
                    source=self._settings.browser.search_engine,
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
                    message=f"Nao encontrei resultados uteis para '{query}'.",
                )

            if (
                self._settings.browser.headless_for_scraping
                and len(" ".join(snippets)) < self._settings.browser.snippet_char_limit
                and results
            ):
                first_url = str(results[0].get("href", "")).strip()
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
                message="A busca web falhou com seguranca e o erro foi registrado.",
            )

    async def _should_open_for_user(self, intent: Intent) -> bool:
        open_keywords = ["abr", "most", "navig", "open", "show", "acessa", "acesse", "vai para"]
        lowered_text = intent.raw_text.lower()
        return (
            any(keyword in lowered_text for keyword in open_keywords)
            and intent.confidence >= self._settings.skills.browser_search.open_for_user_threshold
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
        return query.strip()

    cleaned_text = re.sub(
        (
            r"^(pesquise|procure|busque|search|look up|abra|abre|open|mostre|mostrar|"
            r"navegue|acessa|acesse|go to|vai para)\s+(por|sobre|para)?\s*"
        ),
        "",
        intent.raw_text.strip(),
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


def _build_search_url(query: str, search_engine: str) -> str:
    encoded_query = quote_plus(query)
    if search_engine.lower() == "duckduckgo":
        return f"https://duckduckgo.com/?q={encoded_query}"
    return f"https://www.google.com/search?q={encoded_query}"


def _browser_open_result(
    opened: bool,
    query: str,
    skill_name: str,
    source: str,
) -> SkillResult:
    browser_name = get_default_browser_name()
    if opened:
        return SkillResult(
            skill_name=skill_name,
            success=True,
            message=f"Abrindo '{query}' no {browser_name}.",
            data={"query": query, "source": source, "browser": browser_name},
        )
    return SkillResult(
        skill_name=skill_name,
        success=False,
        message=f"Nao consegui abrir '{query}' no browser padrao.",
        data={"query": query, "source": source, "browser": browser_name},
    )
