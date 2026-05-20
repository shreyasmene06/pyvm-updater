"""History management for pyvm_updater."""

from __future__ import annotations

import json
import platform
import time
from typing import Any, cast

from .constants import HISTORY_FILE


class HistoryManager:
    """Manages the history of Python version installations and updates."""

    @staticmethod
    def save_history(action: str, version: str) -> None:
        """Save an action and version to the history file."""
        history = HistoryManager.get_history()
        entry = {
            "timestamp": time.time(),
            "action": action,
            "version": version,
            "previous_version": platform.python_version(),
        }
        history.append(entry)

        # Keep only the last 10 entries
        history = history[-10:]

        try:
            HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(HISTORY_FILE, "w") as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save history: {e}")

    @staticmethod
    def get_history() -> list[dict[Any, Any]]:
        """Load history from the history file."""
        if not HISTORY_FILE.exists():
            return []
        try:
            with open(HISTORY_FILE) as f:
                return cast(list[dict[Any, Any]], json.load(f))
        except Exception:
            return []

    @staticmethod
    def get_last_action() -> dict[Any, Any] | None:
        """Get the last successful installation/update action."""
        history = HistoryManager.get_history()
        if not history:
            return None
        return history[-1]

    @staticmethod
    def pop_last_action() -> dict[Any, Any] | None:
        """Remove and return the last history entry, persisting the change."""
        history = HistoryManager.get_history()
        if not history:
            return None
        entry = history.pop()
        try:
            HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(HISTORY_FILE, "w") as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not update history: {e}")
        return entry
