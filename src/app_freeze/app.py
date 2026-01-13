"""Main application entry point."""

import asyncio
import contextlib
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import TypeVar

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Center, Container
from textual.widgets import Footer, Header, Label, LoadingIndicator

from app_freeze.adb.client import ADBClient
from app_freeze.adb.errors import (
    ADBDeviceDisconnectedError,
    ADBError,
    ADBNotFoundError,
    ADBPermissionError,
)
from app_freeze.adb.models import AppInfo, DeviceInfo
from app_freeze.reporting import OperationReport, OperationResult, ReportWriter
from app_freeze.state import AppAction, AppState, Screen
from app_freeze.ui.screens import (
    AppListScreen,
    ConfirmationScreen,
    DeviceScreen,
    ExecutionScreen,
    HelpScreen,
)
from app_freeze.ui.theme import THEME_CSS

T = TypeVar("T")


class AppFreezeApp(App[None]):
    """Main application class."""

    TITLE = "App Freeze"
    CSS = (
        THEME_CSS
        + """
    #loading-container {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    #loading-container > Center {
        width: 100%;
        height: auto;
    }

    #loading-container > Center > Label {
        padding: 1;
    }

    #error-container {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    #error-container > Center > .error-title {
        color: $error;
        text-style: bold;
        padding: 1;
    }

    #error-container > Center > .error-message {
        color: $text-muted;
        padding: 1;
    }
    """
    )

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("?", "show_help", "Help"),
    ]

    def __init__(self) -> None:
        """Initialize the application."""
        super().__init__()
        self.state = AppState()
        self._adb: ADBClient | None = None
        self._current_device: DeviceInfo | None = None
        self._apps: list[AppInfo] = []
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._report_writer = ReportWriter()

    async def _run_blocking(self, func: Callable[[], T]) -> T:
        """Run a blocking function in a thread pool."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, func)

    def compose(self) -> ComposeResult:
        """Compose the initial UI."""
        yield Header()
        with Container(id="loading-container"), Center():
            yield LoadingIndicator()
            yield Label("Detecting devices...")
        yield Footer()

    async def on_mount(self) -> None:
        """Handle application mount."""
        await self._initialize()

    async def _initialize(self) -> None:
        """Initialize ADB and detect devices."""
        try:
            self._adb = ADBClient()
            await self._show_device_selection()
        except ADBNotFoundError:
            self._show_error(
                "ADB Not Found",
                "Please install Android SDK and ensure 'adb' is in your PATH.",
            )
        except ADBError as e:
            self._show_error("ADB Error", str(e))

    def _show_error(self, title: str, message: str) -> None:
        """Show an error message."""
        container = self.query_one("#loading-container", Container)
        container.remove()

        error_container = Container(id="error-container")
        error_container.mount(
            Center(
                Label(f"❌ {title}", classes="error-title"),
                Label(message, classes="error-message"),
                Label("Press 'q' to quit", classes="hint"),
            )
        )
        self.mount(error_container, before=self.query_one(Footer))

    async def _show_device_selection(self) -> None:
        """Show device selection screen."""
        if not self._adb:
            return

        try:
            devices = self._adb.get_ready_devices()

            # Fetch detailed info for each device
            detailed_devices: list[DeviceInfo] = []
            for device in devices:
                try:
                    detailed = self._adb.get_device_info(device.device_id)
                    detailed_devices.append(detailed)
                except ADBDeviceDisconnectedError as e:
                    # Device disconnected during info fetch
                    self._show_error("Device Disconnected", str(e))
                    return
                except ADBPermissionError as e:
                    # Permission error during info fetch
                    self._show_error("Permission Error", str(e))
                    return
                except Exception:
                    # Use basic info if detailed fetch fails
                    detailed_devices.append(device)

            self.state.available_devices = detailed_devices

            if len(detailed_devices) == 1:
                # Auto-select single device
                await self._on_device_selected(detailed_devices[0])
            else:
                # Show device selection screen
                device = await self.push_screen_wait(DeviceScreen(detailed_devices))
                if device:
                    await self._on_device_selected(device)
        except ADBDeviceDisconnectedError as e:
            self._show_error("Device Disconnected", str(e))
        except ADBPermissionError as e:
            self._show_error("Permission Error", str(e))
        except ADBError as e:
            self._show_error("Device Error", str(e))

    async def _on_device_selected(self, device: DeviceInfo) -> None:
        """Handle device selection."""
        self._current_device = device
        self.state.selected_device = device
        self.state.current_screen = Screen.APP_LIST

        # Hide loading container if present
        try:
            loading = self.query_one("#loading-container", Container)
            loading.remove()
        except Exception:
            pass

        # Load apps and show app list
        await self._load_and_show_apps()

    async def _load_and_show_apps(self) -> None:
        """Load apps and show the app list screen."""
        if not self._adb or not self._current_device:
            return

        adb = self._adb
        device_id = self._current_device.device_id

        try:
            # Show loading state
            self._show_loading("Loading apps...")

            # Fetch apps (run in thread to not block UI)
            self._apps = await self._run_blocking(
                lambda: adb.list_apps(
                    device_id,
                    include_system=True,
                    include_user=True,
                    fetch_sizes=True,
                )
            )

            # Remove loading
            self._hide_loading()

            # Show app list screen
            result = await self.push_screen_wait(AppListScreen(self._current_device, self._apps))

            if result is None:
                # User went back - show device selection again
                await self._show_device_selection()
            else:
                # User selected apps and action
                selected_packages, action = result
                await self._confirm_action(selected_packages, action)

        except ADBDeviceDisconnectedError as e:
            self._hide_loading()
            self._show_error("Device Disconnected", str(e))
        except ADBPermissionError as e:
            self._hide_loading()
            self._show_error("Permission Error", str(e))
        except ADBError as e:
            self._hide_loading()
            self._show_error("App List Error", str(e))

    def _show_loading(self, message: str) -> None:
        """Show a loading indicator."""
        try:
            container = Container(id="loading-container")
            container.mount(
                Center(
                    LoadingIndicator(),
                    Label(message),
                )
            )
            self.mount(container, before=self.query_one(Footer))
        except Exception:
            pass

    def _hide_loading(self) -> None:
        """Hide the loading indicator."""
        try:
            loading = self.query_one("#loading-container", Container)
            loading.remove()
        except Exception:
            pass

    async def _confirm_action(self, packages: set[str], action: AppAction) -> None:
        """Show confirmation dialog and execute if confirmed."""
        confirmed = await self.push_screen_wait(ConfirmationScreen(packages, action))

        if confirmed:
            await self._execute_action(list(packages), action)
        else:
            # Go back to app list
            await self._load_and_show_apps()

    async def _execute_action(self, packages: list[str], action: AppAction) -> None:
        """Execute enable/disable action on packages."""
        if not self._adb or not self._current_device:
            return

        adb = self._adb
        device = self._current_device
        device_id = device.device_id

        # Show execution screen
        exec_screen = ExecutionScreen(packages, action)
        self.push_screen(exec_screen)

        operation_results: list[OperationResult] = []

        try:
            # Get user IDs
            user_ids = await self._run_blocking(lambda: adb.list_users(device_id))
            if not user_ids:
                user_ids = [0]

            # Execute actions sequentially
            enable = action == AppAction.ENABLE

            for i, package in enumerate(packages):
                exec_screen.update_progress(i, package)

                # Run action in thread - capture package in default arg
                def run_action(pkg: str = package) -> dict[str, tuple[bool, str | None]]:
                    return adb.enable_disable_apps(device_id, [pkg], enable, user_ids)

                try:
                    result = await self._run_blocking(run_action)
                    success, error = result.get(package, (False, "Unknown error"))
                    exec_screen.add_result(package, success, error)
                    operation_results.append(OperationResult(package, success, error))
                except ADBDeviceDisconnectedError as e:
                    # Device disconnected - show error and stop execution
                    exec_screen.add_result(package, False, str(e))
                    operation_results.append(OperationResult(package, False, str(e)))
                    self._show_error("Device Disconnected", str(e))
                    break
                except ADBPermissionError as e:
                    # Permission error - log but continue
                    exec_screen.add_result(package, False, str(e))
                    operation_results.append(OperationResult(package, False, str(e)))
                except ADBError as e:
                    # Other ADB error - log but continue
                    exec_screen.add_result(package, False, str(e))
                    operation_results.append(OperationResult(package, False, str(e)))

            # Update final progress
            exec_screen.update_progress(len(packages), "Complete")
            exec_screen.show_complete()

        except Exception as e:
            # Unexpected error - show and return
            self._show_error("Execution Error", str(e))
            return

        # Wait for user to dismiss
        results = await self.push_screen_wait(exec_screen)

        # Store results in state
        self.state.execution_results = dict((results or {}).items())

        # Generate report
        try:
            report = OperationReport(
                device=device,
                action=action,
                timestamp=datetime.now(),
                results=operation_results,
            )
            await self._run_blocking(lambda: self._report_writer.write_report(report))
            # Could show notification about report location, but keep UI clean for now
        except Exception:
            # Don't fail if report writing fails
            pass

        # Return to app list
        await self._load_and_show_apps()

    async def action_quit(self) -> None:
        """Handle quit action."""
        # Cleanup resources
        self._cleanup()
        self.exit()

    def _cleanup(self) -> None:
        """Cleanup resources on exit."""
        with contextlib.suppress(Exception):
            self._executor.shutdown(wait=False)

    async def on_unmount(self) -> None:
        """Handle application unmount."""
        self._cleanup()

    async def action_show_help(self) -> None:
        """Show help overlay."""
        await self.push_screen(HelpScreen())


def main() -> None:
    """Run the application."""
    app = AppFreezeApp()
    try:
        app.run()
    except KeyboardInterrupt:
        # Clean exit on Ctrl+C
        pass
    except Exception as e:
        # Ensure terminal is restored even on crash
        import sys

        print(f"\nUnexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
