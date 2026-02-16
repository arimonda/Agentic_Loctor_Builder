"""Known Locators Database for duplicate prevention using TinyDB."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from tinydb import Query, TinyDB

from core.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class KnownLocatorsDB:
    """Manages a database of known locators to prevent duplicates."""

    def __init__(self, config: ConfigManager) -> None:
        db_path = config.get_setting("known_locators_db", "./data/known_locators.json")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._db = TinyDB(db_path)
        self._table = self._db.table("locators")

    def add_locator(
        self,
        strategy: str,
        value: str,
        object_name: str,
        page_url: str,
        source: str = "original",
    ) -> int:
        """Add a locator to the database. Returns the document ID."""
        existing = self.find_duplicate(strategy, value)
        if existing:
            logger.debug("Locator already in DB: %s=%s", strategy, value)
            return existing.doc_id
        doc_id = self._table.insert(
            {
                "strategy": strategy,
                "value": value,
                "object_name": object_name,
                "page_url": page_url,
                "source": source,
            }
        )
        logger.info("Added locator to DB: %s=%s (id=%d)", strategy, value, doc_id)
        return doc_id

    def find_duplicate(self, strategy: str, value: str) -> Optional[dict]:
        """Check if a locator already exists in the database."""
        q = Query()
        results = self._table.search((q.strategy == strategy) & (q.value == value))
        return results[0] if results else None

    def is_duplicate(self, strategy: str, value: str) -> bool:
        """Check if a locator is a duplicate."""
        return self.find_duplicate(strategy, value) is not None

    def get_locators_for_object(self, object_name: str) -> list[dict]:
        """Get all locators for a named object."""
        q = Query()
        return self._table.search(q.object_name == object_name)

    def get_all(self) -> list[dict]:
        """Get all locators in the database."""
        return self._table.all()

    def remove_locator(self, strategy: str, value: str) -> None:
        """Remove a locator from the database."""
        q = Query()
        self._table.remove((q.strategy == strategy) & (q.value == value))

    def clear(self) -> None:
        """Clear the entire database."""
        self._table.truncate()
