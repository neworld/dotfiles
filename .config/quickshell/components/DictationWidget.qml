import Quickshell
import Quickshell.Io
import QtQuick

BarText {
  id: root

  property string scriptPath: "/home/neworld/.config/quickshell/scripts/dictate.py"
  property string mode: "idle" // idle | recording
  property string liveText: ""

  property color idleForeground: "#cdd6f4"
  property color recordingForeground: "#d75f5f"
  property string textFontFamily: "Noto Sans Mono"
  property color popupBackground: "#1a1b26"

  text: "󰍬"
  foreground: mode === "recording" ? recordingForeground : idleForeground
  tooltipText: mode === "recording"
    ? "Recording — left-click to send · right-click to cancel"
    : "Click to dictate"

  onClicked: {
    if (mode === "idle") {
      liveText = "";
      mode = "recording";
    } else {
      const captured = liveText;
      mode = "idle";
      if (captured.trim().length > 0) sendProc.exec([scriptPath, "send", captured]);
      liveText = "";
    }
  }

  onRightClicked: {
    if (mode === "recording") {
      mode = "idle";
      liveText = "";
      cancelProc.exec([scriptPath, "cancel"]);
    }
  }

  // Live transcription stream. Bound to `mode`, so flipping to "idle" sends
  // SIGTERM to dictate.py listen (which stops parec and exits).
  Process {
    id: listenProc
    command: [root.scriptPath, "listen"]
    running: root.mode === "recording"
    stdout: SplitParser {
      onRead: function(line) {
        const trimmed = line.trim();
        if (trimmed.length === 0) return;
        try {
          const payload = JSON.parse(trimmed);
          if (payload.text !== undefined) root.liveText = payload.text;
        } catch (e) {
          // ignore non-JSON noise
        }
      }
    }
  }

  Process { id: sendProc }
  Process { id: cancelProc }

  // Live transcript popup — read-only, non-focusable (like BarTooltip).
  PopupWindow {
    id: popup

    anchor.item: root
    anchor.rect.x: Math.round((root.width - box.width) / 2)
    anchor.rect.y: root.height + 4
    anchor.rect.width: box.width
    anchor.rect.height: box.height
    anchor.edges: Edges.Top
    anchor.gravity: Edges.Bottom
    anchor.adjustment: PopupAdjustment.SlideX

    implicitWidth: box.width
    implicitHeight: box.height
    visible: root.mode === "recording"
    color: "transparent"

    Rectangle {
      id: box
      width: 360
      height: label.implicitHeight + 16
      color: root.popupBackground
      border.color: Qt.rgba(root.idleForeground.r, root.idleForeground.g, root.idleForeground.b, 0.28)
      border.width: 1
      radius: 0

      Text {
        id: label
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: 8
        anchors.rightMargin: 8
        text: root.liveText.length > 0 ? root.liveText : "Listening…"
        color: root.liveText.length > 0 ? root.idleForeground
          : Qt.rgba(root.idleForeground.r, root.idleForeground.g, root.idleForeground.b, 0.55)
        font.family: root.textFontFamily
        font.pixelSize: 12
        wrapMode: Text.Wrap
        lineHeight: 1.15
      }
    }
  }
}
