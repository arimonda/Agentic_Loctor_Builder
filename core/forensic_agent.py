"""Forensic Agent for collecting evidence when a locator fails."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

from core.browser_engine import BrowserEngine
from core.config_manager import ConfigManager
from models.audit_result import ForensicEvidence
from models.locator import Locator

logger = logging.getLogger(__name__)


class ForensicAgent:
    """Collects forensic evidence (screenshots, DOM, CSS) on locator failure."""

    def __init__(self, config: ConfigManager, browser: BrowserEngine) -> None:
        self._config = config
        self._browser = browser
        self._screenshot_dir = Path(config.get_setting("screenshot_path", "./logs/screenshots"))
        self._dom_dir = Path(config.get_setting("dom_capture_path", "./logs/dom"))
        self._screenshot_dir.mkdir(parents=True, exist_ok=True)
        self._dom_dir.mkdir(parents=True, exist_ok=True)

    async def collect_evidence(
        self, locator: Locator, page_name: str
    ) -> ForensicEvidence:
        """Collect all forensic evidence for a failed locator."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = self._safe_filename(f"{page_name}_{locator.object_name}")

        evidence = ForensicEvidence(
            page_url=await self._browser.get_page_url(),
            page_title=await self._browser.get_page_title(),
            viewport_size=self._browser.viewport_size,
            timestamp=datetime.now(),
        )

        evidence.full_page_screenshot = await self._capture_full_page_screenshot(
            safe_name, timestamp
        )

        evidence.target_area_screenshot = await self._capture_target_area_screenshot(
            locator, safe_name, timestamp
        )

        evidence.dom_snapshot_path = await self._capture_dom(safe_name, timestamp)

        evidence.html_snippet = await self._browser.get_element_html(locator)

        evidence.css_properties = await self._browser.get_surrounding_elements_css(locator)

        logger.info(
            "Forensic evidence collected for %s on %s",
            locator.object_name, page_name,
        )
        return evidence

    async def _capture_full_page_screenshot(
        self, safe_name: str, timestamp: str
    ) -> str:
        """Save a full-page screenshot."""
        path = str(self._screenshot_dir / f"{safe_name}_{timestamp}_full_page.png")
        try:
            await self._browser.take_screenshot(path, full_page=True)
            return path
        except Exception as e:
            logger.error("Failed to capture full-page screenshot: %s", e)
            return ""

    async def _capture_target_area_screenshot(
        self, locator: Locator, safe_name: str, timestamp: str
    ) -> str:
        """Attempt to capture a cropped screenshot of the target area."""
        path = str(self._screenshot_dir / f"{safe_name}_{timestamp}_target_area.png")
        try:
            element = await self._browser.find_element(locator)
            if element:
                await self._browser.take_element_screenshot(element, path)
                return path

            viewport_path = str(
                self._screenshot_dir / f"{safe_name}_{timestamp}_viewport.png"
            )
            await self._browser.take_screenshot(viewport_path, full_page=False)
            return viewport_path
        except Exception as e:
            logger.warning("Failed to capture target area screenshot: %s", e)
            return ""

    async def _capture_dom(self, safe_name: str, timestamp: str) -> str:
        """Save the full DOM structure."""
        path = str(self._dom_dir / f"{safe_name}_{timestamp}_DOM_structure.html")
        try:
            source = await self._browser.get_page_source()
            with open(path, "w", encoding="utf-8") as f:
                f.write(source)
            logger.info("DOM captured: %s", path)
            return path
        except Exception as e:
            logger.error("Failed to capture DOM: %s", e)
            return ""

    @staticmethod
    def _safe_filename(name: str) -> str:
        """Sanitize a string for use in filenames."""
        return "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in name)
