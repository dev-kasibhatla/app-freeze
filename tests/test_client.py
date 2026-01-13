"""Tests for ADB client with mocked subprocess."""

from unittest.mock import MagicMock, patch

import pytest

from app_freeze.adb.client import ADBClient
from app_freeze.adb.errors import (
    ADBCommandError,
    ADBDeviceDisconnectedError,
    ADBDeviceNotFoundError,
    ADBNotFoundError,
    ADBPermissionError,
    ADBTimeoutError,
)
from app_freeze.adb.models import DeviceState


class TestADBClientInit:
    """Tests for ADBClient initialization."""

    def test_explicit_path(self) -> None:
        client = ADBClient(adb_path="/usr/bin/adb")
        assert client._adb_path == "/usr/bin/adb"

    def test_find_adb_in_path(self) -> None:
        with patch("shutil.which", return_value="/usr/local/bin/adb"):
            client = ADBClient()
            assert client._adb_path == "/usr/local/bin/adb"

    def test_adb_not_found(self) -> None:
        with patch("shutil.which", return_value=None), pytest.raises(ADBNotFoundError):
            ADBClient()

    def test_check_adb_available_true(self) -> None:
        with patch("shutil.which", return_value="/usr/bin/adb"):
            assert ADBClient.check_adb_available() is True

    def test_check_adb_available_false(self) -> None:
        with patch("shutil.which", return_value=None):
            assert ADBClient.check_adb_available() is False


class TestADBClientRun:
    """Tests for ADBClient._run method."""

    @pytest.fixture
    def client(self) -> ADBClient:
        return ADBClient(adb_path="/usr/bin/adb")

    def test_successful_command(self, client: ADBClient) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            stdout, stderr = client._run(["devices"])
            assert stdout == "output"
            assert stderr == ""

    def test_command_with_device_id(self, client: ADBClient) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            client._run(["shell", "pm", "list", "packages"], device_id="device123")
            call_args = mock_run.call_args[0][0]
            expected = ["/usr/bin/adb", "-s", "device123", "shell", "pm", "list", "packages"]
            assert call_args == expected

    def test_timeout_error(self, client: ADBClient) -> None:
        import subprocess

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 30)):
            with pytest.raises(ADBTimeoutError) as exc_info:
                client._run(["devices"], timeout=30)
            assert exc_info.value.timeout == 30

    def test_command_error(self, client: ADBClient) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error message"

        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(ADBCommandError) as exc_info:
                client._run(["shell", "bad_command"])
            assert exc_info.value.exit_code == 1
            assert "error message" in exc_info.value.stderr

    def test_device_not_found_error(self, client: ADBClient) -> None:
        """Test that device disconnected error is raised for specific device."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error: device not found"

        with (
            patch("subprocess.run", return_value=mock_result),
            pytest.raises(ADBDeviceDisconnectedError),
        ):
            client._run(["shell", "pm"], device_id="missing-device")

    def test_permission_error(self, client: ADBClient) -> None:
        """Test that permission error is raised for permission denied."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error: permission denied"

        with (
            patch("subprocess.run", return_value=mock_result),
            pytest.raises(ADBPermissionError) as exc_info,
        ):
            client._run(["shell", "pm", "disable"], device_id="test-device")

        assert "test-device" in str(exc_info.value)
        assert "permission" in str(exc_info.value).lower()


class TestADBClientListDevices:
    """Tests for ADBClient.list_devices."""

    @pytest.fixture
    def client(self) -> ADBClient:
        return ADBClient(adb_path="/usr/bin/adb")

    def test_no_devices(self, client: ADBClient) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "List of devices attached\n"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            devices = client.list_devices()
            assert devices == []

    def test_single_device(self, client: ADBClient) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """List of devices attached
emulator-5554          device product:sdk_phone model:Pixel_4 transport_id:1
"""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            devices = client.list_devices()
            assert len(devices) == 1
            assert devices[0].device_id == "emulator-5554"
            assert devices[0].state == DeviceState.DEVICE
            assert devices[0].model == "Pixel 4"  # Underscores replaced

    def test_multiple_devices(self, client: ADBClient) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """List of devices attached
device1          device product:prod1 model:Model_1 transport_id:1
device2          device product:prod2 model:Model_2 transport_id:2
device3          offline
"""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            devices = client.list_devices()
            assert len(devices) == 3
            assert devices[0].device_id == "device1"
            assert devices[1].device_id == "device2"
            assert devices[2].device_id == "device3"
            assert devices[2].state == DeviceState.OFFLINE


class TestADBClientGetDeviceInfo:
    """Tests for ADBClient.get_device_info."""

    @pytest.fixture
    def client(self) -> ADBClient:
        return ADBClient(adb_path="/usr/bin/adb")

    def test_device_not_found(self, client: ADBClient) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "List of devices attached\n"
        mock_result.stderr = ""

        with (
            patch("subprocess.run", return_value=mock_result),
            pytest.raises(ADBDeviceNotFoundError),
        ):
            client.get_device_info("nonexistent")

    def test_fetches_full_info(self, client: ADBClient) -> None:
        devices_result = MagicMock()
        devices_result.returncode = 0
        devices_result.stdout = """List of devices attached
ABC123          device product:walleye model:Pixel_2 transport_id:1
"""
        devices_result.stderr = ""

        prop_results = {
            "ro.product.model": "Pixel 2",
            "ro.product.manufacturer": "Google",
            "ro.build.version.release": "14",
            "ro.build.version.sdk": "34",
        }

        def mock_run(cmd: list[str], **kwargs: object) -> MagicMock:
            result = MagicMock()
            result.returncode = 0
            result.stderr = ""
            if "devices" in cmd:
                result.stdout = devices_result.stdout
            elif "getprop" in cmd:
                prop_name = cmd[-1]
                result.stdout = prop_results.get(prop_name, "") + "\n"
            return result

        with patch("subprocess.run", side_effect=mock_run):
            info = client.get_device_info("ABC123")
            assert info.device_id == "ABC123"
            assert info.model == "Pixel 2"
            assert info.manufacturer == "Google"
            assert info.android_version == "14"
            assert info.sdk_level == 34

    def test_caches_result(self, client: ADBClient) -> None:
        devices_result = MagicMock()
        devices_result.returncode = 0
        devices_result.stdout = """List of devices attached
ABC123          device product:test model:Test transport_id:1
"""
        devices_result.stderr = ""

        call_count = 0

        def mock_run(cmd: list[str], **kwargs: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            result.returncode = 0
            result.stderr = ""
            if "devices" in cmd:
                result.stdout = devices_result.stdout
            elif "getprop" in cmd:
                if "sdk" in cmd[-1]:
                    result.stdout = "34\n"
                else:
                    result.stdout = "value\n"
            return result

        with patch("subprocess.run", side_effect=mock_run):
            # First call
            info1 = client.get_device_info("ABC123")
            initial_calls = call_count

            # Second call should use cache
            info2 = client.get_device_info("ABC123")
            assert call_count == initial_calls  # No new calls
            assert info1 == info2


class TestADBClientListUsers:
    """Tests for ADBClient.list_users."""

    @pytest.fixture
    def client(self) -> ADBClient:
        return ADBClient(adb_path="/usr/bin/adb")

    def test_single_user(self, client: ADBClient) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """Users:
        UserInfo{0:Owner:4c13} running
"""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            users = client.list_users("device123")
            assert users == [0]

    def test_multiple_users(self, client: ADBClient) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """Users:
        UserInfo{0:Owner:4c13} running
        UserInfo{10:Work:30} running
"""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            users = client.list_users("device123")
            assert users == [0, 10]


class TestADBClientListPackages:
    """Tests for ADBClient.list_packages."""

    @pytest.fixture
    def client(self) -> ADBClient:
        return ADBClient(adb_path="/usr/bin/adb")

    def test_system_and_user_apps(self, client: ADBClient) -> None:
        call_log: list[list[str]] = []

        system_result = MagicMock()
        system_result.returncode = 0
        system_result.stdout = "package:com.android.settings\npackage:com.android.nfc\n"
        system_result.stderr = ""

        user_result = MagicMock()
        user_result.returncode = 0
        user_result.stdout = "package:com.example.app\npackage:com.test.app\n"
        user_result.stderr = ""

        def mock_run(cmd: list[str], **kwargs: object) -> MagicMock:
            call_log.append(cmd)
            # System packages: adb -s device123 shell pm list packages -s
            # User packages: adb -s device123 shell pm list packages -3
            if "-3" in cmd:
                return user_result
            else:
                return system_result

        with patch("subprocess.run", side_effect=mock_run):
            packages = client.list_packages("device123")
            # Should have called twice: once for -s and once for -3
            assert len(call_log) == 2
            assert len(packages) == 4
            assert "com.android.settings" in packages
            assert "com.example.app" in packages
            assert packages == sorted(packages)

    def test_system_apps_only(self, client: ADBClient) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "package:com.android.settings\n"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            packages = client.list_packages("device123", system_apps=True, user_apps=False)
            assert packages == ["com.android.settings"]

    def test_user_apps_only(self, client: ADBClient) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "package:com.example.app\n"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            packages = client.list_packages("device123", system_apps=False, user_apps=True)
            assert packages == ["com.example.app"]


class TestADBClientDeviceSelection:
    """Tests for device selection functionality."""

    @pytest.fixture
    def client(self) -> ADBClient:
        return ADBClient(adb_path="/usr/bin/adb")

    def test_get_ready_devices_all_ready(self, client: ADBClient) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """List of devices attached
device1          device product:prod1 model:Model_1 transport_id:1
device2          device product:prod2 model:Model_2 transport_id:2
"""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            ready = client.get_ready_devices()
            assert len(ready) == 2
            assert all(d.is_ready for d in ready)

    def test_get_ready_devices_filtered(self, client: ADBClient) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """List of devices attached
device1          device product:prod1 model:Model_1 transport_id:1
device2          offline
device3          unauthorized
"""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            ready = client.get_ready_devices()
            assert len(ready) == 1
            assert ready[0].device_id == "device1"

    def test_get_ready_devices_none(self, client: ADBClient) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """List of devices attached
device1          offline
device2          unauthorized
"""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            ready = client.get_ready_devices()
            assert len(ready) == 0

    def test_validate_device_exists_and_ready(self, client: ADBClient) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """List of devices attached
device1          device product:prod1 model:Model_1 transport_id:1
"""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            device = client.validate_device("device1")
            assert device.device_id == "device1"
            assert device.is_ready

    def test_validate_device_not_found(self, client: ADBClient) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """List of devices attached
device1          device product:prod1 model:Model_1 transport_id:1
"""
        mock_result.stderr = ""

        with (
            patch("subprocess.run", return_value=mock_result),
            pytest.raises(ADBDeviceNotFoundError),
        ):
            client.validate_device("nonexistent")

    def test_validate_device_not_ready(self, client: ADBClient) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """List of devices attached
device1          offline
"""
        mock_result.stderr = ""

        with (
            patch("subprocess.run", return_value=mock_result),
            pytest.raises(ADBDeviceNotFoundError),
        ):
            client.validate_device("device1")

    def test_select_device_explicit(self, client: ADBClient) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """List of devices attached
device1          device product:prod1 model:Model_1 transport_id:1
device2          device product:prod2 model:Model_2 transport_id:2
"""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            device = client.select_device("device1")
            assert device.device_id == "device1"

    def test_select_device_auto_single(self, client: ADBClient) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """List of devices attached
device1          device product:prod1 model:Model_1 transport_id:1
"""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            device = client.select_device()
            assert device.device_id == "device1"

    def test_select_device_multiple_no_selection(self, client: ADBClient) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """List of devices attached
device1          device product:prod1 model:Model_1 transport_id:1
device2          device product:prod2 model:Model_2 transport_id:2
"""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(ADBDeviceNotFoundError) as exc_info:
                client.select_device()
            assert "Multiple devices available" in str(exc_info.value)
            assert "device1" in str(exc_info.value)
            assert "device2" in str(exc_info.value)

    def test_select_device_no_ready(self, client: ADBClient) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """List of devices attached
device1          offline
device2          unauthorized
"""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(ADBDeviceNotFoundError) as exc_info:
                client.select_device()
            assert "No ready devices available" in str(exc_info.value)
