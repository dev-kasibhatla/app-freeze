# Contributing to App Freeze

Thank you for your interest in contributing to App Freeze! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, collaborative, and constructive. We're all here to make this project better.

## Development Setup

### Prerequisites

- Python 3.11 or higher
- `uv` package manager
- ADB (Android Debug Bridge)
- Android device with USB debugging enabled (for testing)

### Setup Steps

```bash
# Clone the repository
git clone https://github.com/yourusername/adb-dissable.git
cd adb-dissable

# Create virtual environment using uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Development Workflow

### Before Making Changes

1. Create a new branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Ensure tests pass:
   ```bash
   uv run pytest
   ```

### Making Changes

1. **Write code** following the style guidelines below
2. **Write tests** for your changes
3. **Update documentation** if needed
4. **Run code quality checks**:
   ```bash
   # Format code
   uv run black src/ tests/
   
   # Lint
   uv run ruff check src/ tests/
   
   # Type check
   uv run mypy src/
   
   # Run tests
   uv run pytest
   ```

### Committing Changes

We use conventional commit messages:

```bash
# Format: <type>: <description>

# Types:
feat: add new feature
fix: fix a bug
docs: documentation changes
test: add or update tests
chore: maintenance tasks
refactor: code refactoring
perf: performance improvements

# Examples:
git commit -m "feat: add search functionality to app list"
git commit -m "fix: handle device disconnection gracefully"
git commit -m "docs: update KEYBINDINGS.md with new shortcuts"
```

Pre-commit hooks will automatically:
- Format code with black
- Lint with ruff
- Type check with mypy

If any check fails, fix the issues and commit again.

### Submitting Changes

1. Push your branch:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Open a Pull Request on GitHub
3. Describe your changes clearly
4. Link any related issues
5. Wait for review

## Code Style Guidelines

### Python Style

We follow these principles:

1. **Clarity over cleverness** - Code should be easy to understand
2. **Type everything** - Use type hints everywhere
3. **Handle errors explicitly** - No silent failures
4. **No magic numbers** - Use constants
5. **Keep functions focused** - One responsibility per function

### Specific Rules

**Formatting:**
- Line length: 100 characters
- Use black for formatting
- Use ruff for linting

**Type Hints:**
```python
# Good
def get_device_info(device_id: str) -> DeviceInfo:
    ...

# Bad
def get_device_info(device_id):
    ...
```

**Error Handling:**
```python
# Good
try:
    result = adb_command()
except ADBError as e:
    logger.error(f"ADB command failed: {e}")
    raise

# Bad
try:
    result = adb_command()
except:
    pass
```

**Constants:**
```python
# Good
DEFAULT_TIMEOUT: Final[float] = 30.0
if timeout > DEFAULT_TIMEOUT:
    ...

# Bad
if timeout > 30.0:
    ...
```

### UI/UX Guidelines

**Keep UI and logic separate:**
- UI should never call ADB directly
- UI reacts to state changes
- ADB layer returns structured results

**Never block the UI:**
- Long operations run in threads
- Show progress indicators
- Allow cancellation where appropriate

**Always show feedback:**
- Confirm user actions
- Show progress
- Display keybindings

## Testing Guidelines

### Writing Tests

**Test coverage expectations:**
- All public functions should have tests
- Edge cases should be covered
- Error paths should be tested

**Test structure:**
```python
def test_function_name_scenario() -> None:
    """Test that function_name handles scenario correctly."""
    # Arrange
    setup_test_data()
    
    # Act
    result = function_under_test()
    
    # Assert
    assert result == expected_value
```

**Mock external dependencies:**
```python
from unittest.mock import patch, MagicMock

def test_adb_client() -> None:
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="output",
            stderr=""
        )
        result = client.run_command()
        assert result == "output"
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_client.py

# Run with coverage
uv run pytest --cov=src/app_freeze --cov-report=term-missing

# Run specific test
uv run pytest tests/test_client.py::test_function_name -v
```

## Documentation Guidelines

### Code Documentation

**Docstrings:** All public functions, classes, and modules should have docstrings:

```python
def enable_disable_apps(
    device_id: str,
    packages: list[str],
    enable: bool,
    user_ids: list[int],
) -> dict[str, tuple[bool, str | None]]:
    """
    Enable or disable apps for specified users.
    
    Args:
        device_id: The target device ID.
        packages: List of package names to modify.
        enable: True to enable, False to disable.
        user_ids: List of user IDs to apply changes to.
        
    Returns:
        Dictionary mapping package names to (success, error) tuples.
        
    Raises:
        ADBError: If ADB command fails.
    """
```

**Comments:** Use comments for complex logic only:

```python
# Calculate timeout based on number of apps
# Assume ~2 seconds per app with 30s minimum
timeout = max(30, len(packages) * 2)
```

### Documentation Files

When updating documentation:
- Keep it concise and clear
- Use examples where helpful
- Update table of contents if needed
- Check for broken links

## Areas for Contribution

### High Priority

- [ ] Windows native support
- [ ] Search/filter functionality in app list
- [ ] Performance optimization for large app lists
- [ ] CI/CD pipeline setup

### Medium Priority

- [ ] Export app list to CSV
- [ ] Import app list from file for batch operations
- [ ] Configurable timeouts
- [ ] Custom report formats

### Low Priority

- [ ] App comparison between devices
- [ ] Schedule enable/disable
- [ ] Web interface (optional)

### Good First Issues

- Documentation improvements
- Test coverage improvements
- Error message improvements
- UI polish

## Project Structure

```
adb-dissable/
├── src/
│   └── app_freeze/
│       ├── __init__.py
│       ├── main.py          # Entry point
│       ├── app.py           # Main application
│       ├── state.py         # State models
│       ├── reporting.py     # Report generation
│       ├── adb/             # ADB interaction layer
│       │   ├── client.py    # ADB wrapper
│       │   ├── errors.py    # Error types
│       │   ├── models.py    # Data models
│       │   └── parser.py    # Output parsing
│       └── ui/              # UI components
│           ├── screens.py   # Screen components
│           ├── widgets.py   # Custom widgets
│           └── theme.py     # Color theme
├── tests/                   # Test files
├── docs/                    # Documentation
├── reports/                 # Generated reports (gitignored)
├── build.sh                 # Build script
├── app-freeze.spec          # PyInstaller spec
└── pyproject.toml           # Project configuration
```

## Questions?

- Check existing issues and discussions
- Review the documentation in `docs/`
- Open a new issue with your question

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing to App Freeze! 🎉
