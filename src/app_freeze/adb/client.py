"""ADB client wrapper for all adb interactions."""

import concurrent.futures
import shutil
import subprocess
from collections.abc import Callable
from typing import Final

from app_freeze.adb.errors import (
    ADBCommandError,
    ADBDeviceDisconnectedError,
    ADBDeviceNotFoundError,
    ADBNotFoundError,
    ADBPermissionError,
    ADBTimeoutError,
)
from app_freeze.adb.models import AppInfo, DeviceCache, DeviceInfo
from app_freeze.adb.parser import (
    parse_devices_output,
    parse_du_output,
    parse_dumpsys_package,
    parse_package_path,
    parse_packages_output,
    parse_users_output,
)

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
            stderr_lower = result.stderr.lower()

            # Check for device disconnected/not found error
            if "device" in stderr_lower and (
                "not found" in stderr_lower
                or "offline" in stderr_lower
                or "disconnected" in stderr_lower
            ):
                if device_id:
                    raise ADBDeviceDisconnectedError(device_id)
                raise ADBDeviceNotFoundError(device_id or "unknown")

            # Check for permission errors
            if "permission denied" in stderr_lower or "insufficient permissions" in stderr_lower:
                operation = " ".join(args[:2]) if len(args) >= 2 else " ".join(args)
                raise ADBPermissionError(operation, device_id or "unknown")

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

    def get_ready_devices(self) -> list[DeviceInfo]:
        """
        Get only ready (connected and authorized) devices.

        Returns:
            List of devices with state == DEVICE (connected and ready).
        """
        all_devices = self.list_devices()
        return [d for d in all_devices if d.is_ready]

    def validate_device(self, device_id: str) -> DeviceInfo:
        """
        Validate that a device exists and is ready.

        Args:
            device_id: The device ID to validate.

        Returns:
            DeviceInfo for the device if ready.

        Raises:
            ADBDeviceNotFoundError: If device not found or not ready.
        """
        devices = self.list_devices()
        device = next((d for d in devices if d.device_id == device_id), None)
        if device is None:
            raise ADBDeviceNotFoundError(device_id)
        if not device.is_ready:
            raise ADBDeviceNotFoundError(device_id)
        return device

    def select_device(self, device_id: str | None = None) -> DeviceInfo:
        """
        Select a device, either explicitly or interactively if multiple are available.

        Args:
            device_id: Specific device ID to select. If None, auto-selects if only one
                       ready device exists.

        Returns:
            The selected DeviceInfo.

        Raises:
            ADBDeviceNotFoundError: If device not found, not ready, or no devices available.
        """
        if device_id:
            return self.validate_device(device_id)

        # Auto-select if only one ready device
        ready_devices = self.get_ready_devices()
        if len(ready_devices) == 0:
            raise ADBDeviceNotFoundError("No ready devices available")
        if len(ready_devices) == 1:
            return ready_devices[0]

        # Multiple devices available - user needs to select
        raise ADBDeviceNotFoundError(
            f"Multiple devices available ({len(ready_devices)}). "
            f"Please specify device ID: {', '.join(d.device_id for d in ready_devices)}"
        )

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

    def list_packages(
        self,
        device_id: str,
        system_apps: bool = True,
        user_apps: bool = True,
    ) -> list[str]:
        """
        List installed packages on the device.

        Args:
            device_id: Target device ID.
            system_apps: Include system apps.
            user_apps: Include third-party (user) apps.

        Returns:
            List of package names.
        """
        packages: set[str] = set()

        if system_apps:
            stdout, _ = self._run(["shell", "pm", "list", "packages", "-s"], device_id=device_id)
            packages.update(parse_packages_output(stdout))

        if user_apps:
            stdout, _ = self._run(["shell", "pm", "list", "packages", "-3"], device_id=device_id)
            packages.update(parse_packages_output(stdout))

        return sorted(packages)

    def get_app_info(
        self,
        device_id: str,
        package_name: str,
        user_id: int = 0,
        fetch_size: bool = False,
    ) -> AppInfo:
        """
        Get detailed information about a specific app.

        Args:
            device_id: Target device ID.
            package_name: Package name to query.
            user_id: User ID for app state check.
            fetch_size: If True, fetch app size (slower).

        Returns:
            App information.
        """
        # Determine if it's a system app
        is_system = self._is_system_app(device_id, package_name)

        # Get enabled state, version code, and app label via dumpsys
        dumpsys_stdout, _ = self._run(
            ["shell", "dumpsys", "package", package_name],
            device_id=device_id,
            timeout=10.0,
        )
        metadata = parse_dumpsys_package(dumpsys_stdout, user_id)
        is_enabled = bool(metadata.get("enabled", True))
        version_code = int(metadata.get("version_code", 0))
        app_label = str(metadata.get("app_label", ""))

        # Optionally get app size
        size_mb = 0.0
        if fetch_size:
            size_mb = self._get_app_size(device_id, package_name)

        return AppInfo(
            package_name=package_name,
            is_system=is_system,
            is_enabled=is_enabled,
            size_mb=size_mb,
            version_code=version_code,
            app_label=app_label,
        )

    def list_apps(
        self,
        device_id: str,
        user_id: int = 0,
        include_system: bool = True,
        include_user: bool = True,
        fetch_sizes: bool = False,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> list[AppInfo]:
        """
        List all apps on the device with detailed information.

        Args:
            device_id: Target device ID.
            user_id: User ID for app state check.
            include_system: Include system apps.
            include_user: Include third-party apps.
            fetch_sizes: If True, fetch app sizes (much slower).
            progress_callback: Optional callback(package_name, current, total) for progress.

        Returns:
            Sorted list of app information.
        """
        packages = self.list_packages(device_id, include_system, include_user)
        apps: list[AppInfo] = []
        total = len(packages)
        completed = 0

        def fetch_app(package: str) -> AppInfo | None:
            """Fetch single app info, returns None on error."""
            try:
                return self.get_app_info(device_id, package, user_id, fetch_sizes)
            except (ADBCommandError, ADBTimeoutError):
                return None

        # Use ThreadPoolExecutor for parallel fetching (max 8 workers)
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            # Submit all tasks
            future_to_pkg = {executor.submit(fetch_app, pkg): pkg for pkg in packages}

            # Process as they complete
            for future in concurrent.futures.as_completed(future_to_pkg):
                completed += 1
                pkg = future_to_pkg[future]
                if progress_callback:
                    progress_callback(pkg, completed, total)
                try:
                    app_info = future.result()
                    if app_info:
                        apps.append(app_info)
                except Exception:
                    # Skip apps that fail
                    pass

        # Sort alphabetically by package name
        return sorted(apps, key=lambda a: a.package_name.lower())

    def _is_system_app(self, device_id: str, package_name: str) -> bool:
        """Check if a package is a system app."""
        try:
            stdout, _ = self._run(
                ["shell", "pm", "list", "packages", "-s", package_name],
                device_id=device_id,
                timeout=PROP_TIMEOUT,
            )
            # If the package appears in system apps list, it's a system app
            return f"package:{package_name}" in stdout
        except (ADBCommandError, ADBTimeoutError):
            return False

    def _get_app_size(self, device_id: str, package_name: str) -> float:
        """Get app size in MB."""
        try:
            # Get package path
            path_stdout, _ = self._run(
                ["shell", "pm", "path", package_name],
                device_id=device_id,
                timeout=PROP_TIMEOUT,
            )
            app_dir = parse_package_path(path_stdout)
            if not app_dir:
                return 0.0

            # Get directory size
            size_stdout, _ = self._run(
                ["shell", "du", "-sh", app_dir],
                device_id=device_id,
                timeout=10.0,
            )
            return parse_du_output(size_stdout)
        except (ADBCommandError, ADBTimeoutError, ADBPermissionError):
            return 0.0

    def disable_app(
        self,
        device_id: str,
        package_name: str,
        user_id: int = 0,
    ) -> tuple[bool, str | None]:
        """
        Disable an app for a specific user.

        Args:
            device_id: Target device ID.
            package_name: Package name to disable.
            user_id: User ID for the operation.

        Returns:
            Tuple of (success, error_message).
        """
        try:
            stdout, stderr = self._run(
                ["shell", "pm", "disable-user", "--user", str(user_id), package_name],
                device_id=device_id,
                timeout=10.0,
            )
            # Check for success indicators
            output = stdout + stderr
            if "disabled" in output.lower() or "new state" in output.lower():
                return True, None
            if "error" in output.lower() or "exception" in output.lower():
                return False, output.strip()
            # Assume success if no error
            return True, None
        except ADBCommandError as e:
            return False, str(e)
        except ADBTimeoutError as e:
            return False, str(e)

    def enable_app(
        self,
        device_id: str,
        package_name: str,
        user_id: int = 0,
    ) -> tuple[bool, str | None]:
        """
        Enable an app for a specific user.

        Args:
            device_id: Target device ID.
            package_name: Package name to enable.
            user_id: User ID for the operation.

        Returns:
            Tuple of (success, error_message).
        """
        try:
            stdout, stderr = self._run(
                ["shell", "pm", "enable", "--user", str(user_id), package_name],
                device_id=device_id,
                timeout=10.0,
            )
            # Check for success indicators
            output = stdout + stderr
            if "enabled" in output.lower() or "new state" in output.lower():
                return True, None
            if "error" in output.lower() or "exception" in output.lower():
                return False, output.strip()
            # Assume success if no error
            return True, None
        except ADBCommandError as e:
            return False, str(e)
        except ADBTimeoutError as e:
            return False, str(e)

    def enable_disable_apps(
        self,
        device_id: str,
        packages: list[str],
        enable: bool,
        user_ids: list[int] | None = None,
    ) -> dict[str, tuple[bool, str | None]]:
        """
        Enable or disable multiple apps for all users.

        Args:
            device_id: Target device ID.
            packages: List of package names.
            enable: True to enable, False to disable.
            user_ids: List of user IDs (fetches from device if None).

        Returns:
            Dict mapping package_name to (success, error_message).
        """
        if user_ids is None:
            user_ids = self.list_users(device_id)
            if not user_ids:
                user_ids = [0]

        results: dict[str, tuple[bool, str | None]] = {}
        action = self.enable_app if enable else self.disable_app

        for package in packages:
            # Execute for all users, track overall success
            all_success = True
            last_error: str | None = None

            for user_id in user_ids:
                success, error = action(device_id, package, user_id)
                if not success:
                    all_success = False
                    last_error = error

            results[package] = (all_success, last_error)

        return results
