# CAPM lecture follow-up: does a past optimal mix stay optimal?

This student-facing exercise continues the [first CAPM Article](https://www.linkedin.com/pulse/capm-real-world-does-higher-beta-actually-earn-more-jaehyuk-song-vktre/) with the risk/return choice and capital market line in pages 3–6 of `Investment Analysis/Lecture notes/Topic 3 CAPM.pdf`. The private lecture PDF is not redistributed. This is a retrospective portfolio-choice exercise, **not** a direct test of the CAPM's complete market portfolio.

## Question and design

If an analyst chooses the historically highest-Sharpe mix, does that choice beat a simple equal mix in the following year? This exploratory follow-up selects three U.S. value-weighted beta-sorted portfolios from the official Fama/French library: `Lo 10`, `Dec 5`, and `Hi 10`. These are *portfolio groups*, not three individual stocks. The groups were chosen after the earlier CAPM Article, so the exercise was not preregistered or blind to all historical returns. At each June decision, the algorithm nevertheless uses only the preceding 120 months of returns, checks every long-only 1% weight combination (5,151 possibilities), and holds the highest in-sample Sharpe combination for July–June. If all candidate risky Sharpe ratios are nonpositive, it holds the source risk-free proxy for that year. The comparison is a monthly rebalanced equal-weight mix and the library's U.S. market excess-return proxy. The mix is rebalanced monthly; transaction costs are omitted.

The outcome period is July 1973–June 2026, 53 non-overlapping holding years (636 months). Each training period overlaps earlier training periods but never its own test year. The earliest training period begins July 1963. A new source release may revise this entire history, so this is a historical backtest with a fixed **August 2026 CRSP snapshot**, not a live prospective record.

## Key definitions

Source returns and risk-free rates are **monthly percent**. For a mix with weights `w_i`, monthly excess return is `sum(w_i × (R_i,t − RF_t))`; the equal mix uses `1/3` each. Annualized arithmetic average excess return is `12 × mean(monthly excess return)`, annualized volatility is `sqrt(12) × sample standard deviation(monthly excess return)`, and annualized Sharpe is their ratio. These are arithmetic annualizations, not compound annual returns. No short sales, borrowing, or leverage are allowed in the tested strategy. The displayed historical cash-to-risky allocation line ends at the selected risky mix; extending it beyond that point would imply borrowing.

## Main result

| Portfolio, July 1973–June 2026 | Annualized arithmetic excess return | Annualized volatility | Pooled Sharpe |
| --- | ---: | ---: | ---: |
| Past 10-year max-Sharpe choice | 5.67% | 13.16% | 0.431 |
| Equal mix of the same three groups | 8.54% | 17.35% | 0.492 |
| U.S. market proxy | 8.01% | 15.91% | 0.504 |

The selected mix has **lower risk as well as lower average return** than the equal mix. Its pooled Sharpe difference is −0.062. A paired July–June year-block bootstrap gives a descriptive 95% interval of **[−0.246, +0.114]**; it includes zero. The selected-minus-equal annualized arithmetic average excess-return gap is −2.87 percentage points; a year-block bootstrap interval is [−5.57, −0.28] pp. That average-return gap alone does not judge risk-adjusted optimization. Rolling training windows overlap and source histories can be revised, so the bootstrap interval is only an illustration of sampling variation.

On the **common July 1978–June 2026 outcome window**, changing the estimation lookback changes the result:

| Prior return history | Selected Sharpe | Equal-mix Sharpe | Difference |
| --- | ---: | ---: | ---: |
| 5 years | 0.490 | 0.527 | −0.037 |
| 10 years | 0.504 | 0.527 | −0.024 |
| 15 years | 0.605 | 0.527 | +0.077 |

Thus this exercise does not support a stable claim that a past optimized mix is reliably superior or inferior. The full 10-year sample in the first table and the common-window 10-year figure in the second table have **different start dates**.

## Reproduce

Download these two original ZIPs from the [Kenneth R. French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/data_library.html):

- [Portfolios Formed on Market Beta](https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/ftp/Portfolios_Formed_on_BETA_CSV.zip)
- [Fama/French 3 Research Factors](https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/ftp/F-F_Research_Data_Factors_CSV.zip)

The ZIPs used for the published numbers were retrieved 17 October 2026 and are identified by `SOURCE_MANIFEST.md`. Do not assume a current download reproduces the exact historical values; compare its snapshot label and SHA-256 first. No raw source ZIPs are redistributed here.

```bash
python3 analyze_cml.py --beta-zip /path/to/Portfolios_Formed_on_BETA_CSV.zip \
  --factors-zip /path/to/F-F_Research_Data_Factors_CSV.zip \
  --lookback-years 10 --out outputs_10y
python3 analyze_cml.py --beta-zip /path/to/Portfolios_Formed_on_BETA_CSV.zip \
  --factors-zip /path/to/F-F_Research_Data_Factors_CSV.zip \
  --lookback-years 5 --out outputs_5y
python3 analyze_cml.py --beta-zip /path/to/Portfolios_Formed_on_BETA_CSV.zip \
  --factors-zip /path/to/F-F_Research_Data_Factors_CSV.zip \
  --lookback-years 15 --out outputs_15y
python3 compare_lookbacks.py
```

Python 3.10+ standard library handles the analysis. Matplotlib is optional for PNG charts. The analysis saves `annual_decisions.csv` (formation windows, weights, in-sample estimates), `monthly_oos.csv` (observed subsequent excess returns and risk-free rate), `final_training_window_candidates.csv` (all feasible final-window mixes), `summary.json` and charts. `lookback_sensitivity.csv` compares the same 576 test months. Re-run with later source releases and retain a dated output folder; inspect the publisher's notes and historical revisions before changing any interpretation. The parent folder's `update_snapshot.py` supports snapshot comparison.

## Interpretation limits

The theoretical CML refers to an efficient *complete market portfolio* and expected returns. Here we observe three historical U.S. equity portfolio groups, a stock-market proxy, and realized returns. Their frontier is a constrained, estimated subset frontier, not the CAPM's true CML. Neither market completeness nor investors' expectations or preference assumptions can be observed from these returns. Portfolio groups are not directly investable funds; trading costs, taxes, financing frictions and rebalancing turnover are omitted. The library's 2026 snapshot includes historical revisions and the Treasury-bill proxy's underlying source changes in June 2024. The exploratory asset choice, 1% grid, June decision date and lookback lengths affect the outcome. There is no causal identification.

The practical lesson is to label a portfolio as **historically optimal under specified inputs**, then examine future data and simple alternatives before treating it as a forward-looking recommendation.
