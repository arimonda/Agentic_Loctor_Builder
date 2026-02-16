"""Browser engine using Playwright for page navigation and element interaction."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    ElementHandle,
    Page,
    async_playwright,
)

from core.config_manager import ConfigManager
from models.locator import Locator, LocatorStrategy

logger = logging.getLogger(__name__)

_STRATEGY_MAP = {
    LocatorStrategy.XPATH: "xpath",
    LocatorStrategy.CSS: "css",
    LocatorStrategy.ID: "id",
    LocatorStrategy.NAME: "name",
    LocatorStrategy.CLASS_NAME: "class_name",
}


class BrowserEngine:
    """Manages the browser lifecycle and provides element-finding utilities."""

    def __init__(self, config: ConfigManager) -> None:
        self._config = config
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    async def start(self) -> None:
        """Launch the browser and create a new page."""
        self._playwright = await async_playwright().start()

        browser_type = self._config.get_setting("browser", "chromium")
        headless = self._config.get_setting("headless", True)
        width = self._config.get_setting("viewport_width", 1920)
        height = self._config.get_setting("viewport_height", 1080)

        launcher = getattr(self._playwright, browser_type)
        self._browser = await launcher.launch(headless=headless)
        self._context = await self._browser.new_context(
            viewport={"width": width, "height": height}
        )
        self._page = await self._context.new_page()
        logger.info(
            "Browser started: %s (headless=%s, viewport=%dx%d)",
            browser_type, headless, width, height,
        )

    async def stop(self) -> None:
        """Gracefully close the browser."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Browser stopped")

    async def navigate(self, url: str, wait_until: str = "networkidle") -> None:
        """Navigate to a URL and wait for the page to fully load."""
        timeout = self._config.get_setting("validation_timeout", 5000)
        await self._page.goto(url, wait_until=wait_until, timeout=timeout * 3)
        logger.info("Navigated to: %s", url)

    async def find_element(self, locator: Locator) -> Optional[ElementHandle]:
        """Attempt to find an element using the given locator."""
        timeout = self._config.get_setting("validation_timeout", 5000)
        try:
            selector = self._to_playwright_selector(locator)
            await self._page.wait_for_selector(selector, timeout=timeout, state="attached")
            element = await self._page.query_selector(selector)
            return element
        except Exception as e:
            logger.debug(
                "Element not found with %s=%s: %s", locator.strategy.value, locator.value, e
            )
            return None

    async def find_element_raw(self, strategy: str, value: str) -> Optional[ElementHandle]:
        """Find an element using raw strategy/value strings (for candidate testing)."""
        timeout = self._config.get_setting("validation_timeout", 5000)
        try:
            selector = self._raw_to_playwright_selector(strategy, value)
            await self._page.wait_for_selector(selector, timeout=timeout, state="attached")
            element = await self._page.query_selector(selector)
            return element
        except Exception:
            return None

    async def is_element_visible(self, element: ElementHandle) -> bool:
        """Check if an element is visible in the viewport."""
        try:
            return await element.is_visible()
        except Exception:
            return False

    async def get_element_visibility_score(self, element: ElementHandle) -> float:
        """Calculate a visibility score (0.0 to 1.0) for an element."""
        try:
            is_visible = await element.is_visible()
            if not is_visible:
                return 0.0

            bbox = await element.bounding_box()
            if not bbox:
                return 0.1

            viewport = self._page.viewport_size
            if not viewport:
                return 0.5

            in_viewport = (
                bbox["x"] >= 0
                and bbox["y"] >= 0
                and bbox["x"] + bbox["width"] <= viewport["width"]
                and bbox["y"] + bbox["height"] <= viewport["height"]
            )

            area = bbox["width"] * bbox["height"]
            has_reasonable_size = area > 0

            score = 0.0
            if is_visible:
                score += 0.4
            if in_viewport:
                score += 0.3
            if has_reasonable_size:
                score += 0.2

            is_enabled = await element.is_enabled()
            if is_enabled:
                score += 0.1

            return min(score, 1.0)
        except Exception:
            return 0.0

    async def get_page_source(self) -> str:
        """Get the full page HTML source."""
        return await self._page.content()

    async def get_page_url(self) -> str:
        return self._page.url

    async def get_page_title(self) -> str:
        return await self._page.title()

    async def get_element_html(
        self, locator: Locator, context_range: int = 3
    ) -> str:
        """Get the HTML of the area surrounding where the element should be.

        If the element is not found, returns a larger portion of the page body.
        """
        element = await self.find_element(locator)
        if element:
            outer = await element.evaluate("el => el.outerHTML")
            parent_html = await element.evaluate(
                "el => el.parentElement ? el.parentElement.outerHTML : el.outerHTML"
            )
            return parent_html

        return await self._page.evaluate(
            """() => {
                const body = document.body;
                if (!body) return '<html></html>';
                return body.innerHTML.substring(0, 5000);
            }"""
        )

    async def get_element_css(self, element: ElementHandle) -> dict:
        """Extract computed CSS properties of an element."""
        try:
            return await element.evaluate(
                """el => {
                    const styles = window.getComputedStyle(el);
                    const props = {};
                    const important = [
                        'display', 'visibility', 'opacity', 'position',
                        'width', 'height', 'color', 'background-color',
                        'font-size', 'font-weight', 'border', 'padding',
                        'margin', 'z-index', 'overflow', 'text-align'
                    ];
                    for (const prop of important) {
                        props[prop] = styles.getPropertyValue(prop);
                    }
                    return props;
                }"""
            )
        except Exception:
            return {}

    async def get_surrounding_elements_css(self, locator: Locator) -> dict:
        """Get CSS properties of elements near the target area."""
        try:
            return await self._page.evaluate(
                """(selectorHint) => {
                    const results = {};
                    const candidates = document.querySelectorAll(
                        'button, input, a, select, textarea, [role="button"], [data-testid]'
                    );
                    let count = 0;
                    for (const el of candidates) {
                        if (count >= 10) break;
                        const styles = window.getComputedStyle(el);
                        const tag = el.tagName.toLowerCase();
                        const id = el.id ? '#' + el.id : '';
                        const cls = el.className ? '.' + el.className.split(' ')[0] : '';
                        const key = `${tag}${id}${cls}`;
                        results[key] = {
                            display: styles.display,
                            visibility: styles.visibility,
                            opacity: styles.opacity,
                            text: el.textContent?.trim().substring(0, 50) || '',
                            tag: tag,
                            id: el.id,
                            classes: el.className,
                            type: el.getAttribute('type') || '',
                            role: el.getAttribute('role') || '',
                        };
                        count++;
                    }
                    return results;
                }""",
                locator.value,
            )
        except Exception:
            return {}

    async def take_screenshot(self, path: str, full_page: bool = True) -> str:
        """Take a screenshot and save it to the specified path."""
        await self._page.screenshot(path=path, full_page=full_page)
        logger.info("Screenshot saved: %s", path)
        return path

    async def take_element_screenshot(
        self, element: ElementHandle, path: str
    ) -> str:
        """Take a screenshot of a specific element."""
        await element.screenshot(path=path)
        logger.info("Element screenshot saved: %s", path)
        return path

    @property
    def page(self) -> Page:
        return self._page

    @property
    def viewport_size(self) -> dict:
        size = self._page.viewport_size
        return size if size else {"width": 1920, "height": 1080}

    def _to_playwright_selector(self, locator: Locator) -> str:
        """Convert a Locator to a Playwright selector string."""
        return self._raw_to_playwright_selector(locator.strategy.value, locator.value)

    def _raw_to_playwright_selector(self, strategy: str, value: str) -> str:
        """Convert raw strategy/value to a Playwright selector string."""
        strategy = strategy.lower().strip()
        if strategy == "xpath":
            return f"xpath={value}"
        elif strategy == "css":
            return value
        elif strategy == "id":
            return f"#{value}"
        elif strategy == "name":
            return f"[name='{value}']"
        elif strategy == "class_name":
            return f".{value}"
        elif strategy == "tag_name":
            return value
        elif strategy == "link_text":
            return f"text={value}"
        elif strategy == "partial_link_text":
            return f"text={value}"
        else:
            return value
