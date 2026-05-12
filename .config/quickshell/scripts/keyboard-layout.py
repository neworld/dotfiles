#!/usr/bin/env python3
import json
import subprocess
import sys


FLAGS = {
    "us": "🇺🇸",
    "lt": "🇱🇹",
    "gb": "🇬🇧",
    "uk": "🇬🇧",
    "de": "🇩🇪",
    "fr": "🇫🇷",
    "es": "🇪🇸",
    "pl": "🇵🇱",
    "ru": "🇷🇺",
}


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    try:
        result = subprocess.run(
            ["hyprctl", "devices", "-j"],
            check=False,
            capture_output=True,
            text=True,
            timeout=1.0,
        )
    except Exception:
        return 1

    if result.returncode != 0:
        return 1

    try:
        devices = json.loads(result.stdout)
    except json.JSONDecodeError:
        return 1

    keyboards = devices.get("keyboards", [])
    keyboard = next((item for item in keyboards if item.get("main")), None)
    if keyboard is None and keyboards:
        keyboard = keyboards[0]
    if keyboard is None:
        return 1

    if action == "next":
        name = keyboard.get("name", "")
        if not name:
            return 1
        subprocess.run(
            ["hyprctl", "switchxkblayout", name, "next"],
            check=False,
            capture_output=True,
            text=True,
            timeout=1.0,
        )
        return 0

    layouts = [layout.strip() for layout in keyboard.get("layout", "").split(",")]
    index = keyboard.get("active_layout_index", 0)
    layout = layouts[index] if 0 <= index < len(layouts) else ""
    keymap = keyboard.get("active_keymap", "")
    flag = FLAGS.get(layout.lower(), "⌨")

    print(
        json.dumps(
            {
                "text": flag,
                "tooltip": f"Keyboard: {keymap}" if keymap else "Keyboard layout",
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
