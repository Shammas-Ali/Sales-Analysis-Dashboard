from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime
import os
import re


def _strip_markdown(text: str) -> str:
    """Remove basic markdown bold (**text**) for PDF compatibility."""
    return re.sub(r'\*\*(.*?)\*\*', r'\1', text)


def export_report(kpis, insights, chart_paths, summary_df, executive_summary="", quality_score=None):
    os.makedirs("reports", exist_ok=True)
    filename = f"reports/Sales_Analysis_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4, leftMargin=0.75*inch, rightMargin=0.75*inch)
    styles = getSampleStyleSheet()
    elements = []

    accent = colors.HexColor("#2C5F8A")

    title_style = ParagraphStyle("CustomTitle", parent=styles["Title"],
                                  textColor=accent, fontSize=20, spaceAfter=6)
    h2_style = ParagraphStyle("H2", parent=styles["Heading2"],
                               textColor=accent, fontSize=13, spaceBefore=12, spaceAfter=4)
    h3_style = ParagraphStyle("H3", parent=styles["Heading3"],
                               fontSize=11, spaceBefore=8, spaceAfter=2)
    normal = styles["Normal"]

    # ---------- TITLE ----------
    elements.append(Paragraph("Sales Intelligence Dashboard", title_style))
    elements.append(Paragraph("<b>Analysis Report — Version 2.0</b>", styles["Normal"]))
    elements.append(HRFlowable(width="100%", thickness=2, color=accent))
    elements.append(Spacer(1, 0.15 * inch))
    elements.append(Paragraph(
        f"Student: Muhammad Shammas Ali &nbsp;&nbsp;|&nbsp;&nbsp; Roll No: 23-SET-011<br/>"
        f"Generated On: {datetime.now().strftime('%d %B %Y, %H:%M')}",
        normal
    ))
    elements.append(Spacer(1, 0.2 * inch))

    # ---------- EXECUTIVE SUMMARY ----------
    if executive_summary:
        elements.append(Paragraph("Executive Summary", h2_style))
        clean_summary = _strip_markdown(executive_summary)
        elements.append(Paragraph(clean_summary, normal))
        elements.append(Spacer(1, 0.2 * inch))

    # ---------- DATA QUALITY SCORE ----------
    if quality_score:
        elements.append(Paragraph("Data Quality Score", h2_style))
        grade_color = colors.green if quality_score["overall"] >= 75 else colors.orange if quality_score["overall"] >= 50 else colors.red
        elements.append(Paragraph(
            f"<b>Overall Score: {quality_score['overall']}/100 (Grade: {quality_score['grade']})</b>",
            ParagraphStyle("QS", parent=normal, textColor=grade_color, fontSize=12)
        ))
        for comp, val in quality_score.get("components", {}).items():
            elements.append(Paragraph(f"• {comp}: {val}%", normal))
        elements.append(Spacer(1, 0.2 * inch))

    # ---------- KPIs ----------
    elements.append(Paragraph("Key Performance Indicators", h2_style))
    kpi_data = [["Metric", "Value"]] + [[k, str(v)] for k, v in kpis.items()]
    kpi_table = Table(kpi_data, colWidths=[3 * inch, 3 * inch])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), accent),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F4F8")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 0.3 * inch))

    # ---------- CHARTS ----------
    if chart_paths:
        elements.append(Paragraph("Visual Analysis", h2_style))
        for title, path in chart_paths.items():
            if os.path.exists(path):
                elements.append(Paragraph(title, h3_style))
                elements.append(Image(path, width=5.5 * inch, height=3 * inch))
                elements.append(Spacer(1, 0.2 * inch))

    # ---------- EDA ----------
    elements.append(Paragraph("Exploratory Data Analysis", h2_style))
    if not summary_df.empty:
        summary_data = [summary_df.columns.tolist()] + [[str(v) for v in row] for row in summary_df.values.tolist()]
        eda_table = Table(summary_data, repeatRows=1)
        eda_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), accent),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F4F8")]),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(eda_table)
    elements.append(Spacer(1, 0.3 * inch))

    # ---------- INSIGHTS ----------
    elements.append(Paragraph("Actionable Business Insights", h2_style))
    for ins in insights:
        clean = _strip_markdown(ins)
        elements.append(Paragraph(f"• {clean}", normal))
    elements.append(Spacer(1, 0.3 * inch))

    # ---------- CONCLUSION ----------
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    elements.append(Paragraph("Conclusion", h2_style))
    elements.append(Paragraph(
        "This automated Sales Intelligence Dashboard v2.0 report provides a comprehensive overview of "
        "business performance with AI-enhanced insights, anomaly detection, and data quality scoring. "
        "Key trends, category performance, customer intelligence, and data quality issues have been identified. "
        "Decision-makers are encouraged to focus on high-performing categories while addressing areas "
        "showing declining profit or high missing data to improve overall performance.",
        normal
    ))

    doc.build(elements)
    return filename
