#!/usr/bin/env python3
"""Sonos BT Sync Daemon (cross-platform).

Polls the main BT-receiver Sonos speaker every POLL_SECONDS. When a new
Bluetooth connection is detected, groups all speakers and syncs volume.

Data files (logs + state) live in a per-user data dir:
  - Windows: %LOCALAPPDATA%\\sonos-bt-sync\\
  - macOS / Linux: $XDG_DATA_HOME/sonos-bt-sync/ (default: ~/.local/share/sonos-bt-sync/)
"""

import json
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

import soco

import sonos as sonos_cli

POLL_SECONDS = 5
STABILIZE_SECONDS = 3
MAX_LOG_BYTES = 1_000_000

REPO_DIR = Path(__file__).resolve().parent
SPEAKERS_FILE = REPO_DIR / "sonos_speakers.json"


def data_dir() -> Path:
    if sys.platform == "win32":
        base = os.getenv("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    else:
        base = os.getenv("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    d = Path(base) / "sonos-bt-sync"
    d.mkdir(parents=True, exist_ok=True)
    return d


DATA_DIR = data_dir()
LOG_FILE = DATA_DIR / "sonos-bt-sync.log"
STATE_FILE = DATA_DIR / "sonos-bt-sync.state"


def log(msg: str) -> None:
    line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {msg}\n"
    try:
        if LOG_FILE.exists() and LOG_FILE.stat().st_size > MAX_LOG_BYTES:
            LOG_FILE.replace(LOG_FILE.with_suffix(".log.old"))
    except OSError:
        pass
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line)
    if sys.stdout is not None:
        try:
            print(line, end="", flush=True)
        except (OSError, ValueError):
            pass


def read_state() -> str:
    try:
        return STATE_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return "disconnected"


def write_state(state: str) -> None:
    STATE_FILE.write_text(state, encoding="utf-8")


def load_bt_speaker_ip() -> str:
    with SPEAKERS_FILE.open(encoding="utf-8") as f:
        ips = json.load(f)
    name = sonos_cli.BT_SPEAKER_NAME
    if name not in ips:
        raise KeyError(f"Speaker '{name}' not in {SPEAKERS_FILE}. Run discover.py.")
    return ips[name]


def bt_is_active(ip: str) -> bool:
    bhg = soco.SoCo(ip)
    media = bhg.get_current_media_info()
    blob = (media.get("channel", "") + media.get("uri", "")).lower()
    return "bluetooth" in blob


_stop = False


def _handle_stop(signum, frame):
    global _stop
    _stop = True


def main() -> int:
    signal.signal(signal.SIGINT, _handle_stop)
    signal.signal(signal.SIGTERM, _handle_stop)

    if sys.stdout is not None and sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass

    if not SPEAKERS_FILE.exists():
        log(f"ERROR: {SPEAKERS_FILE} not found. Run `python discover.py` first.")
        return 1

    bt_ip = load_bt_speaker_ip()
    log(f"Daemon started (BT speaker: {sonos_cli.BT_SPEAKER_NAME} @ {bt_ip}, poll={POLL_SECONDS}s)")

    if not STATE_FILE.exists():
        write_state("disconnected")

    while not _stop:
        try:
            active = bt_is_active(bt_ip)
        except Exception as e:
            log(f"WARN: speaker probe failed ({type(e).__name__}: {e}); retrying")
            for _ in range(POLL_SECONDS):
                if _stop:
                    break
                time.sleep(1)
            continue

        prev = read_state()

        if active and prev == "disconnected":
            log("BT active on main speaker -> grouping + syncing")
            time.sleep(STABILIZE_SECONDS)
            try:
                sonos_cli.SPEAKERS = None
                partout_failures = sonos_cli.cmd_partout() or []
                sonos_cli.SPEAKERS = None
                sync_failures = sonos_cli.cmd_sync() or []
                all_failures = set(partout_failures) | set(sync_failures)
                if all_failures:
                    log(f"WARN: partial sync, failed: {sorted(all_failures)}; will retry next poll")
                else:
                    log("Sync OK on all speakers")
                    write_state("connected")
            except Exception as e:
                log(f"WARN: sync crashed ({type(e).__name__}: {e}); will retry next poll")
        elif not active and prev == "connected":
            log("BT disconnected from main speaker")
            write_state("disconnected")

        for _ in range(POLL_SECONDS):
            if _stop:
                break
            time.sleep(1)

    log("Daemon stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
