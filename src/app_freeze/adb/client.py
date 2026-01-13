"""ADB client wrapper for all adb interactions."""

import shutil
import subprocess
from typing import Final

from app_freeze.adb.errors import (
    ADBCommandError,
    ADBDeviceNotFoundError,
    ADBNotFoundError,
    ADBTimeoutError,
)
from app_freeze.adb.models import DeviceCache, DeviceInfo
from app_freeze.adb.parser import parse_devices_output, parse_users_output

DEFAULT_TIMEOUT: Final[float] = 30.0
PROP_TIMEOUT: Final[float] = 5.0


class ADBClient:
    """Client for ADB command execution with caching and error handling."""

    def __init__(self, adb_path: str | None = None, default_timeout: float = DEFAULT_TIMEOUT):
        """
        Initialize ADB client.

        Args:
            adb_path: Explicit path to adb binary. If None, searches PATH.
            default_timeout: Default timeout for adb commands in seconds.
        """
        self._adb_path = adb_path or self._find_adb()
        self._default_timeout = default_timeout
        self._cache = DeviceCache()

    @staticmethod
    def _find_adb() -> str:
        """Find adb binary in PATH."""
        path = shutil.which("adb")
        if not path:
            raise ADBNotFoundError()
        return path

    @staticmethod
    def check_adb_available() -> bool:
        """Check if adb is available on the system."""
        return shutil.which("adb") is not None

    def _run(
        self,
        args: list[str],
        timeout: float | None = None,
        device_id: str | None = None,
    ) -> tuple[str, str]:
        """
        Execute an adb command.

        Args:
            args: Command arguments (without 'adb' prefix).
            timeout: Command timeout in seconds.
            device_id: Target device ID for the command.

        Returns:
            Tuple of (stdout, stderr).

        Raises:
            ADBTimeoutError: If command times out.
            ADBCommandError: If command fails.
        """
        cmd = [self._adb_path]
        if device_id:
            cmd.extend(["-s", device_id])
        cmd.extend(args)

        timeout = timeout or self._default_timeout
        cmd_str = " ".join(cmd)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as e:
            raise ADBTimeoutError(cmd_str, timeout) from e

        if result.returncode != 0:
            # Check for device not found error
            if "device" in result.stderr.lower() and (
                "not found" in result.stderr.lower() or "offline" in result.stderr.lower()
            ):
                raise ADBDeviceNotFoundError(device_id or "unknown")
            raise ADBCommandError(cmd_str, result.returncode, result.stderr)

        return result.stdout, result.stderr

    def list_devices(self, use_cache: bool = False) -> list[DeviceInfo]:
        """
        List all connected devices.

        Args:
            use_cache: If True, returns cached device info when available.

        Returns:
            List of connected devices with basic info.
        """
        stdout, _ = self._run(["devices", "-l"], timeout=PROP_TIMEOUT)
        parsed = parse_devices_output(stdout)

        devices: list[DeviceInfo] = []
        for device_id, state, props in parsed:
            # Check cache first if requested
            if use_cache:
                cached = self._cache.get(device_id)
                if cached is not None and cached.state == state:
                    devices.append(cached)
                    continue

            device = DeviceInfo(
                device_id=device_id,
                state=state,
                model=props.get("model", "").replace("_", " "),
                product=props.get("product", ""),
                transport_id=int(props.get("transport_id", 0)),
            )
            devices.append(device)

        return devices

    def get_device_info(self, device_id: str, force_refresh: bool = False) -> DeviceInfo:
        """
        Get complete device information including Android version.

        Args:
            device_id: The device ID to query.
            force_refresh: If True, bypasses cache.

        Returns:
            Complete device information.

        Raises:
            ADBDeviceNotFoundError: If device is not connected.
        """
        # Check cache
        if not force_refresh:
            cached = self._cache.get(device_id)
            if cached is not None and cached.sdk_level > 0:
                return cached

        # Verify device exists
        devices = self.list_devices()
        device = next((d for d in devices if d.device_id == device_id), None)
        if device is None:
            raise ADBDeviceNotFoundError(device_id)

        if not device.is_ready:
            return device

        # Fetch detailed properties
        model = self._get_prop(device_id, "ro.product.model")
        manufacturer = self._get_prop(device_id, "ro.product.manufacturer")
        android_version = self._get_prop(device_id, "ro.build.version.release")
        sdk_str = self._get_prop(device_id, "ro.build.version.sdk")

        try:
            sdk_level = int(sdk_str) if sdk_str else 0
        except ValueError:
            sdk_level = 0

        full_info = DeviceInfo(
            device_id=device_id,
            state=device.state,
            model=model or device.model,
            manufacturer=manufacturer,
            android_version=android_version,
            sdk_level=sdk_level,
            product=device.product,
            transport_id=device.transport_id,
        )

        # Cache the result
        self._cache.set(device_id, full_info)
        return full_info

    def _get_prop(self, device_id: str, prop: str) -> str:
        """Get a device property via getprop."""
        try:
            stdout, _ = self._run(
                ["shell", "getprop", prop],
                device_id=device_id,
                timeout=PROP_TIMEOUT,
            )
            return stdout.strip()
        except (ADBCommandError, ADBTimeoutError):
            return ""

    def list_users(self, device_id: str) -> list[int]:
        """
        List all user IDs on the device.

        Args:
            device_id: Target device ID.

        Returns:
            List of user IDs.
        """
        stdout, _ = self._run(["shell", "pm", "list", "users"], device_id=device_id)
        return parse_users_output(stdout)

    def invalidate_cache(self, device_id: str | None = None) -> None:
        """
        Invalidate cached device information.

        Args:
            device_id: Specific device to invalidate, or None for all.
        """
        if device_id:
            self._cache.invalidate(device_id)
        else:
            self._cache.clear()
