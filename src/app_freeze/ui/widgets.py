"""Custom widgets for the App Freeze TUI."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Checkbox, Label, ListItem, ListView, Static

from app_freeze.adb.models import AppInfo


class AppItem(ListItem):
    """A single app item in the app list with selection support."""

    COMPONENT_CLASSES = {"app-item--system", "app-item--disabled", "app-item--selected"}

    class Toggled(Message):
        """Emitted when the app selection is toggled."""

        def __init__(self, app_item: "AppItem", selected: bool) -> None:
            self.app_item = app_item
            self.selected = selected
            super().__init__()

    selected = reactive(False)

    def __init__(self, app_info: AppInfo, selected: bool = False) -> None:
        """Initialize app item with app info."""
        super().__init__()
        self.app_info = app_info
        self.selected = selected

    def compose(self) -> ComposeResult:
        """Compose the app item layout."""
        with Horizontal():
            yield Checkbox("", value=self.selected, classes="app-checkbox")
            yield Label(self.app_info.package_name, classes="app-name")
            status_class = "status-enabled" if self.app_info.is_enabled else "status-disabled"
            status_text = "● Enabled" if self.app_info.is_enabled else "○ Disabled"
            yield Label(status_text, classes=f"app-status {status_class}")
            size_str = f"{self.app_info.size_mb:.1f} MB" if self.app_info.size_mb > 0 else "-"
            yield Label(size_str, classes="app-size")
            type_str = "System" if self.app_info.is_system else "User"
            yield Label(type_str, classes="app-type")

    def watch_selected(self, selected: bool) -> None:
        """React to selection changes."""
        self.set_class(selected, "--selected")
        # Only update checkbox if widget is mounted and composed
        try:
            checkbox = self.query_one(Checkbox)
            checkbox.value = selected
        except Exception:
            # Widget not yet composed, checkbox will be created with correct value
            pass

    def toggle(self) -> None:
        """Toggle selection state."""
        self.selected = not self.selected
        self.post_message(self.Toggled(self, self.selected))

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox change."""
        event.stop()
        if event.value != self.selected:
            self.selected = event.value
            self.post_message(self.Toggled(self, self.selected))


class AppListWidget(ListView):
    """Scrollable list of apps with selection support."""

    class SelectionChanged(Message):
        """Emitted when the selection set changes."""

        def __init__(self, selected_packages: set[str]) -> None:
            self.selected_packages = selected_packages
            super().__init__()

    def __init__(
        self,
        apps: list[AppInfo],
        selected_packages: set[str] | None = None,
        *,
        classes: str | None = None,
        id: str | None = None,  # noqa: A002
    ) -> None:
        """Initialize app list with apps."""
        super().__init__(classes=classes, id=id)
        self._apps = apps
        self._selected_packages = selected_packages or set()

    def compose(self) -> ComposeResult:
        """Compose the app list."""
        for app_info in self._apps:
            is_selected = app_info.package_name in self._selected_packages
            yield AppItem(app_info, selected=is_selected)

    @property
    def selected_packages(self) -> set[str]:
        """Get currently selected package names."""
        return self._selected_packages.copy()

    def on_app_item_toggled(self, event: AppItem.Toggled) -> None:
        """Handle app item toggle."""
        event.stop()
        pkg = event.app_item.app_info.package_name
        if event.selected:
            self._selected_packages.add(pkg)
        else:
            self._selected_packages.discard(pkg)
        self.post_message(self.SelectionChanged(self._selected_packages.copy()))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle list item selection (spacebar/enter on focused item)."""
        event.stop()
        if isinstance(event.item, AppItem):
            event.item.toggle()

    def select_all(self) -> None:
        """Select all apps."""
        for item in self.query(AppItem):
            if not item.selected:
                item.selected = True
                self._selected_packages.add(item.app_info.package_name)
        self.post_message(self.SelectionChanged(self._selected_packages.copy()))

    def deselect_all(self) -> None:
        """Deselect all apps."""
        for item in self.query(AppItem):
            if item.selected:
                item.selected = False
        self._selected_packages.clear()
        self.post_message(self.SelectionChanged(self._selected_packages.copy()))

    def toggle_focused(self) -> None:
        """Toggle the currently focused item."""
        if self.highlighted_child and isinstance(self.highlighted_child, AppItem):
            self.highlighted_child.toggle()


class DeviceInfoPanel(Static):
    """Panel displaying device information."""

    def __init__(
        self,
        device_id: str = "",
        model: str = "",
        manufacturer: str = "",
        android_version: str = "",
        sdk_level: int = 0,
        *,
        classes: str | None = None,
    ) -> None:
        """Initialize device info panel."""
        super().__init__(classes=classes)
        self._device_id = device_id
        self._model = model
        self._manufacturer = manufacturer
        self._android_version = android_version
        self._sdk_level = sdk_level
        self.border_title = "Device Info"

    def compose(self) -> ComposeResult:
        """Compose the device info layout."""
        with Vertical():
            with Horizontal():
                yield Label("Device ID:", classes="label")
                yield Label(self._device_id, classes="value")
            with Horizontal():
                yield Label("Model:", classes="label")
                yield Label(self._model or "-", classes="value")
            with Horizontal():
                yield Label("Manufacturer:", classes="label")
                yield Label(self._manufacturer or "-", classes="value")
            with Horizontal():
                yield Label("Android:", classes="label")
                version_str = f"{self._android_version} (SDK {self._sdk_level})"
                yield Label(version_str if self._android_version else "-", classes="value")


class StatusBar(Static):
    """Status bar showing current operation status."""

    def __init__(
        self,
        text: str = "",
        count: str = "",
        *,
        id: str | None = None,  # noqa: A002
    ) -> None:
        """Initialize status bar."""
        super().__init__(id=id)
        self._text = text
        self._count = count

    def compose(self) -> ComposeResult:
        """Compose the status bar."""
        with Horizontal():
            yield Label(self._text, classes="status-text")
            yield Label(self._count, classes="status-count")

    def update_status(self, text: str = "", count: str = "") -> None:
        """Update status bar content."""
        self._text = text
        self._count = count
        self.query_one(".status-text", Label).update(text)
        self.query_one(".status-count", Label).update(count)
