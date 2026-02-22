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

- Python 3
- [SoCo](https://github.com/SoCo/SoCo) (`pip install soco`)
- A Sonos speaker with Bluetooth (Era 100, Era 300, Move, Roam...)

### Configuration

Edit `sonos.py` to match your speaker names:

```python
# In get_coord(), change to your BT receiver speaker name:
def get_coord():
    return get_speakers()["Bureau Haut Gauche"]  # ← your BT speaker
```

Edit `sonos-bt-sync.sh` to set your paths:

```bash
PYTHON="/path/to/your/python3"        # Python with SoCo installed
SONOS_SCRIPT="/path/to/sonos.py"
```

### Run the daemon

```bash
# Start in background
nohup bash sonos-bt-sync.sh &

# Check logs
tail -f /tmp/sonos-bt-sync.log
```

### Run at startup (macOS)

Create a LaunchAgent plist to start the daemon automatically on login.

## Manual Controls

`sonos.py` also works as a standalone CLI:

```bash
python3 sonos.py sync          # Sync all volumes to match BT speaker
python3 sonos.py partout       # Group all speakers + play
python3 sonos.py bureau        # Office mode (boost nearby speakers)
python3 sonos.py volume 40     # Set all speakers to volume 40
python3 sonos.py mute_sauf X   # Mute everything except speaker X
python3 sonos.py stop           # Pause everywhere
python3 sonos.py play           # Resume playback
python3 sonos.py status         # Show all speakers status
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
