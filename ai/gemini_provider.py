"""Google Gemini AI provider implementation."""

from __future__ import annotations

import json
import logging
from typing import Optional

import google.generativeai as genai

from ai.base_provider import BaseAIProvider

logger = logging.getLogger(__name__)


class GeminiProvider(BaseAIProvider):
    """Google Gemini provider for locator healing."""

    def __init__(self, model: str, api_key: str) -> None:
        super().__init__(model, api_key)
        genai.configure(api_key=self.api_key)
        self._model = genai.GenerativeModel(self.model)
        self._name = "Gemini"

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

        parts = [prompt]

        if screenshot_path:
            img_data = self._encode_image(screenshot_path)
            if img_data:
                import base64

                raw_bytes = base64.b64decode(img_data)
                parts.insert(
                    0,
                    {
                        "mime_type": "image/png",
                        "data": raw_bytes,
                    },
                )

        try:
            response = await self._model.generate_content_async(
                parts,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=2048,
                ),
            )
            return self._parse_response(response.text)
        except Exception as e:
            logger.error("Gemini API error: %s", e)
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
- "element_type": what kind of element it is (button, input, link, etc.)
- "purpose": what the element's purpose appears to be
- "visual_description": how it likely appears visually
- "unique_attributes": list of attributes that could uniquely identify it
"""
        parts = [prompt]
        if screenshot_path:
            img_data = self._encode_image(screenshot_path)
            if img_data:
                import base64

                raw_bytes = base64.b64decode(img_data)
                parts.insert(0, {"mime_type": "image/png", "data": raw_bytes})

        try:
            response = await self._model.generate_content_async(parts)
            return self._parse_json_response(response.text)
        except Exception as e:
            logger.error("Gemini analysis error: %s", e)
            return {"error": str(e)}

    def _parse_response(self, text: str) -> list[dict]:
        """Parse the AI response into a list of locator candidates."""
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
            logger.warning("Failed to parse Gemini response as JSON, attempting extraction")
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
        """Attempt to extract JSON array from mixed text."""
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
        return []
