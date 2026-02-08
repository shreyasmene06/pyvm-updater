"""Tests for Microsoft Store Python detection logic."""

from unittest.mock import MagicMock, patch

from pyvm_updater.version import get_installed_python_versions


class TestStoreDetection:
    """Tests for Microsoft Store Python detection in version.py."""

    @patch("pyvm_updater.version.get_os_info")
    @patch("subprocess.run")
    @patch("os.path.isdir")
    @patch("os.listdir")
    @patch("os.path.expandvars")
    def test_detect_via_py_list(self, mock_expandvars, mock_listdir, mock_isdir, mock_run, mock_get_os):
        """Test detection via 'py --list' output."""
        mock_get_os.return_value = ("windows", "10")

        # Mock py --list output
        mock_run_result = MagicMock()
        mock_run_result.returncode = 0
        mock_run_result.stdout = " -3.12-64 (Store) *\n -3.11-64\n"
        mock_run.return_value = mock_run_result

        # Mock other Windows checks to return nothing
        mock_expandvars.return_value = "C:\\Apps"
        mock_isdir.return_value = False

        versions = get_installed_python_versions()

        # Check if 3.12 was detected as Store version
        store_v12 = next((v for v in versions if v["version"] == "3.12"), None)
        assert store_v12 is not None
        assert store_v12["store"] is True
        assert store_v12["default"] is True

    @patch("pyvm_updater.version.get_os_info")
    @patch("subprocess.run")
    @patch("os.path.isdir")
    @patch("os.listdir")
    @patch("os.path.expandvars")
    @patch("os.path.join")
    def test_detect_via_windowsapps_path(
        self, mock_join, mock_expandvars, mock_listdir, mock_isdir, mock_run, mock_get_os
    ):
        """Test detection via %LOCALAPPDATA%\\Microsoft\\WindowsApps path."""
        mock_get_os.return_value = ("windows", "10")

        # Mock py --list to fail or return nothing
        mock_run_result = MagicMock()
        mock_run_result.returncode = 1
        mock_run.return_value = mock_run_result

        # Mock WindowsApps directory
        apps_dir = "C:\\Users\\User\\AppData\\Local\\Microsoft\\WindowsApps"
        mock_expandvars.return_value = apps_dir
        mock_isdir.return_value = True
        mock_listdir.return_value = ["python3.11.exe", "python3.12.exe", "something_else.exe"]
        mock_join.side_effect = lambda *args: "\\".join(args)

        versions = get_installed_python_versions()

        # Check for 3.11 and 3.12
        v11 = next((v for v in versions if v["version"] == "3.11"), None)
        v12 = next((v for v in versions if v["version"] == "3.12"), None)

        assert v11 is not None
        assert v11["store"] is True
        assert v11["path"] == f"{apps_dir}\\python3.11.exe"

        assert v12 is not None
        assert v12["store"] is True
        assert v12["path"] == f"{apps_dir}\\python3.12.exe"

    @patch("pyvm_updater.version.get_os_info")
    @patch("subprocess.run")
    @patch("os.path.isdir")
    @patch("os.listdir")
    @patch("os.path.expandvars")
    def test_merge_py_list_and_path_info(self, mock_expandvars, mock_listdir, mock_isdir, mock_run, mock_get_os):
        """Test that info from py --list and path scanning are merged correctly."""
        mock_get_os.return_value = ("windows", "10")

        # py --list finds 3.12 but doesn't know path
        mock_run_result = MagicMock()
        mock_run_result.returncode = 0
        mock_run_result.stdout = " -3.12-64 (Store)\n"
        mock_run.return_value = mock_run_result

        # Path scanning finds 3.12 path
        apps_dir = "C:\\StoreApps"
        mock_expandvars.return_value = apps_dir
        mock_isdir.return_value = True
        mock_listdir.return_value = ["python3.12.exe"]

        versions = get_installed_python_versions()

        v12 = next((v for v in versions if v["version"] == "3.12"), None)
        assert v12 is not None
        assert v12["store"] is True
        assert v12["path"] is not None
        assert "StoreApps" in v12["path"]
