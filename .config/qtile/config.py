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
from libqtile.widget import base
import re
import subprocess
import os
from pprint import pprint, pformat

mod = "mod4"
shift = "shift"
ctrl = "control"
alt = "mod1"

color_green = "#568c3b"
color_red = '#d22d72'
color_yellow = '#8a8a0f'
color_blue = '#257fad'
color_magenta = '#5d5db1'
color_cyan = '#2d8f6f'

HOME = os.path.expanduser('~')
BIN = HOME + "/bin"
DPI = int(os.environ.get("DPI", 100))

def dpToPx(dp):
    return int(dp / 160 * DPI)

def spawn_bin(program):
    @lazy.function
    def __inner(qtile):
        full_path = BIN + "/" + program
        qtile.cmd_spawn(full_path)

    return __inner

def switch_group(index):
    @lazy.function
    def __inner(qtile):
        qtile.groups[index].cmd_toscreen()

    return __inner

def toggle_scrachpad_on_main(name):
    last_screen = -1

    @lazy.function
    def __inner(qtile):
        nonlocal last_screen
        group = qtile.groups_map.get("scratchpad")
        if name in group.dropdowns and group.dropdowns[name].visible:
            group.dropdowns[name].hide()
            qtile.focus_screen(last_screen)
        else:
            last_screen = qtile.screens.index(qtile.current_screen)
            qtile.focus_screen(0)
            group.cmd_dropdown_toggle('term')

    return __inner

def move_to_group(index):
    @lazy.function
    def __inner(qtile):
        group = qtile.groups[index]
        qtile.current_window.togroup(group.name)

    return __inner

def window_to_prev_group():
    @lazy.function
    def __inner(qtile):
        if qtile.current_window is not None:
            index = qtile.groups.index(qtile.current_group)
            if index > 0:
                group = qtile.groups[index - 1]
            else:
                group = qtile.groups[len(qtile.groups) - 2]

            qtile.current_window.togroup(group.name)
            group.cmd_toscreen()

    return __inner

def window_to_next_group():
    @lazy.function
    def __inner(qtile):
        if qtile.current_window is not None:
            index = qtile.groups.index(qtile.current_group)
            if index < len(qtile.groups) - 2:
                group = qtile.groups[index + 1]
            else:
                group = qtile.groups[0]

            qtile.current_window.togroup(group.name)
            group.cmd_toscreen()

    return __inner

def window_to_prev_screen():
    @lazy.function
    def __inner(qtile):
        if qtile.current_window is not None:
            index = qtile.screens.index(qtile.current_screen)
            if index > 0:
                qtile.current_window.togroup(qtile.screens[index - 1].group.name)
                qtile.toScreen(index - 1)
            else:
                qtile.current_window.togroup(qtile.screens[len(qtile.screens) - 1].group.name)
                qtile.toScreen(0)

    return __inner


def window_to_next_screen():
    @lazy.function
    def __inner(qtile):
        if qtile.current_window is not None:
            index = qtile.screens.index(qtile.current_screen)
            if index < len(qtile.screens) - 1:
                qtile.current_window.togroup(qtile.screens[index + 1].group.name)
                qtile.toScreen(index + 1)
            else:
                qtile.current_window.togroup(qtile.screens[0].group.name)
                qtile.toScreen(0)

    return __inner

def switch_groups_between_screens():
    @lazy.function
    def __inner(qtile):
        other_screen_index = (qtile.screens.index(qtile.current_screen) + 1) % len(qtile.screens)
        other_screen = qtile.screens[other_screen_index]

        qtile.current_screen.set_group(other_screen.group)

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

class CpuFreq(base.InLoopPollText):
    def __init__(self, **config):
        base.InLoopPollText.__init__(self, **config)
        self.update_interval = 5

    def poll(self):
        output = subprocess.check_output("lscpu").decode()
        info = {}
        for line in output.splitlines():
            key, val = line.split(':')
            info[key] = val

        freq = float(info["CPU MHz"].strip())

        return '%dMHz' % freq

class VpnStatus(base.InLoopPollText):
    def __init__(self, **config):
        base.InLoopPollText.__init__(self, **config)
        self.update_interval = 1

    def poll(self):
        output = subprocess.check_output(BIN + "/vpn_status.sh").decode()
        return "vpn: " + output.strip()

class GpuStatus(base.InLoopPollText):
    def __init__(self, **config):
        base.InLoopPollText.__init__(self, **config)
        self.update_interval = 1

    def poll(self):
        command = 'cat /sys/bus/pci/devices/0000:01:00.0/power/control' 
        output = subprocess.check_output(command.split(' ')).decode()
        return "gpu: " + output.strip()

class Commands(object):
    volume_up = 'amixer -q -c 0 sset Master 3dB+'
    volume_down = 'amixer -q -c 0 sset Master 3dB-'
    volume_toggle = 'amixer -q set Master toggle'
    run = f"dmenu_run -i -p '>>>' -fn 'Open Sans-10' -nb '#000' -nf '#fff' -sb '{color_green}' -sf '#fff'"

keys = [
    Key([mod, alt], "space", lazy.next_layout()),

    Key([mod], "Return", lazy.spawn("alacritty")),
    Key([mod], "f", lazy.spawn("thunar")),
    Key([mod], 'c', lazy.spawn("code")),

    Key([mod], "q", lazy.window.kill()),

    Key([mod, "control"], "r", lazy.restart()),
    Key([mod, "control"], "q", lazy.shutdown()),
    Key([mod], "r", lazy.spawn(Commands.run)),

    Key([mod], "Right", lazy.screen.next_group(skip_managed=True)),
    Key([mod], "Left", lazy.screen.prev_group(skip_managed=True)),
    Key([mod, shift], "Right", window_to_next_group()),
    Key([mod, shift], "Left", window_to_prev_group()),

    Key([mod], "period", lazy.layout.grow_main()),
    Key([mod], "comma", lazy.layout.shrink_main()),
    Key([mod], "slash", lazy.window.toggle_fullscreen()),
    Key([mod, ctrl], "space", lazy.layout.swap_main()),

    Key([mod], "Tab", lazy.layout.next()),
    Key([alt, shift], "Tab", lazy.layout.prev()),
    
    Key([mod], "l", lazy.spawn("dm-tool lock")),

    Key([mod], "grave", toggle_scrachpad_on_main("term")),

    Key([mod], "BackSpace", lazy.next_screen()),
    Key([mod, ctrl], "BackSpace", switch_groups_between_screens()),
    Key([mod, shift], "BackSpace", window_to_next_screen()),

    Key([], 'XF86AudioRaiseVolume', lazy.spawn(Commands.volume_up)),
    Key([], 'XF86AudioLowerVolume', lazy.spawn(Commands.volume_down)),
    Key([], 'XF86AudioMute', lazy.spawn(Commands.volume_toggle)),
    Key([], 'XF86AudioNext', lazy.spawn("playerctl next")),
    Key([], 'XF86AudioPrev', lazy.spawn("playerctl previous")),
    Key([], 'XF86AudioPlay', lazy.spawn("playerctl play-pause")),
    Key([], 'XF86MonBrightnessUp', lazy.spawn("light -A 10")),
    Key([], 'XF86MonBrightnessDown', lazy.spawn("light -U 10")),

    Key([alt], 'Tab', lazy.run_extension(extension.WindowList(
        all_groups = True,
        dmenu_ignorecase = True,
    ))),

    Key([mod], 'space', switch_language()),
    
    Key([mod], '1', spawn_bin('screen_clip.sh')),
    Key([mod], '2', spawn_bin('screen_file.sh')),
    Key([mod, shift], '1', spawn_bin('screen_clip_full.sh')),
    Key([mod, shift], '2', spawn_bin('screen_file_full.sh')),
    Key([mod], 's', spawn_bin('screen_layouts/setup.sh')),
    Key([mod], 'p', spawn_bin('dmenu-session.sh')),
]

groups = [
        ScratchPad("scratchpad", [
            DropDown("term", "alacritty -e zsh -c byobu", opacity=0.8, width=1.0, x=0.0, height=0.6)
        ]),
]

group_www = "www"
group_android = "android"
group_chat = "chat"
group_music = "music"
group_game = "game"

groups.append(Group(group_www,
    matches=[Match(wm_class=["Google-chrome"])], 
    spawn="google-chrome-stable", 
    init=True, 
    persist=True,
    position=0,
))

# groups.append(Group(group_android,
#     matches=[Match(wm_class=["jetbrains-studio"])], 
#     persist=True,
#     init=True,
#     position=1,
# ))

# groups.append(Group(group_chat,
#     matches=[Match(wm_class=["Slack"])], 
#     persist=False,
#     init=False,
#     position=2,
# ))

# groups.append(Group(group_music,
#     matches=[Match(wm_class=["spotify"]), Match(wm_class=["vlc"])], 
#     persist=False,
#     init=False,
#     position=3,
# ))

groups.append(Group("1"))
groups.append(Group("2"))
groups.append(Group("3"))
groups.append(Group("4"))
groups.append(Group("5"))
groups.append(Group("6"))
groups.append(Group("7"))

groups.append(Group(group_game,
    layout = "floating"
))

for index, key in enumerate(['F1', 'F2', 'F3', 'F4', 'F5']):
    keys.append(Key([mod], key, switch_group(index)))
    keys.append(Key([mod, shift], key, move_to_group(index)))

layouts = [
    layout.MonadTall(border_focus='#a54242'),
    layout.Floating()
]

widget_defaults = dict(
    font='DejaVu sans',
    padding=dpToPx(3),
    fontsize=dpToPx(17),
)

bolder_font = "DejaVu sans Bold"

extension_defaults = widget_defaults.copy()

screens = [
    Screen(
        top=bar.Bar(
            [
                widget.GroupBox(),
                widget.Prompt(),
                widget.Spacer(length=dpToPx(10)),
                widget.WindowName(),

                widget.CPUGraph(),
                widget.MemoryGraph(graph_color='85678f'),
                widget.NetGraph(graph_color='de935f'),
               
                GpuStatus(background=color_magenta),
                VpnStatus(background=color_cyan),
                CpuFreq(background=color_blue),
                widget.KeyboardLayout(background=color_green,configured_keyboards=['us','lt']),
                widget.Battery(
                    background=color_yellow,
                    charge_char = u'↑',
                    discharge_char = u'↓'
                ),
                widget.Backlight(
                    background=color_red,
                    backlight_name = 'intel_backlight',
                ),
                widget.ThermalSensor(background=color_magenta),
                widget.Wlan(interface='wlp59s0', background=color_cyan),
                widget.Volume(background=color_blue),
                widget.Systray(icon_size=dpToPx(30), padding=dpToPx(3)),
                widget.Clock(format='%Y-%m-%d %a %H:%M'),
                widget.CurrentScreen(
                    active_text='●',
                    inactive_text='○',
                    fontsize=dpToPx(30),
                    active_color=color_green,
                    inactive_color=color_red,
                ),
            ],
            dpToPx(30),
        ),
    ),
]

# Drag floating layouts.
mouse = [
    Drag([mod], "Button1", lazy.window.set_position_floating(),
         start=lazy.window.get_position()),
    Drag([mod], "Button3", lazy.window.set_size_floating(),
         start=lazy.window.get_size()),
    Click([mod], "Button2", lazy.window.bring_to_front()),
    Click([mod], "Button6", lazy.screen.next_group(skip_managed=True)),
    Click([mod], "Button7", lazy.screen.prev_group(skip_managed=True)),
]

dgroups_key_binder = None
dgroups_app_rules = []  # type: List
main = None
follow_mouse_focus = False
bring_front_click = False
cursor_warp = False
floating_layout = layout.Floating(float_rules=[
    # Run the utility of `xprop` to see the wm class and name of an X client.
    *layout.Floating.default_float_rules,
    Match(wm_class='confirmreset'),  # gitk
    Match(wm_class='makebranch'),  # gitk
    Match(wm_class='maketag'),  # gitk
    Match(wm_class='ssh-askpass'),  # ssh-askpass
    Match(title='branchdialog'),  # gitk
    Match(title='pinentry'),  # GPG key password entry
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

@hook.subscribe.startup_once
def autostart():
    path = os.path.expanduser('~/bin/startup.sh')
    subprocess.call([path])

@hook.subscribe.screen_change
def restart_on_randr(qtile, ev):
    qtile.cmd_restart()
