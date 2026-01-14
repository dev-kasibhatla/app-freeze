"""Consistent color theme for the application."""

# App color palette - accessible and consistent
COLORS = {
    "primary": "#5c7cfa",  # Blue for primary actions
    "secondary": "#748ffc",  # Lighter blue
    "success": "#51cf66",  # Green for success
    "warning": "#fcc419",  # Yellow for warnings
    "error": "#ff6b6b",  # Red for errors
    "disabled": "#868e96",  # Gray for disabled items
    "surface": "#1e1e2e",  # Dark surface
    "surface_light": "#2d2d3a",  # Lighter surface
    "text": "#f8f9fa",  # Main text
    "text_muted": "#adb5bd",  # Muted text
    "border": "#495057",  # Border color
    "accent": "#be4bdb",  # Accent for highlights
}

# Comprehensive CSS with theme variables and widget styles
# All CSS is consolidated here to ensure variables are available when PyInstaller packages the app
THEME_CSS = """
$primary: #5c7cfa;
$secondary: #748ffc;
$success: #51cf66;
$warning: #fcc419;
$error: #ff6b6b;
$disabled: #868e96;
$surface: #1e1e2e;
$surface-light: #2d2d3a;
$text: #f8f9fa;
$text-muted: #adb5bd;
$border: #495057;
$accent: #be4bdb;

Screen {
    background: $surface;
}

Header {
    background: $primary;
    color: $text;
}

Footer {
    background: $surface-light;
    color: $text-muted;
}

.bordered {
    border: solid $border;
    border-title-color: $primary;
    border-title-background: $surface;
    padding: 1 2;
}

.success {
    color: $success;
}

.error {
    color: $error;
}

.warning {
    color: $warning;
}

.muted {
    color: $text-muted;
}

.selected {
    background: $primary 30%;
}

.focused {
    border: double $accent;
}

Button {
    background: $primary;
    color: $text;
}

Button:hover {
    background: $secondary;
}

Button.-primary {
    background: $success;
}

Button.-error {
    background: $error;
}

ProgressBar > .bar--complete {
    color: $success;
}

ProgressBar > .bar--indeterminate {
    color: $primary;
}

/* AppItem styles */
AppItem {
    height: 3;
    padding: 0 1;
}

AppItem > Horizontal {
    height: 100%;
    align: left middle;
}

AppItem > Horizontal > .app-checkbox {
    width: 4;
}

AppItem > Horizontal > .app-name {
    width: 1fr;
    padding-left: 1;
}

AppItem > Horizontal > .app-status {
    width: 12;
    text-align: center;
}

AppItem > Horizontal > .app-size {
    width: 10;
    text-align: right;
}

AppItem > Horizontal > .app-type {
    width: 8;
    text-align: center;
    color: $text-muted;
}

AppItem.--selected {
    background: $primary 30%;
}

AppItem:hover {
    background: $surface-light;
}

AppItem.--highlight {
    background: $accent 20%;
}

.status-enabled {
    color: $success;
}

.status-disabled {
    color: $error;
}

/* AppListWidget styles */
AppListWidget {
    height: 1fr;
    border: solid $border;
    border-title-color: $primary;
}

AppListWidget > .app-list-header {
    height: 2;
    background: $surface-light;
    padding: 0 1;
}

AppListWidget:focus {
    border: double $accent;
}

/* DeviceInfoPanel styles */
DeviceInfoPanel {
    height: auto;
    padding: 1 2;
    border: solid $border;
    border-title-color: $primary;
}

DeviceInfoPanel > Vertical > Horizontal {
    height: 1;
}

DeviceInfoPanel > Vertical > Horizontal > .label {
    width: 15;
    color: $text-muted;
}

DeviceInfoPanel > Vertical > Horizontal > .value {
    width: 1fr;
}

/* StatusBar styles */
StatusBar {
    height: 1;
    background: $surface-light;
    padding: 0 2;
}

StatusBar > Horizontal {
    height: 1;
}

StatusBar .status-text {
    width: 1fr;
}

StatusBar .status-count {
    width: auto;
    color: $text-muted;
}
"""
