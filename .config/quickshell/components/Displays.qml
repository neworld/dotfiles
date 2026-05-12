import Quickshell.Hyprland
import QtQuick
import QtQuick.Layouts

RowLayout {
  id: root

  property color foreground: "#cdd6f4"
  property string fontFamily: "JetBrainsMono Nerd Font"

  spacing: 0

  Repeater {
    model: Hyprland.monitors

    DisplayWidget {
      required property var modelData

      monitor: modelData
      foreground: root.foreground
      fontFamily: root.fontFamily
    }
  }
}
