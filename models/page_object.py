"""Data models for page objects and automation scripts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from models.locator import Locator


@dataclass
class PageElement:
    """Represents a single element on a page."""

    name: str
    locator: Locator
    intent: str = ""
    page_name: str = ""
    line_number: Optional[int] = None
    file_path: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "locator": self.locator.to_dict(),
            "intent": self.intent,
            "page_name": self.page_name,
            "line_number": self.line_number,
            "file_path": self.file_path,
        }


@dataclass
class PageObject:
    """Represents a Page Object Model page with its elements."""

    name: str
    url: str
    elements: list[PageElement] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "url": self.url,
            "elements": [e.to_dict() for e in self.elements],
            "description": self.description,
        }


@dataclass
class AutomationScript:
    """Represents a full automation script with pages and elements."""

    name: str
    file_path: str
    base_url: str
    pages: list[PageObject] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def total_elements(self) -> int:
        return sum(len(p.elements) for p in self.pages)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "file_path": self.file_path,
            "base_url": self.base_url,
            "pages": [p.to_dict() for p in self.pages],
            "metadata": self.metadata,
        }
