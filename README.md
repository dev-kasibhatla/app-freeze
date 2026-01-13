# Disable Android Packages
Idea is to disable unwanted packages on Android devices using ADB commands without deleting data.

## Prerequisites
- Ensure you have ADB installed on your computer.
- Connect your Android device via USB and enable USB debugging.

## Disable packages
To disable a specific package, use the following command:
In the `disable-apps.sh` script, declare an array of package names you want to disable.
Then run the script to disable them.
```bash
. /disable-apps.sh
```

## Enable packages
To re-enable a specific package, use the following command:
In the `enable-apps.sh` script, declare an array of package names you want to enable.
Then run the script to enable them.
```bash
. /enable-apps.sh
```


## Verification Commands
```
adb shell pm list packages -d
adb shell dumpsys package com.package.name | grep enabled
```