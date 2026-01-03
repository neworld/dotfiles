#!/bin/bash

direction="$1"

if [[ ! "$direction" == "left" && ! "$direction" == "right" ]]; then
    echo "Usage: $0 left|right"
    exit 1
fi


# Get current workspace ID
current=$(hyprctl activeworkspace -j | jq '.id')

occupied=$(hyprctl monitors -j | jq '[.[] .activeWorkspace.id]')

if [[ "$direction" == "right" ]]; then
    target=$((current + 1))
    while true; do
        if ! jq -e --argjson t "$target" 'index($t) != null' <<< "$occupied" > /dev/null; then
            break
        fi
        target=$((target + 1))
    done
    hyprctl dispatch workspace "$target"
elif [[ "$direction" == "left" ]]; then
    target=$((current - 1))
    while [[ $target -ge 1 ]]; do
        if ! jq -e --argjson t "$target" 'index($t) != null' <<< "$occupied" > /dev/null; then
            hyprctl dispatch workspace "$target"
            exit 0
        fi
        target=$((target - 1))
    done
    # If no free workspace to the left, do nothing
fi

