"""CLI commands for pyvm_updater."""

from __future__ import annotations

import json
import platform
import subprocess
import sys

import click

from . import __version__
from .config import Config, get_config
from .constants import HISTORY_FILE
from .history import HistoryManager
from .installers import (
    remove_python_linux,
    remove_python_macos,
    remove_python_windows,
    show_python_usage_instructions,
    update_python_linux,
    update_python_macos,
    update_python_windows,
)
from .logging_config import get_logger, setup_logging
from .utils import get_os_info, is_admin, validate_version_string
from .version import (
    check_python_version,
    get_active_python_releases,
    get_available_python_versions,
    get_latest_python_info_with_retry,
)

# Module logger
log = get_logger("cli")


@click.group(invoke_without_command=True)
@click.pass_context
@click.option("--version", "-v", is_flag=True, help="Show tool version")
@click.option("--verbose", "-V", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-essential output")
def cli(ctx: click.Context, version: bool, verbose: bool, quiet: bool) -> None:
    """Python Version Manager - Check and install Python (does NOT modify system defaults)"""
    # Initialize logging
    setup_logging(verbose=verbose, quiet=quiet)

    # Store config in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["config"] = get_config()
    ctx.obj["verbose"] = verbose

    if version:
        click.echo(f"Python Version Manager v{__version__}")
        ctx.exit()

    if ctx.invoked_subcommand is None:
        ctx.invoke(check)


@cli.command()
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def rollback(yes: bool) -> None:
    """Rollback to the previous Python version state."""
    try:
        last_action = HistoryManager.get_last_action()
        if not last_action:
            click.echo("No rollback history found.")
            sys.exit(0)

        version = last_action["version"]
        action = last_action["action"]
        prev_version = last_action.get("previous_version", "unknown")

        click.echo(f"Last action: {action} Python {version}")
        click.echo(f"Previous version was: {prev_version}")

        if not yes:
            if not click.confirm(f"\nDo you want to rollback by removing Python {version}?"):
                click.echo("Rollback cancelled.")
                sys.exit(0)

        os_name, _ = get_os_info()
        success = False
        if os_name == "windows":
            success = remove_python_windows(version)
        elif os_name == "linux":
            success = remove_python_linux(version)
        elif os_name == "darwin":
            success = remove_python_macos(version)
        else:
            click.echo(f"Unsupported operating system: {os_name}")
            sys.exit(1)

        if success:
            click.echo(f"\nSuccessfully rolled back: Python {version} removed.")
            history = HistoryManager.get_history()
            if history:
                history.pop()
                try:
                    with open(HISTORY_FILE, "w") as f:
                        json.dump(history, f, indent=2)
                except Exception:
                    pass
        else:
            click.echo("\nRollback encountered issues.")
            sys.exit(1)

    except KeyboardInterrupt:
        click.echo("\n\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        click.echo(f"\nError: {e}")
        sys.exit(1)


@cli.command()
def check() -> None:
    """Check current Python version against latest stable release."""
    try:
        _local_ver, _latest_ver, needs_update = check_python_version(silent=False)

        if needs_update:
            click.echo("\n💡 Tip: Run 'pyvm update' to upgrade Python")
            sys.exit(1)
        else:
            sys.exit(0)

    except KeyboardInterrupt:
        click.echo("\n\nOperation cancelled by user.")
        sys.exit(130)


@cli.command()
@click.argument("version")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def install(version: str, yes: bool) -> None:
    """Install a specific Python version.

    Examples:
        pyvm install 3.12.1
        pyvm install 3.11.5 --yes
    """
    try:
        if not validate_version_string(version) or len(version.split(".")) < 3:
            click.echo(f"Error: Invalid version format: {version}")
            click.echo("Version must be in format: X.Y.Z (e.g., 3.12.1)")
            sys.exit(1)

        local_ver = platform.python_version()
        click.echo(f"Current Python: {local_ver}")
        click.echo(f"Target version: {version}")

        if local_ver == version:
            click.echo(f"\nPython {version} is already your current version.")
            sys.exit(0)

        os_name, arch = get_os_info()
        click.echo(f"System: {os_name.title()} ({arch})")

        if not yes:
            if not click.confirm(f"\nInstall Python {version}?"):
                click.echo("Installation cancelled.")
                sys.exit(0)

        click.echo(f"\nInstalling Python {version}...")

        success = False
        if os_name == "windows":
            success = update_python_windows(version)
        elif os_name == "linux":
            success = update_python_linux(version)
        elif os_name == "darwin":
            success = update_python_macos(version)
        else:
            click.echo(f"Unsupported operating system: {os_name}")
            sys.exit(1)

        if success:
            HistoryManager.save_history("install", version)
            show_python_usage_instructions(version, os_name)
        else:
            click.echo("\nInstallation encountered issues. Check messages above.")
            sys.exit(1)

    except KeyboardInterrupt:
        click.echo("\n\nOperation cancelled.")
        sys.exit(130)
    except Exception as e:
        click.echo(f"\nError: {e}")
        sys.exit(1)


@cli.command()
@click.argument("version")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def remove(version: str, yes: bool) -> None:
    """Remove a specific Python version."""
    try:
        if not validate_version_string(version):
            click.echo(f"Error: Invalid version format: {version}")
            sys.exit(1)

        os_name, _ = get_os_info()

        if not yes:
            if not click.confirm(f"\nAre you sure you want to remove Python {version}?"):
                click.echo("Removal cancelled.")
                sys.exit(0)

        success = False
        if os_name == "windows":
            success = remove_python_windows(version)
        elif os_name == "linux":
            success = remove_python_linux(version)
        elif os_name == "darwin":
            success = remove_python_macos(version)
        else:
            click.echo(f"Unsupported operating system: {os_name}")
            sys.exit(1)

        if success:
            HistoryManager.save_history("remove", version)
            click.echo(f"\nSuccessfully removed Python {version}")
        else:
            click.echo("\nRemoval encountered issues. Check messages above.")
            sys.exit(1)

    except KeyboardInterrupt:
        click.echo("\n\nOperation cancelled.")
        sys.exit(130)
    except Exception as e:
        click.echo(f"\nError: {e}")
        sys.exit(1)


@cli.command("list")
@click.option("--all", "-a", "show_all", is_flag=True, help="Show all versions including patch releases")
def list_versions(show_all: bool) -> None:
    """List available Python versions."""
    try:
        click.echo("Fetching Python versions...\n")

        local_ver = platform.python_version()
        local_series = ".".join(local_ver.split(".")[:2])

        if show_all:
            versions = get_available_python_versions(limit=100)
            if not versions:
                click.echo("Could not fetch available versions.")
                sys.exit(1)

            latest_ver, _ = get_latest_python_info_with_retry()

            click.echo(f"{'VERSION':<12} {'STATUS'}")
            click.echo("-" * 40)

            for v in versions:
                ver = v["version"]
                status = ""
                if ver == local_ver:
                    status = "(installed)"
                elif latest_ver and ver == latest_ver:
                    status = "(latest)"
                click.echo(f"{ver:<12} {status}")
        else:
            releases = get_active_python_releases()
            if not releases:
                click.echo("Could not fetch active releases.")
                sys.exit(1)

            click.echo(f"{'SERIES':<10} {'LATEST':<12} {'STATUS':<15} {'SUPPORT UNTIL'}")
            click.echo("-" * 55)

            for rel in releases:
                series = rel["series"]
                latest = rel.get("latest_version") or "-"
                status = rel.get("status", "")
                end_support = rel.get("end_of_support", "")

                marker = ""
                if series == local_series:
                    marker = " *"

                if "pre-release" in status.lower():
                    status_display = "pre-release"
                elif "bugfix" in status.lower():
                    status_display = "bugfix"
                elif "security" in status.lower():
                    status_display = "security"
                elif "end of life" in status.lower():
                    status_display = "end-of-life"
                else:
                    status_display = status

                click.echo(f"{series:<10} {latest:<12} {status_display:<15} {end_support}{marker}")

            click.echo(f"\n * = your installed version ({local_ver})")
            click.echo("\nUse 'pyvm list --all' to see all patch versions")

        click.echo("Install with: pyvm install <version>")

    except KeyboardInterrupt:
        click.echo("\n\nOperation cancelled.")
        sys.exit(130)
    except Exception as e:
        click.echo(f"Error: {e}")
        sys.exit(1)

  
@cli.command()
@click.option("--auto", is_flag=True, help="Automatically proceed without confirmation")
@click.option("--version", "target_version", default=None, help="Specify a target Python version (e.g., 3.11.5)")
@click.option("--build-from-source", is_flag=True, help="Compile Python from source (Linux only)")
def update(auto: bool, target_version: str | None, build_from_source: bool) -> None:
    """Download and install Python version (does NOT modify system defaults).""" 
    try:
        local_ver = platform.python_version()
        install_version = None

        if target_version:
            if not validate_version_string(target_version) or len(target_version.split(".")) < 3:
                click.echo(f"❌ Error: Invalid version format: {target_version}")
                click.echo("Version must be in format: X.Y.Z (e.g., 3.11.5)")
                sys.exit(1)

            install_version = target_version
            click.echo(f"📌 Target version specified: {install_version}")
            click.echo(f"📊 Current version: {local_ver}")
        else:
            click.echo("🔍 Checking for updates...")
            local_ver, latest_ver, needs_update = check_python_version(silent=True)

            if not latest_ver:
                click.echo("❌ Could not fetch latest version information.")
                sys.exit(1)

            click.echo(f"\n📊 Current version: {local_ver}")
            click.echo(f"📊 Latest version:  {latest_ver}")

            if not needs_update:
                click.echo("\n✅ You already have the latest version!")
                sys.exit(0)

            click.echo(f"\n🚀 Update available: {local_ver} → {latest_ver}")
            install_version = latest_ver

        if not auto:
            if not click.confirm(f"\nDo you want to proceed with installing Python {install_version}?"):
                click.echo("Installation cancelled.")
                sys.exit(0)

        os_name, arch = get_os_info()
        click.echo(f"\n🖥️  Detected: {os_name.title()} ({arch})")

        success = False
        if os_name == "windows":
            success = update_python_windows(install_version)
        elif os_name == "linux":
            # We are now passing the build_from_source variable here
            success = update_python_linux(install_version, build_from_source)
        elif os_name == "darwin":
            success = update_python_macos(install_version)
        else:
            click.echo(f"❌ Unsupported operating system: {os_name}")
            sys.exit(1)

        if success:
            HistoryManager.save_history("update", install_version)
            show_python_usage_instructions(install_version, os_name)
        else:
            click.echo("\n⚠️  Installation process encountered issues.")
            sys.exit(1)

    except KeyboardInterrupt:
        click.echo("\n\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        click.echo(f"\n❌ Error: {e}")
        sys.exit(1)


@cli.command()
def tui() -> None:
    """Launch the interactive TUI interface."""
    try:
        from .tui import run_tui

        run_tui()
    except ImportError:
        click.echo("❌ TUI mode requires the 'textual' package.")
        click.echo("Install it with: pip install pyvm-updater[tui]")
        click.echo("Or: pip install textual")
        sys.exit(1)


@cli.command()
def info() -> None:
    """Show detailed system and Python information."""
    try:
        click.echo("=" * 50)
        click.echo("           System Information")
        click.echo("=" * 50)

        os_name, arch = get_os_info()
        click.echo(f"Operating System: {os_name.title()}")
        click.echo(f"Architecture:     {arch}")
        click.echo(f"Python Version:   {platform.python_version()}")
        click.echo(f"Python Path:      {sys.executable}")
        click.echo(f"Platform:         {platform.platform()}")
        click.echo(f"\nAdmin/Sudo:       {'Yes' if is_admin() else 'No'}")

        try:
            result = subprocess.run(["which", "python3"], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                python3_path = result.stdout.strip()
                if python3_path != sys.executable:
                    click.echo(f"python3 command:  {python3_path}")
        except Exception:
            pass

        click.echo("=" * 50)

    except Exception as e:
        click.echo(f"Error: {e}")
        sys.exit(1)


@cli.command()
@click.option("--show", is_flag=True, help="Show current configuration")
@click.option("--init", "init_config", is_flag=True, help="Create default config file")
@click.option("--path", is_flag=True, help="Show config file path")
def config(show: bool, init_config: bool, path: bool) -> None:
    """View or manage pyvm configuration."""
    from .config import CONFIG_FILE

    if path:
        click.echo(f"Config file: {CONFIG_FILE}")
        if CONFIG_FILE.exists():
            click.echo("Status: exists")
        else:
            click.echo("Status: not created (using defaults)")
        return

    if init_config:
        if CONFIG_FILE.exists():
            click.echo(f"Config file already exists: {CONFIG_FILE}")
            return

        cfg = Config()
        if cfg.save():
            click.echo(f"Created config file: {CONFIG_FILE}")
        else:
            click.echo("Failed to create config file.")
            sys.exit(1)
        return

    # Default: show current config
    cfg = get_config()
    click.echo("Current Configuration:")
    click.echo("-" * 40)
    click.echo(f"Auto-confirm:       {cfg.auto_confirm}")
    click.echo(f"Verbose:            {cfg.verbose}")
    click.echo(f"Preferred installer: {cfg.preferred_installer}")
    click.echo(f"Verify checksum:    {cfg.verify_checksum}")
    click.echo(f"Max retries:        {cfg.max_retries}")
    click.echo(f"Download timeout:   {cfg.download_timeout}s")
    click.echo(f"TUI theme:          {cfg.tui_theme}")
    click.echo("-" * 40)
    click.echo(f"\nConfig file: {CONFIG_FILE}")
    if not CONFIG_FILE.exists():
        click.echo("(Using defaults. Run 'pyvm config --init' to create config file.)")


# Venv subcommand group
@cli.group()
def venv() -> None:
    """Manage virtual environments."""
    pass


@venv.command("create")
@click.argument("name")
@click.option("--python", "-p", "python_version", help="Python version to use (e.g., 3.12)")
@click.option("--path", type=click.Path(), help="Custom path for the venv")
@click.option("--system-site-packages", is_flag=True, help="Include system site-packages")
def venv_create(name: str, python_version: str | None, path: str | None, system_site_packages: bool) -> None:
    """Create a new virtual environment.

    Examples:
        pyvm venv create myproject
        pyvm venv create myproject --python 3.12
        pyvm venv create myproject --path ./venv
    """
    from pathlib import Path as PathLib

    from .venv import create_venv

    venv_path = PathLib(path) if path else None

    click.echo(f"Creating venv '{name}'...")
    if python_version:
        click.echo(f"Using Python {python_version}")

    success, message = create_venv(
        name=name,
        python_version=python_version,
        path=venv_path,
        system_site_packages=system_site_packages,
    )

    if success:
        click.echo(f"✅ {message}")

        # Show activation command
        from .venv import get_venv_activate_command

        activate_cmd = get_venv_activate_command(name)
        if activate_cmd:
            click.echo(f"\n💡 To activate: {activate_cmd}")
    else:
        click.echo(f"❌ {message}")
        sys.exit(1)


@venv.command("list")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def venv_list(as_json: bool) -> None:
    """List all virtual environments."""
    import json as json_module

    from .venv import list_venvs

    venvs = list_venvs()

    if not venvs:
        if as_json:
            click.echo("[]")
        else:
            click.echo("No virtual environments found.")
            click.echo("\nCreate one with: pyvm venv create <name>")
        return

    if as_json:
        click.echo(json_module.dumps(venvs, indent=2))
    else:
        click.echo(f"{'NAME':<20} {'PYTHON':<10} {'STATUS':<10} PATH")
        click.echo("-" * 70)
        for v in venvs:
            status = "✓" if v["exists"] else "✗ missing"
            click.echo(f"{v['name']:<20} {v['python_version']:<10} {status:<10} {v['path']}")
        click.echo(f"\nTotal: {len(venvs)} venv(s)")


@venv.command("remove")
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def venv_remove(name: str, yes: bool) -> None:
    """Remove a virtual environment."""
    from .venv import get_venv_registry, remove_venv

    registry = get_venv_registry()

    if name not in registry:
        from .venv import get_venv_dir

        venv_path = get_venv_dir() / name
        if not venv_path.exists():
            click.echo(f"❌ Venv '{name}' not found.")
            sys.exit(1)

    if not yes:
        if not click.confirm(f"Remove venv '{name}'?"):
            click.echo("Cancelled.")
            return

    success, message = remove_venv(name)

    if success:
        click.echo(f"✅ {message}")
    else:
        click.echo(f"❌ {message}")
        sys.exit(1)


@venv.command("activate")
@click.argument("name")
def venv_activate(name: str) -> None:
    """Show how to activate a virtual environment."""
    from .venv import get_venv_activate_command

    activate_cmd = get_venv_activate_command(name)

    if activate_cmd:
        click.echo(f"To activate '{name}':")
        click.echo(f"\n  {activate_cmd}\n")
    else:
        click.echo(f"❌ Venv '{name}' not found.")
        sys.exit(1)


def main() -> None:
    """Main entry point for the script."""
    try:
        cli()
    except Exception as e:
        click.echo(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
