# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from libqtile.config import Key, Screen, Group, Drag, Click, DropDown, ScratchPad, Match
from libqtile.command import lazy
from libqtile import layout, bar, widget, extension, hook
from libqtile.log_utils import logger
import re
import subprocess
import os

mod = "mod4"
shift = "shift"
ctrl = "control"
alt = "mod1"

workspaces = [
        ('1', 'F1'),
        ('2', 'F2'),
        ('3', 'F3'),
        ('4', 'F4'),
]

def spawn_bin(program):
    @lazy.function
    def __inner(qtile):
        full_path = os.path.expanduser('~/bin/' + program)
        qtile.cmd_spawn(full_path)

    return __inner

def window_to_prev_group():
    @lazy.function
    def __inner(qtile):
        if qtile.currentWindow is not None:
            index = qtile.groups.index(qtile.currentGroup)
            if index > 0:
                qtile.currentWindow.togroup(qtile.groups[index - 1].name)
            else:
                qtile.currentWindow.togroup(qtile.groups[len(qtile.groups) - 2].name)

    return __inner

def window_to_next_group():
    @lazy.function
    def __inner(qtile):
        if qtile.currentWindow is not None:
            index = qtile.groups.index(qtile.currentGroup)
            if index < len(qtile.groups) - 2:
                qtile.currentWindow.togroup(qtile.groups[index + 1].name)
            else:
                qtile.currentWindow.togroup(qtile.groups[0].name)

    return __inner

def window_to_prev_screen():
    @lazy.function
    def __inner(qtile):
        if qtile.currentWindow is not None:
            index = qtile.screens.index(qtile.currentScreen)
            if index > 0:
                qtile.currentWindow.togroup(qtile.screens[index - 1].group.name)
            else:
                qtile.currentWindow.togroup(qtile.screens[len(qtile.screens) - 1].group.name)

    return __inner


def window_to_next_screen():
    @lazy.function
    def __inner(qtile):
        if qtile.currentWindow is not None:
            index = qtile.screens.index(qtile.currentScreen)
            if index < len(qtile.screens) - 1:
                qtile.currentWindow.togroup(qtile.screens[index + 1].group.name)
            else:
                qtile.currentWindow.togroup(qtile.screens[0].group.name)

    return __inner

def switch_language():

    kb_layout_regex = re.compile('layout:\s+(?P<layout>\w+)')
    layouts = ['us', 'lt']

    @lazy.function
    def __inner(qtile):
        command = 'setxkbmap -verbose 10' 
        output = subprocess.check_output(command.split(' ')).decode()

        match_layout = kb_layout_regex.search(output)
        kb = match_layout.group('layout')

        next_keyboard = layouts[(layouts.index(kb) + 1) % len(layouts)]

        subprocess.check_output(['setxkbmap', next_keyboard])

    return __inner


class Commands(object):
    volume_up = 'amixer -q -c 0 sset Master 3dB+'
    volume_down = 'amixer -q -c 0 sset Master 3dB-'
    volume_toggle = 'amixer -q set Master toggle'

keys = [
    Key([mod], "space", lazy.next_layout()),

    Key([mod], "Return", lazy.spawn("urxvt")),

    Key([mod], "w", lazy.window.kill()),

    Key([mod, "control"], "r", lazy.restart()),
    Key([mod, "control"], "q", lazy.shutdown()),
    Key([mod], "r", lazy.spawncmd()),

    Key([mod], "Right", lazy.screen.next_group()),
    Key([mod], "Left", lazy.screen.prev_group()),
    Key([mod, shift], "Right", window_to_next_group()),
    Key([mod, shift], "Left", window_to_prev_group()),

    Key([mod], "period", lazy.layout.grow_main()),
    Key([mod], "comma", lazy.layout.shrink_main()),
    Key([mod], "slash", lazy.window.toggle_fullscreen()),
    Key([mod, ctrl], "space", lazy.layout.swap_main()),

    Key([alt], "Tab", lazy.layout.next()),
    Key([alt, shift], "Tab", lazy.layout.prev()),
    
    Key([mod], "l", lazy.spawn("dm-tool lock")),

    Key([mod], "grave", lazy.group['scratchpad'].dropdown_toggle('term')),

    Key([], 'XF86AudioRaiseVolume', lazy.spawn(Commands.volume_up)),
    Key([], 'XF86AudioLowerVolume', lazy.spawn(Commands.volume_down)),
    Key([], 'XF86AudioMute', lazy.spawn(Commands.volume_toggle)),
    Key([], 'XF86AudioNext', lazy.spawn("playerctl next")),
    Key([], 'XF86AudioPrev', lazy.spawn("playerctl previous")),
    Key([], 'XF86AudioPlay', lazy.spawn("playerctl play-pause")),
    Key([], 'XF86MonBrightnessUp', lazy.spawn("xbacklight -inc 10%")),
    Key([], 'XF86MonBrightnessDown', lazy.spawn("xbacklight -dec 10%")),

    Key([mod], 'Tab', lazy.run_extension(extension.WindowList(
        all_groups = True,
        dmenu_ignorecase = True,
    ))),

    Key([mod], 'z', switch_language()),
    
    Key([mod], '1', spawn_bin('screen_clip.sh')),
    Key([mod], '2', spawn_bin('screen_file.sh')),
    Key([mod, shift], '1', spawn_bin('screen_clip_full.sh')),
    Key([mod, shift], '2', spawn_bin('screen_file_full.sh')),
]

groups = [
        ScratchPad("scratchpad", [
            DropDown("term", "urxvt -e zsh -c byobu", opacity=0.8, width=1.0, x=0.0, height=0.6)
        ]),
]

for workspace, hotkey in workspaces:
    groups.append(Group(workspace))
    keys.append(Key([mod], hotkey, lazy.group[workspace].toscreen()))


group_www = "www"
group_android = "android"
group_chat = "chat"
group_music = "music"

groups.append(Group(group_www,
    matches=[Match(wm_class=["Google-chrome"])], 
    spawn="google-chrome-stable", 
    init=True, 
    layout="max",
    persist=False,
))

groups.append(Group(group_android,
    matches=[Match(wm_class=["jetbrains-studio"], title=["Android Emulator - "])], 
    layout="monadtall",
    persist=False,
))

groups.append(Group(group_chat,
    matches=[Match(wm_class=["Slack"])], 
    layout="max",
    persist=False,
))

groups.append(Group(group_music,
    matches=[Match(wm_class=["Spotify", "vlc"])], 
    layout="max",
    persist=False,
))

layouts = [
    layout.MonadTall(border_focus='#a54242'),
    layout.Max(),
]

widget_defaults = dict(
    font='DejaVu sans',
    fontsize=24,
    padding=3,
)

extension_defaults = widget_defaults.copy()

screens = [
    Screen(
        top=bar.Bar(
            [
                widget.GroupBox(),
                widget.Prompt(),
                widget.Spacer(length=16),
                widget.WindowName(),

                widget.KeyboardLayout(configured_keyboards=['us','lt']),
                widget.Backlight(
                    backlight_name = 'intel_backlight'    
                ),
                widget.Battery(),
                widget.CPUGraph(),
                widget.MemoryGraph(graph_color='85678f'),
                widget.NetGraph(graph_color='de935f'),
                widget.ThermalSensor(),
                widget.Wlan(),
                widget.Volume(),
                widget.YahooWeather(location='Vilnius'),
                widget.Systray(),
                widget.Spacer(length=16),
                widget.Clock(format='%Y-%m-%d %a %H:%M'),
                widget.CurrentLayoutIcon(),
            ],
            40,
        ),
    ),
]

# Drag floating layouts.
mouse = [
    Drag([mod], "Button1", lazy.window.set_position_floating(),
         start=lazy.window.get_position()),
    Drag([mod], "Button2", lazy.window.set_size_floating(),
         start=lazy.window.get_size()),
    Click([mod], "Button3", lazy.window.bring_to_front())
]

dgroups_key_binder = None
dgroups_app_rules = []  # type: List
main = None
follow_mouse_focus = False
bring_front_click = False
cursor_warp = False
floating_layout = layout.Floating(float_rules=[
    {'wmclass': 'confirm'},
    {'wmclass': 'dialog'},
    {'wmclass': 'download'},
    {'wmclass': 'error'},
    {'wmclass': 'file_progress'},
    {'wmclass': 'notification'},
    {'wmclass': 'splash'},
    {'wmclass': 'toolbar'},
    {'wmclass': 'confirmreset'},  # gitk
    {'wmclass': 'makebranch'},  # gitk
    {'wmclass': 'maketag'},  # gitk
    {'wname': 'branchdialog'},  # gitk
    {'wname': 'pinentry'},  # GPG key password entry
    {'wmclass': 'ssh-askpass'},  # ssh-askpasis
    {'wname': 'Android Virtual Device Manager'},
])
auto_fullscreen = True
focus_on_window_activation = "smart"

# XXX: Gasp! We're lying here. In fact, nobody really uses or cares about this
# string besides java UI toolkits; you can see several discussions on the
# mailing lists, github issues, and other WM documentation that suggest setting
# this string if your java app doesn't work correctly. We may as well just lie
# and say that we're a working one by default.
#
# We choose LG3D to maximize irony: it is a 3D non-reparenting WM written in
# java that happens to be on java's whitelist.
wmname = "LG3D"

@hook.subscribe.startup
def autostart():
    path = os.path.expanduser('~/bin/startup.sh')
    subprocess.call([path])

