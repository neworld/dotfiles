#!/bin/sh

if [[ -z "${_STARTUP_IS_DONE}" ]]; then
    exit 0
fi

parcellite &

setxkbmap -option terminate:ctrl_alt_bksp
xset r rate 200 30

nm-applet &
#pasystray &
solaar &
#imwheel -b 45 -k
udiskie --tray &
lxsession &
synergy &


export _STARTUP_IS_DONE="done"
