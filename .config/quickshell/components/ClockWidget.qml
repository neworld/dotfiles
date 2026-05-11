import Quickshell
import QtQuick
import QtQuick.Layouts

BarText {
  id: root

  property date now: new Date()
  property date visibleMonth: new Date(now.getFullYear(), now.getMonth(), 1)
  property bool calendarOpen: false
  property var weekdays: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

  text: Qt.formatDateTime(now, "dddd dd MMMM HH:mm")
  leftPadding: 8.75
  rightPadding: 8.75
  onClicked: {
    visibleMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    calendarOpen = !calendarOpen;
  }

  function daysInMonth(year, month) {
    return new Date(year, month + 1, 0).getDate();
  }

  function firstWeekdayOffset(year, month) {
    return (new Date(year, month, 1).getDay() + 6) % 7;
  }

  function shiftedMonth(offset) {
    return new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() + offset, 1);
  }

  function dayForMonthCell(monthDate, index) {
    const day = index - firstWeekdayOffset(monthDate.getFullYear(), monthDate.getMonth()) + 1;
    const last = daysInMonth(monthDate.getFullYear(), monthDate.getMonth());
    return day >= 1 && day <= last ? day : 0;
  }

  function isTodayInMonth(monthDate, day) {
    return day === now.getDate()
      && monthDate.getMonth() === now.getMonth()
      && monthDate.getFullYear() === now.getFullYear();
  }

  PopupWindow {
    id: calendarPopup

    visible: root.calendarOpen
    anchor.item: root
    anchor.rect.x: Math.round((root.width - calendar.width) / 2)
    anchor.rect.y: root.height + 4
    anchor.rect.width: calendar.width
    anchor.rect.height: calendar.height
    anchor.edges: Edges.Top
    anchor.gravity: Edges.Bottom
    anchor.adjustment: PopupAdjustment.SlideX

    implicitWidth: calendar.width
    implicitHeight: calendar.height
    color: "transparent"

    RowLayout {
      id: calendar

      width: 714
      height: 196
      spacing: 8

      Repeater {
        model: [-1, 0, 1]

        Rectangle {
          required property int modelData

          property date monthDate: root.shiftedMonth(modelData)

          Layout.preferredWidth: 232
          Layout.preferredHeight: 196
          color: "#1a1b26"
          border.color: Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, modelData === 0 ? 0.4 : 0.24)
          border.width: 1
          radius: 0

          ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 8

            Text {
              Layout.fillWidth: true
              text: Qt.formatDateTime(monthDate, "MMMM yyyy")
              color: root.foreground
              font.family: root.fontFamily
              font.pixelSize: 13
              horizontalAlignment: Text.AlignHCenter
            }

            GridLayout {
              Layout.fillWidth: true
              columns: 7
              columnSpacing: 0
              rowSpacing: 0

              Repeater {
                model: root.weekdays

                Text {
                  required property string modelData

                  Layout.preferredWidth: 30
                  Layout.preferredHeight: 20
                  text: modelData
                  color: Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.62)
                  font.family: root.fontFamily
                  font.pixelSize: 10
                  horizontalAlignment: Text.AlignHCenter
                  verticalAlignment: Text.AlignVCenter
                }
              }
            }

            GridLayout {
              Layout.fillWidth: true
              columns: 7
              columnSpacing: 0
              rowSpacing: 1

              Repeater {
                model: 42

                Item {
                  required property int index

                  property int day: root.dayForMonthCell(monthDate, index)

                  Layout.preferredWidth: 30
                  Layout.preferredHeight: 20

                  Rectangle {
                    anchors.centerIn: parent
                    width: 24
                    height: 18
                    visible: parent.day > 0 && root.isTodayInMonth(monthDate, parent.day)
                    color: "transparent"
                    border.color: root.foreground
                    border.width: 1
                    radius: 0
                  }

                  Text {
                    anchors.centerIn: parent
                    text: parent.day > 0 ? String(parent.day) : ""
                    color: root.foreground
                    font.family: root.fontFamily
                    font.pixelSize: 11
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                  }
                }
              }
            }
          }
        }
      }
    }
  }

  Timer {
    interval: 1000
    running: true
    repeat: true
    onTriggered: root.now = new Date()
  }
}
