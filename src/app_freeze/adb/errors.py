"""Structured error types for ADB operations."""


class ADBError(Exception):
    """Base exception for all ADB errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ADBNotFoundError(ADBError):
    """ADB tool not found on the system."""

    def __init__(self) -> None:
        super().__init__(
            "adb not found. Install Android SDK platform-tools and ensure 'adb' is in PATH.\n"
            "macOS: brew install android-platform-tools\n"
            "Linux: sudo apt install adb"
        )


class ADBTimeoutError(ADBError):
    """ADB command timed out."""

    def __init__(self, command: str, timeout: float) -> None:
        self.command = command
        self.timeout = timeout
        super().__init__(f"ADB command timed out after {timeout}s: {command}")


class ADBCommandError(ADBError):
    """ADB command failed with non-zero exit code."""

    def __init__(self, command: str, exit_code: int, stderr: str) -> None:
        self.command = command
        self.exit_code = exit_code
        self.stderr = stderr
        super().__init__(f"ADB command failed (exit {exit_code}): {stderr.strip() or command}")


class ADBDeviceNotFoundError(ADBError):
    """Specified device not found or not connected."""

    def __init__(self, device_id: str) -> None:
        self.device_id = device_id
        super().__init__(f"Device not found or disconnected: {device_id}")


class ADBDeviceDisconnectedError(ADBError):
    """Device was disconnected during operation."""

    def __init__(self, device_id: str) -> None:
        self.device_id = device_id
        super().__init__(
            f"Device disconnected during operation: {device_id}\n"
            "Please reconnect the device and try again."
        )


class ADBPermissionError(ADBError):
    """Permission denied when executing operation."""

    def __init__(self, operation: str, device_id: str) -> None:
        self.operation = operation
        self.device_id = device_id
        super().__init__(
            f"Permission denied for {operation} on device {device_id}\n"
            "Possible solutions:\n"
            "1. Enable USB debugging on your device\n"
            "2. Accept the USB debugging authorization prompt\n"
            "3. For some operations, you may need to enable "
            "'USB debugging (Security settings)' in Developer Options\n"
            "4. Try running: adb kill-server && adb start-server"
        )
