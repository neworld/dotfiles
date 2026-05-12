import Quickshell.Hyprland
import Quickshell.Io
import QtQuick

BarText {
  id: root

  property var screen: null
  property var monitor: null
  property var screenMonitor: screen === null ? null : Hyprland.monitorFor(screen)
  property var activeMonitor: monitor !== null ? monitor : screenMonitor
  property string monitorName: monitor === null ? (screen === null ? "" : screen.name) : monitor.name
  property var monitorData: activeMonitor === null ? ({}) : activeMonitor.lastIpcObject
  property string monitorModel: monitorData.model || (screen === null ? "" : screen.model)
  property string monitorSerial: monitorData.serial || (screen === null ? "" : screen.serialNumber)
  property string monitorDescription: activeMonitor === null ? monitorModel : activeMonitor.description
  property string brightnessText: ""
  property int pendingDelta: 0

  text: isLaptop ? "󰌢" : "󰍹"
  tooltipText: brightnessText.length > 0 ? brightnessText : monitorDescription

  property bool isLaptop: {
    const name = monitorName.toLowerCase();
    return name.indexOf("edp") === 0 || name.indexOf("lvds") === 0;
  }

  function scriptArgs(action, delta) {
    const args = [
      "python3",
      "/home/neworld/.config/quickshell/scripts/display-brightness.py",
      action,
      "--name", monitorName,
      "--model", monitorModel,
      "--serial", monitorSerial,
      "--description", monitorDescription,
    ];

    if (action === "change") args.push("--delta", String(delta));
    return args;
  }

  function applyPayload(text) {
    const trimmed = text.trim();
    if (trimmed.length === 0) return;

    try {
      const payload = JSON.parse(trimmed);
      brightnessText = payload.tooltip || "";
    } catch (error) {
      brightnessText = trimmed;
    }
  }

  leftPadding: 7.5
  rightPadding: 7.5

  Process {
    id: statusProcess
    stdout: StdioCollector {
      onStreamFinished: root.applyPayload(this.text)
    }
  }

  Process {
    id: changeProcess
    stdout: StdioCollector {
      onStreamFinished: root.applyPayload(this.text)
    }
  }

  Timer {
    interval: 1000
    running: true
    repeat: false
    triggeredOnStart: true
    onTriggered: statusProcess.exec(root.scriptArgs("status", 0))
  }

  onWheel: function(delta) {
    pendingDelta += delta > 0 ? 10 : -10;
    pendingDelta = Math.max(-100, Math.min(100, pendingDelta));
    changeDebounce.restart();
  }

  Timer {
    id: changeDebounce
    interval: 250
    repeat: false
    onTriggered: {
      const delta = root.pendingDelta;
      root.pendingDelta = 0;
      changeProcess.exec(root.scriptArgs("change", delta));
    }
  }
}
