"""Loads automation scripts from JSON definitions into PageObject models."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from models.locator import Locator, LocatorStrategy
from models.page_object import AutomationScript, PageElement, PageObject

logger = logging.getLogger(__name__)

STRATEGY_MAP = {
    "xpath": LocatorStrategy.XPATH,
    "css": LocatorStrategy.CSS,
    "css_selector": LocatorStrategy.CSS,
    "id": LocatorStrategy.ID,
    "name": LocatorStrategy.NAME,
    "class_name": LocatorStrategy.CLASS_NAME,
    "class": LocatorStrategy.CLASS_NAME,
    "tag_name": LocatorStrategy.TAG_NAME,
    "link_text": LocatorStrategy.LINK_TEXT,
    "partial_link_text": LocatorStrategy.PARTIAL_LINK_TEXT,
}


def load_script(file_path: str) -> AutomationScript:
    """
    Load an automation script definition from a JSON file.

    Expected JSON format:
    {
      "name": "My Test Script",
      "base_url": "https://example.com",
      "pages": [
        {
          "name": "Login Page",
          "url": "/login",
          "elements": [
            {
              "name": "username_input",
              "strategy": "id",
              "value": "username",
              "intent": "Username text input field",
              "line_number": 15,
              "file_path": "tests/pages/login_page.py"
            }
          ]
        }
      ]
    }
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Script file not found: {file_path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    script = AutomationScript(
        name=data.get("name", path.stem),
        file_path=str(path.resolve()),
        base_url=data["base_url"],
        metadata=data.get("metadata", {}),
    )

    for page_data in data.get("pages", []):
        page = PageObject(
            name=page_data["name"],
            url=page_data.get("url", ""),
            description=page_data.get("description", ""),
        )

        for elem_data in page_data.get("elements", []):
            strategy_str = elem_data.get("strategy", "css")
            strategy = STRATEGY_MAP.get(strategy_str.lower(), LocatorStrategy.CSS)

            locator = Locator(
                strategy=strategy,
                value=elem_data["value"],
                object_name=elem_data["name"],
                description=elem_data.get("intent", ""),
            )

            element = PageElement(
                name=elem_data["name"],
                locator=locator,
                intent=elem_data.get("intent", ""),
                page_name=page.name,
                line_number=elem_data.get("line_number"),
                file_path=elem_data.get("file_path"),
            )
            page.elements.append(element)

        script.pages.append(page)

    logger.info(
        "Loaded script '%s': %d pages, %d total elements",
        script.name, len(script.pages), script.total_elements,
    )
    return script
