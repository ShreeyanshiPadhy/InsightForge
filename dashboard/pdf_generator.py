
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from xml.sax.saxutils import escape


def generate_financial_report(
    df,
    summary_text="",
    regional_data=None,
):
    """Generate an executive PDF report and return its bytes."""
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title="InsightForge Financial Risk Report",
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            textColor=colors.HexColor("#17365D"),
            spaceAfter=12,
        )
    )

    story = []

    story.append(Paragraph("InsightForge", styles["ReportTitle"]))
    story.append(
        Paragraph("Financial Risk Executive Report", styles["Heading2"])
    )
    story.append(Spacer(1, 8))

    total_accounts = len(df)
    total_outstanding = df["Outstanding_Amount"].sum()
    high_risk = int((df["Risk_Category"] == "High").sum())
    medium_risk = int((df["Risk_Category"] == "Medium").sum())
    low_risk = int((df["Risk_Category"] == "Low").sum())

    story.append(Paragraph("Executive KPIs", styles["Heading2"]))

    kpi_data = [
        ["Metric", "Value"],
        ["Total accounts", f"{total_accounts:,}"],
        ["Total outstanding", f"Rs. {total_outstanding:,.2f}"],
        ["High-risk accounts", f"{high_risk:,}"],
        ["Medium-risk accounts", f"{medium_risk:,}"],
        ["Low-risk accounts", f"{low_risk:,}"],
    ]

    kpi_table = Table(kpi_data, colWidths=[85 * mm, 75 * mm])
    kpi_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("ALIGN", (1, 1), (1, -1), "RIGHT"),
            ]
        )
    )
    story.append(kpi_table)
    story.append(Spacer(1, 14))

    if summary_text and str(summary_text).strip():
        story.append(Paragraph("AI-Generated Financial Summary", styles["Heading2"]))
        safe_summary = (
            str(summary_text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br/>")
        )
        story.append(Paragraph(safe_summary, styles["BodyText"]))
        story.append(Spacer(1, 12))

    if regional_data is None and "Region" in df.columns:
        regional_data = (
            df.groupby("Region", dropna=False)["Outstanding_Amount"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )

    if regional_data is not None and not regional_data.empty:
        story.append(Paragraph("Regional Exposure", styles["Heading2"]))

        region_rows = [["Region", "Outstanding (Rs.)"]]
        for _, row in regional_data.iterrows():
            region_rows.append(
                [
                    str(row["Region"]),
                    f"{row['Outstanding_Amount']:,.2f}",
                ]
            )

        region_table = Table(
            region_rows,
            colWidths=[85 * mm, 75 * mm],
            repeatRows=1,
        )
        region_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAF7")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                    ("PADDING", (0, 0), (-1, -1), 5),
                    ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                ]
            )
        )
        story.append(region_table)
        story.append(Spacer(1, 12))

    story.append(Paragraph("Top High-Risk Accounts", styles["Heading2"]))

    high_risk_df = df[df["Risk_Category"] == "High"].copy()
    high_risk_df = high_risk_df.sort_values(
        by="Risk_Score",
        ascending=False,
    ).head(10)

    risk_rows = [
        ["Account ID", "Customer", "Outstanding (Rs.)", "Ageing (days)", "Score"]
    ]

    for _, row in high_risk_df.iterrows():
        risk_rows.append(
            [
                str(row.get("Account_ID", "")),
                str(row.get("Customer_Name", ""))[:35],
                f"{row['Outstanding_Amount']:,.2f}",
                f"{row['Ageing_Days']:,.1f}",
                str(row["Risk_Score"]),
            ]
        )

    risk_table = Table(
        risk_rows,
        colWidths=[27 * mm, 48 * mm, 36 * mm, 27 * mm, 18 * mm],
        repeatRows=1,
    )
    risk_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(risk_table)

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()  

    return pdf_bytes

def generate_general_finance_report(df, numeric_columns, summary_text=""):
    """Generate a PDF report for a general-finance dataset."""
    from io import BytesIO

    import pandas as pd
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitleCenter",
            parent=styles["Title"],
            alignment=TA_CENTER,
        )
    )

    elements = [
        Paragraph("InsightForge - General Financial Analysis", styles["ReportTitleCenter"]),
        Spacer(1, 6 * mm),
        Paragraph("Dataset Overview", styles["Heading2"]),
    ]

    overview = [
        ["Metric", "Value"],
        ["Total records", str(len(df))],
        ["Total columns", str(len(df.columns))],
        ["Numeric measures", str(len(numeric_columns))],
        ["Missing cells", str(int(df.isna().sum().sum()))],
        ["Duplicate rows", str(int(df.duplicated().sum()))],
    ]

    overview_table = Table(overview, colWidths=[65 * mm, 55 * mm])
    overview_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("PADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ])
    )
    elements.extend([overview_table, Spacer(1, 6 * mm)])

    if summary_text and str(summary_text).strip():
        elements.append(Paragraph("AI Financial Summary", styles["Heading2"]))

        safe_summary = escape(str(summary_text)).replace("\n", "<br/>")
        elements.append(Paragraph(safe_summary, styles["BodyText"]))
        elements.append(Spacer(1, 6 * mm))

    valid_numeric = [
        column for column in numeric_columns
        if column in df.columns and pd.api.types.is_numeric_dtype(df[column])
    ]

    if valid_numeric:
        elements.append(Paragraph("Numeric Analysis", styles["Heading2"]))

        stats = df[valid_numeric].describe().round(2)
        display_stats = stats.iloc[:, :6].reset_index()
        display_stats.columns = [str(column) for column in display_stats.columns]

        table_data = [display_stats.columns.tolist()]
        for row in display_stats.itertuples(index=False, name=None):
            table_data.append([
                "" if pd.isna(value) else str(value)
                for value in row
            ])

        stats_table = Table(table_data, repeatRows=1)
        stats_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("PADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )
        elements.extend([stats_table, Spacer(1, 6 * mm)])

    elements.append(Paragraph("Sample Records (first 10 rows)", styles["Heading2"]))

    sample = df.iloc[:10, :8].copy()
    sample = sample.astype(object).where(pd.notna(sample), "")
    sample_data = [[str(column) for column in sample.columns]]

    for row in sample.itertuples(index=False, name=None):
        sample_data.append([str(value) for value in row])

    if len(sample_data[0]) > 0:
        sample_table = Table(sample_data, repeatRows=1)
        sample_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("PADDING", (0, 0), (-1, -1), 3),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )
        elements.append(sample_table)

    doc.build(elements)
    return buffer.getvalue()
