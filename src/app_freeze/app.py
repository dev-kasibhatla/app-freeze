"""Fast, lazygit-inspired TUI for App Freeze using prompt_toolkit."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.layout import (
    ConditionalContainer,
    FormattedTextControl,
    HSplit,
    Layout,
    Window,
)
from prompt_toolkit.styles import Style

from app_freeze.adb.client import ADBClient
from app_freeze.adb.errors import ADBError, ADBNotFoundError
from app_freeze.adb.models import AppInfo, DeviceInfo
from app_freeze.reporting import OperationReport, OperationResult, ReportWriter
from app_freeze.state import AppAction

# Type alias for styled text fragments
StyleAndText = list[tuple[str, str]]

# Catppuccin Mocha color palette for fast, clean rendering
STYLE = Style.from_dict(
    {
        "header": "bg:#1e1e2e #cdd6f4 bold",
        "header.device": "#a6e3a1",
        "footer": "bg:#313244 #cdd6f4",
        "footer.key": "#f9e2af bold",
        "footer.desc": "#bac2de",
        "list": "bg:#1e1e2e #cdd6f4",
        "list.selected": "bg:#45475a #cdd6f4 bold",
        "list.cursor": "bg:#585b70 #cdd6f4",
        "app.enabled": "#a6e3a1",
        "app.disabled": "#f38ba8",
        "app.system": "#6c7086",
        "filter": "bg:#313244 #cdd6f4",
        "filter.label": "#89b4fa",
        "status": "bg:#1e1e2e #6c7086",
        "status.count": "#f9e2af bold",
        "confirm": "bg:#f38ba8 #1e1e2e bold",
        "confirm.yes": "#a6e3a1 bold",
        "error": "#f38ba8 bold",
        "success": "#a6e3a1 bold",
        "progress": "#89b4fa",
    }
)


class ViewState(Enum):
    """Current view state."""

    LOADING = auto()
    DEVICE_SELECT = auto()
    APP_LIST = auto()
    CONFIRM = auto()
    EXECUTING = auto()
    ERROR = auto()


class FilterMode(Enum):
    """App filter mode."""

    ALL = auto()
    ENABLED = auto()
    DISABLED = auto()
    USER = auto()
    SYSTEM = auto()


@dataclass
class UIState:
    """Mutable UI state for the application."""

    view: ViewState = ViewState.LOADING
    error_msg: str = ""

    # Device selection
    devices: list[DeviceInfo] = field(default_factory=list)
    device_cursor: int = 0
    selected_device: DeviceInfo | None = None

    # App list
    apps: list[AppInfo] = field(default_factory=list)
    app_cursor: int = 0
    selected_packages: set[str] = field(default_factory=set)
    filter_text: str = ""
    filter_mode: FilterMode = FilterMode.ALL
    show_filter_input: bool = False

    # Confirmation
    pending_action: AppAction | None = None

    # Execution - stores (package, success, error) tuples
    execution_progress: int = 0
    execution_total: int = 0
    execution_results: list[tuple[str, bool, str | None]] = field(default_factory=list)

    def filtered_apps(self) -> list[AppInfo]:
        """Get apps matching current filter."""
        apps = self.apps

        if self.filter_text:
            q = self.filter_text.lower()
            apps = [a for a in apps if q in a.package_name.lower()]

        if self.filter_mode == FilterMode.ENABLED:
            apps = [a for a in apps if a.is_enabled]
        elif self.filter_mode == FilterMode.DISABLED:
            apps = [a for a in apps if not a.is_enabled]
        elif self.filter_mode == FilterMode.USER:
            apps = [a for a in apps if not a.is_system]
        elif self.filter_mode == FilterMode.SYSTEM:
            apps = [a for a in apps if a.is_system]

        return apps


class AppFreezeUI:
    """Main UI controller using prompt_toolkit."""

    def __init__(self) -> None:
        self.state = UIState()
        self.adb: ADBClient | None = None
        self.report_writer = ReportWriter()
        self.filter_buffer = Buffer(on_text_changed=self._on_filter_changed)

        self.kb = self._create_keybindings()
        self.app: Application[None] = Application(
            layout=Layout(self._create_layout()),
            key_bindings=self.kb,
            style=STYLE,
            full_screen=True,
            mouse_support=True,
        )

    def _on_filter_changed(self, buf: Buffer) -> None:
        """Update filter when text changes."""
        self.state.filter_text = buf.text
        self.state.app_cursor = 0

    def _create_keybindings(self) -> KeyBindings:
        """Create all keybindings."""
        kb = KeyBindings()

        @kb.add("q")
        def quit_app(event: KeyPressEvent) -> None:
            if self.state.view == ViewState.CONFIRM:
                self.state.view = ViewState.APP_LIST
                self.state.pending_action = None
            elif self.state.show_filter_input:
                self.state.show_filter_input = False
            else:
                event.app.exit()

        @kb.add("c-c")
        def force_quit(event: KeyPressEvent) -> None:
            event.app.exit()

        @kb.add("j")
        @kb.add("down")
        def move_down(event: KeyPressEvent) -> None:
            if self.state.show_filter_input:
                return
            if self.state.view == ViewState.DEVICE_SELECT:
                self.state.device_cursor = min(
                    self.state.device_cursor + 1,
                    len(self.state.devices) - 1,
                )
            elif self.state.view == ViewState.APP_LIST:
                filtered = self.state.filtered_apps()
                self.state.app_cursor = min(
                    self.state.app_cursor + 1,
                    len(filtered) - 1,
                )

        @kb.add("k")
        @kb.add("up")
        def move_up(event: KeyPressEvent) -> None:
            if self.state.show_filter_input:
                return
            if self.state.view == ViewState.DEVICE_SELECT:
                self.state.device_cursor = max(self.state.device_cursor - 1, 0)
            elif self.state.view == ViewState.APP_LIST:
                self.state.app_cursor = max(self.state.app_cursor - 1, 0)

        @kb.add("g")
        def go_top(event: KeyPressEvent) -> None:
            if self.state.show_filter_input:
                return
            if self.state.view == ViewState.DEVICE_SELECT:
                self.state.device_cursor = 0
            elif self.state.view == ViewState.APP_LIST:
                self.state.app_cursor = 0

        @kb.add("G")
        def go_bottom(event: KeyPressEvent) -> None:
            if self.state.show_filter_input:
                return
            if self.state.view == ViewState.DEVICE_SELECT:
                self.state.device_cursor = max(0, len(self.state.devices) - 1)
            elif self.state.view == ViewState.APP_LIST:
                filtered = self.state.filtered_apps()
                self.state.app_cursor = max(0, len(filtered) - 1)

        @kb.add("enter")
        def select_item(event: KeyPressEvent) -> None:
            if self.state.view == ViewState.DEVICE_SELECT and self.state.devices:
                self._select_device(self.state.devices[self.state.device_cursor])
            elif self.state.show_filter_input:
                self.state.show_filter_input = False

        @kb.add("space")
        def toggle_selection(event: KeyPressEvent) -> None:
            if self.state.view != ViewState.APP_LIST or self.state.show_filter_input:
                return
            filtered = self.state.filtered_apps()
            if not filtered:
                return
            pkg = filtered[self.state.app_cursor].package_name
            if pkg in self.state.selected_packages:
                self.state.selected_packages.discard(pkg)
            else:
                self.state.selected_packages.add(pkg)

        @kb.add("a")
        def select_all(event: KeyPressEvent) -> None:
            if self.state.view != ViewState.APP_LIST or self.state.show_filter_input:
                return
            for app in self.state.filtered_apps():
                self.state.selected_packages.add(app.package_name)

        @kb.add("n")
        def select_none(event: KeyPressEvent) -> None:
            if self.state.view != ViewState.APP_LIST or self.state.show_filter_input:
                return
            self.state.selected_packages.clear()

        @kb.add("/")
        def start_filter(event: KeyPressEvent) -> None:
            if self.state.view == ViewState.APP_LIST:
                self.state.show_filter_input = True
                event.app.layout.focus(self.filter_buffer)

        @kb.add("escape")
        def cancel_filter(event: KeyPressEvent) -> None:
            if self.state.show_filter_input:
                self.state.show_filter_input = False
                self.filter_buffer.reset()
                self.state.filter_text = ""

        @kb.add("e")
        def filter_enabled(event: KeyPressEvent) -> None:
            if self.state.view != ViewState.APP_LIST or self.state.show_filter_input:
                return
            self.state.filter_mode = (
                FilterMode.ALL
                if self.state.filter_mode == FilterMode.ENABLED
                else FilterMode.ENABLED
            )
            self.state.app_cursor = 0

        @kb.add("d")
        def filter_disabled(event: KeyPressEvent) -> None:
            if self.state.view != ViewState.APP_LIST or self.state.show_filter_input:
                return
            self.state.filter_mode = (
                FilterMode.ALL
                if self.state.filter_mode == FilterMode.DISABLED
                else FilterMode.DISABLED
            )
            self.state.app_cursor = 0

        @kb.add("u")
        def filter_user(event: KeyPressEvent) -> None:
            if self.state.view != ViewState.APP_LIST or self.state.show_filter_input:
                return
            self.state.filter_mode = (
                FilterMode.ALL if self.state.filter_mode == FilterMode.USER else FilterMode.USER
            )
            self.state.app_cursor = 0

        @kb.add("s")
        def filter_system(event: KeyPressEvent) -> None:
            if self.state.view != ViewState.APP_LIST or self.state.show_filter_input:
                return
            self.state.filter_mode = (
                FilterMode.ALL if self.state.filter_mode == FilterMode.SYSTEM else FilterMode.SYSTEM
            )
            self.state.app_cursor = 0

        @kb.add("D")
        def disable_action(event: KeyPressEvent) -> None:
            if self.state.view != ViewState.APP_LIST or self.state.show_filter_input:
                return
            if not self.state.selected_packages:
                return
            self.state.pending_action = AppAction.DISABLE
            self.state.view = ViewState.CONFIRM

        @kb.add("E")
        def enable_action(event: KeyPressEvent) -> None:
            if self.state.view != ViewState.APP_LIST or self.state.show_filter_input:
                return
            if not self.state.selected_packages:
                return
            self.state.pending_action = AppAction.ENABLE
            self.state.view = ViewState.CONFIRM

        @kb.add("y")
        def confirm_yes(event: KeyPressEvent) -> None:
            if self.state.view == ViewState.CONFIRM:
                self._execute_action()

        @kb.add("N")
        def confirm_no(event: KeyPressEvent) -> None:
            if self.state.view == ViewState.CONFIRM:
                self.state.view = ViewState.APP_LIST
                self.state.pending_action = None

        return kb

    def _create_layout(self) -> HSplit:
        """Create the main layout."""
        return HSplit(
            [
                Window(
                    FormattedTextControl(self._get_header),
                    height=1,
                    style="class:header",
                ),
                Window(
                    FormattedTextControl(self._get_content),
                    style="class:list",
                ),
                ConditionalContainer(
                    Window(
                        FormattedTextControl(self._get_filter_bar),
                        height=1,
                        style="class:filter",
                    ),
                    filter=Condition(
                        lambda: self.state.show_filter_input or bool(self.state.filter_text)
                    ),
                ),
                Window(
                    FormattedTextControl(self._get_footer),
                    height=1,
                    style="class:footer",
                ),
            ]
        )

    def _get_header(self) -> StyleAndText:
        """Generate header text."""
        if self.state.view == ViewState.LOADING:
            return [("class:header", " App Freeze — Loading...")]

        if self.state.view == ViewState.DEVICE_SELECT:
            return [("class:header", " App Freeze — Select Device")]

        if self.state.selected_device:
            dev = self.state.selected_device
            name = dev.display_name or dev.device_id
            return [
                ("class:header", " App Freeze — "),
                ("class:header.device", f"{name}"),
                ("class:header", f" ({dev.device_id})"),
            ]

        return [("class:header", " App Freeze")]

    def _get_content(self) -> StyleAndText:
        """Generate main content based on current view."""
        if self.state.view == ViewState.LOADING:
            return [("", "\n  Loading...")]

        if self.state.view == ViewState.ERROR:
            return [
                ("class:error", f"\n  ✗ Error: {self.state.error_msg}\n\n"),
                ("", "  Press q to quit"),
            ]

        if self.state.view == ViewState.DEVICE_SELECT:
            return self._render_device_list()

        if self.state.view in (ViewState.APP_LIST, ViewState.CONFIRM):
            return self._render_app_list()

        if self.state.view == ViewState.EXECUTING:
            return self._render_execution()

        return []

    def _render_device_list(self) -> StyleAndText:
        """Render device selection list."""
        result: StyleAndText = [("", "\n")]

        if not self.state.devices:
            result.append(("class:error", "  No devices found.\n"))
            result.append(("", "  Connect a device and restart."))
            return result

        for i, dev in enumerate(self.state.devices):
            is_cursor = i == self.state.device_cursor
            prefix = "❯ " if is_cursor else "  "
            style = "class:list.cursor" if is_cursor else ""

            name = dev.display_name or dev.device_id
            info = f" (Android {dev.android_version})" if dev.android_version else ""

            result.append((style, f"{prefix}{name}{info}\n"))
            result.append((style, f"    ID: {dev.device_id}\n"))
            result.append(("", "\n"))

        return result

    def _render_app_list(self) -> StyleAndText:
        """Render app list with selection."""
        result: StyleAndText = [("", "\n")]
        filtered = self.state.filtered_apps()

        mode_str = self.state.filter_mode.name.lower()
        result.append(("class:status", f"  Showing: {mode_str}"))
        result.append(("class:status.count", f" ({len(filtered)} apps)\n"))
        result.append(("", "  " + "─" * 70 + "\n"))

        if not filtered:
            result.append(("", "\n  No apps match filter."))
            return result

        # Visible window around cursor
        visible = 15
        start = max(0, self.state.app_cursor - visible // 2)
        end = min(len(filtered), start + visible)
        start = max(0, end - visible)

        if start > 0:
            result.append(("class:status", "  ↑ more above\n"))

        for i in range(start, end):
            app = filtered[i]
            is_cursor = i == self.state.app_cursor
            is_selected = app.package_name in self.state.selected_packages

            if is_cursor and is_selected:
                prefix = "❯●"
            elif is_cursor:
                prefix = "❯ "
            elif is_selected:
                prefix = " ●"
            else:
                prefix = "  "

            state = ("class:app.enabled", "✓") if app.is_enabled else ("class:app.disabled", "✗")
            sys_marker = ("class:app.system", " [S]") if app.is_system else ("", "    ")
            size_str = f"{app.size_mb:>6.1f}MB" if app.size_mb > 0 else "       -"
            pkg_name = app.package_name[:45].ljust(45)

            row_style = (
                "class:list.cursor" if is_cursor else ("class:list.selected" if is_selected else "")
            )

            result.append((row_style, f"  {prefix} "))
            result.append(state)
            result.append(sys_marker)
            result.append((row_style, f" {pkg_name} {size_str}\n"))

        if end < len(filtered):
            result.append(("class:status", "  ↓ more below\n"))

        return result

    def _render_execution(self) -> StyleAndText:
        """Render execution progress."""
        result: StyleAndText = [("", "\n")]

        action = "Disabling" if self.state.pending_action == AppAction.DISABLE else "Enabling"
        progress = self.state.execution_progress
        total = self.state.execution_total

        result.append(("class:progress", f"  {action} apps... {progress}/{total}\n\n"))

        for pkg, success, error in self.state.execution_results[-10:]:
            if success:
                result.append(("class:success", f"  ✓ {pkg}\n"))
            else:
                result.append(("class:error", f"  ✗ {pkg}: {error}\n"))

        return result

    def _get_filter_bar(self) -> StyleAndText:
        """Generate filter bar."""
        text = self.state.filter_text or ""
        return [
            ("class:filter.label", " /"),
            ("class:filter", f" {text}"),
            ("class:filter", " " * 50),
        ]

    def _get_footer(self) -> StyleAndText:
        """Generate footer with context-sensitive keybindings."""
        if self.state.view == ViewState.CONFIRM:
            action = "Disable" if self.state.pending_action == AppAction.DISABLE else "Enable"
            count = len(self.state.selected_packages)
            return [
                ("class:confirm", f" {action} {count} app(s)? "),
                ("class:confirm.yes", "[y]"),
                ("class:footer.desc", "es "),
                ("class:footer.key", "[q]"),
                ("class:footer.desc", "cancel "),
            ]

        if self.state.view == ViewState.DEVICE_SELECT:
            return [
                ("class:footer.key", " [↑↓]"),
                ("class:footer.desc", "nav "),
                ("class:footer.key", "[enter]"),
                ("class:footer.desc", "select "),
                ("class:footer.key", "[q]"),
                ("class:footer.desc", "quit "),
            ]

        if self.state.view == ViewState.APP_LIST:
            selected = len(self.state.selected_packages)
            return [
                ("class:footer.key", " [jk/↑↓]"),
                ("class:footer.desc", "nav "),
                ("class:footer.key", "[space]"),
                ("class:footer.desc", "toggle "),
                ("class:footer.key", "[/]"),
                ("class:footer.desc", "filter "),
                ("class:footer.key", "[D]"),
                ("class:footer.desc", "disable "),
                ("class:footer.key", "[E]"),
                ("class:footer.desc", "enable "),
                ("class:footer.key", "[q]"),
                ("class:footer.desc", "quit "),
                ("class:status.count", f" | {selected} selected"),
            ]

        return [("class:footer", " Press q to quit")]

    def _select_device(self, device: DeviceInfo) -> None:
        """Handle device selection and load apps."""
        self.state.selected_device = device
        self.state.view = ViewState.LOADING

        try:
            if self.adb:
                self.state.apps = self.adb.list_apps(
                    device.device_id,
                    include_system=True,
                    include_user=True,
                    fetch_sizes=True,
                )
                self.state.view = ViewState.APP_LIST
        except ADBError as e:
            self.state.error_msg = str(e)
            self.state.view = ViewState.ERROR

    def _execute_action(self) -> None:
        """Execute the pending enable/disable action."""
        if not self.adb or not self.state.selected_device or not self.state.pending_action:
            return

        self.state.view = ViewState.EXECUTING
        self.state.execution_results = []
        packages = list(self.state.selected_packages)
        self.state.execution_total = len(packages)
        self.state.execution_progress = 0

        device_id = self.state.selected_device.device_id
        action = self.state.pending_action

        for pkg in packages:
            try:
                if action == AppAction.DISABLE:
                    success, msg = self.adb.disable_app(device_id, pkg)
                else:
                    success, msg = self.adb.enable_app(device_id, pkg)

                error = None if success else msg
                self.state.execution_results.append((pkg, success, error))
            except ADBError as e:
                self.state.execution_results.append((pkg, False, str(e)))

            self.state.execution_progress += 1
            self.app.invalidate()

        # Write report
        if self.state.selected_device:
            report_results = [
                OperationResult(package=pkg, success=success, error=error)
                for pkg, success, error in self.state.execution_results
            ]
            report = OperationReport(
                device=self.state.selected_device,
                action=action,
                timestamp=datetime.now(),
                results=report_results,
            )
            self.report_writer.write_report(report)

        self._reload_apps()
        self.state.selected_packages.clear()
        self.state.pending_action = None
        self.state.view = ViewState.APP_LIST

    def _reload_apps(self) -> None:
        """Reload app list after changes."""
        if not self.adb or not self.state.selected_device:
            return

        import contextlib

        with contextlib.suppress(ADBError):
            self.state.apps = self.adb.list_apps(
                self.state.selected_device.device_id,
                include_system=True,
                include_user=True,
                fetch_sizes=True,
            )

    def run(self) -> None:
        """Run the application."""
        try:
            self.adb = ADBClient()
            devices = self.adb.get_ready_devices()

            detailed: list[DeviceInfo] = []
            for dev in devices:
                try:
                    detailed.append(self.adb.get_device_info(dev.device_id))
                except Exception:
                    detailed.append(dev)

            self.state.devices = detailed

            if len(detailed) == 1:
                self._select_device(detailed[0])
            elif detailed:
                self.state.view = ViewState.DEVICE_SELECT
            else:
                self.state.error_msg = "No devices connected"
                self.state.view = ViewState.ERROR

        except ADBNotFoundError:
            self.state.error_msg = "ADB not found. Install Android SDK and add to PATH."
            self.state.view = ViewState.ERROR
        except ADBError as e:
            self.state.error_msg = str(e)
            self.state.view = ViewState.ERROR

        self.app.run()


def main() -> None:
    """Main entry point."""
    ui = AppFreezeUI()
    ui.run()


if __name__ == "__main__":
    main()
