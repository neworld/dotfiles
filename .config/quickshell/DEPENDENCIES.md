# Quickshell — Dependencies

Everything this Quickshell config (the top bar + its scripts) needs to work.
Package names are Arch/`pacman`; one is from the AUR (`yay`). Most are likely
already installed — `--needed` makes re-running harmless.

## Install (official repositories)

```sh
sudo pacman -S --needed \
  quickshell \
  whisper-cpp-vulkan wtype libpulse \
  wireplumber playerctl upower lm_sensors ddcutil \
  hyprland curl python xdg-utils util-linux networkmanager \
  alacritty pavucontrol blueman wlogout btop \
  ttf-jetbrains-mono-nerd noto-fonts noto-fonts-emoji otf-font-awesome
```

## Install (AUR)

```sh
yay -S whisper.cpp-model-small        # speech-to-text model for dictation
```

## Optional

```sh
sudo pacman -S --needed power-profiles-daemon   # adds power-profile to the metrics widget
# nvidia-utils                                    # only for NVIDIA GPU metrics; not needed on Intel Arc
```

---

## What each package powers

### Core
| Package | Used for |
|---|---|
| `quickshell` | the bar itself (pulls in Qt 6) |
| `hyprland` | `hyprctl` — workspaces, keyboard-layout widget, dictation window focus |
| `python` | the `scripts/*.py` widgets and `dictate.py` |

### Dictation (mic widget — `DictationWidget.qml` + `scripts/dictate.py`)
| Package | Used for |
|---|---|
| `whisper-cpp-vulkan` | `whisper-server` / `whisper-cli` — speech-to-text, Vulkan-accelerated on the Intel Arc iGPU |
| `whisper.cpp-model-small` (AUR) | the model file; `dictate.py` auto-detects it under `/usr/share/whisper.cpp-model-*/` |
| `libpulse` | `parec` — microphone capture |
| `wtype` | types the transcript into the focused window |
| `curl` | talks to the local `whisper-server` |

### Bar widgets / indicators
| Package | Widget |
|---|---|
| `wireplumber` | `wpctl` — volume indicator |
| `playerctl` | media / now-playing widget |
| `upower` | battery devices |
| `lm_sensors` | CPU temperatures (metrics) |
| `ddcutil` | external-monitor brightness (Displays widget) |
| `networkmanager` | `nmcli` — Wi-Fi/ethernet indicator |
| `util-linux` | `rfkill` — Bluetooth indicator |

### Apps opened on click
| Package | Opened by |
|---|---|
| `alacritty` | terminal (scratchpad, right-click actions) |
| `pavucontrol` | volume widget click |
| `blueman` | `blueman-manager` — Bluetooth click |
| `wlogout` | power menu |
| `xdg-utils` | `xdg-open` — open URLs (e.g. Codex usage) |
| `btop` | system monitor (metrics click) |

### Fonts
| Package | Provides |
|---|---|
| `ttf-jetbrains-mono-nerd` | Nerd Font glyphs (mic, battery, Wi-Fi, volume…) + mono text |
| `noto-fonts` | Noto Sans Mono (bar text) |
| `noto-fonts-emoji` | Noto Color Emoji (keyboard-layout flags) |
| `otf-font-awesome` | Font Awesome 7 Brands (brand glyph) |

### Omarchy helpers (not a package)
Several click actions call `omarchy-*` scripts and `$OMARCHY_PATH/...`:
`omarchy-menu`, `omarchy-cmd-screenrecord`, `omarchy-launch-wifi`,
`omarchy-launch-or-focus-tui`, `omarchy-launch-floating-terminal-with-presentation`,
and the screen-recording indicator. These come from the Omarchy setup itself —
install Omarchy to get them. Without it the bar still renders; only those specific
clicks/indicators are inert.

---

## Dictation tunables (env vars, optional)

| Variable | Default | Effect |
|---|---|---|
| `DICTATE_MODEL` | auto-detected | absolute path to a `ggml-*.bin` to force a specific model |
| `DICTATE_LANG` | follows keyboard layout (`us`→`en`, `lt`→`lt`) | force a language code, or `auto` for whisper auto-detect |
| `DICTATE_STEP_MS` | `50` | idle poll interval while waiting for new audio |
| `DICTATE_PORT` | `8910` | local `whisper-server` port |
