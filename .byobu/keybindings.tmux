unbind-key -n C-a
#set -g prefix ^A
#set -g prefix2 F12
#bind a send-prefixi

bind-key -n M-Left previous-window
bind-key -n M-right next-window
bind-key -n M-t new-window
bind-key -n M-Down new-window
unbind-key -n F1
unbind-key -n F2
unbind-key -n F3
unbind-key -n F4
unbind-key -n F5
unbind-key -n F6
unbind-key -n F7
unbind-key -n F8
unbind-key -n F9
unbind-key -n F10
unbind-key -n F11
unbind-key -n F12

unbind-key -n M-F5
bind-key -n M-F5 source $BYOBU_PREFIX/share/byobu/profiles/tmuxrc
