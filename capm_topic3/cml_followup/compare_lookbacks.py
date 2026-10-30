"""Compare pre-specified lookbacks over their shared out-of-sample months."""

from __future__ import annotations

import csv
import json
import math
import statistics as stats
from pathlib import Path

ROOT = Path(__file__).resolve().parent
YEARS = (5, 10, 15)


def load(years: int) -> dict[int, dict[str, str]]:
    path = ROOT / f"outputs_{years}y" / "monthly_oos.csv"
    with path.open(newline="") as file:
        rows = {int(row["date"]): row for row in csv.DictReader(file)}
    if not rows:
        raise ValueError(f"No observations: {path}")
    return rows


def summarize(values: list[float]) -> tuple[float, float, float]:
    mean, sd = stats.mean(values), stats.stdev(values)
    vol = math.sqrt(12) * sd
    return 12 * mean, vol, 12 * mean / vol


def main() -> None:
    data = {years: load(years) for years in YEARS}
    common = sorted(set.intersection(*(set(rows) for rows in data.values())))
    if len(common) != 576 or common[0] != 197807 or common[-1] != 202606:
        raise ValueError("Unexpected shared window; review source snapshots and missing data")
    for date in common:
        if len({data[y][date]["equal_excess_pct"] for y in YEARS}) != 1:
            raise ValueError(f"Baseline differs at {date}")
    rows = []
    for years in YEARS:
        selected = [float(data[years][date]["selected_excess_pct"]) for date in common]
        equal = [float(data[years][date]["equal_excess_pct"]) for date in common]
        selected_mean, selected_vol, selected_sharpe = summarize(selected)
        equal_mean, equal_vol, equal_sharpe = summarize(equal)
        rows.append({"lookback_years": years, "first_test_month": common[0], "last_test_month": common[-1],
                     "n_test_months": len(common), "selected_annual_arithmetic_excess_pct": selected_mean,
                     "selected_annual_vol_pct": selected_vol, "selected_sharpe": selected_sharpe,
                     "equal_annual_arithmetic_excess_pct": equal_mean, "equal_annual_vol_pct": equal_vol,
                     "equal_sharpe": equal_sharpe, "selected_minus_equal_sharpe": selected_sharpe - equal_sharpe})
    path = ROOT / "lookback_sensitivity.csv"
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
