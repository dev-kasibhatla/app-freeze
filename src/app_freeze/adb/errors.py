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
