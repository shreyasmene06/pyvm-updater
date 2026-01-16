# Contributing to pyvm

Thank you for your interest in contributing to pyvm. This document provides guidelines for contributing to the project.

## Safety Guidelines

### Code that must NOT be added

- Modifications to `/usr/bin/python3` or system Python symlinks
- Usage of `update-alternatives` to change system defaults
- Alterations to system PATH or shell configuration files
- Modifications to conda or virtualenv environments
- Deletion or replacement of existing Python installations
- Changes to system-wide Python settings

### Code requirements

- Install Python side-by-side with existing versions only
- Respect the user's system configuration
- Provide clear instructions instead of automatic modifications
- Work well with virtual environments
- Include proper error handling and validation

## Development Setup

```bash
# Clone the repository
git clone https://github.com/shreyasmene06/pyvm-updater.git
cd pyvm-updater

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

## Project Structure

```
pyvm-updater/
├── src/pyvm_updater/       # Main package
│   ├── __init__.py         # Package metadata
│   ├── cli.py              # CLI commands (click)
│   ├── config.py           # Configuration management
│   ├── constants.py        # Global constants
│   ├── history.py          # Installation history
│   ├── installers.py       # Platform-specific installers
│   ├── logging_config.py   # Logging configuration
│   ├── tui.py              # Terminal UI (textual)
│   ├── utils.py            # Utility functions
│   ├── venv.py             # Virtual environment management
│   └── version.py          # Version checking
├── tests/                  # Test suite
├── docs/                   # Documentation
└── pyproject.toml          # Package configuration
```

## Testing

Run tests before submitting a pull request:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=pyvm_updater

# Run specific test file
pytest tests/test_utils.py -v
```

## Code Quality

The project uses several tools to maintain code quality:

```bash
# Format code with Black
black src/ tests/

# Run Ruff linter
ruff check .

# Run Flake8
flake8 src/ tests/

# Type checking with mypy
mypy src/pyvm_updater --ignore-missing-imports

# Security scan with Bandit
bandit -r src/ --severity-level medium
```

All checks must pass before a pull request can be merged.

## Code Style

- Follow PEP 8 guidelines
- Use type hints for function parameters and return values
- Add docstrings to all public functions and classes
- Keep functions focused and single-purpose
- Use meaningful variable and function names
- Maximum line length is 120 characters

Example:

```python
def download_file(url: str, destination: Path, timeout: int = 30) -> bool:
    """
    Download a file from a URL to the specified destination.

    Args:
        url: The URL to download from.
        destination: The local path to save the file.
        timeout: Request timeout in seconds.

    Returns:
        True if download succeeded, False otherwise.
    """
    # Implementation
    pass
```

## Pull Request Process

1. Fork the repository and create your branch from `main`
2. Make your changes following the guidelines above
3. Add or update tests for your changes
4. Ensure all tests pass and code quality checks succeed
5. Update documentation if needed
6. Commit with clear, descriptive messages using conventional format:
   ```
   fix: correct version comparison logic
   feat: add support for Python 3.14
   docs: update installation instructions
   test: add tests for history module
   ```
7. Submit a pull request with:
   - Clear description of the changes
   - Reason for the changes
   - How you tested the changes
   - Screenshots if relevant for UI changes

## Bug Reports

When reporting bugs, include:

- Operating system and version
- Python version (`python3 --version`)
- pyvm version (`pyvm --version`)
- Exact command that caused the issue
- Full error message and traceback
- Expected behavior

## Feature Requests

Before requesting features:

1. Ensure it aligns with the tool's purpose (safe Python installation)
2. Verify it does not violate safety guidelines
3. Describe your use case clearly
4. Explain why existing functionality is insufficient

## What Will Not Be Accepted

- Features that modify system defaults automatically
- Code requiring root/admin for basic operations
- Platform-specific implementations that break other platforms
- Features that duplicate existing tools (pyenv, conda, etc.)
- Code without proper error handling
- Changes without corresponding tests

## What We Welcome

- Improved error messages and user guidance
- Better cross-platform compatibility
- Enhanced detection of Python installations
- Documentation improvements
- Bug fixes with test cases
- Performance improvements
- Additional tests for existing functionality

## Documentation

When updating documentation:

- Keep language clear and concise
- Include code examples where appropriate
- Add warnings for potentially dangerous operations
- Update all relevant docs (README, INSTALL, QUICKSTART, etc.)
- Verify all code examples work correctly

## Security Issues

If you find a security vulnerability:

1. Do not open a public issue
2. Email the maintainer directly (see pyproject.toml for contact)
3. Describe the vulnerability and its potential impact
4. Allow time for a fix before public disclosure

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions

If you have questions about contributing, open a discussion on GitHub or reach out to the maintainers.
