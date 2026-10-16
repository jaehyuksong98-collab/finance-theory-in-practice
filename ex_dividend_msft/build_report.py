"""Build the short English methods report from validated pilot inputs."""

import csv
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output" / "MSFT_Ex_Dividend_Methods_2026-10-16.pdf"


def para(text, style="BodyText"):
    return Paragraph(text, STYLES[style])


STYLES = getSampleStyleSheet()
STYLES.add(ParagraphStyle(name="TitleCustom", parent=STYLES["Title"], fontName="Helvetica-Bold", fontSize=18, leading=21, textColor=colors.HexColor("#173f63"), spaceAfter=12))
STYLES.add(ParagraphStyle(name="SectionCustom", parent=STYLES["Heading2"], fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=colors.HexColor("#173f63"), spaceBefore=12, spaceAfter=5))
STYLES.add(ParagraphStyle(name="SmallCustom", parent=STYLES["BodyText"], fontName="Helvetica", fontSize=8.3, leading=11.3, spaceAfter=5))
STYLES.add(ParagraphStyle(name="CaptionCustom", parent=STYLES["BodyText"], fontName="Helvetica", fontSize=8, leading=10.5, textColor=colors.HexColor("#50677a"), spaceAfter=8))
STYLES["BodyText"].fontName = "Helvetica"
STYLES["BodyText"].fontSize = 9
STYLES["BodyText"].leading = 12.5
STYLES["BodyText"].spaceAfter = 7


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#657788"))
    canvas.drawString(43, 28, "Finance Theory in Practice 01 | Data checked 16 Oct 2026")
    canvas.drawRightString(570, 28, f"{doc.page}")
    canvas.restoreState()


def main():
    with (ROOT / "output" / "event_results.csv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    story = []
    story.append(para("Does a stock fall by the cash dividend on the ex-date?", "TitleCustom"))
    story.append(para("A four-event Microsoft pilot | Methods and source audit | 16 October 2026", "CaptionCustom"))
    story.append(para("<b>Finding.</b> The simple -$0.91 per-share benchmark did not describe any of the four observed closing moves. The ex-date opening price was lower than the previous close once; the ex-date closing price was lower all four times. These observations do not identify the dividend's causal price effect."))
    story.append(para("Question and theory", "SectionCustom"))
    story.append(para("Corporate Finance Lecture 4 defines the ex-dividend date as the entitlement cutoff. A buyer on that date does not receive the cash dividend. With no other new information or market movement, the stock should lose roughly the distributed cash per share. Nasdaq Global Indexes illustrates this benchmark in Chart 1 of its August 2025 note. The testable descriptive question here is whether the observed opening or closing change equals -D, where D is the ordinary dividend per share."))
    story.append(para("Data, dates and calculation", "SectionCustom"))
    story.append(para("Four Microsoft ordinary dividends from 20 Nov 2025 to 20 Aug 2026, each $0.91 per share. Official Microsoft releases establish the dates and amounts. Nasdaq MSFT Historical Quotes supplies the displayed prior-day close and ex-date open/close in USD per share. Data were retrieved 16 Oct 2026. No dividend-adjusted closing prices were used. This pilot transcribes only the event rows rather than redistributing a full Nasdaq history."))
    table_data = [["Ex-date", "Prev close", "Ex open", "Ex close", "Open change", "Close change"]]
    for r in rows:
        table_data.append([r["ex_date"], f"${float(r['prior_close_usd']):.2f}", f"${float(r['ex_open_usd']):.2f}", f"${float(r['ex_close_usd']):.2f}", f"{float(r['opening_change_usd']):+.2f}", f"{float(r['closing_change_usd']):+.2f}"])
    t = Table(table_data, colWidths=[92, 72, 72, 72, 84, 84], repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#173f63")), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"), ("FONTNAME", (0,1), (-1,-1), "Helvetica"), ("FONTSIZE", (0,0), (-1,-1), 8), ("BOTTOMPADDING", (0,0), (-1,-1), 7), ("TOPPADDING", (0,0), (-1,-1), 7), ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f2f6f8")]), ("LINEBELOW", (0,-1), (-1,-1), 0.5, colors.HexColor("#b8c9d4"))]))
    story.append(t)
    story.append(Spacer(1, 7))
    story.append(para("Benchmark price = prior close - D. Opening change = ex open - prior close; closing change = ex close - prior close. Residual = observed change + D. Simple dividend-inclusive close-to-close return = (ex close + D - prior close) / prior close. Price levels and changes are USD per share; returns are percentages of the prior close.", "SmallCustom"))
    story.append(para("20 Nov 2025 check: $492.71 - $487.12 = +$5.59 at the open; $478.43 - $487.12 = -$8.69 at the close. The dividend yield was $0.91 / $487.12 = 0.187% of the prior close. The closing residual against -$0.91 was -$7.78 per share.", "SmallCustom"))
    story.append(Spacer(1, 9))
    chart = Image(str(ROOT / "output" / "ex_date_comparison.png"), width=7.15*inch, height=3.83*inch)
    story.append(chart)
    story.append(para("Figure 1. Theoretical -$0.91 per share versus observed close-to-open and close-to-close changes. Sources: Microsoft announcements; Nasdaq MSFT Historical Quotes. Data through 20 Aug 2026, retrieved 16 Oct 2026.", "CaptionCustom"))
    story.append(para("Interpretation, checks and limits", "SectionCustom"))
    story.append(para("The ex-date adjustment is one component of a market price. Overnight news and index moves affect the opening; intraday trading adds noise to the close. The four dividend yields ranged from about 0.19% to 0.23% of the previous close, smaller than several observed daily moves. All four closing changes were negative, but their magnitudes ranged from -$1.14 to -$8.69. A negative close is therefore not proof that the dividend alone caused the drop."))
    story.append(para("The code checks duplicate events, date order, positive prices and source URLs. The four Nasdaq closing-price pairs were cross-checked against Yahoo Finance's split-adjusted Close column, not its dividend-adjusted Adj Close. Calculations are regenerated from CSV. The result is sensitive to price adjustment conventions. This sample is one issuer, four observations, and has no market, sector or company-news control. It is unsuitable for a statistical or trading claim."))
    story.append(para("Repeated tracking workflow", "SectionCustom"))
    story.append(para("1. Read the issuer's cash-dividend announcement and record ex-date, amount and type. 2. Record prior trading day and ex-date raw prices with retrieval date and source URL. 3. Manually inspect splits, special dividends and material company news. 4. Ingest the reviewed CSV as a dated immutable snapshot; changed rows require an explicit revision flag. 5. Regenerate calculations and Figure 1. 6. Later expand to a pre-specified multi-company panel with market-adjusted returns and uncertainty intervals. The current scripts do not automatically collect or verify announcements."))
    story.append(para("Primary sources", "SectionCustom"))
    refs = [
        ("Nasdaq Global Indexes, Total Return without the Dividend?, Aug 2025, p. 1 / Chart 1", "https://www.nasdaq.com/docs/total-return-without-the-dividend"),
        ("Microsoft dividend release, 15 Sep 2025", "https://news.microsoft.com/source/2025/09/15/microsoft-announces-quarterly-dividend-increase-6/"),
        ("Microsoft dividend release, 2 Dec 2025", "https://news.microsoft.com/source/2025/12/02/microsoft-announces-quarterly-dividend-27/"),
        ("Microsoft dividend release, 10 Mar 2026", "https://news.microsoft.com/source/2026/03/10/microsoft-announces-quarterly-dividend-28/"),
        ("Microsoft dividend release, 10 Jun 2026", "https://news.microsoft.com/source/2026/06/10/microsoft-announces-quarterly-dividend-29/"),
        ("Nasdaq MSFT Historical Quotes, retrieved 16 Oct 2026", "https://www.nasdaq.com/market-activity/stocks/msft/historical"),
        ("Yahoo Finance MSFT Historical Prices, Close-column cross-check", "https://finance.yahoo.com/quote/MSFT/history/"),
    ]
    for label, url in refs:
        story.append(para(f'<link href="{url}" color="#1a5b85">{label}</link>', "SmallCustom"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUT), pagesize=(612, 792), rightMargin=43, leftMargin=43, topMargin=39, bottomMargin=45)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUT)


if __name__ == "__main__":
    main()
