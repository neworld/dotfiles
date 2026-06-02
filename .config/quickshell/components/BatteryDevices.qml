import Quickshell.Io
import QtQuick
import QtQuick.Layouts

RowLayout {
  id: root

  property int interval: 5000
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

  function applyOutput(output) {
    const trimmed = output.trim();
    if (trimmed.length === 0) {
      devices = [];
      return;
    }

    try {
      const payload = JSON.parse(trimmed);
      devices = Array.isArray(payload) ? payload : [];
    } catch (error) {
      devices = [];
    }
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

  Process {
    id: batteryProcess

    stdout: StdioCollector {
      onStreamFinished: root.applyOutput(this.text)
    }
  }

  Timer {
    interval: root.interval
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: batteryProcess.exec(["python3", "/home/neworld/.config/quickshell/scripts/battery-status.py"])
  }
}
