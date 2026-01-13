"""Screen components for App Freeze TUI."""

import contextlib

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Grid, Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, ListItem, ListView, ProgressBar

from app_freeze.adb.models import AppInfo, DeviceInfo
from app_freeze.state import AppAction
from app_freeze.ui.widgets import AppListWidget, DeviceInfoPanel, StatusBar


class DeviceItem(ListItem):
    """A device item in the device list."""

    DEFAULT_CSS = """
    DeviceItem {
        height: 4;
        padding: 0 2;
    }

    DeviceItem > Vertical {
        height: 100%;
        padding: 0 1;
    }

    DeviceItem > Vertical > .device-name {
        text-style: bold;
    }

    DeviceItem > Vertical > .device-id {
        color: $text-muted;
    }

    DeviceItem > Vertical > .device-info {
        color: $text-muted;
    }

    DeviceItem:hover {
        background: $surface-light;
    }

    DeviceItem.--highlight {
        background: $accent 20%;
    }
    """

    def __init__(self, device: DeviceInfo) -> None:
        """Initialize device item."""
        super().__init__()
        self.device = device

    def compose(self) -> ComposeResult:
        """Compose the device item layout."""
        with Vertical():
            yield Label(self.device.display_name or self.device.device_id, classes="device-name")
            yield Label(f"ID: {self.device.device_id}", classes="device-id")
            info_parts = []
            if self.device.android_version:
                info_parts.append(f"Android {self.device.android_version}")
            if self.device.sdk_level:
                info_parts.append(f"SDK {self.device.sdk_level}")
            yield Label(" • ".join(info_parts) if info_parts else "", classes="device-info")


class DeviceScreen(Screen[DeviceInfo]):
    """Device selection screen."""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("enter", "select", "Select"),
        Binding("?", "help", "Help"),
    ]

    DEFAULT_CSS = """
    DeviceScreen {
        align: center middle;
    }

    DeviceScreen > Container {
        width: 80;
        height: auto;
        max-height: 80%;
    }

    DeviceScreen > Container > .title {
        text-align: center;
        text-style: bold;
        padding: 1;
    }

    DeviceScreen > Container > .subtitle {
        text-align: center;
        color: $text-muted;
        padding-bottom: 1;
    }

    DeviceScreen > Container > ListView {
        height: auto;
        max-height: 20;
        border: solid $border;
        margin: 1 0;
    }

    DeviceScreen > Container > ListView:focus {
        border: double $accent;
    }

    DeviceScreen > Container > .hint {
        text-align: center;
        color: $text-muted;
        padding: 1;
    }

    DeviceScreen > Container > .no-devices {
        text-align: center;
        color: $error;
        padding: 2;
    }
    """

    class DeviceSelected(Message):
        """Message when a device is selected."""

        def __init__(self, device: DeviceInfo) -> None:
            self.device = device
            super().__init__()

    def __init__(
        self,
        devices: list[DeviceInfo] | None = None,
        name: str | None = None,
    ) -> None:
        """Initialize device screen."""
        super().__init__(name=name)
        self._devices = devices or []

    def compose(self) -> ComposeResult:
        """Compose the device screen."""
        yield Header()
        with Container():
            yield Label("📱 Select Device", classes="title")
            yield Label("Choose a connected Android device", classes="subtitle")
            if self._devices:
                with ListView(id="device-list"):
                    for device in self._devices:
                        yield DeviceItem(device)
                yield Label("↑↓ Navigate • Enter Select • r Refresh • q Quit", classes="hint")
            else:
                yield Label("No devices connected", classes="no-devices")
                yield Label("Connect a device and press 'r' to refresh", classes="hint")
        yield Footer()

    def on_mount(self) -> None:
        """Focus the device list on mount."""
        with contextlib.suppress(Exception):
            self.query_one("#device-list", ListView).focus()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def action_refresh(self) -> None:
        """Refresh device list."""
        self.app.post_message(DeviceScreen.DeviceSelected(None))  # type: ignore

    def action_select(self) -> None:
        """Select the highlighted device."""
        with contextlib.suppress(Exception):
            device_list = self.query_one("#device-list", ListView)
            highlighted = device_list.highlighted_child
            if highlighted and isinstance(highlighted, DeviceItem):
                self.dismiss(highlighted.device)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle device selection."""
        if isinstance(event.item, DeviceItem):
            self.dismiss(event.item.device)

    def action_help(self) -> None:
        """Show help overlay."""
        self.app.push_screen(HelpScreen())


class AppListScreen(Screen[tuple[set[str], AppAction]]):
    """Main app list screen for selecting apps and actions."""

    BINDINGS = [
        Binding("q", "back", "Back"),
        Binding("space", "toggle_selection", "Toggle", show=False),
        Binding("a", "select_all", "Select All"),
        Binding("n", "select_none", "Select None"),
        Binding("e", "enable", "Enable"),
        Binding("d", "disable", "Disable"),
        Binding("s", "toggle_system", "Toggle System"),
        Binding("?", "help", "Help"),
        Binding("tab", "focus_next", "Next", show=False),
        Binding("shift+tab", "focus_previous", "Previous", show=False),
    ]

    DEFAULT_CSS = """
    AppListScreen {
        layout: grid;
        grid-size: 1;
        grid-rows: auto 1fr auto auto;
    }

    AppListScreen > .device-panel {
        height: auto;
        margin: 1 2;
    }

    AppListScreen > .app-list-container {
        margin: 0 2;
    }

    AppListScreen > .app-list-header {
        height: 2;
        background: $surface-light;
        padding: 0 1;
        margin: 0 2;
    }

    AppListScreen > .app-list-header > Horizontal > Label {
        height: 1;
    }

    AppListScreen > .app-list-header > Horizontal > .col-select {
        width: 4;
    }

    AppListScreen > .app-list-header > Horizontal > .col-name {
        width: 1fr;
        padding-left: 1;
    }

    AppListScreen > .app-list-header > Horizontal > .col-status {
        width: 12;
        text-align: center;
    }

    AppListScreen > .app-list-header > Horizontal > .col-size {
        width: 10;
        text-align: right;
    }

    AppListScreen > .app-list-header > Horizontal > .col-type {
        width: 8;
        text-align: center;
    }

    AppListScreen > .actions {
        height: auto;
        margin: 1 2;
        padding: 1;
        border: solid $border;
        border-title-color: $primary;
    }

    AppListScreen > .actions > Horizontal {
        height: 3;
        align: center middle;
    }

    AppListScreen > .actions > Horizontal > Button {
        margin: 0 1;
    }
    """

    show_system = reactive(True)

    def __init__(
        self,
        device: DeviceInfo,
        apps: list[AppInfo],
        selected_packages: set[str] | None = None,
        name: str | None = None,
    ) -> None:
        """Initialize app list screen."""
        super().__init__(name=name)
        self.device = device
        self._all_apps = apps
        self._selected_packages = selected_packages or set()

    @property
    def visible_apps(self) -> list[AppInfo]:
        """Get visible apps based on filter."""
        if self.show_system:
            return self._all_apps
        return [a for a in self._all_apps if not a.is_system]

    def compose(self) -> ComposeResult:
        """Compose the app list screen."""
        yield Header()
        yield DeviceInfoPanel(
            device_id=self.device.device_id,
            model=self.device.model,
            manufacturer=self.device.manufacturer,
            android_version=self.device.android_version,
            sdk_level=self.device.sdk_level,
            classes="device-panel",
        )
        with Container(classes="app-list-header"), Horizontal():
            yield Label("", classes="col-select")
            yield Label("Package Name", classes="col-name")
            yield Label("Status", classes="col-status")
            yield Label("Size", classes="col-size")
            yield Label("Type", classes="col-type")
        yield AppListWidget(
            self.visible_apps,
            self._selected_packages,
            classes="app-list-container",
            id="app-list",
        )
        with Container(classes="actions"), Horizontal():
            yield Button("Enable Selected", id="btn-enable", variant="success")
            yield Button("Disable Selected", id="btn-disable", variant="error")
        yield StatusBar(id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        """Focus app list on mount."""
        self._update_status()
        with contextlib.suppress(Exception):
            self.query_one("#app-list", AppListWidget).focus()

    def _update_status(self) -> None:
        """Update status bar."""
        count = len(self._selected_packages)
        total = len(self.visible_apps)
        text = f"{'s' if self.show_system else 'S'} Toggle system apps"
        count_str = f"{count} of {total} selected"
        with contextlib.suppress(Exception):
            self.query_one("#status-bar", StatusBar).update_status(text, count_str)

    def on_app_list_widget_selection_changed(self, event: AppListWidget.SelectionChanged) -> None:
        """Handle selection changes."""
        self._selected_packages = event.selected_packages
        self._update_status()

    def action_back(self) -> None:
        """Go back to device selection."""
        self.dismiss(None)

    def action_toggle_selection(self) -> None:
        """Toggle the focused app."""
        with contextlib.suppress(Exception):
            self.query_one("#app-list", AppListWidget).toggle_focused()

    def action_select_all(self) -> None:
        """Select all visible apps."""
        with contextlib.suppress(Exception):
            self.query_one("#app-list", AppListWidget).select_all()

    def action_select_none(self) -> None:
        """Deselect all apps."""
        with contextlib.suppress(Exception):
            self.query_one("#app-list", AppListWidget).deselect_all()

    def action_toggle_system(self) -> None:
        """Toggle system apps visibility."""
        self.show_system = not self.show_system
        # Rebuild the app list
        self._rebuild_app_list()

    def _rebuild_app_list(self) -> None:
        """Rebuild the app list with current filter."""
        with contextlib.suppress(Exception):
            old_list = self.query_one("#app-list", AppListWidget)
            new_list = AppListWidget(
                self.visible_apps,
                self._selected_packages,
                classes="app-list-container",
                id="app-list",
            )
            old_list.remove()
            self.mount(new_list, before=self.query_one(".actions"))
            new_list.focus()
            self._update_status()

    def action_enable(self) -> None:
        """Start enable action for selected apps."""
        if self._selected_packages:
            self.dismiss((self._selected_packages.copy(), AppAction.ENABLE))

    def action_disable(self) -> None:
        """Start disable action for selected apps."""
        if self._selected_packages:
            self.dismiss((self._selected_packages.copy(), AppAction.DISABLE))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-enable":
            self.action_enable()
        elif event.button.id == "btn-disable":
            self.action_disable()

    def action_help(self) -> None:
        """Show help overlay."""
        self.app.push_screen(HelpScreen())


class ConfirmationScreen(Screen[bool]):
    """Confirmation dialog for enable/disable actions."""

    BINDINGS = [
        Binding("y", "confirm", "Confirm"),
        Binding("n", "cancel", "Cancel"),
        Binding("enter", "confirm", "Confirm", show=False),
        Binding("escape", "cancel", "Cancel", show=False),
        Binding("q", "cancel", "Cancel", show=False),
    ]

    DEFAULT_CSS = """
    ConfirmationScreen {
        align: center middle;
    }

    ConfirmationScreen > Container {
        width: 80;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: solid $border;
        padding: 1 2;
    }

    ConfirmationScreen > Container > .title {
        text-align: center;
        text-style: bold;
        padding: 1;
    }

    ConfirmationScreen > Container > .action-enable {
        color: $success;
    }

    ConfirmationScreen > Container > .action-disable {
        color: $error;
    }

    ConfirmationScreen > Container > .subtitle {
        text-align: center;
        color: $text-muted;
        padding-bottom: 1;
    }

    ConfirmationScreen > Container > .app-grid {
        height: auto;
        max-height: 20;
        margin: 1 0;
        padding: 1;
        border: solid $border;
    }

    ConfirmationScreen > Container > .app-grid > .app-col {
        width: 50%;
        height: auto;
    }

    ConfirmationScreen > Container > .app-grid > .app-col > Label {
        height: 1;
        padding: 0 1;
    }

    ConfirmationScreen > Container > .buttons {
        height: 3;
        align: center middle;
        margin-top: 1;
    }

    ConfirmationScreen > Container > .buttons > Button {
        margin: 0 2;
    }

    ConfirmationScreen > Container > .hint {
        text-align: center;
        color: $text-muted;
        padding-top: 1;
    }
    """

    def __init__(
        self,
        packages: set[str],
        action: AppAction,
        name: str | None = None,
    ) -> None:
        """Initialize confirmation screen."""
        super().__init__(name=name)
        self.packages = sorted(packages)
        self.action = action

    def compose(self) -> ComposeResult:
        """Compose the confirmation dialog."""
        action_str = "Enable" if self.action == AppAction.ENABLE else "Disable"
        action_class = "action-enable" if self.action == AppAction.ENABLE else "action-disable"

        with Container():
            yield Label(f"⚠️  {action_str} Apps", classes=f"title {action_class}")
            yield Label(
                f"You are about to {action_str.lower()} {len(self.packages)} app(s)",
                classes="subtitle",
            )

            # Two-column layout for packages
            with Grid(classes="app-grid"):
                mid = (len(self.packages) + 1) // 2
                with VerticalScroll(classes="app-col"):
                    for pkg in self.packages[:mid]:
                        yield Label(f"• {pkg}")
                with VerticalScroll(classes="app-col"):
                    for pkg in self.packages[mid:]:
                        yield Label(f"• {pkg}")

            with Horizontal(classes="buttons"):
                yield Button(f"Yes, {action_str}", id="btn-confirm", variant="primary")
                yield Button("Cancel", id="btn-cancel", variant="default")

            yield Label("y Confirm • n/q Cancel", classes="hint")

    def on_mount(self) -> None:
        """Focus confirm button on mount."""
        with contextlib.suppress(Exception):
            self.query_one("#btn-confirm", Button).focus()

    def action_confirm(self) -> None:
        """Confirm the action."""
        self.dismiss(True)

    def action_cancel(self) -> None:
        """Cancel the action."""
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-confirm":
            self.dismiss(True)
        elif event.button.id == "btn-cancel":
            self.dismiss(False)


class ExecutionResult:
    """Result of an app enable/disable operation."""

    def __init__(
        self,
        package_name: str,
        success: bool,
        error: str | None = None,
    ) -> None:
        """Initialize execution result."""
        self.package_name = package_name
        self.success = success
        self.error = error


class ExecutionScreen(Screen[dict[str, bool]]):
    """Execution screen with progress display."""

    BINDINGS = [
        Binding("q", "finish", "Done", show=False),
        Binding("enter", "finish", "Done", show=False),
    ]

    DEFAULT_CSS = """
    ExecutionScreen {
        align: center middle;
    }

    ExecutionScreen > Container {
        width: 80;
        height: auto;
        max-height: 90%;
        background: $surface;
        border: solid $border;
        padding: 1 2;
    }

    ExecutionScreen > Container > .title {
        text-align: center;
        text-style: bold;
        padding: 1;
    }

    ExecutionScreen > Container > .progress-section {
        height: auto;
        padding: 1;
    }

    ExecutionScreen > Container > .progress-section > .progress-label {
        text-align: center;
        padding-bottom: 1;
    }

    ExecutionScreen > Container > .progress-section > ProgressBar {
        margin: 0 2;
    }

    ExecutionScreen > Container > .current-op {
        text-align: center;
        color: $text-muted;
        padding: 1;
    }

    ExecutionScreen > Container > .results {
        height: auto;
        max-height: 15;
        border: solid $border;
        margin: 1 0;
        padding: 1;
    }

    ExecutionScreen > Container > .results > Label {
        height: 1;
    }

    ExecutionScreen > Container > .results > .result-success {
        color: $success;
    }

    ExecutionScreen > Container > .results > .result-error {
        color: $error;
    }

    ExecutionScreen > Container > .summary {
        height: auto;
        padding: 1;
        border: solid $border;
        margin-top: 1;
    }

    ExecutionScreen > Container > .summary > Horizontal {
        height: 1;
    }

    ExecutionScreen > Container > .summary > Horizontal > .label {
        width: 15;
    }

    ExecutionScreen > Container > .summary > Horizontal > .value {
        width: 1fr;
    }

    ExecutionScreen > Container > .summary > Horizontal > .success-count {
        color: $success;
    }

    ExecutionScreen > Container > .summary > Horizontal > .error-count {
        color: $error;
    }

    ExecutionScreen > Container > .done-hint {
        text-align: center;
        color: $text-muted;
        padding-top: 1;
    }

    ExecutionScreen > Container > .hidden {
        display: none;
    }
    """

    progress = reactive(0.0)
    current_package = reactive("")
    is_complete = reactive(False)

    def __init__(
        self,
        packages: list[str],
        action: AppAction,
        name: str | None = None,
    ) -> None:
        """Initialize execution screen."""
        super().__init__(name=name)
        self.packages = packages
        self.action = action
        self.results: dict[str, bool] = {}
        self.errors: dict[str, str] = {}

    def compose(self) -> ComposeResult:
        """Compose the execution screen."""
        action_str = "Enabling" if self.action == AppAction.ENABLE else "Disabling"

        with Container():
            yield Label(f"⚙️  {action_str} Apps", classes="title", id="title")

            with Vertical(classes="progress-section", id="progress-section"):
                yield Label("0 / 0", classes="progress-label", id="progress-label")
                yield ProgressBar(total=len(self.packages), id="progress-bar")

            yield Label("Starting...", classes="current-op", id="current-op")

            with VerticalScroll(classes="results", id="results"):
                pass  # Results will be added dynamically

            with Vertical(classes="summary hidden", id="summary"):
                with Horizontal():
                    yield Label("Total:", classes="label")
                    yield Label("0", classes="value", id="total-count")
                with Horizontal():
                    yield Label("Successful:", classes="label")
                    yield Label("0", classes="value success-count", id="success-count")
                with Horizontal():
                    yield Label("Failed:", classes="label")
                    yield Label("0", classes="value error-count", id="error-count")

            yield Label("Press Enter or q when done", classes="done-hint hidden", id="done-hint")

    def on_mount(self) -> None:
        """Start execution when mounted."""
        # Execution will be triggered by the main app
        pass

    def update_progress(self, completed: int, current: str) -> None:
        """Update progress display."""
        total = len(self.packages)
        self.progress = completed / total if total > 0 else 0
        self.current_package = current

        try:
            self.query_one("#progress-label", Label).update(f"{completed} / {total}")
            self.query_one("#progress-bar", ProgressBar).progress = completed
            self.query_one("#current-op", Label).update(f"Processing: {current}")
        except Exception:
            pass

    def add_result(self, package: str, success: bool, error: str | None = None) -> None:
        """Add a result to the display."""
        self.results[package] = success
        if error:
            self.errors[package] = error

        try:
            results_container = self.query_one("#results", VerticalScroll)
            if success:
                results_container.mount(Label(f"✓ {package}", classes="result-success"))
            else:
                error_text = f": {error}" if error else ""
                results_container.mount(Label(f"✗ {package}{error_text}", classes="result-error"))
            # Scroll to bottom
            results_container.scroll_end(animate=False)
        except Exception:
            pass

    def show_complete(self) -> None:
        """Show completion state."""
        self.is_complete = True

        try:
            # Update title
            action_str = "Enabled" if self.action == AppAction.ENABLE else "Disabled"
            self.query_one("#title", Label).update(f"✅ {action_str} Apps Complete")

            # Hide progress section
            self.query_one("#progress-section").add_class("hidden")
            self.query_one("#current-op").add_class("hidden")

            # Show summary
            summary = self.query_one("#summary")
            summary.remove_class("hidden")

            success_count = sum(1 for s in self.results.values() if s)
            error_count = sum(1 for s in self.results.values() if not s)

            self.query_one("#total-count", Label).update(str(len(self.results)))
            self.query_one("#success-count", Label).update(str(success_count))
            self.query_one("#error-count", Label).update(str(error_count))

            # Show done hint
            self.query_one("#done-hint").remove_class("hidden")
        except Exception:
            pass

    def action_finish(self) -> None:
        """Finish and return results."""
        if self.is_complete:
            self.dismiss(self.results)


class HelpScreen(Screen[None]):
    """Help overlay showing keybindings."""

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("q", "close", "Close"),
        Binding("?", "close", "Close"),
    ]

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }

    HelpScreen > Container {
        width: 60;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: solid $accent;
        padding: 1 2;
    }

    HelpScreen > Container > .title {
        text-align: center;
        text-style: bold;
        padding: 1;
        color: $accent;
    }

    HelpScreen > Container > .section {
        height: auto;
        padding: 1 0;
    }

    HelpScreen > Container > .section > .section-title {
        text-style: bold;
        padding-bottom: 1;
    }

    HelpScreen > Container > .section > Horizontal {
        height: 1;
    }

    HelpScreen > Container > .section > Horizontal > .key {
        width: 15;
        color: $primary;
    }

    HelpScreen > Container > .section > Horizontal > .desc {
        width: 1fr;
    }

    HelpScreen > Container > .hint {
        text-align: center;
        color: $text-muted;
        padding-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the help screen."""
        with Container():
            yield Label("⌨️  Keyboard Shortcuts", classes="title")

            with Vertical(classes="section"):
                yield Label("Navigation", classes="section-title")
                with Horizontal():
                    yield Label("↑ / ↓", classes="key")
                    yield Label("Move up/down in list", classes="desc")
                with Horizontal():
                    yield Label("Tab", classes="key")
                    yield Label("Next focus area", classes="desc")
                with Horizontal():
                    yield Label("Shift+Tab", classes="key")
                    yield Label("Previous focus area", classes="desc")
                with Horizontal():
                    yield Label("q", classes="key")
                    yield Label("Back / Quit", classes="desc")

            with Vertical(classes="section"):
                yield Label("Selection", classes="section-title")
                with Horizontal():
                    yield Label("Space / Enter", classes="key")
                    yield Label("Toggle app selection", classes="desc")
                with Horizontal():
                    yield Label("a", classes="key")
                    yield Label("Select all apps", classes="desc")
                with Horizontal():
                    yield Label("n", classes="key")
                    yield Label("Deselect all apps", classes="desc")
                with Horizontal():
                    yield Label("s", classes="key")
                    yield Label("Toggle system apps", classes="desc")

            with Vertical(classes="section"):
                yield Label("Actions", classes="section-title")
                with Horizontal():
                    yield Label("e", classes="key")
                    yield Label("Enable selected apps", classes="desc")
                with Horizontal():
                    yield Label("d", classes="key")
                    yield Label("Disable selected apps", classes="desc")
                with Horizontal():
                    yield Label("r", classes="key")
                    yield Label("Refresh device list", classes="desc")

            with Vertical(classes="section"):
                yield Label("Dialogs", classes="section-title")
                with Horizontal():
                    yield Label("y / Enter", classes="key")
                    yield Label("Confirm action", classes="desc")
                with Horizontal():
                    yield Label("n / Esc", classes="key")
                    yield Label("Cancel action", classes="desc")
                with Horizontal():
                    yield Label("?", classes="key")
                    yield Label("Show/hide this help", classes="desc")

            yield Label("Press Esc, q, or ? to close", classes="hint")

    def action_close(self) -> None:
        """Close help screen."""
        self.dismiss()
