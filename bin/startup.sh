#!/bin/sh

parcellite &

setxkbmap -option terminate:ctrl_alt_bksp
xset r rate 200 30

nm-applet &
#pasystray &
solaar -w hide &
#imwheel -b 45 -k
udiskie --tray &
lxsession &
/opt/Synergy/synergy &
optimus-manager-qt &
screendimmer &
/usr/bin/numlockx on 

