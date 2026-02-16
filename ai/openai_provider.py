"""OpenAI GPT provider implementation."""

from __future__ import annotations

import json
import logging
from typing import Optional

from openai import AsyncOpenAI

from ai.base_provider import BaseAIProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseAIProvider):
    """OpenAI GPT-4o provider for locator healing."""

    def __init__(self, model: str, api_key: str) -> None:
        super().__init__(model, api_key)
        self._client = AsyncOpenAI(api_key=self.api_key)
        self._name = "OpenAI"

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

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert test automation engineer. "
                    "You respond only with valid JSON arrays."
                ),
            },
        ]

        if screenshot_path:
            img_b64 = self._encode_image(screenshot_path)
            if img_b64:
                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_b64}",
                                    "detail": "high",
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                )
            else:
                messages.append({"role": "user", "content": prompt})
        else:
            messages.append({"role": "user", "content": prompt})

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
                max_tokens=2048,
            )
            return self._parse_response(response.choices[0].message.content)
        except Exception as e:
            logger.error("OpenAI API error: %s", e)
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
        messages = [
            {"role": "system", "content": "You respond only with valid JSON."},
            {"role": "user", "content": prompt},
        ]

        if screenshot_path:
            img_b64 = self._encode_image(screenshot_path)
            if img_b64:
                messages[1] = {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_b64}",
                                "detail": "high",
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
                max_tokens=1024,
            )
            return self._parse_json_response(response.choices[0].message.content)
        except Exception as e:
            logger.error("OpenAI analysis error: %s", e)
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
            logger.warning("Failed to parse OpenAI response, attempting extraction")
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
