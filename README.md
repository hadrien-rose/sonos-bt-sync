# Sonos Bluetooth Auto-Sync

**Automatically sync volume and group all Sonos speakers when your phone connects via Bluetooth.**

## The Problem

If you use a Sonos speaker as a Bluetooth receiver (e.g. Sonos Era 100), every time you connect your phone:

- 🔇 **Other grouped speakers stay silent** — they don't automatically rejoin the group
- 🔊 **Volume is inconsistent** — you have to manually adjust each speaker
- 😤 **Every. Single. Time.** — there's no native Sonos setting to fix this

This means after every Bluetooth reconnection, you need to:
1. Open the Sonos app
2. Re-group all your speakers
3. Adjust volumes manually

## The Solution

A lightweight daemon that polls your Sonos network every 5 seconds. When it detects a new Bluetooth connection on your main speaker, it automatically:

1. **Groups all speakers** together
2. **Starts playback** on all of them
3. **Syncs the volume** across every speaker

No app needed. No manual steps. Just connect your phone and everything works.

## Setup

### Requirements

- Python 3.9+
- A Sonos speaker with Bluetooth (Era 100, Era 300, Move, Roam...) on the same Wi-Fi network as this machine

### 1. Install

Clone the repo, create a virtualenv, install [SoCo](https://github.com/SoCo/SoCo):

```bash
# Windows (PowerShell)
git clone https://github.com/hadrien-rose/sonos-bt-sync.git
cd sonos-bt-sync
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install soco

# macOS / Linux
git clone https://github.com/hadrien-rose/sonos-bt-sync.git
cd sonos-bt-sync
python3 -m venv .venv
./.venv/bin/python -m pip install soco
```

### 2. Discover your speakers

`discover.py` auto-detects every Sonos on your network and writes `sonos_speakers.json`:

```bash
# Windows
.\.venv\Scripts\python.exe discover.py

# macOS / Linux
./.venv/bin/python discover.py
```

### 3. Set your BT speaker name

Open `sonos.py` and edit `BT_SPEAKER_NAME` (top of file) to match the Sonos speaker your phone connects to via Bluetooth:

```python
BT_SPEAKER_NAME = "Bureau Haut Gauche"   # ← change to your BT receiver
```

### 4. Run the daemon

```bash
# Windows
.\.venv\Scripts\python.exe sonos-bt-sync.py

# macOS / Linux
./.venv/bin/python sonos-bt-sync.py
```

Logs and state live in a per-user data dir:
- **Windows:** `%LOCALAPPDATA%\sonos-bt-sync\`
- **macOS / Linux:** `~/.local/share/sonos-bt-sync/` (or `$XDG_DATA_HOME/sonos-bt-sync/`)

### 5. Run at startup

**Windows** — drop a shortcut in the Startup folder:

```powershell
# Open the Startup folder
explorer shell:startup
```

Create a new shortcut in that folder pointing to:
- **Target:** `C:\path\to\sonos-bt-sync\.venv\Scripts\pythonw.exe C:\path\to\sonos-bt-sync\sonos-bt-sync.py`
- **Start in:** `C:\path\to\sonos-bt-sync`

`pythonw.exe` (instead of `python.exe`) runs without a console window.

**macOS** — create a LaunchAgent plist that runs `.venv/bin/python sonos-bt-sync.py` on login.

**Linux** — create a systemd user service that runs `.venv/bin/python sonos-bt-sync.py`.

## Manual Controls

`sonos.py` also works as a standalone CLI:

```bash
# Use the venv's python
python sonos.py sync          # Sync all volumes to match BT speaker
python sonos.py partout       # Group all speakers + play
python sonos.py bureau        # Office mode (boost nearby speakers)
python sonos.py volume 40     # Set all speakers to volume 40
python sonos.py mute_sauf X   # Mute everything except speaker X
python sonos.py stop          # Pause everywhere
python sonos.py play          # Resume playback
python sonos.py status        # Show all speakers status
```

## How it works

```
┌─────────────┐     Bluetooth      ┌──────────────────┐
│   Phone     │ ──────────────────▶ │  Main Speaker    │
└─────────────┘                     │  (Era 100)       │
                                    └──────┬───────────┘
                                           │
                              ┌────────────┼────────────┐
                              │   Daemon detects BT     │
                              │   connection (5s poll)   │
                              └────────────┬────────────┘
                                           │
                                    Auto-groups +
                                    syncs volume
                                           │
                    ┌──────────┬───────────┼───────────┬──────────┐
                    ▼          ▼           ▼           ▼          ▼
               ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
               │Speaker │ │Speaker │ │Speaker │ │Speaker │ │Speaker │
               │   2    │ │   3    │ │   4    │ │   5    │ │  ...   │
               └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
```

## License

MIT
