"""Anthropic Claude AI provider implementation."""

from __future__ import annotations

import json
import logging
from typing import Optional

from anthropic import AsyncAnthropic

from ai.base_provider import BaseAIProvider

logger = logging.getLogger(__name__)


class ClaudeProvider(BaseAIProvider):
    """Anthropic Claude provider for locator healing."""

    def __init__(self, model: str, api_key: str) -> None:
        super().__init__(model, api_key)
        self._client = AsyncAnthropic(api_key=self.api_key)
        self._name = "Claude"

    async def generate_locators(
        self,
        broken_locator: str,
        html_snippet: str,
        css_properties: dict,
        intent: str,
        page_url: str,
        screenshot_path: Optional[str] = None,
    ) -> list[dict]:
        prompt = self._build_healing_prompt(
            broken_locator, html_snippet, css_properties, intent, page_url
        )

        content_blocks = []

        if screenshot_path:
            img_b64 = self._encode_image(screenshot_path)
            if img_b64:
                content_blocks.append(
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img_b64,
                        },
                    }
                )

        content_blocks.append({"type": "text", "text": prompt})

        try:
            response = await self._client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.2,
                system=(
                    "You are an expert test automation engineer. "
                    "You respond only with valid JSON arrays."
                ),
                messages=[{"role": "user", "content": content_blocks}],
            )
            response_text = response.content[0].text
            return self._parse_response(response_text)
        except Exception as e:
            logger.error("Claude API error: %s", e)
            raise

    async def analyze_element(
        self,
        html_snippet: str,
        css_properties: dict,
        screenshot_path: Optional[str] = None,
    ) -> dict:
        prompt = f"""Analyze this web element and describe it:

HTML:
```html
{html_snippet}
```

CSS Properties:
```json
{json.dumps(css_properties, indent=2)}
```

Return a JSON object with:
- "element_type": what kind of element it is
- "purpose": what the element's purpose appears to be
- "visual_description": how it likely appears visually
- "unique_attributes": list of attributes that could uniquely identify it
"""
        content_blocks = []
        if screenshot_path:
            img_b64 = self._encode_image(screenshot_path)
            if img_b64:
                content_blocks.append(
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img_b64,
                        },
                    }
                )
        content_blocks.append({"type": "text", "text": prompt})

        try:
            response = await self._client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.2,
                system="You respond only with valid JSON.",
                messages=[{"role": "user", "content": content_blocks}],
            )
            return self._parse_json_response(response.content[0].text)
        except Exception as e:
            logger.error("Claude analysis error: %s", e)
            return {"error": str(e)}

    def _parse_response(self, text: str) -> list[dict]:
        try:
            cleaned = text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                lines = lines[1:] if lines[0].startswith("```") else lines
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned = "\n".join(lines)
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("Failed to parse Claude response, attempting extraction")
            return self._extract_json_from_text(text)

    def _parse_json_response(self, text: str) -> dict:
        try:
            cleaned = text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                lines = lines[1:] if lines[0].startswith("```") else lines
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned = "\n".join(lines)
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {"raw_response": text}

    def _extract_json_from_text(self, text: str) -> list[dict]:
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
        return []
