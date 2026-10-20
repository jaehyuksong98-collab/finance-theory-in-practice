"""Retain each new French-library release and flag revisions to earlier estimates."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

from analyze import csv_lines, snapshot_label


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="") as stream:
        return {row["formation_year"]: row for row in csv.DictReader(stream)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--beta-zip", required=True, type=Path)
    ap.add_argument("--factors-zip", required=True, type=Path)
    ap.add_argument("--size-beta-zip", required=True, type=Path)
    ap.add_argument("--retrieved-date", default=date.today().isoformat())
    ap.add_argument("--snapshots", type=Path, default=Path(__file__).resolve().parent / "snapshots")
    args = ap.parse_args()
    sources = {"beta_portfolios": args.beta_zip, "three_factors": args.factors_zip, "size_beta_portfolios": args.size_beta_zip}
    labels = {key: snapshot_label(csv_lines(path)) for key, path in sources.items()}
    if len(set(labels.values())) != 1:
        raise ValueError(f"Source releases differ: {labels}")
    release = next(iter(labels.values()))
    target = args.snapshots / release
    if target.exists():
        raise FileExistsError(f"Snapshot {release} already exists. Keep existing results; inspect source hashes and revisions manually.")
    args.snapshots.mkdir(parents=True, exist_ok=True)
    releases = sorted(path for path in args.snapshots.iterdir() if path.is_dir() and path.name.isdigit() and len(path.name) == 6)
    previous = releases[-1] if releases else None
    staging = Path(tempfile.mkdtemp(prefix=f".{release}-", dir=args.snapshots))
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"
    try:
        with tempfile.TemporaryDirectory(prefix="capm-mpl-") as mpl:
            env["MPLCONFIGDIR"] = mpl
            command = [sys.executable, str(Path(__file__).with_name("analyze.py")), "--beta-zip", str(args.beta_zip), "--factors-zip", str(args.factors_zip), "--size-beta-zip", str(args.size_beta_zip), "--retrieved-date", args.retrieved_date, "--out", str(staging)]
            subprocess.run(command, check=True, env=env, stdout=subprocess.DEVNULL)
        staging.rename(target)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    manifest = {
        "release": release,
        "retrieved_date": args.retrieved_date,
        "sources": {key: {"filename": path.name, "sha256": sha256(path)} for key, path in sources.items()},
        "previous_release": previous.name if previous else None,
    }
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    report = {"release": release, "previous_release": previous.name if previous else None, "revised_years": [], "new_years": []}
    if previous:
        old = rows(previous / "yearly_diagnostics.csv")
        new = rows(target / "yearly_diagnostics.csv")
        report["new_years"] = sorted(set(new) - set(old))
        for year in sorted(set(new) & set(old)):
            changes = {}
            for key in ("prior_beta_low", "prior_beta_high", "high_minus_low_monthly_pct", "market_excess_monthly_pct"):
                before, after = float(old[year][key]), float(new[year][key])
                if abs(before - after) > 1e-9:
                    changes[key] = {"before": before, "after": after}
            if changes:
                report["revised_years"].append({"formation_year": year, "changes": changes})
    (target / "revision_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"saved_to": str(target), "new_years": report["new_years"], "revised_year_count": len(report["revised_years"])}, indent=2))


if __name__ == "__main__":
    main()
