#!/bin/sh

DMENU='dmenu -i -p >>> -nb #000 -nf #fff -sb #00BF32 -sf #fff'

layouts=$(ls $HOME/bin/screen_layouts)

choice=$(echo -e "$layouts" | $DMENU)

/bin/bash "$HOME/bin/screen_layouts/$choice"
