# Release Process

This document describes the automated release process for App Freeze.

## Overview

The project uses semantic versioning (semver) and automated builds via GitHub Actions.

## Quick Release

To create a new release:

```bash
# Patch release (0.1.0 -> 0.1.1)
./scripts/release.sh patch

# Minor release (0.1.0 -> 0.2.0)
./scripts/release.sh minor

# Major release (0.1.0 -> 1.0.0)
./scripts/release.sh major
```

## What Happens

1. **Version Update**: The script updates version numbers in:
   - `pyproject.toml`
   - `app-freeze.spec`

2. **Git Operations**:
   - Commits version changes
   - Creates annotated tag (e.g., `v0.2.0`)
   - Pushes to remote

3. **GitHub Actions Build**:
   - Triggered automatically on tag push
   - Runs tests and linting
   - Builds binaries for Linux and macOS
   - Creates GitHub release with artifacts

## Prerequisites

- Clean git working directory (no uncommitted changes)
- Be on `main` branch (recommended)
- Have push access to the repository

## Manual Process

If you need to create a release manually:

```bash
# 1. Update version in pyproject.toml and app-freeze.spec
# 2. Commit changes
git add pyproject.toml app-freeze.spec
git commit -m "chore: bump version to X.Y.Z"

# 3. Create and push tag
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin main
git push origin vX.Y.Z
```

## Monitoring

After pushing a tag, monitor the build:
- Visit: https://github.com/dev-kasibhatla/app-freeze/actions
- The "Build and Release" workflow will run
- Upon success, release will appear at: https://github.com/dev-kasibhatla/app-freeze/releases

## Troubleshooting

### Build fails
- Check GitHub Actions logs
- Ensure all tests pass locally: `uv run pytest -m "not integration"`
- Verify build works: `./build.sh`

### Version conflicts
- Make sure the new version is higher than existing tags
- Check: `git tag --list`

### Permission errors
- Ensure you have write access to the repository
- Check GitHub Actions has `contents: write` permission (already configured)

## Artifacts

Each release includes:
- `app-freeze-Linux-x86_64.tar.gz` - Linux binary
- `app-freeze-Darwin-x86_64.tar.gz` - macOS binary
- Auto-generated release notes from commits

## Rollback

To delete a tag if something goes wrong:

```bash
# Delete local tag
git tag -d vX.Y.Z

# Delete remote tag
git push origin :refs/tags/vX.Y.Z

# Delete the release on GitHub (via web UI)
```
