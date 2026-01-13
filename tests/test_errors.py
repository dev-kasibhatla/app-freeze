"""Tests for ADB error types."""

from app_freeze.adb.errors import (
    ADBCommandError,
    ADBDeviceNotFoundError,
    ADBError,
    ADBNotFoundError,
    ADBTimeoutError,
)


class TestADBError:
    """Tests for ADBError base class."""

    def test_message(self) -> None:
        err = ADBError("test message")
        assert err.message == "test message"
        assert str(err) == "test message"

    def test_inheritance(self) -> None:
        err = ADBError("test")
        assert isinstance(err, Exception)


class TestADBNotFoundError:
    """Tests for ADBNotFoundError."""

    def test_message_contains_instructions(self) -> None:
        err = ADBNotFoundError()
        assert "adb not found" in err.message
        assert "brew" in err.message  # macOS instructions
        assert "apt" in err.message  # Linux instructions

    def test_inheritance(self) -> None:
        err = ADBNotFoundError()
        assert isinstance(err, ADBError)


class TestADBTimeoutError:
    """Tests for ADBTimeoutError."""

    def test_attributes(self) -> None:
        err = ADBTimeoutError("adb devices", 30.0)
        assert err.command == "adb devices"
        assert err.timeout == 30.0
        assert "30" in err.message
        assert "timed out" in err.message

    def test_inheritance(self) -> None:
        err = ADBTimeoutError("cmd", 5.0)
        assert isinstance(err, ADBError)


class TestADBCommandError:
    """Tests for ADBCommandError."""

    def test_attributes(self) -> None:
        err = ADBCommandError("adb shell", 1, "error: device not found")
        assert err.command == "adb shell"
        assert err.exit_code == 1
        assert err.stderr == "error: device not found"
        assert "device not found" in err.message

    def test_empty_stderr(self) -> None:
        err = ADBCommandError("adb shell pm list", 1, "")
        assert "adb shell pm list" in err.message

    def test_inheritance(self) -> None:
        err = ADBCommandError("cmd", 1, "err")
        assert isinstance(err, ADBError)


class TestADBDeviceNotFoundError:
    """Tests for ADBDeviceNotFoundError."""

    def test_attributes(self) -> None:
        err = ADBDeviceNotFoundError("emulator-5554")
        assert err.device_id == "emulator-5554"
        assert "emulator-5554" in err.message
        assert "not found" in err.message.lower() or "disconnected" in err.message.lower()

    def test_inheritance(self) -> None:
        err = ADBDeviceNotFoundError("device")
        assert isinstance(err, ADBError)
