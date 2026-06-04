#!/usr/bin/env sh
set -eu

screens_dir="${HOME}/screens"
mkdir -p "$screens_dir"

file="${screens_dir}/$(date +'%s_grim.png')"
mode="${1:-region}"

case "$mode" in
  region)
    geometry="$(slurp -d)" || exit 0
    grim -g "$geometry" "$file"
    ;;
  monitor)
    monitor="$(hyprctl activeworkspace -j | jq -r '.monitor')"
    grim -o "$monitor" "$file"
    ;;
  *)
    printf 'usage: %s [region|monitor]\n' "$0" >&2
    exit 2
    ;;
esac

printf '%s' "$file" | wl-copy

if command -v notify-send >/dev/null 2>&1; then
  notify-send 'Screenshot saved' "$file"
fi
