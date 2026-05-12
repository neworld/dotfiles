import Quickshell.Io
import QtQuick
import QtQuick.Layouts

RowLayout {
  id: root

  property color foreground: "#cdd6f4"
  property color background: "#1a1b26"
  property string fontFamily: "Noto Sans Mono"
  property string iconFontFamily: "JetBrainsMono Nerd Font"
  property string player: ""
  property string playerIcon: ""
  property string title: ""
  property string artist: ""
  property string playbackStatus: ""
  property string tooltipText: ""
  property real titlePreferredWidth: 420
  property real maxWidgetWidth: titlePreferredWidth + controlsWidth
  readonly property real controlsWidth: 110
  readonly property real titleWidth: Math.max(150, Math.min(titlePreferredWidth, maxWidgetWidth - controlsWidth))

  signal commandRequested(string command)

  spacing: 0
  visible: player.length > 0
  Layout.preferredWidth: visible ? titleWidth + controlsWidth : 0
  Layout.fillHeight: true

  function playerArg() {
    return player.length > 0 ? " -p " + JSON.stringify(player) : "";
  }

  function runPlayerctl(action) {
    if (player.length === 0) return;
    commandRequested("playerctl" + playerArg() + " " + action);
    refreshDelay.restart();
  }

  function applyStatus(text) {
    const trimmed = text.trim();
    if (trimmed.length === 0) {
      player = "";
      title = "";
      artist = "";
      playbackStatus = "";
      tooltipText = "";
      return;
    }

    try {
      const payload = JSON.parse(trimmed);
      player = payload.player || "";
      playerIcon = payload.icon || "";
      title = payload.title || "";
      artist = payload.artist || "";
      playbackStatus = payload.status || "";
      tooltipText = payload.tooltip || "";
    } catch (error) {
      player = "";
    }
  }

  function refresh() {
    statusProcess.exec(["/home/neworld/.config/quickshell/scripts/media-status.py"]);
  }

  Process {
    id: statusProcess
    stdout: StdioCollector {
      onStreamFinished: root.applyStatus(this.text)
    }
  }

  Timer {
    interval: 1000
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: root.refresh()
  }

  Timer {
    id: refreshDelay
    interval: 100
    repeat: false
    onTriggered: root.refresh()
  }

  BarText {
    text: root.playerIcon
    tooltipText: root.tooltipText
    foreground: root.foreground
    background: root.background
    fontFamily: root.iconFontFamily
    leftPadding: 8
    rightPadding: 4
    onClicked: root.runPlayerctl("play-pause")
  }

  BarText {
    text: "󰒮"
    tooltipText: "Previous"
    foreground: root.foreground
    background: root.background
    fontFamily: root.iconFontFamily
    leftPadding: 4
    rightPadding: 4
    onClicked: root.runPlayerctl("previous")
  }

  BarText {
    text: root.playbackStatus === "Playing" ? "" : ""
    tooltipText: root.playbackStatus === "Playing" ? "Pause" : "Play"
    foreground: root.foreground
    background: root.background
    fontFamily: root.iconFontFamily
    leftPadding: 4
    rightPadding: 4
    onClicked: root.runPlayerctl("play-pause")
  }

  BarText {
    text: "󰒭"
    tooltipText: "Next"
    foreground: root.foreground
    background: root.background
    fontFamily: root.iconFontFamily
    leftPadding: 4
    rightPadding: 7
    onClicked: root.runPlayerctl("next")
  }

  Item {
    Layout.preferredWidth: root.titleWidth
    Layout.fillHeight: true
    clip: true

    Text {
      anchors.left: parent.left
      anchors.right: parent.right
      anchors.verticalCenter: parent.verticalCenter
      text: root.artist.length > 0 ? root.artist + " - " + root.title : root.title
      color: root.foreground
      font.family: root.fontFamily
      font.pixelSize: 12
      elide: Text.ElideRight
      verticalAlignment: Text.AlignVCenter
    }

    MouseArea {
      id: titleMouse
      anchors.fill: parent
      hoverEnabled: true
      onClicked: root.runPlayerctl("play-pause")

      BarTooltip {
        visible: titleMouse.containsMouse && root.tooltipText.length > 0
        anchorItem: titleMouse
        text: root.tooltipText
        foreground: root.foreground
        background: root.background
        fontFamily: root.fontFamily
      }
    }
  }
}
