#!/usr/bin/env bash
# Build script for App Freeze
# Creates a standalone binary using PyInstaller

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print with color
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "app-freeze.spec" ]; then
    print_error "app-freeze.spec not found. Please run from project root."
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    print_warn "Virtual environment not activated. Activating..."
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    else
        print_error "Virtual environment not found. Please run: uv venv"
        exit 1
    fi
fi

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    print_info "PyInstaller not found. Installing..."
    uv pip install pyinstaller
fi

# Clean previous builds
print_info "Cleaning previous builds..."
rm -rf build/ dist/

# Run tests first (excluding integration tests which require hardware)
print_info "Running tests..."
if ! uv run pytest -m "not integration"; then
    print_error "Tests failed. Fix tests before building."
    exit 1
fi

# Run linting
print_info "Running linting..."
if ! uv run ruff check src/; then
    print_warn "Linting issues found. Consider fixing before release."
fi

# Run type checking
print_info "Running type checking..."
if ! uv run mypy src/; then
    print_warn "Type checking issues found. Consider fixing before release."
fi

# Build the binary
print_info "Building binary with PyInstaller..."
uv run pyinstaller app-freeze.spec

# Check if build succeeded
if [ -f "dist/app-freeze" ]; then
    print_info "Build successful!"
    print_info "Binary location: dist/app-freeze"
    
    # Get binary size
    SIZE=$(du -h "dist/app-freeze" | cut -f1)
    print_info "Binary size: $SIZE"
    
    # Make executable
    chmod +x dist/app-freeze
    
    # Test the binary (with timeout since it's a TUI app)
    print_info "Testing binary..."
    if timeout 1s dist/app-freeze &> /dev/null || [ $? -eq 124 ]; then
        print_info "Binary executable verified!"
    else
        print_warn "Binary test had issues, but may still work"
    fi
    
    # Test for CSS errors
    print_info "Checking for CSS errors..."
    css_test_output=$(timeout 1s dist/app-freeze 2>&1 || true)
    if echo "$css_test_output" | grep -i "error in stylesheet" > /dev/null; then
        print_error "CSS errors detected in binary!"
        echo "$css_test_output"
        exit 1
    elif echo "$css_test_output" | grep -i "undefined variable" > /dev/null; then
        print_error "Undefined CSS variables detected in binary!"
        echo "$css_test_output"
        exit 1
    else
        print_info "No CSS errors found!"
    fi
    
    print_info ""
    print_info "Build complete! To run:"
    print_info "  ./dist/app-freeze"
    print_info ""
    print_info "To create a release, compress the binary:"
    print_info "  tar -czf app-freeze-$(uname -s)-$(uname -m).tar.gz -C dist app-freeze"
else
    print_error "Build failed. Check errors above."
    exit 1
fi
