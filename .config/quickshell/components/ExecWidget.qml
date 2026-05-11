import Quickshell.Io
import QtQuick

BarText {
  id: root

  property string command: ""
  property string tooltipCommand: ""
  property int interval: 1000
  property bool stream: false
  property bool parseJson: false
  property bool hideWhenEmpty: false
  property bool useFallbackWhenOutput: false
  property string fallbackText: ""
  property color lowForeground: foreground
  property color mediumForeground: foreground
  property color highForeground: foreground
  property string currentClass: ""
  property string lastText: ""
  property string lastTooltip: tooltipText

  text: lastText
  tooltipText: lastTooltip
  foreground: currentClass === "high" ? highForeground
    : currentClass === "medium" ? mediumForeground
    : lowForeground
  active: currentClass === "active"
  visible: !hideWhenEmpty || lastText.length > 0

  function refresh() {
    if (!root.stream && root.command.length > 0) process.exec(["sh", "-c", root.command]);
  }

  function applyLine(line) {
    const trimmed = line.trim();
    if (trimmed.length === 0) {
      if (hideWhenEmpty) lastText = "";
      return;
    }

    if (!parseJson) {
      lastText = useFallbackWhenOutput && fallbackText.length > 0 ? fallbackText : trimmed;
      return;
    }

    try {
      const payload = JSON.parse(trimmed);
      lastText = payload.text || fallbackText;
      lastTooltip = payload.tooltip || lastTooltip;
      currentClass = payload.class || "";
    } catch (error) {
      lastText = fallbackText.length > 0 ? fallbackText : trimmed;
    }
  }

  Process {
    id: process
    command: ["sh", "-c", root.command]
    running: root.stream && root.command.length > 0
    stdout: SplitParser {
      onRead: function(data) {
        root.applyLine(data);
      }
    }
    onRunningChanged: {
      if (root.stream && !running && root.command.length > 0) restart.start();
    }
  }

  Process {
    id: tooltipProcess
    stdout: StdioCollector {
      onStreamFinished: {
        const value = this.text.trim();
        if (value.length > 0) root.lastTooltip = value;
      }
    }
  }

  Timer {
    id: poll
    interval: root.interval
    running: !root.stream && root.command.length > 0
    repeat: true
    triggeredOnStart: true
    onTriggered: root.refresh()
  }

  Timer {
    id: restart
    interval: 2000
    repeat: false
    onTriggered: process.running = true
  }

  Timer {
    interval: root.interval
    running: root.tooltipCommand.length > 0
    repeat: true
    triggeredOnStart: true
    onTriggered: tooltipProcess.exec(["sh", "-c", root.tooltipCommand])
  }
}
