# Finance Theory in Practice 01: Ex-dividend prices

**Question:** Does a share fall by approximately its cash dividend when it starts trading ex-dividend?

This is a reproducible, deliberately small pilot using four Microsoft ordinary cash dividends between November 2025 and August 2026. It compares the prior trading day's unadjusted close with the ex-date open and close. It is a descriptive check, not a causal estimate or a trading strategy.

## Run

```bash
python3 analyze.py --input data/msft_events.csv --output output
python3 -m unittest discover -s tests
```

`analyze.py` uses only the Python standard library. It writes `event_results.csv` and `summary.json`. `plot.py` needs matplotlib and writes `ex_date_comparison.png` from the calculated results.

For the chart and two-page PDF, install the optional packages in `requirements.txt` and run `build_report.py` after plotting.

```bash
python3 plot.py --input output/event_results.csv --output output/ex_date_comparison.png
```

## Long-term collection

The initial CSV is hand-transcribed from the cited issuer announcements and the Nasdaq Historical Quotes table. `ingest.py` accepts a new, reviewed event CSV and appends an immutable dated snapshot under `snapshots/`. It rejects conflicting rows unless `--allow-revision` is explicit; revised rows remain visible in the old snapshot. Run the analysis on the latest snapshot after each event. **There is no unattended scraping or automatic claim that an event has been verified.** A future scheduler may flag new issuer announcements for human review.

```bash
python3 ingest.py --source data/msft_events.csv --snapshot-dir snapshots
```

CSV columns: ticker, ex_date, dividend_usd, prior_date, prior_close_usd, ex_open_usd, ex_close_usd, announcement_url, price_url, retrieved_date. Prices are split-adjusted only if a stock split occurs in the study window; the sample uses Nasdaq's displayed Close/Last and Open. A different data provider must document its adjustment method. Never substitute a dividend-adjusted close for the raw-price event test.

## Calculation

- Benchmark ex-date price: `prior_close_usd - dividend_usd`.
- Opening gap: `ex_open_usd - prior_close_usd`.
- Closing change: `ex_close_usd - prior_close_usd`.
- Dividend-adjusted close-to-close total return: `(ex_close_usd + dividend_usd - prior_close_usd) / prior_close_usd`.
- Residual relative to the simple benchmark: `observed_change + dividend_usd`.

The opening gap is closer to the ex-date mechanical adjustment, but overnight news and market moves also affect it. The closing change adds a full day of trading. The dividend is a transfer from firm value to shareholders, so a drop does not automatically mean an economic loss. A four-event sample cannot establish the average market response.

## Sources and rights

- Microsoft official announcement URLs are recorded per event in `data/msft_events.csv`.
- Nasdaq [MSFT Historical Quotes](https://www.nasdaq.com/market-activity/stocks/msft/historical), observed 16 October 2026; prices were transcribed from the 1Y table. Nasdaq data rights should be checked before redistributing a full price history; this repository includes only the twelve event-day/preceding-day price values needed to audit the four calculations.
- Yahoo Finance [MSFT Historical Prices](https://finance.yahoo.com/quote/MSFT/history/) labels its "Close" column as split-adjusted, while "Adj Close" also accounts for dividends. The four Nasdaq closing-price pairs were cross-checked against Yahoo's "Close" rows; the latter were not used as the stored source.
- Nasdaq Global Indexes, [Total Return without the Dividend?](https://www.nasdaq.com/docs/total-return-without-the-dividend), August 2025, p. 1 / Chart 1, explains the ex-date benchmark.
- Course prompt: Corporate Finance Lecture 4, slide 4 (ex-dividend date) and slide 20 (information content). Course slides are **not** redistributed.

## Next study upgrade

Pre-register a multi-company sample, separate ordinary and special dividends, add market and sector returns, exclude splits and confounding company news, and retain every source/revision snapshot. Without these steps, the pilot measures observed prices only and cannot identify the dividend's causal effect.
