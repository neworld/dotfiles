source .env

#
# ~/.bashrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

alias ls='ls --color=auto'
PS1='[\u@\h \W]\$ '
[ -r /home/neworld/.byobu/prompt ] && . /home/neworld/.byobu/prompt   #byobu-prompt#

