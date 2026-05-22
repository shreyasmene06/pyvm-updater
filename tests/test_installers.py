"""Tests for the installers module dispatch logic."""

from unittest.mock import MagicMock, patch

from pyvm_updater.installers import (
    _install_with_plugins,
    _uninstall_with_plugins,
    remove_python_linux,
    remove_python_macos,
    remove_python_windows,
    show_python_usage_instructions,
    update_python_linux,
    update_python_macos,
    update_python_windows,
)


class TestInstallDispatch:
    @patch("pyvm_updater.installers.get_plugin_manager")
    def test_update_windows_delegates(self, mock_pm):
        mock_installer = MagicMock()
        mock_installer.install.return_value = True
        mock_pm.return_value.get_best_installer.return_value = mock_installer

        result = update_python_windows("3.12.0")
        assert result is True
        mock_installer.install.assert_called_once_with("3.12.0")

    @patch("pyvm_updater.installers.get_plugin_manager")
    def test_update_linux_build_from_source(self, mock_pm):
        mock_installer = MagicMock()
        mock_installer.install.return_value = True
        mock_pm.return_value.get_best_installer.return_value = mock_installer

        result = update_python_linux("3.12.0", build_from_source=True)
        assert result is True
        mock_pm.return_value.get_best_installer.assert_called_once_with(
            preferred="source"
        )

    @patch("pyvm_updater.installers.get_config")
    @patch("pyvm_updater.installers.get_plugin_manager")
    def test_update_linux_uses_preferred_installer(self, mock_pm, mock_config):
        mock_config.return_value.preferred_installer = "pyenv"
        mock_installer = MagicMock()
        mock_installer.install.return_value = True
        mock_pm.return_value.get_best_installer.return_value = mock_installer

        result = update_python_linux("3.12.0")
        assert result is True
        mock_pm.return_value.get_best_installer.assert_called_once_with(
            preferred="pyenv"
        )

    @patch("pyvm_updater.installers.get_plugin_manager")
    def test_update_macos_delegates(self, mock_pm):
        mock_installer = MagicMock()
        mock_installer.install.return_value = True
        mock_pm.return_value.get_best_installer.return_value = mock_installer

        result = update_python_macos("3.12.0")
        assert result is True
        mock_installer.install.assert_called_once_with("3.12.0")

    @patch("pyvm_updater.installers.get_plugin_manager")
    def test_install_no_supported_installer(self, mock_pm):
        mock_pm.return_value.get_best_installer.return_value = None

        result = _install_with_plugins("3.12.0")
        assert result is False

    @patch("pyvm_updater.installers.get_plugin_manager")
    def test_install_preferred_not_supported_falls_back(self, mock_pm):
        mock_installer = MagicMock()
        mock_installer.get_name.return_value = "pyenv"
        mock_installer.install.return_value = True
        mock_pm.return_value.get_best_installer.return_value = mock_installer

        result = _install_with_plugins("3.12.0", preferred="conda")
        assert result is True


class TestUninstallDispatch:
    @patch("pyvm_updater.installers.get_plugin_manager")
    def test_remove_linux(self, mock_pm):
        mock_installer = MagicMock()
        mock_installer.uninstall.return_value = True
        mock_pm.return_value.get_supported_plugins.return_value = [mock_installer]

        result = remove_python_linux("3.12.0")
        assert result is True

    @patch("pyvm_updater.installers.get_plugin_manager")
    def test_remove_windows(self, mock_pm):
        mock_installer = MagicMock()
        mock_installer.uninstall.return_value = True
        mock_pm.return_value.get_supported_plugins.return_value = [mock_installer]

        result = remove_python_windows("3.12.0")
        assert result is True

    @patch("pyvm_updater.installers.get_plugin_manager")
    def test_remove_macos(self, mock_pm):
        mock_installer = MagicMock()
        mock_installer.uninstall.return_value = True
        mock_pm.return_value.get_supported_plugins.return_value = [mock_installer]

        result = remove_python_macos("3.12.0")
        assert result is True

    @patch("pyvm_updater.installers.get_plugin_manager")
    def test_uninstall_no_supported_installer(self, mock_pm):
        mock_pm.return_value.get_supported_plugins.return_value = []

        result = _uninstall_with_plugins("3.12.0")
        assert result is False

    @patch("pyvm_updater.installers.get_plugin_manager")
    def test_uninstall_tries_multiple_installers(self, mock_pm):
        fail = MagicMock()
        fail.uninstall.return_value = False
        succeed = MagicMock()
        succeed.uninstall.return_value = True

        mock_pm.return_value.get_supported_plugins.return_value = [fail, succeed]

        result = _uninstall_with_plugins("3.12.0")
        assert result is True
        fail.uninstall.assert_called_once_with("3.12.0")
        succeed.uninstall.assert_called_once_with("3.12.0")


class TestUsageInstructions:
    def test_linux_instructions(self):
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            show_python_usage_instructions("3.12.0", "linux")
        output = f.getvalue()
        assert "python3.12" in output
        assert "venv" in output

    def test_windows_instructions(self):
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            show_python_usage_instructions("3.12.0", "windows")
        output = f.getvalue()
        assert "py -3.12" in output
        assert "py --list" in output

    def test_macos_instructions(self):
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            show_python_usage_instructions("3.11.5", "darwin")
        output = f.getvalue()
        assert "python3.11" in output

    def test_malformed_version(self):
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            show_python_usage_instructions("not-a-version", "linux")
        output = f.getvalue()
        assert "not-a-version" in output
