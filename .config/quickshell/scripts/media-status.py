#!/usr/bin/env python3
import json
import subprocess
import sys


PLAYER_ICONS = {
    "spotify": "",
    "vlc": "󰕼",
    "chromium": "",
    "google-chrome": "",
    "firefox": "",
    "mpv": "",
}

def run(args):
    return subprocess.run(
        args,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    ).stdout.strip()


def player_icon(player):
    normalized = player.lower()
    for key, icon in PLAYER_ICONS.items():
        if key in normalized:
            return icon
    return ""


def metadata(player, field):
    return run(["playerctl", "-p", player, "metadata", "-f", "{{ " + field + " }}"])


def main():
    players = [line for line in run(["playerctl", "-l"]).splitlines() if line]
    if not players:
        return 0

    selected = players[0]
    selected_status = "Stopped"

    for player in players:
        status = run(["playerctl", "-p", player, "status"])
        if status == "Playing":
            selected = player
            selected_status = status
            break
        if player == selected:
            selected_status = status or selected_status

    title = metadata(selected, "title") or metadata(selected, "xesam:title")
    artist = metadata(selected, "artist") or metadata(selected, "xesam:artist")
    player_name = metadata(selected, "playerName") or selected.split(".")[0]

    if not title:
        title = player_name

    tooltip_parts = [player_name]
    if artist and artist != title:
        tooltip_parts.append(f"{artist} - {title}")
    else:
        tooltip_parts.append(title)

    print(json.dumps({
        "player": selected,
        "playerName": player_name,
        "icon": player_icon(selected),
        "title": title,
        "artist": artist,
        "status": selected_status,
        "tooltip": "\n".join(tooltip_parts),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
