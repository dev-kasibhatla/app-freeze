# Safety Guarantees

App Freeze is designed with safety as the top priority. This document details all safety measures and guarantees.

## Core Safety Principles

### 1. No Data Loss

**Guarantee:** App Freeze will **NEVER** delete or clear any app data.

**How we ensure this:**
- ❌ Never uses `pm uninstall` command
- ❌ Never uses `pm clear` command
- ❌ Never uses `rm` or file deletion commands
- ✅ Only uses `pm disable-user` and `pm enable` commands
- ✅ These commands only change app state, not data

**What this means:**
- All app data remains intact (databases, preferences, files)
- App configuration is preserved
- User data within apps is untouched
- Cache and storage remain unchanged

### 2. Fully Reversible Operations

**Guarantee:** Every operation can be completely reversed.

**How it works:**
- Disabling an app with `pm disable-user` can be reversed with `pm enable`
- App state is the only thing modified
- No permanent changes to system partitions
- No modification of APK files

**Reversibility examples:**
```bash
# Disable app
adb shell pm disable-user --user 0 com.example.app

# Enable it back - fully restored
adb shell pm enable --user 0 com.example.app
```

### 3. Explicit Confirmations

**Guarantee:** No destructive actions without explicit user confirmation.

**Confirmation flow:**
1. **Selection Screen** - User selects apps
2. **Confirmation Screen** - User reviews selection and confirms
3. **Execution** - Only then are changes made

**Features:**
- Clear display of apps to be modified
- Explicit action label (Enable/Disable)
- Must press Enter or 'y' to confirm
- Can cancel at any time with 'n', Esc, or 'q'

### 4. No Root Required

**Guarantee:** Works with standard ADB permissions only.

**What this means:**
- No system partition modifications
- No root-level commands
- No bypassing of Android security
- Works within standard Android permission model

**Why this matters:**
- Safer for your device
- No risk of bricking
- No warranty implications
- Complies with Android security model

### 5. Comprehensive Error Handling

**Guarantee:** Graceful handling of all error conditions.

**Error scenarios handled:**
- Device disconnection during operation
- Permission denied errors (with helpful guidance)
- ADB communication failures
- Timeout conditions
- Invalid package names
- Per-app failures (continues with remaining apps)

**What happens on error:**
- Clear error messages displayed
- Operation continues for remaining apps
- Detailed error logging in reports
- Terminal state always restored
- No partial/corrupted state

### 6. Detailed Audit Trail

**Guarantee:** Complete record of all operations.

**Report contents:**
- Device metadata (ID, model, Android version)
- Timestamp of operation
- Action performed (Enable/Disable)
- Complete list of apps processed
- Success/failure status for each app
- Detailed error messages for failures

**Report location:**
- `reports/{device-id}-{timestamp}.md`
- Markdown format for easy reading
- Never overwritten (timestamp ensures uniqueness)

### 7. Multi-User Safety

**Guarantee:** Proper handling of Android multi-user scenarios.

**How it works:**
- Automatically detects all users on device
- Applies changes to all users consistently
- Prevents partial state across users
- User 0 (owner) always handled

**Why this matters:**
- Consistent app state across all device users
- No orphaned app states
- Works correctly on work profiles
- Proper handling of guest accounts

### 8. Terminal State Protection

**Guarantee:** Terminal is always restored to original state.

**Protections:**
- Clean exit on Ctrl+C
- Resource cleanup on error
- Proper exception handling
- No terminal corruption on crash

**What this means:**
- Terminal always remains usable
- No stuck states
- No escape sequence corruption
- Clean exit under all conditions

## What App Freeze Does NOT Do

### Never Does:

1. ❌ **Uninstall apps** - No `pm uninstall` command used
2. ❌ **Clear app data** - No `pm clear` command used
3. ❌ **Modify APK files** - Files are read-only to this tool
4. ❌ **Modify system partition** - No root, no system writes
5. ❌ **Send data externally** - No network, no telemetry
6. ❌ **Access app content** - Only reads package metadata
7. ❌ **Require root** - Works with standard ADB permissions
8. ❌ **Make silent changes** - Always requires confirmation

### Only Does:

1. ✅ **Read package list** - Via `pm list packages`
2. ✅ **Read package metadata** - Via `dumpsys package`
3. ✅ **Enable apps** - Via `pm enable`
4. ✅ **Disable apps** - Via `pm disable-user`
5. ✅ **List users** - Via `pm list users`
6. ✅ **Write local reports** - In `reports/` directory only

## Android Permission Model

### Required Permissions:

- **USB Debugging** - Enabled in Developer Options
- **USB Debugging Authorization** - One-time prompt on device

### What these permissions allow:

- Execute shell commands via ADB
- Read package information
- Modify app enabled/disabled state

### What these permissions DO NOT allow:

- Deleting apps or data
- Accessing app content
- Modifying system files
- Accessing personal data

## Verification

### Verify Safety Yourself:

1. **Check source code** - All operations in `src/app_freeze/adb/client.py`
2. **Review ADB commands** - Search for "pm " in codebase
3. **Check reports** - See exactly what was done
4. **Test reversibility** - Disable then re-enable an app
5. **Monitor ADB logs** - Run `adb logcat` during operation

### ADB Commands Used:

```bash
# List devices
adb devices -l

# Get device properties  
adb shell getprop ro.product.model
adb shell getprop ro.product.manufacturer
adb shell getprop ro.build.version.release
adb shell getprop ro.build.version.sdk

# List packages
adb shell pm list packages

# Get package info
adb shell dumpsys package {package_name}

# List users
adb shell pm list users

# Enable/Disable (only state-changing commands)
adb shell pm enable {package_name}
adb shell pm disable-user --user {user_id} {package_name}
```

No other ADB commands are used.

## Limitations of Safety

While App Freeze is designed to be completely safe, please be aware:

1. **System apps** - Some system apps should not be disabled (they may cause boot loops)
   - App Freeze shows system apps separately
   - Confirmation required before modifying system apps
   
2. **Essential apps** - Disabling launcher or settings can make device hard to use
   - Can always be re-enabled via ADB
   - Reports show what was disabled

3. **No warranty** - While safe, use at your own risk
   - Test on non-critical device first
   - Keep USB debugging available for recovery

## Recovery Procedures

### If something goes wrong:

1. **Device won't boot properly:**
   ```bash
   # Boot to safe mode (method varies by device)
   # Or use ADB to re-enable apps
   ```

2. **App Freeze itself has issues:**
   ```bash
   # You can always use ADB directly:
   adb shell pm enable {package_name}
   ```

3. **Terminal corrupted:**
   ```bash
   # Reset terminal
   reset
   ```

## Security Considerations

1. **No network access** - App Freeze never connects to network
2. **No telemetry** - No usage data collected
3. **Local reports only** - Reports saved locally only
4. **Open source** - All code is visible and auditable
5. **No external dependencies** - Minimal attack surface

## Compliance

App Freeze complies with:
- Android Debug Bridge (ADB) best practices
- Python security guidelines
- Standard Unix security model
- No violation of Android terms of service

## Questions or Concerns?

If you have any safety concerns or questions:
- Review the source code
- Open an issue on GitHub
- Test on a non-critical device first
- Check the detailed reports after operations

**Remember:** Safety is our top priority. If something doesn't feel right, don't use it.
