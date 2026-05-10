import Quickshell.Hyprland
import QtQuick
import QtQuick.Layouts

RowLayout {
  id: root

  property color foreground: "#cdd6f4"
  property color background: "#1a1b26"
  property color inactiveForeground: Qt.rgba(foreground.r, foreground.g, foreground.b, 0.5)
  property color remoteBorder: "#5c6370"
  property string fontFamily: "Noto Sans Mono"
  property var screen: null

  spacing: 3

  property var monitor: screen === null ? null : Hyprland.monitorFor(screen)

  function workspaceById(id) {
    for (let i = 0; i < Hyprland.workspaces.values.length; i++) {
      const workspace = Hyprland.workspaces.values[i];
      if (workspace.id === id) return workspace;
    }
    return null;
  }

  Repeater {
    model: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    Item {
      required property int modelData

      property var workspace: root.workspaceById(modelData)
      property bool isActive: workspace !== null && workspace.active
      property bool isOnThisMonitor: workspace !== null && root.monitor !== null && workspace.monitor === root.monitor
      property color workspaceForeground: workspace === null ? root.inactiveForeground : root.foreground
      property color workspaceBorder: isActive
        ? (isOnThisMonitor ? root.foreground : root.remoteBorder)
        : "transparent"

      Layout.preferredWidth: 20
      Layout.preferredHeight: 18
      Layout.alignment: Qt.AlignVCenter

      Rectangle {
        anchors.fill: parent
        anchors.margins: 1
        color: root.background
        border.color: workspaceBorder
        border.width: isActive ? 1 : 0
        radius: 0
      }

      Text {
        anchors.centerIn: parent
        text: String(modelData)
        color: workspaceForeground
        font.family: root.fontFamily
        font.pixelSize: 12
        verticalAlignment: Text.AlignVCenter
        horizontalAlignment: Text.AlignHCenter
      }

      MouseArea {
        anchors.fill: parent
        onClicked: {
          if (workspace !== null) workspace.activate();
          else Hyprland.dispatch("workspace " + modelData);
        }
      }
    }
  }
}
