#!/usr/bin/env bash

# ──────────────────────────────────────────────
# CONFIG
SPECIAL_NAME="terminal"         # change if named; use "" for unnamed
# ──────────────────────────────────────────────

TOGGLE_CMD="hl.dsp.workspace.toggle_special(\"$SPECIAL_NAME\")"

# Get currently focused monitor index
# current_mon_idx=$(hyprctl monitors -j | jq -r '.[] | select(.focused == true) | .id')

# if [ "$current_mon_idx" = "0" ]; then
#     # Already on first monitor → just toggle
#     hyprctl dispatch "$TOGGLE_CMD"
#     exit 0
# fi

# Disable cursor warping during switches (cleaner animation)
# hyprctl keyword cursor:no_warps 1 >/dev/null

hyprctl dispatch 'hl.dsp.focus({ monitor = 0 })'
hyprctl dispatch "$TOGGLE_CMD"

# hyprctl keyword cursor:no_warps 0 >/dev/null