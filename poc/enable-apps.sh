#!/usr/bin/env bash

# ===== CONFIG =====
PACKAGES=(
  com.facebook.katana
  com.instagram.android
)
# ==================

# never exit shell on errors
set +e

failures=0

# check adb
if ! command -v adb >/dev/null 2>&1; then
  echo "ERROR: adb not found in PATH"
  exit 1
fi

# check device
if ! adb get-state >/dev/null 2>&1; then
  echo "ERROR: no adb device connected or authorized"
  exit 1
fi

USERS=$(adb shell pm list users 2>/dev/null | sed -n 's/.*{\([0-9]\+\):.*/\1/p')

if [ -z "$USERS" ]; then
  echo "ERROR: no users found"
  exit 1
fi

for user in $USERS; do
  for pkg in "${PACKAGES[@]}"; do
    printf "Enabling %-40s user %s ... " "$pkg" "$user"
    if adb shell pm enable --user "$user" "$pkg" >/dev/null 2>&1; then
      echo "OK"
    else
      echo "FAILED"
      failures=$((failures + 1))
    fi
  done
done

echo "Finished with $failures failure(s)"
