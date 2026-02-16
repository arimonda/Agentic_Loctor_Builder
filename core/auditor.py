"""Main Auditor: orchestrates the full audit-and-heal workflow."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from ai.provider_factory import ProviderFactory
from core.browser_engine import BrowserEngine
from core.config_manager import ConfigManager
from core.file_modifier import FileModifier
from core.forensic_agent import ForensicAgent
from core.git_manager import GitManager
from core.healing_engine import HealingEngine
from core.known_locators_db import KnownLocatorsDB
from core.script_loader import load_script
from models.audit_result import AuditReport, AuditStatus, ElementAuditResult
from models.locator import LocatorStatus
from models.page_object import AutomationScript, PageElement

logger = logging.getLogger(__name__)


class Auditor:
    """
    The main orchestrator that:
    1. Loads scripts
    2. Navigates pages
    3. Audits each element
    4. Triggers healing on failure
    5. Updates source files and commits
    """

    def __init__(self, config: ConfigManager) -> None:
        self._config = config
        self._browser = BrowserEngine(config)
        self._provider_factory = ProviderFactory(config)
        self._forensic = ForensicAgent(config, self._browser)
        self._known_db = KnownLocatorsDB(config)
        self._healing_engine = HealingEngine(
            config, self._browser, self._provider_factory,
            self._forensic, self._known_db,
        )
        self._file_modifier = FileModifier()
        self._git_manager = GitManager(config)
        self._report: Optional[AuditReport] = None
        self._on_element_audited: Optional[Callable] = None
        self._on_page_started: Optional[Callable] = None

    def set_callbacks(
        self,
        on_element_audited: Optional[Callable] = None,
        on_page_started: Optional[Callable] = None,
    ) -> None:
        """Set callback functions for real-time progress reporting."""
        self._on_element_audited = on_element_audited
        self._on_page_started = on_page_started

    async def run_audit(
        self,
        script_path: str,
        repo_path: Optional[str] = None,
    ) -> AuditReport:
        """
        Execute the full audit workflow for a script.

        Returns an AuditReport with results for every element.
        """
        script = load_script(script_path)
        self._report = AuditReport(
            script_name=script.name,
            ai_provider_used=self._config.active_provider,
        )

        if repo_path:
            self._git_manager.init_repo(repo_path)

        logger.info("Starting audit of '%s' (%d elements)", script.name, script.total_elements)

        try:
            await self._browser.start()

            for page in script.pages:
                full_url = self._resolve_url(script.base_url, page.url)
                logger.info("Auditing page: %s (%s)", page.name, full_url)

                if self._on_page_started:
                    self._on_page_started(page.name, full_url)

                try:
                    await self._browser.navigate(full_url)
                except Exception as e:
                    logger.error("Failed to navigate to %s: %s", full_url, e)
                    for elem in page.elements:
                        self._report.results.append(
                            ElementAuditResult(
                                element_name=elem.name,
                                page_name=page.name,
                                original_locator=elem.locator,
                                status=AuditStatus.SKIPPED,
                                error_message=f"Navigation failed: {e}",
                            )
                        )
                    continue

                for element in page.elements:
                    result = await self._audit_element(element, full_url)
                    self._report.results.append(result)

                    if self._on_element_audited:
                        self._on_element_audited(result)

        finally:
            await self._browser.stop()

        self._report.end_time = datetime.now()
        self._save_report(script.name)

        logger.info(
            "Audit complete: %d passed, %d healed, %d failed (%.1f%% success rate)",
            self._report.passed,
            self._report.healed,
            self._report.failed,
            self._report.success_rate,
        )

        return self._report

    async def _audit_element(
        self, element: PageElement, page_url: str
    ) -> ElementAuditResult:
        """Audit a single element: verify its locator, heal if broken."""
        logger.info("Auditing element: %s (%s)", element.name, element.locator.selector_string)

        found = await self._browser.find_element(element.locator)

        if found:
            vis_score = await self._browser.get_element_visibility_score(found)
            if vis_score >= 0.3:
                element.locator.status = LocatorStatus.VALID
                element.locator.last_verified = datetime.now()
                logger.info("Element '%s' PASSED (visibility=%.2f)", element.name, vis_score)
                return ElementAuditResult(
                    element_name=element.name,
                    page_name=element.page_name,
                    original_locator=element.locator,
                    status=AuditStatus.PASSED,
                )

        logger.warning("Element '%s' FAILED verification, initiating healing", element.name)

        result = await self._healing_engine.heal_element(element, page_url)

        if result.status == AuditStatus.HEALED and result.healed_locator:
            self._apply_heal(element, result, page_url)

        return result

    def _apply_heal(
        self,
        element: PageElement,
        result: ElementAuditResult,
        page_url: str,
    ) -> None:
        """Apply the healed locator to the source file and commit."""
        healed = result.healed_locator
        if not healed:
            return

        if element.file_path:
            success = self._file_modifier.update_locator_in_file(
                file_path=element.file_path,
                old_value=element.locator.value,
                new_locator=healed,
                ai_provider=self._config.active_provider,
            )

            if success:
                self._git_manager.commit_heal(
                    file_path=element.file_path,
                    object_name=element.name,
                    page_url=page_url,
                    ai_provider=self._config.active_provider,
                )
        else:
            logger.info(
                "No source file specified for '%s', skipping file update",
                element.name,
            )

    def _resolve_url(self, base_url: str, page_url: str) -> str:
        """Resolve a page URL against the base URL."""
        if page_url.startswith(("http://", "https://")):
            return page_url
        base = base_url.rstrip("/")
        path = page_url if page_url.startswith("/") else f"/{page_url}"
        return f"{base}{path}"

    def _save_report(self, script_name: str) -> None:
        """Save the audit report as JSON."""
        if not self._report:
            return
        report_dir = Path("./logs/reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = report_dir / f"audit_{script_name}_{timestamp}.json"
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(self._report.to_dict(), f, indent=2)
            logger.info("Report saved: %s", report_path)
        except Exception as e:
            logger.error("Failed to save report: %s", e)

    @property
    def report(self) -> Optional[AuditReport]:
        return self._report

    @property
    def provider_factory(self) -> ProviderFactory:
        return self._provider_factory
