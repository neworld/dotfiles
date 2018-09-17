#!/bin/bash
#
# a simple dmenu session script 
# inspired from https://bbs.archlinux.org/viewtopic.php?id=95984
# by zordsdavini, 2015
#
###

DMENU='dmenu -i -p >>> -nb #000 -nf #fff -sb #00BF32 -sf #fff'
choice=$(echo -e "logout\nshutdown\nreboot\nsuspend\nhibernate" | $DMENU)

case "$choice" in
  logout) sudo kill $(pgrep X) & ;;
  shutdown) /usr/bin/systemctl -i poweroff ;;
  reboot) /usr/bin/systemctl -i reboot ;;
  suspend) /usr/bin/systemctl -i suspend ;;
  hibernate) /usr/bin/systemctl -i hibernate ;;
esac