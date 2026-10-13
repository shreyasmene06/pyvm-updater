"""Tests for --json output flag on check, list, and info commands."""

import json
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from pyvm_updater.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


class TestCheckJson:
    """Tests for pyvm check --json."""

    @patch("pyvm_updater.cli.check_python_version")
    def test_check_json_output_is_valid(self, mock_check, runner):
        mock_check.return_value = ("3.12.1", "3.13.0", True)
        result = runner.invoke(cli, ["check", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["local_version"] == "3.12.1"
        assert data["latest_version"] == "3.13.0"
        assert data["update_available"] is True

    @patch("pyvm_updater.cli.check_python_version")
    def test_check_json_no_update(self, mock_check, runner):
        mock_check.return_value = ("3.13.0", "3.13.0", False)
        result = runner.invoke(cli, ["check", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["update_available"] is False

    @patch("pyvm_updater.cli.check_python_version")
    def test_check_json_network_failure(self, mock_check, runner):
        mock_check.return_value = ("3.12.1", None, False)
        result = runner.invoke(cli, ["check", "--json"])
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["latest_version"] is None
        assert data["update_available"] is False


class TestInfoJson:
    """Tests for pyvm info --json."""

    def test_info_json_output_is_valid(self, runner):
        result = runner.invoke(cli, ["info", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "os" in data
        assert "architecture" in data
        assert "python_version" in data
        assert "python_path" in data
        assert "platform" in data
        assert "admin" in data

    def test_info_json_types(self, runner):
        result = runner.invoke(cli, ["info", "--json"])
        data = json.loads(result.output)
        assert isinstance(data["os"], str)
        assert isinstance(data["admin"], bool)


class TestListJson:
    """Tests for pyvm list --json."""

    @patch("pyvm_updater.cli.get_active_python_releases")
    def test_list_json_releases(self, mock_releases, runner):
        mock_releases.return_value = [
            {
                "series": "3.13",
                "latest_version": "3.13.0",
                "status": "bugfix",
                "end_of_support": "2029-10",
            },
            {
                "series": "3.12",
                "latest_version": "3.12.7",
                "status": "security",
                "end_of_support": "2028-10",
            },
        ]
        result = runner.invoke(cli, ["list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "local_version" in data
        assert "releases" in data
        assert len(data["releases"]) == 2
        assert data["releases"][0]["series"] == "3.13"

    @patch("pyvm_updater.cli.get_available_python_versions")
    @patch("pyvm_updater.cli.get_latest_python_info_with_retry")
    def test_list_all_json(self, mock_latest, mock_versions, runner):
        mock_versions.return_value = [
            {"version": "3.13.0"},
            {"version": "3.12.7"},
        ]
        mock_latest.return_value = ("3.13.0", "https://example.com")
        result = runner.invoke(cli, ["list", "--all", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "versions" in data
        assert len(data["versions"]) == 2
        assert data["versions"][0]["version"] == "3.13.0"
        assert data["versions"][0]["latest"] is True

def test_list_json_releases():
    """Validates standard active branch json mapping format."""
    from click.testing import CliRunner
    from pyvm_updater.cli import cli
    import json

    runner = CliRunner()
    result = runner.invoke(cli, ["list", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "local_version" in data
    assert "releases" in data


def test_list_all_json():
    """Validates the --all flag combinations match output specs."""
    from click.testing import CliRunner
    from pyvm_updater.cli import cli
    import json

    runner = CliRunner()
    result = runner.invoke(cli, ["list", "--all", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "latest_version" in data
