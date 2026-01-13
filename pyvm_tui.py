#!/usr/bin/env python3
"""
Python Version Manager - TUI Interface
A clean terminal user interface for managing Python versions
"""

import asyncio
import sys
from typing import Any, Optional

try:
    from textual import work
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Container, Horizontal, Vertical
    from textual.screen import Screen
    from textual.widgets import Button, Footer, Header, Label, ListItem, ListView, LoadingIndicator, Static
except ImportError:
    print("ERROR: TUI mode requires the 'textual' package.")
    print("Install it with: pip install textual")
    sys.exit(1)

# Import from main module
from python_version import (
    check_python_version,
    get_active_python_releases,
    get_installed_python_versions,
    get_os_info,
    update_python_linux,
    update_python_macos,
    remove_python_windows,
    remove_python_linux,
    remove_python_macos,
    validate_version_string,
)


class StatusBar(Static):
    """Status bar for showing messages"""

    def __init__(self, **kwargs):
        super().__init__("", **kwargs)

    def set_message(self, message: str, style: str = "") -> None:
        if style:
            self.update(f"[{style}]{message}[/{style}]")
        else:
            self.update(message)

    def clear(self) -> None:
        self.update("")


class VersionItem(ListItem):
    """A selectable version item in a list"""

    def __init__(self, version: str, info: str = "", is_current: bool = False, can_install: bool = False):
        super().__init__()
        self.version = version
        self.info = info
        self.is_current = is_current
        self.can_install = can_install

    def compose(self) -> ComposeResult:
        text = f"{self.version}"
        if self.is_current:
            text = f"[cyan bold]{self.version}[/cyan bold] [dim](current)[/dim]"
        elif self.info:
            text = f"{self.version} [dim]{self.info}[/dim]"
        yield Label(text)


class InstalledList(ListView):
    """List of installed Python versions"""

    BINDINGS = [
        Binding("tab", "focus_next_panel", "Next Panel", show=False),
        Binding("shift+tab", "focus_prev_panel", "Prev Panel", show=False),
        Binding("x", "remove_selected", "Remove", show=True),
        Binding("delete", "remove_selected", "Remove", show=False),
    ]

    def action_focus_next_panel(self) -> None:
        if hasattr(self.screen, "focus_next_panel"):
            self.screen.focus_next_panel()  # type: ignore[attr-defined]

    def action_focus_prev_panel(self) -> None:
        if hasattr(self.screen, "focus_prev_panel"):
            self.screen.focus_prev_panel()  # type: ignore[attr-defined]

    def action_remove_selected(self) -> None:
        if self.highlighted_child and isinstance(self.highlighted_child, VersionItem):
            version = self.highlighted_child.version
            
            # Prevent removing current python (major.minor check)
            local_ver = platform.python_version()
            local_parts = local_ver.split('.')
            version_parts = version.split('.')
            
            is_same_major_minor = False
            if len(local_parts) >= 2 and len(version_parts) >= 2:
                if local_parts[0] == version_parts[0] and local_parts[1] == version_parts[1]:
                    is_same_major_minor = True

            if self.highlighted_child.is_current or is_same_major_minor:
                self.app.bell()
                self.screen.query_one("#status-bar").set_message(f"Cannot remove Python {version} (matches running major.minor)", "red")
                return
            self.screen.start_remove(version)


class AvailableList(ListView):
    """List of available Python versions - press Enter to install"""

    BINDINGS = [
        Binding("tab", "focus_next_panel", "Next Panel", show=False),
        Binding("shift+tab", "focus_prev_panel", "Prev Panel", show=False),
        Binding("enter", "install_selected", "Install", show=True),
    ]

    def action_focus_next_panel(self) -> None:
        if hasattr(self.screen, "focus_next_panel"):
            self.screen.focus_next_panel()  # type: ignore[attr-defined]

    def action_focus_prev_panel(self) -> None:
        if hasattr(self.screen, "focus_prev_panel"):
            self.screen.focus_prev_panel()  # type: ignore[attr-defined]

    def action_install_selected(self) -> None:
        if self.highlighted_child and isinstance(self.highlighted_child, VersionItem):
            version = self.highlighted_child.version
            if hasattr(self.screen, "start_install"):
                self.screen.start_install(version)  # type: ignore[attr-defined]


class MainScreen(Screen):
    """Main TUI screen with navigable panels"""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("u", "update_latest", "Update"),
        Binding("1", "focus_installed", "Installed", show=False),
        Binding("2", "focus_available", "Available", show=False),
        Binding("?", "help", "Help"),
    ]

    CSS = """
    MainScreen {
        layout: vertical;
    }

    #main-container {
        height: 100%;
        padding: 1 2;
    }

    #title-box {
        height: auto;
        text-align: center;
        padding: 0 2;
        margin-bottom: 1;
        border-bottom: solid $primary;
    }

    #content-area {
        height: 1fr;
        layout: horizontal;
    }

    .panel {
        width: 1fr;
        height: 100%;
        border: solid $primary;
        margin: 0 1;
        background: $surface;
    }

    .panel:first-child {
        margin-left: 0;
    }

    .panel:last-child {
        margin-right: 0;
    }

    .panel-title {
        text-style: bold;
        text-align: center;
        padding: 0 1;
        border-bottom: solid $primary;
        background: $surface-darken-1;
    }

    .panel-title-focused {
        background: $primary;
        color: $background;
    }

    #installed-list, #available-list {
        height: 1fr;
        scrollbar-gutter: stable;
    }

    #installed-list:focus, #available-list:focus {
        border: none;
    }

    #installed-list > ListItem, #available-list > ListItem {
        padding: 0 1;
    }

    #installed-list > ListItem:hover, #available-list > ListItem:hover {
        background: $primary 20%;
    }

    #installed-list > ListItem.-highlight, #available-list > ListItem.-highlight {
        background: $primary 40%;
    }

    #status-panel-container {
        padding: 1;
    }

    #status-info {
        text-align: center;
    }

    #button-area {
        height: auto;
        margin-top: 1;
        layout: horizontal;
        align: center middle;
        padding: 1 0;
    }

    Button {
        margin: 0 1;
        min-width: 14;
    }

    #status-bar {
        height: 1;
        dock: bottom;
        padding: 0 2;
        background: $surface;
        border-top: solid $primary;
    }

    #loading {
        height: 3;
        align: center middle;
        display: none;
    }

    #loading.visible {
        display: block;
    }

    #hint-bar {
        height: auto;
        text-align: center;
        padding: 0;
        color: $text-muted;
    }
    """

    def __init__(self):
        super().__init__()
        self.local_ver: str = "..."
        self.latest_ver: Optional[str] = None
        self.needs_update: bool = False
        self.installed_versions: list[dict] = []
        self.available_releases: list[dict] = []
        self.panels = ["installed-list", "available-list"]
        self.current_panel_idx = 1  # Start on available

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Container(id="main-container"):
            yield Static("[bold]PYTHON VERSION MANAGER[/bold]", id="title-box")

            with Container(id="loading"):
                yield LoadingIndicator()
                yield Label("Loading...")

            yield Static(
                "[dim]Tab: switch panels | Arrow keys: navigate | Enter: install | X: remove | R: refresh | U: update | Q: quit[/dim]",
                id="hint-bar"
            )

            with Horizontal(id="content-area"):
                with Vertical(classes="panel", id="installed-panel"):
                    yield Static("INSTALLED", classes="panel-title", id="installed-title")
                    yield InstalledList(id="installed-list")

                with Vertical(classes="panel", id="available-panel"):
                    yield Static("AVAILABLE (Enter to install)", classes="panel-title", id="available-title")
                    yield AvailableList(id="available-list")

                with Vertical(classes="panel", id="status-panel"):
                    yield Static("STATUS", classes="panel-title", id="status-title")
                    with Container(id="status-panel-container"):
                        yield Static(id="status-info")

            with Horizontal(id="button-area"):
                yield Button("Refresh [R]", id="refresh-btn", variant="default")
                yield Button("Update [U]", id="update-btn", variant="primary")
                yield Button("Quit [Q]", id="quit-btn", variant="error")

            yield StatusBar(id="status-bar")

        yield Footer()

    def on_mount(self) -> None:
        self.refresh_all()
        # Focus available list by default
        self.set_timer(0.1, self._focus_available)

    def _focus_available(self) -> None:
        try:
            self.query_one("#available-list", AvailableList).focus()
            self._update_panel_highlights()
        except Exception:
            pass

    def focus_next_panel(self) -> None:
        """Switch to next panel"""
        self.current_panel_idx = (self.current_panel_idx + 1) % len(self.panels)
        self._focus_current_panel()

    def focus_prev_panel(self) -> None:
        """Switch to previous panel"""
        self.current_panel_idx = (self.current_panel_idx - 1) % len(self.panels)
        self._focus_current_panel()

    def _focus_current_panel(self) -> None:
        panel_id = self.panels[self.current_panel_idx]
        try:
            self.query_one(f"#{panel_id}").focus()
            self._update_panel_highlights()
        except Exception:
            pass

    def _update_panel_highlights(self) -> None:
        """Update panel title styling based on focus"""
        # Reset all
        for title_id in ["installed-title", "available-title", "status-title"]:
            try:
                self.query_one(f"#{title_id}").remove_class("panel-title-focused")
            except Exception:
                pass

        # Highlight focused
        focused = self.focused
        if focused:
            if focused.id == "installed-list":
                self.query_one("#installed-title").add_class("panel-title-focused")
            elif focused.id == "available-list":
                self.query_one("#available-title").add_class("panel-title-focused")

    def on_focus(self, event: Any) -> None:
        self._update_panel_highlights()

    def action_focus_installed(self) -> None:
        self.current_panel_idx = 0
        self._focus_current_panel()

    def action_focus_available(self) -> None:
        self.current_panel_idx = 1
        self._focus_current_panel()

    @work(exclusive=True)
    async def refresh_all(self) -> None:
        """Refresh all data"""
        loading = self.query_one("#loading")
        loading.add_class("visible")
        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.set_message("Loading...", "dim")

        try:
            # Check versions
            local_ver, latest_ver, needs_update = await asyncio.to_thread(check_python_version, True)
            self.local_ver = local_ver
            self.latest_ver = latest_ver
            self.needs_update = needs_update

            # Get installed versions
            self.installed_versions = await asyncio.to_thread(get_installed_python_versions)
            await self._populate_installed_list()

            # Get available releases
            self.available_releases = await asyncio.to_thread(get_active_python_releases)
            await self._populate_available_list()

            # Update status panel
            status_info = self.query_one("#status-info", Static)
            if needs_update:
                status_info.update(
                    f"[bold]Current:[/bold]\n[cyan]{local_ver}[/cyan]\n\n"
                    f"[bold]Latest:[/bold]\n[green]{latest_ver}[/green]\n\n"
                    f"[yellow bold]Update available![/yellow bold]\n"
                    f"[dim]Press U to update[/dim]"
                )
                status_bar.set_message(f"Update available: {local_ver} -> {latest_ver}", "yellow")
            else:
                status_info.update(
                    f"[bold]Current:[/bold]\n[cyan]{local_ver}[/cyan]\n\n"
                    f"[bold]Latest:[/bold]\n[green]{latest_ver}[/green]\n\n"
                    f"[green bold]Up to date[/green bold]"
                )
                status_bar.set_message("Up to date", "green")

        except Exception as e:
            status_bar.set_message(f"Error: {e}", "red")
        finally:
            loading.remove_class("visible")

    async def _populate_installed_list(self) -> None:
        """Populate the installed versions list"""
        installed_list = self.query_one("#installed-list", InstalledList)
        await installed_list.clear()

        if not self.installed_versions:
            await installed_list.append(VersionItem("No versions detected", "", False, False))
            return

        for v in self.installed_versions:
            ver = v.get("version", "Unknown")
            path = v.get("path", "")
            is_current = v.get("default", False)
            # Shorten path for display
            short_path = path.split("/")[-1] if "/" in path else path.split("\\")[-1] if "\\" in path else ""
            await installed_list.append(VersionItem(ver, short_path, is_current, False))

    async def _populate_available_list(self) -> None:
        """Populate the available versions list"""
        available_list = self.query_one("#available-list", AvailableList)
        await available_list.clear()

        if not self.available_releases:
            await available_list.append(VersionItem("Could not fetch releases", "", False, False))
            return

        for rel in self.available_releases:
            version = rel.get("latest_version", "")
            status = rel.get("status", "")

            # Shorten status
            if "pre-release" in status.lower():
                status = "prerelease"
            elif "bugfix" in status.lower():
                status = "active"
            elif "security" in status.lower():
                status = "security"
            elif "end of life" in status.lower():
                status = "EOL"

            if version:
                is_current = version.startswith(".".join(self.local_ver.split(".")[:2]))
                await available_list.append(VersionItem(version, status, is_current, True))

        # Select first item
        if available_list.children:
            available_list.index = 0

    def start_install(self, version: str) -> None:
        """Start installing a version (called from AvailableList)"""
        self.run_install_with_suspend(version)

    def start_remove(self, version: str) -> None:
        """Start removing a version (called from InstalledList)"""
        self.run_remove_with_suspend(version)

    def run_install_with_suspend(self, version: str) -> None:
        """Run installation with TUI suspended so terminal output is visible"""
        from textual.app import SuspendNotSupported

        os_name, _ = get_os_info()
        success = False

        def do_installation():
            print(f"\n{'=' * 50}")
            print(f"Installing Python {version}")
            print(f"{'=' * 50}\n")

            if os_name == "windows":
                return update_python_windows(version)
            elif os_name == "linux":
                return update_python_linux(version)
            elif os_name == "darwin":
                return update_python_macos(version)
            else:
                print(f"Unsupported OS: {os_name}")
                return False

        try:
            # Suspend TUI, run installation, then resume
            with self.app.suspend():
                success = do_installation()
                print(f"\n{'=' * 50}")
                if success:
                    print("Installation complete!")
                else:
                    print("Installation may have had issues.")
                print(f"{'=' * 50}")
                print("\nPress Enter to return to TUI...")
                try:
                    input()
                except EOFError:
                    pass
        except SuspendNotSupported:
            # Fallback for environments that don't support suspend (e.g., Textual Web)
            status_bar = self.query_one("#status-bar", StatusBar)
            status_bar.set_message(f"Installing Python {version}... (check terminal)", "yellow")
            success = do_installation()

        # Update status and refresh after resuming
        status_bar = self.query_one("#status-bar", StatusBar)
        if success:
            status_bar.set_message(f"Python {version} installed successfully!", "green")
            self.app.push_screen(SuccessScreen(version, os_name))
        else:
            status_bar.set_message("Installation had issues.", "yellow")

        # Refresh to show updated installed versions
        self.refresh_all()

    def run_remove_with_suspend(self, version: str) -> None:
        """Run removal with TUI suspended so terminal output is visible"""
        from textual.app import SuspendNotSupported
        
        os_name, _ = get_os_info()
        success = False

        def do_removal():
            print(f"\n{'='*50}")
            print(f"Removing Python {version}")
            print(f"{'='*50}\n")

            if os_name == 'windows':
                return remove_python_windows(version)
            elif os_name == 'linux':
                return remove_python_linux(version)
            elif os_name == 'darwin':
                return remove_python_macos(version)
            else:
                print(f"Unsupported OS: {os_name}")
                return False

        try:
            # Suspend TUI, run removal, then resume
            with self.app.suspend():
                # Add confirmation in suspended mode for safety
                print(f"Are you sure you want to remove Python {version}? (y/n): ", end="", flush=True)
                confirm = input().lower()
                if confirm == 'y':
                    success = do_removal()
                    print(f"\n{'='*50}")
                    if success:
                        print(f"Removal complete!")
                    else:
                        print(f"Removal may have had issues.")
                    print(f"{'='*50}")
                else:
                    print("Removal cancelled.")
                
                print("\nPress Enter to return to TUI...")
                try:
                    input()
                except EOFError:
                    pass
        except SuspendNotSupported:
            # Fallback
            status_bar = self.query_one("#status-bar", StatusBar)
            status_bar.set_message(f"Removing Python {version}... (check terminal)", "yellow")
            success = do_removal()

        # Update status and refresh after resuming
        status_bar = self.query_one("#status-bar", StatusBar)
        if success:
            status_bar.set_message(f"Python {version} removed successfully!", "green")
        else:
            status_bar.set_message("Removal had issues or was cancelled.", "yellow")

        # Refresh to show updated installed versions
        self.refresh_all()

    @work(exclusive=True)
    async def do_install(self, version: str) -> None:
        """Install a specific Python version (async wrapper that suspends TUI)"""
        # Use the synchronous suspend method
        self.run_install_with_suspend(version)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "refresh-btn":
            self.action_refresh()
        elif event.button.id == "update-btn":
            self.action_update_latest()
        elif event.button.id == "quit-btn":
            self.action_quit()

    def action_refresh(self) -> None:
        self.refresh_all()

    def action_update_latest(self) -> None:
        status_bar = self.query_one("#status-bar", StatusBar)

        if not self.latest_ver:
            status_bar.set_message("No version info yet. Please wait or press R to refresh.", "red")
            return

        status_bar.set_message(f"Starting update to Python {self.latest_ver}...", "yellow")
        self.do_install(self.latest_ver)

    def action_quit(self) -> None:
        self.app.exit()

    def action_help(self) -> None:
        self.app.push_screen(HelpScreen())


class SuccessScreen(Screen):
    """Screen shown after successful installation"""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("enter", "go_back", "Back"),
        Binding("q", "quit", "Quit"),
    ]

    CSS = """
    SuccessScreen {
        align: center middle;
    }

    #success-container {
        width: 65;
        height: auto;
        padding: 1 2;
        border: solid $success;
        background: $surface;
    }

    #success-title {
        text-align: center;
        text-style: bold;
        color: $success;
        padding: 1;
        margin-bottom: 1;
        border-bottom: solid $success;
    }

    #back-btn {
        margin-top: 1;
        width: 100%;
    }
    """

    def __init__(self, version: str, os_name: str):
        super().__init__()
        self.version = version
        self.os_name = os_name

    def compose(self) -> ComposeResult:
        parts = self.version.split(".")
        major_minor = f"{parts[0]}.{parts[1]}" if len(parts) >= 2 else self.version

        with Container(id="success-container"):
            yield Static("INSTALLATION COMPLETE", id="success-title")
            yield Static(f"Python {self.version} installed successfully.\n")

            if self.os_name in ("linux", "darwin"):
                instructions = f"""[bold]Usage:[/bold]
  python{major_minor} script.py
  python{major_minor} -m venv myenv
  python{major_minor} --version"""
            else:
                instructions = f"""[bold]Usage:[/bold]
  py -{major_minor} script.py
  py -{major_minor} -m venv myenv
  py --list"""

            yield Static(instructions)
            yield Static("\n[dim]Previous version remains as system default.[/dim]")
            yield Button("Back [Enter]", id="back-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.action_go_back()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_quit(self) -> None:
        self.app.exit()


class HelpScreen(Screen):
    """Help screen"""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("enter", "go_back", "Back"),
        Binding("q", "go_back", "Back"),
    ]

    CSS = """
    HelpScreen {
        align: center middle;
    }

    #help-container {
        width: 55;
        height: auto;
        padding: 1 2;
        border: solid $primary;
        background: $surface;
    }

    #help-title {
        text-align: center;
        text-style: bold;
        padding: 1;
        margin-bottom: 1;
        border-bottom: solid $primary;
    }

    #close-btn {
        width: 100%;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="help-container"):
            yield Static("KEYBOARD SHORTCUTS", id="help-title")

            help_text = """
[bold]Navigation[/bold]
  Tab       Next panel
  Shift+Tab Previous panel
  1 / 2     Jump to Installed / Available
  Up/Down   Move in list

[bold]Actions[/bold]
  Enter     Install selected version
  X         Remove selected version
  R         Refresh data
  U         Update to latest version
  ?         This help
  Q         Quit

[bold]CLI Commands[/bold]
  pyvm list      List versions
  pyvm install   Install version
  pyvm update    Update to latest
  pyvm check     Check for updates
"""
            yield Static(help_text)
            yield Button("Close [Enter]", id="close-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.action_go_back()

    def action_go_back(self) -> None:
        self.app.pop_screen()


class PyvmTUI(App):
    """Main TUI Application"""

    TITLE = "Python Version Manager"
    SUB_TITLE = "pyvm"

    CSS = """
    Screen {
        background: $background;
    }
    """

    SCREENS = {
        "main": MainScreen,
    }

    def on_mount(self) -> None:
        self.push_screen("main")


def run_tui():
    """Entry point for TUI mode"""
    app = PyvmTUI()
    app.run()


if __name__ == "__main__":
    run_tui()
