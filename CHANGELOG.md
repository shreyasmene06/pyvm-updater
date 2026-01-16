# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2026-01-15

### Added

- Virtual Environment Management with `pyvm venv` command group
  - `pyvm venv create <name>` creates a new venv with optional Python version
  - `pyvm venv list` shows all managed virtual environments
  - `pyvm venv remove <name>` removes a virtual environment
  - `pyvm venv activate <name>` shows activation command
- Configuration System with user preferences at `~/.config/pyvm/config.toml`
  - `pyvm config` shows current configuration
  - `pyvm config --init` creates default config file
  - `pyvm config --path` shows config file location
- Verbose and quiet modes with `--verbose` and `--quiet` CLI flags
- Comprehensive test suite with 34 tests covering core functionality

### Changed

- Modular Architecture: Complete refactor into `src/pyvm_updater/` package
  - Split monolithic script into 11 focused modules
  - Follows modern Python packaging with `src/` layout
  - Cleaner separation of concerns
- Updated documentation

### Technical

- New modules: `config.py`, `logging_config.py`, `venv.py`
- Added pytest test files for history, utils, venv, and version modules
- Removed deprecated root level `python_version.py` and `pyvm_tui.py`

## [2.1.0] - 2026-01-14

### Added

- SHA256 Checksum Verification for all Python downloads
  - Calculates SHA256 hash of downloaded files
  - Fetches expected checksum from python.org
  - Blocks installation if checksum mismatch detected
- Rollback Command (`pyvm rollback`) to undo previous installations
  - Tracks installation history (last 10 entries)
  - Removes last installed Python version
  - Available in both CLI and TUI (press B)
- Auto pyenv Installation on RHEL/CentOS/Fedora systems
  - Installs required build dependencies via dnf/yum
  - Downloads and configures pyenv using official installer
  - Sets up shell environment automatically
- Remove Version from TUI by pressing X
- Type hints added to `check_requirements.py`

### Changed

- Migrated from `setup.py` to `pyproject.toml` for modern Python packaging
- Improved code formatting with pre-commit hooks
- Enhanced error handling for installer execution and cleanup

### Fixed

- Various spelling corrections and code formatting improvements

## [2.0.1] - 2026-01-10

### Changed

- textual is now a core dependency
- No longer requires `pip install pyvm-updater[tui]`

### Fixed

- TUI not working after fresh install

## [2.0.0] - 2026-01-10

Major TUI redesign release.

### Added

- Interactive TUI with navigable panels
  - Tab/Shift+Tab navigation between Installed, Available, and Status panels
  - Arrow key navigation within panels
  - Press Enter on Available panel to install selected version
  - Mouse click support for all interactions
- mise Integration for version management
  - Auto-detects mise-installed Python versions
  - Uses mise for installation on Linux/macOS when available
- pyenv Integration
  - Auto-detects pyenv-installed Python versions
  - Uses pyenv as fallback installation method
- Improved Version Detection scanning mise, pyenv, and system directories
- Terminal Suspension during installation to show progress

### Changed

- Breaking: Removed modal input dialog
- Installation Flow now uses mise, pyenv, package manager chain
  - Linux: mise, pyenv, apt (deadsnakes), dnf/yum
  - macOS: mise, pyenv, Homebrew, manual installer
  - Windows: Official python.org installer
- TUI Layout with three-panel design
- Panel Navigation with focused panel highlighting
- Update Button works regardless of update status
- Status Display shows current Python, latest available, and update status

### Improved

- Better keyboard-driven workflow for power users
- Clearer visual feedback with panel highlighting
- More robust installation with multiple fallback options
- Cross-platform consistency across Linux, macOS, and Windows

### Technical

- Refactored TUI to use ListView widgets for better keyboard support
- Added comprehensive error handling for suspend operations
- Improved version detection to scan multiple installation directories
- Better cross-platform path handling

## [1.2.1] - 2025-11-30

### Security Fix

This release addresses a critical issue where previous versions contained code that could freeze Linux systems by modifying the system Python symlink.

### Breaking Changes

- Removed `pyvm set-default` command
- Removed `--set-default` flag from `pyvm update` command
- Tool now only installs Python side-by-side, never modifies system defaults

### Fixed

- System freeze issue caused by modifying `/usr/bin/python3` symlink via `update-alternatives`
- Terminal crashes from dangerous system Python default modification
- System GUI failures from broken Python configuration
- Package manager corruption from touching system Python configuration

### Removed

- `_set_python_default_linux()` function
- `prompt_set_as_default()` function
- `_show_access_instructions()` function (replaced with safe version)
- `pyvm set-default` CLI command
- `--set-default` flag from update command

### Added

- `show_python_usage_instructions()` for safe instruction display
- Safety documentation in `docs/CRITICAL_SECURITY_FIX_v1.2.1.md`
- Clear warnings about safe behavior
- Virtual environment usage instructions

### Changed

- `update_python_linux()` now only installs Python without modifying system defaults
- All docstrings updated to clarify safe behavior
- CLI help text updated to emphasize safety

Migration: If you were using `pyvm set-default`, switch to virtual environments:
```bash
python3.12 -m venv myproject
source myproject/bin/activate
```

## [1.2.0] - 2024-11-09

**Note**: This version is deprecated. Contains system-breaking code. Update to 1.2.1 or later.

### Added

- `--set-default` flag for `pyvm update`
- `pyvm set-default` command
- Automatic version detection
- Installation verification
- Additional packages for Ubuntu/Debian

### Changed

- Improved `update-alternatives` setup
- Better default setting logic
- Enhanced verification
- More robust path detection
- Improved error messages

### Fixed

- Linux default Python issue
- Hardcoded version bug
- PATH issues for non-Anaconda users
- Better handling of existing alternatives

## [1.1.0] - 2024-11-09

### Added

- Interactive prompt after update
- Automatic setup instructions
- Platform-specific guidance
- Linux default setter using `update-alternatives`
- pipx installation method documentation
- Troubleshooting for PEP 668 errors

### Changed

- Improved update process user experience
- Better documentation structure
- Updated installation instructions
- Enhanced Anaconda user guidance

### Fixed

- Better handling of multiple Python versions
- Clearer communication about default Python behavior

## [1.0.2] - 2024-11-08

### Fixed

- Type checking issue with `ctypes.windll` on Windows
- BeautifulSoup attribute type handling
- Type safety for BeautifulSoup `.get()` return values
- Error handling for download URL processing

### Changed

- Updated author information
- Added .gitignore file

## [1.0.1] - Previous Release

### Added

- Cross-platform Python version checking
- Automatic Python updates for Windows, Linux, and macOS
- CLI interface with click
- System information display
- Comprehensive documentation

## [1.0.0] - Initial Release

### Added

- Initial release of Python Version Manager
- Support for Windows, Linux, and macOS
- Version checking against python.org
- Automated installation features
