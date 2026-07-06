"""
Builds the final due diligence report as a PDF using reportlab
(programmatic layout, no HTML/CSS rendering step -- avoids weasyprint's
native GTK/Pango/Cairo dependency, which isn't available on this
machine and is a common pain point on Windows/some deploy targets).
"""
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

_SEVERITY_COLORS = {
    "low": colors.HexColor("#3e5c8a"),
    "medium": colors.HexColor("#b8752e"),
    "high": colors.HexColor("#a3492a"),
    "critical": colors.HexColor("#a32a2a"),
}

_BRAND = colors.HexColor("#0f6b5c")


def _styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "ReportTitle", parent=styles["Title"], textColor=_BRAND, spaceAfter=4
        )
    )
    styles.add(
        ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            textColor=_BRAND,
            spaceBefore=16,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle("Body", parent=styles["BodyText"], leading=14, spaceAfter=6)
    )
    return styles


def _fmt_currency(value, currency="USD"):
    if value is None:
        return "—"
    return f"{currency} {value:,.0f}"


def generate_pdf_report(data: dict) -> bytes:
    """
    `data` shape (all keys optional except company_name):
    {
      "company_name": str,
      "health_score": float | None,
      "risk_score": float | None,
      "company": {"industry", "headquarters", "business_model", "products", "summary"} | None,
      "financials": [{"year", "revenue", "profit", "expenses", "assets",
                       "liabilities", "cash_flow", "debt", "currency"}, ...],
      "red_flags": [{"title", "category", "reason", "severity", "recommendation"}, ...],
      "executive_summary": {"company_summary", "financial_summary", "major_risks",
                             "opportunities", "future_outlook"} | None,
      "recommendations": [{"category", "recommendation", "rationale"}, ...],
    }
    """
    styles = _styles()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
    )
    story = []

    company_name = data.get("company_name") or "Untitled Investigation"
    story.append(Paragraph(f"{company_name} — Due Diligence Report", styles["ReportTitle"]))
    story.append(
        Paragraph(
            f"Financial Health Score: <b>{data.get('health_score') or '—'}</b>/100 &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Risk Score: <b>{data.get('risk_score') or '—'}</b>/100",
            styles["Body"],
        )
    )

    company = data.get("company")
    if company:
        story.append(Paragraph("Company Overview", styles["SectionHeading"]))
        if company.get("summary"):
            story.append(Paragraph(company["summary"], styles["Body"]))
        overview_rows = [
            [k, company.get(v) or "—"]
            for k, v in [
                ("Industry", "industry"),
                ("Headquarters", "headquarters"),
                ("Business Model", "business_model"),
                ("Products", "products"),
            ]
            if company.get(v)
        ]
        if overview_rows:
            story.append(_simple_table(overview_rows))

    financials = data.get("financials") or []
    if financials:
        story.append(Paragraph("Financial Analysis", styles["SectionHeading"]))
        header = ["Year", "Revenue", "Profit", "Expenses", "Debt", "Cash Flow"]
        rows = [header]
        for row in sorted(financials, key=lambda r: r["year"]):
            currency = row.get("currency") or "USD"
            rows.append(
                [
                    str(row["year"]),
                    _fmt_currency(row.get("revenue"), currency),
                    _fmt_currency(row.get("profit"), currency),
                    _fmt_currency(row.get("expenses"), currency),
                    _fmt_currency(row.get("debt"), currency),
                    _fmt_currency(row.get("cash_flow"), currency),
                ]
            )
        table = Table(rows, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), _BRAND),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e4e3de")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f7f4")]),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(table)

        story.append(Paragraph("Timeline", styles["SectionHeading"]))
        for row in sorted(financials, key=lambda r: r["year"]):
            currency = row.get("currency") or "USD"
            story.append(
                Paragraph(
                    f"<b>{row['year']}</b> — Revenue {_fmt_currency(row.get('revenue'), currency)}, "
                    f"Profit {_fmt_currency(row.get('profit'), currency)}",
                    styles["Body"],
                )
            )

    red_flags = data.get("red_flags") or []
    if red_flags:
        story.append(Paragraph("Risk Analysis — Red Flags", styles["SectionHeading"]))
        for flag in red_flags:
            severity = (flag.get("severity") or "medium").lower()
            color = _SEVERITY_COLORS.get(severity, colors.grey)
            story.append(
                Paragraph(
                    f'<font color="{color.hexval()}"><b>[{severity.upper()}]</b></font> '
                    f"<b>{flag.get('title', '')}</b>",
                    styles["Body"],
                )
            )
            story.append(Paragraph(flag.get("reason", ""), styles["Body"]))
            story.append(
                Paragraph(f"<i>Recommendation:</i> {flag.get('recommendation', '')}", styles["Body"])
            )
            story.append(Spacer(1, 6))

    summary = data.get("executive_summary")
    if summary:
        story.append(Paragraph("Executive Summary", styles["SectionHeading"]))
        for label, key in [
            ("Company Summary", "company_summary"),
            ("Financial Summary", "financial_summary"),
            ("Major Risks", "major_risks"),
            ("Opportunities", "opportunities"),
            ("Future Outlook", "future_outlook"),
        ]:
            if summary.get(key):
                story.append(Paragraph(f"<b>{label}:</b> {summary[key]}", styles["Body"]))

    recommendations = data.get("recommendations") or []
    if recommendations:
        story.append(Paragraph("Recommendations", styles["SectionHeading"]))
        for rec in recommendations:
            story.append(
                Paragraph(
                    f"<b>[{rec.get('category', '').upper()}]</b> {rec.get('recommendation', '')}",
                    styles["Body"],
                )
            )
            story.append(Paragraph(f"<i>Why:</i> {rec.get('rationale', '')}", styles["Body"]))
            story.append(Spacer(1, 6))

    doc.build(story)
    return buffer.getvalue()


def _simple_table(rows) -> Table:
    table = Table(rows, hAlign="LEFT", colWidths=[1.6 * inch, 4 * inch])
    table.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (0, -1), _BRAND),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table
