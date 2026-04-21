"""Playwright-based page text extraction."""

from __future__ import annotations

from playwright.async_api import async_playwright


class PlaywrightAgent:
    """Fetch visible text from dynamic pages."""

    async def fetch_page_text(self, url: str) -> str:
        """Return clean text from a remote page."""

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle")
            text = await page.evaluate(
                """
                () => {
                  const body = document.body;
                  return body ? body.innerText.replace(/\\s+/g, " ").trim() : "";
                }
                """
            )
            await browser.close()
        return str(text)

