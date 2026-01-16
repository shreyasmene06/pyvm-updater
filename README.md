Here is the updated `README.md` with the new sections (API Documentation, Comparison, and expanded Troubleshooting) integrated into the file.

```markdown
# Python Version Manager (pyvm)

A cross-platform CLI tool with an interactive TUI to check and install Python versions side-by-side with your existing installation.

## Overview

pyvm provides a safe and convenient way to manage multiple Python versions on your system. It installs new versions alongside your existing Python without modifying system defaults, ensuring your system tools remain functional.

**Documentation**: [Installation Guide](docs/INSTALL.md) | [Quick Start](docs/QUICKSTART.md) | [Quick Reference](docs/QUICK_REFERENCE.md)

## Features

### Interactive TUI

- Terminal interface with keyboard and mouse support
- Three-panel layout showing installed versions, available releases, and status
- Keyboard navigation with Tab, arrows, and shortcuts
- Live installation progress updates
- Theme switching between dark and light modes

### CLI Features

- Check current Python version against latest stable release
- Install the latest Python or specific versions side-by-side
- List all available Python versions with support status
- Cross-platform support for Windows, Linux, and macOS
- Virtual environment management
- Configuration system for user preferences

### Safety

- Never modifies system Python defaults
- SHA256 checksum verification for all downloads
- Smart installation using mise, pyenv, or system package managers
- Rollback support to undo installations
- Multiple Python versions coexist without conflicts

## Installation

### From PyPI (Recommended)

```bash
pip install --user pyvm-updater

```

### From GitHub

```bash
git clone [https://github.com/shreyasmene06/pyvm-updater.git](https://github.com/shreyasmene06/pyvm-updater.git)
cd pyvm-updater
pip install --user .

```

### Using pipx

```bash
pipx install pyvm-updater

```

**Note**: On newer Linux systems (Ubuntu 23.04+, Debian 12+), use the `--user` flag or pipx to avoid "externally-managed-environment" errors.

### Verify Installation

```bash
pyvm --version
pyvm check

```

## Quick Start

```bash
# Check your Python version
pyvm check

# Update to latest Python
pyvm update

# Launch interactive TUI
pyvm tui

# List available versions
pyvm list

# Install a specific version
pyvm install 3.12.8

```

## Usage

### Interactive TUI Mode

```bash
pyvm tui

```

Keyboard Shortcuts:

| Key | Action |
| --- | --- |
| Tab / Shift+Tab | Switch between panels |
| Arrow Keys | Navigate within panel |
| Enter | Install selected version |
| U | Update to latest Python |
| B | Rollback last installation |
| X | Remove selected version |
| R | Refresh data |
| T | Toggle theme |
| Q | Quit |

### CLI Commands

| Command | Description |
| --- | --- |
| `pyvm check` | Check Python version against latest |
| `pyvm list` | List available Python versions |
| `pyvm list --all` | Show all versions including patches |
| `pyvm install <version>` | Install specific Python version |
| `pyvm update` | Update to latest Python version |
| `pyvm update --version 3.12.0` | Update to specific version |
| `pyvm remove <version>` | Remove an installed version |
| `pyvm rollback` | Undo last installation |
| `pyvm venv create <name>` | Create virtual environment |
| `pyvm venv list` | List virtual environments |
| `pyvm config` | View configuration |
| `pyvm info` | Show system information |

### Virtual Environment Management

```bash
# Create a new virtual environment
pyvm venv create myproject

# Create with specific Python version
pyvm venv create myproject --python 3.12

# List all managed environments
pyvm venv list

# Show activation command
pyvm venv activate myproject

# Remove an environment
pyvm venv remove myproject

```

### Using Installed Python Versions

After installation, the new Python is available alongside your existing version:

Linux/macOS:

```bash
# Use the new version
python3.12 your_script.py

# Create a virtual environment
python3.12 -m venv myproject
source myproject/bin/activate

```

Windows:

```bash
# Use Python Launcher
py -3.12 your_script.py

# List installed versions
py --list

```

## How It Works

pyvm uses an intelligent fallback chain for installation:

Linux:

1. mise (if available)
2. pyenv (if available)
3. apt with deadsnakes PPA (Ubuntu/Debian)
4. dnf/yum (Fedora/RHEL)

macOS:

1. mise (if available)
2. pyenv (if available)
3. Homebrew

Windows:

* Downloads official installer from python.org

## Comparison with Other Tools

`pyvm` is designed to be a safe, user-friendly wrapper that works *with* existing tools rather than replacing them entirely.

| Feature | **pyvm** | **pyenv** | **mise** (rtx) | **asdf** |
| --- | --- | --- | --- | --- |
| **Primary Goal** | User-friendly, safe updates & TUI | Granular version switching | Fast, polyglot version manager | Polyglot version manager |
| **Windows Support** | ✅ **Native** (Official Installers) | ❌ (Requires pyenv-win fork) | ⚠️ (Experimental) | ❌ (WSL only) |
| **Interface** | CLI + **Interactive TUI** | CLI only | CLI only | CLI only |
| **System Safety** | **High** (Side-by-side only) | High (Shims) | High (Shims) | High (Shims) |
| **Installation Method** | **Intelligent Fallback** (Uses mise/pyenv/apt/brew) | Compiles from source | Compiles from source / Pre-built | Compiles from source |
| **Virtual Envs** | ✅ Built-in management | ❌ (Requires pyenv-virtualenv) | ❌ (Env vars only) | ❌ (Plugin required) |

### Why use pyvm?

1. **Cross-Platform Consistency:** `pyvm` offers the exact same commands and TUI experience on Windows, Linux, and macOS.
2. **Safety First:** Unlike some tools that manipulate your shell's PATH aggressively, `pyvm` prioritizes "side-by-side" installation. It never modifies your system python (`/usr/bin/python3`) symlinks.
3. **Visual Management:** The TUI allows you to visualize what versions are installed, which are end-of-life, and which have security updates available without parsing CLI output.
4. **Meta-Manager:** On Linux/macOS, `pyvm` actually detects if you have `mise` or `pyenv` installed and *uses them* to perform the installation. You get the power of those tools with the ease of use of `pyvm`.

## Configuration

Configuration is stored at `~/.config/pyvm/config.toml`:

```toml
[general]
auto_confirm = false
verbose = false
preferred_installer = "auto"

[download]
verify_checksum = true
max_retries = 3
timeout = 120

[tui]
theme = "dark"

```

Manage configuration:

```bash
pyvm config           # View current settings
pyvm config --init    # Create default config
pyvm config --path    # Show config file location

```

## Library Usage (API)

Developers can use `pyvm-updater` as a library to manage Python versions and virtual environments programmatically.

### Core Modules

**`pyvm_updater.version`**
Functions for checking, listing, and comparing Python versions.

* `check_python_version(silent: bool = False) -> tuple`
* `get_installed_python_versions() -> list[dict]`
* `get_active_python_releases() -> list[dict]`

**`pyvm_updater.venv`**
Functions to manage virtual environments safely.

* `create_venv(name: str, python_version: str | None, ...) -> tuple[bool, str]`
* `list_venvs() -> list[dict]`
* `get_venv_activate_command(name: str) -> str`

**`pyvm_updater.installers`**
Platform-specific installation logic.

* `update_python_windows(version_str: str) -> bool`
* `update_python_linux(version_str: str, ...) -> bool`

**`pyvm_updater.config`**

* `get_config()`: Returns the global `Config` object to read/write user preferences.

## Requirements

* Python 3.9 or higher
* Internet connection
* Admin/sudo privileges for some package manager operations

## Dependencies

Automatically installed:

* requests
* beautifulsoup4
* packaging
* click
* textual

## Troubleshooting

### "pyvm: command not found"

If the terminal says `command not found: pyvm` after installation:

1. **Linux/macOS:** Ensure `~/.local/bin` is in your PATH.
```bash
export PATH="$HOME/.local/bin:$PATH"

```


2. **Windows:** Ensure the Python Scripts directory is in your PATH (typically `%APPDATA%\Python\Python3XX\Scripts`).

### "externally-managed-environment" Error

On newer Linux systems (Ubuntu 23.04+, Debian 12+), you cannot install packages into the system Python globally.

* **Solution:** Use `pipx` for safe isolation:
```bash
sudo apt install pipx
pipx install pyvm-updater

```



### Permission Denied Errors

* **Installation:** If `pip install` fails, use the `--user` flag:
```bash
pip install --user pyvm-updater

```


* **Runtime:** If `pyvm` fails to install Python, ensure you have necessary privileges (sudo/admin). On Linux, `pyvm` may ask for sudo to run `apt` or `dnf`.

### Firewall & Network Issues

`pyvm` requires access to `python.org` to check versions and download installers.

* **SSL Errors:** Run `pip install --upgrade certifi` to update SSL certificates.
* **Proxies:** If you are behind a corporate proxy, set the standard environment variables (`HTTP_PROXY`, `HTTPS_PROXY`).

### TUI Display Issues

If the TUI looks broken or characters are missing:

* Ensure your terminal supports UTF-8.
* Verify your font supports standard box-drawing characters (e.g., Nerd Fonts).

### "Already installed but shows old version"

The new Python is installed alongside your existing version. Use the specific version command:

```bash
python3.12 --version    # Linux/macOS
py -3.12 --version      # Windows

```

## Development

```bash
# Clone and install in development mode
git clone [https://github.com/shreyasmene06/pyvm-updater.git](https://github.com/shreyasmene06/pyvm-updater.git)
cd pyvm-updater
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run linters
ruff check .
black --check .
mypy src/pyvm_updater

```

## Exit Codes

| Code | Meaning |
| --- | --- |
| 0 | Success or up-to-date |
| 1 | Update available or error |
| 130 | Operation cancelled by user |

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](https://www.google.com/search?q=CONTRIBUTING.md) for guidelines.

## License

MIT License. See [LICENSE](https://www.google.com/search?q=LICENSE) for details.

## Author

Shreyas Mene

## Disclaimer

This tool downloads and installs software from python.org. Always verify the authenticity of downloaded files. The authors are not responsible for any issues arising from Python installations.

```

```