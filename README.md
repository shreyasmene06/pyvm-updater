# Python Version Manager (pyvm)

A cross-platform CLI tool with an interactive TUI to check and install Python versions side-by-side with your existing installation.

## Overview

pyvm provides a safe and convenient way to manage multiple Python versions on your system. It installs new versions alongside your existing Python without modifying system defaults, ensuring your system tools remain functional.

**Documentation**: [Installation Guide](docs/INSTALL.md) | [Quick Start](docs/QUICKSTART.md) | [Quick Reference](docs/QUICK_REFERENCE.md)

## Features

### Interactive TUI

<img width="1914" height="1039" alt="image" src="https://github.com/user-attachments/assets/6ffc278a-752b-468b-8a57-fff4d2936677" />

- Terminal interface with keyboard and mouse support
- Three-panel layout showing installed versions, available releases, and status
- Keyboard navigation with Tab, arrows, and shortcuts
- Live installation progress updates
- Theme switching between dark and light modes

### CLI Features

- Check current Python version against latest stable release
- Install the latest Python or specific versions side-by-side
- List all available Python versions with support status
- Interactive progress spinners for network operations
- Cross-platform support for Windows, Linux, and macOS
- Virtual environment management
- Configuration system for user preferences

### Safety

- Never modifies system Python defaults
- SHA256 checksum verification for all downloads
- Smart installation using mise, pyenv, conda, or system package managers
- Plugin system for custom installers (see [Plugins](#plugin-system))
- Rollback support to undo installations
- Multiple Python versions coexist without conflicts

## Plugin System

pyvm supports custom installation backends through a plugin system. You can add your own installers by placing Python files in `~/.config/pyvm/plugins/`.

### Security Note

> [!WARNING]
> **Custom plugins are executed as arbitrary Python code.** Only install plugins from trusted sources. pyvm will load and execute any `.py` file found in the plugins directory during startup.

## Installation

### From PyPI (Recommended)

```bash
pip install --user pyvm-updater
```

### From GitHub

```bash
git clone https://github.com/shreyasmene06/pyvm-updater.git
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

### Shell Completion

Enable tab completion for your shell:

#### Bash

Add this to `~/.bashrc`:

```bash
eval "$(_PYVM_COMPLETE=bash_source pyvm)"
```

#### Zsh

Add this to `~/.zshrc`:

```bash
eval "$(_PYVM_COMPLETE=zsh_source pyvm)"
```

#### Fish

Add this to `~/.config/fish/config.fish`:

```fish
_PYVM_COMPLETE=fish_source pyvm | source
```

### Interactive TUI Mode

```bash
pyvm tui
```

Keyboard Shortcuts:

| Key | Action |
|-----|--------|
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
|---------|-------------|
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

#### Linux/macOS

```bash
# Use the new version
python3.12 your_script.py

# Create a virtual environment
python3.12 -m venv myproject
source myproject/bin/activate
```

#### Windows

```bash
# Use Python Launcher
py -3.12 your_script.py

# List installed versions
py --list
```

## How It Works

pyvm uses an intelligent fallback chain for installation:

#### Linux

1. mise (if available)
2. pyenv (if available)
3. apt with deadsnakes PPA (Ubuntu/Debian)
4. dnf/yum (Fedora/RHEL)

#### macOS

1. mise (if available)
2. pyenv (if available)
3. Homebrew

#### Windows

- Downloads official installer from python.org

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

## Data Locations (XDG Compliance)

`pyvm` stores configuration, data, and cache files following the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html) on Linux/macOS, and standard `LocalAppData` locations on Windows.

**Linux / macOS:**
- **Config:** `~/.config/pyvm/` (`$XDG_CONFIG_HOME`)
- **Data (Venvs/History):** `~/.local/share/pyvm/` (`$XDG_DATA_HOME`)
- **Cache (Metadata):** `~/.cache/pyvm/` (`$XDG_CACHE_HOME`)

**Windows:**
- **Config / Data / Cache:** `%LOCALAPPDATA%\pyvm\`

### Automatic Migration for Existing Users
If you are upgrading from an older version of `pyvm` that used legacy paths (e.g., `~/.pyvm`, `~/.pyvm_history.json`), the tool will **automatically migrate** your files and virtual environments to the new locations the next time you run any `pyvm` command.

* **Logs:** If you run into issues, check your terminal output. Failed partial migrations will be retried automatically on subsequent runs until successful.

## Requirements

- Python 3.9 or higher
- Internet connection
- Admin/sudo privileges for some package manager operations

## Dependencies

Automatically installed:

- requests
- beautifulsoup4
- packaging
- click
- textual

## Troubleshooting

### "externally-managed-environment" Error

Use one of these solutions:

```bash
# Option 1: User install
pip install --user pyvm-updater

# Option 2: Use pipx
pipx install pyvm-updater

# Option 3: Use virtual environment
python3 -m venv venv && source venv/bin/activate
pip install pyvm-updater
```

### "pyvm: command not found"

Add the installation directory to your PATH:

```bash
# For pip install --user
export PATH="$HOME/.local/bin:$PATH"

# For pipx
pipx ensurepath
```

### "Already installed but shows old version"

The new Python is installed alongside your existing version. Use the specific version command:

```bash
python3.12 --version    # Linux/macOS
py -3.12 --version      # Windows
```

### Permission Denied Errors

- **Cause:** The script lacks execute permissions or is trying to write to a protected folder.
- **Fix:**
  - Run the command with `sudo` (Linux/Mac) or as Administrator (Windows).
  - Ensure the script is executable: `chmod +x pyvm-updater`.

### Firewall/Antivirus Blocking

- **Cause:** Security software might flag the updater as suspicious because it modifies system files.
- **Fix:** Whitelist `pyvm-updater` in your antivirus settings or temporarily disable the firewall during the update process.

## 🆚 Comparison with other tools

| Feature | pyvm | pyenv | asdf |
|---------|------|-------|------|
| **Scope** | Python only | Python only | Multi-language |
| **Complexity** | Low (Single script) | High (Shims, builds) | High (Plugins) |
| **OS Support** | Cross-platform | Unix-focused | Unix-focused |
| **Use Case** | Quick updates & lightweight management | Deep version management | Universal dev environments |

## 📖 API Documentation

Developers can use `pyvm-updater` as a Python library to manage installations programmatically.

### Installation Functions

The module provides platform-specific functions to install Python versions.

```python
from pyvm_updater import installers

# Windows: Downloads and runs the official installer
success = installers.update_python_windows("3.12.1")

# Linux: Tries mise, pyenv, then system package managers (apt/dnf)
success = installers.update_python_linux("3.12.1", build_from_source=False)

# macOS: Tries mise, pyenv, brew, then official installer
success = installers.update_python_macos("3.12.1")
```

## Development

```bash
# Clone and install in development mode
git clone https://github.com/shreyasmene06/pyvm-updater.git
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
|------|---------|
| 0 | Success or up-to-date |
| 1 | Update available or error |
| 130 | Operation cancelled by user |

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License. See [LICENSE](LICENSE) for details.

## Author

Shreyas Mene

## Contributors

<!-- CONTRIBUTORS_START -->
<a href="https://github.com/Build-with-Akshit"><img src="https://github.com/Build-with-Akshit.png" width="50px" loading="lazy" title="Build-with-Akshit" style="border-radius:50%;margin:5px;" alt="Build-with-Akshit" /></a><a href="https://github.com/Nidzz07"><img src="https://github.com/Nidzz07.png" width="50px" loading="lazy" title="Nidzz07" style="border-radius:50%;margin:5px;" alt="Nidzz07" /></a><a href="https://github.com/ParthG2209"><img src="https://github.com/ParthG2209.png" width="50px" loading="lazy" title="ParthG2209" style="border-radius:50%;margin:5px;" alt="ParthG2209" /></a><a href="https://github.com/Pikolosan"><img src="https://github.com/Pikolosan.png" width="50px" loading="lazy" title="Pikolosan" style="border-radius:50%;margin:5px;" alt="Pikolosan" /></a><a href="https://github.com/RahilHalai7"><img src="https://github.com/RahilHalai7.png" width="50px" loading="lazy" title="RahilHalai7" style="border-radius:50%;margin:5px;" alt="RahilHalai7" /></a><a href="https://github.com/ShaikhWarsi"><img src="https://github.com/ShaikhWarsi.png" width="50px" loading="lazy" title="ShaikhWarsi" style="border-radius:50%;margin:5px;" alt="ShaikhWarsi" /></a><a href="https://github.com/Sivanesan-R"><img src="https://github.com/Sivanesan-R.png" width="50px" loading="lazy" title="Sivanesan-R" style="border-radius:50%;margin:5px;" alt="Sivanesan-R" /></a><a href="https://github.com/Sumit0919"><img src="https://github.com/Sumit0919.png" width="50px" loading="lazy" title="Sumit0919" style="border-radius:50%;margin:5px;" alt="Sumit0919" /></a><a href="https://github.com/Ved178"><img src="https://github.com/Ved178.png" width="50px" loading="lazy" title="Ved178" style="border-radius:50%;margin:5px;" alt="Ved178" /></a><a href="https://github.com/advay-demo"><img src="https://github.com/advay-demo.png" width="50px" loading="lazy" title="advay-demo" style="border-radius:50%;margin:5px;" alt="advay-demo" /></a><a href="https://github.com/ashmeet-chhabra"><img src="https://github.com/ashmeet-chhabra.png" width="50px" loading="lazy" title="ashmeet-chhabra" style="border-radius:50%;margin:5px;" alt="ashmeet-chhabra" /></a><a href="https://github.com/davideciaccio"><img src="https://github.com/davideciaccio.png" width="50px" loading="lazy" title="davideciaccio" style="border-radius:50%;margin:5px;" alt="davideciaccio" /></a><a href="https://github.com/fgrabowski"><img src="https://github.com/fgrabowski.png" width="50px" loading="lazy" title="fgrabowski" style="border-radius:50%;margin:5px;" alt="fgrabowski" /></a><a href="https://github.com/ghost"><img src="https://github.com/ghost.png" width="50px" loading="lazy" title="ghost" style="border-radius:50%;margin:5px;" alt="ghost" /></a><a href="https://github.com/guitolino"><img src="https://github.com/guitolino.png" width="50px" loading="lazy" title="guitolino" style="border-radius:50%;margin:5px;" alt="guitolino" /></a><a href="https://github.com/itsdakshjain"><img src="https://github.com/itsdakshjain.png" width="50px" loading="lazy" title="itsdakshjain" style="border-radius:50%;margin:5px;" alt="itsdakshjain" /></a><a href="https://github.com/kush-mehra1"><img src="https://github.com/kush-mehra1.png" width="50px" loading="lazy" title="kush-mehra1" style="border-radius:50%;margin:5px;" alt="kush-mehra1" /></a><a href="https://github.com/lamiyacodes"><img src="https://github.com/lamiyacodes.png" width="50px" loading="lazy" title="lamiyacodes" style="border-radius:50%;margin:5px;" alt="lamiyacodes" /></a><a href="https://github.com/saksham-stack"><img src="https://github.com/saksham-stack.png" width="50px" loading="lazy" title="saksham-stack" style="border-radius:50%;margin:5px;" alt="saksham-stack" /></a><a href="https://github.com/shauryavardhan1307"><img src="https://github.com/shauryavardhan1307.png" width="50px" loading="lazy" title="shauryavardhan1307" style="border-radius:50%;margin:5px;" alt="shauryavardhan1307" /></a><a href="https://github.com/shreyasmene06"><img src="https://github.com/shreyasmene06.png" width="50px" loading="lazy" title="shreyasmene06" style="border-radius:50%;margin:5px;" alt="shreyasmene06" /></a><a href="https://github.com/swarnimbandekar"><img src="https://github.com/swarnimbandekar.png" width="50px" loading="lazy" title="swarnimbandekar" style="border-radius:50%;margin:5px;" alt="swarnimbandekar" /></a><a href="https://github.com/vishaal2002"><img src="https://github.com/vishaal2002.png" width="50px" loading="lazy" title="vishaal2002" style="border-radius:50%;margin:5px;" alt="vishaal2002" /></a><a href="https://github.com/yashstack-bot"><img src="https://github.com/yashstack-bot.png" width="50px" loading="lazy" title="yashstack-bot" style="border-radius:50%;margin:5px;" alt="yashstack-bot" /></a>
<!-- CONTRIBUTORS_END -->

## Disclaimer

This tool downloads and installs software from python.org. Always verify the authenticity of downloaded files. The authors are not responsible for any issues arising from Python installations.
