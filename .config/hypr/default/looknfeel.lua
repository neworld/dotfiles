-- Refer to https://wiki.hypr.land/configuring/core/config-options/

-- In order to fully work, omarchy compatible theme must be linked to .config/themes/current

-- Variables
local activeBorderColor   = { colors = { "rgba(33ccffee)", "rgba(00ff99ee)" }, angle = 45 }
local inactiveBorderColor = "rgba(595959aa)"

hl.config({
    general = {
        gaps_in  = 5,
        gaps_out = 10,

        border_size = 2,

        col = {
            active_border   = activeBorderColor,
            inactive_border = inactiveBorderColor,
        },

        -- Set to true enable resizing windows by clicking and dragging on borders and gaps
        resize_on_border = false,

        -- Please see https://wiki.hypr.land/configuring/extra/tearing/ before you turn this on
        allow_tearing = false,

        layout = "dwindle",
    },

    decoration = {
        rounding = 0,

        shadow = {
            enabled      = true,
            range        = 2,
            render_power = 3,
            color        = "rgba(1a1a1aee)",
        },

        blur = {
            enabled    = true,
            size       = 2,
            passes     = 2,
            special    = false,
            brightness = 0.60,
            contrast   = 0.75,
        },
    },

    group = {
        col = {
            border_active          = activeBorderColor,
            border_inactive        = inactiveBorderColor,
            border_locked_active   = activeBorderColor,
            border_locked_inactive = inactiveBorderColor,
        },

        groupbar = {
            font_size            = 12,
            font_family          = "monospace",
            font_weight_active   = "ultraheavy",
            font_weight_inactive = "normal",

            indicator_height = 0,
            indicator_gap    = 5,
            height           = 22,
            gaps_in          = 5,
            gaps_out         = 0,

            text_color          = "rgb(ffffff)",
            text_color_inactive = "rgba(ffffff90)",
            col = {
                active   = "rgba(00000040)",
                inactive = "rgba(00000020)",
            },

            gradients                 = true,
            gradient_rounding         = 0,
            gradient_round_only_edges = false,
        },
    },

    animations = {
        enabled = true, -- yes, please :)
    },

    -- See https://wiki.hypr.land/configuring/layouts/dwindle-layout/ for more
    dwindle = {
        preserve_split = true, -- You probably want this
        force_split    = 2,    -- Always split on the right
    },

    -- See https://wiki.hypr.land/configuring/layouts/master-layout/ for more
    master = {
        new_status = "master",
    },

    misc = {
        disable_hyprland_logo     = true,
        disable_splash_rendering  = true,
        focus_on_activate         = true,
        anr_missed_pings          = 3,
        on_focus_under_fullscreen = 0,
        middle_click_paste        = false,
    },

    cursor = {
        hide_on_key_press = true,
    },

    input = {
        touchpad = {
            natural_scroll = true,
        },
    },
})

-- Animations, see https://wiki.hypr.land/configuring/core/animations/
hl.curve("easeOutQuint",   { type = "bezier", points = { {0.23, 1},    {0.32, 1}    } })
hl.curve("easeInOutCubic", { type = "bezier", points = { {0.65, 0.05}, {0.36, 1}    } })
hl.curve("linear",         { type = "bezier", points = { {0, 0},       {1, 1}       } })
hl.curve("almostLinear",   { type = "bezier", points = { {0.5, 0.5},   {0.75, 1.0}  } })
hl.curve("quick",          { type = "bezier", points = { {0.15, 0},    {0.1, 1}     } })

hl.animation({ leaf = "global",        enabled = true,  speed = 10,   bezier = "default" })
hl.animation({ leaf = "border",        enabled = true,  speed = 5.39, bezier = "easeOutQuint" })
hl.animation({ leaf = "windows",       enabled = true,  speed = 4.79, bezier = "easeOutQuint" })
hl.animation({ leaf = "windowsIn",     enabled = true,  speed = 4.1,  bezier = "easeOutQuint", style = "popin 87%" })
hl.animation({ leaf = "windowsOut",    enabled = true,  speed = 1.49, bezier = "linear",       style = "popin 87%" })
hl.animation({ leaf = "fadeIn",        enabled = true,  speed = 1.73, bezier = "almostLinear" })
hl.animation({ leaf = "fadeOut",       enabled = true,  speed = 1.46, bezier = "almostLinear" })
hl.animation({ leaf = "fade",          enabled = true,  speed = 3.03, bezier = "quick" })
hl.animation({ leaf = "layers",        enabled = true,  speed = 3.81, bezier = "easeOutQuint" })
hl.animation({ leaf = "layersIn",      enabled = true,  speed = 4,    bezier = "easeOutQuint", style = "fade" })
hl.animation({ leaf = "layersOut",     enabled = true,  speed = 1.5,  bezier = "linear",       style = "fade" })
hl.animation({ leaf = "fadeLayersIn",  enabled = true,  speed = 1.79, bezier = "almostLinear" })
hl.animation({ leaf = "fadeLayersOut", enabled = true,  speed = 1.39, bezier = "almostLinear" })
hl.animation({ leaf = "workspaces",    enabled = false })

-- Style Gum confirm to match terminal theme
hl.env("GUM_CONFIRM_PROMPT_FOREGROUND", "6")     -- Cyan
hl.env("GUM_CONFIRM_SELECTED_FOREGROUND", "0")   -- Black
hl.env("GUM_CONFIRM_SELECTED_BACKGROUND", "2")   -- Green
hl.env("GUM_CONFIRM_UNSELECTED_FOREGROUND", "0") -- Black
hl.env("GUM_CONFIRM_UNSELECTED_BACKGROUND", "8") -- Dark grey
