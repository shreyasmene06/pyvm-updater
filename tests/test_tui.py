"""Tests for TUI keyboard bindings."""

from pathlib import Path


def test_main_screen_binds_t_to_toggle_theme():
    tui_source = Path("src/pyvm_updater/tui.py").read_text(encoding="utf-8")
    assert 'Binding("t", "toggle_theme", "Theme")' in tui_source
    assert "def action_toggle_theme(self) -> None:" in tui_source
