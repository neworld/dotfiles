#!/bin/sh

if [[ $(nmcli con | grep -i tun) ]]; then
	echo "on"
else
	echo "off"
fi

