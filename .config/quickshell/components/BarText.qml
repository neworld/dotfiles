import QtQuick
import QtQuick.Layouts

Item {
  id: root

  property alias text: label.text
  property alias textFormat: label.textFormat
  property string tooltipText: ""
  property color foreground: "#cdd6f4"
  property color background: "transparent"
  property string fontFamily: "Noto Sans Mono"
  property int fontPixelSize: 12
  property real leftPadding: 0
  property real rightPadding: 0
  property bool active: false
  property color activeForeground: foreground

  signal clicked()
  signal rightClicked()
  signal wheel(real delta)

  Layout.preferredWidth: visible ? label.implicitWidth + leftPadding + rightPadding : 0
  Layout.fillHeight: true
  visible: text.length > 0

  Rectangle {
    anchors.fill: parent
    color: root.background
  }

  Text {
    id: label
    anchors.centerIn: parent
    color: root.active ? root.activeForeground : root.foreground
    font.family: root.fontFamily
    font.pixelSize: root.fontPixelSize
    textFormat: Text.PlainText
    verticalAlignment: Text.AlignVCenter
  }

  MouseArea {
    id: mouse
    anchors.fill: parent
    hoverEnabled: true
    acceptedButtons: Qt.LeftButton | Qt.RightButton
    onClicked: function(event) {
      if (event.button === Qt.RightButton) root.rightClicked();
      else root.clicked();
    }
    onWheel: function(event) {
      root.wheel(event.angleDelta.y);
    }

    BarTooltip {
      visible: mouse.containsMouse && root.tooltipText.length > 0
      anchorItem: mouse
      text: root.tooltipText
      foreground: root.foreground
      background: "#1a1b26"
      fontFamily: root.fontFamily
    }
  }
}
