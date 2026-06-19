#!/usr/bin/env python3
"""Sonos control script for OpenClaw."""

import sys
import os
import json
import soco

if sys.stdout is not None and sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

BT_SPEAKER_NAME = "Bureau Haut Gauche"

SPEAKERS = None
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sonos_speakers.json")

def get_speakers():
    global SPEAKERS
    if SPEAKERS is None:
        with open(CACHE_FILE) as f:
            ips = json.load(f)
        SPEAKERS = {name: soco.SoCo(ip) for name, ip in ips.items()}
    return SPEAKERS

def get_coord():
    return get_speakers()[BT_SPEAKER_NAME]


def detect_source(speaker=None):
    """Detect the audio source type on the BT speaker (or given speaker).

    Returns 'bt', 'linein', or None for idle/other sources (streaming, AirPlay...).
    """
    if speaker is None:
        speaker = get_coord()
    try:
        media = speaker.get_current_media_info()
    except Exception:
        return None
    blob = ((media.get("channel") or "") + " " + (media.get("uri") or "")).lower()
    if "bluetooth" in blob:
        return "bt"
    if "line-in" in blob or "linein" in blob:
        return "linein"
    return None


def transport_is_playing(speaker=None):
    """True if the speaker is currently playing audio (vs. paused/stopped)."""
    if speaker is None:
        speaker = get_coord()
    try:
        ti = speaker.get_current_transport_info()
    except Exception:
        return False
    return ti.get("current_transport_state") == "PLAYING"


def group_missing(speaker=None):
    """Return the set of speaker names NOT currently in the speaker's group.

    Used by the daemon to detect group degradation while line-in is playing.
    """
    if speaker is None:
        speaker = get_coord()
    sp = get_speakers()
    expected = set(sp.keys())
    try:
        members = {m.player_name for m in speaker.group.members}
    except Exception:
        return set()
    return expected - members

def cmd_sync():
    """Calque le volume de toutes les enceintes sur le speaker BT.

    Returns: list of (name, exception) for speakers that failed.
    """
    import time
    sp = get_speakers()
    ref_vol = sp[BT_SPEAKER_NAME].volume

    def _apply(name, s):
        s.mute = False
        s.volume = ref_vol

    failures = []
    for name, s in sp.items():
        try:
            _apply(name, s)
        except Exception as e:
            failures.append((name, s, e))

    if failures:
        time.sleep(2)
        retried = []
        for name, s, _ in failures:
            try:
                _apply(name, s)
            except Exception as e:
                retried.append((name, e))
        failures = retried

    if failures:
        for name, e in failures:
            print(f"⚠️ {name}: {type(e).__name__}")
        print(f"⚠️ Sync partiel : {len(sp) - len(failures)}/{len(sp)} OK (ref {ref_vol})")
    else:
        print(f"✅ Toutes les enceintes à {ref_vol} (sync sur {BT_SPEAKER_NAME})")
    return [name for name, _ in failures]

DESK_SPEAKERS = [BT_SPEAKER_NAME, "Bureau Droite"]
DISTANT_SPEAKERS = ["Fond", "Salle de bain"]


def cmd_bureau():
    """Mode bureau : enceintes du bureau -10, enceintes distantes +12."""
    sp = get_speakers()
    base = sp[BT_SPEAKER_NAME].volume

    for name in DESK_SPEAKERS:
        s = sp[name]
        old = s.volume
        s.volume = max(0, base - 10)
        print(f"{name}: {old} → {s.volume}")

    for name in DISTANT_SPEAKERS:
        s = sp[name]
        old = s.volume
        s.volume = min(100, old + 12)
        s.mute = False
        print(f"{name}: {old} → {s.volume}")

    print("✅ Mode bureau activé")

def cmd_partout():
    """Groupe toutes les enceintes et lance la lecture.

    Returns: list of speaker names that failed to join.
    """
    import time
    sp = get_speakers()
    coord = get_coord()

    def _join(name, s):
        s.join(coord)
        s.mute = False

    others = [(name, s) for name, s in sp.items() if name != BT_SPEAKER_NAME]
    failures = []
    for name, s in others:
        try:
            _join(name, s)
        except Exception as e:
            failures.append((name, s, e))

    if failures:
        time.sleep(2)
        retried = []
        for name, s, _ in failures:
            try:
                _join(name, s)
            except Exception as e:
                retried.append((name, e))
        failures = retried

    try:
        coord.play()
    except Exception as e:
        print(f"⚠️ play() sur {BT_SPEAKER_NAME}: {type(e).__name__}")

    if failures:
        for name, e in failures:
            print(f"⚠️ {name}: {type(e).__name__}")
        print(f"⚠️ Groupement partiel : {len(others) - len(failures)}/{len(others)} OK")
    else:
        print("✅ Lecture sur toutes les enceintes")
    return [name for name, _ in failures]

def cmd_mute_sauf(keep):
    """Mute tout sauf l'enceinte spécifiée."""
    sp = get_speakers()
    found = False
    for name, s in sp.items():
        if name.lower() == keep.lower():
            s.mute = False
            found = True
            print(f"🔊 {name} — unmuted (vol: {s.volume})")
        else:
            s.mute = True
            print(f"🔇 {name} — muted")
    if not found:
        print(f"⚠️ Enceinte '{keep}' non trouvée")

def cmd_volume(vol):
    """Met toutes les enceintes au volume spécifié."""
    vol = int(vol)
    sp = get_speakers()
    for s in sp.values():
        s.mute = False
        s.volume = vol
    print(f"✅ Toutes les enceintes à {vol}")

def cmd_stop():
    """Pause partout."""
    get_coord().pause()
    print("⏸️ Pause")

def cmd_play():
    """Play."""
    get_coord().play()
    print("▶️ Lecture")

def cmd_status():
    """Affiche le statut de toutes les enceintes."""
    sp = get_speakers()
    for name in sorted(sp.keys()):
        s = sp[name]
        info = s.get_current_transport_info()
        state = info["current_transport_state"]
        muted = "🔇" if s.mute else "🔊"
        print(f"{muted} {name} — Vol: {s.volume} — {state}")

def cmd_bass_max():
    """Met les basses à +10 sur toutes les enceintes."""
    sp = get_speakers()
    for name, s in sp.items():
        s.bass = 10
        print(f"🔊 {name} — bass: +10")
    print("✅ Basses à fond partout")

def cmd_bass_off():
    """Remet les basses à 0 sur toutes les enceintes."""
    sp = get_speakers()
    for name, s in sp.items():
        s.bass = 0
        print(f"🔊 {name} — bass: 0")
    print("✅ Basses à zéro partout")

COMMANDS = {
    "sync": cmd_sync,
    "bureau": cmd_bureau,
    "partout": cmd_partout,
    "mute_sauf": cmd_mute_sauf,
    "volume": cmd_volume,
    "stop": cmd_stop,
    "play": cmd_play,
    "status": cmd_status,
    "bass_max": cmd_bass_max,
    "bass_off": cmd_bass_off,
}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Commandes: sync, bureau, partout, mute_sauf <nom>, volume <n>, stop, play, status")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd not in COMMANDS:
        print(f"Commande inconnue: {cmd}")
        sys.exit(1)

    if cmd in ("mute_sauf", "volume"):
        if len(sys.argv) < 3:
            print(f"Usage: sonos {cmd} <valeur>")
            sys.exit(1)
        COMMANDS[cmd](sys.argv[2])
    else:
        COMMANDS[cmd]()
