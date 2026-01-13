"""Application state models."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app_freeze.adb.models import AppInfo, DeviceInfo


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
class AppState:
    """Overall application state."""

    current_screen: Screen = field(default=Screen.DEVICE_SELECTION)
    selected_device: "DeviceInfo | None" = field(default=None)
    available_devices: list["DeviceInfo"] = field(default_factory=list)
    apps: list["AppInfo"] = field(default_factory=list)
    selected_apps: set[str] = field(default_factory=set)  # Package names
    current_action: AppAction | None = field(default=None)
    execution_results: dict[str, bool] = field(default_factory=dict)  # package_name -> success
    error_message: str | None = field(default=None)
