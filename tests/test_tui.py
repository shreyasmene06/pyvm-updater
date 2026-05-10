import pytest

pytest.importorskip("textual")

from pyvm_updater.tui import MainScreen


def test_main_screen_binds_t_to_toggle_theme():
    """README advertises T as the theme toggle in TUI mode."""
    actions_for_t = [binding.action for binding in MainScreen.BINDINGS if binding.key == "t"]

    assert actions_for_t == ["toggle_theme"]
