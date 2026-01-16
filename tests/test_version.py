"""Tests for pyvm_updater.version module."""

from unittest.mock import patch

from pyvm_updater.version import (
    check_python_version,
    get_installed_python_versions,
    is_python_version_installed,
)


class TestGetInstalledPythonVersions:
    """Tests for get_installed_python_versions function."""

    def test_returns_list(self):
        """Test that function returns a list."""
        result = get_installed_python_versions()
        assert isinstance(result, list)

    def test_contains_current_version(self):
        """Test that current Python version is in the list."""
        import platform

        current_ver = platform.python_version()
        result = get_installed_python_versions()
        versions = [v["version"] for v in result]
        assert current_ver in versions

    def test_each_item_has_required_keys(self):
        """Test that each item has required keys."""
        result = get_installed_python_versions()
        for item in result:
            assert "version" in item
            assert "path" in item
            assert "default" in item


class TestCheckPythonVersion:
    """Tests for check_python_version function."""

    def test_returns_tuple(self):
        """Test that function returns a tuple of 3 elements."""
        result = check_python_version(silent=True)
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_local_version_is_string(self):
        """Test that local version is a string."""
        local_ver, _, _ = check_python_version(silent=True)
        assert isinstance(local_ver, str)
        # Should be in X.Y.Z format
        parts = local_ver.split(".")
        assert len(parts) >= 2

    @patch("pyvm_updater.version.get_latest_python_info_with_retry")
    def test_handles_network_failure(self, mock_get_latest):
        """Test graceful handling when network fails."""
        mock_get_latest.return_value = (None, None)
        local_ver, latest_ver, needs_update = check_python_version(silent=True)
        assert latest_ver is None
        assert needs_update is False


class TestIsPythonVersionInstalled:
    """Tests for is_python_version_installed function."""

    def test_current_version_is_installed(self):
        """Test that current Python version is detected as installed."""
        import platform

        current_ver = platform.python_version()
        assert is_python_version_installed(current_ver) is True

    def test_fake_version_is_not_installed(self):
        """Test that a fake version is not detected as installed."""
        assert is_python_version_installed("99.99.99") is False

    def test_major_minor_match(self):
        """Test that current Python version is correctly detected."""
        import platform

        # Get the current full version (e.g., "3.12.12")
        current_ver = platform.python_version()

        # The current full version should definitely be installed
        assert is_python_version_installed(current_ver) is True
