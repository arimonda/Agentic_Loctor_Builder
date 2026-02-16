"""Factory for creating AI provider instances based on configuration."""

from __future__ import annotations

import logging
from typing import Optional

from ai.base_provider import BaseAIProvider
from ai.claude_provider import ClaudeProvider
from ai.gemini_provider import GeminiProvider
from ai.openai_provider import OpenAIProvider
from core.config_manager import ConfigManager

logger = logging.getLogger(__name__)

_PROVIDERS = {
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
    "claude": ClaudeProvider,
}


class ProviderFactory:
    """Creates and caches AI provider instances."""

    def __init__(self, config: ConfigManager) -> None:
        self._config = config
        self._cache: dict[str, BaseAIProvider] = {}

    def get_provider(self, name: Optional[str] = None) -> BaseAIProvider:
        """
        Get an AI provider instance.

        Uses the active provider from config if name is not specified.
        Instances are cached for reuse.
        """
        name = name or self._config.active_provider

        if name in self._cache:
            return self._cache[name]

        if name not in _PROVIDERS:
            raise ValueError(
                f"Unknown provider: '{name}'. Available: {list(_PROVIDERS.keys())}"
            )

        provider_cfg = self._config.get_provider_config(name)
        model = provider_cfg["model"]
        api_key = provider_cfg["api_key"]

        if not api_key or api_key == "YOUR_KEY_HERE":
            raise ValueError(
                f"API key not configured for provider '{name}'. "
                f"Set it in config.json or via environment variable."
            )

        provider_class = _PROVIDERS[name]
        instance = provider_class(model=model, api_key=api_key)
        self._cache[name] = instance
        logger.info("Created %s provider with model %s", name, model)
        return instance

    def switch_provider(self, name: str) -> BaseAIProvider:
        """Switch the active provider and return its instance."""
        self._config.active_provider = name
        return self.get_provider(name)

    def clear_cache(self) -> None:
        """Clear all cached provider instances."""
        self._cache.clear()
