"""Abstract base class for all AI providers."""

from __future__ import annotations

import base64
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class BaseAIProvider(ABC):
    """Abstract interface that all AI providers must implement."""

    def __init__(self, model: str, api_key: str) -> None:
        self.model = model
        self.api_key = api_key
        self._name = self.__class__.__name__

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    async def generate_locators(
        self,
        broken_locator: str,
        html_snippet: str,
        css_properties: dict,
        intent: str,
        page_url: str,
        screenshot_path: Optional[str] = None,
    ) -> list[dict]:
        """
        Ask the AI to generate replacement locator candidates.

        Returns a list of dicts with keys:
            - strategy: str (xpath, css, id, etc.)
            - value: str (the locator expression)
            - reasoning: str (why this locator was chosen)
            - confidence: float (0.0 to 1.0)
        """
        ...

    @abstractmethod
    async def analyze_element(
        self,
        html_snippet: str,
        css_properties: dict,
        screenshot_path: Optional[str] = None,
    ) -> dict:
        """
        Analyze an element and return structured information about it.

        Returns a dict describing what the element is, its purpose, and
        its visual characteristics.
        """
        ...

    def _build_healing_prompt(
        self,
        broken_locator: str,
        html_snippet: str,
        css_properties: dict,
        intent: str,
        page_url: str,
    ) -> str:
        """Build the standard prompt for locator healing."""
        return f"""You are an expert test automation engineer specializing in web element locators.

A locator has FAILED to find the intended element on a web page. Your task is to analyze the
surrounding HTML and CSS, understand the intent, and generate exactly 3 new robust locator
strategies.

## Failed Locator
{broken_locator}

## Page URL
{page_url}

## Element Intent
{intent}

## Surrounding HTML
```html
{html_snippet}
```

## Computed CSS Properties of Nearby Elements
```json
{css_properties}
```

## Instructions
Generate exactly 3 locator candidates, each using a DIFFERENT strategy:
1. An ID-based or attribute-based locator (most stable)
2. A CSS selector locator
3. A robust relative XPath locator

For each candidate, respond in this exact JSON format:
```json
[
  {{
    "strategy": "id|css|xpath|name|class_name",
    "value": "the_locator_expression",
    "reasoning": "Brief explanation of why this locator is robust",
    "confidence": 0.95
  }},
  ...
]
```

Requirements:
- Each locator must be UNIQUE (no duplicates).
- Prefer stable attributes (data-testid, aria-label, id) over positional XPaths.
- CSS selectors should not rely on dynamic classes.
- XPath must be relative, not absolute.
- Confidence is your estimated probability (0.0 to 1.0) that this locator will correctly find the element.
- Return ONLY the JSON array, no other text.
"""

    def _encode_image(self, image_path: str) -> Optional[str]:
        """Encode an image file to base64 for API consumption."""
        path = Path(image_path)
        if not path.exists():
            return None
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
