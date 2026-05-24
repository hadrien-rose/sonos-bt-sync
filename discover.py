#!/usr/bin/env python3
"""Auto-discover Sonos speakers on the local network and write sonos_speakers.json."""

import json
import sys
from pathlib import Path

import soco

OUTPUT = Path(__file__).resolve().parent / "sonos_speakers.json"


def main():
    print("Searching for Sonos speakers on the local network...")
    speakers = soco.discover(timeout=5)

    if not speakers:
        print("No Sonos speakers found. Check that you're on the same Wi-Fi network as your Sonos system.")
        sys.exit(1)

    by_name = {}
    for sp in speakers:
        info = sp.get_speaker_info()
        name = info.get("zone_name") or sp.player_name
        by_name[name] = sp.ip_address

    by_name = dict(sorted(by_name.items()))

    if OUTPUT.exists():
        print(f"{OUTPUT.name} already exists. Overwrite? [y/N] ", end="")
        if input().strip().lower() != "y":
            print("Aborted.")
            sys.exit(0)

    OUTPUT.write_text(json.dumps(by_name, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nFound {len(by_name)} speaker(s):")
    for name, ip in by_name.items():
        print(f"  - {name:30s} {ip}")
    print(f"\nWritten to {OUTPUT}")


if __name__ == "__main__":
    main()
