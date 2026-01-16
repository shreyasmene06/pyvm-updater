# Project Structure

This document describes the organization of the pyvm-updater codebase.

## Directory Layout

```
pyvm-updater/
├── pyproject.toml              # Package configuration and dependencies
├── README.md                   # Main documentation
├── CHANGELOG.md                # Version history
├── CONTRIBUTING.md             # Contribution guidelines
├── LICENSE                     # MIT License
├── PROJECT_STRUCTURE.md        # This file
├── conftest.py                 # Pytest configuration
├── check_requirements.py       # Pre-installation verification
├── install.sh                  # Linux/macOS installation script
├── install.bat                 # Windows installation script
│
├── src/pyvm_updater/           # Main package
│   ├── __init__.py             # Package metadata and version
│   ├── cli.py                  # CLI commands (click)
│   ├── config.py               # Configuration management
│   ├── constants.py            # Global constants
│   ├── history.py              # Installation history tracking
│   ├── installers.py           # Platform-specific installers
│   ├── logging_config.py       # Logging configuration
│   ├── tui.py                  # Terminal User Interface (textual)
│   ├── utils.py                # Utility functions
│   ├── venv.py                 # Virtual environment management
│   └── version.py              # Version checking and fetching
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── test_history.py         # Tests for history module
│   ├── test_utils.py           # Tests for utils module
│   ├── test_venv.py            # Tests for venv module
│   └── test_version.py         # Tests for version module
│
└── docs/                       # Documentation
    ├── CRITICAL_SECURITY_FIX_v1.2.1.md
    ├── FIXES_SUMMARY.md
    ├── INSTALL.md
    ├── QUICK_REFERENCE.md
    └── QUICKSTART.md
```

## Module Descriptions

### Core Package (src/pyvm_updater/)

| Module | Description |
|--------|-------------|
| `__init__.py` | Package metadata including version and author |
| `cli.py` | Command-line interface using Click framework |
| `config.py` | Configuration file management (~/.config/pyvm/config.toml) |
| `constants.py` | Network timeouts, file paths, and other constants |
| `history.py` | Tracks installation/update history for rollback support |
| `installers.py` | Platform-specific Python installation logic |
| `logging_config.py` | Configurable logging with verbose/quiet modes |
| `tui.py` | Interactive Terminal User Interface using Textual |
| `utils.py` | Helper functions for downloads, checksums, and validation |
| `venv.py` | Virtual environment creation and management |
| `version.py` | Version checking against python.org |

## CLI Commands

| Command | Description |
|---------|-------------|
| `pyvm check` | Check current Python version against latest |
| `pyvm list` | List available Python versions |
| `pyvm install <version>` | Install a specific Python version |
| `pyvm update` | Update to the latest Python version |
| `pyvm remove <version>` | Remove an installed Python version |
| `pyvm rollback` | Undo the last installation |
| `pyvm config` | View or manage configuration |
| `pyvm venv create <name>` | Create a virtual environment |
| `pyvm venv list` | List virtual environments |
| `pyvm venv activate <name>` | Show activation command |
| `pyvm venv remove <name>` | Remove a virtual environment |
| `pyvm tui` | Launch interactive TUI |
| `pyvm info` | Show system information |

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

## Testing

Run tests using pytest:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=pyvm_updater

# Run specific test file
pytest tests/test_utils.py -v
```

## Dependencies

### Runtime

| Package | Purpose |
|---------|---------|
| requests | HTTP requests for downloading |
| beautifulsoup4 | HTML parsing for python.org |
| packaging | Version comparison |
| click | CLI framework |
| textual | Terminal UI framework |

### Development

| Package | Purpose |
|---------|---------|
| pytest | Test framework |
| pytest-cov | Coverage reporting |
| mypy | Type checking |
| black | Code formatting |
| ruff | Fast linting |
| flake8 | Additional linting |
| bandit | Security scanning |

## Development Setup

```bash
# Clone repository
git clone https://github.com/shreyasmene06/pyvm-updater.git
cd pyvm-updater

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run linters
ruff check .
black --check .
mypy src/pyvm_updater
```

## Build and Distribution

```bash
# Build package
pip install build
python -m build

# Output in dist/
# - pyvm_updater-X.Y.Z.tar.gz (source)
# - pyvm_updater-X.Y.Z-py3-none-any.whl (wheel)
```

## GitHub Actions

The project uses GitHub Actions for CI/CD:

- **pr-review.yml**: Runs on pull requests and pushes to main
  - Type checking (mypy)
  - Linting (ruff, flake8)
  - Format checking (black)
  - Security scanning (bandit)
  - Dependency checking (pip-audit)
  - Tests (pytest) on Python 3.9-3.13

- **python-publish.yml**: Publishes to PyPI on release
