"""Fast, lazygit-inspired TUI for App Freeze using prompt_toolkit."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import TYPE_CHECKING

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.layout import (
    BufferControl,
    FormattedTextControl,
    HSplit,
    Layout,
    VSplit,
    Window,
)
from prompt_toolkit.styles import Style

from app_freeze.adb.client import ADBClient
from app_freeze.adb.errors import ADBError, ADBNotFoundError
from app_freeze.adb.models import AppInfo, DeviceInfo
from app_freeze.reporting import OperationReport, OperationResult, ReportWriter
from app_freeze.state import AppAction

if TYPE_CHECKING:
    pass

# Type alias for styled text fragments
StyleAndText = list[tuple[str, str]]

# ─────────────────────────────────────────────────────────────────────────────
# Styles - Catppuccin Mocha palette
# ─────────────────────────────────────────────────────────────────────────────

STYLE = Style.from_dict(
    {
        "header": "bg:#1e1e2e #cdd6f4 bold",
        "header.device": "#a6e3a1 bold",
        "device-info": "bg:#313244 #cdd6f4",
        "device-info.label": "#89b4fa",
        "device-info.value": "#cdd6f4 bold",
        "footer": "bg:#313244 #cdd6f4",
        "footer.key": "#f9e2af bold",
        "footer.desc": "#bac2de",
        "list": "#cdd6f4",
        "list.selected": "bg:#45475a #cdd6f4 bold",
        "list.cursor": "bg:#585b70 #cdd6f4",
        "app.enabled": "#a6e3a1",
        "app.disabled": "#f38ba8",
        "app.system": "#6c7086",
        "tabs": "bg:#313244 #6c7086",
        "tabs.active": "bg:#45475a #cdd6f4 bold",
        "tabs.key": "#f9e2af bold",
        "filter": "bg:#313244 #cdd6f4",
        "filter.label": "#89b4fa bold",
        "summary": "bg:#1e1e2e #6c7086",
        "summary.count": "#f9e2af bold",
        "confirm": "bg:#f38ba8 #1e1e2e bold",
        "confirm.yes": "#a6e3a1 bold",
        "error": "#f38ba8 bold",
        "success": "#a6e3a1 bold",
        "progress": "#89b4fa",
        "result-log": "#cdd6f4",
        "result-log.title": "#89b4fa bold",
    }
)


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────


class ViewState(Enum):
    """Current view state."""

    LOADING = auto()
    DEVICE_SELECT = auto()
    APP_LIST = auto()
    CONFIRM = auto()
    EXECUTING = auto()
    RESULT = auto()  # Shows result log after action
    ERROR = auto()


class FilterMode(Enum):
    """App filter mode (tabs)."""

    ALL = auto()
    USER = auto()
    SYSTEM = auto()
    ENABLED = auto()
    DISABLED = auto()


# ─────────────────────────────────────────────────────────────────────────────
# State
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class UIState:
    """Mutable UI state for the application."""

    view: ViewState = ViewState.LOADING
    error_msg: str = ""
    loading_status: str = ""  # Status message during loading

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

    # Confirmation
    pending_action: AppAction | None = None

    # Execution results
    execution_progress: int = 0
    execution_total: int = 0
    execution_current: str = ""  # Current package being processed
    execution_results: list[tuple[str, bool, str | None]] = field(default_factory=list)

    def filtered_apps(self) -> list[AppInfo]:
        """Get apps matching current filter."""
        apps = self.apps

        # Text filter
        if self.filter_text:
            q = self.filter_text.lower()
            apps = [a for a in apps if q in a.package_name.lower()]

        # Mode filter
        if self.filter_mode == FilterMode.ENABLED:
            apps = [a for a in apps if a.is_enabled]
        elif self.filter_mode == FilterMode.DISABLED:
            apps = [a for a in apps if not a.is_enabled]
        elif self.filter_mode == FilterMode.USER:
            apps = [a for a in apps if not a.is_system]
        elif self.filter_mode == FilterMode.SYSTEM:
            apps = [a for a in apps if a.is_system]

        return apps

    def get_stats(self) -> dict[str, int]:
        """Get app statistics."""
        total = len(self.apps)
        system = sum(1 for a in self.apps if a.is_system)
        user = total - system
        enabled = sum(1 for a in self.apps if a.is_enabled)
        disabled = total - enabled
        return {
            "total": total,
            "system": system,
            "user": user,
            "enabled": enabled,
            "disabled": disabled,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Renderers - Each function renders a piece of UI
# ─────────────────────────────────────────────────────────────────────────────


def render_header(state: UIState) -> StyleAndText:
    """Render header bar with stylish title."""
    if state.view == ViewState.LOADING:
        return [
            ("class:header", "⚡ App Freeze"),
            ("class:header", "\n"),
            ("class:header.device", "Loading..."),
        ]
    if state.view == ViewState.DEVICE_SELECT:
        return [
            ("class:header", "📱 Select Device"),
            ("class:header", "\n"),
            ("class:header.device", "Choose a connected Android device"),
        ]
    if state.selected_device:
        dev = state.selected_device
        name = dev.display_name or dev.device_id
        return [
            ("class:header", "⚡ App Freeze"),
            ("class:header", "\n"),
            ("class:header.device", f"on {name}"),
        ]
    return [
        ("class:header", "⚡ App Freeze"),
        ("class:header", "\n"),
    ]


def render_device_info(state: UIState) -> StyleAndText:
    """Render compact device info widget."""
    if not state.selected_device:
        return []

    dev = state.selected_device
    result: StyleAndText = []

    # Line: Model • Android version • Device ID
    model = dev.model or dev.device_id
    android = dev.android_version or "?"
    result.append(("class:device-info.label", " 📱 "))
    result.append(("class:device-info.value", f"{model}"))
    result.append(("class:device-info", f" • Android {android}"))
    result.append(("class:device-info", f" • {dev.device_id}"))

    return result


def render_summary(state: UIState) -> StyleAndText:
    """Render app statistics summary."""
    stats = state.get_stats()
    result: StyleAndText = [("class:summary", " ")]
    result.append(("class:summary.count", f"{stats['total']}"))
    result.append(("class:summary", " apps │ "))
    result.append(("class:summary.count", f"{stats['user']}"))
    result.append(("class:summary", " user │ "))
    result.append(("class:summary.count", f"{stats['system']}"))
    result.append(("class:summary", " system │ "))
    result.append(("class:app.enabled", f"{stats['enabled']}"))
    result.append(("class:summary", " enabled │ "))
    result.append(("class:app.disabled", f"{stats['disabled']}"))
    result.append(("class:summary", " disabled"))
    return result


def render_tabs(state: UIState) -> StyleAndText:
    """Render filter mode tabs."""
    modes = [
        (FilterMode.ALL, "1", "All"),
        (FilterMode.USER, "2", "User"),
        (FilterMode.SYSTEM, "3", "System"),
        (FilterMode.ENABLED, "4", "Enabled"),
        (FilterMode.DISABLED, "5", "Disabled"),
    ]
    result: StyleAndText = [("class:tabs", " ")]
    for mode, key, label in modes:
        is_active = state.filter_mode == mode
        style = "class:tabs.active" if is_active else "class:tabs"
        result.append(("class:tabs.key", f"[{key}]"))
        result.append((style, f"{label} "))
    return result


def render_device_list(state: UIState) -> StyleAndText:
    """Render device selection list."""
    result: StyleAndText = [("", "\n")]
    if not state.devices:
        result.append(("class:error", "  No devices found.\n"))
        result.append(("", "  Connect a device and restart.\n"))
        return result

    for i, dev in enumerate(state.devices):
        is_cursor = i == state.device_cursor
        prefix = "❯ " if is_cursor else "  "
        style = "class:list.cursor" if is_cursor else ""

        name = dev.display_name or dev.device_id
        info = f" (Android {dev.android_version})" if dev.android_version else ""
        result.append((style, f"{prefix}{name}{info}\n"))
        result.append((style, f"    ID: {dev.device_id}\n\n"))

    return result


def render_app_list(state: UIState, height: int = 20) -> StyleAndText:
    """Render app list with cursor and selection."""
    result: StyleAndText = []
    filtered = state.filtered_apps()

    # Show current filter and count
    mode_str = state.filter_mode.name.lower()
    result.append(("class:summary", f" Showing: {mode_str} "))
    result.append(("class:summary.count", f"({len(filtered)} apps)"))
    if state.filter_text:
        result.append(("class:filter.label", f" filter: '{state.filter_text}'"))
    result.append(("", "\n"))
    result.append(("", " " + "─" * 72 + "\n"))

    if not filtered:
        result.append(("", "\n  No apps match filter.\n"))
        return result

    # Adaptive visible window - use available height minus header/footer
    visible = max(5, height - 8)
    start = max(0, state.app_cursor - visible // 2)
    end = min(len(filtered), start + visible)
    start = max(0, end - visible)

    if start > 0:
        result.append(("class:summary", f" ↑ {start} more above\n"))

    for i in range(start, end):
        app = filtered[i]
        is_cursor = i == state.app_cursor
        is_selected = app.package_name in state.selected_packages

        # Prefix: cursor and selection markers
        if is_cursor and is_selected:
            prefix = "❯●"
        elif is_cursor:
            prefix = "❯ "
        elif is_selected:
            prefix = " ●"
        else:
            prefix = "  "

        # Status indicator
        state_style = "class:app.enabled" if app.is_enabled else "class:app.disabled"
        state_char = "✓" if app.is_enabled else "✗"

        # System marker
        sys_marker = (" [S]", "class:app.system") if app.is_system else ("    ", "")

        # Size
        size_str = f"{app.size_mb:>6.1f}MB" if app.size_mb > 0 else "      -"

        # Package name - truncate to fit
        pkg_name = app.package_name[:50].ljust(50)

        # Row style
        if is_cursor:
            row_style = "class:list.cursor"
        elif is_selected:
            row_style = "class:list.selected"
        else:
            row_style = ""

        result.append((row_style, f" {prefix} "))
        result.append((state_style, state_char))
        result.append((sys_marker[1] if sys_marker[1] else row_style, sys_marker[0]))
        result.append((row_style, f" {pkg_name} {size_str}\n"))

    remaining = len(filtered) - end
    if remaining > 0:
        result.append(("class:summary", f" ↓ {remaining} more below\n"))

    return result


def render_confirm(state: UIState) -> StyleAndText:
    """Render confirmation dialog inline."""
    result: StyleAndText = [("", "\n")]
    action = "DISABLE" if state.pending_action == AppAction.DISABLE else "ENABLE"
    count = len(state.selected_packages)

    result.append(("class:confirm", f"  {action} {count} app(s)?\n\n"))

    # List affected packages
    for pkg in sorted(state.selected_packages)[:10]:
        result.append(("", f"    • {pkg}\n"))
    if count > 10:
        result.append(("class:summary", f"    ... and {count - 10} more\n"))

    result.append(("", "\n"))
    result.append(("", "  Press "))
    result.append(("class:confirm.yes", "[y]"))
    result.append(("", " to confirm or "))
    result.append(("class:footer.key", "[q]"))
    result.append(("", " to cancel\n"))

    return result


def render_execution(state: UIState) -> StyleAndText:
    """Render execution progress."""
    result: StyleAndText = [("", "\n")]
    action = "Disabling" if state.pending_action == AppAction.DISABLE else "Enabling"
    progress = state.execution_progress
    total = state.execution_total

    # Progress bar
    bar_width = 40
    filled = int(bar_width * progress / total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_width - filled)

    result.append(("class:progress", f"  {action} apps...\n\n"))
    result.append(("class:progress", f"  [{bar}] {progress}/{total}\n"))

    # Current package being processed
    if state.execution_current:
        result.append(("class:filter.label", "\n  ⚡ Processing: "))
        result.append(("class:progress", f"{state.execution_current}\n"))

    result.append(("", "\n"))

    # Recent results
    for pkg, success, error in state.execution_results[-6:]:
        if success:
            result.append(("class:success", f"  ✓ {pkg}\n"))
        else:
            result.append(("class:error", f"  ✗ {pkg}: {error}\n"))

    return result


def render_result(state: UIState) -> StyleAndText:
    """Render result log after action completion."""
    result: StyleAndText = [("", "\n")]
    action = "Disabled" if state.pending_action == AppAction.DISABLE else "Enabled"

    # Count results
    success_count = sum(1 for _, s, _ in state.execution_results if s)
    fail_count = len(state.execution_results) - success_count

    result.append(("class:result-log.title", f"  ═══ {action} Results ═══\n\n"))
    result.append(("class:success", f"  ✓ Success: {success_count}\n"))
    result.append(("class:error", f"  ✗ Failed:  {fail_count}\n"))
    result.append(("", "\n"))

    # Details
    result.append(("class:result-log.title", "  Details:\n"))
    for pkg, success, error in state.execution_results:
        if success:
            result.append(("class:success", f"    ✓ {pkg}\n"))
        else:
            result.append(("class:error", f"    ✗ {pkg}: {error}\n"))

    result.append(("", "\n"))
    result.append(("class:summary", "  Report saved to reports/ folder\n"))
    result.append(("", "\n  Press "))
    result.append(("class:footer.key", "[enter]"))
    result.append(("", " or "))
    result.append(("class:footer.key", "[q]"))
    result.append(("", " to continue\n"))

    return result


def render_error(state: UIState) -> StyleAndText:
    """Render error message."""
    return [
        ("", "\n"),
        ("class:error", f"  ✗ Error: {state.error_msg}\n\n"),
        ("", "  Press "),
        ("class:footer.key", "[q]"),
        ("", " to quit\n"),
    ]


def render_footer(state: UIState) -> StyleAndText:
    """Render context-sensitive footer keybindings."""
    if state.view == ViewState.CONFIRM:
        return [
            ("class:footer.key", " [y]"),
            ("class:footer.desc", "confirm "),
            ("class:footer.key", "[q]"),
            ("class:footer.desc", "cancel "),
        ]

    if state.view == ViewState.RESULT:
        return [
            ("class:footer.key", " [enter/q]"),
            ("class:footer.desc", "continue "),
        ]

    if state.view == ViewState.DEVICE_SELECT:
        return [
            ("class:footer.key", " [j/k]"),
            ("class:footer.desc", "navigate "),
            ("class:footer.key", "[enter]"),
            ("class:footer.desc", "select "),
            ("class:footer.key", "[q]"),
            ("class:footer.desc", "quit "),
        ]

    if state.view == ViewState.APP_LIST:
        selected = len(state.selected_packages)
        return [
            ("class:footer.key", " [j/k]"),
            ("class:footer.desc", "nav "),
            ("class:footer.key", "[space]"),
            ("class:footer.desc", "sel "),
            ("class:footer.key", "[/]"),
            ("class:footer.desc", "search "),
            ("class:footer.key", "[1-5]"),
            ("class:footer.desc", "tabs "),
            ("class:footer.key", "[D]"),
            ("class:footer.desc", "disable "),
            ("class:footer.key", "[E]"),
            ("class:footer.desc", "enable "),
            ("class:footer.key", "[q]"),
            ("class:footer.desc", "quit "),
            ("class:summary.count", f"│ {selected} sel"),
        ]

    return [("class:footer", " Press q to quit")]


# ─────────────────────────────────────────────────────────────────────────────
# Main UI Controller
# ─────────────────────────────────────────────────────────────────────────────


class AppFreezeUI:
    """Main UI controller using prompt_toolkit."""

    def __init__(self) -> None:
        self.state = UIState()
        self.adb: ADBClient | None = None
        self.report_writer = ReportWriter()

        # Filter input buffer - control visibility via state
        self.filter_buffer = Buffer(on_text_changed=self._on_filter_changed)
        self.filter_visible = False

        self.kb = self._create_keybindings()
        self.app: Application[None] = Application(
            layout=Layout(self._create_layout()),
            key_bindings=self.kb,
            style=STYLE,
            full_screen=True,
            mouse_support=True,
        )

    def _on_filter_changed(self, buf: Buffer) -> None:
        """Update filter text from buffer."""
        self.state.filter_text = buf.text
        self.state.app_cursor = 0

    def _create_keybindings(self) -> KeyBindings:
        """Create all keybindings."""
        kb = KeyBindings()

        # ─── Quit / Cancel ─────────────────────────────────────────────────
        @kb.add("q")
        def quit_or_cancel(event: KeyPressEvent) -> None:
            if self.filter_visible:
                self._close_filter()
            elif self.state.view in (ViewState.CONFIRM, ViewState.RESULT):
                self.state.view = ViewState.APP_LIST
                self.state.pending_action = None
            else:
                event.app.exit()

        @kb.add("c-c")
        def force_quit(event: KeyPressEvent) -> None:
            event.app.exit()

        # ─── Navigation ────────────────────────────────────────────────────
        @kb.add("j")
        @kb.add("down")
        def move_down(event: KeyPressEvent) -> None:
            if self.filter_visible:
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
                    max(0, len(filtered) - 1),
                )

        @kb.add("k")
        @kb.add("up")
        def move_up(event: KeyPressEvent) -> None:
            if self.filter_visible:
                return
            if self.state.view == ViewState.DEVICE_SELECT:
                self.state.device_cursor = max(self.state.device_cursor - 1, 0)
            elif self.state.view == ViewState.APP_LIST:
                self.state.app_cursor = max(self.state.app_cursor - 1, 0)

        @kb.add("g")
        def go_top(event: KeyPressEvent) -> None:
            if self.filter_visible:
                return
            self.state.app_cursor = 0
            self.state.device_cursor = 0

        @kb.add("G")
        def go_bottom(event: KeyPressEvent) -> None:
            if self.filter_visible:
                return
            if self.state.view == ViewState.DEVICE_SELECT:
                self.state.device_cursor = max(0, len(self.state.devices) - 1)
            elif self.state.view == ViewState.APP_LIST:
                filtered = self.state.filtered_apps()
                self.state.app_cursor = max(0, len(filtered) - 1)

        # ─── Selection ─────────────────────────────────────────────────────
        @kb.add("enter")
        def select_item(event: KeyPressEvent) -> None:
            if self.filter_visible:
                self._close_filter()
            elif self.state.view == ViewState.DEVICE_SELECT and self.state.devices:
                self._select_device(self.state.devices[self.state.device_cursor])
            elif self.state.view == ViewState.RESULT:
                self.state.view = ViewState.APP_LIST
                self.state.pending_action = None

        @kb.add("space")
        def toggle_selection(event: KeyPressEvent) -> None:
            if self.state.view != ViewState.APP_LIST or self.filter_visible:
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
            if self.state.view != ViewState.APP_LIST or self.filter_visible:
                return
            for app in self.state.filtered_apps():
                self.state.selected_packages.add(app.package_name)

        @kb.add("n")
        def select_none(event: KeyPressEvent) -> None:
            if self.state.view != ViewState.APP_LIST or self.filter_visible:
                return
            self.state.selected_packages.clear()

        # ─── Filter / Search ───────────────────────────────────────────────
        @kb.add("/")
        def start_filter(event: KeyPressEvent) -> None:
            if self.state.view == ViewState.APP_LIST and not self.filter_visible:
                self.filter_visible = True
                self.app.invalidate()

        @kb.add("escape")
        def cancel_filter(event: KeyPressEvent) -> None:
            if self.filter_visible:
                self.filter_buffer.reset()
                self.state.filter_text = ""
                self._close_filter()

        # ─── Tab Filters (1-5) ─────────────────────────────────────────────
        @kb.add("1")
        def tab_all(event: KeyPressEvent) -> None:
            if self.state.view == ViewState.APP_LIST and not self.filter_visible:
                self.state.filter_mode = FilterMode.ALL
                self.state.app_cursor = 0

        @kb.add("2")
        def tab_user(event: KeyPressEvent) -> None:
            if self.state.view == ViewState.APP_LIST and not self.filter_visible:
                self.state.filter_mode = FilterMode.USER
                self.state.app_cursor = 0

        @kb.add("3")
        def tab_system(event: KeyPressEvent) -> None:
            if self.state.view == ViewState.APP_LIST and not self.filter_visible:
                self.state.filter_mode = FilterMode.SYSTEM
                self.state.app_cursor = 0

        @kb.add("4")
        def tab_enabled(event: KeyPressEvent) -> None:
            if self.state.view == ViewState.APP_LIST and not self.filter_visible:
                self.state.filter_mode = FilterMode.ENABLED
                self.state.app_cursor = 0

        @kb.add("5")
        def tab_disabled(event: KeyPressEvent) -> None:
            if self.state.view == ViewState.APP_LIST and not self.filter_visible:
                self.state.filter_mode = FilterMode.DISABLED
                self.state.app_cursor = 0

        # ─── Actions ───────────────────────────────────────────────────────
        @kb.add("D")
        def disable_action(event: KeyPressEvent) -> None:
            if self.state.view != ViewState.APP_LIST or self.filter_visible:
                return
            if not self.state.selected_packages:
                return
            self.state.pending_action = AppAction.DISABLE
            self.state.view = ViewState.CONFIRM

        @kb.add("E")
        def enable_action(event: KeyPressEvent) -> None:
            if self.state.view != ViewState.APP_LIST or self.filter_visible:
                return
            if not self.state.selected_packages:
                return
            self.state.pending_action = AppAction.ENABLE
            self.state.view = ViewState.CONFIRM

        @kb.add("y")
        def confirm_yes(event: KeyPressEvent) -> None:
            if self.state.view == ViewState.CONFIRM:
                # Run action in background thread to keep UI responsive
                action_thread = threading.Thread(target=self._execute_action, daemon=True)
                action_thread.start()

        return kb

    def _close_filter(self) -> None:
        """Close filter input."""
        self.filter_visible = False
        self.app.invalidate()

    def _create_layout(self) -> HSplit:
        """Create the main layout with responsive content."""
        # Main content area - uses all available space
        content_window = Window(
            FormattedTextControl(self._get_content),
            style="class:list",
            wrap_lines=False,
        )

        # Filter input bar with buffer control
        filter_bar = VSplit(
            [
                Window(
                    FormattedTextControl(lambda: [("class:filter.label", " / ")]),
                    width=3,
                    style="class:filter",
                ),
                Window(
                    BufferControl(buffer=self.filter_buffer),
                    style="class:filter",
                ),
            ],
            height=1,
        )

        return HSplit(
            [
                # Header - slightly taller for better visual hierarchy
                Window(
                    FormattedTextControl(lambda: render_header(self.state)),
                    height=2,
                    style="class:header",
                ),
                # Device info bar
                Window(
                    FormattedTextControl(self._get_device_bar),
                    height=1,
                    style="class:device-info",
                ),
                # Tabs bar
                Window(
                    FormattedTextControl(self._get_tabs_bar),
                    height=1,
                    style="class:tabs",
                ),
                # Summary stats bar
                Window(
                    FormattedTextControl(self._get_summary_bar),
                    height=1,
                    style="class:summary",
                ),
                # Main content area - grows to fill space
                content_window,
                # Filter input bar
                filter_bar,
                # Footer
                Window(
                    FormattedTextControl(lambda: render_footer(self.state)),
                    height=1,
                    style="class:footer",
                ),
                # Loading status - only shown during loading
                Window(
                    FormattedTextControl(self._get_loading_status),
                    height=1,
                    style="class:progress",
                ),
            ]
        )

    def _get_device_bar(self) -> StyleAndText:
        """Get device info bar content."""
        if self.state.view not in (
            ViewState.APP_LIST,
            ViewState.CONFIRM,
            ViewState.RESULT,
        ):
            return []
        return render_device_info(self.state)

    def _get_tabs_bar(self) -> StyleAndText:
        """Get tabs bar content."""
        if self.state.view not in (ViewState.APP_LIST,):
            return []
        return render_tabs(self.state)

    def _get_summary_bar(self) -> StyleAndText:
        """Get summary stats bar content."""
        if self.state.view not in (ViewState.APP_LIST,):
            return []
        return render_summary(self.state)

    def _get_loading_status(self) -> StyleAndText:
        """Get loading status message."""
        if self.state.view != ViewState.LOADING or not self.state.loading_status:
            return []
        return [("class:progress", f" ⏳ {self.state.loading_status}")]

    def _get_content(self) -> StyleAndText:
        """Generate main content based on current view."""
        if self.state.view == ViewState.LOADING:
            return [("", "\n\n  Loading...")]

        if self.state.view == ViewState.ERROR:
            return render_error(self.state)

        if self.state.view == ViewState.DEVICE_SELECT:
            return render_device_list(self.state)

        if self.state.view == ViewState.CONFIRM:
            return render_confirm(self.state)

        if self.state.view == ViewState.EXECUTING:
            return render_execution(self.state)

        if self.state.view == ViewState.RESULT:
            return render_result(self.state)

        if self.state.view == ViewState.APP_LIST:
            # Get terminal size for responsive list
            try:
                size = self.app.output.get_size()
                height = size.rows
            except Exception:
                height = 25
            return render_app_list(self.state, height)

        return []

    def _select_device(self, device: DeviceInfo) -> None:
        """Handle device selection and load apps."""
        self.state.selected_device = device
        self.state.view = ViewState.LOADING
        self.state.loading_status = f"Connecting to {device.display_name or device.device_id}..."
        self.app.invalidate()

        try:
            if self.adb:

                def progress_callback(package: str, current: int, total: int) -> None:
                    """Update loading status with current package."""
                    self.state.loading_status = (
                        f"Fetching app details ({current}/{total})... {package}"
                    )
                    self.app.invalidate()

                self.state.apps = self.adb.list_apps(
                    device.device_id,
                    include_system=True,
                    include_user=True,
                    fetch_sizes=True,
                    progress_callback=progress_callback,
                )

                self.state.loading_status = f"Loaded {len(self.state.apps)} apps"
                self.app.invalidate()
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
        self.state.execution_current = ""

        # Show executing view immediately
        self.app.invalidate()

        device_id = self.state.selected_device.device_id
        action = self.state.pending_action

        for pkg in packages:
            # Set current package and show it before processing
            self.state.execution_current = pkg
            self.app.invalidate()

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
        self._write_report()

        # Reload apps and show result
        self._reload_apps()
        self.state.selected_packages.clear()
        self.state.view = ViewState.RESULT  # Show result log

    def _write_report(self) -> None:
        """Write operation report to file."""
        if not self.state.selected_device or not self.state.pending_action:
            return

        report_results = [
            OperationResult(package=pkg, success=success, error=error)
            for pkg, success, error in self.state.execution_results
        ]
        report = OperationReport(
            device=self.state.selected_device,
            action=self.state.pending_action,
            timestamp=datetime.now(),
            results=report_results,
        )
        self.report_writer.write_report(report)

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

    def _initialize_in_background(self) -> None:
        """Initialize ADB and load devices in background thread."""
        try:
            self.state.loading_status = "Initializing ADB..."
            self.app.invalidate()
            self.adb = ADBClient()

            self.state.loading_status = "Scanning for devices..."
            self.app.invalidate()
            devices = self.adb.get_ready_devices()

            # Get detailed device info
            detailed: list[DeviceInfo] = []
            for i, dev in enumerate(devices, 1):
                self.state.loading_status = f"Getting device info ({i}/{len(devices)})..."
                self.app.invalidate()
                try:
                    detailed.append(self.adb.get_device_info(dev.device_id))
                except Exception:
                    detailed.append(dev)

            self.state.devices = detailed

            if len(detailed) == 1:
                self._select_device(detailed[0])
            elif detailed:
                self.state.loading_status = ""
                self.state.view = ViewState.DEVICE_SELECT
                self.app.invalidate()
            else:
                self.state.error_msg = "No devices connected"
                self.state.view = ViewState.ERROR
                self.app.invalidate()

        except ADBNotFoundError:
            self.state.error_msg = "ADB not found. Install Android SDK and add to PATH."
            self.state.view = ViewState.ERROR
            self.app.invalidate()
        except ADBError as e:
            self.state.error_msg = str(e)
            self.state.view = ViewState.ERROR
            self.app.invalidate()

    def run(self) -> None:
        """Run the application."""
        # Start background initialization
        init_thread = threading.Thread(target=self._initialize_in_background, daemon=True)
        init_thread.start()

        # Run the UI (this blocks until exit)
        self.app.run()


def main() -> None:
    """Main entry point."""
    ui = AppFreezeUI()
    ui.run()


if __name__ == "__main__":
    main()
