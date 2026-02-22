#!/usr/bin/env python3
"""Philips Hue control script for OpenClaw."""

import sys
import json
import urllib.request

BRIDGE = "192.168.1.39"
API_KEY = "NMr0w5iaXgcr5QSqYKjn5UcvVzepCkTE4rqjCUYB"

# Zones/Rooms
GROUPS = {
    "accueil": "86",
    "sdb": "81",
    "toilette": "82",
    "cuisine": "83",
    "sejour": "84",
    "lit": "85",
    "bureau": "87",
    "fond": "88",
    "chambre": "89",
    "studio": "90",
}

# Scénarios Accueil (zone 86)
SCENES_ACCUEIL = {
    "crepuscule": "MJxBwt1WNe92sUIB",
    "nuit": "TS-3pHiEA4QA8fEi",
    "lumineux": "1RZnf5eEGJ2f176d",
}

def api(method, path, data=None):
    url = f"http://{BRIDGE}/api/{API_KEY}/{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read())

def cmd_scene(name):
    """Active un scénario Accueil."""
    key = name.lower().replace("é", "e").replace("è", "e")
    sid = SCENES_ACCUEIL.get(key)
    if not sid:
        print(f"⚠️ Scénario inconnu: {name}")
        print(f"Disponibles: {', '.join(SCENES_ACCUEIL.keys())}")
        return
    api("PUT", f"groups/86/action", {"scene": sid})
    print(f"✅ Scénario '{name}' activé sur Accueil")

def cmd_on(zone):
    """Allume une zone."""
    gid = GROUPS.get(zone.lower())
    if not gid:
        print(f"⚠️ Zone inconnue: {zone}")
        print(f"Disponibles: {', '.join(GROUPS.keys())}")
        return
    api("PUT", f"groups/{gid}/action", {"on": True})
    print(f"💡 {zone} allumé")

def cmd_off(zone):
    """Éteint une zone."""
    gid = GROUPS.get(zone.lower())
    if not gid:
        print(f"⚠️ Zone inconnue: {zone}")
        print(f"Disponibles: {', '.join(GROUPS.keys())}")
        return
    api("PUT", f"groups/{gid}/action", {"on": False})
    print(f"⬛ {zone} éteint")

def cmd_all_on():
    """Allume tout (Accueil = toutes les lumières)."""
    api("PUT", "groups/86/action", {"on": True})
    print("💡 Tout allumé")

def cmd_all_off():
    """Éteint tout."""
    api("PUT", "groups/86/action", {"on": False})
    print("⬛ Tout éteint")

def cmd_bri(zone, val):
    """Règle la luminosité d'une zone (0-100)."""
    gid = GROUPS.get(zone.lower())
    if not gid:
        print(f"⚠️ Zone inconnue: {zone}")
        return
    bri = max(1, min(254, int(int(val) * 254 / 100)))
    api("PUT", f"groups/{gid}/action", {"on": True, "bri": bri})
    print(f"🔆 {zone} → {val}%")

def cmd_bri_all(val):
    """Règle la luminosité de tout (Accueil)."""
    bri = max(1, min(254, int(int(val) * 254 / 100)))
    api("PUT", "groups/86/action", {"on": True, "bri": bri})
    print(f"🔆 Tout → {val}%")

def cmd_status():
    """Statut de toutes les zones."""
    for name, gid in sorted(GROUPS.items()):
        data = api("GET", f"groups/{gid}")
        state = data.get("state", {})
        any_on = state.get("any_on", False)
        all_on = state.get("all_on", False)
        icon = "💡" if all_on else ("🔅" if any_on else "⬛")
        print(f"{icon} {name}")

COMMANDS = {
    "crepuscule": lambda: cmd_scene("crepuscule"),
    "nuit": lambda: cmd_scene("nuit"),
    "lumineux": lambda: cmd_scene("lumineux"),
    "on": cmd_on,
    "off": cmd_off,
    "tout_on": cmd_all_on,
    "tout_off": cmd_all_off,
    "bri": cmd_bri,
    "bri_all": cmd_bri_all,
    "status": cmd_status,
}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Commandes:")
        print("  Scénarios Accueil : crepuscule, nuit, lumineux")
        print("  Zones : on <zone>, off <zone>")
        print("  Luminosité : bri <zone> <0-100>, bri_all <0-100>")
        print("  Tout : tout_on, tout_off")
        print("  Info : status")
        print(f"  Zones: {', '.join(GROUPS.keys())}")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd in ("on", "off"):
        if len(sys.argv) < 3:
            print(f"Usage: hue {cmd} <zone>")
            sys.exit(1)
        COMMANDS[cmd](sys.argv[2])
    elif cmd == "bri":
        if len(sys.argv) < 4:
            print("Usage: hue bri <zone> <0-100>")
            sys.exit(1)
        cmd_bri(sys.argv[2], sys.argv[3])
    elif cmd == "bri_all":
        if len(sys.argv) < 3:
            print("Usage: hue bri_all <0-100>")
            sys.exit(1)
        cmd_bri_all(sys.argv[2])
    elif cmd in COMMANDS:
        COMMANDS[cmd]()
    else:
        print(f"Commande inconnue: {cmd}")
        sys.exit(1)
