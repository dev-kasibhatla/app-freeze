# app-freeze

Safely disable and enable Android apps across all users using ADB, without uninstalling or clearing data.

## What We Are Building

A terminal based interactive application that detects connected Android devices and lets a user enable or disable installed apps using a keyboard driven UI.

The tool:
- Works on non rooted devices
- Uses only adb
- Never removes APKs
- Never clears app data
- Is safe, reversible, and auditable

The UI behaves like a lightweight TUI application rather than a traditional one shot CLI.

## Why TUI and Not GUI

- No platform specific GUI dependencies
- Works over SSH
- Faster iteration and testing
- Easier binary packaging
- Lower maintenance cost
- Consistent UX across macOS and Linux

## Technology Decisions

Language
- Python 3.11+

Reasoning:
- Fast development
- Excellent TUI libraries
- Very readable for AI agents
- Strong testing ecosystem
- Simple cross platform builds

TUI Framework
- Textual (preferred)
- Rich for rendering and colors

Reasons:
- Native keyboard and mouse support
- Layouts, borders, headers, footers built in
- Event driven architecture
- Clean separation of state and UI

ADB Interaction
- subprocess.run with explicit timeout
- No shell=True
- All adb calls isolated in one module
- Output parsed into structured models

## Binary Distribution

Goal:
- Single file binary
- No Python required on target machine
- Works on macOS and Linux

Tooling:
- PyInstaller in onefile mode

Notes:
- Build per platform
- Static linking where possible
- Strip symbols
- Disable debug output
- Use UPX compression if compatible

Reverse Engineering Considerations
- Python bytecode frozen into executable
- No plain text scripts shipped
- Minimal logging
- No secrets embedded
- Obfuscation is not a primary goal but casual inspection should be difficult

## High Level Architecture

```

app/
main.py              # entry point
state.py             # app state models
adb/
client.py          # adb wrapper
parser.py          # output parsing
ui/
screens/
main.py
device.py
confirm.py
help.py
widgets/
reports/
tests/

```

Key Principles
- UI never calls adb directly
- UI reacts only to state changes
- adb layer returns structured results
- All side effects are explicit

## Screen Flow

Main Screen
- Detect adb
- Detect devices
- Show connection status
- If multiple devices exist, show selector

Device Screen
- Fetch and display device metadata
- Fetch and display installed apps
- Show enabled or disabled state
- Show app size in MB
- Scrollable, searchable list
- Keyboard and mouse selection

Confirm Screen
- Two column app list
- Clear action label (Enable or Disable)
- Explicit confirmation required

Execution Screen
- Progress bar
- Live per app status
- Color coded results
- No blocking UI

Summary
- Totals
- Failures
- Return navigation

## Example ADB Commands Used

Disable app for a user
```

adb shell pm disable-user --user 0 com.example.app

```

Enable app for a user
```

adb shell pm enable --user 0 com.example.app

```

List users
```

adb shell pm list users

```

List packages
```

adb shell pm list packages

```

## Reporting

Each operation creates a report file.

Filename:
```

reports/<device-id>-<timestamp>.md

```

Contents:
- Device metadata
- Action performed
- App list with status
- Per app result
- Failure reasons
- Timestamp

Reports are append only and never overwritten.

## Safety Guarantees

- No uninstall commands used
- No pm clear ever used
- No root access
- No system image changes
- All operations reversible

## Non Goals

- No background daemon
- No cloud sync
- No analytics
- No app store interaction

This tool should feel boring, predictable, and trustworthy.
