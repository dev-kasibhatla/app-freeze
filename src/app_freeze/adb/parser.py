"""Parsers for ADB command outputs."""

import re

from app_freeze.adb.models import DeviceState


def parse_device_state(state_str: str) -> DeviceState:
    """Parse device state string to enum."""
    state_map = {
        "device": DeviceState.DEVICE,
        "offline": DeviceState.OFFLINE,
        "unauthorized": DeviceState.UNAUTHORIZED,
        "bootloader": DeviceState.BOOTLOADER,
        "recovery": DeviceState.RECOVERY,
        "sideload": DeviceState.SIDELOAD,
    }
    return state_map.get(state_str.lower(), DeviceState.UNKNOWN)


def parse_devices_output(output: str) -> list[tuple[str, DeviceState, dict[str, str]]]:
    """
    Parse 'adb devices -l' output.
    Returns list of (device_id, state, properties).
    """
    devices: list[tuple[str, DeviceState, dict[str, str]]] = []

    for line in output.strip().splitlines():
        line = line.strip()
        # Skip header and empty lines
        if not line or line.startswith("List of devices"):
            continue

        parts = line.split()
        if len(parts) < 2:
            continue

        device_id = parts[0]
        state = parse_device_state(parts[1])

        # Parse additional properties (key:value pairs)
        props: dict[str, str] = {}
        for part in parts[2:]:
            if ":" in part:
                key, value = part.split(":", 1)
                props[key] = value

        devices.append((device_id, state, props))

    return devices


def parse_users_output(output: str) -> list[int]:
    """
    Parse 'pm list users' output.
    Returns list of user IDs.
    """
    users: list[int] = []
    # Pattern: UserInfo{0:Owner:flags}
    pattern = re.compile(r"UserInfo\{(\d+):")

    for line in output.strip().splitlines():
        match = pattern.search(line)
        if match:
            users.append(int(match.group(1)))

    return users


def parse_packages_output(output: str) -> list[str]:
    """
    Parse 'pm list packages' output.
    Returns list of package names.
    """
    packages: list[str] = []

    for line in output.strip().splitlines():
        line = line.strip()
        if line.startswith("package:"):
            packages.append(line[8:])  # Remove 'package:' prefix

    return packages
