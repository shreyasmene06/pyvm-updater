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


class TestValidateVenvName:
    """Tests for _validate_venv_name input validation."""

    # --- valid names (should pass) ---

    def test_valid_simple_name(self):
        from pyvm_updater.venv import _validate_venv_name

        valid, err = _validate_venv_name("myproject")
        assert valid is True
        assert err == ""

    def test_valid_name_with_hyphens_and_underscores(self):
        from pyvm_updater.venv import _validate_venv_name

        valid, err = _validate_venv_name("my-project_v2")
        assert valid is True

    def test_valid_name_with_dots(self):
        from pyvm_updater.venv import _validate_venv_name

        valid, err = _validate_venv_name("env.3.12")
        assert valid is True

    # --- path traversal (should fail) ---

    def test_rejects_dotdot_slash(self):
        from pyvm_updater.venv import _validate_venv_name

        valid, err = _validate_venv_name("../escape")
        assert valid is False
        assert "path separators" in err

    def test_rejects_deep_traversal(self):
        from pyvm_updater.venv import _validate_venv_name

        valid, err = _validate_venv_name("../../etc")
        assert valid is False

    def test_rejects_dotdot_alone(self):
        from pyvm_updater.venv import _validate_venv_name

        valid, err = _validate_venv_name("..")
        assert valid is False
        assert "'.'" in err or "'..'" in err

    def test_rejects_dot_alone(self):
        from pyvm_updater.venv import _validate_venv_name

        valid, err = _validate_venv_name(".")
        assert valid is False

    def test_rejects_absolute_unix_path(self):
        from pyvm_updater.venv import _validate_venv_name

        valid, err = _validate_venv_name("/absolute/path")
        assert valid is False

    def test_rejects_windows_backslash(self):
        from pyvm_updater.venv import _validate_venv_name

        valid, err = _validate_venv_name("..\\escape")
        assert valid is False

    # --- empty / too long ---

    def test_rejects_empty_string(self):
        from pyvm_updater.venv import _validate_venv_name

        valid, err = _validate_venv_name("")
        assert valid is False
        assert "empty" in err

    def test_rejects_whitespace_only(self):
        from pyvm_updater.venv import _validate_venv_name

        valid, err = _validate_venv_name("   ")
        assert valid is False

    def test_rejects_name_over_128_chars(self):
        from pyvm_updater.venv import _validate_venv_name

        valid, err = _validate_venv_name("a" * 129)
        assert valid is False
        assert "128" in err

    # --- special characters ---

    def test_rejects_semicolon(self):
        from pyvm_updater.venv import _validate_venv_name

        valid, err = _validate_venv_name("name; rm -rf")
        assert valid is False

    def test_rejects_null_byte(self):
        from pyvm_updater.venv import _validate_venv_name

        valid, err = _validate_venv_name("name\x00evil")
        assert valid is False
        assert "null" in err

    # --- integration: create_venv rejects bad name ---

    def test_create_venv_rejects_traversal_name(self):
        success, message = create_venv("../outside")
        assert success is False
        assert "Invalid" in message or "path separators" in message

    def test_remove_venv_rejects_traversal_name(self):
        from pyvm_updater.venv import remove_venv

        success, message = remove_venv("../outside")
        assert success is False
        assert "Invalid" in message

    def test_rename_venv_rejects_traversal_new_name(self):
        from pyvm_updater.venv import rename_venv

        success, message = rename_venv("myenv", "../outside")
        assert success is False
        assert "Invalid" in message

    def test_duplicate_venv_rejects_traversal_new_name(self):
        from pyvm_updater.venv import duplicate_venv

        success, message = duplicate_venv("myenv", "../outside")
        assert success is False
        assert "Invalid" in message