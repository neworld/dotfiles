local vars    = require("variables")
local bin_dir = vars.bin_dir

-- Set programs that you use
local terminal    = "alacritty"
local fileManager = "dolphin"
local menu        = "rofi -show drun"

-- Main one

hl.bind("SUPER + return", hl.dsp.exec_cmd(terminal))
hl.bind("SUPER + Q",      hl.dsp.window.close())
hl.bind("SUPER + slash",  hl.dsp.window.float({ action = "toggle" }))
hl.bind("SUPER + R",      hl.dsp.exec_cmd(menu))
hl.bind("SUPER + F",      hl.dsp.exec_cmd(fileManager))
hl.bind("SUPER + M",      hl.dsp.exit())
hl.bind("SUPER + L",      hl.dsp.exec_cmd("hyprlock"))
hl.bind("SUPER + P",      hl.dsp.exec_cmd("wlogout"))

-- Clipboard
hl.bind("SUPER + Tab", hl.dsp.exec_cmd("cliphist list | rofi -dmenu -display-columns 2 | cliphist decode | wl-copy"))
-- workaround for terminal to use SUPER + C to kill programs
-- hl.bind("SUPER + C", hl.dsp.exec_cmd("wtype -M ctrl c -m ctrl"))

-- Utilities

hl.bind("SUPER + Z", hl.dsp.exec_cmd("rofi -show calc -modi calc -no-show-match -no-sort"))
hl.bind("SUPER + X", hl.dsp.exec_cmd("rofi -modi emoji -show emoji"))
hl.bind("SUPER + 3", hl.dsp.exec_cmd("XDG_CURRENT_DESKTOP=sway flameshot gui"))

-- Screenshot

hl.bind("SUPER + 1",         hl.dsp.exec_cmd([[grim -g "$(slurp -d)" - | wl-copy]]))
hl.bind("SUPER + SHIFT + 1", hl.dsp.exec_cmd([[grim -o "$(hyprctl activeworkspace -j | jq -r '.monitor')" - | wl-copy]]))
hl.bind("SUPER + 2",         hl.dsp.exec_cmd(bin_dir .. "/screenshot-to-file.sh region"))
hl.bind("SUPER + SHIFT + 2", hl.dsp.exec_cmd(bin_dir .. "/screenshot-to-file.sh monitor"))

-- Scroll through existing workspaces with mainMod + scroll
hl.bind("SUPER + mouse_down", hl.dsp.focus({ workspace = "e+1" }))
hl.bind("SUPER + mouse_up",   hl.dsp.focus({ workspace = "e-1" }))

-- Move/resize windows with mainMod + LMB/RMB and dragging
hl.bind("SUPER + mouse:272", hl.dsp.window.drag(),   { mouse = true })
hl.bind("SUPER + mouse:273", hl.dsp.window.resize(), { mouse = true })

-- Laptop multimedia keys for volume and LCD brightness
hl.bind("XF86AudioRaiseVolume",  hl.dsp.exec_cmd("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+"), { repeating = true, locked = true })
hl.bind("XF86AudioLowerVolume",  hl.dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"),      { repeating = true, locked = true })
hl.bind("XF86AudioMute",         hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"),     { repeating = true, locked = true })
hl.bind("XF86AudioMicMute",      hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"),   { repeating = true, locked = true })
hl.bind("XF86MonBrightnessUp",   hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%+"),                  { repeating = true, locked = true })
hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%-"),                  { repeating = true, locked = true })

-- Requires playerctl
hl.bind("XF86AudioNext",  hl.dsp.exec_cmd("playerctl next"),       { locked = true })
hl.bind("XF86AudioPause", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPlay",  hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPrev",  hl.dsp.exec_cmd("playerctl previous"),   { locked = true })

-- Workspace management

hl.bind("SUPER + Backspace",         hl.dsp.focus({ monitor = "+1" }))
hl.bind("SUPER + left",              hl.dsp.exec_cmd(bin_dir .. "/switch_workspace.sh left"))
hl.bind("SUPER + right",             hl.dsp.exec_cmd(bin_dir .. "/switch_workspace.sh right"))
hl.bind("SUPER + SHIFT + left",      hl.dsp.exec_cmd(bin_dir .. "/move_window_to_workspace.sh left"))
hl.bind("SUPER + SHIFT + right",     hl.dsp.exec_cmd(bin_dir .. "/move_window_to_workspace.sh right"))
hl.bind("SUPER + grave",             hl.dsp.exec_cmd(bin_dir .. "/toggle-terminal.sh"))
hl.bind("SUPER + CTRL + Backspace",  hl.dsp.workspace.swap_monitors({ monitor1 = "current", monitor2 = "+1" }))
hl.bind("SUPER + SHIFT + Backspace", hl.dsp.window.move({ monitor = "+1", follow = true }))
hl.bind("ALT + Tab",                 hl.dsp.window.cycle_next())

hl.bind("SUPER + A", hl.dsp.focus({ direction = "left" }))
hl.bind("SUPER + W", hl.dsp.focus({ direction = "up" }))
hl.bind("SUPER + D", hl.dsp.focus({ direction = "right" }))
hl.bind("SUPER + S", hl.dsp.focus({ direction = "down" }))

hl.bind("SUPER + CTRL + A", hl.dsp.window.swap({ direction = "left" }))
hl.bind("SUPER + CTRL + W", hl.dsp.window.swap({ direction = "up" }))
hl.bind("SUPER + CTRL + D", hl.dsp.window.swap({ direction = "right" }))
hl.bind("SUPER + CTRL + S", hl.dsp.window.swap({ direction = "down" }))

hl.bind("SUPER + SHIFT + A", hl.dsp.window.move({ direction = "left" }))
hl.bind("SUPER + SHIFT + W", hl.dsp.window.move({ direction = "up" }))
hl.bind("SUPER + SHIFT + D", hl.dsp.window.move({ direction = "right" }))
hl.bind("SUPER + SHIFT + S", hl.dsp.window.move({ direction = "down" }))

-- Switch to a submap called `resize`.
hl.bind("SUPER + E", hl.dsp.submap("resize"))

-- Start a submap called "resize".
hl.define_submap("resize", function()
    local function resize(x, y)
        return hl.dsp.window.resize({ x = x, y = y, relative = true })
    end

    -- Set repeatable binds for resizing the active window.
    hl.bind("right", resize(20, 0),  { repeating = true })
    hl.bind("left",  resize(-20, 0), { repeating = true })
    hl.bind("up",    resize(0, -20), { repeating = true })
    hl.bind("down",  resize(0, 20),  { repeating = true })

    hl.bind("d", resize(20, 0),  { repeating = true })
    hl.bind("a", resize(-20, 0), { repeating = true })
    hl.bind("w", resize(0, -20), { repeating = true })
    hl.bind("s", resize(0, 20),  { repeating = true })

    -- Use `reset` to go back to the global submap
    hl.bind("escape", hl.dsp.submap("reset"))
end)
