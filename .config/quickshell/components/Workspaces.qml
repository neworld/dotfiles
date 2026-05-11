import Quickshell.Hyprland
import Quickshell.Io
import QtQuick
import QtQuick.Layouts

RowLayout {
  id: root

  property color foreground: "#cdd6f4"
  property color background: "#1a1b26"
  property color inactiveForeground: Qt.rgba(foreground.r, foreground.g, foreground.b, 0.5)
  property color remoteBorder: "#5c6370"
  property string fontFamily: "Noto Sans Mono"
  property string iconFontFamily: "JetBrainsMono Nerd Font"
  property var screen: null
  property var windowIcons: ({})

  spacing: 3

  property var monitor: screen === null ? null : Hyprland.monitorFor(screen)

  function workspaceById(id) {
    for (let i = 0; i < Hyprland.workspaces.values.length; i++) {
      const workspace = Hyprland.workspaces.values[i];
      if (workspace.id === id) return workspace;
    }
    return null;
  }

  function classIconData(windowClass) {
    const normalized = String(windowClass || "").toLowerCase();
    const icons = {
      "alacritty": { icon: "" },
      "chromium": { icon: "" },
      "code": { icon: "󰨞" },
      "code-oss": { icon: "󰨞" },
      "discord": { icon: "" },
      "firefox": { icon: "" },
      "freecad": { icon: "󰆧" },
      "google-chrome": { icon: "" },
      "kitty": { icon: "" },
      "org.gnome.nautilus": { icon: "" },
      "prusa-slicer": { icon: "󰹛" },
      "slack": { icon: "󰒱" },
      "spotify": { icon: "" },
      "steam": { icon: "" },
      "telegramdesktop": { icon: "" },
      "thunderbird": { icon: "" },
      "vesktop": { icon: "" }
    };

    if (icons[normalized] !== undefined) return icons[normalized];
    if (normalized.indexOf("chrome") !== -1) return { icon: "" };
    if (normalized.indexOf("firefox") !== -1) return { icon: "" };
    if (normalized.indexOf("terminal") !== -1) return { icon: "" };
    if (normalized.indexOf("jetbrains") !== -1) return { icon: "" };
    return { icon: "" };
  }

  function workspaceIcon(id) {
    return windowIcons[id] || "";
  }

  function updateWindowIcons(text) {
    let clients = [];

    try {
      clients = JSON.parse(text);
    } catch (error) {
      return;
    }

    const choices = {};

    for (let i = 0; i < clients.length; i++) {
      const client = clients[i];
      const workspace = client.workspace || {};
      const id = workspace.id;

      if (id < 1 || id > 10 || client.hidden || client.pinned) continue;

      const existing = choices[id];
      const currentFocus = client.focusHistoryID === undefined ? 999999 : client.focusHistoryID;
      const existingFocus = existing === undefined || existing.focusHistoryID === undefined ? 999999 : existing.focusHistoryID;

      if (existing === undefined || currentFocus < existingFocus) {
        choices[id] = client;
      }
    }

    const icons = {};
    for (const id in choices) {
      const iconData = classIconData(choices[id].class || choices[id].initialClass);
      icons[id] = iconData.icon;
    }

    windowIcons = icons;
  }

  Process {
    id: clientProcess
    stdout: StdioCollector {
      onStreamFinished: root.updateWindowIcons(this.text)
    }
  }

  Timer {
    interval: 1000
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: clientProcess.exec(["hyprctl", "clients", "-j"])
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
      property string icon: root.workspaceIcon(modelData)

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
        text: icon.length > 0 ? icon : String(modelData)
        color: workspaceForeground
        font.family: icon.length > 0 ? root.iconFontFamily : root.fontFamily
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
