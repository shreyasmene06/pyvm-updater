"""Platform-specific Python installation logic for pyvm_updater."""

from __future__ import annotations

from typing import Any

import click

from .config import get_config
from .plugins.manager import get_plugin_manager


def update_python_windows(version_str: str, preferred: str = "auto", **kwargs: Any) -> bool:
    """Update Python on Windows."""
    return _install_with_plugins(version_str, preferred=preferred)


def update_python_linux(
    version_str: str, build_from_source: bool = False, preferred: str = "auto", **kwargs: Any
) -> bool:
    """Install Python on Linux."""
    if preferred == "auto" and build_from_source:
        preferred = "source"
    elif preferred == "auto":
        preferred = get_config().preferred_installer

    return _install_with_plugins(version_str, preferred=preferred, **kwargs)


def update_python_macos(version_str: str, preferred: str = "auto", **kwargs: Any) -> bool:
    """Update Python on macOS."""
    return _install_with_plugins(version_str, preferred=preferred, **kwargs)


def _install_with_plugins(version_str: str, preferred: str = "auto", **kwargs: Any) -> bool:
    """Generic installation logic using the plugin system."""
    pm = get_plugin_manager()

    installers_to_try = []

    if preferred != "auto":
        requested_installer = pm.get_plugin(preferred)
        if requested_installer and requested_installer.is_supported():
            # If explicitly requested and supported, only try that one
            installers_to_try = [requested_installer]
        else:
            # If requested is not supported, warn and fall back to all supported
            best = pm.get_best_installer()
            if best:
                click.echo(
                    f"⚠️  Requested installer '{preferred}' is not supported or not found. "
                    f"Falling back to '{best.get_name()}'."
                )
                installers_to_try = pm.get_supported_plugins()
    else:
        # Auto mode: try all supported in priority order
        installers_to_try = pm.get_supported_plugins()

    if not installers_to_try:
        click.echo("❌ No supported installer found for your system.")
        return False

    for idx, installer in enumerate(installers_to_try):
        if installer.install(version_str, **kwargs):
            return True

        if idx < len(installers_to_try) - 1:
            click.echo(f"⚠️  Installer '{installer.get_name()}' failed. Falling back to next available mechanism...")

    click.echo("❌ All available installation methods failed.")
    return False


def remove_python_windows(version_str: str) -> bool:
    """Remove Python on Windows."""
    return _uninstall_with_plugins(version_str)


def remove_python_linux(version_str: str) -> bool:
    """Remove Python on Linux."""
    return _uninstall_with_plugins(version_str)


def remove_python_macos(version_str: str) -> bool:
    """Remove Python on macOS."""
    return _uninstall_with_plugins(version_str)


def _uninstall_with_plugins(version_str: str) -> bool:
    """Generic uninstallation logic using the plugin system."""
    pm = get_plugin_manager()
    # Try all supported installers until one succeeds
    for installer in pm.get_supported_plugins():
        if installer.uninstall(version_str):
            click.echo(f"[OK] Python {version_str} uninstalled via {installer.get_name()}.")
            return True

    click.echo(f"❌ Could not find an automated way to remove Python {version_str}.")
    return False


def show_python_usage_instructions(version_str: str, os_name: str) -> None:
    """Show user how to use the newly installed Python version."""
    try:
        parts = version_str.split(".")
        major_minor = f"{parts[0]}.{parts[1]}"
    except (ValueError, IndexError):
        major_minor = version_str

    click.echo("\n" + "=" * 60)
    click.echo("✅ Installation Complete!")
    click.echo("=" * 60)
    click.echo(f"\n📌 Python {version_str} has been installed successfully!")
    click.echo("\n📚 How to use your new Python version:")
    click.echo("-" * 60)

    if os_name in ("linux", "darwin"):
        click.echo(f"\n1️⃣  Run scripts: python{major_minor} your_script.py")
        click.echo(f"\n2️⃣  Create venv: python{major_minor} -m venv myproject")
        click.echo(f"\n3️⃣  Check version: python{major_minor} --version")
    else:
        click.echo(f"\n1️⃣  Use launcher: py -{major_minor} your_script.py")
        click.echo("\n2️⃣  List versions: py --list")
        click.echo(f"\n3️⃣  Create venv: py -{major_minor} -m venv myproject")

    click.echo("-" * 60)
    click.echo("\n💡 Your old Python remains the system default.")
