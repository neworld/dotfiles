#!/usr/bin/env python3

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


WEEK_SECONDS = 7 * 24 * 60 * 60


def run_status(provider: str) -> dict:
    if provider == "codex":
        command = ["codexbar", "--format", "{session_pct}% · {weekly_pct}%"]
    elif provider == "anthropic":
        command = [
            "ai-usagebar",
            "--vendor",
            "anthropic",
            "--format",
            "{session_pct}% · {weekly_pct}%",
            "--json",
        ]
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    result = subprocess.run(command, capture_output=True, text=True, timeout=20)
    output = result.stdout.strip()
    if not output:
        raise RuntimeError(result.stderr.strip() or "Usage command returned no output")
    return json.loads(output.splitlines()[-1])


def parse_reset_at(value: str) -> float:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def usage_data(provider: str) -> tuple[float, float, float]:
    cache_root = Path.home() / ".cache"

    if provider == "codex":
        data = json.loads((cache_root / "codexbar" / "usage.json").read_text())
        rate_limit = data["rate_limit"]
        session = float(rate_limit["primary_window"]["used_percent"])
        weekly = rate_limit["secondary_window"]
        weekly_used = float(weekly["used_percent"])
        seconds_left = float(weekly.get("reset_after_seconds", 0))
        window_seconds = float(weekly.get("limit_window_seconds", WEEK_SECONDS))
    else:
        data = json.loads(
            (cache_root / "ai-usagebar" / "anthropic" / "usage.json").read_text()
        )
        session = float(data["five_hour"]["utilization"])
        weekly = data["seven_day"]
        weekly_used = float(weekly["utilization"])
        seconds_left = parse_reset_at(weekly["resets_at"]) - time.time()
        window_seconds = WEEK_SECONDS

    return session, weekly_used, max(0.0, seconds_left / window_seconds)


def weekly_pressure(weekly_used: float, time_left_fraction: float) -> int:
    quota_left_fraction = max(0.0, 1.0 - weekly_used / 100.0)
    if quota_left_fraction == 0:
        return 100

    # 50% is an even spending pace. Lower means more quota is available for
    # the remaining time; higher means the provider should be conserved.
    pressure = 50.0 * time_left_fraction / quota_left_fraction
    return round(min(100.0, max(0.0, pressure)))


def status_class(session_used: float, pressure: int) -> str:
    constrained_by = max(session_used, pressure)
    if constrained_by >= 90:
        return "high"
    if constrained_by >= 70:
        return "medium"
    return "low"


def main() -> None:
    provider = sys.argv[1] if len(sys.argv) == 2 else ""
    payload = run_status(provider)

    try:
        session_used, weekly_used, time_left_fraction = usage_data(provider)
        pressure = weekly_pressure(weekly_used, time_left_fraction)
        paused = " ⏸" if "⏸" in str(payload.get("text", "")) else ""
        payload["text"] = f"{round(session_used)}% · {pressure}%{paused}"
        payload["class"] = status_class(session_used, pressure)
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError):
        # Keep the provider's normal output if its cache format changes.
        pass

    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
