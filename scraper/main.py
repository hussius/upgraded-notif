#!/usr/bin/env python3
"""
upgraded-notifs: daily digest of new consulting assignments from upgraded.se.

Usage:
  python main.py            # normal run
  python main.py --dry-run  # scrape + analyse, print matches, skip email
"""
import json
import sys
from pathlib import Path

from analyze import analyze_listing
from notify import send_notification
from scrape import fetch_listings

ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "config.json"
SEEN_PATH = ROOT / "data" / "seen.json"


def load_seen() -> set[str]:
    if SEEN_PATH.exists():
        return set(json.loads(SEEN_PATH.read_text()))
    return set()


def save_seen(seen: set[str]) -> None:
    SEEN_PATH.parent.mkdir(exist_ok=True)
    SEEN_PATH.write_text(json.dumps(sorted(seen), indent=2) + "\n")


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text())


def main(dry_run: bool = False) -> None:
    config = load_config()
    roles = config["roles"]

    print("Fetching listings from upgraded.se...")
    listings = fetch_listings()
    print(f"Fetched {len(listings)} listings total.")

    seen = load_seen()
    new_listings = [l for l in listings if l["id"] not in seen]

    if not new_listings:
        print("No new listings since last run.")
        return

    print(f"{len(new_listings)} new listings — analysing with Claude...")

    matches = []
    for listing in new_listings:
        matched_roles = analyze_listing(listing, roles)
        seen.add(listing["id"])
        if matched_roles:
            listing["matched_roles"] = matched_roles
            matches.append(listing)
            print(f"  MATCH  [{', '.join(matched_roles)}]  {listing['title']}")
        else:
            print(f"  skip   {listing['title']}")

    # Always persist seen IDs, even when there are no matches.
    save_seen(seen)

    if not matches:
        print("No listings matched role criteria — no email sent.")
        return

    if dry_run:
        print(f"\n[dry-run] Would email {len(matches)} matching listing(s) — skipping send.")
        return

    print(f"\nSending email for {len(matches)} matching listing(s)...")
    send_notification(matches, config)


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    try:
        main(dry_run=dry_run)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
