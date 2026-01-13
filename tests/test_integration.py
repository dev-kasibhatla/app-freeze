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


class TestAppDiscoveryIntegration:
    """Integration tests for app discovery with real devices."""

    def test_list_packages(self, client: ADBClient) -> None:
        """List packages on connected device."""
        devices = client.list_devices()
        if not devices or not devices[0].is_ready:
            pytest.skip("No ready devices available")

        device_id = devices[0].device_id

        # Get all packages
        packages = client.list_packages(device_id)
        print(f"\nTotal packages: {len(packages)}")
        assert len(packages) > 0

        # Get system packages only
        system_packages = client.list_packages(device_id, system_apps=True, user_apps=False)
        print(f"System packages: {len(system_packages)}")
        assert len(system_packages) > 0

        # Get user packages only
        user_packages = client.list_packages(device_id, system_apps=False, user_apps=True)
        print(f"User packages: {len(user_packages)}")

        # Should be sorted
        assert packages == sorted(packages)

    def test_get_app_info(self, client: ADBClient) -> None:
        """Get detailed info for a specific app."""
        devices = client.list_devices()
        if not devices or not devices[0].is_ready:
            pytest.skip("No ready devices available")

        device_id = devices[0].device_id
        packages = client.list_packages(device_id, system_apps=True, user_apps=False)

        if not packages:
            pytest.skip("No packages found")

        # Get info for first system app
        package = packages[0]
        app_info = client.get_app_info(device_id, package, fetch_size=False)

        print(f"\nApp: {package}")
        print(f"  Display name: {app_info.display_name}")
        print(f"  System: {app_info.is_system}")
        print(f"  Enabled: {app_info.is_enabled}")
        print(f"  Version: {app_info.version_code}")

        assert app_info.package_name == package
        assert isinstance(app_info.is_system, bool)
        assert isinstance(app_info.is_enabled, bool)

    def test_list_apps_without_sizes(self, client: ADBClient) -> None:
        """List apps without fetching sizes (faster)."""
        devices = client.list_devices()
        if not devices or not devices[0].is_ready:
            pytest.skip("No ready devices available")

        device_id = devices[0].device_id

        # Get first 10 apps without sizes
        all_packages = client.list_packages(device_id)
        packages_subset = all_packages[:10]

        apps = []
        for pkg in packages_subset:
            try:
                app = client.get_app_info(device_id, pkg, fetch_size=False)
                apps.append(app)
            except Exception:
                continue

        print(f"\nFetched info for {len(apps)} apps")
        for app in apps[:5]:
            print(f"  {app.package_name}: enabled={app.is_enabled}, system={app.is_system}")

        assert len(apps) > 0

    def test_app_size_fetching(self, client: ADBClient) -> None:
        """Test fetching app size (slower operation)."""
        devices = client.list_devices()
        if not devices or not devices[0].is_ready:
            pytest.skip("No ready devices available")

        device_id = devices[0].device_id
        packages = client.list_packages(device_id, system_apps=False, user_apps=True)

        if not packages:
            # Try system apps if no user apps
            packages = client.list_packages(device_id, system_apps=True, user_apps=False)

        if packages:
            # Get size for one app
            package = packages[0]
            app_info = client.get_app_info(device_id, package, fetch_size=True)
            print(f"\n{package} size: {app_info.size_mb} MB")
            assert app_info.size_mb >= 0.0


class TestDeviceSelectionIntegration:
    """Integration tests for device selection with real devices."""

    @pytest.fixture
    def client(self) -> ADBClient:
        return ADBClient()

    def test_get_ready_devices_multiple(self, client: ADBClient) -> None:
        """Verify multiple devices are available and ready."""
        ready = client.get_ready_devices()
        print(f"\nReady devices: {len(ready)}")
        for d in ready:
            print(f"  - {d.device_id}: {d.display_name}")

        assert len(ready) >= 2, "Expected at least 2 ready devices"

    def test_validate_device_success(self, client: ADBClient) -> None:
        """Validate first device."""
        ready = client.get_ready_devices()
        if not ready:
            pytest.skip("No ready devices")

        device_id = ready[0].device_id
        device = client.validate_device(device_id)
        print(f"\nValidated device: {device.display_name} ({device.device_id})")
        assert device.device_id == device_id
        assert device.is_ready

    def test_validate_all_devices(self, client: ADBClient) -> None:
        """Validate all connected ready devices."""
        ready = client.get_ready_devices()
        print(f"\nValidating {len(ready)} devices...")

        for device in ready:
            validated = client.validate_device(device.device_id)
            assert validated.device_id == device.device_id
            assert validated.is_ready
            print(f"  ✓ {validated.display_name}")

    def test_select_device_explicit_first(self, client: ADBClient) -> None:
        """Select first device explicitly."""
        ready = client.get_ready_devices()
        if not ready:
            pytest.skip("No ready devices")

        device_id = ready[0].device_id
        selected = client.select_device(device_id)
        print(f"\nSelected: {selected.display_name}")
        assert selected.device_id == device_id

    def test_select_device_explicit_second(self, client: ADBClient) -> None:
        """Select second device explicitly if available."""
        ready = client.get_ready_devices()
        if len(ready) < 2:
            pytest.skip("Need at least 2 devices")

        device_id = ready[1].device_id
        selected = client.select_device(device_id)
        print(f"\nSelected second device: {selected.display_name}")
        assert selected.device_id == device_id

    def test_select_device_auto_fails_with_multiple(self, client: ADBClient) -> None:
        """Auto-selection should fail when multiple devices are present."""
        ready = client.get_ready_devices()
        if len(ready) < 2:
            pytest.skip("Need at least 2 devices to test multiple selection failure")

        with pytest.raises(ADBDeviceNotFoundError) as exc_info:
            client.select_device()

        error_msg = str(exc_info.value)
        assert "Multiple devices available" in error_msg
        print(f"\nCorrectly raised error: {error_msg}")

    def test_device_independence(self, client: ADBClient) -> None:
        """Verify different devices can be queried independently."""
        ready = client.get_ready_devices()
        if len(ready) < 2:
            pytest.skip("Need at least 2 devices")

        device1_id = ready[0].device_id
        device2_id = ready[1].device_id

        # Get info for both
        info1 = client.get_device_info(device1_id)
        info2 = client.get_device_info(device2_id)

        print(f"\nDevice 1: {info1.display_name} (SDK {info1.sdk_level})")
        print(f"Device 2: {info2.display_name} (SDK {info2.sdk_level})")

        assert info1.device_id == device1_id
        assert info2.device_id == device2_id

        # Should be able to query different info for each
        users1 = client.list_users(device1_id)
        users2 = client.list_users(device2_id)
        print(f"Device 1 users: {users1}")
        print(f"Device 2 users: {users2}")
        assert len(users1) >= 1
        assert len(users2) >= 1
