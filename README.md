# App Freeze

A modern TUI (Terminal User Interface) tool to manage Android app states via ADB. Enable and disable Android apps with an intuitive interface, without deleting any data.

## Features

- 🎯 Interactive terminal UI with keyboard navigation
- 📱 Multi-device support with automatic detection
- 🔍 Browse installed apps with detailed metadata
- ✅ Batch enable/disable operations
- 📊 Detailed operation reports with timestamps
- 🛡️ Safety confirmations before destructive actions
- 🚀 Fast and responsive

## Prerequisites

- Python 3.11 or higher
- ADB (Android Debug Bridge) installed and in PATH
- Android device with USB debugging enabled

## Installation

### Using uv (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd adb-dissable

# Create virtual environment and install
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

### Development Setup

```bash
# Install dev dependencies
uv pip install pre-commit black ruff mypy

# Install pre-commit hooks
pre-commit install

# Run code quality checks
black .
ruff check .
mypy .
```

## Usage

```bash
# Run the application
python -m app_freeze.main
```

### Navigation

- `↑/↓` or `j/k` - Navigate through app list
- `Space` - Toggle app selection
- `Enter` - Confirm action
- `Tab/Shift+Tab` - Switch focus between UI sections
- `?` - Show help overlay
- `q` - Go back/Exit

### Workflow

1. Launch the app
2. Select device (if multiple connected)
3. Browse and select apps to enable/disable
4. Confirm your selection
5. View operation progress
6. Check generated report in `reports/` directory

## Reports

Reports are automatically generated in the `reports/` directory with the format:
- `report-{device-id}-{timestamp}.md`

Each report includes:
- Device metadata
- List of apps processed
- Success/failure status for each operation
- Operation timestamps

## Safety Features

- Confirmation dialog before any state changes
- No data deletion - only app state changes
- Detailed progress tracking
- Comprehensive error handling
- Terminal state restoration on exit

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the code style guidelines
4. Run tests and code quality checks
5. Commit your changes (`git commit -m 'feat: add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

[Add your license here]