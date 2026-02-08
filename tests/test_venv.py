"""Tests for pyvm_updater.venv module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from pyvm_updater.venv import (
    create_venv,
    get_venv_activate_command,
    list_venvs,
    remove_venv,
)


class TestCreateVenv:
    """Tests for create_venv function."""

    @pytest.fixture
    def temp_venv_dir(self):
        """Create a temporary directory for venvs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_create_venv_success(self, temp_venv_dir):
        """Test successful venv creation."""
        venv_path = temp_venv_dir / "test_venv"

        with patch("pyvm_updater.venv.get_venv_dir", return_value=temp_venv_dir):
            with patch("pyvm_updater.venv.save_venv_registry"):
                success, message = create_venv("test_venv", path=venv_path)

        assert success is True
        assert "Created" in message
        assert venv_path.exists()

    def test_create_venv_already_exists(self, temp_venv_dir):
        """Test creating venv that already exists."""
        venv_path = temp_venv_dir / "existing_venv"
        venv_path.mkdir()

        success, message = create_venv("existing_venv", path=venv_path)

        assert success is False
        assert "already exists" in message

    def test_create_venv_with_requirements(self, temp_venv_dir):
        """Test venv creation with requirements file."""
        venv_path = temp_venv_dir / "req_venv"
        req_file = temp_venv_dir / "requirements.txt"
        req_file.write_text("requests==2.25.0")

        with patch("pyvm_updater.venv.get_venv_dir", return_value=temp_venv_dir):
            with patch("pyvm_updater.venv.save_venv_registry"):
                with patch("pyvm_updater.venv.subprocess.run") as mock_run:
                    success, message = create_venv("req_venv", path=venv_path, requirements_file=req_file)

        assert success is True
        assert "Installed requirements" in message

        # Verify pip install was called
        assert mock_run.call_count == 2

        args, _ = mock_run.call_args_list[1]
        cmd = args[0]
        assert "install" in cmd
        assert "-r" in cmd
        assert str(req_file) in cmd


class TestListVenvs:
    """Tests for list_venvs function."""

    def test_list_venvs_empty(self):
        """Test list_venvs when no venvs exist."""
        with patch("pyvm_updater.venv.get_venv_registry", return_value={}):
            with patch("pyvm_updater.venv.get_venv_dir") as mock_dir:
                mock_dir.return_value = Path("/nonexistent")
                result = list_venvs()

        assert isinstance(result, list)

    def test_list_venvs_returns_list(self):
        """Test list_venvs returns a list."""
        with patch("pyvm_updater.venv.get_venv_registry", return_value={}):
            with patch("pyvm_updater.venv.get_venv_dir") as mock_dir:
                mock_dir.return_value = Path("/nonexistent")
                result = list_venvs()

        assert isinstance(result, list)


class TestRemoveVenv:
    """Tests for remove_venv function."""

    @pytest.fixture
    def temp_venv_dir(self):
        """Create a temporary directory for venvs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_remove_nonexistent_venv(self, temp_venv_dir):
        """Test removing venv that doesn't exist."""
        with patch("pyvm_updater.venv.get_venv_registry", return_value={}):
            with patch("pyvm_updater.venv.get_venv_dir", return_value=temp_venv_dir):
                success, message = remove_venv("nonexistent")

        assert success is False
        assert "not found" in message

    def test_remove_existing_venv(self, temp_venv_dir):
        """Test removing existing venv."""
        venv_path = temp_venv_dir / "to_remove"
        venv_path.mkdir()

        registry = {"to_remove": {"path": str(venv_path)}}

        with patch("pyvm_updater.venv.get_venv_registry", return_value=registry):
            with patch("pyvm_updater.venv.save_venv_registry"):
                success, message = remove_venv("to_remove")

        assert success is True
        assert "Removed" in message
        assert not venv_path.exists()


class TestGetVenvActivateCommand:
    """Tests for get_venv_activate_command function."""

    @pytest.fixture
    def temp_venv_dir(self):
        """Create a temporary directory for venvs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_activate_nonexistent_venv(self, temp_venv_dir):
        """Test getting activate command for nonexistent venv."""
        with patch("pyvm_updater.venv.get_venv_registry", return_value={}):
            with patch("pyvm_updater.venv.get_venv_dir", return_value=temp_venv_dir):
                result = get_venv_activate_command("nonexistent")

        assert result is None

    def test_activate_existing_venv(self, temp_venv_dir):
        """Test getting activate command for existing venv."""
        venv_path = temp_venv_dir / "test_venv"
        bin_dir = venv_path / "bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "activate").touch()

        registry = {"test_venv": {"path": str(venv_path)}}

        with patch("pyvm_updater.venv.get_venv_registry", return_value=registry):
            with patch("pyvm_updater.venv.get_os_info", return_value=("linux", "amd64")):
                result = get_venv_activate_command("test_venv")

        assert result is not None
        assert "activate" in result
