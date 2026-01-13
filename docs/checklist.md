# Production Readiness Checklist

## Project Setup
- [ ] Use only Python 3.11+ for all development and production environments
- [ ] Initialize a new git repository for version control
- [ ] Set up Python environment management using `uv` exclusively (no venv, no pip)
- [ ] Add a `pyproject.toml` for project metadata and tool configuration
- [ ] Configure code quality tools: black (formatting), ruff (linting), and mypy (type checking)
- [ ] Set up pre-commit hooks to enforce code standards before every commit
- [ ] Write a clear and concise `README.md` with setup, usage, and contribution instructions

## CLI Framework
- [ ] Select a modern TUI framework (Textual or Rich) for the CLI interface
- [ ] Define a robust application state model for managing UI and logic
- [ ] Design a clear screen routing/navigation model for all app flows
- [ ] Implement the main event loop to handle user input and state updates
- [ ] Ensure clean exit handling to restore terminal state on quit

## ADB Layer
- [ ] Create a dedicated module to wrap all adb command interactions
- [ ] Detect adb tool availability and provide actionable error if missing
- [ ] Detect all connected Android devices reliably
- [ ] Handle scenarios with multiple connected devices
- [ ] Support device selection by user when multiple devices are present
- [ ] Capture both stdout and stderr from adb commands robustly
- [ ] Add timeout handling for all adb operations to prevent hangs
- [ ] Define and use structured error types for all adb failures

## Device Discovery
- [ ] Fetch device ID for each connected device
- [ ] Fetch model name, manufacturer, Android version, and SDK level
- [ ] Cache device info to avoid redundant adb calls

## App Discovery
- [ ] List all installed packages on the device
- [ ] Identify and separate user apps from system apps
- [ ] Fetch enabled/disabled state for each app
- [ ] Fetch app size in MB for reporting
- [ ] Normalize and validate all package metadata
- [ ] Sort app list alphabetically for display

## UI Core
- [ ] Build the main page layout for app selection and actions
- [ ] Build the device page layout for device info and selection
- [ ] Implement visually distinct bordered sections for clarity
- [ ] Implement headers and footers for navigation and status
- [ ] Ensure responsive resizing for various terminal sizes
- [ ] Implement a consistent and accessible color theme

## Input Handling
- [ ] Implement keyboard navigation for all UI elements
- [ ] Support spacebar to toggle app selection
- [ ] Use Enter for confirmation actions
- [ ] Use 'q' for navigation backward/exit
- [ ] Use '?' to show a help overlay with keybindings
- [ ] Support Tab and Shift+Tab for focus switching
- [ ] (Optional) Add mouse support for selection and navigation

## Confirmation Dialog
- [ ] Display selected apps in two columns for easy review
- [ ] Clearly show whether the action is enable or disable
- [ ] Require explicit user confirmation before proceeding
- [ ] Allow user to cancel and return to previous screen

## Execution Engine
- [ ] Enumerate all users on the device for multi-user support
- [ ] Execute enable/disable actions per user as needed
- [ ] Execute actions per app sequentially, not in parallel
- [ ] Stream execution results live to the UI
- [ ] Capture both success and failure for each operation
- [ ] Never abort the process on a single failure; continue for all apps

## Progress Display
- [ ] Show a progress bar for app operations
- [ ] Update progress bar and status per completed app
- [ ] Show a live status line with current operation
- [ ] Color code success and failure for clarity

## Summary Screen
- [ ] Hide progress bar after completion
- [ ] Show total number of apps processed
- [ ] Show count of successful operations
- [ ] Show count of failed operations
- [ ] Allow user to return to main navigation

## Reporting
- [ ] Create a `reports` directory for output
- [ ] Generate report filenames using device ID and timestamp for uniqueness
- [ ] Write a `report.md` with operation details
- [ ] Include device metadata in the report
- [ ] Include app list with status (success/failure)
- [ ] Include operation timestamps
- [ ] Ensure deterministic formatting for all reports

## Testing
- [ ] Write unit tests for adb wrapper module
- [ ] Write unit tests for all parsing logic
- [ ] Write unit tests for state transitions
- [ ] Write snapshot tests for UI components
- [ ] Write integration tests with mocked adb
- [ ] Test multiple device scenarios
- [ ] Test failure scenarios (adb errors, permission errors, etc)

## Reliability
- [ ] Handle adb disconnects gracefully and inform the user
- [ ] Handle permission errors gracefully and provide guidance
- [ ] Ensure no terminal corruption on crash or error
- [ ] Always cleanup and restore terminal state on exit

## Packaging
- [ ] Configure PyInstaller spec to use uv as the Python environment
- [ ] Produce a single, non-reversible binary for macOS and Linux (no source extraction possible)
- [ ] Test the binary on a clean system (no Python installed)
- [ ] Verify that no Python dependency is required to run the binary
- [ ] Validate that startup time is fast and user experience is smooth

## Documentation
- [ ] Write clear usage instructions for all features
- [ ] Write a keybindings reference for all supported shortcuts
- [ ] Document all safety guarantees (no destructive actions without confirmation)
- [ ] Document known limitations and edge cases

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
