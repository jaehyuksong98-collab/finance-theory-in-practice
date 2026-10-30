"""A rolling, out-of-sample illustration of portfolio choice and a capital allocation line.

This is a three-portfolio teaching exercise, not a test that the complete market
portfolio is mean-variance efficient. Source files are downloaded separately from
the Kenneth R. French Data Library; see README.md.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import statistics as stats
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyze import csv_lines, factors, holding_year, section, snapshot_label  # noqa: E402


ASSETS = ("Lo 10", "Dec 5", "Hi 10")
GRID_DENOMINATOR = 100


def expected_months(year: int) -> list[int]:
    return [year * 100 + m for m in range(7, 13)] + [(year + 1) * 100 + m for m in range(1, 7)]


def moments(rows: list[tuple[float, float, float]]) -> tuple[list[float], list[list[float]]]:
    means = [stats.mean(row[i] for row in rows) for i in range(3)]
    cov = [
        [sum((row[i] - means[i]) * (row[j] - means[j]) for row in rows) / (len(rows) - 1) for j in range(3)]
        for i in range(3)
    ]
    return means, cov


def portfolio_stats(weights: tuple[float, float, float], means: list[float], cov: list[list[float]]) -> dict[str, float]:
    monthly_mean = sum(weights[i] * means[i] for i in range(3))
    monthly_var = sum(weights[i] * weights[j] * cov[i][j] for i in range(3) for j in range(3))
    annual_vol = math.sqrt(12 * max(0, monthly_var))
    return {
        "annual_excess_pct": 12 * monthly_mean,
        "annual_vol_pct": annual_vol,
        "annual_sharpe": 12 * monthly_mean / annual_vol if annual_vol > 0 else float("nan"),
    }


def candidate_weights():
    n = GRID_DENOMINATOR
    for a in range(n + 1):
        for b in range(n - a + 1):
            yield (a / n, b / n, (n - a - b) / n)


def choose_risky_mix(means: list[float], cov: list[list[float]]) -> tuple[tuple[float, float, float], dict[str, float]]:
    best_weights = None
    best_stats = None
    for weights in candidate_weights():
        result = portfolio_stats(weights, means, cov)
        if not math.isfinite(result["annual_sharpe"]):
            continue
        if best_stats is None or result["annual_sharpe"] > best_stats["annual_sharpe"]:
            best_weights, best_stats = weights, result
    if best_weights is None or best_stats is None:
        raise ValueError("No valid risky portfolio")
    return best_weights, best_stats


def summary_stats(monthly_excess: list[float]) -> dict[str, float]:
    mean = stats.mean(monthly_excess)
    sd = stats.stdev(monthly_excess)
    return {"annual_excess_pct": 12 * mean, "annual_vol_pct": math.sqrt(12) * sd,
            "annual_sharpe": math.sqrt(12) * mean / sd if sd else float("nan")}


def year_bootstrap_ci(values: list[float], seed: int = 20261027) -> list[float]:
    rng = random.Random(seed)
    draws = sorted(stats.mean(rng.choices(values, k=len(values))) for _ in range(10000))
    return [draws[249], draws[9749]]


def sharpe_difference_bootstrap(monthly: list[dict], seed: int = 20261028) -> list[float]:
    """Paired July-June block bootstrap of pooled Sharpe differences."""
    blocks = [monthly[i:i + 12] for i in range(0, len(monthly), 12)]
    if any(len(block) != 12 or len({row["test_year"] for row in block}) != 1 for block in blocks):
        raise ValueError("Bootstrap blocks must be complete July-June holding years")
    rng = random.Random(seed)
    draws = []
    for _ in range(10000):
        sample = [row for block in rng.choices(blocks, k=len(blocks)) for row in block]
        selected = summary_stats([row["selected_excess_pct"] for row in sample])["annual_sharpe"]
        equal = summary_stats([row["equal_excess_pct"] for row in sample])["annual_sharpe"]
        draws.append(selected - equal)
    draws.sort()
    return [draws[249], draws[9749]]


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def source_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--beta-zip", required=True, type=Path)
    parser.add_argument("--factors-zip", required=True, type=Path)
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "outputs")
    parser.add_argument("--lookback-years", type=int, default=10)
    args = parser.parse_args()
    if args.lookback_years < 2:
        parser.error("--lookback-years must be at least 2")
    lookback_months = 12 * args.lookback_years

    beta_lines, factor_lines = csv_lines(args.beta_zip), csv_lines(args.factors_zip)
    snapshot = snapshot_label(beta_lines)
    if snapshot_label(factor_lines) != snapshot:
        raise ValueError("Source snapshot labels differ")
    returns = section(beta_lines, "Value Weighted Returns -- Monthly", 6)
    factor = factors(factor_lines)
    years = sorted({holding_year(d) for d in returns if d >= 196307})
    full_years = [y for y in years if all(d in returns and d in factor for d in expected_months(y))]
    if not full_years or full_years != list(range(1963, full_years[-1] + 1)):
        raise ValueError("Complete holding years are not continuous from 1963")
    if len(full_years) <= args.lookback_years:
        raise ValueError("Insufficient history for rolling test")

    all_dates = [d for y in full_years for d in expected_months(y)]
    excess = {d: tuple(returns[d][a] - factor[d]["RF"] for a in ASSETS) for d in all_dates}
    decisions, monthly, final_candidates = [], [], []
    for index in range(args.lookback_years, len(full_years)):
        year = full_years[index]
        train = all_dates[(index * 12 - lookback_months):index * 12]
        test = expected_months(year)
        if train[-1] >= test[0] or len(train) != lookback_months:
            raise AssertionError("Look-ahead or window-length error")
        mu, cov = moments([excess[d] for d in train])
        weights, fitted = choose_risky_mix(mu, cov)
        use_cash = fitted["annual_sharpe"] <= 0
        if index == len(full_years) - 1:
            final_candidates = [dict(zip(("weight_low", "weight_middle", "weight_high"), w, strict=True),
                                     **portfolio_stats(w, mu, cov)) for w in candidate_weights()]
        year_diffs = []
        for d in test:
            selected = 0.0 if use_cash else sum(weights[i] * excess[d][i] for i in range(3))
            equal = sum(excess[d]) / 3
            market = factor[d]["Mkt-RF"]
            rf = factor[d]["RF"]
            monthly.append({"date": d, "test_year": year, "selected_excess_pct": selected,
                            "equal_excess_pct": equal, "market_excess_pct": market, "rf_pct": rf})
            year_diffs.append(selected - equal)
        decisions.append({"test_year": year, "train_start": train[0], "train_end": train[-1],
                          "test_start": test[0], "test_end": test[-1],
                          "weight_low": weights[0], "weight_middle": weights[1], "weight_high": weights[2],
                          "cash_selected": use_cash, "train_selected_sharpe": fitted["annual_sharpe"],
                          "train_selected_excess_pct": fitted["annual_excess_pct"],
                          "train_selected_vol_pct": fitted["annual_vol_pct"],
                          "test_selected_minus_equal_arithmetic_pp": 12 * stats.mean(year_diffs)})

    if any(d["train_end"] >= d["test_start"] for d in decisions):
        raise AssertionError("A training period overlaps its test period")
    if len(monthly) != 12 * len(decisions):
        raise AssertionError("Incorrect test-month count")
    result = {
        "source_snapshot": f"{snapshot} CRSP database",
        "beta_zip_sha256": source_hash(args.beta_zip),
        "factors_zip_sha256": source_hash(args.factors_zip),
        "asset_labels": list(ASSETS),
        "train_months": lookback_months,
        "test_months_per_decision": 12,
        "grid_step": 1 / GRID_DENOMINATOR,
        "test_years": [decisions[0]["test_year"], decisions[-1]["test_year"]],
        "n_test_years": len(decisions),
        "n_test_months": len(monthly),
        "cash_decisions": sum(d["cash_selected"] for d in decisions),
        "pooled_oos": {label: summary_stats([m[f"{label}_excess_pct"] for m in monthly])
                       for label in ("selected", "equal", "market")},
        "selected_minus_equal_annual_arithmetic_pp": stats.mean(d["test_selected_minus_equal_arithmetic_pp"] for d in decisions),
        "selected_minus_equal_year_bootstrap_95pct_pp": year_bootstrap_ci([d["test_selected_minus_equal_arithmetic_pp"] for d in decisions]),
        "selected_minus_equal_oos_sharpe": (summary_stats([m["selected_excess_pct"] for m in monthly])["annual_sharpe"]
                                             - summary_stats([m["equal_excess_pct"] for m in monthly])["annual_sharpe"]),
        "selected_minus_equal_sharpe_year_bootstrap_95pct": sharpe_difference_bootstrap(monthly),
        "mean_selected_weights_when_invested": {
            part: stats.mean(d[f"weight_{part}"] for d in decisions if not d["cash_selected"])
            for part in ("low", "middle", "high")
        },
        "final_window": {"train_start": decisions[-1]["train_start"], "train_end": decisions[-1]["train_end"],
                         "test_start": decisions[-1]["test_start"], "test_end": decisions[-1]["test_end"],
                         "weights": [decisions[-1][f"weight_{part}"] for part in ("low", "middle", "high")],
                         "cash_selected": decisions[-1]["cash_selected"],
                         "train_selected_sharpe": decisions[-1]["train_selected_sharpe"]},
    }
    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "annual_decisions.csv", decisions)
    write_csv(args.out / "monthly_oos.csv", monthly)
    write_csv(args.out / "final_training_window_candidates.csv", final_candidates)
    (args.out / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))

    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return
    points = sorted(final_candidates, key=lambda row: row["annual_vol_pct"])
    fig, ax = plt.subplots(figsize=(8.8, 5.3), dpi=180)
    ax.scatter([p["annual_vol_pct"] for p in points], [p["annual_excess_pct"] for p in points],
               s=3, alpha=.16, color="#7194a8", label="Feasible long-only mixes")
    final = decisions[-1]
    ax.scatter([final["train_selected_vol_pct"]], [final["train_selected_excess_pct"]],
               s=85, color="#c26732", zorder=5, label="Highest past Sharpe on grid")
    slope = final["train_selected_sharpe"]
    if slope > 0:
        ax.plot([0, final["train_selected_vol_pct"]],
                [0, final["train_selected_excess_pct"]], ls="--", color="#c26732", lw=1.5,
                label="Historical cash-to-risky allocation line")
    ax.set(xlabel="Annualized volatility of monthly excess returns (%)",
           ylabel="Annualized arithmetic mean excess return (%)",
           title=f"What looked efficient? Training window: July {final['train_start']//100}–June {final['train_end']//100}")
    ax.grid(alpha=.2)
    ax.legend(frameon=False, fontsize=8)
    fig.text(.12, .005, f"Source: Kenneth R. French Data Library, beta portfolios and factors; {snapshot} CRSP snapshot. No borrowing in test.", fontsize=7, color="#516477")
    fig.tight_layout(rect=[0, .035, 1, 1])
    fig.savefig(args.out / "historical_frontier.png", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.8, 4.6), dpi=180)
    labels = ["Past-Sharpe choice", "Equal 3-way mix", "U.S. stock market proxy"]
    keys = ["selected", "equal", "market"]
    values = [result["pooled_oos"][key]["annual_sharpe"] for key in keys]
    bars = ax.bar(labels, values, color=["#c26732", "#156082", "#7d8b98"], width=.55)
    for bar, value in zip(bars, values, strict=True):
        ax.text(bar.get_x() + bar.get_width() / 2, value + .015, f"{value:.2f}", ha="center", fontsize=9)
    ax.set(ylabel="Realized annualized Sharpe ratio", title=f"Following-year outcomes across {len(decisions)} non-overlapping tests")
    ax.grid(axis="y", alpha=.2)
    ax.set_axisbelow(True)
    ci_low, ci_high = result["selected_minus_equal_sharpe_year_bootstrap_95pct"]
    fig.text(.1, .055, f"Choice minus equal mix: {result['selected_minus_equal_oos_sharpe']:+.2f}; 95% year-block bootstrap interval [{ci_low:+.2f}, {ci_high:+.2f}].", fontsize=8, color="#243e54")
    fig.text(.1, .018, f"Source: Kenneth R. French Data Library; {snapshot} CRSP snapshot. July {decisions[0]['test_year']}–June {decisions[-1]['test_year']+1}; {args.lookback_years}-year rolling training; before costs.", fontsize=7, color="#516477")
    fig.tight_layout(rect=[0, .10, 1, 1])
    fig.savefig(args.out / "out_of_sample_sharpe.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
