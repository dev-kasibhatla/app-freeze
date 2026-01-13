"""Report generation for operation results."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app_freeze.adb.models import DeviceInfo
    from app_freeze.state import AppAction


@dataclass
class OperationResult:
    """Result of an app operation."""

    package: str
    success: bool
    error: str | None = None


@dataclass
class OperationReport:
    """Complete report for an operation session."""

    device: "DeviceInfo"
    action: "AppAction"
    timestamp: datetime
    results: list[OperationResult]

    @property
    def total_count(self) -> int:
        """Total number of operations."""
        return len(self.results)

    @property
    def success_count(self) -> int:
        """Number of successful operations."""
        return sum(1 for r in self.results if r.success)

    @property
    def failure_count(self) -> int:
        """Number of failed operations."""
        return sum(1 for r in self.results if not r.success)


class ReportWriter:
    """Writer for generating operation reports."""

    def __init__(self, reports_dir: Path | None = None) -> None:
        """Initialize report writer.

        Args:
            reports_dir: Directory to write reports to. Defaults to 'reports' in current dir.
        """
        self.reports_dir = reports_dir or Path("reports")

    def write_report(self, report: OperationReport) -> Path:
        """Write report to disk.

        Args:
            report: The operation report to write.

        Returns:
            Path to the written report file.
        """
        # Ensure reports directory exists
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename: <device-id>-<timestamp>.md
        timestamp_str = report.timestamp.strftime("%Y%m%d-%H%M%S")
        filename = f"{report.device.device_id}-{timestamp_str}.md"
        filepath = self.reports_dir / filename

        # Generate report content
        content = self._generate_markdown(report)

        # Write file
        filepath.write_text(content, encoding="utf-8")

        return filepath

    def _generate_markdown(self, report: OperationReport) -> str:
        """Generate markdown content for report.

        Args:
            report: The operation report.

        Returns:
            Markdown formatted report content.
        """
        action_str = "Enable" if report.action.name == "ENABLE" else "Disable"
        timestamp_str = report.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        lines: list[str] = []

        # Title and metadata
        lines.append(f"# App Freeze Report: {action_str}")
        lines.append("")
        lines.append(f"**Generated:** {timestamp_str}")
        lines.append("")

        # Device information
        lines.append("## Device Information")
        lines.append("")
        lines.append(f"- **Device ID:** {report.device.device_id}")
        if report.device.display_name:
            lines.append(f"- **Name:** {report.device.display_name}")
        if report.device.manufacturer:
            lines.append(f"- **Manufacturer:** {report.device.manufacturer}")
        if report.device.model:
            lines.append(f"- **Model:** {report.device.model}")
        if report.device.android_version:
            lines.append(f"- **Android Version:** {report.device.android_version}")
        if report.device.sdk_level:
            lines.append(f"- **SDK Level:** {report.device.sdk_level}")
        lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Action:** {action_str}")
        lines.append(f"- **Total Apps:** {report.total_count}")
        lines.append(f"- **Successful:** {report.success_count}")
        lines.append(f"- **Failed:** {report.failure_count}")
        lines.append("")

        # Results table
        lines.append("## Results")
        lines.append("")
        lines.append("| Status | Package Name | Error |")
        lines.append("|--------|-------------|-------|")

        for result in report.results:
            status = "✓" if result.success else "✗"
            error = result.error or ""
            lines.append(f"| {status} | {result.package} | {error} |")

        lines.append("")

        # Failures detail (if any)
        failures = [r for r in report.results if not r.success]
        if failures:
            lines.append("## Failed Operations")
            lines.append("")
            for result in failures:
                lines.append(f"### {result.package}")
                lines.append("")
                lines.append(f"**Error:** {result.error or 'Unknown error'}")
                lines.append("")

        return "\n".join(lines)
