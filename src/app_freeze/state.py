"""Application state models."""

from dataclasses import dataclass
from enum import Enum, auto


class Screen(Enum):
    """Available screens in the application."""

    DEVICE_SELECTION = auto()
    APP_LIST = auto()
    CONFIRMATION = auto()
    EXECUTION = auto()
    SUMMARY = auto()


class AppAction(Enum):
    """Actions that can be performed on apps."""

    ENABLE = auto()
    DISABLE = auto()


@dataclass
class Device:
    """Android device information."""

    device_id: str
    model: str
    manufacturer: str
    android_version: str
    sdk_level: int


@dataclass
class App:
    """Android app information."""

    package_name: str
    name: str
    enabled: bool
    is_system: bool
    size_mb: float


@dataclass
class AppState:
    """Overall application state."""

    current_screen: Screen
    selected_device: Device | None
    available_devices: list[Device]
    apps: list[App]
    selected_apps: set[str]  # Package names
    current_action: AppAction | None
    execution_results: dict[str, bool]  # package_name -> success
    error_message: str | None

    def __init__(self) -> None:
        """Initialize application state."""
        self.current_screen = Screen.DEVICE_SELECTION
        self.selected_device = None
        self.available_devices = []
        self.apps = []
        self.selected_apps = set()
        self.current_action = None
        self.execution_results = {}
        self.error_message = None
