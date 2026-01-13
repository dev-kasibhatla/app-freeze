"""Main application entry point."""

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header

from app_freeze.state import AppState, Screen


class AppFreezeApp(App[None]):
    """Main application class."""

    TITLE = "App Freeze"
    CSS = """
    Screen {
        align: center middle;
    }

    Container {
        width: 100%;
        height: 100%;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("?", "show_help", "Help"),
    ]

    def __init__(self) -> None:
        """Initialize the application."""
        super().__init__()
        self.state = AppState()

    def compose(self) -> ComposeResult:
        """Compose the initial UI."""
        yield Header()
        yield Container(id="main-content")
        yield Footer()

    def on_mount(self) -> None:
        """Handle application mount."""
        self._navigate_to_screen(Screen.DEVICE_SELECTION)

    def _navigate_to_screen(self, screen: Screen) -> None:
        """Navigate to a specific screen."""
        self.state.current_screen = screen
        # Screen switching logic will be implemented with actual screens
        pass

    async def action_quit(self) -> None:
        """Handle quit action."""
        self.exit()

    async def action_show_help(self) -> None:
        """Show help overlay."""
        # Help overlay will be implemented
        pass


def main() -> None:
    """Run the application."""
    app = AppFreezeApp()
    app.run()


if __name__ == "__main__":
    main()
