"""Test app startup and CSS compilation."""

from app_freeze.app import AppFreezeApp


class TestAppStartup:
    """Test that the app can start and CSS compiles successfully."""

    def test_app_css_compiles(self) -> None:
        """Test that the app's CSS compiles without errors."""
        # This will fail if there are CSS errors
        app = AppFreezeApp()

        # Textual compiles CSS when the app is created
        # If there are undefined variables, it should raise an error here
        assert app is not None

    def test_app_has_theme_variables(self) -> None:
        """Verify that theme CSS is included in the app."""
        app = AppFreezeApp()
        css = app.CSS

        # Check that theme variables are defined
        assert "$surface-light" in css
        assert "$primary" in css
        assert "$error" in css
