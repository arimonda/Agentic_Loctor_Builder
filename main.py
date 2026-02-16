"""
Loctor Builder - AI-Powered Autonomous Locator Validator
=========================================================

Entry point for the application. Supports both CLI and programmatic usage.

Usage:
    # CLI
    python main.py audit scripts/my_script.json
    python main.py audit scripts/my_script.json --provider openai --no-headless
    python main.py switch claude
    python main.py status
    python main.py providers
    python main.py dashboard

    # Programmatic
    from main import run_audit
    import asyncio
    report = asyncio.run(run_audit("scripts/my_script.json"))
"""

from __future__ import annotations

import asyncio
import logging
import sys
from typing import Optional

from core.auditor import Auditor
from core.config_manager import ConfigManager
from models.audit_result import AuditReport


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/loctor_builder.log", encoding="utf-8"),
        ],
    )


async def run_audit(
    script_path: str,
    config_path: str = "config.json",
    repo_path: Optional[str] = None,
    provider: Optional[str] = None,
) -> AuditReport:
    """
    Programmatic entry point for running an audit.

    Args:
        script_path: Path to the automation script JSON file.
        config_path: Path to the config.json file.
        repo_path: Path to the Git repository (optional).
        provider: Override the AI provider (optional).

    Returns:
        AuditReport with full results.
    """
    config = ConfigManager(config_path)
    setup_logging(config.get_setting("log_level", "INFO"))

    if provider:
        config.active_provider = provider

    auditor = Auditor(config)
    return await auditor.run_audit(script_path, repo_path)


def main() -> None:
    """Main entry point - delegates to Click CLI."""
    from cli import cli

    setup_logging()
    cli()


if __name__ == "__main__":
    main()
