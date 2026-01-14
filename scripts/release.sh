#!/usr/bin/env bash
# Script to create and push a new version tag with automatic semver increment
# Usage: ./scripts/release.sh [major|minor|patch]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Not in a git repository"
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    print_error "You have uncommitted changes. Please commit or stash them first."
    git status --short
    exit 1
fi

# Make sure we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    print_warn "You are on branch '$CURRENT_BRANCH', not 'main'"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Aborted"
        exit 1
    fi
fi

# Pull latest changes
print_step "Pulling latest changes..."
git pull --tags

# Get the latest tag
LATEST_TAG=$(git tag --sort=-version:refname | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | head -1)

if [ -z "$LATEST_TAG" ]; then
    print_warn "No existing version tags found. Starting from v0.1.0"
    LATEST_TAG="v0.0.0"
fi

print_info "Latest tag: $LATEST_TAG"

# Parse version
VERSION=${LATEST_TAG#v}
IFS='.' read -r -a VERSION_PARTS <<< "$VERSION"
MAJOR="${VERSION_PARTS[0]}"
MINOR="${VERSION_PARTS[1]}"
PATCH="${VERSION_PARTS[2]}"

# Determine increment type
INCREMENT_TYPE=${1:-patch}

case $INCREMENT_TYPE in
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    patch)
        PATCH=$((PATCH + 1))
        ;;
    *)
        print_error "Invalid increment type: $INCREMENT_TYPE"
        print_error "Usage: $0 [major|minor|patch]"
        exit 1
        ;;
esac

NEW_VERSION="$MAJOR.$MINOR.$PATCH"
NEW_TAG="v$NEW_VERSION"

print_info "New version: $NEW_TAG"

# Update pyproject.toml version
print_step "Updating pyproject.toml..."
if [ -f "pyproject.toml" ]; then
    if command -v sed &> /dev/null; then
        # macOS and Linux compatible
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/^version = .*/version = \"$NEW_VERSION\"/" pyproject.toml
        else
            sed -i "s/^version = .*/version = \"$NEW_VERSION\"/" pyproject.toml
        fi
        print_info "Updated pyproject.toml to version $NEW_VERSION"
    else
        print_warn "sed not found, skipping pyproject.toml update"
    fi
fi

# Update app-freeze.spec version if it exists
print_step "Updating app-freeze.spec..."
if [ -f "app-freeze.spec" ]; then
    if command -v sed &> /dev/null; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/^APP_VERSION = .*/APP_VERSION = '$NEW_VERSION'/" app-freeze.spec
        else
            sed -i "s/^APP_VERSION = .*/APP_VERSION = '$NEW_VERSION'/" app-freeze.spec
        fi
        print_info "Updated app-freeze.spec to version $NEW_VERSION"
    fi
fi

# Show changes
if git diff --quiet; then
    print_info "No version files to commit"
else
    print_step "Changes to be committed:"
    git diff pyproject.toml app-freeze.spec 2>/dev/null || true
    
    echo
    read -p "Commit these changes? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        print_error "Aborted. Changes not committed."
        git checkout -- pyproject.toml app-freeze.spec 2>/dev/null || true
        exit 1
    fi
    
    git add pyproject.toml app-freeze.spec 2>/dev/null || true
    git commit -m "chore: bump version to $NEW_VERSION"
fi

# Confirm tag creation
echo
print_step "Ready to create and push tag: $NEW_TAG"
read -p "Proceed? (Y/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Nn]$ ]]; then
    print_info "Aborted"
    exit 1
fi

# Create tag
print_step "Creating tag $NEW_TAG..."
git tag -a "$NEW_TAG" -m "Release $NEW_TAG"

# Push changes and tag
print_step "Pushing to remote..."
git push origin "$CURRENT_BRANCH"
git push origin "$NEW_TAG"

print_info ""
print_info "✓ Tag $NEW_TAG created and pushed successfully!"
print_info ""
print_info "GitHub Actions will now build and create a release."
print_info "Monitor progress at: https://github.com/dev-kasibhatla/app-freeze/actions"
print_info ""
