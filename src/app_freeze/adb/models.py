"""Data models for ADB responses."""

from dataclasses import dataclass, field
from enum import Enum


class DeviceState(Enum):
    """ADB device connection states."""

    DEVICE = "device"  # Connected and ready
    OFFLINE = "offline"  # Not responding
    UNAUTHORIZED = "unauthorized"  # USB debugging not authorized
    BOOTLOADER = "bootloader"  # In bootloader mode
    RECOVERY = "recovery"  # In recovery mode
    SIDELOAD = "sideload"  # In sideload mode
    UNKNOWN = "unknown"  # Unknown state


@dataclass(frozen=True)
class DeviceInfo:
    """Complete Android device information."""

    device_id: str
    state: DeviceState
    model: str = ""
    manufacturer: str = ""
    android_version: str = ""
    sdk_level: int = 0
    product: str = ""
    transport_id: int = 0

    @property
    def is_ready(self) -> bool:
        """Check if device is ready for commands."""
        return self.state == DeviceState.DEVICE

    @property
    def display_name(self) -> str:
        """Human-readable device name."""
        if self.model and self.manufacturer:
            return f"{self.manufacturer} {self.model}"
        if self.model:
            return self.model
        return self.device_id


@dataclass(frozen=True)
class AppInfo:
    """Android application information."""

    package_name: str
    is_system: bool
    is_enabled: bool
    size_mb: float = 0.0
    version_code: int = 0
    app_label: str = ""  # Actual app name from Android manifest

    @property
    def display_name(self) -> str:
        """Human-readable app name."""
        # Use actual app label if available, otherwise derive from package
        if self.app_label:
            return self.app_label
        # Fallback: extract from package (e.g., com.android.chrome -> Chrome)
        parts = self.package_name.split(".")
        return parts[-1].replace("_", " ").title()


@dataclass
class DeviceCache:
    """Cache for device information to avoid redundant adb calls."""

    _cache: dict[str, DeviceInfo] = field(default_factory=dict)

    def get(self, device_id: str) -> DeviceInfo | None:
        """Get cached device info."""
        return self._cache.get(device_id)

    def set(self, device_id: str, info: DeviceInfo) -> None:
        """Cache device info."""
        self._cache[device_id] = info

    def invalidate(self, device_id: str) -> None:
        """Invalidate cache for a specific device."""
        self._cache.pop(device_id, None)

    def clear(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
