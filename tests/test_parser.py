"""Tests for ADB parser module."""

from app_freeze.adb.models import DeviceState
from app_freeze.adb.parser import (
    parse_device_state,
    parse_devices_output,
    parse_du_output,
    parse_dumpsys_package,
    parse_package_path,
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


class TestParsePackagePath:
    """Tests for parse_package_path."""

    def test_single_apk(self) -> None:
        output = "package:/data/app/com.example.app/base.apk"
        result = parse_package_path(output)
        assert result == "/data/app/com.example.app"

    def test_split_apks(self) -> None:
        base = "/data/app/~~F49ae31o-kKiA0xvdaky0g=="
        pkg = "com.android.chrome--VzEbVhPAXFIp4b-jzB8rQ=="
        base_path = f"{base}/{pkg}"
        output = f"""package:{base_path}/base.apk
package:{base_path}/split_chrome.apk"""
        result = parse_package_path(output)
        assert result == base_path

    def test_no_base_apk(self) -> None:
        output = "package:/system/app/Settings/Settings.apk"
        result = parse_package_path(output)
        assert result is None

    def test_empty_output(self) -> None:
        result = parse_package_path("")
        assert result is None


class TestParseDumpsysPackage:
    """Tests for parse_dumpsys_package."""

    def test_enabled_app(self) -> None:
        output = """Packages:
  Package [com.android.chrome]
    versionCode=725815837 minSdk=29 targetSdk=35
    User 0: installed=true hidden=false suspended=false stopped=false notLaunched=false enabled=0
"""
        result = parse_dumpsys_package(output, user_id=0)
        assert result["enabled"] is True
        assert result["version_code"] == 725815837

    def test_disabled_app(self) -> None:
        output = """Packages:
  Package [com.android.nfc]
    versionCode=340000000 minSdk=34 targetSdk=34
    User 0: installed=true hidden=false suspended=false stopped=false enabled=2
"""
        result = parse_dumpsys_package(output, user_id=0)
        assert result["enabled"] is False
        assert result["version_code"] == 340000000

    def test_multiple_users(self) -> None:
        output = """Packages:
  Package [com.example.app]
    versionCode=123 minSdk=21 targetSdk=30
    User 0: installed=true enabled=0
    User 10: installed=true enabled=2
"""
        # Query for user 0
        result_0 = parse_dumpsys_package(output, user_id=0)
        assert result_0["enabled"] is True

        # Query for user 10
        result_10 = parse_dumpsys_package(output, user_id=10)
        assert result_10["enabled"] is False

    def test_missing_data(self) -> None:
        output = "Some random output"
        result = parse_dumpsys_package(output, user_id=0)
        assert result["enabled"] is True  # Default
        assert result["version_code"] == 0  # Default


class TestParseDuOutput:
    """Tests for parse_du_output."""

    def test_megabytes(self) -> None:
        output = "25M\t/data/app/com.example.app"
        result = parse_du_output(output)
        assert result == 25.0

    def test_kilobytes(self) -> None:
        output = "512K\t/data/app/com.example.app"
        result = parse_du_output(output)
        assert result == 0.51  # 512K = 0.512MB

    def test_gigabytes(self) -> None:
        output = "1.5G\t/data/app/com.example.app"
        result = parse_du_output(output)
        assert result == 1536.0  # 1.5G = 1536MB

    def test_decimal_megabytes(self) -> None:
        output = "12.5M\t/data/app/com.example.app"
        result = parse_du_output(output)
        assert result == 12.5

    def test_no_unit(self) -> None:
        output = "1024\t/data/app/com.example.app"
        result = parse_du_output(output)
        assert result == 1.02  # Treated as KB

    def test_empty_output(self) -> None:
        result = parse_du_output("")
        assert result == 0.0

    def test_invalid_format(self) -> None:
        result = parse_du_output("invalid")
        assert result == 0.0
