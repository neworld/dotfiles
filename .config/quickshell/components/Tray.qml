import Quickshell.Services.SystemTray
import Quickshell.Widgets
import QtQuick
import QtQuick.Layouts

RowLayout {
  id: root

  required property var panelWindow

  Layout.rightMargin: 16
  spacing: 17

  Repeater {
    model: SystemTray.items

    Item {
      id: trayItem

      required property var modelData

      Layout.preferredWidth: 12
      Layout.preferredHeight: 26

      IconImage {
        anchors.centerIn: parent
        implicitSize: 12
        source: modelData.icon
      }

      MouseArea {
        id: mouse

        anchors.fill: parent
        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
        onClicked: function(event) {
          if (event.button === Qt.RightButton && modelData.hasMenu) {
            const point = mouse.mapToItem(null, event.x, event.y);
            modelData.display(root.panelWindow, Math.round(point.x), Math.round(point.y));
          } else if (event.button === Qt.MiddleButton) {
            modelData.secondaryActivate();
          } else {
            modelData.activate();
          }
        }
        onWheel: function(event) {
          modelData.scroll(event.angleDelta.y, false);
        }
      }
    }
  }
}
