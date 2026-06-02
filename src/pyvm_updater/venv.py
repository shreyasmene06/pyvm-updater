"""Virtual environment management for pyvm_updater."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from .logging_config import get_logger
from .paths import get_venv_dir as _get_venv_dir
from .paths import get_venv_registry_file
from .utils import get_os_info
from .version import get_installed_python_versions

log = get_logger("venv")

# Default venv directory (XDG_DATA_HOME/pyvm/venvs)
DEFAULT_VENV_DIR = _get_venv_dir()
VENV_REGISTRY = get_venv_registry_file()


def get_venv_dir() -> Path:
    """Get the directory where venvs are stored."""
    return DEFAULT_VENV_DIR


def get_venv_registry() -> dict[str, Any]:
    """Load the venv registry from disk."""
    if not VENV_REGISTRY.exists():
        return {}
    try:
        with open(VENV_REGISTRY) as f:
            data = json.load(f)
            return dict(data) if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_venv_registry(registry: dict[str, Any]) -> None:
    """Save the venv registry to disk."""
    try:
        VENV_REGISTRY.parent.mkdir(parents=True, exist_ok=True)
        with open(VENV_REGISTRY, "w") as f:
            json.dump(registry, f, indent=2)
    except OSError as e:
        log.warning(f"Could not save venv registry: {e}")
        raise


def find_python_executable(version: str) -> str | None:
    """Find a Python executable for the given version.

    Args:
        version: Python version (e.g., "3.12" or "3.12.1")

    Returns:
        Path to Python executable, or None if not found.
    """
    os_name, _ = get_os_info()

    # Parse version
    parts = version.split(".")
    major_minor = f"{parts[0]}.{parts[1]}" if len(parts) >= 2 else version

    # Check installed versions
    installed = get_installed_python_versions()
    for v in installed:
        v_parts = v["version"].split(".")
        v_major_minor = f"{v_parts[0]}.{v_parts[1]}" if len(v_parts) >= 2 else v["version"]
        if v_major_minor == major_minor and v.get("path"):
            path = v["path"]
            return str(path) if path else None

    # Try common paths
    if os_name == "windows":
        # Try py launcher
        try:
            result = subprocess.run(
                ["py", f"-{major_minor}", "-c", "import sys; print(sys.executable)"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            return result.stdout.strip()
        except Exception:
            pass
    else:
        # Try common Unix paths
        candidates = [
            f"python{major_minor}",
            f"python{parts[0]}",
            os.path.expanduser(f"~/.local/share/mise/installs/python/{version}/bin/python3"),
            os.path.expanduser(f"~/.pyenv/versions/{version}/bin/python3"),
        ]

        for candidate in candidates:
            if os.path.isabs(candidate):
                if os.path.exists(candidate) and os.access(candidate, os.X_OK):
                    return candidate
            else:
                path = shutil.which(candidate)
                if path:
                    return str(path)

    return None


def create_venv(
    name: str,
    python_version: str | None = None,
    path: Path | None = None,
    system_site_packages: bool = False,
    requirements_file: Path | None = None,
) -> tuple[bool, str]:
    """Create a new virtual environment.

    Args:
        name: Name of the venv.
        python_version: Python version to use (e.g., "3.12"). If None, uses current Python.
        path: Custom path for venv. If None, uses default location.
        system_site_packages: Whether to include system site-packages.
        requirements_file: Path to requirements.txt file to install.

    Returns:
        Tuple of (success, message).
    """
    # Determine venv path
    if path:
        venv_path = path
    else:
        venv_path = get_venv_dir() / name

    # Check if already exists
    if venv_path.exists():
        return False, f"Venv '{name}' already exists at {venv_path}"

    # Find Python executable
    if python_version:
        python_exe = find_python_executable(python_version)
        if not python_exe:
            return (
                False,
                f"Python {python_version} not found. Install it first with: pyvm install {python_version}.0",
            )
    else:
        python_exe = sys.executable
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"

    cmd = [python_exe, "-m", "venv"]
    if system_site_packages:
        cmd.append("--system-site-packages")
    cmd.append(str(venv_path))

    try:
        # Create parent directory
        venv_path.parent.mkdir(parents=True, exist_ok=True)

        # Create venv
        subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Register venv
        registry = get_venv_registry()
        registry[name] = {
            "path": str(venv_path),
            "python_version": python_version,
            "python_executable": python_exe,
            "system_site_packages": system_site_packages,
        }
        save_venv_registry(registry)

        success_msg = f"Created venv '{name}' at {venv_path}"

        # Install requirements if specified
        if requirements_file:
            os_name, _ = get_os_info()
            if os_name == "windows":
                pip_exe = venv_path / "Scripts" / "pip.exe"
            else:
                pip_exe = venv_path / "bin" / "pip"

            if not pip_exe.exists():
                if os_name == "windows":
                    python_in_venv = venv_path / "Scripts" / "python.exe"
                else:
                    python_in_venv = venv_path / "bin" / "python"
                pip_cmd = [str(python_in_venv), "-m", "pip"]
            else:
                pip_cmd = [str(pip_exe)]

            try:
                # Upgrade pip first (optional helper)
                # subprocess.run(pip_cmd + ["install", "--upgrade", "pip"], capture_output=True, check=False)

                # Install requirements
                subprocess.run(
                    pip_cmd + ["install", "-r", str(requirements_file)], capture_output=True, text=True, check=True
                )
                success_msg += f"\n   Installed requirements from {requirements_file.name}"
            except subprocess.CalledProcessError as e:
                error_output = e.stderr or e.stdout
                return (
                    True,
                    f"{success_msg}\n   [!] Warning: Failed to install requirements from {requirements_file.name}:\n"
                    f"{error_output}",
                )

        return True, success_msg

    except subprocess.CalledProcessError as e:
        return (
            False,
            f"Failed to create venv: {e.stderr or e.stdout or str(e)}",
        )
    except OSError as e:
        return False, f"Failed to create venv: {e}"


def list_venvs() -> list[dict[str, Any]]:
    """List all registered virtual environments.

    Returns:
        List of venv info dicts with keys: name, path, python_version, exists.
    """
    registry = get_venv_registry()
    venvs = []

    for name, info in registry.items():
        venv_path = Path(info.get("path", ""))
        venvs.append(
            {
                "name": name,
                "path": str(venv_path),
                "python_version": info.get("python_version", "unknown"),
                "exists": venv_path.exists(),
            }
        )

    # Also check for unregistered venvs in default directory
    venv_dir = get_venv_dir()
    if venv_dir.exists():
        for entry in venv_dir.iterdir():
            if entry.is_dir() and entry.name not in registry:
                # Check if it's a venv
                activate = entry / "bin" / "activate"
                if not activate.exists():
                    activate = entry / "Scripts" / "activate.bat"
                if activate.exists():
                    venvs.append(
                        {
                            "name": entry.name,
                            "path": str(entry),
                            "python_version": "unknown",
                            "exists": True,
                        }
                    )

    return sorted(venvs, key=lambda x: x["name"])


def remove_venv(name: str, force: bool = False) -> tuple[bool, str]:
    """Remove a virtual environment.

    Args:
        name: Name of the venv to remove.
        force: Skip confirmation (for programmatic use).

    Returns:
        Tuple of (success, message).
    """
    registry = get_venv_registry()

    # Find venv path
    if name in registry:
        venv_path = Path(registry[name].get("path", ""))
    else:
        venv_path = get_venv_dir() / name

    if not venv_path.exists():
        # Remove from registry if it exists
        if name in registry:
            del registry[name]
            save_venv_registry(registry)
            return True, f"Removed stale registry entry for '{name}'"
        return False, f"Venv '{name}' not found"

    try:
        shutil.rmtree(venv_path)

        # Remove from registry
        if name in registry:
            del registry[name]
            save_venv_registry(registry)

        return True, f"Removed venv '{name}'"

    except OSError as e:
        return False, f"Failed to remove venv: {e}"


def _fix_venv_paths(venv_path: Path, old_path: Path) -> None:
    """Fix hardcoded paths inside a venv so it points to its new location.

    Args:
        venv_path: The new venv directory.
        old_path: The original venv directory.
    """
    old_str = str(old_path)
    new_str = str(venv_path)

    # Fix pyvenv.cfg
    cfg = venv_path / "pyvenv.cfg"
    if cfg.exists():
        try:
            t = cfg.read_text(encoding="utf-8")
            cfg.write_text(t.replace(old_str, new_str), encoding="utf-8")
        except OSError:
            pass

    # Fix all scripts in bin/Scripts (activation scripts, pip, wrappers, etc.)
    for scripts_dir in [venv_path / "bin", venv_path / "Scripts"]:
        if not scripts_dir.exists():
            continue

        for script in scripts_dir.iterdir():
            if not script.is_file():
                continue

            try:
                # Try to process as text first (for shell scripts, .bat, .ps1, python scripts)
                try:
                    t = script.read_text(encoding="utf-8")
                    if old_str in t:
                        script.write_text(t.replace(old_str, new_str), encoding="utf-8")
                except UnicodeDecodeError:
                    # Fallback for binary wrappers (e.g. pip.exe launcher)
                    b = script.read_bytes()
                    old_bytes = old_str.encode("utf-8")
                    new_bytes = new_str.encode("utf-8")
                    if old_bytes in b:
                        script.write_bytes(b.replace(old_bytes, new_bytes))
            except OSError:
                pass


def rename_venv(old_name: str, new_name: str) -> tuple[bool, str]:
    """Rename a virtual environment on disk and in the registry.

    Args:
        old_name: Current name of the venv.
        new_name: Desired new name for the venv.

    Returns:
        Tuple of (success, message).
    """
    registry = get_venv_registry()

    # Resolve old venv path
    if old_name in registry:
        old_path = Path(registry[old_name].get("path", ""))
    else:
        old_path = get_venv_dir() / old_name

    # Check old venv exists (on disk or in registry)
    if old_name not in registry and not old_path.exists():
        return False, f"Venv '{old_name}' not found"

    # Check new name is not taken
    new_path = old_path.parent / new_name
    if new_name in registry:
        return False, f"Venv '{new_name}' already exists in registry"
    if new_path.exists():
        return False, f"Directory '{new_path}' already exists"

    disk_moved = False
    try:
        # Move the folder on disk if it exists
        if old_path.exists():
            new_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(old_path), str(new_path))
            disk_moved = True
            _fix_venv_paths(new_path, old_path)

        # Update registry
        if old_name in registry:
            entry = registry.pop(old_name)
            entry["path"] = str(new_path)
            registry[new_name] = entry
        else:
            # Unregistered venv on disk, create a registry entry
            registry[new_name] = {
                "path": str(new_path),
                "python_version": "unknown",
            }

        try:
            save_venv_registry(registry)
        except OSError as e:
            # Rollback disk rename
            if disk_moved:
                shutil.move(str(new_path), str(old_path))
                _fix_venv_paths(old_path, new_path)
            return False, f"Failed to save registry, rename rolled back: {e}"

        return True, f"Renamed venv '{old_name}' to '{new_name}'"

    except OSError as e:
        return False, f"Failed to rename venv: {e}"


def duplicate_venv(source_name: str, new_name: str) -> tuple[bool, str]:
    """Duplicate a virtual environment by copying it to a new name.

    Copies the venv folder on disk, fixes internal paths, and registers
    the new venv in the JSON registry.

    Args:
        source_name: Name of the existing venv to copy.
        new_name: Name for the new copy.

    Returns:
        Tuple of (success, message).
    """
    registry = get_venv_registry()

    # Resolve source path
    if source_name in registry:
        source_path = Path(registry[source_name].get("path", ""))
    else:
        source_path = get_venv_dir() / source_name

    # Validate source exists on disk
    if not source_path.exists():
        return False, f"Venv '{source_name}' not found on disk"

    # Validate new name is not taken
    new_path = get_venv_dir() / new_name
    if new_name in registry:
        return False, f"Venv '{new_name}' already exists in registry"
    if new_path.exists():
        return False, f"Directory '{new_path}' already exists"

    try:
        # Copy the entire venv directory
        new_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(str(source_path), str(new_path))

        # Fix hardcoded paths in the copy
        _fix_venv_paths(new_path, source_path)

        # Register the new venv
        if source_name in registry:
            entry = dict(registry[source_name])
        else:
            entry = {"python_version": "unknown"}
        entry["path"] = str(new_path)
        registry[new_name] = entry
        save_venv_registry(registry)

        return True, f"Duplicated venv '{source_name}' as '{new_name}'"

    except OSError as e:
        # Clean up partial copy if it exists
        if new_path.exists():
            shutil.rmtree(new_path, ignore_errors=True)
        return False, f"Failed to duplicate venv: {e}"


def get_venv_activate_command(name: str) -> str | None:
    """Get the command to activate a venv.

    Args:
        name: Name of the venv.

    Returns:
        Activation command string, or None if venv not found.
    """
    registry = get_venv_registry()
    os_name, _ = get_os_info()

    if name in registry:
        venv_path = Path(registry[name].get("path", ""))
    else:
        venv_path = get_venv_dir() / name

    if not venv_path.exists():
        return None

    if os_name == "windows":
        activate_script = venv_path / "Scripts" / "activate.bat"
        if activate_script.exists():
            return str(activate_script)
    else:
        activate_script = venv_path / "bin" / "activate"
        if activate_script.exists():
            return f"source {activate_script}"

    return None


def get_venv_path(name: str) -> str | None:
    """Get the path of a virtual environment.

    Args:
        name: Name of the venv.

    Returns:
        Path string, or None if venv not found.
    """
    registry = get_venv_registry()

    if name in registry:
        venv_path = Path(registry[name].get("path", ""))
    else:
        venv_path = get_venv_dir() / name

    if not venv_path.exists():
        return None

    return str(venv_path)
