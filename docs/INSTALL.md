# Installation Guide

This guide covers all installation methods for pyvm-updater.

## Requirements

- Python 3.9 or higher
- pip package manager
- Internet connection
- Admin/sudo privileges (for some installation methods)

## Quick Install

### From PyPI

```bash
pip install --user pyvm-updater
```

### From GitHub

```bash
git clone https://github.com/shreyasmene06/pyvm-updater.git
cd pyvm-updater
pip install --user .
```

## Installation Methods

### Method 1: pip with user flag (Recommended)

This installs the package in your user directory without requiring admin privileges.

```bash
pip install --user pyvm-updater
```

### Method 2: pipx (Best for CLI tools)

pipx installs Python applications in isolated environments.

```bash
# Install pipx if not already installed
sudo apt install pipx    # Ubuntu/Debian
brew install pipx        # macOS

# Install pyvm-updater
pipx install pyvm-updater

# Ensure PATH is configured
pipx ensurepath
```

### Method 3: Virtual Environment

```bash
# Create virtual environment
python3 -m venv pyvm-env
source pyvm-env/bin/activate

# Install
pip install pyvm-updater
```

### Method 4: System-wide (Requires admin)

```bash
sudo pip install pyvm-updater
```

### Method 5: Development Install

For contributors and developers:

```bash
git clone https://github.com/shreyasmene06/pyvm-updater.git
cd pyvm-updater
pip install -e ".[dev]"
```

## Pre-Installation Check

Run the requirements checker before installation:

```bash
python3 check_requirements.py
```

This verifies:
- Python version compatibility
- pip installation
- Internet connectivity
- Operating system support
- Installation permissions

## Platform-Specific Notes

### Linux (Ubuntu/Debian)

On Ubuntu 23.04+ and Debian 12+, the system Python is protected. Use one of these approaches:

```bash
# Option 1: User install
pip install --user pyvm-updater

# Option 2: Use pipx
sudo apt install pipx
pipx install pyvm-updater

# Option 3: Virtual environment
python3 -m venv ~/.local/pyvm-env
~/.local/pyvm-env/bin/pip install pyvm-updater
```

### Linux (Fedora/RHEL/CentOS)

```bash
pip install --user pyvm-updater
```

### macOS

```bash
pip3 install --user pyvm-updater
```

If you have Homebrew:

```bash
brew install pipx
pipx install pyvm-updater
```

### Windows

```bash
pip install pyvm-updater
```

If you encounter permission issues, try:

```bash
pip install --user pyvm-updater
```

## Verify Installation

After installation, verify pyvm is working:

```bash
# Check version
pyvm --version

# Check Python version
pyvm check

# Show help
pyvm --help
```

## PATH Configuration

If `pyvm` command is not found after installation, add the installation directory to your PATH.

### Linux/macOS

Add to `~/.bashrc` or `~/.zshrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Then reload:

```bash
source ~/.bashrc    # or source ~/.zshrc
```

### Windows

Add to PATH via System Properties:
1. Open System Properties > Advanced > Environment Variables
2. Under User variables, edit PATH
3. Add: `%APPDATA%\Python\Python3XX\Scripts`

## Updating pyvm

### From PyPI

```bash
pip install --upgrade pyvm-updater
```

### From GitHub

```bash
cd pyvm-updater
git pull
pip install --upgrade .
```

## Uninstallation

```bash
pip uninstall pyvm-updater
```

## Dependencies

The following packages are automatically installed:

| Package | Purpose |
|---------|---------|
| requests | HTTP requests for downloading |
| beautifulsoup4 | HTML parsing for python.org |
| packaging | Version comparison |
| click | CLI framework |
| textual | Terminal UI framework |

## Troubleshooting

### "externally-managed-environment" Error

This occurs on newer Linux systems. Solutions:

```bash
# Use user install
pip install --user pyvm-updater

# Or use pipx
pipx install pyvm-updater
```

### "Command not found" Error

The installation directory is not in PATH. See PATH Configuration section above.

### Permission Denied

Use `--user` flag or run with sudo:

```bash
pip install --user pyvm-updater
# or
sudo pip install pyvm-updater
```

### Import Errors

Reinstall with dependencies:

```bash
pip install --user --force-reinstall pyvm-updater
```

### Network/SSL Errors

Update pip and certificates:

```bash
pip install --upgrade pip certifi
```

## Anaconda/Miniconda Users

pyvm works with Anaconda but installs Python to the system, not your Anaconda environment.

```bash
# Install using pip (not conda)
pip install --user pyvm-updater
```

After updating Python with pyvm:

```bash
# Your Anaconda Python (unchanged)
python --version

# System Python updated by pyvm
python3.12 --version
```

To use the updated Python:

1. Use it directly: `python3.12 your_script.py`
2. Create a virtual environment: `python3.12 -m venv myenv`
3. Continue using Anaconda for your data science work

## Next Steps

After successful installation:

1. Run `pyvm check` to see your Python version status
2. Run `pyvm list` to see available Python versions
3. Run `pyvm tui` to explore the interactive interface
4. See [QUICKSTART.md](QUICKSTART.md) for usage examples
