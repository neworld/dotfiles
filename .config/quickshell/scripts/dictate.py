#!/usr/bin/env python3
"""Click-to-dictate backend for the Quickshell mic widget.

Subcommands:
  listen   record the mic and stream the running transcript as JSON lines
           ({"text": "..."}) to stdout. Runs until killed (left-click stop).
  send T   refocus the window that was active when listening started, then
           type T into it via wtype.
  cancel   kill any recording / clean up (right-click cancel).

Live transcription keeps a whisper.cpp model resident via `whisper-server`
(started on demand and left warm), so each update is just an inference call
instead of a model reload. Audio is captured as raw PCM with `parec`; each tick
we wrap the buffer in a WAV header in-memory and POST it to the server.
"""

import glob
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import wave

RATE = 16000
PORT = int(os.environ.get("DICTATE_PORT", "8910"))
HOST = "127.0.0.1"
STEP_MS = int(os.environ.get("DICTATE_STEP_MS", "50"))  # idle poll while waiting for new audio
LANG_OVERRIDE = os.environ.get("DICTATE_LANG", "")  # ""=follow keyboard layout; "auto"=whisper detects

# xkb layout code -> whisper language code (only the layouts in use)
LAYOUT_TO_WHISPER = {
    "us": "en",
    "lt": "lt",
}

# Where to look for a ggml model, in preference order. Covers the AUR
# `whisper.cpp-model-*` packages (various layouts) plus a manual ~/.config drop.
MODEL_SIZES = ["small", "base", "medium", "large-v3-turbo", "large-v3", "tiny"]
MODEL_GLOBS = [
    "/usr/share/whisper.cpp-model-{size}/*.bin",
    "/usr/share/whisper.cpp/models/ggml-{size}*.bin",
    "/usr/share/whisper.cpp*/ggml-{size}*.bin",
    "/usr/share/whisper*/**/ggml-{size}*.bin",
    os.path.expanduser("~/.config/quickshell/models/ggml-{size}*.bin"),
    os.path.expanduser("~/.local/share/whisper*/**/ggml-{size}*.bin"),
]


def find_model():
    env = os.environ.get("DICTATE_MODEL")
    if env and os.path.exists(env):
        return env
    for size in MODEL_SIZES:
        for pat in MODEL_GLOBS:
            hits = glob.glob(pat.format(size=size), recursive=True)
            if hits:
                return sorted(hits)[0]
    return None


def keyboard_language():
    """Whisper language code following the active Hyprland keyboard layout."""
    if LANG_OVERRIDE:
        return LANG_OVERRIDE
    try:
        import json
        out = subprocess.run(
            ["hyprctl", "devices", "-j"],
            capture_output=True, text=True, timeout=1,
        ).stdout
        kbs = json.loads(out).get("keyboards", [])
        kb = next((k for k in kbs if k.get("main")), kbs[0] if kbs else None)
        if kb:
            layouts = [s.strip().lower() for s in kb.get("layout", "").split(",")]
            idx = kb.get("active_layout_index", 0)
            code = layouts[idx] if 0 <= idx < len(layouts) else ""
            if code:
                return LAYOUT_TO_WHISPER.get(code, code)
    except Exception:
        pass
    return "en"

RUNTIME = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "dictation")
RAW = os.path.join(RUNTIME, "rec.raw")
TARGET = os.path.join(RUNTIME, "target")
PAREC_PID = os.path.join(RUNTIME, "parec.pid")
SERVER_LOG = os.path.join(RUNTIME, "server.log")

MIN_BYTES = int(RATE * 0.3) * 2  # ~0.3s of 16-bit mono before first transcription


def emit(text):
    """Send one transcript update to the widget (single JSON line)."""
    # Hand-build JSON so we don't depend on escaping surprises; text is plain.
    safe = (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", " ")
        .replace("\r", " ")
        .replace("\t", " ")
    )
    sys.stdout.write('{"text":"' + safe + '"}\n')
    sys.stdout.flush()


def ensure_runtime():
    os.makedirs(RUNTIME, exist_ok=True)


def port_open():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex((HOST, PORT)) == 0


def ensure_server():
    """Start whisper-server if it isn't already listening. Returns True if ready."""
    if port_open():
        return True
    binary = shutil.which("whisper-server")
    if not binary:
        emit("⚠ whisper-server not found — install whisper-cpp-vulkan")
        return False
    model = find_model()
    if not model:
        emit("⚠ no whisper model found — install e.g. whisper.cpp-model-small")
        return False
    emit("… loading model …")
    with open(SERVER_LOG, "wb") as log:
        subprocess.Popen(
            [
                binary, "-m", model,
                "--host", HOST, "--port", str(PORT),
                "-t", "8",
            ],
            stdout=log, stderr=log, stdin=subprocess.DEVNULL,
            start_new_session=True,  # survive this process exiting -> stays warm
        )
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if port_open():
            return True
        time.sleep(0.25)
    emit("⚠ whisper-server did not start (see server.log)")
    return False


def save_target_window():
    try:
        out = subprocess.run(
            ["hyprctl", "activewindow", "-j"],
            capture_output=True, text=True, timeout=1,
        ).stdout
        import json
        addr = json.loads(out).get("address", "")
    except Exception:
        addr = ""
    with open(TARGET, "w") as f:
        f.write(addr)


def start_parec():
    raw = open(RAW, "wb")
    # --latency-msec keeps fragments small so audio is flushed to the file
    # frequently; otherwise parec buffers ~1s and that, not whisper, paces us.
    if shutil.which("parec"):
        cmd = ["parec", "--rate=%d" % RATE, "--channels=1", "--format=s16le",
               "--latency-msec=100"]
    else:  # fall back to parecord writing raw PCM
        cmd = ["parecord", "--rate=%d" % RATE, "--channels=1",
               "--file-format=raw", "--latency-msec=100", "/dev/stdout"]
    proc = subprocess.Popen(cmd, stdout=raw, stderr=subprocess.DEVNULL)
    with open(PAREC_PID, "w") as f:
        f.write(str(proc.pid))
    return proc, raw


def stop_parec(proc=None):
    if proc is not None:
        proc.terminate()
    else:
        try:
            with open(PAREC_PID) as f:
                os.kill(int(f.read().strip()), signal.SIGTERM)
        except Exception:
            pass


def wav_bytes(raw_path):
    try:
        with open(raw_path, "rb") as f:
            data = f.read()
    except FileNotFoundError:
        return None
    if len(data) < MIN_BYTES:
        return None
    if len(data) % 2:
        data = data[:-1]
    import io
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(data)
    return buf.getvalue()


def transcribe(wav, lang):
    tmp = os.path.join(RUNTIME, "snap.wav")
    with open(tmp, "wb") as f:
        f.write(wav)
    try:
        out = subprocess.run(
            [
                "curl", "-s", "--max-time", "20",
                "http://%s:%d/inference" % (HOST, PORT),
                "-F", "file=@%s" % tmp,
                "-F", "response_format=text",
                "-F", "temperature=0",
                "-F", "language=%s" % lang,
            ],
            capture_output=True, text=True,
        ).stdout
    except Exception:
        return None
    text = out.strip()
    # Drop pure non-speech annotations whisper emits on silence, e.g.
    # "[BLANK_AUDIO]", "[APPLAUSE]", "(speaking foreign language)".
    if re.fullmatch(r"[\[(].*[\])]", text):
        return ""
    return text


def cmd_listen():
    ensure_runtime()
    open(RAW, "wb").close()  # truncate
    save_target_window()
    if not ensure_server():
        return 1

    lang = keyboard_language()
    proc, raw = start_parec()

    stop = {"flag": False}

    def handle(_sig, _frame):
        stop["flag"] = True

    signal.signal(signal.SIGTERM, handle)
    signal.signal(signal.SIGINT, handle)

    last_text = ""
    last_size = 0
    try:
        while not stop["flag"]:
            try:
                size = os.path.getsize(RAW)
            except OSError:
                size = 0
            if size < MIN_BYTES or size == last_size:
                time.sleep(STEP_MS / 1000.0)  # nothing new to transcribe yet
                continue
            last_size = size
            wav = wav_bytes(RAW)
            if wav is None:
                continue
            # transcription itself (~1s) paces the loop — no extra sleep
            text = transcribe(wav, lang)
            if text and text != last_text:
                last_text = text
                emit(text)
    finally:
        stop_parec(proc)
        raw.close()
    return 0


def cmd_send(text):
    text = text.strip()
    if not text:
        return 0
    addr = ""
    try:
        with open(TARGET) as f:
            addr = f.read().strip()
    except FileNotFoundError:
        pass
    if addr:
        subprocess.run(
            ["hyprctl", "dispatch", "focuswindow", "address:" + addr],
            capture_output=True,
        )
        time.sleep(0.12)
    subprocess.run(["wtype", "--", text])
    return 0


def cmd_cancel():
    stop_parec()
    for path in (RAW, os.path.join(RUNTIME, "snap.wav")):
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
    return 0


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "listen"
    if action == "listen":
        return cmd_listen()
    if action == "send":
        return cmd_send(sys.argv[2] if len(sys.argv) > 2 else "")
    if action == "cancel":
        return cmd_cancel()
    sys.stderr.write("usage: dictate.py [listen|send TEXT|cancel]\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
