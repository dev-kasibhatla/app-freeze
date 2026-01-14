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
- prompt_toolkit (primary)
- Rich for formatted output

Reasons:
- Instant startup (no async initialization overhead)
- Synchronous event loop - simpler mental model
- First-class keyboard navigation (Vi/Emacs modes)
- Lightweight and fast like lazygit
- Built-in completion, search, and filtering
- Full-screen layouts with HSplit/VSplit
- Works perfectly with PyInstaller

Design Goals (lazygit-inspired):
- Sub-100ms startup time
- Compact single-screen layout with panels
- All actions accessible via single keystrokes
- Real-time filtering/search with '/'
- No modal dialogs - inline confirmations
- Status bar shows current context and keybindings

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

Single-Screen Layout (lazygit-style):
```
┌─────────────────────────────────────────────────────────────────┐
│ App Freeze - Device: Pixel 7 (abc123)                    [?]Help│
├─────────────────────────────────────────────────────────────────┤
│ Filter: _____________                        [d]isabled [e]nabled│
├─────────────────────────────────────────────────────────────────┤
│   Package Name                           Size    State   Action │
│ ─────────────────────────────────────────────────────────────── │
│ > com.facebook.katana                   150MB   enabled   [ ]   │
│   com.instagram.android                 120MB   enabled   [ ]   │
│   com.whatsapp                           80MB   enabled   [x]   │
│   com.twitter.android                    90MB  disabled   [ ]   │
│                                                                 │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ 1 selected │ [space]toggle [a]ll [n]one [D]isable [E]nable [q]uit│
└─────────────────────────────────────────────────────────────────┘
```

Keybindings:
- j/k or ↑/↓: Navigate list
- space: Toggle selection
- a: Select all visible
- n: Deselect all
- /: Focus filter input
- d: Show only disabled apps
- e: Show only enabled apps
- D: Disable selected apps (with inline confirm)
- E: Enable selected apps (with inline confirm)
- y: Confirm action
- q: Quit / cancel
- ?: Show help

Inline Confirmation:
- When D or E pressed, status bar changes to:
  "Disable 3 apps? [y]es [n]o"
- No modal dialog - stays in same view
- Shows affected apps highlighted

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
