import QtQuick

BarText {
  id: root

  property date now: new Date()

  text: Qt.formatDateTime(now, "dddd dd MMMM HH:mm")
  leftPadding: 8.75
  rightPadding: 8.75

  Timer {
    interval: 1000
    running: true
    repeat: true
    onTriggered: root.now = new Date()
  }
}
