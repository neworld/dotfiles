import Quickshell
import QtQuick

PopupWindow {
  id: root

  required property var anchorItem
  property string text: ""
  property color foreground: "#cdd6f4"
  property color background: "#1a1b26"
  property string fontFamily: "Noto Sans Mono"
  property int fontPixelSize: 12
  property bool richText: false

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function pangoToRichText(value) {
    return escapeHtml(value)
      .replace(/&lt;span font_weight=['"]bold['"] foreground=['"]([^'"]+)['"]&gt;/g, "<span style=\"color:$1; font-weight:bold\">")
      .replace(/&lt;span foreground=['"]([^'"]+)['"] font_weight=['"]bold['"]&gt;/g, "<span style=\"color:$1; font-weight:bold\">")
      .replace(/&lt;span foreground=['"]([^'"]+)['"]&gt;/g, "<span style=\"color:$1\">")
      .replace(/&lt;\/span&gt;/g, "</span>")
      .replace(/\n/g, "<br/>");
  }

  anchor.item: anchorItem
  anchor.rect.x: Math.round((anchorItem.width - tooltip.width) / 2)
  anchor.rect.y: anchorItem.height + 4
  anchor.rect.width: tooltip.width
  anchor.rect.height: tooltip.height
  anchor.edges: Edges.Top
  anchor.gravity: Edges.Bottom
  anchor.adjustment: PopupAdjustment.SlideX

  implicitWidth: tooltip.width
  implicitHeight: tooltip.height
  color: "transparent"

  Rectangle {
    id: tooltip

    width: label.implicitWidth + 12
    height: label.implicitHeight + 6
    color: root.background
    border.color: Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.28)
    border.width: 1
    radius: 0

    Text {
      id: label
      anchors.centerIn: parent
      text: root.richText ? "<pre style=\"margin:0; white-space:pre\">" + root.pangoToRichText(root.text) + "</pre>" : root.text
      color: root.foreground
      font.family: root.fontFamily
      font.pixelSize: root.fontPixelSize
      lineHeight: 1.15
      textFormat: root.richText ? Text.RichText : Text.PlainText
    }
  }
}
