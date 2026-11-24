#!/bin/bash
# Shows whether the unlock is active on this boot. Needs no root. Changes nothing.
s=$(cat /sys/bus/acpi/devices/NVDA0820:*/status 2>/dev/null); case "$s" in 15) echo "Boost device: announced (unlock active)";; 0) echo "Boost device: hidden (stock)";; *) echo "Boost device: not found";; esac
journalctl -k -b --no-pager -o cat 2>/dev/null | grep -E 'Table Upgrade.*NPCFON' || echo "The added table was not loaded on this boot, or the log is not readable"
echo "nvidia-powerd: $(systemctl is-active nvidia-powerd)"; nvidia-smi --query-gpu=enforced.power.limit,power.max_limit,power.draw,temperature.gpu --format=csv
