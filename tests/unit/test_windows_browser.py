"""Tests for Windows browser detection helpers."""

from unittest.mock import patch

from skills.browser.windows_browser import get_default_browser_name


def test_get_default_browser_name_chrome() -> None:
    with patch("skills.browser.windows_browser.get_default_browser_path") as mock_path:
        mock_path.return_value = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

        assert get_default_browser_name() == "Google Chrome"


def test_get_default_browser_name_edge() -> None:
    with patch("skills.browser.windows_browser.get_default_browser_path") as mock_path:
        mock_path.return_value = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

        assert get_default_browser_name() == "Microsoft Edge"


def test_get_default_browser_name_unknown() -> None:
    with patch("skills.browser.windows_browser.get_default_browser_path") as mock_path:
        mock_path.return_value = r"C:\SomeBrowser\browser.exe"

        assert get_default_browser_name() == "browser"
