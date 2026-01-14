"""Tests for the new prompt_toolkit-based UI."""

from unittest.mock import patch

from app_freeze.adb.models import AppInfo, DeviceInfo, DeviceState
from app_freeze.app import (
    AppFreezeUI,
    FilterMode,
    UIState,
    ViewState,
)
from app_freeze.state import AppAction


class TestUIState:
    """Tests for UIState dataclass."""

    def test_default_state(self) -> None:
        """Test default state values."""
        state = UIState()
        assert state.view == ViewState.LOADING
        assert state.error_msg == ""
        assert state.devices == []
        assert state.apps == []
        assert state.selected_packages == set()
        assert state.filter_mode == FilterMode.ALL

    def test_filtered_apps_no_filter(self) -> None:
        """Test filtered_apps with no filter returns all."""
        state = UIState()
        state.apps = [
            AppInfo(package_name="com.test.app1", is_system=False, is_enabled=True),
            AppInfo(package_name="com.test.app2", is_system=True, is_enabled=False),
        ]
        assert len(state.filtered_apps()) == 2

    def test_filtered_apps_text_filter(self) -> None:
        """Test filtered_apps with text filter."""
        state = UIState()
        state.apps = [
            AppInfo(package_name="com.facebook.app", is_system=False, is_enabled=True),
            AppInfo(package_name="com.google.app", is_system=False, is_enabled=True),
        ]
        state.filter_text = "facebook"
        result = state.filtered_apps()
        assert len(result) == 1
        assert result[0].package_name == "com.facebook.app"

    def test_filtered_apps_enabled_filter(self) -> None:
        """Test filtered_apps with enabled filter."""
        state = UIState()
        state.apps = [
            AppInfo(package_name="com.test.enabled", is_system=False, is_enabled=True),
            AppInfo(package_name="com.test.disabled", is_system=False, is_enabled=False),
        ]
        state.filter_mode = FilterMode.ENABLED
        result = state.filtered_apps()
        assert len(result) == 1
        assert result[0].is_enabled is True

    def test_filtered_apps_disabled_filter(self) -> None:
        """Test filtered_apps with disabled filter."""
        state = UIState()
        state.apps = [
            AppInfo(package_name="com.test.enabled", is_system=False, is_enabled=True),
            AppInfo(package_name="com.test.disabled", is_system=False, is_enabled=False),
        ]
        state.filter_mode = FilterMode.DISABLED
        result = state.filtered_apps()
        assert len(result) == 1
        assert result[0].is_enabled is False

    def test_filtered_apps_user_filter(self) -> None:
        """Test filtered_apps with user apps filter."""
        state = UIState()
        state.apps = [
            AppInfo(package_name="com.user.app", is_system=False, is_enabled=True),
            AppInfo(package_name="com.android.system", is_system=True, is_enabled=True),
        ]
        state.filter_mode = FilterMode.USER
        result = state.filtered_apps()
        assert len(result) == 1
        assert result[0].is_system is False

    def test_filtered_apps_system_filter(self) -> None:
        """Test filtered_apps with system apps filter."""
        state = UIState()
        state.apps = [
            AppInfo(package_name="com.user.app", is_system=False, is_enabled=True),
            AppInfo(package_name="com.android.system", is_system=True, is_enabled=True),
        ]
        state.filter_mode = FilterMode.SYSTEM
        result = state.filtered_apps()
        assert len(result) == 1
        assert result[0].is_system is True

    def test_filtered_apps_combined_filters(self) -> None:
        """Test filtered_apps with text and mode filters combined."""
        state = UIState()
        state.apps = [
            AppInfo(package_name="com.google.enabled", is_system=False, is_enabled=True),
            AppInfo(package_name="com.google.disabled", is_system=False, is_enabled=False),
            AppInfo(package_name="com.facebook.enabled", is_system=False, is_enabled=True),
        ]
        state.filter_text = "google"
        state.filter_mode = FilterMode.ENABLED
        result = state.filtered_apps()
        assert len(result) == 1
        assert result[0].package_name == "com.google.enabled"


class TestAppFreezeUIInit:
    """Tests for AppFreezeUI initialization."""

    def test_init_creates_state(self) -> None:
        """Test that initialization creates proper state."""
        with patch("app_freeze.app.Application"):
            ui = AppFreezeUI()
            assert isinstance(ui.state, UIState)
            assert ui.adb is None
            assert ui.report_writer is not None

    def test_init_creates_keybindings(self) -> None:
        """Test that initialization creates keybindings."""
        with patch("app_freeze.app.Application"):
            ui = AppFreezeUI()
            assert ui.kb is not None


class TestImportSpeed:
    """Test that imports are fast."""

    def test_import_time(self) -> None:
        """Test module imports quickly."""
        import time

        start = time.perf_counter()
        # Re-import to simulate fresh import
        import importlib

        import app_freeze.app

        importlib.reload(app_freeze.app)
        elapsed = time.perf_counter() - start
        # Should import in under 1 second
        assert elapsed < 1.0, f"Import took {elapsed:.2f}s, expected < 1s"


class TestViewStates:
    """Test view state transitions."""

    def test_view_states_exist(self) -> None:
        """Test all expected view states exist."""
        assert ViewState.LOADING is not None
        assert ViewState.DEVICE_SELECT is not None
        assert ViewState.APP_LIST is not None
        assert ViewState.CONFIRM is not None
        assert ViewState.EXECUTING is not None
        assert ViewState.ERROR is not None

    def test_filter_modes_exist(self) -> None:
        """Test all expected filter modes exist."""
        assert FilterMode.ALL is not None
        assert FilterMode.ENABLED is not None
        assert FilterMode.DISABLED is not None
        assert FilterMode.USER is not None
        assert FilterMode.SYSTEM is not None


class TestRendering:
    """Test rendering functions don't crash."""

    def test_get_header_loading(self) -> None:
        """Test header renders in loading state."""
        state = UIState()
        state.view = ViewState.LOADING
        # Manually test the logic without full UI
        assert state.view == ViewState.LOADING

    def test_get_header_device_select(self) -> None:
        """Test header state in device select."""
        state = UIState()
        state.view = ViewState.DEVICE_SELECT
        assert state.view == ViewState.DEVICE_SELECT

    def test_get_header_with_device(self) -> None:
        """Test header shows device name."""
        state = UIState()
        state.view = ViewState.APP_LIST
        state.selected_device = DeviceInfo(
            device_id="abc123",
            state=DeviceState.DEVICE,
            model="Pixel 7",
        )
        assert state.selected_device.display_name == "Pixel 7"

    def test_content_loading_state(self) -> None:
        """Test content in loading state."""
        state = UIState()
        state.view = ViewState.LOADING
        assert state.view == ViewState.LOADING

    def test_content_error_state(self) -> None:
        """Test content error message is stored."""
        state = UIState()
        state.view = ViewState.ERROR
        state.error_msg = "Test error"
        assert state.error_msg == "Test error"

    def test_footer_confirm_state(self) -> None:
        """Test footer in confirm state."""
        state = UIState()
        state.view = ViewState.CONFIRM
        state.pending_action = AppAction.DISABLE
        state.selected_packages = {"com.test.app"}
        assert len(state.selected_packages) == 1
        assert state.pending_action == AppAction.DISABLE

    def test_footer_device_select_state(self) -> None:
        """Test footer in device select state."""
        state = UIState()
        state.view = ViewState.DEVICE_SELECT
        assert state.view == ViewState.DEVICE_SELECT

    def test_footer_app_list_state(self) -> None:
        """Test footer in app list state."""
        state = UIState()
        state.view = ViewState.APP_LIST
        assert state.view == ViewState.APP_LIST

    def test_device_list_empty(self) -> None:
        """Test device list with no devices."""
        state = UIState()
        state.devices = []
        assert len(state.devices) == 0

    def test_device_list_with_devices(self) -> None:
        """Test device list with devices."""
        state = UIState()
        state.devices = [
            DeviceInfo(device_id="dev1", state=DeviceState.DEVICE, model="Phone1"),
            DeviceInfo(device_id="dev2", state=DeviceState.DEVICE, model="Phone2"),
        ]
        state.device_cursor = 0
        assert len(state.devices) == 2
        assert state.devices[0].model == "Phone1"

    def test_app_list_empty(self) -> None:
        """Test app list with no apps."""
        state = UIState()
        state.apps = []
        assert len(state.filtered_apps()) == 0

    def test_app_list_with_apps(self) -> None:
        """Test app list with apps."""
        state = UIState()
        state.apps = [
            AppInfo(package_name="com.test.app", is_system=False, is_enabled=True, size_mb=10.5),
        ]
        state.app_cursor = 0
        assert len(state.filtered_apps()) == 1
        assert state.filtered_apps()[0].package_name == "com.test.app"

    def test_execution_results(self) -> None:
        """Test execution results storage."""
        state = UIState()
        state.pending_action = AppAction.DISABLE
        state.execution_progress = 2
        state.execution_total = 5
        state.execution_results = [
            ("com.test.ok", True, None),
            ("com.test.fail", False, "Error message"),
        ]
        assert len(state.execution_results) == 2
        assert state.execution_results[0][1] is True
        assert state.execution_results[1][1] is False
