# Known Limitations and Edge Cases

This document describes known limitations, edge cases, and potential issues with App Freeze.

## System Requirements

### Required

- **Python 3.11+** (for running from source; binaries are standalone)
- **ADB (Android Debug Bridge)** must be installed and in PATH
- **USB Debugging** must be enabled on Android device
- **USB connection** or wireless ADB connection

### Platform Support

**Supported:**
- ✅ Linux (tested on Ubuntu, Fedora, Arch)
- ✅ macOS (tested on 11+)

**Not Supported:**
- ❌ Windows (Textual TUI library has limited Windows support)
  - May work in WSL2 (Windows Subsystem for Linux)
  - Native Windows support not guaranteed

**Workaround for Windows:**
- Use WSL2 (recommended)
- Use a Linux VM
- Use Git Bash or MinGW (untested)

## Android Device Limitations

### Minimum Android Version

- **Tested:** Android 5.0 (API 21) and above
- **Recommended:** Android 7.0+ for best compatibility
- Older versions may work but are untested

### USB Debugging

**Required:**
1. Developer Options must be enabled
2. USB Debugging must be enabled
3. USB Debugging authorization must be granted

**Common Issues:**
- Some devices hide Developer Options deeply in settings
- Some manufacturers require additional steps
- Some ROMs have different permission models

### System Apps

**Limitations:**
- Some system apps cannot be disabled (Android restriction)
- Disabling critical system apps can cause issues:
  - Launcher (home screen) - device may boot to black screen
  - Settings - unable to access settings
  - System UI - interface elements disappear
  - Phone/Contacts - calling may not work

**Workaround:**
- System apps shown separately - use caution
- Can always re-enable via ADB command line
- Keep USB debugging enabled for recovery

**Recovery:**
```bash
# If launcher disabled:
adb shell pm enable com.android.launcher
# Or boot to safe mode and re-enable
```

### Multi-User Devices

**Works with:**
- ✅ Multiple Android users
- ✅ Work profiles (Android for Work)
- ✅ Guest users

**Limitation:**
- All users affected simultaneously
- Cannot selectively enable/disable per user
- App state must be consistent across users

**Why:** This is actually safer - prevents partial/inconsistent state

### Manufacturer-Specific Issues

**Samsung:**
- Some Knox-protected apps cannot be disabled
- Bixby and Samsung apps may have special protection

**Xiaomi (MIUI):**
- MIUI optimization may re-enable apps automatically
- Some system apps protected by MIUI

**Huawei:**
- EMUI has additional restrictions
- Some apps tied to EMUI framework

**OnePlus:**
- OxygenOS generally works well
- Some system apps part of OxygenOS core

**Workaround:** Test with non-critical apps first

## ADB Limitations

### Connection Issues

**USB Connection:**
- Device must remain connected during operations
- Disconnection during operation handled gracefully but stops process
- USB cable quality matters (some cables are charge-only)

**Wireless ADB:**
- Should work but has higher latency
- More prone to disconnections
- Not recommended for large batch operations

### Permission Model

**USB Debugging Authorization:**
- Must be accepted on device when first connecting
- Some devices require re-authorization after reboot
- Authorization can be revoked in developer settings

**ADB Permissions:**
- Cannot access content inside apps (good for security)
- Cannot modify system partition (safe)
- Cannot delete apps or data (safe)

### Timeout Constraints

**Default timeouts:**
- Standard commands: 30 seconds
- Property queries: 5 seconds

**When timeouts occur:**
- Very slow device
- Many apps (thousands)
- Device under heavy load
- Wireless ADB with poor connection

**Workaround:** Run on fewer apps at once

## Performance Limitations

### Large App Lists

**Issue:** Devices with 500+ apps may be slow to:
- Load app list
- Fetch app sizes
- Display in UI

**Workaround:**
- Use system app filter to reduce visible apps
- Operations still work, just slower initial load

### Batch Operations

**Issue:** Enabling/disabling many apps sequentially
- Each app processed one at a time
- Many apps = longer operation time

**Why sequential:** Safer, better error handling, clearer progress

**Typical speed:** ~1-2 apps per second

**Example:** 100 apps = ~1-2 minutes

### Size Calculation

**Issue:** Fetching app sizes is slow
- Requires `du` command per app
- Can add significant time to initial load

**Current behavior:** Size fetching enabled by default

**Potential improvement:** Add option to skip size fetching

## UI Limitations

### Terminal Requirements

**Minimum terminal size:**
- Width: 80 columns (recommended: 100+)
- Height: 24 rows (recommended: 30+)

**Too small terminal:**
- Layout may break
- Some content may be hidden
- Resize terminal to fix

### Color Support

**Requirements:**
- Terminal must support 256 colors
- Most modern terminals do

**Fallback:**
- Works in monochrome but less visually appealing

### Mouse Support

**Availability:**
- Depends on terminal emulator
- Works in: iTerm2, GNOME Terminal, Konsole
- May not work in: basic terminals, some SSH scenarios

**Workaround:** All functionality available via keyboard

## Report Generation

### Report Location

**Default:** `reports/` directory in current working directory

**Limitation:**
- If no write permission, report will fail silently
- If disk full, report may be incomplete

**Workaround:** Ensure reports directory is writable

### Report Accumulation

**Issue:** Reports are never deleted automatically
- Can accumulate over time
- Each operation creates new report

**Workaround:** Manually clean up old reports periodically

## Error Handling

### Partial Failures

**Scenario:** 10 apps selected, 2 fail to disable

**Behavior:**
- Continues with remaining 8 apps
- Reports success for 8, failure for 2
- Both successes and failures shown in report

**Limitation:** No automatic retry of failed apps

### Device Disconnection

**During operation:**
- Currently executing app completes or fails
- Remaining apps not processed
- Partial results saved in report

**Recovery:** Re-run after reconnecting device

### Permission Denied

**Common causes:**
- USB debugging not authorized
- Some apps have special protection
- Manufacturer-specific restrictions

**Behavior:**
- Clear error message with guidance
- Operation stops (for device permission issues)
- Or continues with next app (for app-specific issues)

## Security Limitations

### No Encryption

**Reports:** Saved as plain text markdown
- Contains device info
- Contains app list
- No sensitive user data, but device-identifying

**Workaround:** Encrypt your disk

### USB Debugging Risks

**When enabled:**
- Device can be controlled via ADB
- Physical access = full control
- Keep device locked when not in use

**Not a limitation of App Freeze:** This is how ADB works

## Known Issues

### Issue #1: Rapid Enable/Disable

**Problem:** Rapidly enabling then disabling same app may not work

**Cause:** Android caching

**Workaround:** Wait a few seconds between operations

### Issue #2: Some Apps Remain "Enabled" After Disable

**Problem:** App shows as enabled even after disable command succeeds

**Cause:** Android behavior, app is disabled for user but installed state shown

**Verification:** Check `dumpsys package` output - will show disabled state

### Issue #3: Terminal Corruption on Ctrl+Z

**Problem:** Suspending app with Ctrl+Z may corrupt terminal

**Workaround:** Use `q` to quit properly, or `reset` command to fix terminal

## Feature Limitations (Not Yet Implemented)

**Not included:**
- ❌ Search/filter apps by name
- ❌ Sort apps by different criteria
- ❌ Export app list to CSV
- ❌ Bulk operations from file
- ❌ App comparison between devices
- ❌ Schedule enable/disable
- ❌ Custom report formats

These may be added in future versions.

## Platform-Specific Issues

### Linux

**Issue:** AppArmor or SELinux may block ADB
**Workaround:** Add exception or disable temporarily

### macOS

**Issue:** Gatekeeper may block unsigned binary
**Workaround:** `xattr -d com.apple.quarantine app-freeze`

**Issue:** Terminal.app has limited color support
**Workaround:** Use iTerm2 or another modern terminal

### SSH/Remote Use

**Issue:** Some key combinations don't work over SSH
**Workaround:** Use alternative keybindings (j/k instead of arrows)

**Issue:** Terminal size detection may fail
**Workaround:** Export COLUMNS and LINES environment variables

## Recommended Best Practices

1. **Test first** - Try on non-critical device initially
2. **System apps** - Be very careful with system apps
3. **Keep reports** - Don't delete reports of system app changes
4. **USB debugging** - Keep enabled for emergency recovery
5. **Backups** - While App Freeze doesn't touch data, always backup critical data
6. **Small batches** - For safety, disable apps in small batches first
7. **Check reports** - Review operation reports for failures

## Getting Help

**If you encounter issues:**

1. Check this document first
2. Review [SAFETY.md](SAFETY.md) for recovery procedures
3. Check ADB connection: `adb devices`
4. Check ADB version: `adb version`
5. Check device authorization
6. Review operation reports in `reports/`
7. Open an issue on GitHub with:
   - App Freeze version
   - Operating system
   - ADB version
   - Device model and Android version
   - Complete error message
   - Steps to reproduce

## Future Improvements

Potential improvements to address limitations:

- [ ] Windows native support
- [ ] Async app size fetching
- [ ] Configurable timeouts
- [ ] Search/filter functionality
- [ ] Report cleanup utility
- [ ] Per-user enable/disable
- [ ] Retry failed operations
- [ ] Export/import app lists

Contributions welcome!
