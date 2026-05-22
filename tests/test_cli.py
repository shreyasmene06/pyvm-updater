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

    
def test_build_from_source_windows(runner):
    result = runner.invoke(
        cli,
        ["install", "3.12.1", "--build-from-source"]
    )

    assert result.exit_code != 0
    assert "only supported on Linux" in result.output