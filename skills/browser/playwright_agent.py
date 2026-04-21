"""Playwright browser agent with headless and visible user-facing modes."""

from __future__ import annotations

import asyncio
from enum import Enum
from urllib.parse import quote_plus

from loguru import logger
from playwright.async_api import Browser, Page, async_playwright

from skills.browser.windows_browser import open_url_in_default_browser


class BrowserMode(str, Enum):
    """Supported browser execution modes."""

    HEADLESS = "headless"
    VISIBLE = "visible"


class PlaywrightAgent:
    """Browser automation agent for scraping and user-visible navigation."""

    def __init__(self) -> None:
        self._logger = logger.bind(component="playwright_agent")

    async def fetch_page_text(self, url: str) -> str:
        """Fetch and extract visible page text using headless Chromium."""

        async with async_playwright() as playwright:
            browser: Browser = await playwright.chromium.launch(headless=True)
            try:
                page: Page = await browser.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=15_000)
                text = await page.evaluate(
                    """() => {
                        const clone = document.cloneNode(true);
                        const removable = clone.querySelectorAll("script, style, nav, footer, header");
                        removable.forEach((element) => element.remove());
                        return clone.body?.innerText || "";
                    }"""
                )
                return str(text).strip()[:8000]
            finally:
                await browser.close()

    async def open_for_user(self, url: str) -> bool:
        """Open a URL in the user's default Windows browser."""

        self._logger.info("opening_url_for_user url={}", url)
        return await asyncio.to_thread(open_url_in_default_browser, url)

    async def search_and_open(
        self,
        query: str,
        search_engine: str = "google",
    ) -> bool:
        """Open search results for a query in the user's default browser."""

        search_url = _build_search_url(query=query, search_engine=search_engine)
        return await self.open_for_user(search_url)

    async def fill_form_headless(
        self,
        url: str,
        fields: dict[str, str],
        submit_selector: str | None = None,
    ) -> str:
        """Fill a form using headless Chromium and return the resulting HTML."""

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=15_000)
                for selector, value in fields.items():
                    await page.fill(selector, value)
                if submit_selector:
                    await page.click(submit_selector)
                    await page.wait_for_load_state("networkidle", timeout=10_000)
                return await page.content()
            finally:
                await browser.close()


def _build_search_url(query: str, search_engine: str) -> str:
    encoded_query = quote_plus(query)
    if search_engine.lower() == "duckduckgo":
        return f"https://duckduckgo.com/?q={encoded_query}"
    return f"https://www.google.com/search?q={encoded_query}"
