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


def parse_package_path(output: str) -> str | None:
    """
    Parse 'pm path' output to get the base APK path.
    Returns the directory containing the APK.
    """
    for line in output.strip().splitlines():
        line = line.strip()
        if line.startswith("package:") and "base.apk" in line:
            path = line[8:]  # Remove 'package:' prefix
            # Extract directory path (remove /base.apk)
            if path.endswith("/base.apk"):
                return path[: -len("/base.apk")]
    return None


def parse_dumpsys_package(output: str, user_id: int = 0) -> dict[str, str | int | bool]:
    """
    Parse 'dumpsys package <package>' output for app details.
    Returns dict with enabled state, app label, and other metadata.
    """
    result: dict[str, str | int | bool] = {
        "enabled": True,  # Default to enabled
        "version_code": 0,
        "app_label": "",
    }

    # Look for user-specific state (e.g., "User 0: ... enabled=0")
    user_pattern = re.compile(rf"User {user_id}:.*?enabled=(\d+)")
    version_pattern = re.compile(r"versionCode=(\d+)")
    # App label can appear as: applicationInfo=... labelRes=... nonLocalizedLabel=...
    # or in ApplicationInfo section
    label_pattern = re.compile(r"(?:nonLocalizedLabel|labelRes)=([^\s]+)")

    for line in output.splitlines():
        # Check for enabled state
        user_match = user_pattern.search(line)
        if user_match:
            # enabled=0 means ENABLED, enabled=2 means DISABLED_USER, enabled=3 means DEFAULT
            enabled_value = int(user_match.group(1))
            result["enabled"] = enabled_value in (0, 1)  # 0 and 1 are enabled states

        # Check for version code
        version_match = version_pattern.search(line)
        if version_match:
            result["version_code"] = int(version_match.group(1))

        # Check for app label
        label_match = label_pattern.search(line)
        if label_match and not result["app_label"]:
            label = label_match.group(1).strip()
            # Remove quotes and resource IDs
            if label and not label.startswith("0x"):
                result["app_label"] = label.strip('"')

    return result


def parse_du_output(output: str) -> float:
    """
    Parse 'du -sh' output to extract size in MB.
    Returns size in MB.
    """
    line = output.strip().split("\n")[0] if output.strip() else ""
    parts = line.split()
    if len(parts) < 1:
        return 0.0

    size_str = parts[0]
    # Parse size with unit (e.g., "25M", "1.5G", "512K")
    match = re.match(r"([\d.]+)([KMGT])?", size_str)
    if not match:
        return 0.0

    value = float(match.group(1))
    unit = match.group(2) or "K"

    # Convert to MB
    multipliers = {"K": 0.001, "M": 1.0, "G": 1024.0, "T": 1024.0 * 1024.0}
    return round(value * multipliers.get(unit, 1.0), 2)
