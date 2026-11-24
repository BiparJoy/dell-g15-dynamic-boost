#!/bin/bash
# Removes the boot entry and the table. usage: sudo ./uninstall.sh
set -euo pipefail
R=${NPCF_TEST_ROOT:-}; [ -n "$R" ] || [ "$EUID" -eq 0 ] || { echo "run it with sudo" >&2; exit 1; }
rm -fv "$R/boot/loader/entries/$(cat "$R/etc/machine-id")-0-npcf-boost.conf" "$R/boot/npcf-boost.cpio"; sync
echo "Removed. Restart into your normal entry."
