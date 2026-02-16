"""FileModifier utility for updating locators in source code files."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from models.locator import LocatorCandidate

logger = logging.getLogger(__name__)


class FileModifier:
    """Finds and replaces locators in source code files."""

    LOCATOR_PATTERNS = {
        "python_selenium": [
            r"""(find_element\s*\(\s*By\.\w+\s*,\s*)(["'])(.+?)\2""",
            r"""(find_element_by_\w+\s*\(\s*)(["'])(.+?)\2""",
        ],
        "java_selenium": [
            r"""(findElement\s*\(\s*By\.\w+\s*\(\s*)(["'])(.+?)\2""",
        ],
        "javascript_selenium": [
            r"""(findElement\s*\(\s*By\.\w+\s*\(\s*)(["'])(.+?)\2""",
            r"""(driver\.findElement\s*\(\s*\{\s*\w+\s*:\s*)(["'])(.+?)\2""",
        ],
        "playwright": [
            r"""(page\.\w+\s*\(\s*)(["'])(.+?)\2""",
            r"""(locator\s*\(\s*)(["'])(.+?)\2""",
        ],
        "generic": [
            r"""(["'])({old_value})\1""",
        ],
    }

    def update_locator_in_file(
        self,
        file_path: str,
        old_value: str,
        new_locator: LocatorCandidate,
        ai_provider: str,
    ) -> bool:
        """
        Update a locator value in a source file.

        Searches for the old locator value and replaces it with the new one.
        Adds a documentation comment above the line.
        """
        path = Path(file_path)
        if not path.exists():
            logger.error("File not found: %s", file_path)
            return False

        try:
            content = path.read_text(encoding="utf-8")
            lines = content.split("\n")
        except Exception as e:
            logger.error("Failed to read file %s: %s", file_path, e)
            return False

        new_value = new_locator.locator.value
        comment = self._build_comment(
            file_path, ai_provider, new_locator.reasoning
        )

        updated = False
        new_lines = []

        for i, line in enumerate(lines):
            if old_value in line:
                new_line = line.replace(old_value, new_value)
                indent = self._get_indent(line)
                comment_line = f"{indent}{comment}"
                new_lines.append(comment_line)
                new_lines.append(new_line)
                updated = True
                logger.info(
                    "Updated locator on line %d in %s: '%s' -> '%s'",
                    i + 1, file_path, old_value, new_value,
                )
            else:
                new_lines.append(line)

        if not updated:
            updated = self._try_regex_replacement(
                lines, old_value, new_value, comment, new_lines
            )

        if updated:
            try:
                new_content = "\n".join(new_lines)
                path.write_text(new_content, encoding="utf-8")
                logger.info("File updated successfully: %s", file_path)
                return True
            except Exception as e:
                logger.error("Failed to write file %s: %s", file_path, e)
                return False

        logger.warning("Locator '%s' not found in %s", old_value, file_path)
        return False

    def find_locator_line(
        self, file_path: str, locator_value: str
    ) -> Optional[int]:
        """Find the line number where a locator value appears."""
        path = Path(file_path)
        if not path.exists():
            return None

        try:
            lines = path.read_text(encoding="utf-8").split("\n")
            for i, line in enumerate(lines):
                if locator_value in line:
                    return i + 1
            return None
        except Exception:
            return None

    def _try_regex_replacement(
        self,
        original_lines: list[str],
        old_value: str,
        new_value: str,
        comment: str,
        new_lines: list[str],
    ) -> bool:
        """Attempt replacement using regex patterns for known frameworks."""
        new_lines.clear()
        escaped = re.escape(old_value)

        for i, line in enumerate(original_lines):
            if re.search(escaped, line):
                new_line = re.sub(escaped, new_value, line)
                indent = self._get_indent(line)
                new_lines.append(f"{indent}{comment}")
                new_lines.append(new_line)
                return True
            else:
                new_lines.append(line)

        return False

    def _build_comment(
        self, file_path: str, ai_provider: str, reasoning: str
    ) -> str:
        """Build the documentation comment for the healed locator."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        ext = Path(file_path).suffix.lower()

        reason_short = reasoning[:80] if reasoning else "auto-healed"

        comment_styles = {
            ".py": f"# AI-Generated on {date_str}: verified via {ai_provider} - {reason_short}",
            ".java": f"// AI-Generated on {date_str}: verified via {ai_provider} - {reason_short}",
            ".js": f"// AI-Generated on {date_str}: verified via {ai_provider} - {reason_short}",
            ".ts": f"// AI-Generated on {date_str}: verified via {ai_provider} - {reason_short}",
            ".rb": f"# AI-Generated on {date_str}: verified via {ai_provider} - {reason_short}",
            ".cs": f"// AI-Generated on {date_str}: verified via {ai_provider} - {reason_short}",
        }

        return comment_styles.get(
            ext,
            f"// AI-Generated on {date_str}: verified via {ai_provider} - {reason_short}",
        )

    @staticmethod
    def _get_indent(line: str) -> str:
        """Extract the leading whitespace from a line."""
        return line[: len(line) - len(line.lstrip())]
