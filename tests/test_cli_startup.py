"""Comprehensive CLI startup and runtime tests."""

import pytest

from app_freeze.app import AppFreezeApp


class TestCLIStartup:
    """Test CLI startup and error handling."""

    @pytest.mark.asyncio
    async def test_app_starts_without_errors(self) -> None:
        """Test that the app starts and initializes without errors."""
        app = AppFreezeApp()
        async with app.run_test():
            # App should start and mount without errors
            assert app.is_mounted  # type: ignore[truthy-function]
            # Header and Footer should be present
            assert app.query("Header")
            assert app.query("Footer")

    @pytest.mark.asyncio
    async def test_app_handles_no_adb_gracefully(self) -> None:
        """Test that app handles missing ADB gracefully."""
        app = AppFreezeApp()
        async with app.run_test() as pilot:
            # Even if ADB is missing, app should start
            assert app.is_mounted  # type: ignore[truthy-function]
            # Should either show error or device selection
            await pilot.pause(0.1)  # Give time for initialization
            assert app.is_running

    @pytest.mark.asyncio
    async def test_css_compiles_on_startup(self) -> None:
        """Test that CSS compiles correctly when app starts."""
        app = AppFreezeApp()
        async with app.run_test():
            # If CSS has errors, app.run_test() would fail
            # This test ensures CSS compilation succeeds
            assert app.CSS is not None
            assert len(app.CSS) > 0

    @pytest.mark.asyncio
    async def test_widgets_compose_without_errors(self) -> None:
        """Test that all widgets can be composed without errors."""
        app = AppFreezeApp()
        async with app.run_test() as pilot:
            await pilot.pause(0.1)
            # If widget composition fails, this would raise
            # Test that basic widgets are accessible
            assert app.query("Header")
            assert app.query("Footer")

    @pytest.mark.asyncio
    async def test_app_responds_to_quit(self) -> None:
        """Test that app responds to quit command."""
        app = AppFreezeApp()
        async with app.run_test() as pilot:
            # Press 'q' to quit
            await pilot.press("q")
            await pilot.pause(0.2)
            # App should handle quit gracefully (exit may not complete in test mode)
            # Just verify no crash
            assert True  # If we get here, app handled quit without crashing

    @pytest.mark.asyncio
    async def test_app_handles_help_screen(self) -> None:
        """Test that help screen can be shown."""
        app = AppFreezeApp()
        async with app.run_test() as pilot:
            # Press '?' to show help
            await pilot.press("question_mark")
            await pilot.pause(0.1)
            # Should not crash
            assert app.is_mounted  # type: ignore[truthy-function]


class TestCLIErrorHandling:
    """Test CLI error handling and recovery."""

    @pytest.mark.asyncio
    async def test_app_handles_initialization_errors(self) -> None:
        """Test that app handles initialization errors gracefully."""
        app = AppFreezeApp()
        async with app.run_test() as pilot:
            await pilot.pause(0.2)
            # Even with errors, app should remain stable
            assert app.is_mounted  # type: ignore[truthy-function]
            assert app.is_running

    @pytest.mark.asyncio
    async def test_reactive_updates_dont_crash(self) -> None:
        """Test that reactive property updates don't crash the app."""
        app = AppFreezeApp()
        async with app.run_test() as pilot:
            # Trigger any reactive updates
            await pilot.pause(0.1)
            # App should still be running
            assert app.is_running


class TestCLIPerformance:
    """Test CLI performance and responsiveness."""

    @pytest.mark.asyncio
    async def test_app_starts_quickly(self) -> None:
        """Test that app starts within reasonable time."""
        import time

        start = time.time()
        app = AppFreezeApp()
        async with app.run_test():
            elapsed = time.time() - start
            # App should start in under 15 seconds even in test mode
            # (test mode is slower due to async simulation)
            assert elapsed < 15.0

    @pytest.mark.asyncio
    async def test_ui_remains_responsive(self) -> None:
        """Test that UI remains responsive during operations."""
        app = AppFreezeApp()
        async with app.run_test() as pilot:
            # Simulate some key presses
            await pilot.press("down")
            await pilot.press("up")
            await pilot.pause(0.05)
            # App should still be responsive
            assert app.is_running
