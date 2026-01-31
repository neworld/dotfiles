#!/usr/bin/env bash

# ──────────────────────────────────────────────
# CONFIG
SPECIAL_NAME="terminal"         # change if named; use "" for unnamed
# ──────────────────────────────────────────────

if [ -z "$SPECIAL_NAME" ]; then
    TOGGLE_CMD="togglespecialworkspace"
    WS_ARG=""
else
    TOGGLE_CMD="togglespecialworkspace $SPECIAL_NAME"
    WS_ARG="special:$SPECIAL_NAME"
fi

# Get currently focused monitor index
# current_mon_idx=$(hyprctl monitors -j | jq -r '.[] | select(.focused == true) | .id')

# if [ "$current_mon_idx" = "0" ]; then
#     # Already on first monitor → just toggle
#     hyprctl dispatch "$TOGGLE_CMD"
#     exit 0
# fi

# Disable cursor warping during switches (cleaner animation)
# hyprctl keyword cursor:no_warps 1 >/dev/null

hyprctl dispatch focusmonitor 0
hyprctl dispatch $TOGGLE_CMD

# hyprctl keyword cursor:no_warps 0 >/dev/null