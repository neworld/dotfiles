#!/usr/bin/env python3
import json
import re
import subprocess
import sys


DEFAULT_ICONS = ["󰁺", "󰁻", "󰁼", "󰁽", "󰁾", "󰁿", "󰂀", "󰂁", "󰂂", "󰁹"]
CHARGING_ICONS = ["󰢜", "󰂆", "󰂇", "󰂈", "󰢝", "󰂉", "󰢞", "󰂊", "󰂋", "󰂅"]
ALMOST_EMPTY_THRESHOLD = 10
KNOWN_DEVICE_TYPES = {
    "battery",
    "computer",
    "display",
    "gaming-input",
    "headphones",
    "headset",
    "keyboard",
    "line-power",
    "monitor",
    "mouse",
    "phone",
    "tablet",
    "ups",
}
BATTERY_LEVEL_PERCENT = {
    "unknown": None,
    "none": None,
    "empty": 0,
    "critical": 5,
    "low": 10,
    "normal": 50,
    "high": 75,
    "full": 100,
}


def split_devices(text):
    devices = []
    current = []

    for line in text.splitlines():
        if line.startswith("Device: "):
            if current:
                devices.append("\n".join(current))
            current = [line]
        elif current:
            current.append(line)

    if current:
        devices.append("\n".join(current))

    return devices


def parse_device(block):
    lines = block.splitlines()
    if not lines:
        return {}

    first = lines[0].strip()
    path = first.split("Device:", 1)[1].strip() if first.startswith("Device:") else ""
    fields = {"path": path, "type": ""}

    for raw_line in lines[1:]:
        line = raw_line.strip()
        if not line:
            continue

        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip().lower()] = value.strip().strip("'")
        elif line in KNOWN_DEVICE_TYPES:
            fields["type"] = line

    return fields


def percentage_value(value):
    match = re.search(r"(-?\d+(?:\.\d+)?)\s*%", value or "")
    return float(match.group(1)) if match else None


def percent_for(device):
    percent = percentage_value(device.get("percentage", ""))
    if percent is not None:
        return percent

    level = device.get("battery-level", "").lower()
    return BATTERY_LEVEL_PERCENT.get(level)


def parse_time_minutes(value):
    match = re.search(r"(\d+(?:\.\d+)?)\s+([a-zA-Z]+)", value or "")
    if not match:
        return None

    amount = float(match.group(1))
    unit = match.group(2).lower()
    if unit.startswith("second"):
        return amount / 60
    if unit.startswith("minute"):
        return amount
    if unit.startswith("hour"):
        return amount * 60
    if unit.startswith("day"):
        return amount * 24 * 60
    return None


def parse_watts(value):
    match = re.search(r"(-?\d+(?:\.\d+)?)\s*W", value or "")
    return float(match.group(1)) if match else None


def format_percent(percent):
    return str(int(percent + 0.5))


def format_time_label(minutes):
    rounded_minutes = max(0, int(minutes + 0.5))
    small_buckets = [0, 5, 10, 30, 60, 90]

    if rounded_minutes <= 90:
        bucket = min(small_buckets, key=lambda value: (abs(value - rounded_minutes), -value))
        return f"{bucket}m"

    hours = max(2, int((rounded_minutes / 60) + 0.5))
    return f"{hours}h"


def battery_icon(percent, charging=False):
    icons = CHARGING_ICONS if charging else DEFAULT_ICONS
    if percent is None:
        return icons[0]

    index = max(0, min(len(icons) - 1, int(percent / 10)))
    return icons[index]


def is_display_device(device):
    return device.get("path", "").endswith("/DisplayDevice")


def is_laptop(device):
    return (
        device.get("type") == "battery"
        and device.get("power supply") == "yes"
        and not is_display_device(device)
    )


def is_battery_device(device):
    if is_display_device(device):
        return False
    if device.get("type") == "line-power":
        return False
    if device.get("present", "yes") == "no":
        return False
    return percent_for(device) is not None or bool(device.get("battery-level"))


def has_active_charge(device):
    state = device.get("state", "")
    if state == "charging":
        return True
    return state == "pending-charge" and (
        parse_watts(device.get("energy-rate")) not in (None, 0)
        or bool(device.get("time to full"))
    )


def has_active_discharge(device):
    state = device.get("state", "")
    if state == "discharging":
        return True
    return state == "pending-discharge" and (
        parse_watts(device.get("energy-rate")) not in (None, 0)
        or bool(device.get("time to empty"))
    )


def class_for(device, percent):
    warning = device.get("warning-level", "").lower()
    if warning in {"critical", "action"} or (
        percent is not None and percent <= ALMOST_EMPTY_THRESHOLD
    ):
        return "low"
    if has_active_charge(device):
        return "charging"
    return "normal"


def stable_label(device, percent):
    state = device.get("state", "")
    if state == "fully-charged" or (percent is not None and percent >= 99):
        return "full"
    if state in {"pending-charge", "pending-discharge"}:
        return "hold"
    return "idle"


def laptop_text(device, percent):
    if has_active_charge(device):
        icon = battery_icon(percent, charging=True)
        minutes = parse_time_minutes(device.get("time to full"))
        return f"{icon} {format_time_label(minutes)}" if minutes is not None else f"{icon} chg"

    icon = battery_icon(percent)
    if has_active_discharge(device):
        minutes = parse_time_minutes(device.get("time to empty"))
        return f"{icon} {format_time_label(minutes)}" if minutes is not None else f"{icon} use"

    return f"{icon} {stable_label(device, percent)}"


def title_for(device):
    return (
        device.get("model")
        or device.get("native-path")
        or device.get("type", "").title()
        or device.get("path", "").rsplit("/", 1)[-1]
    )


def tooltip_for(device, percent):
    state = device.get("state", "unknown")
    lines = [title_for(device)]

    if device.get("native-path") and device.get("native-path") != lines[0]:
        lines.append(f"Device: {device.get('native-path')}")
    if device.get("type"):
        lines.append(f"Type: {device.get('type')}")
    if percent is not None:
        lines.append(f"Charge: {format_percent(percent)}%")
    if device.get("battery-level"):
        lines.append(f"Battery level: {device.get('battery-level')}")
    if state:
        lines.append(f"State: {state}")
    if device.get("time to full"):
        lines.append(f"Time to full: {device.get('time to full')}")
    if device.get("time to empty"):
        lines.append(f"Time to empty: {device.get('time to empty')}")

    watts = parse_watts(device.get("energy-rate"))
    if watts not in (None, 0) and (
        has_active_charge(device) or has_active_discharge(device)
    ):
        lines.append(f"Energy rate: {device.get('energy-rate')}")

    return "\n".join(lines)


def format_device(device):
    if not is_battery_device(device):
        return None

    percent = percent_for(device)
    if percent is None:
        return None

    laptop = is_laptop(device)
    return {
        "kind": "laptop" if laptop else "device",
        "text": laptop_text(device, percent) if laptop else battery_icon(percent, has_active_charge(device)),
        "tooltip": tooltip_for(device, percent),
        "class": class_for(device, percent),
    }


def format_devices(text):
    devices = []
    for block in split_devices(text):
        formatted = format_device(parse_device(block))
        if formatted:
            devices.append(formatted)

    return sorted(devices, key=lambda device: 0 if device["kind"] == "laptop" else 1)


def read_upower():
    result = subprocess.run(
        ["upower", "-d"],
        check=False,
        capture_output=True,
        text=True,
        timeout=1.5,
    )
    return result.stdout if result.returncode == 0 else ""


def read_battery_devices():
    return format_devices(read_upower())


def main():
    print(json.dumps(read_battery_devices(), ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
