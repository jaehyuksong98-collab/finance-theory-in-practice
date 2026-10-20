"""CAPM teaching test using the August 2026 Fama/French source ZIPs.

No raw third-party source file is bundled here. See README.md for definitions.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import re
import statistics as stats
import zipfile
from collections import defaultdict
import datetime
from pathlib import Path


DECS = ("Lo 10", "Dec 2", "Dec 3", "Dec 4", "Dec 5", "Dec 6", "Dec 7", "Dec 8", "Dec 9", "Hi 10")
MISSING = {-99.99, -999.0}


def csv_lines(zip_path: Path) -> list[str]:
    with zipfile.ZipFile(zip_path) as z:
        members = [name for name in z.namelist() if name.lower().endswith(".csv")]
        if len(members) != 1:
            raise ValueError(f"Expected one CSV member in {zip_path}: {members}")
        raw = z.read(members[0])
        try:
            return raw.decode("utf-8-sig").splitlines()
        except UnicodeDecodeError:
            return raw.decode("latin-1").splitlines()


def snapshot_label(lines: list[str]) -> str:
    match = re.search(r"using the (\d{6}) CRSP database", "\n".join(lines[:5]))
    if not match:
        raise ValueError("CRSP source snapshot label missing")
    return match.group(1)


def section(lines: list[str], title: str, date_digits: int) -> dict[int, dict[str, float]]:
    """Parse one named table and stop at its first non-date row."""
    starts = [i for i, line in enumerate(lines) if line.strip() == title]
    if len(starts) != 1:
        raise ValueError(f"Expected one section {title!r}; found {len(starts)}")
    i = starts[0] + 1
    while not lines[i].lstrip().startswith(","):
        i += 1
    names = next(csv.reader([lines[i]]))[1:]
    out = {}
    started = False
    for line in lines[i + 1 :]:
        row = next(csv.reader([line])) if line.strip() else []
        key = row[0].strip() if row else ""
        if not re.fullmatch(rf"\d{{{date_digits}}}", key):
            if started:
                break
            continue
        if len(row) != len(names) + 1:
            raise ValueError(f"Incorrect width for {title}, {key}")
        values = [float(value) for value in row[1:]]
        if any(value in MISSING for value in values):
            raise ValueError(f"Missing sentinel in {title}, {key}")
        out[int(key)] = dict(zip(names, values, strict=True))
        started = True
    if not out:
        raise ValueError(f"No records found for {title}")
    return out


def factors(lines: list[str]) -> dict[int, dict[str, float]]:
    starts = [i for i, line in enumerate(lines) if line.strip().startswith(",Mkt-RF,")]
    if not starts:
        raise ValueError("Could not locate monthly factor header")
    names = next(csv.reader([lines[starts[0]]]))[1:]
    out = {}
    for line in lines[starts[0] + 1 :]:
        row = next(csv.reader([line])) if line.strip() else []
        key = row[0].strip() if row else ""
        if not re.fullmatch(r"\d{6}", key):
            break
        if len(row) != len(names) + 1:
            raise ValueError(f"Incorrect factor width at {key}")
        out[int(key)] = {name: float(v) for name, v in zip(names, row[1:], strict=True)}
    return out


def holding_year(yyyymm: int) -> int:
    year, month = divmod(yyyymm, 100)
    if not 1 <= month <= 12:
        raise ValueError(f"Invalid month: {yyyymm}")
    return year if month >= 7 else year - 1


def slope_intercept(x: list[float], y: list[float]) -> tuple[float, float]:
    xbar, ybar = stats.mean(x), stats.mean(y)
    var = sum((v - xbar) ** 2 for v in x)
    slope = sum((a - xbar) * (b - ybar) for a, b in zip(x, y, strict=True)) / var
    return slope, ybar - slope * xbar


def bootstrap_ci(values: list[float], seed: int = 20261017) -> tuple[float, float]:
    rng = random.Random(seed)
    draws = [stats.mean(rng.choices(values, k=len(values))) for _ in range(10000)]
    draws.sort()
    return draws[249], draws[9749]


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--beta-zip", required=True, type=Path)
    parser.add_argument("--factors-zip", required=True, type=Path)
    parser.add_argument("--size-beta-zip", type=Path)
    parser.add_argument("--out", type=Path, default=Path("outputs"))
    parser.add_argument("--retrieved-date", default=datetime.date.today().isoformat(), help="YYYY-MM-DD date source files were retrieved")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    beta_lines = csv_lines(args.beta_zip)
    factor_lines = csv_lines(args.factors_zip)
    snapshot = snapshot_label(beta_lines)
    if snapshot_label(factor_lines) != snapshot:
        raise ValueError("Portfolio and factor snapshots differ")
    returns = section(beta_lines, "Value Weighted Returns -- Monthly", 6)
    prior_betas = section(beta_lines, "Value-Weighted Average of Prior Beta", 4)
    factor = factors(factor_lines)

    grouped: dict[int, list[int]] = defaultdict(list)
    for date in returns:
        grouped[holding_year(date)].append(date)
    years = [year for year, dates in sorted(grouped.items()) if len(dates) == 12 and year in prior_betas]
    if not years or years != list(range(1963, years[-1] + 1)):
        raise ValueError(f"Unexpected complete July–June years: {years[:2]}...{years[-2:]}")
    monthly = []
    yearly = []
    for year in years:
        dates = sorted(grouped[year])
        expected = [year * 100 + month for month in range(7, 13)] + [(year + 1) * 100 + month for month in range(1, 7)]
        if dates != expected or any(date not in factor for date in dates):
            raise ValueError(f"Date mismatch in holding year {year}")
        xs = [prior_betas[year][name] for name in DECS]
        if xs != sorted(xs):
            raise ValueError(f"Prior betas not sorted in {year}")
        ys = []
        for name in DECS:
            excess = []
            for date in dates:
                gross = returns[date][name]
                rf = factor[date]["RF"]
                monthly.append({"date": date, "formation_year": year, "decile": name, "prior_beta": prior_betas[year][name], "return_pct": gross, "rf_pct": rf, "excess_pct": gross - rf})
                excess.append(gross - rf)
            ys.append(stats.mean(excess))
        market = stats.mean(factor[date]["Mkt-RF"] for date in dates)
        slope, intercept = slope_intercept(xs, ys)
        yearly.append({"formation_year": year, "prior_beta_low": xs[0], "prior_beta_high": xs[-1], "low_excess_monthly_pct": ys[0], "high_excess_monthly_pct": ys[-1], "high_minus_low_monthly_pct": ys[-1] - ys[0], "market_excess_monthly_pct": market, "capm_implied_spread_monthly_pct": (xs[-1] - xs[0]) * market, "spread_minus_capm_monthly_pct": (ys[-1] - ys[0]) - (xs[-1] - xs[0]) * market, "cross_section_slope_monthly_pct_per_beta": slope, "cross_section_intercept_monthly_pct": intercept})

    decile_rows = []
    time_series = []
    dates_for_test = [date for year in years for date in sorted(grouped[year])]
    market_series = [factor[date]["Mkt-RF"] for date in dates_for_test]
    for name in DECS:
        selected = [row for row in monthly if row["decile"] == name]
        decile_rows.append({"decile": name, "mean_prior_beta": stats.mean(row["prior_beta"] for row in selected), "mean_excess_monthly_pct": stats.mean(row["excess_pct"] for row in selected), "annualized_arithmetic_excess_pct": 12 * stats.mean(row["excess_pct"] for row in selected), "n_months": len(selected)})
        observed = [returns[date][name] - factor[date]["RF"] for date in dates_for_test]
        ols_beta, alpha = slope_intercept(market_series, observed)
        fitted = [alpha + ols_beta * x for x in market_series]
        total = sum((y - stats.mean(observed)) ** 2 for y in observed)
        residual = sum((y - yhat) ** 2 for y, yhat in zip(observed, fitted, strict=True))
        time_series.append({"decile": name, "regression_beta": ols_beta, "alpha_monthly_pct": alpha, "r_squared": 1 - residual / total, "systematic_variance_share": ols_beta ** 2 * stats.variance(market_series) / stats.variance(observed)})

    spreads = [row["high_minus_low_monthly_pct"] for row in yearly]
    forecast_errors = [row["spread_minus_capm_monthly_pct"] for row in yearly]
    slope_years = [row["cross_section_slope_monthly_pct_per_beta"] for row in yearly]
    low = [row for row in monthly if row["decile"] == "Lo 10"]
    high = [row for row in monthly if row["decile"] == "Hi 10"]
    assert len(low) == len(high) == len(years) * 12
    assert all(a["date"] == b["date"] for a, b in zip(low, high, strict=True))
    assert abs(stats.mean(b["excess_pct"] - a["excess_pct"] for a, b in zip(low, high, strict=True)) - stats.mean(spreads)) < 1e-10
    ci = bootstrap_ci(spreads)

    size_results = None
    if args.size_beta_zip:
        size_lines = csv_lines(args.size_beta_zip)
        if snapshot_label(size_lines) != snapshot:
            raise ValueError("Size-beta and main source snapshots differ")
        size_returns = section(size_lines, "Average Value Weighted Returns -- Monthly", 6)
        groups = [
            ("Small", "SMALL LoBETA", "SMALL HiBETA"),
            ("ME2", "ME2 BETA1", "ME2 BETA5"),
            ("ME3", "ME3 BETA1", "ME3 BETA5"),
            ("ME4", "ME4 BETA1", "ME4 BETA5"),
            ("Big", "BIG LoBETA", "BIG HiBETA"),
        ]
        size_results = []
        all_dates = [date for year in years for date in sorted(grouped[year])]
        for label, lo, hi in groups:
            if any(date not in size_returns for date in all_dates):
                raise ValueError(f"Missing size-beta month in {label}")
            by_year = [stats.mean(size_returns[date][hi] - size_returns[date][lo] for date in grouped[year]) for year in years]
            size_results.append({"size_bucket": label, "high_minus_low_monthly_pct": stats.mean(by_year), "annualized_arithmetic_spread_pct": 12 * stats.mean(by_year), "positive_year_fraction": sum(v > 0 for v in by_year) / len(by_year)})

    summary = {
        "source_snapshot": f"{snapshot} CRSP database",
        "retrieved_date": args.retrieved_date,
        "holding_years": [years[0], years[-1]],
        "complete_holding_year_count": len(years),
        "monthly_observations_per_decile": len(low),
        "market_excess_monthly_pct": stats.mean(row["market_excess_monthly_pct"] for row in yearly),
        "annualized_arithmetic_market_excess_pct": 12 * stats.mean(row["market_excess_monthly_pct"] for row in yearly),
        "market_excess_monthly_sd_pct": stats.stdev(market_series),
        "market_ex_post_annualized_sharpe": stats.mean(market_series) / stats.stdev(market_series) * math.sqrt(12),
        "high_minus_low_monthly_pct": stats.mean(spreads),
        "annualized_arithmetic_high_minus_low_pct": 12 * stats.mean(spreads),
        "high_minus_low_year_block_bootstrap_95pct_monthly": list(ci),
        "capm_implied_high_minus_low_monthly_pct": stats.mean(row["capm_implied_spread_monthly_pct"] for row in yearly),
        "observed_minus_capm_monthly_pct": stats.mean(forecast_errors),
        "observed_minus_capm_year_block_bootstrap_95pct_monthly": list(bootstrap_ci(forecast_errors, seed=20261018)),
        "positive_spread_year_fraction": sum(value > 0 for value in spreads) / len(spreads),
        "positive_slope_year_fraction": sum(value > 0 for value in slope_years) / len(slope_years),
        "mean_yearly_cross_section_slope_monthly_pct_per_beta": stats.mean(slope_years),
        "mean_yearly_cross_section_intercept_monthly_pct": stats.mean(row["cross_section_intercept_monthly_pct"] for row in yearly),
        "deciles": decile_rows,
        "time_series_regressions": time_series,
        "size_conditioned": size_results,
    }
    write_csv(args.out / "yearly_diagnostics.csv", yearly, list(yearly[0]))
    write_csv(args.out / "decile_summary.csv", decile_rows, list(decile_rows[0]))
    write_csv(args.out / "time_series_regressions.csv", time_series, list(time_series[0]))
    if size_results:
        write_csv(args.out / "size_conditioned.csv", size_results, list(size_results[0]))
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))

    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return
    fig, ax = plt.subplots(figsize=(9, 5.2), dpi=180)
    xs = [row["mean_prior_beta"] for row in decile_rows]
    ys = [row["annualized_arithmetic_excess_pct"] for row in decile_rows]
    premium = summary["annualized_arithmetic_market_excess_pct"]
    ax.plot([0, max(xs) + .15], [0, (max(xs) + .15) * premium], color="#718096", lw=1.5, ls="--", label="CAPM line using realized market premium")
    ax.plot(xs, ys, color="#156082", marker="o", lw=2.3, label="Observed beta-decile means")
    for k, (x, y) in enumerate(zip(xs, ys, strict=True), 1):
        ax.annotate(str(k), (x, y), xytext=(5, 5), textcoords="offset points", fontsize=8)
    ax.set(xlabel="Average beta estimated before holding year", ylabel="Average excess return (%, arithmetic annualized)", title="Does higher prior beta imply higher later return?")
    ax.grid(axis="y", alpha=.25)
    ax.legend(frameon=False, fontsize=8, loc="best")
    fig.text(.13, .005, f"Fama/French US value-weighted beta deciles and factors; July 1963–June {years[-1]+1}. {snapshot} CRSP snapshot. Ex-post descriptive test.", fontsize=7, color="#4a5568")
    fig.tight_layout(rect=[0, .035, 1, 1])
    fig.savefig(args.out / "beta_deciles_vs_capm.png", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4.2), dpi=180)
    positions = list(range(1, 11))
    explained = [row["r_squared"] * 100 for row in time_series]
    unexplained = [100 - value for value in explained]
    ax.bar(positions, explained, color="#156082", label="Explained by market proxy")
    ax.bar(positions, unexplained, bottom=explained, color="#d7a56d", label="Residual variation")
    ax.set(xlabel="Beta portfolio decile (1 = lowest prior beta)", ylabel="Share of historical return variance (%)", title="Market-linked and residual variation in beta portfolios", ylim=(0, 100), xticks=positions)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    ax.grid(axis="y", alpha=.2)
    ax.set_axisbelow(True)
    fig.text(.13, .005, f"One-factor OLS of monthly portfolio excess returns on market excess returns; July 1963–June {years[-1]+1}. {snapshot} CRSP snapshot.", fontsize=7, color="#4a5568")
    fig.tight_layout(rect=[0, .04, 1, 1])
    fig.savefig(args.out / "risk_decomposition.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
