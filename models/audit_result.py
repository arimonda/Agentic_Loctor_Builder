"""Data models for audit results and forensic evidence."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from models.locator import Locator, LocatorCandidate


class AuditStatus(enum.Enum):
    PASSED = "passed"
    FAILED = "failed"
    HEALED = "healed"
    SKIPPED = "skipped"


@dataclass
class ForensicEvidence:
    """Forensic data captured when a locator fails."""

    full_page_screenshot: Optional[str] = None
    target_area_screenshot: Optional[str] = None
    dom_snapshot_path: Optional[str] = None
    html_snippet: str = ""
    css_properties: dict = field(default_factory=dict)
    page_url: str = ""
    page_title: str = ""
    viewport_size: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "full_page_screenshot": self.full_page_screenshot,
            "target_area_screenshot": self.target_area_screenshot,
            "dom_snapshot_path": self.dom_snapshot_path,
            "html_snippet": self.html_snippet,
            "css_properties": self.css_properties,
            "page_url": self.page_url,
            "page_title": self.page_title,
            "viewport_size": self.viewport_size,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ElementAuditResult:
    """Result of auditing a single element."""

    element_name: str
    page_name: str
    original_locator: Locator
    status: AuditStatus
    healed_locator: Optional[LocatorCandidate] = None
    forensic_evidence: Optional[ForensicEvidence] = None
    error_message: str = ""
    healing_attempts: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "element_name": self.element_name,
            "page_name": self.page_name,
            "original_locator": self.original_locator.to_dict(),
            "status": self.status.value,
            "healed_locator": self.healed_locator.to_dict() if self.healed_locator else None,
            "forensic_evidence": (
                self.forensic_evidence.to_dict() if self.forensic_evidence else None
            ),
            "error_message": self.error_message,
            "healing_attempts": self.healing_attempts,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class AuditReport:
    """Full audit report for a script run."""

    script_name: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    results: list[ElementAuditResult] = field(default_factory=list)
    ai_provider_used: str = ""

    @property
    def total_elements(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.status == AuditStatus.PASSED)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.status == AuditStatus.FAILED)

    @property
    def healed(self) -> int:
        return sum(1 for r in self.results if r.status == AuditStatus.HEALED)

    @property
    def success_rate(self) -> float:
        if not self.results:
            return 0.0
        return (self.passed + self.healed) / len(self.results) * 100

    def to_dict(self) -> dict:
        return {
            "script_name": self.script_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_elements": self.total_elements,
            "passed": self.passed,
            "failed": self.failed,
            "healed": self.healed,
            "success_rate": round(self.success_rate, 2),
            "ai_provider_used": self.ai_provider_used,
            "results": [r.to_dict() for r in self.results],
        }
