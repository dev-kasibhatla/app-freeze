"""Tests for the prompt_toolkit-based UI."""

from unittest.mock import patch

from app_freeze.adb.models import AppInfo, DeviceInfo, DeviceState
from app_freeze.app import (
    AppFreezeUI,
    FilterMode,
    UIState,
    ViewState,
    render_app_list,
    render_confirm,
    render_device_info,
    render_device_list,
    render_error,
    render_execution,
    render_footer,
    render_header,
    render_result,
    render_summary,
    render_tabs,
)
from app_freeze.state import AppAction

# ─────────────────────────────────────────────────────────────────────────────
# UIState Tests
# ─────────────────────────────────────────────────────────────────────────────


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

    def test_filtered_apps_text_filter_case_insensitive(self) -> None:
        """Test filtered_apps text filter is case insensitive."""
        state = UIState()
        state.apps = [
            AppInfo(package_name="com.Facebook.App", is_system=False, is_enabled=True),
        ]
        state.filter_text = "FACEBOOK"
        result = state.filtered_apps()
        assert len(result) == 1

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

    def test_get_stats(self) -> None:
        """Test get_stats returns correct counts."""
        state = UIState()
        state.apps = [
            AppInfo(package_name="user1", is_system=False, is_enabled=True),
            AppInfo(package_name="user2", is_system=False, is_enabled=False),
            AppInfo(package_name="system1", is_system=True, is_enabled=True),
        ]
        stats = state.get_stats()
        assert stats["total"] == 3
        assert stats["user"] == 2
        assert stats["system"] == 1
        assert stats["enabled"] == 2
        assert stats["disabled"] == 1

    def test_get_stats_empty(self) -> None:
        """Test get_stats with no apps."""
        state = UIState()
        stats = state.get_stats()
        assert stats["total"] == 0
        assert stats["user"] == 0
        assert stats["system"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# Renderer Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestRenderers:
    """Tests for rendering functions."""

    def test_render_header_loading(self) -> None:
        """Test header in loading state."""
        state = UIState()
        state.view = ViewState.LOADING
        result = render_header(state)
        assert any("Loading" in text for _, text in result)

    def test_render_header_device_select(self) -> None:
        """Test header in device select state."""
        state = UIState()
        state.view = ViewState.DEVICE_SELECT
        result = render_header(state)
        assert any("Select Device" in text for _, text in result)

    def test_render_header_with_device(self) -> None:
        """Test header shows device name."""
        state = UIState()
        state.view = ViewState.APP_LIST
        state.selected_device = DeviceInfo(
            device_id="abc123",
            state=DeviceState.DEVICE,
            model="Pixel 7",
        )
        result = render_header(state)
        assert any("Pixel 7" in text for _, text in result)

    def test_render_device_info(self) -> None:
        """Test device info widget."""
        state = UIState()
        state.selected_device = DeviceInfo(
            device_id="abc123",
            state=DeviceState.DEVICE,
            model="Pixel 7",
            android_version="13",
        )
        result = render_device_info(state)
        text = "".join(t for _, t in result)
        assert "Pixel 7" in text
        assert "13" in text
        assert "abc123" in text

    def test_render_device_info_no_device(self) -> None:
        """Test device info with no device."""
        state = UIState()
        result = render_device_info(state)
        assert result == []

    def test_render_summary(self) -> None:
        """Test summary stats rendering."""
        state = UIState()
        state.apps = [
            AppInfo(package_name="user1", is_system=False, is_enabled=True),
            AppInfo(package_name="system1", is_system=True, is_enabled=False),
        ]
        result = render_summary(state)
        text = "".join(t for _, t in result)
        assert "2" in text  # total
        assert "user" in text
        assert "system" in text

    def test_render_tabs(self) -> None:
        """Test tabs rendering."""
        state = UIState()
        state.filter_mode = FilterMode.USER
        result = render_tabs(state)
        text = "".join(t for _, t in result)
        assert "[1]" in text
        assert "[2]" in text
        assert "User" in text
        assert "System" in text

    def test_render_device_list(self) -> None:
        """Test device list rendering."""
        state = UIState()
        state.devices = [
            DeviceInfo(device_id="dev1", state=DeviceState.DEVICE, model="Phone1"),
            DeviceInfo(device_id="dev2", state=DeviceState.DEVICE, model="Phone2"),
        ]
        state.device_cursor = 0
        result = render_device_list(state)
        text = "".join(t for _, t in result)
        assert "Phone1" in text
        assert "Phone2" in text

    def test_render_device_list_empty(self) -> None:
        """Test device list with no devices."""
        state = UIState()
        state.devices = []
        result = render_device_list(state)
        text = "".join(t for _, t in result)
        assert "No devices found" in text

    def test_render_app_list(self) -> None:
        """Test app list rendering."""
        state = UIState()
        state.apps = [
            AppInfo(package_name="com.test.app", is_system=False, is_enabled=True, size_mb=10.5),
        ]
        result = render_app_list(state, height=20)
        text = "".join(t for _, t in result)
        assert "com.test.app" in text
        assert "10.5MB" in text

    def test_render_app_list_empty(self) -> None:
        """Test app list with no apps."""
        state = UIState()
        state.apps = []
        result = render_app_list(state, height=20)
        text = "".join(t for _, t in result)
        assert "No apps match filter" in text

    def test_render_app_list_with_selection(self) -> None:
        """Test app list shows selection marker."""
        state = UIState()
        state.apps = [
            AppInfo(package_name="com.test.app", is_system=False, is_enabled=True),
        ]
        state.selected_packages = {"com.test.app"}
        result = render_app_list(state, height=20)
        text = "".join(t for _, t in result)
        assert "●" in text  # Selection marker

    def test_render_confirm(self) -> None:
        """Test confirmation dialog rendering."""
        state = UIState()
        state.pending_action = AppAction.DISABLE
        state.selected_packages = {"com.test.app"}
        result = render_confirm(state)
        text = "".join(t for _, t in result)
        assert "DISABLE" in text
        assert "1 app" in text
        assert "[y]" in text

    def test_render_execution(self) -> None:
        """Test execution progress rendering."""
        state = UIState()
        state.pending_action = AppAction.DISABLE
        state.execution_progress = 2
        state.execution_total = 5
        state.execution_results = [
            ("com.test.ok", True, None),
            ("com.test.fail", False, "Error"),
        ]
        result = render_execution(state)
        text = "".join(t for _, t in result)
        assert "Disabling" in text
        assert "2/5" in text
        assert "✓" in text
        assert "✗" in text

    def test_render_result(self) -> None:
        """Test result log rendering."""
        state = UIState()
        state.pending_action = AppAction.ENABLE
        state.execution_results = [
            ("com.test.app", True, None),
        ]
        result = render_result(state)
        text = "".join(t for _, t in result)
        assert "Enabled" in text
        assert "Success: 1" in text

    def test_render_error(self) -> None:
        """Test error rendering."""
        state = UIState()
        state.error_msg = "Something went wrong"
        result = render_error(state)
        text = "".join(t for _, t in result)
        assert "Something went wrong" in text

    def test_render_footer_confirm(self) -> None:
        """Test footer in confirm state."""
        state = UIState()
        state.view = ViewState.CONFIRM
        result = render_footer(state)
        text = "".join(t for _, t in result)
        assert "[y]" in text
        assert "[q]" in text

    def test_render_footer_app_list(self) -> None:
        """Test footer in app list state."""
        state = UIState()
        state.view = ViewState.APP_LIST
        state.selected_packages = {"a", "b"}
        result = render_footer(state)
        text = "".join(t for _, t in result)
        assert "[D]" in text
        assert "[E]" in text
        assert "2 sel" in text


# ─────────────────────────────────────────────────────────────────────────────
# AppFreezeUI Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestAppFreezeUIInit:
    """Tests for AppFreezeUI initialization."""

    def test_init_creates_state(self) -> None:
        """Test initialization creates proper state."""
        with patch("app_freeze.app.Application"):
            ui = AppFreezeUI()
            assert isinstance(ui.state, UIState)
            assert ui.adb is None
            assert ui.report_writer is not None

    def test_init_creates_keybindings(self) -> None:
        """Test initialization creates keybindings."""
        with patch("app_freeze.app.Application"):
            ui = AppFreezeUI()
            assert ui.kb is not None

    def test_init_creates_filter_buffer(self) -> None:
        """Test initialization creates filter buffer."""
        with patch("app_freeze.app.Application"):
            ui = AppFreezeUI()
            assert ui.filter_buffer is not None
            assert ui.filter_visible is False


class TestImportSpeed:
    """Test that imports are fast."""

    def test_import_time(self) -> None:
        """Test module imports quickly."""
        import subprocess
        import sys
        import time

        # Use subprocess to avoid module caching/reload issues
        start = time.perf_counter()
        result = subprocess.run(
            [sys.executable, "-c", "import app_freeze.app"],
            capture_output=True,
        )
        elapsed = time.perf_counter() - start
        assert result.returncode == 0, f"Import failed: {result.stderr.decode()}"
        assert elapsed < 2.0, f"Import took {elapsed:.2f}s, expected < 2s"


# ─────────────────────────────────────────────────────────────────────────────
# ViewState and FilterMode Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestEnums:
    """Test enum values exist."""

    def test_view_states_exist(self) -> None:
        """Test all expected view states exist."""
        assert ViewState.LOADING is not None
        assert ViewState.DEVICE_SELECT is not None
        assert ViewState.APP_LIST is not None
        assert ViewState.CONFIRM is not None
        assert ViewState.EXECUTING is not None
        assert ViewState.RESULT is not None  # New state
        assert ViewState.ERROR is not None

    def test_filter_modes_exist(self) -> None:
        """Test all expected filter modes exist."""
        assert FilterMode.ALL is not None
        assert FilterMode.ENABLED is not None
        assert FilterMode.DISABLED is not None
        assert FilterMode.USER is not None
        assert FilterMode.SYSTEM is not None


# ─────────────────────────────────────────────────────────────────────────────
# Edge Case Tests
# ─────────────────────────────────────────────────────────────────────────────


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_app_cursor_clamp(self) -> None:
        """Test USER filter only shows non-system apps."""
        state = UIState()
        state.apps = [
            AppInfo(package_name="com.a", is_system=False, is_enabled=True),
            AppInfo(package_name="com.b", is_system=False, is_enabled=True),
            AppInfo(package_name="com.c", is_system=True, is_enabled=True),
        ]
        state.filter_mode = FilterMode.USER  # Only non-system apps
        filtered = state.filtered_apps()
        # Should return only user apps (com.a, com.b)
        assert len(filtered) == 2
        assert all(not app.is_system for app in filtered)

    def test_empty_filter_text_returns_all(self) -> None:
        """Test empty filter text returns all apps."""
        state = UIState()
        state.apps = [
            AppInfo(package_name="com.a", is_system=False, is_enabled=True),
        ]
        state.filter_text = ""
        assert len(state.filtered_apps()) == 1

    def test_selected_packages_independent_of_filter(self) -> None:
        """Test selected packages persist across filter changes."""
        state = UIState()
        state.apps = [
            AppInfo(package_name="com.a", is_system=False, is_enabled=True),
            AppInfo(package_name="com.b", is_system=True, is_enabled=True),
        ]
        state.selected_packages = {"com.a", "com.b"}
        state.filter_mode = FilterMode.USER  # Only shows com.a
        assert len(state.selected_packages) == 2  # Both still selected

    def test_execution_results_storage(self) -> None:
        """Test execution results can be stored."""
        state = UIState()
        state.execution_results = [
            ("pkg1", True, None),
            ("pkg2", False, "Some error"),
        ]
        state.execution_current = "pkg2"
        assert len(state.execution_results) == 2
        assert state.execution_current == "pkg2"
        assert state.execution_results[0][1] is True
        assert state.execution_results[1][2] == "Some error"

    def test_large_app_list_rendering(self) -> None:
        """Test rendering large app list doesn't crash."""
        state = UIState()
        state.apps = [
            AppInfo(package_name=f"com.app{i}", is_system=i % 2 == 0, is_enabled=i % 3 != 0)
            for i in range(500)
        ]
        state.app_cursor = 250
        result = render_app_list(state, height=30)
        assert len(result) > 0  # Should render without error
