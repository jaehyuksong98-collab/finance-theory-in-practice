"""Save reviewed event input as an immutable snapshot, preserving revisions."""

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from analyze import INPUT_FIELDS, read_events


def ingest(source, snapshot_dir, allow_revision=False):
    incoming = read_events(source)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    old_files = sorted(snapshot_dir.glob("*.csv"))
    previous = read_events(old_files[-1]) if old_files else []
    merged = {(r["ticker"], r["ex_date"]): r for r in previous}
    revisions = []
    additions = []
    for row in incoming:
        key = (row["ticker"], row["ex_date"])
        if key in merged and merged[key] != row:
            revisions.append(key)
        elif key not in merged:
            additions.append(key)
        merged[key] = row
    if revisions and not allow_revision:
        raise ValueError(f"Conflicting events require --allow-revision: {revisions}")
    if not additions and not revisions:
        return None
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    target = snapshot_dir / f"{timestamp}.csv"
    with target.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=INPUT_FIELDS)
        writer.writeheader()
        writer.writerows(sorted(merged.values(), key=lambda r: (r["ticker"], r["ex_date"])))
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix(".json").write_text(json.dumps({
        "created_utc": timestamp, "source_file": str(source), "sha256": digest,
        "additions": additions, "revisions": revisions,
    }, indent=2) + "\n", encoding="utf-8")
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    parser.add_argument("--allow-revision", action="store_true")
    args = parser.parse_args()
    print(ingest(args.source, args.snapshot_dir, args.allow_revision) or "No new events")
