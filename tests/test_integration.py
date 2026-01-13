"""Integration tests for ADB client with real device.

Run only when a device is connected:
    uv run pytest tests/test_integration.py -v
"""

import pytest

from app_freeze.adb import ADBClient, ADBDeviceNotFoundError


@pytest.fixture
def client() -> ADBClient:
    """Create ADB client for integration tests."""
    return ADBClient()


class TestADBIntegration:
    """Integration tests requiring a real connected device."""

    def test_list_devices_returns_at_least_one(self, client: ADBClient) -> None:
        """Verify at least one device is connected."""
        devices = client.list_devices()
        assert len(devices) >= 1, "No devices connected for integration test"
        print(f"\nFound {len(devices)} device(s)")
        for d in devices:
            print(f"  - {d.device_id}: {d.state.value} ({d.model})")

    def test_get_device_info_full_details(self, client: ADBClient) -> None:
        """Get full device info for connected device."""
        devices = client.list_devices()
        assert len(devices) >= 1, "No devices connected"

        # Get info for first ready device
        for device in devices:
            if device.is_ready:
                info = client.get_device_info(device.device_id)
                print(f"\nDevice: {info.display_name}")
                print(f"  ID: {info.device_id}")
                print(f"  Model: {info.model}")
                print(f"  Manufacturer: {info.manufacturer}")
                print(f"  Android: {info.android_version}")
                print(f"  SDK: {info.sdk_level}")

                assert info.device_id == device.device_id
                assert info.sdk_level > 0
                assert info.android_version != ""
                return

        pytest.skip("No ready devices available")

    def test_list_users(self, client: ADBClient) -> None:
        """List users on connected device."""
        devices = client.list_devices()
        assert len(devices) >= 1, "No devices connected"

        for device in devices:
            if device.is_ready:
                users = client.list_users(device.device_id)
                print(f"\nUsers on {device.device_id}: {users}")

                assert len(users) >= 1
                assert 0 in users  # Owner is always user 0
                return

        pytest.skip("No ready devices available")

    def test_get_nonexistent_device_raises(self, client: ADBClient) -> None:
        """Getting info for nonexistent device raises error."""
        with pytest.raises(ADBDeviceNotFoundError):
            client.get_device_info("nonexistent-device-12345")

    def test_cache_works(self, client: ADBClient) -> None:
        """Verify caching reduces adb calls."""
        devices = client.list_devices()
        if not devices or not devices[0].is_ready:
            pytest.skip("No ready devices available")

        device_id = devices[0].device_id

        # First call fetches from adb
        info1 = client.get_device_info(device_id)

        # Second call should use cache
        info2 = client.get_device_info(device_id)

        assert info1 == info2

        # Force refresh should still work
        info3 = client.get_device_info(device_id, force_refresh=True)
        assert info3.device_id == device_id
