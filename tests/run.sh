#!/bin/bash
# Runs the installer against a fake system in a temporary folder. Touches nothing on the real one.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1; T=$(mktemp -d); trap 'rm -rf "$T"' EXIT; export NPCF_TEST_ROOT=$T/r NPCF_TEST_KERNEL=9.9.9-test; n=0; bad=0; ID=abc123
fresh() { rm -rf "$T/r"; local r=$T/r; mkdir -p $r/sys/class/dmi/id $r/sys/bus/pci/devices/a $r/sys/bus/acpi/devices/NVDA0820:00 $r/sys/firmware/acpi/tables $r/sys/firmware/efi/efivars $r/sys/kernel/security $r/boot/loader/entries $r/etc
  echo 'Dell Inc.' > $r/sys/class/dmi/id/sys_vendor; echo 'Dell G15 Special Edition 5521' > $r/sys/class/dmi/id/product_name; echo 1.44.0 > $r/sys/class/dmi/id/bios_version; echo 0x10de > $r/sys/bus/pci/devices/a/vendor; echo 0x24e0 > $r/sys/bus/pci/devices/a/device; echo 0 > $r/sys/bus/acpi/devices/NVDA0820:00/status
  printf 'DSDTxxxxxxDELL  Dell Inc DSNH NVDB DSNT' > $r/sys/firmware/acpi/tables/DSDT; printf 'SSDT____\002_DELL\0\0NvdTable____ DBEN NVDB' > $r/sys/firmware/acpi/tables/SSDT12; printf 'SSDT____\002_DELL\0\0OtherTab____' > $r/sys/firmware/acpi/tables/SSDT1
  printf '\006\0\0\0\0' > $r/sys/firmware/efi/efivars/SecureBoot-x; echo '[none] integrity' > $r/sys/kernel/security/lockdown; echo CONFIG_ACPI_TABLE_UPGRADE=y > $r/boot/config-9.9.9-test; echo $ID > $r/etc/machine-id; touch $r/boot/initramfs-9.9.9-test.img
  printf 'title Linux\nversion 9.9.9-test\nlinux /vmlinuz-9.9.9-test\ninitrd /initramfs-9.9.9-test.img\noptions root=UUID=x ro quiet\ngrub_class linux\n' > $r/boot/loader/entries/$ID-9.9.9-test.conf; }
t() { n=$((n+1)); if eval "$2"; then echo "pass  $1"; else echo "FAIL  $1"; bad=$((bad+1)); fi; }
tree() { (cd "$T/r" && find . -type f -exec sha256sum {} + | sort); }
refuses() { local b; b=$(tree); out=$(echo YES | ./install.sh 2>&1); [ $? -eq 1 ] && grep -q "REFUSED: .*$1" <<< "$out" && [ "$b" = "$(tree)" ]; }
fresh; b=$(tree); t "dry run writes nothing" './install.sh --dry-run > "$T/o" 2>&1 && grep -q "nothing was written" "$T/o" && [ "$b" = "$(tree)" ]'
t "cancel writes nothing" '! echo no | ./install.sh > /dev/null 2>&1 && [ "$b" = "$(tree)" ]'
s=$(sha256sum < $T/r/boot/loader/entries/$ID-9.9.9-test.conf); N=$T/r/boot/loader/entries/$ID-0-npcf-boost.conf
t "install works" 'echo YES | ./install.sh > "$T/o" 2>&1 && [ -f "$N" ]'
t "stock entry unchanged" '[ "$s" = "$(sha256sum < $T/r/boot/loader/entries/$ID-9.9.9-test.conf)" ]'
t "table comes before the initramfs" '[ "$(grep ^initrd "$N" | tr "\n" "|")" = "initrd /npcf-boost.cpio|initrd /initramfs-9.9.9-test.img|" ]'
t "kernel and options are kept" 'grep -q "^linux /vmlinuz-9.9.9-test" "$N" && grep -q "^options root=UUID=x ro quiet" "$N"'
t "cpio holds exactly the table" 'mkdir -p $T/x && (cd $T/x && cpio -id --quiet < $T/r/boot/npcf-boost.cpio) && cmp -s $T/x/kernel/firmware/acpi/npcf-on.aml src/npcf-on.aml && [ "$(cd $T/x && find . -type f | wc -l)" = 1 ]'
t "second install is refused" 'refuses "already installed"'
t "uninstall removes only its files" './uninstall.sh > /dev/null && [ "$b" = "$(tree)" ]'
fresh; sed -i 's#initrd /#initrd /boot/#' $T/r/boot/loader/entries/$ID-9.9.9-test.conf; t "boot inside root partition" 'echo YES | ./install.sh > /dev/null 2>&1 && grep -q "^initrd /boot/npcf-boost.cpio" "$N"'
fresh; echo 'Dell G15 5520' > $T/r/sys/class/dmi/id/product_name; t "refuses another model" 'refuses "made for the Dell G15"'
fresh; echo 0x2520 > $T/r/sys/bus/pci/devices/a/device; t "refuses another GPU" 'refuses "10de:24e0"'
fresh; echo 15 > $T/r/sys/bus/acpi/devices/NVDA0820:00/status; t "refuses when boost is already on" 'refuses "already announced"'
fresh; rm -r $T/r/sys/bus/acpi/devices/NVDA0820:00; t "refuses without the boost device" 'refuses "does not declare"'
fresh; printf 'SSDT____\002_DELL\0\0NvdTable____ NVDB' > $T/r/sys/firmware/acpi/tables/SSDT12; t "refuses an unknown NvdTable" 'refuses "expected methods"'
fresh; printf 'DSDT DSNH NVDB' > $T/r/sys/firmware/acpi/tables/DSDT; t "refuses a DSDT without markers" 'refuses "no field DSNT"'
fresh; printf '\006\0\0\0\001' > $T/r/sys/firmware/efi/efivars/SecureBoot-x; t "refuses with Secure Boot on" 'refuses "Secure Boot"'
fresh; echo 'none [integrity]' > $T/r/sys/kernel/security/lockdown; t "refuses a locked-down kernel" 'refuses "locked down"'
fresh; echo '# CONFIG_ACPI_TABLE_UPGRADE is not set' > $T/r/boot/config-9.9.9-test; t "refuses a kernel without support" 'refuses "cannot load"'
fresh; rm $T/r/boot/loader/entries/*.conf; t "refuses without a BLS entry" 'refuses "BLS"'
fresh; rm $T/r/boot/initramfs-9.9.9-test.img; t "refuses without an initramfs" 'refuses "initramfs"'
echo "$n tests, $bad failed"; [ $bad -eq 0 ]
