import Quickshell.Io
import QtQuick
import QtQuick.Layouts

Item {
  id: root

  property color foreground: "#cdd6f4"
  property color lowForeground: foreground
  property color mediumForeground: "#d7af5f"
  property color highForeground: "#d75f5f"
  property string fontFamily: "JetBrainsMono Nerd Font"
  property string brandFontFamily: "Font Awesome 7 Brands"
  property string usageText: ""
  property string tooltipText: ""
  property string currentClass: "low"
  property color statusColor: currentClass === "high" ? highForeground
    : currentClass === "medium" || currentClass === "mid" ? mediumForeground
    : lowForeground

  signal clicked()

  Layout.preferredWidth: usageRow.implicitWidth + 15
  Layout.preferredHeight: 26
  Layout.fillHeight: true
  visible: usageText.length > 0

  function applyLine(line) {
    const trimmed = line.trim();
    if (trimmed.length === 0) return;

    try {
      const payload = JSON.parse(trimmed);
      usageText = payload.text || "";
      tooltipText = payload.tooltip || "";
      currentClass = payload.class || "low";
    } catch (error) {
      usageText = trimmed;
    }
  }

  Process {
    id: codexProcess
    stdout: SplitParser {
      onRead: function(data) {
        root.applyLine(data);
      }
    }
  }

  Timer {
    interval: 60000
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: codexProcess.exec(["sh", "-c", "codexbar --format '{session_pct}% · {weekly_pct}%  ' 2>/dev/null || true"])
  }

  RowLayout {
    id: usageRow
    anchors.centerIn: parent
    spacing: 4

    Text {
      text: "\ue7cf"
      color: root.statusColor
      font.family: root.brandFontFamily
      font.pixelSize: 12
      verticalAlignment: Text.AlignVCenter
      Layout.alignment: Qt.AlignVCenter
    }

    Text {
      text: root.usageText
      color: root.statusColor
      font.family: root.fontFamily
      font.pixelSize: 12
      textFormat: Text.RichText
      verticalAlignment: Text.AlignVCenter
      Layout.alignment: Qt.AlignVCenter
    }
  }

  MouseArea {
    id: mouse

    anchors.fill: parent
    hoverEnabled: true
    onClicked: root.clicked()

    BarTooltip {
      visible: mouse.containsMouse && root.tooltipText.length > 0
      anchorItem: mouse
      text: root.tooltipText
      foreground: root.statusColor
      background: "#1a1b26"
      fontFamily: root.fontFamily
      richText: true
    }
  }
}
