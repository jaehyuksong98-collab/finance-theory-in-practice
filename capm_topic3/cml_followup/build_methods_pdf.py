"""Create a compact three-page methods report from checked analysis outputs."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parent
MAIN = json.loads((ROOT / "outputs_10y/summary.json").read_text())
SENS = list(csv.DictReader((ROOT / "lookback_sensitivity.csv").open(newline="")))
OUT = ROOT / "CML_Forward_Test_Methods.pdf"

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleX", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=19, leading=22,
                          textColor=colors.HexColor("#17384e"), spaceAfter=10))
styles.add(ParagraphStyle(name="H1X", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=12,
                          leading=15, textColor=colors.HexColor("#156082"), spaceBefore=9, spaceAfter=5))
styles.add(ParagraphStyle(name="BodyX", parent=styles["BodyText"], fontName="Helvetica", fontSize=9,
                          leading=12.8, spaceAfter=6))
styles.add(ParagraphStyle(name="SmallX", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.5,
                          leading=10.2, spaceAfter=5, textColor=colors.HexColor("#435667")))


def p(text: str, style: str = "BodyX") -> Paragraph:
    return Paragraph(text, styles[style])


def table(rows, widths):
    item = Table(rows, colWidths=widths, hAlign="LEFT", repeatRows=1)
    item.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f1f5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#17384e")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("LEADING", (0, 0), (-1, -1), 10.5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, 0), .6, colors.HexColor("#91afc0")),
        ("LINEBELOW", (0, 1), (-1, -2), .2, colors.HexColor("#dce5ea")),
    ]))
    return item


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#cbd5df"))
    canvas.line(18 * mm, 16 * mm, 192 * mm, 16 * mm)
    canvas.setFillColor(colors.HexColor("#506577"))
    canvas.setFont("Helvetica", 7.3)
    canvas.drawString(18 * mm, 12 * mm, "CAPM lecture follow-up | Methods | 27 October 2026")
    canvas.drawRightString(192 * mm, 12 * mm, str(doc.page))
    canvas.restoreState()


story = [p("Does a past optimal mix stay optimal?", "TitleX"),
         p("A rolling, out-of-sample teaching exercise on the capital allocation line", "H1X"),
         p("<b>Question.</b> When three U.S. equity portfolio groups are available, does a mix chosen for its highest <i>past</i> Sharpe ratio achieve a higher Sharpe ratio in the following year than a simple equal mix? This illustrates the gap between a classroom efficient-frontier diagram and an implementable estimate. It is not a direct test of the CAPM's complete-market portfolio."),
         p("<b>Result.</b> Over 53 July-June test years (July 1973-June 2026), the past 10-year choice realized a pooled Sharpe of <b>0.431</b> versus <b>0.492</b> for equal weighting. The difference is -0.062; a descriptive paired year-block bootstrap interval is [-0.246, +0.114]. No clear risk-adjusted advantage is established."),
         table([
             ["Outcome, 1973-2026", "Excess mean / yr", "Volatility / yr", "Sharpe"],
             ["Prior 10-year Sharpe choice", "5.67%", "13.16%", "0.431"],
             ["Equal three-group mix", "8.54%", "17.35%", "0.492"],
             ["U.S. market proxy", "8.01%", "15.91%", "0.504"],
         ], [60*mm, 37*mm, 37*mm, 29*mm]),
         Spacer(1, 3*mm),
         Image(str(ROOT / "outputs_10y/out_of_sample_sharpe.png"), width=163*mm, height=83*mm),
         p("Figure 1. Realized annualized Sharpe ratios from 636 subsequent monthly observations; gross, before costs. Source: Kenneth R. French Data Library, 202608 CRSP snapshot, retrieved 17 October 2026; calculations 27 October 2026. The bootstrap interval includes zero.", "SmallX"),
         PageBreak(),
         p("1. Theory and decision rule", "TitleX"),
         p("The theoretical <b>capital market line</b> plots expected return against total volatility for efficient combinations of a risk-free asset and the complete market portfolio. The observed chart below is a <b>subset frontier</b> for three historical equity portfolio groups. The dashed cash-to-risky line stops at the selected mix because this test does not allow borrowing."),
         p("At each June formation date, use only the previous 120 monthly observations to estimate mean excess returns and their sample covariance. Search all 5,151 nonnegative three-asset weight combinations in 1% steps, summing to 100%. Select the mix with maximum fitted annualized Sharpe; if every candidate's Sharpe is nonpositive, hold the source risk-free proxy. Apply the chosen weights to the <i>next</i> 12 months, rebalancing monthly. Repeat for each complete year."),
         Image(str(ROOT / "outputs_10y/historical_frontier.png"), width=163*mm, height=98*mm),
         p("Figure 2. Final estimation window: July 2015-June 2025. The selected point was 40% low-beta, 60% middle-beta, 0% high-beta. Those weights were then evaluated over July 2025-June 2026. Source and vintage as Figure 1. This line is estimated from past data, not a forward market CML.", "SmallX"),
         p("<b>Definitions.</b> Monthly excess return = sum of weights times (portfolio total return minus monthly RF). Annual arithmetic excess mean = 12 times the monthly mean. Annualized volatility = square root of 12 times monthly sample standard deviation. Annualized Sharpe = annualized excess mean divided by annualized volatility. All source values are percentages per month; these are not compounded annual returns."),
         PageBreak(),
         p("2. Sensitivity, checks and interpretation", "TitleX"),
         p("Changing the return-estimation history changes the result. The table compares all three choices on the <b>same</b> July 1978-June 2026 test months (576 months). The first page's 10-year result starts five years earlier, so its Sharpe is not directly the 10-year number here."),
         table([
             ["History used at June", "Selected Sharpe", "Equal Sharpe", "Difference"],
             *[[f"{row['lookback_years']} years", f"{float(row['selected_sharpe']):.3f}",
                f"{float(row['equal_sharpe']):.3f}", f"{float(row['selected_minus_equal_sharpe']):+.3f}"]
               for row in SENS],
         ], [57*mm, 38*mm, 35*mm, 33*mm]),
         p("<b>Independent raw-data check.</b> The official July 2025 value-weighted return row gives -2.01% for low beta and -0.62% for middle beta; the factors row gives RF = 0.34%. With selected weights 40%/60%, the next-month excess return is 0.4 x (-2.01 - 0.34) + 0.6 x (-0.62 - 0.34) = <b>-1.516%</b>, matching the generated monthly record. Code also rejects mismatched source snapshot labels, incomplete July-June years, overlapping training/test dates and unexpected shared-window dates."),
         p("<b>What can be inferred?</b> The 10-year selected mix had less volatility and less average excess return than the equal mix. Its lower average alone is not a failure of risk-adjusted choice. The risk-adjusted difference's interval includes zero, and a 15-year lookback has a higher observed Sharpe than equal weighting on the common window. Thus this particular historical exercise shows <i>instability across design choices</i>, not a universal winner."),
         p("<b>Practical judgement.</b> State the asset universe, estimation period, objective, constraints and holding period before calling a portfolio optimal. Examine a simple benchmark and a later, untouched outcome period. Do not pick the lookback retrospectively because it happens to win this sample. Retain new data releases as dated snapshots and flag historical revisions for human review before updating conclusions."),
         p("<b>Limits.</b> The complete market portfolio, investor beliefs and true expected returns are not observed. This is an exploratory follow-up to an earlier CAPM analysis; the asset groups were not chosen blind to all historical returns. These historical groups are not directly investable funds. Trading costs, taxes, turnover and financing frictions are excluded. The fixed 202608 CRSP snapshot can later be revised, and the risk-free proxy's data provider changes in June 2024. Overlapping rolling training windows and serial dependence qualify the year-block bootstrap interval. No causal or live-trading claim follows."),
         p("3. Sources and reproducibility", "H1X"),
         p('[<link href="https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/data_library.html" color="#156082">Kenneth R. French Data Library and definitions</link>]; [<link href="https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/ftp/Portfolios_Formed_on_BETA_CSV.zip" color="#156082">Portfolios Formed on Market Beta, CSV ZIP</link>]; [<link href="https://mba.tuck.dartmouth.edu/pages/faculty/Ken.French/ftp/F-F_Research_Data_Factors_CSV.zip" color="#156082">Fama/French 3 Research Factors, CSV ZIP</link>]. Both ZIP headers identify the 202608 CRSP database and were downloaded 17 October 2026. Theory: [<link href="https://doi.org/10.1111/j.1540-6261.1964.tb02865.x" color="#156082">Sharpe (1964), Capital Asset Prices</link>]. Private course reference: Investment Analysis, Topic 3 CAPM, pp. 3-6.'),
         p("The Python scripts, source SHA-256 manifest, derived monthly and annual CSVs, and charts accompany this report. The original source ZIPs and private lecture notes are not redistributed.", "SmallX")]

doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=18*mm, rightMargin=18*mm,
                        topMargin=16*mm, bottomMargin=21*mm,
                        title="Does a past optimal mix stay optimal? - methods", author="JaeHyuk Song")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUT)
