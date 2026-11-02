-- https://wiki.hypr.land/configuring/
--
-- Files are loaded with require(), relative to ~/.config/hypr
-- (e.g. require("default.bindings") loads default/bindings.lua).

-- Load a module only if the file exists. Used for per-machine files
-- that are gitignored (monitors.lua, variables_custom.lua).
function optional_require(name)
    if package.searchpath(name, package.path) then
        return require(name)
    end
end

hl.config({
    debug = {
        disable_logs = false,
    },
})

-- See https://wiki.hypr.land/configuring/core/monitors/
hl.monitor({ output = "", mode = "preferred", position = "auto", scale = 1 })

---- HDPI ----

hl.config({
    xwayland = {
        force_zero_scaling = true,
    },
})

hl.env("GDK_SCALE", "2")
hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")

-- Force all apps to use Wayland
hl.env("GDK_BACKEND", "wayland,x11,*")
hl.env("QT_QPA_PLATFORM", "wayland;xcb")
hl.env("QT_STYLE_OVERRIDE", "kvantum")
hl.env("SDL_VIDEODRIVER", "wayland")
hl.env("MOZ_ENABLE_WAYLAND", "1")
hl.env("ELECTRON_OZONE_PLATFORM_HINT", "wayland")
hl.env("OZONE_PLATFORM", "wayland")
hl.env("XDG_SESSION_TYPE", "wayland")

-- Allow better support for screen sharing (Google Meet, Discord, etc)
hl.env("XDG_CURRENT_DESKTOP", "Hyprland")
hl.env("XDG_SESSION_DESKTOP", "Hyprland")

-- Per-machine monitor setup (gitignored)
optional_require("monitors")

require("default.looknfeel")
require("default.bindings")
require("input")
require("autostart")
require("bindings")


---------------------
---- PERMISSIONS ----
---------------------

-- See https://wiki.hypr.land/configuring/core/advanced-configuration/permissions/
-- Please note permission changes here require a Hyprland restart and are not applied on-the-fly
-- for security reasons

-- hl.config({
--   ecosystem = {
--     enforce_permissions = true,
--   },
-- })

-- hl.permission("/usr/(bin|local/bin)/grim", "screencopy", "allow")
-- hl.permission("/usr/(lib|libexec|lib64)/xdg-desktop-portal-hyprland", "screencopy", "allow")
-- hl.permission("/usr/(bin|local/bin)/hyprpm", "plugin", "allow")


--------------------------------
---- WINDOWS AND WORKSPACES ----
--------------------------------

-- See https://wiki.hypr.land/configuring/core/rules/

hl.window_rule({
    -- Ignore maximize requests from all apps. You'll probably like this.
    name  = "suppress-maximize-events",
    match = { class = ".*" },

    suppress_event = "maximize",
})

hl.window_rule({
    -- Fix some dragging issues with XWayland
    name  = "fix-xwayland-drags",
    match = {
        class      = "^$",
        title      = "^$",
        xwayland   = true,
        float      = true,
        fullscreen = false,
        pin        = false,
    },

    no_focus = true,
})

-- Hyprland-run windowrule
hl.window_rule({
    name  = "move-hyprland-run",
    match = { class = "hyprland-run" },

    move  = "20 monitor_h-120",
    float = true,
})

-- Setup scratchpad
hl.workspace_rule({
    workspace        = "special:terminal",
    on_created_empty = "alacritty --class scratchpad_terminal -e zsh -c byobu",
})

hl.window_rule({
    name  = "Scratchpad terminal",
    match = { class = "^scratchpad_terminal$" },

    -- Don't pop the scratchpad open when the terminal requests activation
    -- (e.g. a bell from Claude in byobu); focus_on_activate is on globally.
    suppress_event = "activatefocus",
    float = true,
    size  = { "monitor_w-20", "monitor_h*0.7" },
    move  = { 10, 35 },
})

-- Flameshot hacks
hl.window_rule({
    name  = "flameshot",
    match = { title = "flameshot" },

    float          = true,
    move           = { 0, 0 },
    suppress_event = "fullscreen",
})
