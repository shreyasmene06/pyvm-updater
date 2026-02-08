"""Base class for Python installer plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class InstallerPlugin(ABC):
    """Base class for all Python installer plugins."""

    @abstractmethod
    def get_name(self) -> str:
        """Return the unique name of the installer plugin."""
        pass

    @abstractmethod
    def is_supported(self) -> bool:
        """Return True if this installer is supported on the current system."""
        pass

    @abstractmethod
    def install(self, version: str, **kwargs: Any) -> bool:
        """Install a specific Python version.

        Args:
            version: The version string to install (e.g., "3.12.1").
            **kwargs: Additional installer-specific arguments.

        Returns:
            True if installation was successful, False otherwise.
        """
        pass

    @abstractmethod
    def uninstall(self, version: str) -> bool:
        """Uninstall a specific Python version.

        Args:
            version: The version string to uninstall.

        Returns:
            True if uninstallation was successful, False otherwise.
        """
        pass

    def get_priority(self) -> int:
        """Return the priority of this installer (higher is better).

        Default priority is 10. Standard installers like mise/pyenv should have
        higher priority than generic system package managers.
        """
        return 10
