#!/usr/bin/env python3
import json
import re
import subprocess
import sys


DEFAULT_ICONS = ["󰁺", "󰁻", "󰁼", "󰁽", "󰁾", "󰁿", "󰂀", "󰂁", "󰂂", "󰁹"]
CHARGING_ICONS = ["󰢜", "󰂆", "󰂇", "󰂈", "󰢝", "󰂉", "󰢞", "󰂊", "󰂋", "󰂅"]


def field(text, name):
    match = re.search(rf"^\s*{re.escape(name)}:\s*(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def icon_for(percent, charging):
    icons = CHARGING_ICONS if charging else DEFAULT_ICONS
    index = max(0, min(len(icons) - 1, int(percent / 10)))
    return icons[index]


def main():
    result = subprocess.run(
        ["upower", "-i", "/org/freedesktop/UPower/devices/DisplayDevice"],
        check=False,
        capture_output=True,
        text=True,
        timeout=1.5,
    )

    if result.returncode != 0:
        return

    text = result.stdout
    native_path = field(text, "native-path")
    power_supply = field(text, "power supply")
    device_type = field(text, "type")
    state = field(text, "state")
    percentage = field(text, "percentage")
    time_to_empty = field(text, "time to empty")
    time_to_full = field(text, "time to full")
    energy_rate = field(text, "energy-rate")

    if (
        device_type != "battery"
        or native_path in {"", "(null)"}
        or power_supply == "no"
    ):
        return

    try:
        percent = float(percentage.rstrip("%"))
    except ValueError:
        return

    charging = state in {"charging", "pending-charge"}
    discharging = state in {"discharging", "pending-discharge"}
    plugged = state in {"fully-charged", "empty", "unknown"} and percent >= 99

    if plugged:
        display = "󰂅" if percent >= 100 else ""
    else:
        remaining = time_to_full if charging else time_to_empty
        time_part = f" {remaining}" if remaining and (charging or discharging) else ""
        display = f"{percent:.0f}%{time_part} {icon_for(percent, charging)}"

    css_class = "low"
    if percent <= 10 and discharging:
        css_class = "high"
    elif percent <= 20 and discharging:
        css_class = "medium"

    arrow = "↑" if charging else "↓"
    tooltip = f"{energy_rate}{arrow} {percent:.0f}%" if energy_rate else f"{percent:.0f}%"
    print(json.dumps({"text": display, "class": css_class, "tooltip": tooltip}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
