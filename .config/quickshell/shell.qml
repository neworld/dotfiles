//@ pragma UseQApplication
import Quickshell
import Quickshell.Io
import QtQuick
import QtQuick.Layouts
import "components"

Scope {
  id: root

  property color foreground: "#cdd6f4"
  property color background: "#1a1b26"
  property color warning: "#d7af5f"
  property color critical: "#d75f5f"
  property string fontFamily: "Noto Sans Mono"
  property string iconFontFamily: "JetBrainsMono Nerd Font"

  function launch(command) {
    launcher.exec(["sh", "-c", command]);
  }

  Process {
    id: launcher
  }

  Variants {
    model: Quickshell.screens

    PanelWindow {
      id: panel

      required property var modelData
      screen: modelData

      anchors {
        top: true
        left: true
        right: true
      }

      implicitHeight: 26
      color: root.background
      exclusiveZone: 26

      Rectangle {
        anchors.fill: parent
        color: root.background

        RowLayout {
          id: leftModules
          anchors.left: parent.left
          anchors.top: parent.top
          anchors.bottom: parent.bottom
          anchors.leftMargin: 8
          spacing: 0

          BarText {
            text: ""
            tooltipText: "Scratchpad terminal"
            foreground: root.foreground
            fontFamily: root.iconFontFamily
            leftPadding: 7.5
            rightPadding: 7.5
            onClicked: root.launch("/home/neworld/.config/hypr/bin/toggle-terminal.sh")
          }

          Workspaces {
            screen: panel.screen
            foreground: root.foreground
            background: root.background
            fontFamily: root.fontFamily
          }
        }

        RowLayout {
          id: centerModules
          anchors.horizontalCenter: parent.horizontalCenter
          anchors.top: parent.top
          anchors.bottom: parent.bottom
          spacing: 0
          z: 1

          ClockWidget {
            foreground: root.foreground
            fontFamily: root.fontFamily
            onRightClicked: root.launch("omarchy-launch-floating-terminal-with-presentation omarchy-tz-select")
          }

          ExecWidget {
            command: "[ -n \"$OMARCHY_PATH\" ] && [ -x \"$OMARCHY_PATH/default/waybar/indicators/screen-recording.sh\" ] && \"$OMARCHY_PATH/default/waybar/indicators/screen-recording.sh\" || true"
            interval: 2000
            parseJson: true
            hideWhenEmpty: true
            foreground: root.foreground
            activeForeground: "#a55555"
            fontFamily: root.iconFontFamily
            fontPixelSize: 10
            leftPadding: 8.75
            rightPadding: 7.5
            onClicked: root.launch("omarchy-cmd-screenrecord")
          }
        }

        RowLayout {
          id: rightModules
          anchors.right: parent.right
          anchors.top: parent.top
          anchors.bottom: parent.bottom
          anchors.rightMargin: 8
          spacing: 0

          CodexUsage {
            foreground: root.foreground
            lowForeground: root.foreground
            mediumForeground: root.warning
            highForeground: root.critical
            fontFamily: root.iconFontFamily
            brandFontFamily: "Font Awesome 7 Brands"
            onClicked: root.launch("xdg-open https://chatgpt.com/codex/settings/usage")
          }

          PixelMetrics {
            foreground: root.foreground
            lowForeground: root.foreground
            mediumForeground: root.warning
            highForeground: root.critical
            fontFamily: root.iconFontFamily
            onClicked: root.launch("omarchy-launch-or-focus-tui btop")
            onRightClicked: root.launch("alacritty")
          }

          Tray {
            panelWindow: panel
          }

          ExecWidget {
            command: "bluetoothctl show 2>/dev/null | awk '/Powered:/ { powered=$2 } /Discoverable:/ { } END { if (powered == \"yes\") print \"\"; else print \"󰂲\" }'"
            interval: 5000
            foreground: root.foreground
            fontFamily: root.iconFontFamily
            rightPadding: 17
            onClicked: root.launch("blueman-manager")
          }

          ExecWidget {
            command: "nmcli -t -f TYPE,STATE,CONNECTION dev status 2>/dev/null | awk -F: '$1==\"wifi\" && $2==\"connected\" { print \"󰤨\"; found=1; exit } $1==\"ethernet\" && $2==\"connected\" { print \"󰀂\"; found=1; exit } END { if (!found) print \"󰤮\" }'"
            interval: 3000
            foreground: root.foreground
            fontFamily: root.iconFontFamily
            rightPadding: 13
            onClicked: root.launch("omarchy-launch-wifi")
          }

          ExecWidget {
            command: "pamixer --get-volume-human 2>/dev/null | awk '{ if ($1 == \"muted\") print \"\"; else { gsub(/%/, \"\", $1); if ($1 < 34) print \"\"; else if ($1 < 67) print \"\"; else print \"\" } }'"
            interval: 1000
            foreground: root.foreground
            fontFamily: root.iconFontFamily
            tooltipCommand: "pamixer --get-volume-human 2>/dev/null | awk '{ print \"Playing at \" $1 }'"
            leftPadding: 7.5
            rightPadding: 7.5
            onClicked: root.launch("pavucontrol")
            onRightClicked: root.launch("pamixer -t")
            onWheel: function(delta) {
              root.launch(delta > 0 ? "pamixer -i 5" : "pamixer -d 5");
            }
          }

          ExecWidget {
            command: "/home/neworld/.config/quickshell/scripts/battery-status.py"
            interval: 5000
            parseJson: true
            hideWhenEmpty: true
            foreground: root.foreground
            lowForeground: root.foreground
            mediumForeground: root.warning
            highForeground: root.critical
            fontFamily: root.iconFontFamily
            leftPadding: 7.5
            rightPadding: 7.5
            onClicked: root.launch("omarchy-menu power")
          }
        }
      }
    }
  }
}
