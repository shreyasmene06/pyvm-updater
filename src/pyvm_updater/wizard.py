"""Interactive installation wizard for pyvm."""

from __future__ import annotations

import platform
import re
from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Checkbox,
    ContentSwitcher,
    Input,
    Label,
    RadioButton,
    RadioSet,
    Static,
)

from .plugins.manager import get_plugin_manager


class WizardScreen(ModalScreen[dict[str, Any]]):
    """A guided installation wizard for Python versions."""

    CSS = """
    WizardScreen {
        align: center middle;
        background: rgba(0, 0, 0, 0.5);
    }

    #wizard-container {
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    .wizard-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        background: $primary;
        color: $text;
    }

    .step-container {
        margin: 1 0;
        height: auto;
    }

    .step-label {
        margin-bottom: 1;
    }

    #button-nav {
        margin-top: 1;
        align: center middle;
        height: auto;
    }

    Button {
        margin: 0 1;
    }

    .hidden {
        display: none;
    }

    RadioSet {
        margin: 1 0;
    }
    """

    def __init__(self, version: str | None = None):
        super().__init__()
        self.version = version or ""
        self.steps = ["step-version", "step-installer", "step-options", "step-confirm"]
        self.current_step_idx = 0
        if self.version:
            self.current_step_idx = 1  # Skip version selection if provided

        self.options: dict[str, Any] = {
            "version": self.version,
            "installer": "auto",
            "build_from_source": False,
            "optimizations": True,
            "install_path": "",
            "add_to_path": True,
        }

    def compose(self) -> ComposeResult:
        with Vertical(id="wizard-container"):
            yield Label("PYTHON INSTALLATION WIZARD", classes="wizard-title")

            with ContentSwitcher(initial=self.steps[self.current_step_idx]):
                # Step 1: Version Selection
                with Vertical(id="step-version", classes="step-container"):
                    yield Label("Enter the Python version you want to install:", classes="step-label")
                    yield Label("(e.g., 3.12.1)", classes="step-label")
                    yield Input(placeholder="3.12.1", id="version-input", value=self.version)

                # Step 2: Installer Selection
                with Vertical(id="step-installer", classes="step-container"):
                    yield Label("Select preferred installer:", classes="step-label")
                    with RadioSet(id="installer-select"):
                        yield RadioButton("Automatic (Recommended)", id="installer-auto", value=True)
                        pm = get_plugin_manager()
                        for plugin in pm.get_supported_plugins():
                            yield RadioButton(plugin.get_name().title(), id=f"installer-{plugin.get_name()}")

                # Step 3: Advanced Options
                with Vertical(id="step-options", classes="step-container"):
                    yield Label("Advanced Installation Options:", classes="step-label")

                    if platform.system() == "Linux":
                        yield Checkbox("Build from source (Recommended for performance)", id="opt-source", value=False)
                        yield Checkbox(
                            "Enable optimizations (--enable-optimizations)", id="opt-optimizations", value=True
                        )

                    yield Label("Custom Installation Path (Optional):", classes="step-label")
                    yield Input(placeholder="/usr/local/custom-python", id="opt-path")

                    if platform.system() == "Windows":
                        yield Checkbox("Add Python to PATH", id="opt-add-path", value=True)

                # Step 4: Confirmation
                with Vertical(id="step-confirm", classes="step-container"):
                    yield Label("Confirm Installation Details:", classes="step-label")
                    yield Static(id="confirm-details")
                    yield Label("\nProceed with installation?", classes="step-label")

            with Horizontal(id="button-nav"):
                yield Button("Back", id="btn-back", variant="default")
                yield Button("Next", id="btn-next", variant="primary")
                yield Button("Cancel", id="btn-cancel", variant="error")

    def on_mount(self) -> None:
        self._update_nav_buttons()

    def _update_nav_buttons(self) -> None:
        back_btn = self.query_one("#btn-back", Button)
        next_btn = self.query_one("#btn-next", Button)

        if self.current_step_idx == 0:
            back_btn.disabled = True
        else:
            back_btn.disabled = False

        if self.current_step_idx == len(self.steps) - 1:
            next_btn.label = "Install"
            next_btn.variant = "success"
            self._update_confirm_details()
        else:
            next_btn.label = "Next"
            next_btn.variant = "primary"

    def _update_confirm_details(self) -> None:
        details = f"Version: [cyan]{self.options['version']}[/cyan]\n"
        details += f"Installer: [cyan]{self.options['installer']}[/cyan]\n"

        if platform.system() == "Linux" and self.options.get("build_from_source"):
            details += "Build: [cyan]From Source[/cyan]\n"
            details += f"Optimizations: [cyan]{'Enabled' if self.options.get('optimizations') else 'Disabled'}[/cyan]\n"

        if self.options.get("install_path"):
            details += f"Path: [cyan]{self.options['install_path']}[/cyan]\n"

        if platform.system() == "Windows":
            details += f"Add to PATH: [cyan]{'Yes' if self.options.get('add_to_path') else 'No'}[/cyan]\n"

        self.query_one("#confirm-details", Static).update(details)

    @on(Button.Pressed, "#btn-cancel")
    def cancel_wizard(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#btn-back")
    def prev_step(self) -> None:
        if self.current_step_idx > 0:
            self.current_step_idx -= 1
            self.query_one(ContentSwitcher).current = self.steps[self.current_step_idx]
            self._update_nav_buttons()

    @on(Button.Pressed, "#btn-next")
    def next_step(self) -> None:
        # Validate current step
        if self.current_step_idx == 0:
            ver = self.query_one("#version-input", Input).value.strip()
            if not ver or not re.match(r"^\d+\.\d+\.\d+$", ver):
                self.query_one("#version-input", Input).styles.border = ("solid", "red")
                return
            self.query_one("#version-input", Input).styles.border = None
            self.options["version"] = ver

        elif self.current_step_idx == 1:
            # Installer selection is handled by radio set event or we can check it here
            rs = self.query_one("#installer-select", RadioSet)
            if rs.pressed_button and rs.pressed_button.id:
                btn_id = rs.pressed_button.id
                if btn_id == "installer-auto":
                    self.options["installer"] = "auto"
                else:
                    self.options["installer"] = btn_id.replace("installer-", "")

        elif self.current_step_idx == 2:
            # Collect options
            if platform.system() == "Linux":
                try:
                    self.options["build_from_source"] = self.query_one("#opt-source", Checkbox).value
                    self.options["optimizations"] = self.query_one("#opt-optimizations", Checkbox).value
                except Exception:
                    pass

            path_input = self.query_one("#opt-path", Input).value.strip()
            self.options["install_path"] = path_input

            if platform.system() == "Windows":
                try:
                    self.options["add_to_path"] = self.query_one("#opt-add-path", Checkbox).value
                except Exception:
                    pass

        if self.current_step_idx < len(self.steps) - 1:
            self.current_step_idx += 1
            self.query_one(ContentSwitcher).current = self.steps[self.current_step_idx]
            self._update_nav_buttons()
        else:
            # Final step: Install
            self.dismiss(self.options)
