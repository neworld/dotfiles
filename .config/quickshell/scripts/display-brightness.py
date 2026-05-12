#!/usr/bin/env python3
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


BACKLIGHT_DIR = Path("/sys/class/backlight")
CACHE_DIR = Path(tempfile.gettempdir()) / "quickshell-display-brightness"


def clamp(value, low=0, high=100):
    return max(low, min(high, value))


def is_laptop_output(name):
    lowered = (name or "").lower()
    return lowered.startswith("edp") or lowered.startswith("lvds")


def backlight_device():
    if not BACKLIGHT_DIR.exists():
        return None

    devices = sorted(path for path in BACKLIGHT_DIR.iterdir() if path.is_dir())
    return devices[0] if devices else None


def read_backlight():
    device = backlight_device()
    if device is None:
        return None

    try:
        current = int((device / "brightness").read_text().strip())
        maximum = int((device / "max_brightness").read_text().strip())
    except (OSError, ValueError):
        return None

    if maximum <= 0:
        return None

    return {
        "kind": "backlight",
        "selector": str(device),
        "current": round((current / maximum) * 100),
        "raw_current": current,
        "raw_max": maximum,
    }


def set_backlight(percent):
    device = backlight_device()
    if device is None:
        return False

    try:
        maximum = int((device / "max_brightness").read_text().strip())
        target = round((clamp(percent) / 100) * maximum)
        (device / "brightness").write_text(str(target))
        return True
    except (OSError, ValueError):
        return False


def ddc_selector(args):
    selector = []
    if args.serial:
        selector.extend(["--sn", args.serial])
    elif args.model:
        selector.extend(["--model", args.model])
    return selector


def cache_key(args):
    key = args.serial or args.model or args.name or "display"
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", key)


def read_cache(args):
    try:
        return int((CACHE_DIR / cache_key(args)).read_text().strip())
    except (OSError, ValueError):
        return None


def write_cache(args, value):
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        (CACHE_DIR / cache_key(args)).write_text(str(clamp(value)))
    except OSError:
        pass


def run_ddc(args, command):
    if not shutil.which("ddcutil"):
        return None

    try:
        result = subprocess.run(
            [
                "ddcutil",
                "--noverify",
                "--sleep-multiplier",
                "0.1",
                "--disable-dynamic-sleep",
                *ddc_selector(args),
                *command,
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=3.0,
        )
    except Exception:
        return None

    if result.returncode != 0:
        return None
    return result.stdout


def read_ddc(args):
    text = run_ddc(args, ["getvcp", "10"])
    if not text:
        return None

    match = re.search(r"current value\s*=\s*(\d+).*?max value\s*=\s*(\d+)", text, re.I | re.S)
    if match:
        current = int(match.group(1))
        maximum = int(match.group(2))
    else:
        numbers = [int(value) for value in re.findall(r"\b\d+\b", text)]
        if len(numbers) < 2:
            return None
        current = numbers[-2]
        maximum = numbers[-1]

    if maximum <= 0:
        return None

    return {
        "kind": "ddc",
        "selector": " ".join(ddc_selector(args)) or "default display",
        "current": round((current / maximum) * 100),
        "raw_current": current,
        "raw_max": maximum,
    }


def set_ddc(args, percent):
    value = clamp(percent)
    return run_ddc(args, ["setvcp", "10", str(value)]) is not None


def change_ddc(args, delta):
    direction = "+" if delta > 0 else "-"
    amount = str(abs(delta))
    return run_ddc(args, ["setvcp", "10", direction, amount]) is not None


def read_brightness(args):
    if is_laptop_output(args.name):
        return read_backlight()
    return read_ddc(args) or read_backlight()


def set_brightness(args, percent):
    if is_laptop_output(args.name):
        return set_backlight(percent)
    return set_ddc(args, percent) or set_backlight(percent)


def output_status(args):
    brightness = read_backlight() if is_laptop_output(args.name) else None
    cached = read_cache(args)
    display_name = args.description or args.model or args.name or "Display"

    if brightness is None:
        if cached is not None:
            payload = {
                "available": True,
                "text": f"{cached}%",
                "tooltip": f"{display_name}\nBrightness: {cached}%",
            }
            print(json.dumps(payload), flush=True)
            return

        payload = {
            "available": False,
            "text": "",
            "tooltip": f"{display_name}\nBrightness: unknown",
        }
    else:
        payload = {
            "available": True,
            "text": f"{brightness['current']}%",
            "tooltip": f"{display_name}\nBrightness: {brightness['current']}%",
        }

    print(json.dumps(payload), flush=True)


def change_brightness(args):
    if is_laptop_output(args.name):
        brightness = read_backlight()
        if brightness is None:
            output_status(args)
            return 1

        target = clamp(brightness["current"] + args.delta)
        set_brightness(args, target)
        write_cache(args, target)
        output_status(args)
        return 0

    cached = read_cache(args)
    if cached is None:
        cached = 50

    target = clamp(cached + args.delta)
    if set_ddc(args, target) or change_ddc(args, args.delta):
        write_cache(args, target)
    output_status(args)
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["status", "change"])
    parser.add_argument("--name", default="")
    parser.add_argument("--model", default="")
    parser.add_argument("--serial", default="")
    parser.add_argument("--description", default="")
    parser.add_argument("--delta", type=int, default=0)
    args = parser.parse_args()

    if args.action == "change":
        return change_brightness(args)

    output_status(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
