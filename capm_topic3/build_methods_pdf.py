"""Build the three-page CAPM methods note from verified derived outputs."""

from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "CAPM_Topic3_Methods.pdf"
DATA = json.loads((ROOT / "outputs/summary.json").read_text())
DECS = DATA["deciles"]

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleX", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=colors.HexColor("#15364d"), spaceAfter=12))
styles.add(ParagraphStyle(name="H1X", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=colors.HexColor("#156082"), spaceBefore=9, spaceAfter=5))
styles.add(ParagraphStyle(name="BodyX", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.4, leading=13.2, spaceAfter=7))
styles.add(ParagraphStyle(name="SmallX", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.6, leading=10.4, spaceAfter=5, textColor=colors.HexColor("#415363")))


def p(text: str, style: str = "BodyX") -> Paragraph:
    return Paragraph(text, styles[style])


def bullet(text: str) -> Paragraph:
    return p("&#8226; " + text)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#cbd5df"))
    canvas.line(18 * mm, 16 * mm, 192 * mm, 16 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#506577"))
    canvas.drawString(18 * mm, 12 * mm, "CAPM in the real world | Research note | 17 October 2026")
    canvas.drawRightString(192 * mm, 12 * mm, str(doc.page))
    canvas.restoreState()


def table(rows, widths):
    t = Table(rows, colWidths=widths, hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f1f5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#15364d")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.4),
        ("LEADING", (0, 0), (-1, -1), 11),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, 0), .7, colors.HexColor("#91afc0")),
        ("LINEBELOW", (0, 1), (-1, -2), .25, colors.HexColor("#dce5ea")),
    ]))
    return t


story = []
story.append(p("CAPM in the real world", "TitleX"))
story.append(p("A lecture-wide, reproducible check of beta and later returns", "H1X"))
story.append(p("<b>Question.</b> Does a higher beta estimated before portfolio formation correspond to a higher subsequent excess return? The CAPM itself is a statement about <i>expected</i> equilibrium returns, so realized data provide a diagnostic rather than a decisive test."))
story.append(table([
    ["Measure", "Low beta", "High beta"],
    ["Average prior beta", f"{DECS[0]['mean_prior_beta']:.2f}", f"{DECS[-1]['mean_prior_beta']:.2f}"],
    ["Later average excess return", f"{DECS[0]['annualized_arithmetic_excess_pct']:.2f}%/yr", f"{DECS[-1]['annualized_arithmetic_excess_pct']:.2f}%/yr"],
    ["Ex-post CAPM line value", f"{DECS[0]['mean_prior_beta']*DATA['annualized_arithmetic_market_excess_pct']:.2f}%/yr", f"{DECS[-1]['mean_prior_beta']*DATA['annualized_arithmetic_market_excess_pct']:.2f}%/yr"],
], [82 * mm, 42 * mm, 42 * mm]))
story.append(Spacer(1, 5 * mm))
img = Image(str(ROOT / "outputs/beta_deciles_vs_capm.png"), width=165 * mm, height=95 * mm)
story.append(img)
story.append(p("Figure 1. Observed U.S. beta-decile means and an ex-post CAPM reference line. Value-weighted monthly total returns, complete July 1963-June 2026 holding years. Source: Fama/French Data Library, 202608 CRSP snapshot, retrieved 17 October 2026. The line uses the <i>realized</i> market premium and is not a forecast.", "SmallX"))
story.append(PageBreak())

story.append(p("1. Theory mapped to observable quantities", "TitleX"))
story.append(p("<b>Security market line:</b> expected asset excess return = market beta x expected market excess return. Beta = Cov(asset, market) / Var(market). <b>Capital market line:</b> only efficient combinations of the risk-free asset and the theoretical market portfolio lie on this total-volatility/expected-return line. These two lines answer different questions."))
story.append(p("<b>Regression and risk decomposition:</b> observed asset excess return = alpha + beta x observed market excess return + residual. In an OLS regression with intercept, total return variance = beta-squared x market variance + residual variance; R-squared is the explained share of historical variance. Alpha is a model-specific historical intercept, not proof of skill."))
story.append(p("<b>What is testable?</b> We can check whether June-formed beta groups have a roughly linear relation with later average returns. We cannot observe every investor's beliefs, the complete wealth market portfolio, or the true forward expected market premium."))
story.append(p(f"The observed U.S. stock-market proxy had a mean excess return of {DATA['market_excess_monthly_pct']:.2f}% per month and monthly standard deviation of {DATA['market_excess_monthly_sd_pct']:.2f}%; its ex-post annualized Sharpe ratio was {DATA['market_ex_post_annualized_sharpe']:.2f}. This describes one proxy and does not prove CML efficiency."))
story.append(p("2. Data and pre-defined comparison", "H1X"))
story.append(bullet("Universe: eligible NYSE, AMEX and NASDAQ stocks; NYSE beta breakpoints. June formation uses the previous 60 monthly returns, requiring at least 24, with the Scholes-Williams beta method. The file provides portfolio-level value-weighted prior beta and later monthly total returns."))
story.append(bullet("Time: 63 complete non-overlapping July-June holding years, July 1963-June 2026. July-August 2026 is available but omitted from full-year comparisons. Each decile contributes 756 monthly returns."))
story.append(bullet("Units: each source return, market premium and risk-free rate is a percentage <i>per month</i>. Portfolio excess return = portfolio total return - monthly RF. Annualized arithmetic mean = 12 x mean monthly percentage; it is not a geometric compounded return."))
story.append(bullet("Main benchmark: compare average prior beta with later mean excess return across ten groups. The dashed line uses the <i>realized</i> sample market premium of 7.21% per year. It is an ex-post reference, not a prospective cost of equity."))
story.append(bullet("Uncertainty: resample the 63 whole formation years, 10,000 times with a fixed seed, to form a descriptive 95% interval for the high-minus-low average. This retains monthly clustering inside a holding year."))
story.append(p("3. Reproducibility checks", "H1X"))
story.append(bullet("The script requires matching CRSP snapshot labels across source ZIPs, joins the same month in portfolio and factor files, checks that every included holding year has twelve months, rejects missing sentinels, and confirms the prior betas are ordered across deciles."))
story.append(bullet("Independent spot check: the source's July 2025-June 2026 high-minus-low monthly returns sum to 9.38 percentage points, giving 0.7817 percentage points per month, exactly matching the generated yearly table."))
story.append(PageBreak())

story.append(p("4. Results, use and limits", "TitleX"))
spread = DATA["annualized_arithmetic_high_minus_low_pct"]
ci = DATA["high_minus_low_year_block_bootstrap_95pct_monthly"]
story.append(p(f"The high-beta group exceeded the low-beta group by <b>{spread:.2f} percentage points per year</b> on an arithmetic-average basis. The year-block bootstrap interval is <b>{12*ci[0]:+.2f} to {12*ci[1]:+.2f} percentage points per year</b>. The second-highest beta group's mean excess return ({DECS[-2]['annualized_arithmetic_excess_pct']:.2f}%/yr) exceeded the highest group's ({DECS[-1]['annualized_arithmetic_excess_pct']:.2f}%/yr). This sample therefore does not trace the simple rising SML picture."))
ts = DATA["time_series_regressions"]
story.append(p(f"A same-sample time-series regression gives beta {ts[0]['regression_beta']:.2f} and R-squared {ts[0]['r_squared']:.2f} for the low group, versus beta {ts[-1]['regression_beta']:.2f} and R-squared {ts[-1]['r_squared']:.2f} for the high group. These full-period regression betas are <i>not</i> the past betas used to assign stocks each June; changing portfolios and estimators matter."))
story.append(Image(str(ROOT / "outputs/risk_decomposition.png"), width=158 * mm, height=74 * mm))
story.append(p("Figure 2. Historical market-explained versus residual variance by beta decile. R-squared and 1 - R-squared from one-factor monthly regressions; same source snapshot and sample as Figure 1. This is not a forecast of future risk.", "SmallX"))
story.append(p("<b>Size check:</b> Within each of five size groups, the beta-high minus beta-low portfolio had a positive mean gross return spread in this snapshot, but the arithmetic annualized spreads ranged from 0.28 to 2.71 percentage points. This does not establish that beta alone causes a premium. The size-by-beta cells have different constituents and the analysis omits trading costs and other risk factors."))
story.append(p("<b>Practical use:</b> For a cost-of-equity estimate, an analyst needs a forward-looking risk-free rate, a defensible forward market premium and a beta matched to the company's business and leverage. Change each assumption in sensitivity analysis. Historical beta is useful exposure information; historical market returns should not be inserted mechanically as future expectations."))
story.append(p("<b>Important limits:</b> The theoretical market includes non-listed wealth and human capital, while this data uses a U.S. listed-equity proxy. Regression residuals can include omitted common factors, so they are not pure firm-specific risk. Realized returns are noisy; source histories can be revised; beta changes with time; sample selection, taxes, turnover and leverage can alter results. The Data Library changed CRSP monthly-return processing in its 2025 release. No causal claim or universal trading rule follows from this descriptive test."))
story.append(p("5. Sources and next update", "H1X"))
story.append(p('Fama/French [<link href="https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/data_library.html" color="#156082">Data Library and definitions</link>], [<link href="https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/ftp/Portfolios_Formed_on_BETA_CSV.zip" color="#156082">beta portfolios</link>], [<link href="https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/ftp/F-F_Research_Data_Factors_CSV.zip" color="#156082">three research factors</link>], and [<link href="https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/ftp/25_Portfolios_ME_BETA_5x5_CSV.zip" color="#156082">size x beta portfolios</link>]. All use the 202608 CRSP snapshot, retrieved 17 October 2026.'))
story.append(p('Theory context: Fama and French (1992), [<link href="https://doi.org/10.1111/j.1540-6261.1992.tb04398.x" color="#156082">The Cross-Section of Expected Stock Returns</link>]; Roll (1977), [<link href="https://www.anderson.ucla.edu/documents/areas/fac/finance/1977-2.pdf" color="#156082">A Critique of the Asset Pricing Theory\'s Tests</link>]. Private course reference: Investment Analysis, Topic 3 CAPM, pp. 4-20.'))
story.append(p("Source files remain at their publishers. The Python parser, generated summaries and chart are ready for user review. New data should be saved with its release date, compared against the prior snapshot and checked by a person before updating this conclusion.", "SmallX"))

doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=17*mm, bottomMargin=21*mm, title="CAPM in the real world — methods", author="JaeHyuk Song")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUT)
