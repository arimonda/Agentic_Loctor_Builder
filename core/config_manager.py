"""Centralized configuration management with runtime switching."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

load_dotenv()


class ConfigManager:
    """Manages application configuration with thread-safe runtime updates."""

    _instance: Optional[ConfigManager] = None
    _lock = threading.Lock()

    def __new__(cls, config_path: str = "config.json") -> ConfigManager:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, config_path: str = "config.json") -> None:
        if self._initialized:
            return
        self._config_path = Path(config_path)
        self._config: dict = {}
        self._callbacks: list = []
        self._rw_lock = threading.RLock()
        self._load_config()
        self._apply_env_overrides()
        self._initialized = True

    def _load_config(self) -> None:
        """Load configuration from JSON file."""
        if not self._config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self._config_path}")
        with open(self._config_path, "r", encoding="utf-8") as f:
            self._config = json.load(f)
        self._ensure_directories()

    def _apply_env_overrides(self) -> None:
        """Override config values with environment variables."""
        env_key_map = {
            "gemini": "GEMINI_API_KEY",
            "openai": "OPENAI_API_KEY",
            "claude": "CLAUDE_API_KEY",
        }
        for provider, env_key in env_key_map.items():
            val = os.getenv(env_key)
            if val and provider in self._config.get("providers", {}):
                self._config["providers"][provider]["api_key"] = val

        active = os.getenv("ACTIVE_PROVIDER")
        if active:
            self._config["active_provider"] = active

        headless = os.getenv("HEADLESS")
        if headless is not None:
            self._config.setdefault("settings", {})["headless"] = headless.lower() == "true"

    def _ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        settings = self._config.get("settings", {})
        for dir_key in ["screenshot_path", "dom_capture_path"]:
            path = settings.get(dir_key)
            if path:
                Path(path).mkdir(parents=True, exist_ok=True)
        db_path = settings.get("known_locators_db")
        if db_path:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    @property
    def active_provider(self) -> str:
        with self._rw_lock:
            return self._config.get("active_provider", "gemini")

    @active_provider.setter
    def active_provider(self, provider: str) -> None:
        valid = list(self._config.get("providers", {}).keys())
        if provider not in valid:
            raise ValueError(f"Invalid provider '{provider}'. Valid: {valid}")
        with self._rw_lock:
            self._config["active_provider"] = provider
            self._save_config()
            self._notify("provider_changed", provider)

    def get_provider_config(self, provider: Optional[str] = None) -> dict:
        """Get configuration for a specific AI provider."""
        provider = provider or self.active_provider
        with self._rw_lock:
            cfg = self._config.get("providers", {}).get(provider)
            if not cfg:
                raise ValueError(f"No configuration for provider: {provider}")
            return dict(cfg)

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        with self._rw_lock:
            return self._config.get("settings", {}).get(key, default)

    def set_setting(self, key: str, value: Any) -> None:
        """Update a setting value at runtime."""
        with self._rw_lock:
            self._config.setdefault("settings", {})[key] = value
            self._save_config()
            self._notify("setting_changed", {key: value})

    def get_all_providers(self) -> list[str]:
        """List all configured provider names."""
        with self._rw_lock:
            return list(self._config.get("providers", {}).keys())

    def _save_config(self) -> None:
        """Persist current config to disk."""
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2)

    def on_change(self, callback) -> None:
        """Register a callback for config changes."""
        self._callbacks.append(callback)

    def _notify(self, event: str, data: Any) -> None:
        for cb in self._callbacks:
            try:
                cb(event, data)
            except Exception:
                pass

    def to_dict(self) -> dict:
        """Return a safe copy of the config (without API keys)."""
        with self._rw_lock:
            cfg = json.loads(json.dumps(self._config))
            for prov in cfg.get("providers", {}).values():
                if "api_key" in prov:
                    prov["api_key"] = "***REDACTED***"
            return cfg

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton (for testing)."""
        with cls._lock:
            cls._instance = None
