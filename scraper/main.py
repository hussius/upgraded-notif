#!/usr/bin/env python3
"""
upgraded-notifs: daily digest of new consulting assignments / tenders.

Usage:
  python main.py                       # all sources
  python main.py --dry-run             # scrape + analyse, print matches, skip email
  python main.py --source upgraded     # single source
  python main.py --source offentlig    # single source
"""
import json
import os
import sys
import traceback
from pathlib import Path

from analyze import analyze_listing
from notify import send_notification
import scrape as scrape_upgraded
import scrape_offentlig

ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "config.json"
SEEN_PATH = ROOT / "data" / "seen.json"

SOURCES = {
    "upgraded": scrape_upgraded.fetch_listings,
    "offentlig": scrape_offentlig.fetch_listings,
}


def load_seen() -> set[str]:
    if not SEEN_PATH.exists():
        return set()
    data = json.loads(SEEN_PATH.read_text())
    # Migrate old flat list (no source prefix) → prefix with "upgraded:"
    if isinstance(data, list) and data and ":" not in data[0]:
        migrated = {f"upgraded:{id_}" for id_ in data}
        save_seen(migrated)
        return migrated
    return set(data)


def save_seen(seen: set[str]) -> None:
    SEEN_PATH.parent.mkdir(exist_ok=True)
    SEEN_PATH.write_text(json.dumps(sorted(seen), indent=2) + "\n")


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text())


def main(dry_run: bool = False, only_source: str | None = None) -> None:
    config = load_config()
    roles = config["roles"]
    seen = load_seen()

    sources = (
        {only_source: SOURCES[only_source]}
        if only_source
        else SOURCES
    )

    all_matches = []

    for source_name, fetch_fn in sources.items():
        if source_name == "offentlig" and not os.environ.get("OFFENTLIG_API_KEY"):
            print(f"Skipping {source_name} — OFFENTLIG_API_KEY not set")
            continue

        print(f"\nFetching listings from {source_name}...")
        try:
            listings = fetch_fn()
        except Exception:
            print(f"ERROR fetching {source_name}:")
            traceback.print_exc()
            continue

        print(f"Fetched {len(listings)} listings.")

        new_listings = [l for l in listings if l["id"] not in seen]
        if not new_listings:
            print("No new listings since last run.")
            continue

        print(f"{len(new_listings)} new — analysing with Claude...")

        for listing in new_listings:
            matched_roles = analyze_listing(listing, roles)
            seen.add(listing["id"])
            if matched_roles:
                listing["matched_roles"] = matched_roles
                all_matches.append(listing)
                print(f"  MATCH  [{', '.join(matched_roles)}]  {listing['title']}")
            else:
                print(f"  skip   {listing['title']}")

    # Always persist, even with no matches or errors.
    save_seen(seen)

    if not all_matches:
        print("\nNo listings matched role criteria — no email sent.")
        return

    if dry_run:
        print(f"\n[dry-run] Would email {len(all_matches)} matching listing(s) — skipping send.")
        return

    print(f"\nSending email for {len(all_matches)} matching listing(s)...")
    send_notification(all_matches, config)


if __name__ == "__main__":
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    only_source = None
    if "--source" in args:
        idx = args.index("--source")
        only_source = args[idx + 1] if idx + 1 < len(args) else None
        if only_source not in SOURCES:
            print(f"Unknown source '{only_source}'. Valid: {', '.join(SOURCES)}")
            sys.exit(1)

    try:
        main(dry_run=dry_run, only_source=only_source)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
