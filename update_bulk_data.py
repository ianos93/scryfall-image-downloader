#!/usr/bin/env python3
"""Build Luminary's local card database from Scryfall's bulk data.

Downloads the `default_cards` bulk file (gzipped JSONL since Scryfall's 2026-07-20
migration) and writes two files into ./data:

  prints_index.json   oracle_id -> printings, oldest first. Each printing is
                      [id, set, YYYYMMDD, gamesBits, flagsBits, collectorNumber]
                      gamesBits: 1 paper, 2 mtgo, 4 arena
                      flagsBits: 1 digital, 2 promo
  bulk_manifest.json  timestamps and counts, shown as the database age in the app

Run it after each set release. Needs Python 3.7+ and nothing outside the standard
library.
"""

import gzip
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone

FORMAT_VERSION = 3

# Scryfall requires a User-Agent that identifies the application; generic ones such
# as Python-urllib are refused. Bump the version alongside the app.
USER_AGENT = "Luminary-BulkUpdater/4.1 (+https://github.com/ianos93/scryfall-image-downloader)"
BULK_INFO_URL = "https://api.scryfall.com/bulk-data/default_cards"

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
INDEX_PATH = os.path.join(DATA_DIR, "prints_index.json")
MANIFEST_PATH = os.path.join(DATA_DIR, "bulk_manifest.json")

GAME_BITS = {"paper": 1, "mtgo": 2, "arena": 4}


def request(url):
    return urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/json;q=0.9,*/*;q=0.8",
    })


def fetch_bulk_info():
    with urllib.request.urlopen(request(BULK_INFO_URL), timeout=30) as res:
        info = json.load(res)
    if "jsonl_download_uri" not in info:
        raise SystemExit("Scryfall's bulk-data response has no jsonl_download_uri. "
                         "The bulk format may have changed again; check scryfall.com/docs/api/bulk-data.")
    return info


def collector_sort_key(cn):
    # Numeric part first, so "9" < "10" < "10a"; non-numeric numbers ("S1", "★") after.
    m = re.match(r"(\d+)", cn or "")
    return (0, int(m.group(1)), cn) if m else (1, 0, cn or "")


def iter_cards(url, total_bytes):
    with urllib.request.urlopen(request(url), timeout=60) as res:
        counted = CountingReader(res, total_bytes)
        with gzip.GzipFile(fileobj=counted) as gz:
            for line in gz:
                line = line.strip()
                if line:
                    yield json.loads(line)
        counted.finish()


class CountingReader:
    """Wraps the HTTP response to print download progress."""

    def __init__(self, raw, total):
        self.raw, self.total, self.read_bytes, self.last_pct = raw, total or 0, 0, -1

    def read(self, n=-1):
        chunk = self.raw.read(n)
        self.read_bytes += len(chunk)
        if self.total:
            pct = int(self.read_bytes * 100 / self.total)
            if pct != self.last_pct and pct % 5 == 0:
                self.last_pct = pct
                print(f"\r  downloading… {pct:3d}%", end="", flush=True)
        return chunk

    def finish(self):
        print(f"\r  downloaded {self.read_bytes / 1_048_576:.1f} MB      ")


def main():
    print("Asking Scryfall for the current bulk file…")
    info = fetch_bulk_info()
    print(f"  default_cards updated {info['updated_at']}, "
          f"{info.get('compressed_size', 0) / 1_048_576:.0f} MB compressed")

    index = {}
    total = 0
    for card in iter_cards(info["jsonl_download_uri"], info.get("compressed_size")):
        # Reversible cards carry oracle_id on their faces rather than the card.
        oracle_id = card.get("oracle_id") or (card.get("card_faces") or [{}])[0].get("oracle_id")
        if not oracle_id or not card.get("released_at"):
            continue
        games = 0
        for g in card.get("games", []):
            games |= GAME_BITS.get(g, 0)
        flags = (1 if card.get("digital") else 0) | (2 if card.get("promo") else 0)
        index.setdefault(oracle_id, []).append([
            card["id"],
            card["set"],
            card["released_at"].replace("-", ""),
            games,
            flags,
            card.get("collector_number", ""),
        ])
        total += 1

    # Oldest first. The app breaks same-day ties by collector number itself, but
    # ordering them here too keeps the file stable between runs.
    for prints in index.values():
        prints.sort(key=lambda p: (p[2], p[1], collector_sort_key(p[5]), p[0]))

    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = INDEX_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(index, f, separators=(",", ":"), ensure_ascii=False)
    os.replace(tmp, INDEX_PATH)   # never leave a half-written index behind

    size_mb = round(os.path.getsize(INDEX_PATH) / 1_048_576, 1)
    manifest = {
        "local_updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scryfall_updated_at": info["updated_at"],
        "oracle_count": len(index),
        "total_entries": total,
        "file_size_mb": size_mb,
        "format_version": FORMAT_VERSION,
    }
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

    print(f"Wrote {INDEX_PATH}")
    print(f"  {len(index):,} cards, {total:,} printings, {size_mb} MB")
    print("Commit both files in data/, then use Refresh Database in the app's info panel.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nCancelled.")
