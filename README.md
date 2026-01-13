# App Freeze

A safe, modern TUI (Terminal User Interface) tool to manage Android app states via ADB. Enable and disable Android apps across all users with an intuitive keyboard-driven interface, without uninstalling or clearing any data.

## Features

- 🎯 **Interactive TUI** - Keyboard-driven interface built with Textual
- 📱 **Multi-device support** - Automatic detection and selection
- 🔍 **App browser** - View all installed apps with metadata (size, state, type)
- ✅ **Batch operations** - Enable/disable multiple apps at once
- 👥 **Multi-user support** - Works across all Android users on device
- 📊 **Detailed reports** - Markdown reports saved automatically
- 🛡️ **Safety first** - Explicit confirmations, no data loss
- 🚀 **Fast & responsive** - Async operations, no UI blocking

## Prerequisites

- **Python 3.11 or higher** (for development)
- **ADB (Android Debug Bridge)** installed and in PATH
  - macOS: `brew install android-platform-tools`
  - Linux: `sudo apt install adb` or `sudo pacman -S android-tools`
- **Android device** with USB debugging enabled

## Installation

### Binary (Recommended for Users)

Download the pre-built binary for your platform from releases:

```bash
# macOS/Linux - make it executable and run
chmod +x app-freeze
./app-freeze
```

### From Source (For Development)

```bash
# Clone the repository
git clone https://github.com/yourusername/adb-dissable.git
cd adb-dissable

# Install using uv (recommended)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# Run the application
python -m app_freeze.main
```

## Usage

### Quick Start

1. **Connect your Android device** via USB
2. **Enable USB debugging** on your device (Settings → Developer Options)
3. **Run app-freeze**: `./app-freeze` (or `python -m app_freeze.main`)
4. **Accept USB debugging** authorization on your device if prompted
5. **Select apps** using arrow keys and spacebar
6. **Choose action** - press `e` to enable or `d` to disable
7. **Confirm** - review selection and press Enter to proceed

### Navigation & Controls

| Key | Action |
|-----|--------|
| `↑` / `↓` or `j` / `k` | Navigate app list |
| `Space` / `Enter` | Toggle app selection |
| `a` | Select all apps |
| `n` | Deselect all apps |
| `s` | Toggle system apps visibility |
| `e` | Enable selected apps |
| `d` | Disable selected apps |
| `Tab` / `Shift+Tab` | Switch focus between sections |
| `?` | Show help overlay |
| `q` | Go back / Quit |
| `r` | Refresh device list |

See [KEYBINDINGS.md](docs/KEYBINDINGS.md) for complete reference.

### Workflow Example

```
1. Launch → Device Selection Screen
   ↓ (if single device, auto-selected)
   
2. App List Screen
   ↓ Select apps with Space
   ↓ Press 'd' to disable
   
3. Confirmation Screen
   ↓ Review selection
   ↓ Press Enter to confirm
   
4. Execution Screen
   ↓ Watch progress
   
5. Summary Screen
   ↓ View results
   ↓ Report saved to reports/
```

### Reports

Reports are automatically generated in `reports/` directory:

**Filename format:** `{device-id}-{timestamp}.md`

**Contains:**
- Device metadata (model, Android version, SDK level)
- Operation type (Enable/Disable)
- Complete app list with results
- Error details for failed operations
- Timestamps

## Safety Guarantees

App Freeze is designed to be **completely safe and reversible**:

- ✅ **No uninstalls** - Never uses `pm uninstall`
- ✅ **No data clearing** - Never uses `pm clear`
- ✅ **No root required** - Works with standard ADB permissions
- ✅ **Explicit confirmations** - Always asks before making changes
- ✅ **Reversible** - All operations can be undone
- ✅ **Auditable** - Detailed reports of all operations

See [SAFETY.md](docs/SAFETY.md) for complete safety documentation.

## Limitations

- Requires USB debugging enabled on device
- Some system apps cannot be disabled (Android limitation)
- Requires ADB permissions (usually granted via USB debugging prompt)
- Device must remain connected during operations

See [LIMITATIONS.md](docs/LIMITATIONS.md) for detailed limitations and workarounds.

## Development

### Setup

```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/app_freeze --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_client.py -v
```

### Code Quality

```bash
# Format code
uv run black src/ tests/

# Lint
uv run ruff check src/ tests/

# Type check
uv run mypy src/
```

### Building Binary

```bash
# Build for current platform
./build.sh

# Binary will be in dist/app-freeze
```

## Troubleshooting

**ADB not found:**
```bash
# Install ADB
# macOS: brew install android-platform-tools
# Linux: sudo apt install adb

# Verify installation
adb version
```

**Device not detected:**
```bash
# Check USB debugging is enabled
# Check device shows in: adb devices
# Try: adb kill-server && adb start-server
```

**Permission denied:**
- Accept USB debugging authorization on device
- Enable "USB debugging (Security settings)" in Developer Options
- Try running: `adb kill-server && adb start-server`

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the code style guidelines
4. Write tests for your changes
5. Run all tests and code quality checks
6. Commit your changes (`git commit -m 'feat: add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details

## Acknowledgments

- Built with [Textual](https://textual.textualize.io/) TUI framework
- Inspired by the need for safe Android app management
- Thanks to all contributors and testers

## Support

- 📖 [Full Documentation](docs/)
- 🐛 [Report Issues](https://github.com/yourusername/adb-dissable/issues)
- 💡 [Feature Requests](https://github.com/yourusername/adb-dissable/issues)
5. Commit your changes (`git commit -m 'feat: add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

[Add your license here]