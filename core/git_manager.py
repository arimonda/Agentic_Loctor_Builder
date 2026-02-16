"""Git integration for auto-committing healed locators."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from git import InvalidGitRepositoryError, Repo

from core.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class GitManager:
    """Manages Git operations for the target repository."""

    def __init__(self, config: ConfigManager, repo_path: Optional[str] = None) -> None:
        self._config = config
        self._repo: Optional[Repo] = None
        self._repo_path = repo_path

    def init_repo(self, path: Optional[str] = None) -> bool:
        """Initialize or connect to a Git repository."""
        repo_path = path or self._repo_path or "."
        try:
            self._repo = Repo(repo_path)
            logger.info("Connected to Git repo: %s", self._repo.working_dir)
            return True
        except InvalidGitRepositoryError:
            logger.warning("%s is not a Git repository. Initializing...", repo_path)
            try:
                self._repo = Repo.init(repo_path)
                logger.info("Initialized new Git repo: %s", repo_path)
                return True
            except Exception as e:
                logger.error("Failed to initialize Git repo: %s", e)
                return False
        except Exception as e:
            logger.error("Git error: %s", e)
            return False

    def commit_heal(
        self,
        file_path: str,
        object_name: str,
        page_url: str,
        ai_provider: str,
    ) -> Optional[str]:
        """
        Stage and commit a healed locator file.

        Returns the commit SHA on success, or None on failure.
        """
        if not self._config.get_setting("auto_commit", True):
            logger.info("Auto-commit disabled, skipping")
            return None

        if not self._repo:
            logger.warning("No Git repo initialized, skipping commit")
            return None

        try:
            rel_path = self._get_relative_path(file_path)
            self._repo.index.add([rel_path])

            message = (
                f"[AI-HEAL] Updated locator for object: {object_name} "
                f"on page: {page_url}\n\n"
                f"Provider: {ai_provider}\n"
                f"Auto-healed by Loctor Builder"
            )

            commit = self._repo.index.commit(message)
            sha = commit.hexsha[:8]
            logger.info(
                "Committed heal for '%s': %s (sha: %s)",
                object_name, rel_path, sha,
            )
            return commit.hexsha
        except Exception as e:
            logger.error("Git commit failed: %s", e)
            return None

    def get_current_branch(self) -> str:
        """Get the name of the current branch."""
        if not self._repo:
            return "unknown"
        try:
            return str(self._repo.active_branch)
        except Exception:
            return "detached"

    def get_status(self) -> dict:
        """Get the current Git status."""
        if not self._repo:
            return {"error": "No repo initialized"}
        try:
            return {
                "branch": self.get_current_branch(),
                "is_dirty": self._repo.is_dirty(),
                "untracked": self._repo.untracked_files,
                "modified": [item.a_path for item in self._repo.index.diff(None)],
                "staged": [item.a_path for item in self._repo.index.diff("HEAD")],
            }
        except Exception as e:
            return {"error": str(e)}

    def _get_relative_path(self, file_path: str) -> str:
        """Convert an absolute path to a repo-relative path."""
        if not self._repo or not self._repo.working_dir:
            return file_path
        try:
            return str(Path(file_path).relative_to(self._repo.working_dir))
        except ValueError:
            return file_path
