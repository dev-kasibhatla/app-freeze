#!/usr/bin/env python3
"""Demo script to showcase ADB layer and app discovery with multiple devices."""

from app_freeze.adb import ADBClient


def main() -> None:
    """Run demo showing device and app discovery."""
    client = ADBClient()

    # List all connected devices
    print("=" * 80)
    print("CONNECTED DEVICES")
    print("=" * 80)
    devices = client.list_devices()
    print(f"Found {len(devices)} device(s):\n")

    for device in devices:
        if not device.is_ready:
            print(f"  ⚠️  {device.device_id} - {device.state.value}")
            continue

        # Get full device info
        info = client.get_device_info(device.device_id)
        print(f"  ✓ {info.display_name}")
        print(f"    ID: {info.device_id}")
        print(f"    Android {info.android_version} (SDK {info.sdk_level})")

        # List users
        users = client.list_users(device.device_id)
        print(f"    Users: {users}")
        print()

    # App discovery on first ready device
    ready_device = next((d for d in devices if d.is_ready), None)
    if not ready_device:
        print("No ready devices for app discovery")
        return

    print("=" * 80)
    print(f"APP DISCOVERY ON {ready_device.display_name}")
    print("=" * 80)

    # Get package counts
    all_packages = client.list_packages(ready_device.device_id)
    system_packages = client.list_packages(
        ready_device.device_id, system_apps=True, user_apps=False
    )
    user_packages = client.list_packages(ready_device.device_id, system_apps=False, user_apps=True)

    print(f"Total packages: {len(all_packages)}")
    print(f"System packages: {len(system_packages)}")
    print(f"User packages: {len(user_packages)}")
    print()

    # Show sample apps
    print("Sample User Apps:")
    for pkg in user_packages[:5]:
        app = client.get_app_info(ready_device.device_id, pkg, fetch_size=False)
        status = "✓ enabled" if app.is_enabled else "✗ disabled"
        print(f"  {status} - {pkg}")
    print()

    # Check for disabled apps
    disabled_count = 0
    for pkg in all_packages[:20]:
        try:
            app = client.get_app_info(ready_device.device_id, pkg, fetch_size=False)
            if not app.is_enabled:
                disabled_count += 1
                print(f"  ✗ DISABLED: {pkg}")
        except Exception:
            pass

    if disabled_count == 0:
        print("  No disabled apps found in sample")
    print()

    print("=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
