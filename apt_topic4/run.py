"""Simple APT illustration: market-only versus Fama–French three factors.

Run: python3 run.py
Needs: numpy, pandas, matplotlib. The two official ZIPs are downloaded only
if absent. Source values and RMSE are in monthly percentage points.
"""

from io import StringIO
from pathlib import Path
import re
from urllib.request import urlretrieve
from zipfile import ZipFile

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
OUT = ROOT / "outputs"
BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/ftp/"
FILES = {
    "factors.zip": ("F-F_Research_Data_Factors_CSV.zip", ",Mkt-RF,SMB,HML,RF"),
    "industries.zip": ("49_Industry_Portfolios_CSV.zip", ",Agric,Food"),
}


def read_monthly(local_name, remote_name, header_start):
    RAW.mkdir(exist_ok=True)
    path = RAW / local_name
    if not path.exists():
        urlretrieve(BASE + remote_name, path)
    with ZipFile(path) as archive:
        lines = archive.read(archive.namelist()[0]).decode("latin1").splitlines()
    match = re.search(r"\b\d{6}\b", lines[0])
    if not match:
        raise ValueError("Source vintage missing from official file")
    start = next(i for i, line in enumerate(lines) if line.startswith(header_start))
    block = [lines[start]]
    for line in lines[start + 1 :]:
        if not line[:6].isdigit():
            break
        block.append(line)
    data = pd.read_csv(StringIO("\n".join(block)), na_values=[-99.99, -999])
    data.columns = ["month", *[str(c).strip() for c in data.columns[1:]]]
    if data.month.duplicated().any():
        raise ValueError("Duplicate month in official file")
    return data, match.group()


def fit(x, y):
    return np.linalg.lstsq(np.column_stack([np.ones(len(x)), x]), y, rcond=None)[0]


def error(x, y, coefficients):
    difference = y - np.column_stack([np.ones(len(x)), x]) @ coefficients
    return float(np.sqrt(np.mean(difference**2)))


def main():
    factors, factor_vintage = read_monthly("factors.zip", *FILES["factors.zip"])
    sectors, sector_vintage = read_monthly("industries.zip", *FILES["industries.zip"])
    if factor_vintage != sector_vintage:
        raise ValueError("Factor and industry source vintages differ")
    data = factors.merge(sectors, on="month", validate="one_to_one")
    assert len(sectors.columns) == 50  # month + 49 industries
    results = []
    for sector in sectors.columns[1:]:
        rows = data[["month", "RF", "Mkt-RF", "SMB", "HML", sector]].dropna()
        train = rows[rows.month.between(196307, 201412)]
        test = rows[rows.month.between(201501, 202412)]
        if len(train) < 120 or len(test) != 120:
            raise ValueError(f"Missing months for {sector}")
        y_train = (train[sector] - train.RF).to_numpy()
        y_test = (test[sector] - test.RF).to_numpy()
        market = ["Mkt-RF"]
        three = ["Mkt-RF", "SMB", "HML"]
        market_fit = fit(train[market].to_numpy(), y_train)
        three_fit = fit(train[three].to_numpy(), y_train)
        results.append(
            {
                "industry": sector,
                "market_rmse_pctpt": error(test[market].to_numpy(), y_test, market_fit),
                "three_factor_rmse_pctpt": error(test[three].to_numpy(), y_test, three_fit),
            }
        )
    result = pd.DataFrame(results).sort_values("industry")
    OUT.mkdir(exist_ok=True)
    result.to_csv(OUT / "results.csv", index=False, float_format="%.6f")
    better = result.three_factor_rmse_pctpt < result.market_rmse_pctpt
    x, y = result.market_rmse_pctpt, result.three_factor_rmse_pctpt
    print(f"Source vintage: {factor_vintage}")
    print(f"Three factors lower error: {better.sum()} of {len(result)} industries")
    print(f"Median monthly error: market {x.median():.2f}, three factors {y.median():.2f} percentage points")
    for sector in ("Banks", "Softw"):
        row = result[result.industry == sector].iloc[0]
        print(f"{sector}: {row.market_rmse_pctpt:.2f} -> {row.three_factor_rmse_pctpt:.2f} percentage points")

    fig, ax = plt.subplots(figsize=(8, 7), dpi=170)
    limit = max(x.max(), y.max()) + 0.3
    ax.plot([0, limit], [0, limit], "--", color="#83909d", label="Equal error")
    ax.scatter(x[better], y[better], color="#176b88", label=f"3 factors better ({better.sum()})")
    ax.scatter(x[~better], y[~better], color="#bd6a34", label=f"Market only better ({(~better).sum()})")
    ax.set(xlim=(0, limit), ylim=(0, limit), xlabel="Market-only RMSE (monthly percentage points)", ylabel="Three-factor RMSE (monthly percentage points)")
    ax.set_aspect("equal")
    ax.grid(alpha=0.2)
    ax.legend(frameon=False)
    fig.suptitle("Do three factors explain industry returns more closely?", fontweight="bold")
    fig.text(0.12, 0.08, "49 US industries | fit: Jul 1963–Dec 2014 | compare: Jan 2015–Dec 2024", fontsize=8)
    fig.text(0.12, 0.055, f"Source: Kenneth R. French Data Library, {factor_vintage} snapshot. Realized factors: explanation, not forecast.", fontsize=8)
    fig.subplots_adjust(bottom=0.16)
    fig.savefig(OUT / "chart.png", bbox_inches="tight")


if __name__ == "__main__":
    main()
