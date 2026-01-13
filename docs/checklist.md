# Production Readiness Checklist

- [x] Add GPLv3 license and reference in documentation

## Project Setup
- [x] Use only Python 3.11+ for all development and production environments
- [x] Initialize a new git repository for version control
- [x] Set up Python environment management using `uv` exclusively (no venv, no pip)
- [x] Add a `pyproject.toml` for project metadata and tool configuration
- [x] Configure code quality tools: black (formatting), ruff (linting), and mypy (type checking)
- [x] Set up pre-commit hooks to enforce code standards before every commit
- [x] Write a clear and concise `README.md` with setup, usage, and contribution instructions

## CLI Framework
- [x] Select a modern TUI framework (Textual or Rich) for the CLI interface
- [x] Define a robust application state model for managing UI and logic
- [x] Design a clear screen routing/navigation model for all app flows
- [x] Implement the main event loop to handle user input and state updates
- [x] Ensure clean exit handling to restore terminal state on quit

## ADB Layer
- [x] Create a dedicated module to wrap all adb command interactions
- [x] Detect adb tool availability and provide actionable error if missing
- [x] Detect all connected Android devices reliably
- [x] Handle scenarios with multiple connected devices
- [x] Support device selection by user when multiple devices are present
- [x] Capture both stdout and stderr from adb commands robustly
- [x] Add timeout handling for all adb operations to prevent hangs
- [x] Define and use structured error types for all adb failures

## Device Discovery
- [x] Fetch device ID for each connected device
- [x] Fetch model name, manufacturer, Android version, and SDK level
- [x] Cache device info to avoid redundant adb calls

## App Discovery
- [x] List all installed packages on the device
- [x] Identify and separate user apps from system apps
- [x] Fetch enabled/disabled state for each app
- [x] Fetch app size in MB for reporting
- [x] Normalize and validate all package metadata
- [x] Sort app list alphabetically for display

## UI Core
- [x] Build the main page layout for app selection and actions
- [x] Build the device page layout for device info and selection
- [x] Implement visually distinct bordered sections for clarity
- [x] Implement headers and footers for navigation and status
- [x] Ensure responsive resizing for various terminal sizes
- [x] Implement a consistent and accessible color theme

## Input Handling
- [x] Implement keyboard navigation for all UI elements
- [x] Support spacebar to toggle app selection
- [x] Use Enter for confirmation actions
- [x] Use 'q' for navigation backward/exit
- [x] Use '?' to show a help overlay with keybindings
- [x] Support Tab and Shift+Tab for focus switching
- [x] (Optional) Add mouse support for selection and navigation

## Confirmation Dialog
- [x] Display selected apps in two columns for easy review
- [x] Clearly show whether the action is enable or disable
- [x] Require explicit user confirmation before proceeding
- [x] Allow user to cancel and return to previous screen

## Execution Engine
- [x] Enumerate all users on the device for multi-user support
- [x] Execute enable/disable actions per user as needed
- [x] Execute actions per app sequentially, not in parallel
- [x] Stream execution results live to the UI
- [x] Capture both success and failure for each operation
- [x] Never abort the process on a single failure; continue for all apps

## Progress Display
- [x] Show a progress bar for app operations
- [x] Update progress bar and status per completed app
- [x] Show a live status line with current operation
- [x] Color code success and failure for clarity

## Summary Screen
- [x] Hide progress bar after completion
- [x] Show total number of apps processed
- [x] Show count of successful operations
- [x] Show count of failed operations
- [x] Allow user to return to main navigation

## Reporting
- [x] Create a `reports` directory for output
- [x] Generate report filenames using device ID and timestamp for uniqueness
- [x] Write a `report.md` with operation details
- [x] Include device metadata in the report
- [x] Include app list with status (success/failure)
- [x] Include operation timestamps
- [x] Ensure deterministic formatting for all reports

## Testing
- [x] Write unit tests for adb wrapper module
- [x] Write unit tests for all parsing logic
- [x] Write unit tests for reporting module
- [ ] Write unit tests for state transitions
- [ ] Write snapshot tests for UI components
- [x] Write integration tests with mocked adb
- [x] Test multiple device scenarios
- [x] Test failure scenarios (adb errors, permission errors, etc)

## Reliability
- [x] Handle adb disconnects gracefully and inform the user
- [x] Handle permission errors gracefully and provide guidance
- [x] Ensure no terminal corruption on crash or error
- [x] Always cleanup and restore terminal state on exit

## Packaging
- [x] Configure PyInstaller spec to use uv as the Python environment
- [x] Produce a single, non-reversible binary for macOS and Linux (no source extraction possible)
- [ ] Test the binary on a clean system (no Python installed)
- [ ] Verify that no Python dependency is required to run the binary
- [ ] Validate that startup time is fast and user experience is smooth

## Documentation
- [x] Write clear usage instructions for all features
- [x] Write a keybindings reference for all supported shortcuts
- [x] Document all safety guarantees (no destructive actions without confirmation)
- [x] Document known limitations and edge cases

## CI
- [ ] Add lint checks to CI pipeline
- [ ] Add test execution to CI pipeline
- [ ] Add build verification to CI pipeline
- [ ] Add binary artifact generation to CI pipeline

## Final Validation
- [ ] Test the app with a single device
- [ ] Test the app with multiple devices connected
- [ ] Test both enable and disable flows end-to-end
- [ ] Verify that no data loss occurs during operations
- [ ] Verify that generated reports are correct and complete
