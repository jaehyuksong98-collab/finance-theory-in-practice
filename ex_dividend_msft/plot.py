"""Chart the theoretical -dividend change and observed opening/closing changes."""

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with args.input.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    dates = [row["ex_date"] for row in rows]
    benchmark = [float(row["benchmark_change_usd"]) for row in rows]
    opening = [float(row["opening_change_usd"]) for row in rows]
    closing = [float(row["closing_change_usd"]) for row in rows]
    x = list(range(len(rows)))
    fig, ax = plt.subplots(figsize=(10.8, 5.7), dpi=180)
    fig.patch.set_facecolor("white")
    ax.axhline(0, color="#66788a", linewidth=0.8)
    for i in x:
        ax.plot([i, i], [min(benchmark[i], opening[i], closing[i]), max(benchmark[i], opening[i], closing[i])], color="#d9e0e7", linewidth=2, zorder=1)
    ax.scatter([i-0.13 for i in x], benchmark, label="Theory: -$0.91 dividend", s=80, color="#bd612e", marker="D", zorder=3)
    ax.scatter(x, opening, label="Observed: prior close to ex-date open", s=80, color="#21867a", zorder=3)
    ax.scatter([i+0.13 for i in x], closing, label="Observed: prior close to ex-date close", s=80, color="#173f63", marker="s", zorder=3)
    ax.set_xticks(x, [d[5:] + "\n" + d[:4] for d in dates])
    ax.set_ylabel("Change per share (USD)")
    ax.set_title("Microsoft ex-dividend price moves vs the simple $0.91 benchmark", loc="left", fontsize=15, fontweight="bold", pad=18)
    ax.set_ylim(-11, 7)
    ax.grid(axis="y", color="#e3e8ed")
    ax.spines[['top', 'right']].set_visible(False)
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    fig.text(0.08, 0.02, "4 ordinary dividends, Nov 2025-Aug 2026. Sources: Microsoft announcements; Nasdaq MSFT Historical Quotes (retrieved 16 Oct 2026).", fontsize=8, color="#526679")
    fig.subplots_adjust(left=0.08, right=0.97, top=0.83, bottom=0.20)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, facecolor="white")


if __name__ == "__main__":
    main()
