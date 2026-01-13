"""Tests for ADB models."""

import pytest

from app_freeze.adb.models import DeviceCache, DeviceInfo, DeviceState


class TestDeviceState:
    """Tests for DeviceState enum."""

    def test_all_states_defined(self) -> None:
        states = [
            DeviceState.DEVICE,
            DeviceState.OFFLINE,
            DeviceState.UNAUTHORIZED,
            DeviceState.BOOTLOADER,
            DeviceState.RECOVERY,
            DeviceState.SIDELOAD,
            DeviceState.UNKNOWN,
        ]
        assert len(states) == 7


class TestDeviceInfo:
    """Tests for DeviceInfo dataclass."""

    def test_basic_creation(self) -> None:
        device = DeviceInfo(device_id="test123", state=DeviceState.DEVICE)
        assert device.device_id == "test123"
        assert device.state == DeviceState.DEVICE
        assert device.model == ""
        assert device.sdk_level == 0

    def test_full_creation(self) -> None:
        device = DeviceInfo(
            device_id="ABC123",
            state=DeviceState.DEVICE,
            model="Pixel 5",
            manufacturer="Google",
            android_version="14",
            sdk_level=34,
            product="redfin",
            transport_id=1,
        )
        assert device.manufacturer == "Google"
        assert device.android_version == "14"
        assert device.sdk_level == 34

    def test_is_ready_true(self) -> None:
        device = DeviceInfo(device_id="test", state=DeviceState.DEVICE)
        assert device.is_ready is True

    def test_is_ready_false_offline(self) -> None:
        device = DeviceInfo(device_id="test", state=DeviceState.OFFLINE)
        assert device.is_ready is False

    def test_is_ready_false_unauthorized(self) -> None:
        device = DeviceInfo(device_id="test", state=DeviceState.UNAUTHORIZED)
        assert device.is_ready is False

    def test_display_name_with_both(self) -> None:
        device = DeviceInfo(
            device_id="test",
            state=DeviceState.DEVICE,
            model="Pixel 5",
            manufacturer="Google",
        )
        assert device.display_name == "Google Pixel 5"

    def test_display_name_model_only(self) -> None:
        device = DeviceInfo(
            device_id="test",
            state=DeviceState.DEVICE,
            model="Pixel 5",
        )
        assert device.display_name == "Pixel 5"

    def test_display_name_fallback_to_id(self) -> None:
        device = DeviceInfo(device_id="emulator-5554", state=DeviceState.DEVICE)
        assert device.display_name == "emulator-5554"

    def test_frozen(self) -> None:
        device = DeviceInfo(device_id="test", state=DeviceState.DEVICE)
        with pytest.raises(AttributeError):
            device.device_id = "changed"  # type: ignore[misc]


class TestDeviceCache:
    """Tests for DeviceCache."""

    def test_get_nonexistent(self) -> None:
        cache = DeviceCache()
        assert cache.get("nonexistent") is None

    def test_set_and_get(self) -> None:
        cache = DeviceCache()
        device = DeviceInfo(device_id="test", state=DeviceState.DEVICE)
        cache.set("test", device)
        assert cache.get("test") == device

    def test_invalidate(self) -> None:
        cache = DeviceCache()
        device = DeviceInfo(device_id="test", state=DeviceState.DEVICE)
        cache.set("test", device)
        cache.invalidate("test")
        assert cache.get("test") is None

    def test_invalidate_nonexistent(self) -> None:
        cache = DeviceCache()
        cache.invalidate("nonexistent")  # Should not raise

    def test_clear(self) -> None:
        cache = DeviceCache()
        device1 = DeviceInfo(device_id="test1", state=DeviceState.DEVICE)
        device2 = DeviceInfo(device_id="test2", state=DeviceState.DEVICE)
        cache.set("test1", device1)
        cache.set("test2", device2)
        cache.clear()
        assert cache.get("test1") is None
        assert cache.get("test2") is None
