#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import deque
from pathlib import Path

import psutil


INTERVAL = 2.0
HISTORY_LEN = 40
NET_SCALE_BPS = 100_000_000 / 8
TEMP_MIN = 20.0
TEMP_MAX = 100.0


def clamp(value, low=0.0, high=100.0):
    return max(low, min(high, value))


def ram_usage(memory):
    used = max(0, memory.total - memory.available)
    percent = (used / memory.total) * 100 if memory.total > 0 else 0
    return used, percent


def fmt_rate(bytes_per_sec):
    mbps = (bytes_per_sec * 8) / 1_000_000
    if mbps >= 10:
        return f"{mbps:.0f} Mbps"
    return f"{mbps:.1f} Mbps"


def fmt_bytes(byte_count):
    if byte_count >= 1024 ** 4:
        return f"{byte_count / (1024 ** 4):.2f} TiB"
    if byte_count >= 1024 ** 3:
        return f"{byte_count / (1024 ** 3):.1f} GiB"
    if byte_count >= 1024 ** 2:
        return f"{byte_count / (1024 ** 2):.1f} MiB"
    return f"{byte_count / 1024:.0f} KiB"


def fmt_gib(bytes_value):
    return f"{bytes_value / (1024 ** 3):.1f} GiB"


def fmt_mib_as_gib(mib_value):
    return f"{mib_value / 1024:.1f} GiB"


def fmt_percent(value):
    return f"{clamp(value):.0f}%"


def fmt_load(value):
    return f"{value:.2f}"


def fmt_mbps(bytes_per_sec):
    mbps = clamp((bytes_per_sec * 8) / 1_000_000, 0, 99)
    return f"{mbps:.0f}m"


def fmt_temp(value):
    return f"{clamp(value, -99, 999):.0f}C"


def temp_percent(value):
    return clamp(((value - TEMP_MIN) / (TEMP_MAX - TEMP_MIN)) * 100.0)


def find_rapl_energy_file():
    base = Path("/sys/class/powercap")
    if not base.exists():
        return None

    for name_file in base.glob("intel-rapl:*/name"):
        try:
            name = name_file.read_text().strip().lower()
        except OSError:
            continue

        if name in {"package-0", "package-1", "package"} or name.startswith("package-"):
            energy_file = name_file.parent / "energy_uj"
            if energy_file.exists():
                return energy_file

    return None


def read_energy_uj(path):
    if path is None:
        return None
    try:
        return int(path.read_text().strip())
    except (OSError, ValueError):
        return None


def read_temperature():
    if not shutil.which("sensors"):
        return None

    try:
        result = subprocess.run(
            ["sensors"],
            check=False,
            capture_output=True,
            text=True,
            timeout=1.5,
        )
    except Exception:
        return None

    if result.returncode != 0:
        return None

    temps = []
    details = []
    cpu_temps = []
    cpu_details = []
    chip = ""
    lines = result.stdout.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            chip = ""
            continue

        if (
            not line.startswith(" ")
            and not line.startswith("\t")
            and index + 1 < len(lines)
            and lines[index + 1].strip().startswith("Adapter:")
        ):
            chip = stripped
            continue

        if stripped.startswith("Adapter:"):
            continue

        reading = line.split("(", 1)[0]
        match = re.search(r"([+-]?[0-9]+(?:\.[0-9]+)?)\s*°C", reading)
        if not match:
            continue

        try:
            temp = float(match.group(1))
        except ValueError:
            continue

        if -50.0 <= temp <= 150.0:
            temps.append(temp)
            label = reading.split(":", 1)[0].strip()
            if label:
                details.append((chip, label, temp))
                chip_lower = chip.lower()
                label_lower = label.lower()
                is_cpu = (
                    "k10temp" in chip_lower
                    or "amd tsi" in label_lower
                    or label_lower in {"tctl", "tdie"}
                    or label_lower.startswith("tccd")
                    or label_lower.startswith("package id")
                    or label_lower.startswith("core ")
                )
                if is_cpu:
                    cpu_temps.append(temp)
                    cpu_details.append((chip, label, temp))

    if not temps:
        return None

    return {
        "value": max(cpu_temps if cpu_temps else temps),
        "details": cpu_details if cpu_details else details,
    }


def temperature_tooltip(reading):
    if reading is None:
        return "Temperature: n/a"

    details = reading.get("details", [])
    if not details:
        return f"Temperature: {reading['value']:.1f}°C"

    lines = []
    for chip, label, temp in details:
        prefix = f"{chip} " if chip else ""
        lines.append(f"{prefix}{label}: {temp:.1f}°C")

    return "\n".join(lines)


def read_gpu():
    if not shutil.which("nvidia-smi"):
        return None

    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw",
                "--format=csv,noheader,nounits",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=1.5,
        )
    except Exception:
        return None

    if result.returncode != 0:
        return None

    process_count = 0
    try:
        process_result = subprocess.run(
            [
                "nvidia-smi",
                "--query-compute-apps=pid",
                "--format=csv,noheader,nounits",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=1.5,
        )
        if process_result.returncode == 0:
            process_count = len(
                [
                    line
                    for line in process_result.stdout.splitlines()
                    if line.strip() and line.strip().lower() != "no running processes found"
                ]
            )
    except Exception:
        process_count = 0

    first_line = result.stdout.strip().splitlines()[0:1]
    if not first_line:
        return None

    parts = [part.strip() for part in first_line[0].split(",")]
    if len(parts) < 5:
        return None

    try:
        memory_used = float(parts[1])
        memory_total = float(parts[2])
        memory = (memory_used / memory_total) * 100.0 if memory_total > 0 else 0.0
        try:
            power = float(parts[4])
        except ValueError:
            power = None

        return {
            "util": float(parts[0]),
            "memory": memory,
            "memory_used": memory_used,
            "memory_total": memory_total,
            "temp": float(parts[3]),
            "power": power,
            "process_count": process_count,
        }
    except ValueError:
        return None


def read_power_state():
    if shutil.which("powerprofilesctl"):
        try:
            result = subprocess.run(
                ["powerprofilesctl", "get"],
                check=False,
                capture_output=True,
                text=True,
                timeout=1.0,
            )
            if result.returncode == 0:
                profile = result.stdout.strip()
                if profile:
                    return profile
        except Exception:
            pass

    governor_path = Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
    try:
        governor = governor_path.read_text().strip()
    except OSError:
        return "n/a"

    return governor


def status_class(cpu, ram, temp):
    temp_score = temp if temp is not None else 0.0
    load = max(cpu, ram, temp_score)
    if load >= 85:
        return "high"
    if load >= 65:
        return "medium"
    return "low"


def rounded(values, scale=100.0):
    return [round(clamp(value, 0.0, scale), 1) for value in values]


def main():
    histories = {
        "cpu_util": deque(maxlen=HISTORY_LEN),
        "cpu_mem": deque(maxlen=HISTORY_LEN),
        "cpu_temp": deque(maxlen=HISTORY_LEN),
        "gpu_util": deque(maxlen=HISTORY_LEN),
        "gpu_mem": deque(maxlen=HISTORY_LEN),
        "gpu_temp": deque(maxlen=HISTORY_LEN),
        "net": deque(maxlen=HISTORY_LEN),
    }

    psutil.cpu_percent(interval=None)
    last_net = psutil.net_io_counters()
    last_time = time.monotonic()
    rapl_energy_file = find_rapl_energy_file()
    last_energy = read_energy_uj(rapl_energy_file)
    last_energy_time = last_time
    cpu_power = None
    temperature = None
    gpu = None
    probe_at = 0.0

    while True:
        now = time.monotonic()
        elapsed = max(now - last_time, 0.001)
        net = psutil.net_io_counters()

        cpu = psutil.cpu_percent(interval=None)
        load1, load5, load15 = os.getloadavg()
        power_state = read_power_state()
        memory = psutil.virtual_memory()
        ram_used, ram = ram_usage(memory)
        disk = psutil.disk_usage("/").percent

        down_bps = max(0.0, (net.bytes_recv - last_net.bytes_recv) / elapsed)
        up_bps = max(0.0, (net.bytes_sent - last_net.bytes_sent) / elapsed)
        net_bps = down_bps + up_bps
        net_arrow = "↑" if up_bps > down_bps else "↓"
        net_display_bps = max(down_bps, up_bps)

        last_net = net
        last_time = now

        energy = read_energy_uj(rapl_energy_file)
        if energy is not None and last_energy is not None:
            energy_delta = energy - last_energy
            if energy_delta >= 0:
                cpu_power = (energy_delta / 1_000_000) / max(now - last_energy_time, 0.001)
        if energy is not None:
            last_energy = energy
            last_energy_time = now

        if now >= probe_at:
            temperature = read_temperature()
            gpu = read_gpu()
            probe_at = now + 5.0

        temp = temperature["value"] if temperature is not None else None

        histories["cpu_util"].append(cpu)
        histories["cpu_mem"].append(ram)
        histories["net"].append(clamp(net_bps, 0.0, NET_SCALE_BPS))
        if temp is not None:
            histories["cpu_temp"].append(temp_percent(temp))
        if gpu is not None:
            histories["gpu_util"].append(gpu["util"])
            histories["gpu_mem"].append(gpu["memory"])
            histories["gpu_temp"].append(temp_percent(gpu["temp"]))

        series = [
            {
                "key": "cpu_util",
                "value": fmt_percent(cpu),
                "tooltip": "\n".join(
                    [
                        f"CPU usage: {cpu:.1f}%",
                        f"Power: {cpu_power:.1f} W" if cpu_power is not None else "Power: n/a",
                    ]
                ),
                "scale": 100,
                "values": rounded(histories["cpu_util"]),
            },
            {
                "key": "cpu_load",
                "value": fmt_load(load1),
                "tooltip": "\n".join(
                    [
                        f"Load average: {load1:.2f}, {load5:.2f}, {load15:.2f}",
                    ]
                ),
                "scale": 100,
                "values": [],
            },
            {
                "key": "cpu_power_state",
                "value": power_state,
                "tooltip": f"Power state: {power_state}",
                "scale": 100,
                "values": [],
            },
            {
                "key": "cpu_mem",
                "value": fmt_percent(ram),
                "tooltip": "\n".join(
                    [
                        f"RAM: {fmt_gib(ram_used)} / {fmt_gib(memory.total)}",
                        f"Usage: {ram:.1f}%",
                        f"Available: {fmt_gib(memory.available)}",
                    ]
                ),
                "scale": 100,
                "values": rounded(histories["cpu_mem"]),
            },
        ]

        if temp is not None:
            series.append(
                {
                    "key": "cpu_temp",
                    "value": fmt_temp(temp),
                    "tooltip": "\n".join(
                        [
                            f"CPU temperature: {temp:.1f}°C",
                            temperature_tooltip(temperature),
                        ]
                    ),
                    "scale": 100,
                    "values": rounded(histories["cpu_temp"]),
                }
            )

        if gpu is not None:
            series.extend(
                [
                    {
                        "key": "gpu_util",
                        "value": fmt_percent(gpu["util"]),
                        "tooltip": "\n".join(
                            [
                                f"GPU usage: {gpu['util']:.1f}%",
                                f"Power: {gpu['power']:.1f} W" if gpu["power"] is not None else "Power: n/a",
                                f"Processes: {gpu['process_count']}",
                            ]
                        ),
                        "scale": 100,
                        "values": rounded(histories["gpu_util"]),
                    },
                    {
                        "key": "gpu_mem",
                        "value": fmt_percent(gpu["memory"]),
                        "tooltip": "\n".join(
                            [
                                f"GPU memory: {fmt_mib_as_gib(gpu['memory_used'])} / {fmt_mib_as_gib(gpu['memory_total'])}",
                                f"Usage: {gpu['memory']:.1f}%",
                            ]
                        ),
                        "scale": 100,
                        "values": rounded(histories["gpu_mem"]),
                    },
                    {
                        "key": "gpu_temp",
                        "value": fmt_temp(gpu["temp"]),
                        "tooltip": f"GPU temperature: {gpu['temp']:.1f}°C",
                        "scale": 100,
                        "values": rounded(histories["gpu_temp"]),
                    },
                ]
            )

        series.append(
            {
                "key": "net",
                "value": f"{net_arrow}{fmt_mbps(net_display_bps)}",
                "tooltip": "\n".join(
                    [
                        f"Download: {fmt_rate(down_bps)}",
                        f"Upload: {fmt_rate(up_bps)}",
                        f"Total: {fmt_rate(net_bps)}",
                        f"Downloaded: {fmt_bytes(net.bytes_recv)}",
                        f"Uploaded: {fmt_bytes(net.bytes_sent)}",
                    ]
                ),
                "scale": NET_SCALE_BPS,
                "values": rounded(histories["net"], NET_SCALE_BPS),
            },
        )

        tooltip_lines = [
            f"CPU: {cpu:.1f}%",
            f"RAM: {ram:.1f}% ({ram_used / (1024 ** 3):.1f}/{memory.total / (1024 ** 3):.1f} GiB)",
            f"Network: down {fmt_rate(down_bps)}, up {fmt_rate(up_bps)}",
            f"Disk /: {disk:.1f}%",
        ]
        if gpu is not None:
            tooltip_lines.append(
                "GPU: "
                f"{gpu['util']:.1f}%, "
                f"{gpu['memory']:.1f}% "
                f"({gpu['memory_used'] / 1024:.1f}/{gpu['memory_total'] / 1024:.1f} GiB), "
                f"{gpu['temp']:.0f}°C"
            )
        tooltip_lines.append(temperature_tooltip(temperature))

        payload = {
            "class": status_class(cpu, ram, temp),
            "series": series,
            "tooltip": "\n".join(tooltip_lines),
        }
        print(json.dumps(payload, ensure_ascii=False), flush=True)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(0)
