"""Locator validation engine for testing candidate locators."""

from __future__ import annotations

import logging
from typing import Optional

from core.browser_engine import BrowserEngine
from core.known_locators_db import KnownLocatorsDB
from models.locator import (
    Locator,
    LocatorCandidate,
    LocatorCandidateList,
    LocatorStatus,
    LocatorStrategy,
)

logger = logging.getLogger(__name__)


class LocatorValidator:
    """Validates candidate locators by performing dry-run tests against the live page."""

    def __init__(
        self, browser: BrowserEngine, known_db: KnownLocatorsDB
    ) -> None:
        self._browser = browser
        self._known_db = known_db

    async def validate_candidates(
        self,
        candidate_list: LocatorCandidateList,
        page_url: str,
    ) -> Optional[LocatorCandidate]:
        """
        Test each candidate locator against the live page.

        Returns the first candidate that passes validation with the
        highest visibility score, or None if all fail.
        """
        logger.info(
            "Validating %d candidates for %s",
            len(candidate_list.candidates),
            candidate_list.broken_locator.object_name,
        )

        for candidate in candidate_list.candidates:
            loc = candidate.locator
            strategy = loc.strategy.value
            value = loc.value

            if self._known_db.is_duplicate(strategy, value):
                existing = self._known_db.find_duplicate(strategy, value)
                if existing and existing.get("object_name") != loc.object_name:
                    logger.warning(
                        "Skipping duplicate locator %s=%s (belongs to %s)",
                        strategy, value, existing.get("object_name"),
                    )
                    continue

            element = await self._browser.find_element_raw(strategy, value)

            if element is None:
                logger.debug("Candidate FAILED: %s=%s", strategy, value)
                candidate.validated = False
                continue

            vis_score = await self._browser.get_element_visibility_score(element)
            candidate.visibility_score = vis_score

            if vis_score >= 0.3:
                candidate.validated = True
                candidate.locator.status = LocatorStatus.HEALED
                logger.info(
                    "Candidate PASSED: %s=%s (visibility=%.2f)",
                    strategy, value, vis_score,
                )
            else:
                logger.debug(
                    "Candidate has low visibility: %s=%s (score=%.2f)",
                    strategy, value, vis_score,
                )
                candidate.validated = False

        selected = candidate_list.select_best()

        if selected:
            self._known_db.add_locator(
                strategy=selected.locator.strategy.value,
                value=selected.locator.value,
                object_name=selected.locator.object_name,
                page_url=page_url,
                source=f"ai-healed-{selected.ai_provider}",
            )
            logger.info(
                "Selected best candidate: %s=%s (visibility=%.2f)",
                selected.locator.strategy.value,
                selected.locator.value,
                selected.visibility_score,
            )

        return selected

    def build_candidate_list(
        self,
        broken_locator: Locator,
        ai_suggestions: list[dict],
        ai_provider: str,
    ) -> LocatorCandidateList:
        """Convert AI suggestions into a LocatorCandidateList."""
        candidate_list = LocatorCandidateList(broken_locator=broken_locator)

        for i, suggestion in enumerate(ai_suggestions):
            try:
                strategy = self._parse_strategy(suggestion.get("strategy", "css"))
                locator = Locator(
                    strategy=strategy,
                    value=suggestion["value"],
                    object_name=broken_locator.object_name,
                    description=suggestion.get("reasoning", ""),
                    confidence=suggestion.get("confidence", 0.0),
                )
                candidate = LocatorCandidate(
                    locator=locator,
                    rank=i + 1,
                    ai_provider=ai_provider,
                    reasoning=suggestion.get("reasoning", ""),
                )
                candidate_list.add_candidate(candidate)
            except (KeyError, ValueError) as e:
                logger.warning("Skipping invalid AI suggestion: %s (%s)", suggestion, e)

        return candidate_list

    @staticmethod
    def _parse_strategy(strategy_str: str) -> LocatorStrategy:
        """Parse a strategy string into a LocatorStrategy enum."""
        mapping = {
            "xpath": LocatorStrategy.XPATH,
            "css": LocatorStrategy.CSS,
            "css_selector": LocatorStrategy.CSS,
            "css-selector": LocatorStrategy.CSS,
            "id": LocatorStrategy.ID,
            "name": LocatorStrategy.NAME,
            "class_name": LocatorStrategy.CLASS_NAME,
            "class": LocatorStrategy.CLASS_NAME,
            "tag_name": LocatorStrategy.TAG_NAME,
            "tag": LocatorStrategy.TAG_NAME,
            "link_text": LocatorStrategy.LINK_TEXT,
            "partial_link_text": LocatorStrategy.PARTIAL_LINK_TEXT,
        }
        return mapping.get(strategy_str.lower().strip(), LocatorStrategy.CSS)
