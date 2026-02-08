from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from pyvm_updater.cli import cli


class TestCliUse:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @patch("pyvm_updater.venv.find_python_executable")
    @patch("pyvm_updater.cli.subprocess.run")
    def test_use_version_success_linux(self, mock_run, mock_find, runner):
        # Mock finding python
        mock_find.return_value = "/usr/bin/python3.11"
        mock_session_dir = "/mock/pyvm_session_123"

        # Mock OS info for Linux
        with patch("pyvm_updater.cli.get_os_info", return_value=("linux", "amd64")):
            # Mock os.symlink, os.makedirs, mkdtemp
            with (
                patch("os.symlink"),
                patch("os.makedirs"),
                patch("tempfile.mkdtemp") as mock_mkdtemp,
                patch("shutil.rmtree") as mock_rmtree,
                patch("os.path.exists", return_value=False),
            ):  # For pip checks

                mock_mkdtemp.return_value = mock_session_dir

                result = runner.invoke(cli, ["use", "3.11.5"])

                assert result.exit_code == 0
                assert "Entering temporary shell for Python 3.11.5" in result.output

                # Check if symlinks were created
                # We expect symlink for python
                # mock_symlink.assert_any_call("/usr/bin/python3.11", f"{mock_session_dir}/bin/python")

                # Check subprocess call
                mock_run.assert_called_once()

                # Check cleanup
                mock_rmtree.assert_called_once_with(mock_session_dir)

    @patch("pyvm_updater.venv.find_python_executable")
    def test_use_version_not_found(self, mock_find, runner):
        mock_find.return_value = None

        result = runner.invoke(cli, ["use", "3.12.0"])

        # Note: click/sys.exit(1) generally results in exit_code 1
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_use_version_invalid_format(self, runner):
        result = runner.invoke(cli, ["use", "invalid-version"])
        assert result.exit_code == 1
        assert "Invalid version format" in result.output

    @patch("pyvm_updater.venv.find_python_executable")
    @patch("pyvm_updater.cli.subprocess.run")
    def test_use_version_windows_shim(self, mock_run, mock_find, runner):
        mock_find.return_value = "C:\\Python311\\python.exe"

        with patch("pyvm_updater.cli.get_os_info", return_value=("windows", "amd64")):
            with (
                patch("os.symlink", side_effect=OSError("Privilege error")),
                patch("os.makedirs"),
                patch("tempfile.mkdtemp", return_value="C:\\Temp\\session"),
                patch("shutil.rmtree"),
                patch("builtins.open", new_callable=MagicMock) as mock_open,
            ):

                result = runner.invoke(cli, ["use", "3.11.5"])

                assert result.exit_code == 0
                # Should attempt to write shim
                mock_open.assert_called()
