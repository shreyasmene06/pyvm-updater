"""Plugin manager for Python installers."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from ..config import CONFIG_DIR
from .base import InstallerPlugin
from .standard import (
    AptInstaller,
    AsdfInstaller,
    BrewInstaller,
    CondaInstaller,
    MicrosoftStoreInstaller,
    MiseInstaller,
    PyenvInstaller,
    SourceInstaller,
    WindowsInstaller,
)


class PluginManager:
    """Manages discovery and loading of installer plugins."""

    _instance: PluginManager | None = None
    _plugins: dict[str, InstallerPlugin] = {}

    def __new__(cls) -> PluginManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._register_builtins()
            cls._instance._load_custom_plugins()
        return cls._instance

    def _register_builtins(self) -> None:
        """Register built-in installer plugins."""
        builtins = [
            MiseInstaller(),
            AsdfInstaller(),
            PyenvInstaller(),
            BrewInstaller(),
            CondaInstaller(),
            AptInstaller(),
            MicrosoftStoreInstaller(),
            WindowsInstaller(),
            SourceInstaller(),
        ]
        for plugin in builtins:
            self.register_plugin(plugin)

    def _load_custom_plugins(self) -> None:
        """Load custom plugins from the user's config directory."""
        plugin_dir = CONFIG_DIR / "plugins"
        if not plugin_dir.exists():
            return

        for file in plugin_dir.glob("*.py"):
            if file.name == "__init__.py":
                continue
            self._load_plugin_from_file(file)

    def _load_plugin_from_file(self, file_path: Path) -> None:
        """Load a plugin from a Python file."""
        try:
            module_name = f"pyvm_plugins.{file_path.stem}"
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find classes that inherit from InstallerPlugin
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, InstallerPlugin) and attr is not InstallerPlugin:
                        self.register_plugin(attr())
        except Exception as e:
            print(f"Error loading plugin from {file_path}: {e}")

    def register_plugin(self, plugin: InstallerPlugin) -> None:
        """Register a plugin instance."""
        self._plugins[plugin.get_name()] = plugin

    def get_plugin(self, name: str) -> InstallerPlugin | None:
        """Get a plugin by name."""
        return self._plugins.get(name)

    def get_all_plugins(self) -> list[InstallerPlugin]:
        """Get all registered plugins."""
        return list(self._plugins.values())

    def get_supported_plugins(self) -> list[InstallerPlugin]:
        """Get all plugins supported on the current system, sorted by priority."""
        supported = [p for p in self._plugins.values() if p.is_supported()]
        return sorted(supported, key=lambda p: p.get_priority(), reverse=True)

    def get_best_installer(self, preferred: str = "auto") -> InstallerPlugin | None:
        """Get the best installer based on preference and support."""
        if preferred != "auto":
            plugin = self.get_plugin(preferred)
            if plugin and plugin.is_supported():
                return plugin

        supported = self.get_supported_plugins()
        return supported[0] if supported else None


# Convenience function
def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager instance."""
    return PluginManager()
