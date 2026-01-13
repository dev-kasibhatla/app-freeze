"""Tests for the reporting module."""

from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from app_freeze.adb.models import DeviceInfo, DeviceState
from app_freeze.reporting import OperationReport, OperationResult, ReportWriter
from app_freeze.state import AppAction


def test_operation_result() -> None:
    """Test OperationResult creation."""
    result = OperationResult(package="com.example.app", success=True)
    assert result.package == "com.example.app"
    assert result.success is True
    assert result.error is None

    failed_result = OperationResult(
        package="com.example.failed", success=False, error="Permission denied"
    )
    assert failed_result.success is False
    assert failed_result.error == "Permission denied"


def test_operation_report_properties() -> None:
    """Test OperationReport computed properties."""
    device = DeviceInfo(
        device_id="test123",
        state=DeviceState.DEVICE,
        model="Test Model",
        manufacturer="Test Manufacturer",
    )

    results = [
        OperationResult(package="app1", success=True),
        OperationResult(package="app2", success=True),
        OperationResult(package="app3", success=False, error="Failed"),
    ]

    report = OperationReport(
        device=device,
        action=AppAction.DISABLE,
        timestamp=datetime.now(),
        results=results,
    )

    assert report.total_count == 3
    assert report.success_count == 2
    assert report.failure_count == 1


def test_report_writer_creates_directory() -> None:
    """Test that ReportWriter creates the reports directory."""
    with TemporaryDirectory() as tmpdir:
        reports_dir = Path(tmpdir) / "custom_reports"
        writer = ReportWriter(reports_dir=reports_dir)

        device = DeviceInfo(device_id="test123", state=DeviceState.DEVICE)
        report = OperationReport(
            device=device,
            action=AppAction.ENABLE,
            timestamp=datetime.now(),
            results=[],
        )

        filepath = writer.write_report(report)

        assert reports_dir.exists()
        assert filepath.exists()
        assert filepath.parent == reports_dir


def test_report_writer_filename_format() -> None:
    """Test that report filenames follow the expected format."""
    with TemporaryDirectory() as tmpdir:
        writer = ReportWriter(reports_dir=Path(tmpdir))

        device = DeviceInfo(device_id="ABC123", state=DeviceState.DEVICE)
        timestamp = datetime(2024, 1, 15, 14, 30, 45)

        report = OperationReport(
            device=device,
            action=AppAction.DISABLE,
            timestamp=timestamp,
            results=[],
        )

        filepath = writer.write_report(report)

        # Filename should be: ABC123-20240115-143045.md
        assert filepath.name == "ABC123-20240115-143045.md"


def test_report_markdown_content() -> None:
    """Test that generated markdown contains expected content."""
    with TemporaryDirectory() as tmpdir:
        writer = ReportWriter(reports_dir=Path(tmpdir))

        device = DeviceInfo(
            device_id="TEST123",
            state=DeviceState.DEVICE,
            model="Pixel 8",
            manufacturer="Google",
            android_version="14",
            sdk_level=34,
        )

        results = [
            OperationResult(package="com.example.app1", success=True),
            OperationResult(package="com.example.app2", success=False, error="Permission denied"),
        ]

        timestamp = datetime(2024, 1, 15, 14, 30, 45)

        report = OperationReport(
            device=device,
            action=AppAction.ENABLE,
            timestamp=timestamp,
            results=results,
        )

        filepath = writer.write_report(report)
        content = filepath.read_text(encoding="utf-8")

        # Check title
        assert "# App Freeze Report: Enable" in content

        # Check timestamp
        assert "2024-01-15 14:30:45" in content

        # Check device info
        assert "TEST123" in content
        assert "Pixel 8" in content
        assert "Google" in content
        assert "Android Version:** 14" in content
        assert "SDK Level:** 34" in content

        # Check summary
        assert "Total Apps:** 2" in content
        assert "Successful:** 1" in content
        assert "Failed:** 1" in content

        # Check results table
        assert "com.example.app1" in content
        assert "com.example.app2" in content
        assert "Permission denied" in content

        # Check failure detail section
        assert "## Failed Operations" in content


def test_report_disable_action() -> None:
    """Test report for disable action."""
    with TemporaryDirectory() as tmpdir:
        writer = ReportWriter(reports_dir=Path(tmpdir))

        device = DeviceInfo(device_id="TEST", state=DeviceState.DEVICE)
        report = OperationReport(
            device=device,
            action=AppAction.DISABLE,
            timestamp=datetime.now(),
            results=[OperationResult(package="test.app", success=True)],
        )

        filepath = writer.write_report(report)
        content = filepath.read_text(encoding="utf-8")

        assert "# App Freeze Report: Disable" in content
        assert "Action:** Disable" in content


def test_report_no_failures() -> None:
    """Test that Failed Operations section is not present when all succeed."""
    with TemporaryDirectory() as tmpdir:
        writer = ReportWriter(reports_dir=Path(tmpdir))

        device = DeviceInfo(device_id="TEST", state=DeviceState.DEVICE)
        results = [
            OperationResult(package="app1", success=True),
            OperationResult(package="app2", success=True),
        ]

        report = OperationReport(
            device=device,
            action=AppAction.ENABLE,
            timestamp=datetime.now(),
            results=results,
        )

        filepath = writer.write_report(report)
        content = filepath.read_text(encoding="utf-8")

        # Failed Operations section should not exist
        assert "## Failed Operations" not in content
        assert "Successful:** 2" in content
        assert "Failed:** 0" in content


def test_multiple_reports_unique_filenames() -> None:
    """Test that multiple reports create unique files."""
    with TemporaryDirectory() as tmpdir:
        writer = ReportWriter(reports_dir=Path(tmpdir))

        device = DeviceInfo(device_id="TEST", state=DeviceState.DEVICE)

        # Write first report
        report1 = OperationReport(
            device=device,
            action=AppAction.ENABLE,
            timestamp=datetime(2024, 1, 15, 14, 30, 45),
            results=[],
        )
        filepath1 = writer.write_report(report1)

        # Write second report with different timestamp
        report2 = OperationReport(
            device=device,
            action=AppAction.DISABLE,
            timestamp=datetime(2024, 1, 15, 14, 35, 10),
            results=[],
        )
        filepath2 = writer.write_report(report2)

        assert filepath1 != filepath2
        assert filepath1.exists()
        assert filepath2.exists()
