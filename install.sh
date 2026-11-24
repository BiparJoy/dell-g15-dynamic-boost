#!/bin/bash
# Adds one extra boot entry that loads the 148-byte table. Changes nothing else.
# usage: sudo ./install.sh [--dry-run]      --dry-run runs every check and writes nothing
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
R=${NPCF_TEST_ROOT:-}                        # tests point this at a fake system
K=${NPCF_TEST_KERNEL:-$(uname -r)}
DRY=; [ "${1:-}" = --dry-run ] && DRY=1
[ -n "${1:-}" ] && [ -z "$DRY" ] && { echo "usage: $0 [--dry-run]" >&2; exit 2; }
no() { echo "REFUSED: $*" >&2; exit 1; }
ok() { echo "  ok  $*"; }

[ -n "$R" ] || [ "$EUID" -eq 0 ] || no "run it with sudo"
for c in cpio sha256sum od; do command -v $c >/dev/null || no "$c is not installed"; done
(cd "$HERE/src" && sha256sum --quiet -c SHA256SUMS) || no "src/npcf-on.aml does not match its checksum"; ok "table checksum"

echo "Checking this machine"
DMI=$R/sys/class/dmi/id; MODEL="$(cat "$DMI/sys_vendor") $(cat "$DMI/product_name")"
[ "$MODEL" = "Dell Inc. Dell G15 Special Edition 5521" ] || no "this was made for the Dell G15 Special Edition 5521, not '$MODEL'"; ok "$MODEL"
BIOS=$(cat "$DMI/bios_version"); [ "$BIOS" = 1.44.0 ] && ok "BIOS $BIOS" || echo "  note  tested on BIOS 1.44.0, yours is $BIOS"
GPU=; for d in "$R"/sys/bus/pci/devices/*; do [ "$(cat "$d/vendor")" = 0x10de ] && [ "$(cat "$d/device")" = 0x24e0 ] && GPU=1; done
[ -n "$GPU" ] || no "no RTX 3070 Ti Laptop GPU (10de:24e0) found"; ok "GPU 10de:24e0"

# the fault itself: the firmware declares the boost device but reports it absent
shopt -s nullglob; DEV=("$R"/sys/bus/acpi/devices/NVDA0820:*)
[ ${#DEV[@]} -eq 1 ] || no "the firmware does not declare the boost device (NVDA0820)"
case "$(cat "${DEV[0]}/status")" in 0) ok "Dynamic Boost is hidden by the firmware";; 15) no "Dynamic Boost is already announced on this boot; nothing to do";; *) no "unexpected boost device status";; esac
T=$R/sys/firmware/acpi/tables; NV=
for f in "$T"/SSDT*; do [ "$(dd if="$f" bs=1 skip=16 count=8 status=none | tr -d '\0')" = NvdTable ] && NV=$f; done
[ -n "$NV" ] && grep -aq DBEN "$NV" && grep -aq NVDB "$NV" || no "Dell's NvdTable does not have the expected methods"
for n in DSNH DSNT NVDB; do grep -aq $n "$T/DSDT" || no "the DSDT has no field $n"; done; ok "Dell's tables have the expected flag and markers"

SB=("$R"/sys/firmware/efi/efivars/SecureBoot-*); [ ${#SB[@]} -eq 0 ] || [ "$(od -An -tu1 -j4 -N1 "${SB[0]}" | tr -d ' ')" = 0 ] || no "Secure Boot is on; the kernel would ignore the table"
L=$R/sys/kernel/security/lockdown; [ ! -e "$L" ] || grep -q '\[none\]' "$L" || no "the kernel is locked down; it would ignore the table"; ok "Secure Boot off, no lockdown"
grep -q '^CONFIG_ACPI_TABLE_UPGRADE=y' "$R/boot/config-$K" || no "kernel $K cannot load ACPI tables from an initrd"; ok "kernel $K can load the table"

ID=$(cat "$R/etc/machine-id"); E=$R/boot/loader/entries; STOCK=$E/$ID-$K.conf; NEW=$E/$ID-0-npcf-boost.conf; CPIO=$R/boot/npcf-boost.cpio
[ -f "$STOCK" ] || no "no boot entry $STOCK (only GRUB with BLS entries is supported)"
[ ! -e "$NEW" ] && [ ! -e "$CPIO" ] || no "already installed; run uninstall.sh first"
INITRD=$(awk '$1 == "initrd" {print $2; exit}' "$STOCK"); [ -n "$INITRD" ] && [ -f "$R/boot/$(basename "$INITRD")" ] || no "cannot find the initramfs of kernel $K"
grep -q '^linux ' "$STOCK" || no "the boot entry has no linux line"; PRE=$(dirname "$INITRD"); PRE=${PRE%/}; ok "boot entry for $K"
ENTRY=$(awk -v pre="$PRE" -v k="$K" '$1 == "title" {print "title GPU boost UNLOCK (" k ")"; next} $1 == "id" {next} $1 == "initrd" && !d {print "initrd " pre "/npcf-boost.cpio"; d = 1} {print}' "$STOCK")

echo; echo "This entry would be added as $NEW:"; echo "$ENTRY" | sed 's/^/    /'
[ -z "$DRY" ] || { echo; echo "Dry run: nothing was written."; exit 0; }
echo; echo "It raises the GPU power limit and heat. Your normal entry stays the default. Keep a rescue USB stick at hand."
read -rp "Type YES to add it: " a; [ "$a" = YES ] || no "cancelled, nothing was written"

W=$(mktemp -d); trap 'rm -rf "$W"' EXIT; BEFORE=$(sha256sum < "$STOCK")
mkdir -p "$W/kernel/firmware/acpi"; cp "$HERE/src/npcf-on.aml" "$W/kernel/firmware/acpi/"; (cd "$W" && find kernel | sort | cpio -H newc -o --quiet --reproducible -R 0:0) > "$W/npcf-boost.cpio"
echo "$ENTRY" > "$W/entry"; install -m 0644 "$W/npcf-boost.cpio" "$CPIO"; cmp -s "$W/npcf-boost.cpio" "$CPIO" || { rm -f "$CPIO"; no "could not write $CPIO"; }
install -m 0644 "$W/entry" "$NEW"; cmp -s "$W/entry" "$NEW" || { rm -f "$NEW" "$CPIO"; no "could not write $NEW"; }
sync; [ "$BEFORE" = "$(sha256sum < "$STOCK")" ] || no "the stock entry changed; please check $STOCK"
echo "Done. Restart and choose 'GPU boost UNLOCK', then run ./check.sh"
