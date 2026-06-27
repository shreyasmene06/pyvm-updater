"""Configuration management for pyvm_updater."""

from __future__ import annotations

import logging
from typing import Any

from .paths import get_config_dir
from .paths import get_config_file as _get_config_file

log = logging.getLogger("pyvm.config")

# Try to import tomllib (Python 3.11+) or fallback to tomli
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore

# Config file location (XDG-compliant)
CONFIG_DIR = get_config_dir()
CONFIG_FILE = _get_config_file()

# Default configuration
DEFAULT_CONFIG: dict[str, Any] = {
    "general": {
        "auto_confirm": False,
        "verbose": False,
        "preferred_installer": "auto",  # auto, mise, pyenv, system
    },
    "download": {
        "verify_checksum": True,
        "max_retries": 3,
        "timeout": 120,
    },
    "tui": {
        "theme": "dark",
        "show_eol_versions": False,
    },
}


class Config:
    """Configuration manager for pyvm."""

    _instance: Config | None = None
    _config: dict[str, Any]

    def __new__(cls) -> Config:
        """Singleton pattern to ensure only one config instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = DEFAULT_CONFIG.copy()
            cls._instance._load()
        return cls._instance

    def _load(self) -> None:
        """Load configuration from file if it exists."""
        if not CONFIG_FILE.exists():
            return

        if tomllib is None:
            return  # Can't parse TOML without library

        try:
            with open(CONFIG_FILE, "rb") as f:
                user_config = tomllib.load(f)
            self._merge_config(user_config)
        except Exception as e:
            log.warning("failed to parse %s: %s", CONFIG_FILE, e)

    def _merge_config(self, user_config: dict[str, Any]) -> None:
        """Merge user config into default config."""
        for section, values in user_config.items():
            if section in self._config and isinstance(values, dict):
                self._config[section].update(values)
            else:
                self._config[section] = values

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            section: Config section (e.g., "general", "download").
            key: Config key within section.
            default: Default value if not found.

        Returns:
            Configuration value or default.
        """
        try:
            return self._config[section][key]
        except KeyError:
            return default

    def set(self, section: str, key: str, value: Any) -> None:
        """Set a configuration value (runtime only, not persisted).

        Args:
            section: Config section.
            key: Config key.
            value: Value to set.
        """
        if section not in self._config:
            self._config[section] = {}
        self._config[section][key] = value

    @property
    def auto_confirm(self) -> bool:
        """Whether to skip confirmation prompts."""
        return bool(self.get("general", "auto_confirm", False))

    @property
    def verbose(self) -> bool:
        """Whether to show verbose output."""
        return bool(self.get("general", "verbose", False))

    @property
    def preferred_installer(self) -> str:
        """Preferred installation method."""
        return str(self.get("general", "preferred_installer", "auto"))

    @property
    def verify_checksum(self) -> bool:
        """Whether to verify download checksums."""
        return bool(self.get("download", "verify_checksum", True))

    @property
    def max_retries(self) -> int:
        """Maximum download retries."""
        return int(self.get("download", "max_retries", 3))

    @property
    def download_timeout(self) -> int:
        """Download timeout in seconds."""
        return int(self.get("download", "timeout", 120))

    @property
    def tui_theme(self) -> str:
        """TUI theme (dark/light)."""
        return str(self.get("tui", "theme", "dark"))

    def save(self) -> bool:
        """Save current configuration to file.

        Returns:
            True if saved successfully, False otherwise.
        """
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)

            # Format config as TOML manually (avoid dependency)
            lines = []
            for section, values in self._config.items():
                lines.append(f"[{section}]")
                for key, value in values.items():
                    if isinstance(value, bool):
                        lines.append(f"{key} = {str(value).lower()}")
                    elif isinstance(value, str):
                        lines.append(f'{key} = "{value}"')
                    else:
                        lines.append(f"{key} = {value}")
                lines.append("")

            with open(CONFIG_FILE, "w") as f:
                f.write("\n".join(lines))
            return True
        except Exception as e:
            log.warning("failed to save config to %s: %s", CONFIG_FILE, e)
            return False

    @staticmethod
    def create_default_config() -> bool:
        """Create default config file if it doesn't exist.

        Returns:
            True if created, False if already exists or error.
        """
        if CONFIG_FILE.exists():
            return False

        config = Config()
        return config.save()


# Convenience function
def get_config() -> Config:
    """Get the global configuration instance."""
    return Config()
