#!/usr/bin/env python3
import json
import importlib.util
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
BATTERY_REFRESH_TICKS = 5
HISTORY_LEN = 40
NET_SCALE_BPS = 100_000_000 / 8
TEMP_MIN = 20.0
TEMP_MAX = 100.0
PROCESS_PROBE_INTERVAL = 5.0
PROCESS_CPU_MIN_TOTAL_PERCENT = 30.0
PROCESS_MEMORY_MIN_PROCESS_RSS = 16 * 1024 ** 2
PROCESS_MEMORY_MIN_GROUP_RSS = 64 * 1024 ** 2
PROCESS_TOP_CPU_LIMIT = 3
PROCESS_TOP_MEMORY_LIMIT = 5


def load_battery_status_module():
    path = Path(__file__).with_name("battery-status.py")
    spec = importlib.util.spec_from_file_location("quickshell_battery_status", path)
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        return None
    return module


BATTERY_STATUS = load_battery_status_module()


def clamp(value, low=0.0, high=100.0):
    return max(low, min(high, value))


def read_zfs_arc_reclaimable():
    arcstats = Path("/proc/spl/kstat/zfs/arcstats")
    if not arcstats.is_file():
        return 0

    values = {}
    try:
        for line in arcstats.read_text().splitlines():
            parts = line.split()
            if len(parts) >= 3 and parts[0] in {"size", "c_min"}:
                values[parts[0]] = int(parts[2])
    except (OSError, ValueError):
        return 0

    return max(0, values.get("size", 0) - values.get("c_min", 0))


def read_meminfo_value(name):
    try:
        with open("/proc/meminfo", "r", encoding="ascii") as meminfo:
            prefix = f"{name}:"
            for line in meminfo:
                if line.startswith(prefix):
                    return int(line.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
        pass
    return 0


def read_battery_devices():
    if BATTERY_STATUS is None:
        return []

    try:
        return BATTERY_STATUS.read_battery_devices()
    except Exception:
        return []


def ram_usage(memory):
    arc_reclaimable = read_zfs_arc_reclaimable()
    sreclaimable = read_meminfo_value("SReclaimable")
    buffers = getattr(memory, "buffers", 0)
    cached = getattr(memory, "cached", 0)
    shared = getattr(memory, "shared", 0)
    non_arc_cache_excluded = max(0, buffers + cached + sreclaimable - shared)
    cache_excluded = non_arc_cache_excluded + arc_reclaimable
    used = max(0, memory.total - memory.free - cache_excluded)
    usable = max(0, memory.total - used)
    percent = (used / memory.total) * 100 if memory.total > 0 else 0
    return used, percent, usable, cache_excluded, non_arc_cache_excluded, arc_reclaimable


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


def fmt_process_bytes(bytes_value):
    if bytes_value >= 1024 ** 3:
        return f"{bytes_value / (1024 ** 3):.1f} GiB"
    return f"{bytes_value / (1024 ** 2):.0f} MiB"


def fmt_mib_as_gib(mib_value):
    return f"{mib_value / 1024:.1f} GiB"


def fmt_percent(value):
    return f"{clamp(value):.0f}%"


def fmt_load(value):
    return f"{value:.2f}"


def fmt_net_display(bytes_per_sec):
    mbps = max(0, int(((bytes_per_sec * 8) / 1_000_000) + 0.5))
    if mbps < 100:
        return f"{mbps}m"
    return f"{min(mbps, 999)}"


def net_direction(down_bps, up_bps):
    return "↑" if up_bps > down_bps else "↓"


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


def process_label(name):
    cleaned = (name or "").strip()
    if cleaned.startswith("[") and cleaned.endswith("]"):
        return ""
    return cleaned or "unknown"


def read_process_summary(cpu_samples, last_scan_at, now, cpu_count):
    elapsed = now - last_scan_at if last_scan_at is not None else 0.0
    next_cpu_samples = {}
    cpu_by_name = {}
    memory_by_name = {}
    count_by_name = {}

    for proc in psutil.process_iter(["pid", "name", "cpu_times", "memory_info"]):
        try:
            info = proc.info
            label = process_label(info.get("name"))
            if not label:
                continue

            cpu_times = info.get("cpu_times")
            process_time = (cpu_times.user + cpu_times.system) if cpu_times is not None else None
            if process_time is not None:
                pid = info["pid"]
                next_cpu_samples[pid] = process_time
                previous_time = cpu_samples.get(pid)
                if previous_time is not None and elapsed > 0:
                    delta = process_time - previous_time
                    if delta > 0:
                        cpu_percent = (delta / elapsed / cpu_count) * 100.0
                        if cpu_percent > 0:
                            cpu_by_name[label] = cpu_by_name.get(label, 0.0) + cpu_percent

            memory_info = info.get("memory_info")
            rss = memory_info.rss if memory_info is not None else 0
            if rss >= PROCESS_MEMORY_MIN_PROCESS_RSS:
                memory_by_name[label] = memory_by_name.get(label, 0) + rss
                count_by_name[label] = count_by_name.get(label, 0) + 1
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess, OSError):
            continue

    top_cpu = [
        {"name": name, "cpu": value}
        for name, value in sorted(cpu_by_name.items(), key=lambda item: item[1], reverse=True)
        if value >= PROCESS_CPU_MIN_TOTAL_PERCENT
    ][:PROCESS_TOP_CPU_LIMIT]

    top_memory = []
    memory_entries = [
        (name, value)
        for name, value in sorted(memory_by_name.items(), key=lambda item: item[1], reverse=True)
        if value >= PROCESS_MEMORY_MIN_GROUP_RSS
    ][:PROCESS_TOP_MEMORY_LIMIT]
    for name, value in memory_entries:
        top_memory.append(
            {
                "name": name,
                "rss": value,
                "count": count_by_name.get(name, 0),
            }
        )

    return {
        "top_cpu": top_cpu,
        "top_memory": top_memory,
        "cpu_samples": next_cpu_samples,
    }


def process_name_with_count(item):
    count = item.get("count", 0)
    if count > 1:
        return f"{item['name']} x{count}"
    return item["name"]


def top_cpu_lines(process_summary):
    entries = process_summary.get("top_cpu", [])
    if not entries:
        return []

    lines = ["Top CPU:"]
    for item in entries:
        lines.append(f"  {item['name']}: {item['cpu']:.1f}% total")
    return lines


def top_memory_lines(process_summary):
    entries = process_summary.get("top_memory", [])
    if not entries:
        return []

    lines = ["Top memory (RSS):"]
    for item in entries:
        lines.append(f"  {process_name_with_count(item)}: {fmt_process_bytes(item['rss'])}")
    return lines


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
    process_probe_at = 0.0
    process_scan_at = None
    process_cpu_samples = {}
    process_summary = {"top_cpu": [], "top_memory": []}
    cpu_count = max(1, psutil.cpu_count() or 1)
    tick = 0
    battery_devices = []

    while True:
        now = time.monotonic()
        elapsed = max(now - last_time, 0.001)
        net = psutil.net_io_counters()

        cpu = psutil.cpu_percent(interval=None)
        load1, load5, load15 = os.getloadavg()
        power_state = read_power_state()
        memory = psutil.virtual_memory()
        ram_used, ram, ram_usable, ram_cache_excluded, ram_non_arc_cache_excluded, ram_arc_reclaimable = ram_usage(memory)
        disk = psutil.disk_usage("/").percent

        down_bps = max(0.0, (net.bytes_recv - last_net.bytes_recv) / elapsed)
        up_bps = max(0.0, (net.bytes_sent - last_net.bytes_sent) / elapsed)
        net_bps = down_bps + up_bps
        net_arrow = net_direction(down_bps, up_bps)
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

        if now >= process_probe_at:
            process_summary = read_process_summary(process_cpu_samples, process_scan_at, now, cpu_count)
            process_cpu_samples = process_summary.pop("cpu_samples", {})
            process_scan_at = now
            process_probe_at = now + PROCESS_PROBE_INTERVAL

        if tick % BATTERY_REFRESH_TICKS == 0:
            battery_devices = read_battery_devices()

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
                    + top_cpu_lines(process_summary)
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
                        f"RAM used: {fmt_gib(ram_used)} / {fmt_gib(memory.total)}",
                        f"Usage: {ram:.1f}%",
                        f"Usable: {fmt_gib(ram_usable)}",
                        f"Cache excluded: {fmt_gib(ram_cache_excluded)} total",
                        f"  regular cache: {fmt_gib(ram_non_arc_cache_excluded)}",
                        f"  ZFS ARC: {fmt_gib(ram_arc_reclaimable)}",
                    ]
                    + top_memory_lines(process_summary)
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
                "value": fmt_net_display(net_display_bps),
                "direction": net_arrow,
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
            f"RAM: {ram:.1f}% ({ram_used / (1024 ** 3):.1f}/{memory.total / (1024 ** 3):.1f} GiB, {ram_usable / (1024 ** 3):.1f} GiB usable)",
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
            "batteryDevices": battery_devices,
        }
        print(json.dumps(payload, ensure_ascii=False), flush=True)
        tick += 1
        time.sleep(INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(0)
