local vars = require("variables")

hl.bind("SUPER + C", hl.dsp.exec_cmd(vars.bin_dir .. "/copy-date-time.sh"))
