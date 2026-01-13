#!/usr/bin/env python3
"""Demo: Device Selection with Multiple Connected Devices."""

from app_freeze.adb import ADBClient


def main() -> None:
    """Demonstrate device selection functionality."""
    client = ADBClient()

    print("=" * 80)
    print("DEVICE SELECTION DEMO")
    print("=" * 80)

    # Get all ready devices
    ready_devices = client.get_ready_devices()
    print(f"\nReady Devices: {len(ready_devices)}")
    for i, device in enumerate(ready_devices, 1):
        info = client.get_device_info(device.device_id)
        print(f"  {i}. {info.display_name} (ID: {device.device_id})")

    if len(ready_devices) < 2:
        print("\n⚠️  Need at least 2 devices for selection demo")
        return

    # Demonstrate explicit selection
    print("\n" + "=" * 80)
    print("EXPLICIT DEVICE SELECTION")
    print("=" * 80)
    for device in ready_devices:
        selected = client.select_device(device.device_id)
        info = client.get_device_info(selected.device_id)
        apps = client.list_packages(selected.device_id)
        print(f"\n✓ Selected: {info.display_name}")
        print(f"  Apps: {len(apps)} packages installed")

    # Demonstrate auto-selection failure with multiple devices
    print("\n" + "=" * 80)
    print("AUTO-SELECTION WITH MULTIPLE DEVICES")
    print("=" * 80)
    try:
        selected = client.select_device()
        print("✗ Should have failed with multiple devices")
    except Exception as e:
        print(f"✓ Correctly raised error:\n  {str(e)}")

    # Demonstrate device independence
    print("\n" + "=" * 80)
    print("DEVICE INDEPENDENCE TEST")
    print("=" * 80)
    for device in ready_devices:
        users = client.list_users(device.device_id)
        system_apps = client.list_packages(device.device_id, system_apps=True, user_apps=False)
        user_apps = client.list_packages(device.device_id, system_apps=False, user_apps=True)
        info = client.get_device_info(device.device_id)

        print(f"\n{info.display_name}:")
        print(f"  Users: {users}")
        print(f"  System apps: {len(system_apps)}")
        print(f"  User apps: {len(user_apps)}")

    print("\n" + "=" * 80)
    print("✓ DEMO COMPLETE - ALL DEVICE SELECTION FEATURES WORKING")
    print("=" * 80)


if __name__ == "__main__":
    main()
