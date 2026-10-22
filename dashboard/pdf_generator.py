
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from xml.sax.saxutils import escape


def _report_table_style(header_color=colors.HexColor("#17365D"), font_size=8):
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), header_color),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), font_size),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]
    )


def _make_horizontal_bar_chart(title, labels, values, chart_width=365, bar_colors=None):
    labels = [str(label) for label in labels]
    values = [float(value) for value in values]
    row_height = 14
    chart_height = 26 + max(1, len(labels)) * row_height
    drawing = Drawing(chart_width, chart_height)
    drawing.add(
        String(0, chart_height - 12, title, fontName="Helvetica-Bold", fontSize=9)
    )

    label_width = 145
    value_width = 82
    bar_start = label_width + 5
    bar_width = max(20, chart_width - bar_start - value_width - 8)
    max_value = max(values, default=0) or 1
    drawing.add(
        Line(bar_start, 8, bar_start, chart_height - 19, strokeColor=colors.grey)
    )

    for index, (label, value) in enumerate(zip(labels, values)):
        y = chart_height - 29 - index * row_height
        display_label = label if len(label) <= 24 else f"{label[:21]}..."
        drawing.add(
            String(
                label_width,
                y,
                display_label,
                textAnchor="end",
                fontName="Helvetica",
                fontSize=6.5,
            )
        )
        scaled_width = bar_width * max(0, value) / max_value
        bar_color = bar_colors[index] if bar_colors else colors.HexColor("#2878A8")
        drawing.add(
            Rect(bar_start + 1, y - 2, scaled_width, 8, fillColor=bar_color, strokeColor=None)
        )
        drawing.add(
            String(
                bar_start + scaled_width + 5,
                y,
                f"{value:,.0f}",
                fontName="Helvetica",
                fontSize=6.5,
            )
        )

    return drawing


def _account_value(value):
    if value is None:
        return ""
    return escape(str(value))


def generate_financial_report(
    df,
    summary_text="",
    regional_data=None,
    risk_config=None,
):
    """Generate a complete receivables risk and exposure PDF report."""
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
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
    styles.add(
        ParagraphStyle(
            name="ReportTableCell",
            parent=styles["BodyText"],
            fontSize=6,
            leading=7,
        )
    )

    story = []

    story.append(Paragraph("InsightForge", styles["ReportTitle"]))
    story.append(
        Paragraph("Financial Risk and Exposure Report", styles["Heading2"])
    )
    story.append(Spacer(1, 8))

    total_accounts = len(df)
    total_outstanding = df["Outstanding_Amount"].sum()
    risk_order = ["High", "Medium", "Low"]
    risk_counts = df["Risk_Category"].value_counts()
    risk_exposure = df.groupby("Risk_Category")["Outstanding_Amount"].sum()
    high_risk = int(risk_counts.get("High", 0))
    medium_risk = int(risk_counts.get("Medium", 0))
    low_risk = int(risk_counts.get("Low", 0))
    high_risk_exposure = float(risk_exposure.get("High", 0))

    story.append(Paragraph("Executive KPIs", styles["Heading2"]))

    kpi_data = [
        ["Metric", "Value", "Metric", "Value"],
        ["Total accounts", f"{total_accounts:,}", "Total outstanding", f"Rs. {total_outstanding:,.2f}"],
        ["High-risk accounts", f"{high_risk:,}", "High-risk exposure", f"Rs. {high_risk_exposure:,.2f}"],
        ["Medium-risk accounts", f"{medium_risk:,}", "Low-risk accounts", f"{low_risk:,}"],
    ]

    kpi_table = Table(kpi_data, colWidths=[55 * mm, 70 * mm, 55 * mm, 70 * mm])
    kpi_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 1), (2, -1), "Helvetica-Bold"),
            ]
        )
    )
    story.append(kpi_table)
    story.append(Spacer(1, 10))

    if risk_config:
        story.append(Paragraph("Active Risk Thresholds", styles["Heading2"]))
        threshold_data = [
            ["Ageing medium", "Ageing high", "Ageing critical", "Exposure low", "Exposure medium", "Exposure high"],
            [
                f"{risk_config.get('ageing_medium', 'N/A')} days",
                f"{risk_config.get('ageing_high', 'N/A')} days",
                f"{risk_config.get('ageing_critical', 'N/A')} days",
                f"Rs. {risk_config.get('exposure_low', 'N/A')}",
                f"Rs. {risk_config.get('exposure_medium', 'N/A')}",
                f"Rs. {risk_config.get('exposure_high', 'N/A')}",
            ],
        ]
        threshold_table = Table(threshold_data, colWidths=[45 * mm] * 6)
        threshold_table.setStyle(_report_table_style(font_size=7))
        story.extend([threshold_table, Spacer(1, 10)])

    if summary_text and str(summary_text).strip():
        story.append(Paragraph("AI-Generated Financial Summary", styles["Heading2"]))
        safe_summary = escape(str(summary_text)).replace("\n", "<br/>")
        story.append(Paragraph(safe_summary, styles["BodyText"]))
        story.append(Spacer(1, 10))

    story.append(Paragraph("Risk and Exposure by Category", styles["Heading2"]))
    category_rows = [["Risk category", "Accounts", "Outstanding exposure (Rs.)", "Portfolio exposure"]]
    for category in risk_order:
        category_amount = float(risk_exposure.get(category, 0))
        exposure_share = category_amount / total_outstanding * 100 if total_outstanding else 0
        category_rows.append([
            category,
            f"{int(risk_counts.get(category, 0)):,}",
            f"{category_amount:,.2f}",
            f"{exposure_share:.1f}%",
        ])
    category_table = Table(category_rows, colWidths=[55 * mm, 35 * mm, 90 * mm, 55 * mm], repeatRows=1)
    category_table.setStyle(_report_table_style())
    story.append(category_table)
    story.append(Spacer(1, 10))

    if regional_data is None and "Region" in df.columns:
        regional_data = (
            df.groupby("Region", dropna=False)["Outstanding_Amount"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )

    regional_labels = []
    regional_values = []
    if regional_data is not None and not regional_data.empty:
        story.append(Paragraph("Regional Exposure and Risk", styles["Heading2"]))
        region_rows = [["Region", "Accounts", "Outstanding exposure (Rs.)", "High-risk accounts"]]
        for _, row in regional_data.iterrows():
            region = row["Region"]
            region_accounts = df[df["Region"].fillna("Unknown") == region] if "Region" in df.columns else df.iloc[0:0]
            high_count = int((region_accounts["Risk_Category"] == "High").sum())
            regional_labels.append(str(region))
            regional_values.append(float(row["Outstanding_Amount"]))
            region_rows.append([
                _account_value(region),
                f"{len(region_accounts):,}",
                f"{float(row['Outstanding_Amount']):,.2f}",
                f"{high_count:,}",
            ])
        region_table = Table(region_rows, colWidths=[55 * mm, 35 * mm, 90 * mm, 55 * mm], repeatRows=1)
        region_table.setStyle(_report_table_style())
        story.append(region_table)
        story.append(Spacer(1, 10))

    story.append(Paragraph("Risk and Exposure Charts", styles["Heading2"]))
    chart_specs = [
        (
            "Risk category distribution (accounts)",
            risk_order,
            [int(risk_counts.get(category, 0)) for category in risk_order],
            [colors.HexColor("#C94C4C"), colors.HexColor("#E5A93D"), colors.HexColor("#4C956C")],
        ),
        (
            "Outstanding exposure by risk (Rs.)",
            risk_order,
            [float(risk_exposure.get(category, 0)) for category in risk_order],
            [colors.HexColor("#C94C4C"), colors.HexColor("#E5A93D"), colors.HexColor("#4C956C")],
        ),
    ]
    if "Risk_Score" in df.columns:
        score_counts = df["Risk_Score"].value_counts().sort_index()
        chart_specs.append(("Risk score distribution (accounts)", score_counts.index.tolist(), score_counts.tolist(), None))
    if "Ageing_Days" in df.columns:
        ageing_bins = [0, 30, 60, 90, float("inf")]
        ageing_labels = ["0-29 days", "30-59 days", "60-89 days", "90+ days"]
        ageing_counts = [
            int(((df["Ageing_Days"] >= start) & (df["Ageing_Days"] < end)).sum())
            for start, end in zip(ageing_bins[:-1], ageing_bins[1:])
        ]
        chart_specs.append(("Ageing distribution (accounts)", ageing_labels, ageing_counts, None))
    if "Outstanding_Amount" in df.columns:
        top_exposure = df.nlargest(10, "Outstanding_Amount")
        chart_specs.append((
            "Top 10 accounts by exposure (Rs.)",
            top_exposure.get("Customer_Name", top_exposure.get("Account_ID", top_exposure.index)).astype(str).tolist(),
            top_exposure["Outstanding_Amount"].tolist(),
            None,
        ))
    if regional_labels:
        chart_specs.append(("Regional exposure (Rs.)", regional_labels, regional_values, None))
    if "Region" in df.columns:
        regional_risk = df.groupby(["Region", "Risk_Category"], dropna=False).size()
        regional_risk = regional_risk.sort_values(ascending=False).head(12)
        chart_specs.append((
            "Regional risk distribution (accounts)",
            [f"{region} - {category}" for region, category in regional_risk.index],
            regional_risk.tolist(),
            None,
        ))

    chart_rows = []
    for index in range(0, len(chart_specs), 2):
        row = []
        for title, labels, values, bar_colors in chart_specs[index:index + 2]:
            row.append(_make_horizontal_bar_chart(title, labels, values, bar_colors=bar_colors))
        if len(row) == 1:
            row.append("")
        chart_rows.append(row)
    charts_table = Table(chart_rows, colWidths=[doc.width / 2] * 2, hAlign="LEFT")
    charts_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(charts_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Top High-Risk Accounts", styles["Heading2"]))

    high_risk_df = df[df["Risk_Category"] == "High"].copy()
    high_risk_df = high_risk_df.sort_values(
        by="Risk_Score",
        ascending=False,
    ).head(10)

    risk_rows = [
        ["Account ID", "Customer", "Region", "Outstanding (Rs.)", "Ageing (days)", "Score", "Risk reason"]
    ]

    for _, row in high_risk_df.iterrows():
        risk_rows.append(
            [
                _account_value(row.get("Account_ID", "")),
                Paragraph(_account_value(row.get("Customer_Name", "")), styles["ReportTableCell"]),
                _account_value(row.get("Region", "")),
                f"{row['Outstanding_Amount']:,.2f}",
                f"{row['Ageing_Days']:,.1f}",
                str(row["Risk_Score"]),
                Paragraph(_account_value(row.get("Risk_Reason", "")), styles["ReportTableCell"]),
            ]
        )

    risk_table = Table(
        risk_rows,
        colWidths=[25 * mm, 43 * mm, 27 * mm, 37 * mm, 25 * mm, 18 * mm, 85 * mm],
        repeatRows=1,
    )
    risk_table.setStyle(_report_table_style())
    story.append(risk_table)

    story.append(Spacer(1, 12))
    story.append(Paragraph("Full Analyzed Portfolio", styles["Heading2"]))
    appendix_columns = [(column, str(column)) for column in df.columns]
    appendix_rows = [[label for _, label in appendix_columns]]
    for _, row in df.iterrows():
        appendix_rows.append([
            Paragraph(_account_value(row[column]), styles["ReportTableCell"])
            for column, _ in appendix_columns
        ])
    appendix_table = Table(
        appendix_rows,
        colWidths=[doc.width / len(appendix_columns)] * len(appendix_columns),
        repeatRows=1,
    )
    appendix_table.setStyle(_report_table_style(font_size=6.5))
    story.append(appendix_table)

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
