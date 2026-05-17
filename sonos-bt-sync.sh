#!/bin/bash
# Sonos BT Sync Daemon
# Vérifie toutes les 30s si Bureau Haut Gauche reçoit du Bluetooth.
# Si nouvelle connexion BT détectée → sync volume sur toutes les enceintes.

PYTHON="$HOME/.openclaw/workspace/.venvs/sonos/bin/python3"
SONOS_SCRIPT="$HOME/.openclaw/workspace/scripts/sonos.py"
STATE_FILE="/tmp/sonos-bt-sync.state"
LOG_FILE="/tmp/sonos-bt-sync.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

# Init state
if [ ! -f "$STATE_FILE" ]; then
    echo "disconnected" > "$STATE_FILE"
fi

log "Daemon démarré (mode Sonos BT check)"

while true; do
    # Check si Bureau Haut Gauche est en mode Bluetooth via SoCo
    BT_ACTIVE=$("$PYTHON" -c "
import json, os, soco
try:
    cache = os.path.expanduser('~/.openclaw/workspace/scripts/sonos_speakers.json')
    with open(cache) as f:
        ips = json.load(f)
    bhg = soco.SoCo(ips['Bureau Haut Gauche'])
    media = bhg.get_current_media_info()
    if 'bluetooth' in (media.get('channel','') + media.get('uri','')).lower():
        print('yes')
    else:
        print('no')
except:
    print('error')
" 2>/dev/null)

    PREV_STATE=$(cat "$STATE_FILE" 2>/dev/null)

    if [ "$BT_ACTIVE" = "yes" ] && [ "$PREV_STATE" = "disconnected" ]; then
        log "🔗 Bluetooth actif sur Bureau Haut Gauche → sync + groupement"
        sleep 3
        OUTPUT=$("$PYTHON" "$SONOS_SCRIPT" partout 2>&1)
        log "$OUTPUT"
        OUTPUT=$("$PYTHON" "$SONOS_SCRIPT" sync 2>&1)
        log "$OUTPUT"
        echo "connected" > "$STATE_FILE"
    elif [ "$BT_ACTIVE" = "no" ] && [ "$PREV_STATE" = "connected" ]; then
        log "📴 Bluetooth déconnecté de Bureau Haut Gauche"
        echo "disconnected" > "$STATE_FILE"
    fi

    sleep 5
done
