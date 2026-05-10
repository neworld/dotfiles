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
  property string tooltipText: ""
  property string currentClass: "low"
  property var cpuMetricOrder: ["cpu_util", "cpu_mem", "cpu_temp"]
  property var gpuMetricOrder: ["gpu_util", "gpu_mem", "gpu_temp"]
  property var metrics: ({})
  property color graphColor: currentClass === "high" ? highForeground
    : currentClass === "medium" ? mediumForeground
    : lowForeground

  signal clicked()
  signal rightClicked()

  function metricColor(key) {
    const colors = {
      cpu_util: "#7aa2f7",
      gpu_util: "#7aa2f7",
      cpu_mem: "#9ece6a",
      gpu_mem: "#9ece6a",
      cpu_temp: "#f7768e",
      gpu_temp: "#f7768e",
      net: "#7dcfff",
    };
    return colors[key] || graphColor;
  }

  function metric(key) {
    return metrics[key] || ({ key: key, value: "", scale: 100, values: [] });
  }

  function compactValue(value) {
    const text = String(value || "");
    if (text.length >= 3) return text.slice(0, 3);
    return ("   " + text).slice(-3);
  }

  Layout.preferredWidth: metricsRow.implicitWidth + 15
  Layout.preferredHeight: 26
  Layout.fillHeight: true

  function applyPayload(line) {
    const trimmed = line.trim();
    if (trimmed.length === 0) return;

    try {
      const payload = JSON.parse(trimmed);
      const nextMetrics = {};
      for (let i = 0; i < (payload.series || []).length; i++) {
        const metric = payload.series[i];
        nextMetrics[metric.key] = metric;
      }

      root.currentClass = payload.class || "low";
      root.tooltipText = payload.tooltip || "";
      root.metrics = nextMetrics;
    } catch (error) {
      console.log("metrics parse error", error);
    }
  }

  Process {
    id: metricsProcess
    command: ["/home/neworld/.config/quickshell/scripts/metrics-stream.py"]
    running: true
    stdout: SplitParser {
      onRead: function(data) {
        root.applyPayload(data);
      }
    }
    onRunningChanged: if (!running) restart.start()
  }

  Timer {
    id: restart
    interval: 2000
    repeat: false
    onTriggered: metricsProcess.running = true
  }

  MouseArea {
    anchors.fill: parent
    acceptedButtons: Qt.LeftButton | Qt.RightButton
    onClicked: function(event) {
      if (event.button === Qt.RightButton) root.rightClicked();
      else root.clicked();
    }
  }

  RowLayout {
    id: metricsRow
    anchors.centerIn: parent
    spacing: 9

    RowLayout {
      spacing: 4
      Layout.preferredHeight: 18

      Text {
        text: "󰍛"
        color: root.foreground
        font.family: root.fontFamily
        font.pixelSize: 12
        verticalAlignment: Text.AlignVCenter
        Layout.alignment: Qt.AlignVCenter
      }

      Repeater {
        model: root.cpuMetricOrder

        RowLayout {
          required property string modelData

          property var metric: root.metric(modelData)

          spacing: 4
          Layout.preferredHeight: 14
          Layout.alignment: Qt.AlignVCenter
          visible: metric.values.length > 0

          Item {
            Layout.preferredWidth: 28
            Layout.preferredHeight: 14
            Layout.alignment: Qt.AlignVCenter

            Canvas {
              id: graph

              anchors.fill: parent

              property var values: metric.values || []
              property real scale: metric.scale || 100
              property color color: root.metricColor(metric.key)

              onValuesChanged: requestPaint()
              onScaleChanged: requestPaint()
              onColorChanged: requestPaint()
              onPaint: root.paintGraph(this, getContext("2d"), values, scale, color)
            }

            MouseArea {
              id: cpuGraphMouse

              anchors.fill: parent
              hoverEnabled: true
              acceptedButtons: Qt.NoButton
              BarTooltip {
                visible: cpuGraphMouse.containsMouse && String(metric.tooltip || metric.value || "").length > 0
                anchorItem: cpuGraphMouse
                text: String(metric.tooltip || metric.value || "")
                foreground: root.metricColor(metric.key)
                background: "#1a1b26"
                fontFamily: root.fontFamily
              }
            }
          }

          Text {
            text: root.compactValue(metric.value)
            color: root.metricColor(metric.key)
            font.family: root.fontFamily
            font.pixelSize: 12
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignRight
            leftPadding: 2
            rightPadding: 2
            Layout.preferredWidth: 24
            Layout.alignment: Qt.AlignVCenter
            transform: Translate { y: 2 }

            MouseArea {
              id: cpuLabelMouse

              anchors.fill: parent
              hoverEnabled: true
              acceptedButtons: Qt.NoButton
              BarTooltip {
                visible: cpuLabelMouse.containsMouse && String(metric.tooltip || metric.value || "").length > 0
                anchorItem: cpuLabelMouse
                text: String(metric.tooltip || metric.value || "")
                foreground: root.metricColor(metric.key)
                background: "#1a1b26"
                fontFamily: root.fontFamily
              }
            }
          }
        }
      }
    }

    RowLayout {
      spacing: 4
      Layout.preferredHeight: 18
      visible: root.metric("gpu_util").values.length > 0

      Text {
        text: "󰢮"
        color: root.foreground
        font.family: root.fontFamily
        font.pixelSize: 12
        verticalAlignment: Text.AlignVCenter
        Layout.alignment: Qt.AlignVCenter
      }

      Repeater {
        model: root.gpuMetricOrder

        RowLayout {
          required property string modelData

          property var metric: root.metric(modelData)

          spacing: 4
          Layout.preferredHeight: 14
          Layout.alignment: Qt.AlignVCenter
          visible: metric.values.length > 0

          Item {
            Layout.preferredWidth: 28
            Layout.preferredHeight: 14
            Layout.alignment: Qt.AlignVCenter

            Canvas {
              id: graph

              anchors.fill: parent

              property var values: metric.values || []
              property real scale: metric.scale || 100
              property color color: root.metricColor(metric.key)

              onValuesChanged: requestPaint()
              onScaleChanged: requestPaint()
              onColorChanged: requestPaint()
              onPaint: root.paintGraph(this, getContext("2d"), values, scale, color)
            }

            MouseArea {
              id: gpuGraphMouse

              anchors.fill: parent
              hoverEnabled: true
              acceptedButtons: Qt.NoButton
              BarTooltip {
                visible: gpuGraphMouse.containsMouse && String(metric.tooltip || metric.value || "").length > 0
                anchorItem: gpuGraphMouse
                text: String(metric.tooltip || metric.value || "")
                foreground: root.metricColor(metric.key)
                background: "#1a1b26"
                fontFamily: root.fontFamily
              }
            }
          }

          Text {
            text: root.compactValue(metric.value)
            color: root.metricColor(metric.key)
            font.family: root.fontFamily
            font.pixelSize: 12
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignRight
            leftPadding: 2
            rightPadding: 2
            Layout.preferredWidth: 24
            Layout.alignment: Qt.AlignVCenter
            transform: Translate { y: 2 }

            MouseArea {
              id: gpuLabelMouse

              anchors.fill: parent
              hoverEnabled: true
              acceptedButtons: Qt.NoButton
              BarTooltip {
                visible: gpuLabelMouse.containsMouse && String(metric.tooltip || metric.value || "").length > 0
                anchorItem: gpuLabelMouse
                text: String(metric.tooltip || metric.value || "")
                foreground: root.metricColor(metric.key)
                background: "#1a1b26"
                fontFamily: root.fontFamily
              }
            }
          }
        }
      }
    }

    RowLayout {
      spacing: 4
      Layout.preferredHeight: 18

      Text {
        text: "󰤨"
        color: root.foreground
        font.family: root.fontFamily
        font.pixelSize: 12
        verticalAlignment: Text.AlignVCenter
        Layout.alignment: Qt.AlignVCenter
      }

      Repeater {
        model: ["net"]

        RowLayout {
          required property string modelData

          property var metric: root.metric(modelData)

          spacing: 4
          Layout.preferredHeight: 14
          Layout.alignment: Qt.AlignVCenter
          visible: metric.values.length > 0

          Item {
            Layout.preferredWidth: 28
            Layout.preferredHeight: 14
            Layout.alignment: Qt.AlignVCenter

            Canvas {
              id: graph

              anchors.fill: parent

              property var values: metric.values || []
              property real scale: metric.scale || 100
              property color color: root.metricColor(metric.key)

              onValuesChanged: requestPaint()
              onScaleChanged: requestPaint()
              onColorChanged: requestPaint()
              onPaint: root.paintGraph(this, getContext("2d"), values, scale, color)
            }

            MouseArea {
              id: netGraphMouse

              anchors.fill: parent
              hoverEnabled: true
              acceptedButtons: Qt.NoButton
              BarTooltip {
                visible: netGraphMouse.containsMouse && String(metric.tooltip || metric.value || "").length > 0
                anchorItem: netGraphMouse
                text: String(metric.tooltip || metric.value || "")
                foreground: root.metricColor(metric.key)
                background: "#1a1b26"
                fontFamily: root.fontFamily
              }
            }
          }

          Text {
            text: String(metric.value || "")
            color: root.metricColor(metric.key)
            font.family: root.fontFamily
            font.pixelSize: 12
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignRight
            leftPadding: 2
            rightPadding: 2
            Layout.preferredWidth: 38
            Layout.alignment: Qt.AlignVCenter
            transform: Translate { y: 2 }

            MouseArea {
              id: netLabelMouse

              anchors.fill: parent
              hoverEnabled: true
              acceptedButtons: Qt.NoButton
              BarTooltip {
                visible: netLabelMouse.containsMouse && String(metric.tooltip || metric.value || "").length > 0
                anchorItem: netLabelMouse
                text: String(metric.tooltip || metric.value || "")
                foreground: root.metricColor(metric.key)
                background: "#1a1b26"
                fontFamily: root.fontFamily
              }
            }
          }
        }
      }
    }
  }

  function paintGraph(item, ctx, values, scale, color) {
    ctx.reset();
    ctx.clearRect(0, 0, item.width, item.height);

    const count = values.length;
    const maxBars = Math.floor(item.width);
    const start = Math.max(0, count - maxBars);
    const visibleValues = values.slice(start);

    ctx.fillStyle = Qt.rgba(root.foreground.r, root.foreground.g, root.foreground.b, 0.16);
    ctx.fillRect(0, item.height - 1, item.width, 1);
    ctx.fillStyle = color;

    for (let i = 0; i < visibleValues.length; i++) {
      const ratio = Math.max(0, Math.min(1, visibleValues[i] / scale));
      const barHeight = Math.max(1, Math.round(ratio * item.height));
      const x = item.width - visibleValues.length + i;
      const y = item.height - barHeight;
      ctx.fillRect(x, y, 1, barHeight);
    }
  }
}
