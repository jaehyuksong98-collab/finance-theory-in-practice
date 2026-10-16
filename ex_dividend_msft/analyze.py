"""Auditable ex-dividend event arithmetic with no network calls."""

import argparse
import csv
import json
from datetime import date
from pathlib import Path

INPUT_FIELDS = [
    "ticker", "ex_date", "dividend_usd", "prior_date", "prior_close_usd",
    "ex_open_usd", "ex_close_usd", "announcement_url", "price_url", "retrieved_date",
]


def read_events(path):
    with open(path, newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != INPUT_FIELDS:
            raise ValueError(f"Expected columns: {INPUT_FIELDS}")
        events = list(reader)
    if not events:
        raise ValueError("Input contains no events")
    keys = set()
    for row in events:
        key = (row["ticker"], row["ex_date"])
        if key in keys:
            raise ValueError(f"Duplicate event: {key}")
        keys.add(key)
        if date.fromisoformat(row["prior_date"]) >= date.fromisoformat(row["ex_date"]):
            raise ValueError(f"Prior date must precede ex-date: {key}")
        for name in ("dividend_usd", "prior_close_usd", "ex_open_usd", "ex_close_usd"):
            if float(row[name]) <= 0:
                raise ValueError(f"{name} must be positive: {key}")
        if not row["announcement_url"].startswith("https://") or not row["price_url"].startswith("https://"):
            raise ValueError(f"Missing secure source URL: {key}")
    return events


def calculate(row):
    dividend = float(row["dividend_usd"])
    prior = float(row["prior_close_usd"])
    open_price = float(row["ex_open_usd"])
    close_price = float(row["ex_close_usd"])
    return {
        "ticker": row["ticker"],
        "ex_date": row["ex_date"],
        "dividend_usd": dividend,
        "dividend_yield_pct": round(100 * dividend / prior, 6),
        "prior_close_usd": prior,
        "ex_open_usd": open_price,
        "ex_close_usd": close_price,
        "benchmark_change_usd": -dividend,
        "opening_change_usd": round(open_price - prior, 2),
        "closing_change_usd": round(close_price - prior, 2),
        "opening_residual_usd": round(open_price - prior + dividend, 2),
        "closing_residual_usd": round(close_price - prior + dividend, 2),
        "total_return_pct": round(100 * (close_price + dividend - prior) / prior, 6),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    events = [calculate(row) for row in read_events(args.input)]
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "event_results.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(events[0]))
        writer.writeheader()
        writer.writerows(events)
    summary = {
        "sample_size": len(events),
        "opening_declines": sum(row["opening_change_usd"] < 0 for row in events),
        "closing_declines": sum(row["closing_change_usd"] < 0 for row in events),
        "mean_opening_residual_usd": round(sum(row["opening_residual_usd"] for row in events) / len(events), 4),
        "mean_closing_residual_usd": round(sum(row["closing_residual_usd"] for row in events) / len(events), 4),
        "mean_dividend_yield_pct": round(sum(row["dividend_yield_pct"] for row in events) / len(events), 6),
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
