# CAPM in the real world — lecture-wide study

This project turns `Investment Analysis/Lecture notes/Topic 3 CAPM.pdf` (20 pages) into a student-friendly empirical explanation. The lecture PDF is a private reference and is not redistributed.

## Questions from the lecture

| Pages | Idea | What can be checked with market data? |
| --- | --- | --- |
| 3–6 | Risk/return choice, common efficient risky portfolio, capital market line | Illustrate the market risk premium and efficient-frontier benchmark; the full market portfolio and investor preferences are not directly observed. |
| 7–13 | Security market line, beta, alpha, systematic versus residual risk | Estimate beta and alpha for diversified beta-sorted portfolios. Compare realized average excess returns with a retrospective CAPM benchmark. |
| 14–17 | Time-series and cross-sectional estimation, variance decomposition | Keep prior beta and later returns separate; calculate time-series regression and variance shares. |
| 18–20 | Empirical predictions and critiques | Check whether higher prior beta predicts higher later excess returns, across years and after conditioning on firm size. Discuss market-proxy and model assumptions. |

**Important:** CAPM is about expected returns in equilibrium. A realized-return test is a noisy diagnostic, not a proof or disproof of the theorem. A portfolio constructed using past beta is not a random sample of securities.

## Source, snapshot and measurement

All figures in the analysis use the August 2026 Kenneth R. French Data Library snapshot, retrieved 17 October 2026:

- [Portfolios Formed on Market Beta](https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/ftp/Portfolios_Formed_on_BETA_CSV.zip) — monthly value-weighted portfolio total returns in percent and value-weighted average *prior* beta by June formation year. Beta is estimated with the Scholes–Williams method from up to 60 prior monthly returns, at least 24 required. NYSE breakpoints; eligible NYSE, AMEX and NASDAQ firms.
- [Fama/French 3 Research Factors](https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/ftp/F-F_Research_Data_Factors_CSV.zip) — monthly `Mkt-RF` and `RF`, both percent per month. `RF` is a one-month Treasury bill proxy; its underlying provider changes in June 2024.
- [25 Portfolios Formed on Size and Market Beta](https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/ftp/25_Portfolios_ME_BETA_5x5_CSV.zip) — size-conditioned robustness check.
- [Library definitions and revision notes](https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/data_library.html). The library can reconstruct and revise historical returns each month. It changed its CRSP return processing format starting with the January 2025 release.

The files are copyrighted by Fama and French. This repository contains analysis code and derived summary outputs; download the original ZIPs from their library yourself. Do not upload the raw ZIPs to GitHub.

## Run

```bash
python3 analyze.py \
  --beta-zip /path/to/Portfolios_Formed_on_BETA_CSV.zip \
  --factors-zip /path/to/F-F_Research_Data_Factors_CSV.zip \
  --size-beta-zip /path/to/25_Portfolios_ME_BETA_5x5_CSV.zip \
  --out outputs
```

Python 3.10+ standard library handles parsing and calculations. Matplotlib is optional for PNG charts (`python3 -m pip install matplotlib`). The script checks date alignment, missing sentinels, beta ordering, and matching source snapshot labels. It restricts the main test to complete July–June holding years. The most recent full holding year in this snapshot ends June 2026; July–August 2026 is excluded from full-year comparisons.

For later library releases, run `update_snapshot.py` with the same three ZIP arguments. It saves each release in `snapshots/YYYYMM/` with SHA-256 hashes and a revision report comparing common historical holding years. It refuses to overwrite a release folder. The script flags candidate changes; a person must inspect the publisher's new files before changing the published interpretation. Source downloads are manual so no unattended job silently substitutes revised source data.

## Interpretation guardrails

- Monthly source returns are percentages, not decimal fractions. Annualized average figures are `12 × arithmetic monthly mean`, not compound annual growth rates.
- High-minus-low return differences cancel the common monthly risk-free rate. Gross returns omit trading cost, financing, turnover and taxes.
- The line using the **realized** market premium is an ex-post illustration. It is not an investable forecast or an independently estimated forward equity risk premium.
- Equal weighting of 63 June formation years keeps calendar windows separate. A bootstrap over formation years describes sampling variation across these windows, not causal certainty.
- The public market proxy omits private businesses, human capital, real estate and other wealth; Roll's critique therefore applies.
- The 2026 source snapshot can later be revised. Each later run should retain its source date and compare revisions before interpreting changes.

## Publication workflow

1. Verify the generated outputs against the source ZIPs and record the source snapshot.
2. Prepare the English LinkedIn Article, separate short feed introduction, methodology PDF, Korean review summary and chart captions.
3. Show the full package to the user for explicit approval.
4. After approval, publish to the **JaeHyuk Song personal profile** and update the GitHub repository.

The original lecture file is not published.
