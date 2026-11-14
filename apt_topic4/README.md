# APT in practice: one simple check

**Question.** Does adding size and value factors leave less of US industry returns unexplained than a market-only model?

This illustrates the multifactor idea from *Investment Analysis, Topic 4*, pp. 16–20. APT says that, under its assumptions, well-diversified portfolios with the same common-risk exposures should have similar expected returns. It does **not** tell us which factors to choose. Here we observe realized returns and use Fama–French's three factors as one example; this is not a proof of APT or a search for risk-free arbitrage.

## Data and calculation

- Official [Fama–French factors](https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/Data_Library/f-f_factors.html) and [49 US industry portfolios](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_49_ind_port.html), monthly, value-weighted. Source files use the 202609 CRSP database and were downloaded on 10 November 2026. Returns and errors below are in **monthly percentage points**.
- Fit each model on available observations within July 1963–December 2014 (546–618 months depending on industry). Compare its error on January 2015–December 2024 (120 months per industry). Missing observations are not filled.
- Market-only: industry return − risk-free rate = constant + market beta × (market return − risk-free rate) + error.
- Three-factor: add SMB (small minus big) and HML (value minus growth). Estimate the coefficients together by ordinary least squares.
- Error measure: RMSE, the square root of the mean squared monthly error. Smaller means the model describes those months more closely.

| Held-out result | Market only | Three factors |
| --- | ---: | ---: |
| Median industry RMSE, percentage points per month | 3.72 | 3.65 |
| Bank industry RMSE | 3.70 | 2.64 |
| Software industry RMSE | 3.93 | 4.38 |

The three-factor model had lower error in **37 of 49** industries; the market-only model did better in **12**. Banks and software are illustrative examples selected after inspecting the results. The median improvement is small, and the result is not universal.

**Important limit.** The comparison uses the factor returns that actually occurred in 2015–2024 and a 2026 revision of historical data. It is a held-out **ex-post explanation**, not a real-time forecast or a trading strategy. It does not establish that SMB and HML are the true priced APT factors. The earlier, broader project plan was simplified after the first results were seen, so this is an educational illustration rather than a pre-registered statistical test.

## Reproduce

Install `numpy`, `pandas`, and `matplotlib`, then run `python3 run.py`. The script downloads the two official ZIPs into `raw/` if absent, writes `outputs/results.csv`, and creates `outputs/chart.png`. Raw source ZIPs stay local. The [Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/data_library.html) can revise historical returns, so a later download may not match the included 202609 results exactly.
