# Quick Start Guide

Get started with pyvm in minutes.

## Installation

### Linux/macOS

```bash
pip install --user pyvm-updater
```

### Windows

```bash
pip install pyvm-updater
```

### Verify Installation

```bash
pyvm --version
```

If the command is not found, add `~/.local/bin` to your PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Basic Usage

### Check Your Python Version

```bash
pyvm check
```

Output:
```
Checking Python version... (Current: 3.12.3)

========================================
     Python Version Check Report
========================================
Your version:   3.12.3
Latest version: 3.14.0
========================================
A new version (3.14.0) is available!

Tip: Run 'pyvm update' to upgrade Python
```

### List Available Versions

```bash
pyvm list
```

Output:
```
SERIES     LATEST       STATUS          SUPPORT UNTIL
-------------------------------------------------------
3.14       3.14.2       bugfix          2030-10
3.13       3.13.11      bugfix          2029-10
3.12       3.12.12      security        2028-10
3.11       3.11.14      security        2027-10
3.10       3.10.19      security        2026-10
```

### Update to Latest Python

```bash
pyvm update
```

### Install a Specific Version

```bash
pyvm install 3.12.8
```

### Launch Interactive TUI

```bash
pyvm tui
```

## TUI Navigation

| Key | Action |
|-----|--------|
| Tab | Switch between panels |
| Arrow Keys | Navigate within panel |
| Enter | Install selected version |
| U | Update to latest |
| R | Refresh data |
| Q | Quit |

## Virtual Environment Management

### Create Environment

```bash
pyvm venv create myproject
```

### Create with Specific Python

```bash
pyvm venv create myproject --python 3.12
```

### List Environments

```bash
pyvm venv list
```

### Activate Environment

```bash
pyvm venv activate myproject
# Follow the printed instructions to activate
```

### Remove Environment

```bash
pyvm venv remove myproject
```

## Using Installed Python Versions

After installing a new Python version, it's available alongside your existing version.

### Linux/macOS

```bash
# Use new version directly
python3.12 your_script.py

# Create virtual environment with new version
python3.12 -m venv myproject
source myproject/bin/activate
```

### Windows

```bash
# Use Python Launcher
py -3.12 your_script.py

# List all versions
py --list

# Create virtual environment
py -3.12 -m venv myproject
myproject\Scripts\activate
```

## Common Commands

| Command | Description |
|---------|-------------|
| `pyvm check` | Check version status |
| `pyvm list` | List available versions |
| `pyvm install 3.12.8` | Install specific version |
| `pyvm update` | Update to latest |
| `pyvm update --auto` | Update without confirmation |
| `pyvm tui` | Launch interactive interface |
| `pyvm info` | Show system information |
| `pyvm rollback` | Undo last installation |
| `pyvm config` | View configuration |

## Configuration

View current configuration:

```bash
pyvm config
```

Create default configuration file:

```bash
pyvm config --init
```

Configuration location: `~/.config/pyvm/config.toml`

## Troubleshooting

### Command Not Found

Add to PATH:

```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"
source ~/.bashrc
```

### Permission Denied

Use user installation:

```bash
pip install --user pyvm-updater
```

### Missing Dependencies

Reinstall:

```bash
pip install --user --force-reinstall pyvm-updater
```

## Next Steps

- Explore `pyvm --help` for all available commands
- Try `pyvm tui` for an interactive experience
- See [INSTALL.md](INSTALL.md) for detailed installation options
- Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for command reference
