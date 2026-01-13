# Keyboard Shortcuts Reference

Complete reference for all keyboard shortcuts in App Freeze.

## Global Shortcuts

Available on all screens:

| Key | Action | Description |
|-----|--------|-------------|
| `q` | Quit/Back | Exit application or return to previous screen |
| `?` | Help | Show help overlay with keybindings |
| `Ctrl+C` | Force Quit | Emergency exit (terminal restored) |

## Device Selection Screen

| Key | Action | Description |
|-----|--------|-------------|
| `↑` / `k` | Move Up | Navigate to previous device |
| `↓` / `j` | Move Down | Navigate to next device |
| `Enter` | Select | Select the highlighted device |
| `r` | Refresh | Re-scan for connected devices |
| `q` | Quit | Exit application |

## App List Screen

### Navigation

| Key | Action | Description |
|-----|--------|-------------|
| `↑` / `k` | Move Up | Navigate to previous app |
| `↓` / `j` | Move Down | Navigate to next app |
| `Page Up` | Page Up | Jump up one page |
| `Page Down` | Page Down | Jump down one page |
| `Home` | Go to Top | Jump to first app |
| `End` | Go to Bottom | Jump to last app |
| `Tab` | Next Section | Switch to next UI section |
| `Shift+Tab` | Previous Section | Switch to previous UI section |

### Selection

| Key | Action | Description |
|-----|--------|-------------|
| `Space` | Toggle | Toggle selection for highlighted app |
| `Enter` | Toggle | Same as Space - toggle selection |
| `a` | Select All | Select all visible apps |
| `n` | Clear Selection | Deselect all apps |
| `s` | Toggle System | Show/hide system apps |

### Actions

| Key | Action | Description |
|-----|--------|-------------|
| `e` | Enable | Enable all selected apps (shows confirmation) |
| `d` | Disable | Disable all selected apps (shows confirmation) |
| `q` | Back | Return to device selection |

## Confirmation Screen

| Key | Action | Description |
|-----|--------|-------------|
| `y` / `Enter` | Confirm | Proceed with the operation |
| `n` / `Esc` | Cancel | Cancel operation and return |
| `q` | Cancel | Same as 'n' - cancel and return |

## Execution Screen

| Key | Action | Description |
|-----|--------|-------------|
| `Enter` | Continue | Dismiss screen when operation complete |
| `q` | Continue | Same as Enter - dismiss when done |

Note: During execution, no input is accepted until operation completes.

## Help Overlay

| Key | Action | Description |
|-----|--------|-------------|
| `Esc` | Close | Close help overlay |
| `q` | Close | Close help overlay |
| `?` | Close | Toggle help overlay |

## Mouse Support

Mouse support is available (if your terminal supports it):

| Action | Effect |
|--------|--------|
| Click | Select app or UI element |
| Scroll | Navigate app list |
| Double-click | Toggle app selection |

## Terminal Compatibility

### Recommended Terminals

- **Linux**: GNOME Terminal, Konsole, Alacritty, kitty
- **macOS**: Terminal.app, iTerm2, Alacritty, kitty
- **SSH**: Works well over SSH with proper terminal emulation

### Key Combinations

Some terminals may interpret certain keys differently:

- If `Ctrl+C` doesn't work, try `q` to quit
- If arrow keys don't work, try `hjkl` (Vim-style navigation)
- If `Tab` doesn't work, try clicking to change focus

## Tips & Tricks

1. **Fast Navigation**: Use `j`/`k` for quick, Vim-style movement
2. **Bulk Selection**: Press `a` to select all, then `Space` to deselect specific apps
3. **System Apps**: Press `s` to toggle system app visibility for cleaner list
4. **Quick Help**: Press `?` anytime to see keybindings without exiting
5. **Abort Safely**: Press `q` at any screen before confirmation - no changes made

## Accessibility

- All functionality available via keyboard
- Clear visual feedback for selections
- Color-coded status indicators
- Progress bars for long operations
- Help overlay always available via `?`
