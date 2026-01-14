# Quick Release Guide

## Create a New Release

```bash
# For a patch release (bug fixes): 0.2.0 -> 0.2.1
./scripts/release.sh patch

# For a minor release (new features): 0.2.0 -> 0.3.0
./scripts/release.sh minor

# For a major release (breaking changes): 0.2.0 -> 1.0.0
./scripts/release.sh major
```

## What the Script Does

1. ✓ Checks for uncommitted changes (must be clean)
2. ✓ Pulls latest code
3. ✓ Increments version number
4. ✓ Updates `pyproject.toml` and `app-freeze.spec`
5. ✓ Commits version bump
6. ✓ Creates git tag (e.g., `v0.2.1`)
7. ✓ Pushes commit and tag to GitHub

## What GitHub Actions Does (Automatic)

1. ✓ Detects new tag push
2. ✓ Runs tests on Linux and macOS
3. ✓ Builds binaries with PyInstaller
4. ✓ Creates release artifacts (.tar.gz)
5. ✓ Publishes GitHub release with binaries

## Monitor Build

After running the script, watch the build progress:
- https://github.com/dev-kasibhatla/app-freeze/actions

## Download Release

Released binaries will be available at:
- https://github.com/dev-kasibhatla/app-freeze/releases

## Prerequisites

- Clean git working directory
- Be on `main` branch
- Have push access to repo

## Example

```bash
$ ./scripts/release.sh patch
[INFO] Latest tag: v0.1.0
[INFO] New version: v0.2.0
[STEP] Updating pyproject.toml...
[INFO] Updated pyproject.toml to version 0.2.0
[STEP] Updating app-freeze.spec...
[INFO] Updated app-freeze.spec to version 0.2.0
Proceed? (Y/n): y
[STEP] Creating tag v0.2.0...
[STEP] Pushing to remote...
[INFO] ✓ Tag v0.2.0 created and pushed successfully!
```

Then GitHub Actions automatically builds and releases!
