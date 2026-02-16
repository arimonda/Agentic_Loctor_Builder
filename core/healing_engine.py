"""Self-Healing Engine: orchestrates AI consultation and locator validation."""

from __future__ import annotations

import logging
from typing import Optional

from ai.base_provider import BaseAIProvider
from ai.provider_factory import ProviderFactory
from core.browser_engine import BrowserEngine
from core.config_manager import ConfigManager
from core.forensic_agent import ForensicAgent
from core.known_locators_db import KnownLocatorsDB
from core.locator_validator import LocatorValidator
from models.audit_result import AuditStatus, ElementAuditResult, ForensicEvidence
from models.locator import Locator, LocatorCandidate
from models.page_object import PageElement

logger = logging.getLogger(__name__)


class HealingEngine:
    """Coordinates the self-healing workflow: forensic capture -> AI consultation -> validation."""

    def __init__(
        self,
        config: ConfigManager,
        browser: BrowserEngine,
        provider_factory: ProviderFactory,
        forensic_agent: ForensicAgent,
        known_db: KnownLocatorsDB,
    ) -> None:
        self._config = config
        self._browser = browser
        self._provider_factory = provider_factory
        self._forensic = forensic_agent
        self._validator = LocatorValidator(browser, known_db)
        self._retry_limit = config.get_setting("retry_limit", 3)

    async def heal_element(
        self, element: PageElement, page_url: str
    ) -> ElementAuditResult:
        """
        Attempt to heal a broken element locator.

        Steps:
        1. Collect forensic evidence.
        2. Consult the AI provider.
        3. Build and validate candidate locators.
        4. Return the result (healed or failed).
        """
        locator = element.locator
        provider = self._provider_factory.get_provider()
        result = ElementAuditResult(
            element_name=element.name,
            page_name=element.page_name,
            original_locator=locator,
            status=AuditStatus.FAILED,
        )

        logger.info(
            "Healing element '%s' on page '%s' (provider: %s)",
            element.name, element.page_name, provider.name,
        )

        evidence = await self._forensic.collect_evidence(locator, element.page_name)
        result.forensic_evidence = evidence

        for attempt in range(1, self._retry_limit + 1):
            result.healing_attempts = attempt
            logger.info("Healing attempt %d/%d", attempt, self._retry_limit)

            try:
                ai_suggestions = await provider.generate_locators(
                    broken_locator=locator.selector_string,
                    html_snippet=evidence.html_snippet,
                    css_properties=evidence.css_properties,
                    intent=element.intent or f"Find the '{element.name}' element",
                    page_url=page_url,
                    screenshot_path=evidence.full_page_screenshot,
                )
            except Exception as e:
                logger.error("AI provider error on attempt %d: %s", attempt, e)
                result.error_message = f"AI error: {e}"
                continue

            if not ai_suggestions:
                logger.warning("AI returned no suggestions on attempt %d", attempt)
                continue

            candidate_list = self._validator.build_candidate_list(
                broken_locator=locator,
                ai_suggestions=ai_suggestions,
                ai_provider=provider.name,
            )

            selected = await self._validator.validate_candidates(
                candidate_list, page_url
            )

            if selected:
                result.status = AuditStatus.HEALED
                result.healed_locator = selected
                logger.info(
                    "Element '%s' healed: %s=%s (attempt %d, provider: %s)",
                    element.name,
                    selected.locator.strategy.value,
                    selected.locator.value,
                    attempt,
                    provider.name,
                )
                return result

            logger.warning(
                "No valid candidate found on attempt %d", attempt
            )

        logger.error(
            "Failed to heal element '%s' after %d attempts",
            element.name, self._retry_limit,
        )
        result.error_message = (
            f"Could not find a valid locator after {self._retry_limit} attempts"
        )
        return result
