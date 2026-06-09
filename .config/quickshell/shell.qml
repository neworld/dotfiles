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
  property color batteryLow: "#f7768e"
  property color batteryCharging: "#7aa2f7"
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
            iconFontFamily: root.iconFontFamily
          }

          Item {
            Layout.preferredWidth: 40
            Layout.fillHeight: true
          }

          MediaWidget {
            id: mediaWidget
            foreground: root.foreground
            background: root.background
            fontFamily: root.fontFamily
            iconFontFamily: root.iconFontFamily
            maxWidgetWidth: Math.max(260, centerModules.x - (leftModules.x + mediaWidget.x) - 40)
            onCommandRequested: function(command) {
              root.launch(command);
            }
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
            id: clockWidget
            foreground: root.foreground
            fontFamily: root.fontFamily
            onRightClicked: root.launch("omarchy-launch-floating-terminal-with-presentation omarchy-tz-select")
          }

          ExecWidget {
            command: "curl -fsS --max-time 3 'https://wttr.in/Vilnius?format=%c%20%t' 2>/dev/null | tr -d '+'"
            tooltipCommand: "curl -fsS --max-time 3 'https://wttr.in/Vilnius?format=Vilnius:%20%C,%20%t,%20feels%20%f,%20wind%20%w' 2>/dev/null | tr -d '+'"
            interval: 900000
            hideWhenEmpty: true
            foreground: root.foreground
            fontFamily: root.fontFamily
            leftPadding: 7.5
            rightPadding: 7.5
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
            id: pixelMetrics
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

          Displays {
            foreground: root.foreground
            fontFamily: root.iconFontFamily
          }

          BatteryDevices {
            devices: pixelMetrics.batteryDevices
            foreground: root.foreground
            lowForeground: root.batteryLow
            chargingForeground: root.batteryCharging
            fontFamily: root.iconFontFamily
            onClicked: root.launch("omarchy-menu power")
          }

          ExecWidget {
            command: "rfkill list bluetooth 2>/dev/null | awk 'BEGIN { icon=\"󰂲\" } /Soft blocked: no/ { soft=1 } /Hard blocked: no/ { hard=1 } END { if (soft && hard) print \"\"; else print icon }'"
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
            id: volumeWidget
            command: "wpctl get-volume @DEFAULT_AUDIO_SINK@ 2>/dev/null | awk '{ muted=($0 ~ /\\[MUTED\\]/); volume=int($2 * 100 + 0.5); if (muted) print \"󰝟\"; else if (volume < 34) print \"󰕿\"; else if (volume < 67) print \"󰖀\"; else print \"󰕾\" }'"
            interval: 1000
            foreground: root.foreground
            fontFamily: root.iconFontFamily
            tooltipCommand: "wpctl get-volume @DEFAULT_AUDIO_SINK@ 2>/dev/null | awk '{ muted=($0 ~ /\\[MUTED\\]/); volume=int($2 * 100 + 0.5); print muted ? \"Muted at \" volume \"%\" : \"Playing at \" volume \"%\" }'"
            leftPadding: 7.5
            rightPadding: 7.5
            onClicked: root.launch("pavucontrol")
            onRightClicked: {
              root.launch("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle");
              volumeRefresh.restart();
            }
            onWheel: function(delta) {
              root.launch(delta > 0 ? "wpctl set-volume -l 1.0 @DEFAULT_AUDIO_SINK@ 5%+" : "wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-");
              volumeRefresh.restart();
            }

            Timer {
              id: volumeRefresh
              interval: 75
              repeat: false
              onTriggered: volumeWidget.refresh()
            }
          }

          ExecWidget {
            id: keyboardLayoutWidget
            command: "/home/neworld/.config/quickshell/scripts/keyboard-layout.py"
            interval: 1000
            parseJson: true
            hideWhenEmpty: true
            foreground: root.foreground
            fontFamily: "Noto Color Emoji"
            fontPixelSize: 12
            leftPadding: 7.5
            rightPadding: 7.5
            onClicked: {
              root.launch("/home/neworld/.config/quickshell/scripts/keyboard-layout.py next");
              keyboardRefresh.restart();
            }

            Timer {
              id: keyboardRefresh
              interval: 100
              repeat: false
              onTriggered: keyboardLayoutWidget.refresh()
            }
          }

          BarText {
            text: "⏻"
            tooltipText: "Power menu"
            foreground: root.foreground
            fontFamily: root.iconFontFamily
            fontPixelSize: 13
            leftPadding: 7.5
            rightPadding: 7.5
            onClicked: root.launch("wlogout")
          }
        }
      }
    }
  }
}
