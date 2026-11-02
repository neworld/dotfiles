-- Shared values for the Lua config. Use with: local vars = require("variables")
-- Note: hypridle and hyprlock don't read Lua, they still use variables.conf.

local home = os.getenv("HOME")

local vars = {
    theme_dir = home .. "/.config/themes/current",
    bin_dir   = home .. "/.config/hypr/bin",
}

-- Per-machine overrides (gitignored). variables_custom.lua should return a table,
-- e.g. return { bin_dir = "..." }
for k, v in pairs(optional_require("variables_custom") or {}) do
    vars[k] = v
end

return vars
