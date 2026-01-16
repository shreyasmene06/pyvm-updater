# Quick Reference

Command reference for pyvm version 2.2.0.

## CLI Commands

### Version Check

```bash
pyvm check
```

Check your current Python version against the latest stable release.

### List Versions

```bash
# Show active release series
pyvm list

# Show all versions including patches
pyvm list --all
```

### Install Python

```bash
# Install specific version
pyvm install 3.12.8

# Install without confirmation
pyvm install 3.12.8 -y
```

### Update Python

```bash
# Update to latest
pyvm update

# Update to specific version
pyvm update --version 3.12.0

# Update without confirmation
pyvm update --auto
```

### Remove Python

```bash
# Remove specific version
pyvm remove 3.11.5

# Remove without confirmation
pyvm remove 3.11.5 -y
```

### Rollback

```bash
# Undo last installation
pyvm rollback

# Rollback without confirmation
pyvm rollback -y
```

### System Information

```bash
pyvm info
```

### Configuration

```bash
# View configuration
pyvm config

# Create default config file
pyvm config --init

# Show config file path
pyvm config --path
```

### Virtual Environments

```bash
# Create environment
pyvm venv create myproject

# Create with specific Python
pyvm venv create myproject --python 3.12

# List environments
pyvm venv list

# Show activation command
pyvm venv activate myproject

# Remove environment
pyvm venv remove myproject
```

### Interactive TUI

```bash
pyvm tui
```

## TUI Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Tab | Next panel |
| Shift+Tab | Previous panel |
| Arrow Keys | Navigate in panel |
| Enter | Install selected version |
| 1 | Jump to Installed panel |
| 2 | Jump to Available panel |
| U | Update to latest Python |
| B | Rollback last installation |
| X | Remove selected version |
| R | Refresh data |
| T | Toggle theme |
| ? | Show help |
| Q | Quit |

## Global Options

```bash
# Show version
pyvm --version
pyvm -v

# Show help
pyvm --help

# Enable verbose output
pyvm --verbose check
pyvm -V check

# Suppress non-essential output
pyvm --quiet check
pyvm -q check
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success or up-to-date |
| 1 | Update available or error |
| 130 | Cancelled by user (Ctrl+C) |

## Configuration File

Location: `~/.config/pyvm/config.toml`

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

## Installation Priority

pyvm uses this order when installing Python:

Linux:
1. mise
2. pyenv
3. apt (Ubuntu/Debian with deadsnakes PPA)
4. dnf/yum (Fedora/RHEL)

macOS:
1. mise
2. pyenv
3. Homebrew

Windows:
- Official python.org installer

## Using Installed Versions

Linux/macOS:
```bash
python3.12 script.py
python3.12 -m venv myenv
```

Windows:
```bash
py -3.12 script.py
py --list
```

## Common Tasks

### Check if update available

```bash
pyvm check
# Exit code 0 = up-to-date
# Exit code 1 = update available
```

### Automated update in scripts

```bash
if ! pyvm check; then
    pyvm update --auto
fi
```

### Install and create venv

```bash
pyvm install 3.12.8
pyvm venv create myproject --python 3.12
```

## Files and Locations

| File | Purpose |
|------|---------|
| `~/.config/pyvm/config.toml` | User configuration |
| `~/.pyvm_history.json` | Installation history |
| `~/.local/share/pyvm/venvs/` | Managed virtual environments |

## Troubleshooting

### Command not found

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Permission denied

```bash
pip install --user pyvm-updater
```

### externally-managed-environment

```bash
pip install --user pyvm-updater
# or
pipx install pyvm-updater
```
