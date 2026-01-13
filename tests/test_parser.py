"""Tests for ADB parser module."""

from app_freeze.adb.models import DeviceState
from app_freeze.adb.parser import (
    parse_device_state,
    parse_devices_output,
    parse_packages_output,
    parse_users_output,
)


class TestParseDeviceState:
    """Tests for parse_device_state."""

    def test_device_state(self) -> None:
        assert parse_device_state("device") == DeviceState.DEVICE

    def test_offline_state(self) -> None:
        assert parse_device_state("offline") == DeviceState.OFFLINE

    def test_unauthorized_state(self) -> None:
        assert parse_device_state("unauthorized") == DeviceState.UNAUTHORIZED

    def test_bootloader_state(self) -> None:
        assert parse_device_state("bootloader") == DeviceState.BOOTLOADER

    def test_recovery_state(self) -> None:
        assert parse_device_state("recovery") == DeviceState.RECOVERY

    def test_sideload_state(self) -> None:
        assert parse_device_state("sideload") == DeviceState.SIDELOAD

    def test_unknown_state(self) -> None:
        assert parse_device_state("weird") == DeviceState.UNKNOWN

    def test_case_insensitive(self) -> None:
        assert parse_device_state("DEVICE") == DeviceState.DEVICE
        assert parse_device_state("Device") == DeviceState.DEVICE


class TestParseDevicesOutput:
    """Tests for parse_devices_output."""

    def test_empty_output(self) -> None:
        output = "List of devices attached\n"
        result = parse_devices_output(output)
        assert result == []

    def test_single_device(self) -> None:
        output = """List of devices attached
127.0.0.1:6555         device product:vbox86p model:Nexus_4 device:vbox86p transport_id:3
"""
        result = parse_devices_output(output)
        assert len(result) == 1
        device_id, state, props = result[0]
        assert device_id == "127.0.0.1:6555"
        assert state == DeviceState.DEVICE
        assert props["model"] == "Nexus_4"
        assert props["product"] == "vbox86p"
        assert props["transport_id"] == "3"

    def test_multiple_devices(self) -> None:
        output = """List of devices attached
emulator-5554          device product:sdk_phone model:Android_SDK transport_id:1
ABCD1234               device product:walleye model:Pixel_2 transport_id:2
192.168.1.100:5555     device product:beyond model:Galaxy_S10 transport_id:3
"""
        result = parse_devices_output(output)
        assert len(result) == 3
        assert result[0][0] == "emulator-5554"
        assert result[1][0] == "ABCD1234"
        assert result[2][0] == "192.168.1.100:5555"

    def test_offline_device(self) -> None:
        output = """List of devices attached
ABCD1234               offline
"""
        result = parse_devices_output(output)
        assert len(result) == 1
        assert result[0][1] == DeviceState.OFFLINE
        assert result[0][2] == {}

    def test_unauthorized_device(self) -> None:
        output = """List of devices attached
XYZ789               unauthorized
"""
        result = parse_devices_output(output)
        assert len(result) == 1
        assert result[0][1] == DeviceState.UNAUTHORIZED

    def test_mixed_states(self) -> None:
        output = """List of devices attached
device1                device product:test model:Test_1 transport_id:1
device2                offline
device3                unauthorized
"""
        result = parse_devices_output(output)
        assert len(result) == 3
        assert result[0][1] == DeviceState.DEVICE
        assert result[1][1] == DeviceState.OFFLINE
        assert result[2][1] == DeviceState.UNAUTHORIZED

    def test_whitespace_handling(self) -> None:
        output = """List of devices attached

device1                device

"""
        result = parse_devices_output(output)
        assert len(result) == 1


class TestParseUsersOutput:
    """Tests for parse_users_output."""

    def test_single_user(self) -> None:
        output = """Users:
        UserInfo{0:Owner:4c13} running
"""
        result = parse_users_output(output)
        assert result == [0]

    def test_multiple_users(self) -> None:
        output = """Users:
        UserInfo{0:Owner:4c13} running
        UserInfo{10:Work:30} running
        UserInfo{150:Guest:14}
"""
        result = parse_users_output(output)
        assert result == [0, 10, 150]

    def test_empty_output(self) -> None:
        output = "Users:\n"
        result = parse_users_output(output)
        assert result == []


class TestParsePackagesOutput:
    """Tests for parse_packages_output."""

    def test_parse_packages(self) -> None:
        output = """package:com.android.chrome
package:com.google.android.apps.maps
package:org.mozilla.firefox
"""
        result = parse_packages_output(output)
        assert result == [
            "com.android.chrome",
            "com.google.android.apps.maps",
            "org.mozilla.firefox",
        ]

    def test_empty_output(self) -> None:
        result = parse_packages_output("")
        assert result == []

    def test_whitespace_handling(self) -> None:
        output = """
  package:com.test.app1
package:com.test.app2

"""
        result = parse_packages_output(output)
        assert len(result) == 2
