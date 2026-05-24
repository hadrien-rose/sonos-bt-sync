#!/usr/bin/env python3
"""Sonos control script for OpenClaw."""

import sys
import os
import json
import soco

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
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

def cmd_sync():
    """Calque le volume de toutes les enceintes sur le speaker BT."""
    sp = get_speakers()
    ref_vol = sp[BT_SPEAKER_NAME].volume
    for s in sp.values():
        s.mute = False
        s.volume = ref_vol
    print(f"✅ Toutes les enceintes à {ref_vol} (sync sur {BT_SPEAKER_NAME})")

def cmd_bureau():
    """Mode bureau : Fond et Barre De Son +12, speaker BT -10."""
    sp = get_speakers()
    bhg = sp[BT_SPEAKER_NAME]
    base = bhg.volume

    bhg.volume = max(0, base - 10)
    print(f"{BT_SPEAKER_NAME}: {base} → {bhg.volume}")

    for name in ["Fond", "Barre De Son"]:
        s = sp[name]
        old = s.volume
        s.volume = min(100, old + 12)
        s.mute = False
        print(f"{name}: {old} → {s.volume}")

    print("✅ Mode bureau activé")

def cmd_partout():
    """Groupe toutes les enceintes et lance la lecture."""
    sp = get_speakers()
    coord = get_coord()
    for name, s in sp.items():
        if name != BT_SPEAKER_NAME:
            s.join(coord)
            s.mute = False
    coord.play()
    print("✅ Lecture sur toutes les enceintes")

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
