import QtQuick
import QtQuick.Layouts

RowLayout {
  id: root

  property var devices: []
  property color foreground: "#cdd6f4"
  property color lowForeground: "#d75f5f"
  property color chargingForeground: "#7aa2f7"
  property string fontFamily: "JetBrainsMono Nerd Font"
  property real laptopWidth: 52
  property real deviceWidth: 18

  signal clicked()

  spacing: 0
  visible: devices.length > 0

  function colorFor(deviceClass) {
    if (deviceClass === "low") return lowForeground;
    if (deviceClass === "charging") return chargingForeground;
    return foreground;
  }

  Repeater {
    model: root.devices

    BarText {
      required property var modelData

      text: modelData.text || ""
      tooltipText: modelData.tooltip || ""
      foreground: root.colorFor(modelData["class"] || "")
      fontFamily: root.fontFamily
      fontPixelSize: 12
      fixedWidth: modelData.kind === "laptop" ? root.laptopWidth : root.deviceWidth
      onClicked: root.clicked()
    }
  }
}
