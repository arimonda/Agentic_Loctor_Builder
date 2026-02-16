"""Data models for locators and locator candidates."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class LocatorStrategy(enum.Enum):
    XPATH = "xpath"
    CSS = "css"
    ID = "id"
    NAME = "name"
    CLASS_NAME = "class_name"
    TAG_NAME = "tag_name"
    LINK_TEXT = "link_text"
    PARTIAL_LINK_TEXT = "partial_link_text"


class LocatorStatus(enum.Enum):
    VALID = "valid"
    BROKEN = "broken"
    HEALED = "healed"
    UNVERIFIED = "unverified"


@dataclass
class Locator:
    """Represents a single element locator."""

    strategy: LocatorStrategy
    value: str
    object_name: str
    description: str = ""
    status: LocatorStatus = LocatorStatus.UNVERIFIED
    confidence: float = 0.0
    last_verified: Optional[datetime] = None

    @property
    def selector_string(self) -> str:
        return f"{self.strategy.value}={self.value}"

    def to_dict(self) -> dict:
        return {
            "strategy": self.strategy.value,
            "value": self.value,
            "object_name": self.object_name,
            "description": self.description,
            "status": self.status.value,
            "confidence": self.confidence,
            "last_verified": self.last_verified.isoformat() if self.last_verified else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Locator:
        return cls(
            strategy=LocatorStrategy(data["strategy"]),
            value=data["value"],
            object_name=data["object_name"],
            description=data.get("description", ""),
            status=LocatorStatus(data.get("status", "unverified")),
            confidence=data.get("confidence", 0.0),
            last_verified=(
                datetime.fromisoformat(data["last_verified"])
                if data.get("last_verified")
                else None
            ),
        )


@dataclass
class LocatorCandidate:
    """A candidate locator suggested by the AI healing engine."""

    locator: Locator
    rank: int = 0
    ai_provider: str = ""
    reasoning: str = ""
    visibility_score: float = 0.0
    validated: bool = False

    def to_dict(self) -> dict:
        return {
            "locator": self.locator.to_dict(),
            "rank": self.rank,
            "ai_provider": self.ai_provider,
            "reasoning": self.reasoning,
            "visibility_score": self.visibility_score,
            "validated": self.validated,
        }


@dataclass
class LocatorCandidateList:
    """A list of candidate locators for a single broken element."""

    broken_locator: Locator
    candidates: list[LocatorCandidate] = field(default_factory=list)
    selected: Optional[LocatorCandidate] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def add_candidate(self, candidate: LocatorCandidate) -> None:
        candidate.rank = len(self.candidates) + 1
        self.candidates.append(candidate)

    def select_best(self) -> Optional[LocatorCandidate]:
        """Select the first validated candidate with the highest visibility score."""
        validated = [c for c in self.candidates if c.validated]
        if not validated:
            return None
        self.selected = max(validated, key=lambda c: c.visibility_score)
        return self.selected
