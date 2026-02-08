"""Tests for the plugin system."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from pyvm_updater.plugins.base import InstallerPlugin
from pyvm_updater.plugins.manager import PluginManager
from pyvm_updater.plugins.standard import MiseInstaller


class TestPluginManager:
    """Tests for PluginManager class."""

    def test_singleton(self):
        """Test that PluginManager is a singleton."""
        pm1 = PluginManager()
        pm2 = PluginManager()
        assert pm1 is pm2

    def test_builtin_registration(self):
        """Test that built-in plugins are registered automatically."""
        pm = PluginManager()
        plugins = pm.get_all_plugins()

        # Verify common built-ins are present
        plugin_names = [p.get_name() for p in plugins]
        assert "mise" in plugin_names
        assert "asdf" in plugin_names
        assert "pyenv" in plugin_names
        assert "conda" in plugin_names
        assert "source" in plugin_names

    def test_get_plugin(self):
        """Test getting a plugin by name."""
        pm = PluginManager()
        plugin = pm.get_plugin("mise")
        assert isinstance(plugin, MiseInstaller)

        assert pm.get_plugin("non-existent") is None

    def test_priority_ordering(self):
        """Test that supported plugins are returned sorted by priority."""
        pm = PluginManager()

        # Create some mock plugins with different priorities
        p1 = MagicMock(spec=InstallerPlugin)
        p1.get_name.return_value = "low-priority"
        p1.get_priority.return_value = 10
        p1.is_supported.return_value = True

        p2 = MagicMock(spec=InstallerPlugin)
        p2.get_name.return_value = "high-priority"
        p2.get_priority.return_value = 100
        p2.is_supported.return_value = True

        # Clear existing plugins for this test
        with patch.dict(pm._plugins, {"low": p1, "high": p2}, clear=True):
            supported = pm.get_supported_plugins()
            assert len(supported) == 2
            assert supported[0].get_name() == "high-priority"
            assert supported[1].get_name() == "low-priority"

    def test_custom_plugin_loading(self):
        """Test loading a custom plugin from a file."""
        pm = PluginManager()

        # Create a temporary plugin file
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            plugin_file = temp_path / "custom_plugin.py"

            plugin_code = """
from pyvm_updater.plugins.base import InstallerPlugin
from typing import Any

class CustomTestPlugin(InstallerPlugin):
    def get_name(self) -> str:
        return "custom-test"
    def is_supported(self) -> bool:
        return True
    def install(self, version: str, **kwargs: Any) -> bool:
        return True
    def uninstall(self, version: str) -> bool:
        return True
    def get_priority(self) -> int:
        return 500
"""
            plugin_file.write_text(plugin_code)

            # Use _load_plugin_from_file to load it
            pm._load_plugin_from_file(plugin_file)

            # Verify it's registered
            plugin = pm.get_plugin("custom-test")
            assert plugin is not None
            assert plugin.get_name() == "custom-test"
            assert plugin.get_priority() == 500

            # Clean up (remove from registered plugins)
            if "custom-test" in pm._plugins:
                del pm._plugins["custom-test"]
