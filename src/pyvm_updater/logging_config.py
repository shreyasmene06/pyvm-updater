"""Logging configuration for pyvm_updater."""

from __future__ import annotations

import logging
import sys

# Module-level logger
logger = logging.getLogger("pyvm")


def setup_logging(verbose: bool = False, quiet: bool = False) -> logging.Logger:
    """Configure logging for pyvm.

    Args:
        verbose: If True, show DEBUG level messages.
        quiet: If True, only show WARNING and above.

    Returns:
        Configured logger instance.
    """
    # Determine log level
    if quiet:
        level = logging.WARNING
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    # Configure root logger for pyvm
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers.clear()

    # Create console handler with formatting
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)

    # Simple format for CLI output
    if verbose:
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")
    else:
        # Clean format for normal use
        formatter = logging.Formatter("%(message)s")

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Optional submodule name (e.g., "version", "installers").
              If None, returns the root pyvm logger.

    Returns:
        Logger instance.
    """
    if name:
        return logging.getLogger(f"pyvm.{name}")
    return logger
