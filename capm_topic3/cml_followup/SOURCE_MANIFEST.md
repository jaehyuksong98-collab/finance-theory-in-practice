# Source manifest — CML follow-up

The files were retrieved **17 October 2026** from the [Kenneth R. French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/data_library.html). Their headers identify the **202608 CRSP database**. Calculations were completed 27 October 2026. The course file `Investment Analysis/Lecture notes/Topic 3 CAPM.pdf` was a private teaching reference and is not distributed.

| Input | Official file | SHA-256 of local ZIP | Units and use |
| --- | --- | --- | --- |
| Portfolios Formed on Market Beta | [ZIP](https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/ftp/Portfolios_Formed_on_BETA_CSV.zip) | `fb317445a0160c694ee2773d1718490259e1c6873f1490191efc9ec3bcc1b65e` | Monthly value-weighted percent total returns; `Lo 10`, `Dec 5`, `Hi 10` |
| Fama/French 3 Research Factors | [ZIP](https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/ftp/F-F_Research_Data_Factors_CSV.zip) | `593f4fbef03181bc0b22ff6292f217689dd1fb79355049ca905d95b262040a66` | Monthly percent `Mkt-RF` and `RF` |

The source library documents portfolio formation, June rebalancing, breakpoints and data revisions. The beta portfolios group eligible NYSE, AMEX and NASDAQ firms using NYSE breakpoints; `RF` is a Treasury-bill proxy whose underlying data provider changes from June 2024. The original ZIP files are not redistributed. [Sharpe (1964)](https://doi.org/10.1111/j.1540-6261.1964.tb02865.x) supplies the theoretical capital-market-line setting, not these realized inputs.

Independent spot check: the original value-weighted July 2025 row reports `Lo 10 = −2.01%`, `Dec 5 = −0.62%`, and `Hi 10 = 8.41%`, while the factors row reports `RF = 0.34%` and `Mkt-RF = 1.98%`. With the June 2025 selected weights 40%/60%/0%, July 2025 selected excess return is `0.4×(−2.01−0.34)+0.6×(−0.62−0.34)=−1.516%`, matching `outputs_10y/monthly_oos.csv`. This verifies one raw-to-output row independently of the analysis parser.
