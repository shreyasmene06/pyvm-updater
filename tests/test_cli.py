from unittest.mock import patch

import pytest
from click.testing import CliRunner

from pyvm_updater.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_install_dry_run(runner):
    """Verify that the install dry-run flag prints the correct message and exits 0."""
    result = runner.invoke(cli, ["install", "3.12.1", "--dry-run"])
    assert result.exit_code == 0
    assert "[DRY-RUN]" in result.output
    assert "Would download and install Python 3.12.1" in result.output


def test_remove_dry_run(runner):
    """Verify that the remove dry-run flag prints the correct message and exits 0."""
    result = runner.invoke(cli, ["remove", "3.12.1", "--dry-run"])
    assert result.exit_code == 0
    assert "[DRY-RUN]" in result.output
    assert "Would remove Python 3.12.1" in result.output


def test_doctor_all_pass(runner):
    """All three checks pass."""
    with (
        patch("pyvm_updater.cli.shutil.which") as mock_which,
        patch("pyvm_updater.cli.requests.get"),
        patch("pyvm_updater.cli.os.access") as mock_access,
    ):
        mock_which.side_effect = lambda x: "/usr/bin/" + x if x == "pyenv" else None
        mock_access.return_value = True
        result = runner.invoke(cli, ["doctor"])
    assert result.exit_code == 0
    assert "System is healthy" in result.output


def test_doctor_missing_helper_tool(runner):
    """pyenv and mise both absent — warning only, still healthy."""
    with (
        patch("pyvm_updater.cli.shutil.which", return_value=None),
        patch("pyvm_updater.cli.requests.get"),
        patch("pyvm_updater.cli.os.access") as mock_access,
    ):
        mock_access.return_value = True
        result = runner.invoke(cli, ["doctor"])
    assert result.exit_code == 0
    assert "Neither pyenv nor mise found" in result.output
    assert "System is healthy" in result.output


def test_doctor_network_failure(runner):
    """Network unreachable marks overall health as failed."""
    with (
        patch("pyvm_updater.cli.shutil.which") as mock_which,
        patch("pyvm_updater.cli.requests.get") as mock_get,
        patch("pyvm_updater.cli.os.access") as mock_access,
    ):
        mock_which.side_effect = lambda x: "/usr/bin/" + x if x == "pyenv" else None
        mock_get.side_effect = Exception("Connection failed")
        mock_access.return_value = True
        result = runner.invoke(cli, ["doctor"])
    assert result.exit_code == 0
    assert "Failed to reach python.org" in result.output
    assert "Some checks failed" in result.output


def test_doctor_no_permission(runner):
    """Home directory not writable marks overall health as failed."""
    with (
        patch("pyvm_updater.cli.shutil.which") as mock_which,
        patch("pyvm_updater.cli.requests.get"),
        patch("pyvm_updater.cli.os.access") as mock_access,
    ):
        mock_which.side_effect = lambda x: "/usr/bin/" + x if x == "pyenv" else None
        mock_access.return_value = False
        result = runner.invoke(cli, ["doctor"])
    assert result.exit_code == 0
    assert "No write access" in result.output
    assert "Some checks failed" in result.output
