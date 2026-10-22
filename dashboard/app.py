
import streamlit as st
import pandas as pd
import json
import sys
import os
import re

import plotly.express as px

from general_finance import (
    detect_general_header_row,
)
from dataset_analytics import (
    generate_dynamic_kpis,
    numeric_values,
    profile_dataset,
)

from visualizations import (
    risk_category_chart,
    risk_exposure_chart,
    top_exposure_chart,
    ageing_distribution_chart,
    risk_score_chart,
    regional_exposure_chart,
    regional_risk_chart,
)
from upload_processor import prepare_uploaded_data
from ai.risk_detection import DEFAULT_RISK_CONFIG, perform_risk_analysis
from pdf_generator import (
    generate_financial_report,
    generate_general_finance_report,
)

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../ai"))
)

from financial_context import create_financial_context
from llm import (
    answer_dataset_question,
    answer_financial_question,
    generate_dataset_summary,
    generate_financial_summary,
)
from anomaly_detection import perform_anomaly_analysis


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="InsightForge",
    page_icon="📊",
    layout="wide",
)


st.markdown("""
<style>
/* Make ALL buttons blue, including download buttons */
.stButton > button,
.stDownloadButton > button,
button[kind="primary"],
button[kind="secondary"] {
    background-color: #2563EB !important;
    color: white !important;
    border: 1px solid #2563EB !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: background-color 0.2s ease;
}

/* Hover effect */
.stButton > button:hover,
.stDownloadButton > button:hover,
button[kind="primary"]:hover,
button[kind="secondary"]:hover {
    background-color: #1D4ED8 !important;
    color: white !important;
    border-color: #1D4ED8 !important;
}

/* Keyboard focus */
.stButton > button:focus,
.stDownloadButton > button:focus {
    color: white !important;
    box-shadow: 0 0 0 2px #93C5FD !important;
}

/* Keep disabled buttons visually distinct */
.stButton > button:disabled,
.stDownloadButton > button:disabled {
    background-color: #64748B !important;
    color: white !important;
    border-color: #64748B !important;
}
</style>
""", unsafe_allow_html=True)


HEADER_HINTS = {
    "account_id": [
        "cust code", "cust.code", "customer code",
        "customer id", "account id", "debtor code",
        "debtor number", "account number", "client id",
        "account_id",
    ],
    "customer_name": [
        "customer name", "client name", "debtor name",
        "account name", "customer", "debtor", "party",
        "customer_name",
    ],
    "outstanding": [
        "outstanding amount", "outstanding balance",
        "receivable amount", "open balance",
        "may'26 exp.", "amount due", "balance due",
        "total outstanding", "outstanding_amount",
    ],
    "region": [
        "region", "territory", "sales region",
        "geography", "location",
    ],
    "status": [
        "active / inactive", "account status",
        "customer status", "status",
    ],
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def normalize_header(value):
    value = str(value).replace("\u00a0", " ").strip().lower()
    return re.sub(r"[^a-z0-9]+", "", value)


def format_inr(value):
    """Format values in Indian Rupees, lakh, and crore."""
    value = float(value)

    if abs(value) >= 1_00_00_000:
        return f"₹{value / 1_00_00_000:,.2f} crore"
    elif abs(value) >= 1_00_000:
        return f"₹{value / 1_00_000:,.2f} lakh"

    return f"₹{value:,.2f}"


def detect_header_row(preview):
    """Return the best zero-based candidate header row, or None."""
    best_row = None
    best_score = 0

    normalized_hints = {
        field: [normalize_header(hint) for hint in hints]
        for field, hints in HEADER_HINTS.items()
    }

    for row_index, row in preview.iterrows():
        values = [
            normalize_header(value)
            for value in row.tolist()
            if pd.notna(value) and str(value).strip()
        ]

        if not values:
            continue

        matched_fields = set()

        for value in values:
            for field, hints in normalized_hints.items():
                if any(value == hint for hint in hints):
                    matched_fields.add(field)

        ageing_matches = sum(
            bool(re.search(r"\d+\s*(?:-|to)\s*\d+", value))
            or bool(re.search(r"\d+\s*\+", value))
            or "ageing" in value
            or "aging" in value
            for value in values
        )

        score = len(matched_fields) * 3 + min(ageing_matches, 3)

        if score > best_score:
            best_score = score
            best_row = int(row_index)

    return best_row if best_score >= 6 else None


def safe_columns(dataframe, columns):
    """Return only columns that exist in the dataframe."""
    return [column for column in columns if column in dataframe.columns]


# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================

session_defaults = {
    "financial_summary": "",
    "last_financial_answer": "",
    "financial_pdf": None,
    "mapped_financial_df": None,
    "mapping_signature": None,
    "mapping_success": False,
    "risk_config": DEFAULT_RISK_CONFIG.copy(),
    "general_finance_pdf": None,
    "general_finance_summary": "",
    "general_finance_answer": "",
}

for key, default_value in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default_value


# ============================================================
# APPLICATION HEADER
# ============================================================

st.title("📊 InsightForge")
st.subheader("Financial Intelligence Dashboard")
st.write(
    "Analyze receivables, identify financial risks, explore exposure, "
    "and generate AI-assisted financial insights."
)

st.divider()


# ============================================================
# DATASET UPLOAD AND PROCESSING
# ============================================================

st.header("1. Upload Dataset")

uploaded_file = st.file_uploader(
    "Upload a CSV or Excel dataset",
    type=["csv", "xlsx", "xls"],
    key="financial_upload",
)

if uploaded_file is None:
    st.info("Upload a financial dataset to begin analysis.")
    st.stop()


try:
    uploaded_file.seek(0)

    if uploaded_file.name.lower().endswith(".csv"):
        preview = pd.read_csv(uploaded_file, header=None, nrows=30)
    else:
        preview = pd.read_excel(uploaded_file, header=None, nrows=30)

    detected_row = detect_header_row(preview)
    if detected_row is None:
        detected_row = detect_general_header_row(preview)

    if detected_row is not None:
        st.success(f"Suggested header row: {detected_row + 1}")
        default_row = detected_row + 1
    else:
        st.warning(
            "Could not confidently detect the header row. "
            "Please select it manually."
        )
        default_row = min(5, max(1, len(preview)))

    manual_override = st.checkbox(
        "Choose header row manually",
        value=detected_row is None,
        key="manual_header_override",
    )

    if manual_override:
        header_row = st.number_input(
            "Header row number",
            min_value=1,
            max_value=100,
            value=int(default_row),
            step=1,
            help="Enter the spreadsheet row containing the column names.",
        )
    else:
        header_row = default_row

    uploaded_file.seek(0)

    if uploaded_file.name.lower().endswith(".csv"):
        raw_df = pd.read_csv(uploaded_file, header=int(header_row) - 1)
    else:
        raw_df = pd.read_excel(uploaded_file, header=int(header_row) - 1)

    raw_df.columns = [
        str(column).replace("\u00a0", " ").strip()
        for column in raw_df.columns
    ]

    if raw_df.empty:
        st.error("The selected header row produced an empty dataset.")
        st.stop()

    

# Uploaded Data Preview with a View Full Data button
    if "show_full_uploaded_data" not in st.session_state:
        st.session_state.show_full_uploaded_data = False


    def toggle_uploaded_full_data():
        st.session_state.show_full_uploaded_data = (
            not st.session_state.show_full_uploaded_data
        )


    heading_col, button_col = st.columns([4, 1])

    with heading_col:
        st.subheader("Uploaded Data Preview")

    with button_col:
        st.button(
            (
                "Hide Full Data"
                if st.session_state.show_full_uploaded_data
                else "View Full Data"
            ),
            key="toggle_uploaded_full_data",
            on_click=toggle_uploaded_full_data,
            use_container_width=True,
            type="primary",
        )

    if st.session_state.show_full_uploaded_data:
        st.dataframe(raw_df, use_container_width=True, height=500)
    else:
        st.dataframe(raw_df.head(10), use_container_width=True)

    st.caption(f"Rows: {len(raw_df):,} | Columns: {len(raw_df.columns):,}")



    # Route general-finance datasets before receivables-only column mapping.
    
    # Route datasets before receivables-only column mapping.
    def _norm_col(value):
        return re.sub(r"[^a-z0-9]+", "", str(value).strip().lower())

    normalized_columns = [_norm_col(c) for c in raw_df.columns]
    normalized = set(normalized_columns)

    # Use broader aliases so receivables files with different headers
    # can still reach the manual column-mapping interface.
    has_id = bool(normalized & {
        "accountid", "customerid", "debtorid",
        "accountnumber", "debtornumber", "customercode",
        "custcode", "clientid",
    })

    has_customer = bool(normalized & {
        "customername", "customer", "debtorname",
        "accountname", "clientname", "debtor", "party",
    })

    has_outstanding = any(
        term in column
        for column in normalized
        for term in (
            "outstandingamount", "outstandingbalance",
            "receivableamount", "amountdue", "balancedue",
            "openbalance", "totaloutstanding", "may26exp",
        )
    )

    has_ageing = any(
        any(term in _norm_col(column) for term in (
            "ageingdays", "agingdays", "daysoverdue",
            "dayspastdue", "daysoutstanding", "ageing", "aging",
        ))
        or bool(re.search(r"\d+\s*(?:-|to)\s*\d+", str(column).lower()))
        or bool(re.search(r"(?:>\s*=?\s*\d+|\d+\s*\+)", str(column).lower()))
        for column in raw_df.columns
    )

    # The existing receivables workflow requires both an exposure and ageing measure.
    looks_like_receivables = (
        has_id and has_customer and has_outstanding and has_ageing
    )

    if not looks_like_receivables:
        # Keep the uploaded values intact; analytics derive temporary views.
        finance_df = raw_df.copy()
        dataset_profile = profile_dataset(finance_df)
        dynamic_analytics = generate_dynamic_kpis(finance_df, dataset_profile)
        numeric_columns = dataset_profile["candidate_measures"]

        if finance_df.empty:
            st.error("The uploaded dataset contains no data rows.")
            st.stop()

        st.session_state["dataset_type"] = "general_finance"

        st.divider()
        st.header("Dataset-Driven Analysis")
        st.caption(
            "Metrics, dimensions, and charts are derived from this upload. "
            "Receivables-specific risk scoring is used only for recognized "
            "receivables datasets."
        )

        if not numeric_columns:
            st.warning(
                "No numeric financial measures were detected. "
                "Check the header row and data format."
            )

        # Identify financial measures using semantic hints, not fixed headers.
        def _finance_col(*terms):
            return next(
                (
                    col for col in numeric_columns
                    if any(term in _norm_col(col) for term in terms)
                ),
                None,
            )

        revenue_col = _finance_col("revenue", "income", "sales", "turnover")
        expenditure_col = _finance_col("expenditure", "expense", "spending", "cost")
        capital_col = _finance_col("capitaloutlay")

        year_col = next(
            (
                col for col in finance_df.columns
                if col in dataset_profile["date_columns"]
                or _norm_col(col) in {"year", "financialyear", "fiscalyear"}
            ),
            None,
        )

        group_candidates = dataset_profile["candidate_dimensions"]

        # Shared controls for general-finance analysis.
        if numeric_columns:
            default_metric = (
                revenue_col
                or expenditure_col
                or capital_col
                or numeric_columns[0]
            )

            selected_metric = st.selectbox(
                "Financial metric to analyze",
                numeric_columns,
                index=numeric_columns.index(default_metric),
                key="general_finance_metric",
            )

            group_options = ["None"]
            if year_col:
                group_options.append(year_col)
            group_options.extend(
                col for col in group_candidates
                if col not in group_options
            )

            selected_group = st.selectbox(
                "Group results by",
                group_options,
                index=1 if year_col else 0,
                key="general_finance_dimension",
            )

            metric_position = next(
                item["position"] for item in dataset_profile["columns"]
                if item["column"] == selected_metric
            )
            metric_values = numeric_values(finance_df.iloc[:, metric_position])

        else:
            selected_metric = None
            selected_group = "None"
            metric_values = pd.Series(dtype=float)

        # Four dashboard sections, adapted for general finance.
        analytics_tab, ai_tab, data_tab, reports_tab = st.tabs(
            [
                "📊 Analytics",
                "🤖 AI Assistant",
                "📋 Data & Quality",
                "📥 Reports & Downloads",
            ]
        )

        # ----------------------------------------------------
        # TAB 1: FINANCIAL ANALYTICS
        # ----------------------------------------------------
        with analytics_tab:
            st.header("Dataset Overview")

            if numeric_columns:
                featured = [
                    metric for metric in dynamic_analytics["kpis"]
                    if metric["calculation"] == "sum"
                    and metric["label"].startswith("Total ")
                    and metric["label"] != "Total "
                ][:4]
                if not featured:
                    featured = [
                        metric for metric in dynamic_analytics["kpis"]
                        if metric["calculation"] in {"mean", "median"}
                    ][:4]
                if featured:
                    cards = st.columns(len(featured))
                    for card, metric in zip(cards, featured):
                        card.metric(metric["label"], f"{metric['value']:,.2f}")
                        card.caption(
                            f"Source: {metric['source_columns'][0]} "
                            f"({metric['calculation']})"
                        )

                a, b, c = st.columns(3)
                a.metric("Records", f"{len(finance_df):,}")
                b.metric(
                    f"Total {selected_metric}",
                    f"{metric_values.sum():,.2f}",
                )
                c.metric(
                    "Average per record",
                    (
                        f"{metric_values.mean():,.2f}"
                        if metric_values.notna().any()
                        else "N/A"
                    ),
                )

                if selected_group != "None":
                    chart_data = finance_df[
                        [selected_group, selected_metric]
                    ].copy()
                    chart_data[selected_metric] = metric_values
                    if selected_group in dataset_profile["date_columns"]:
                        chart_data[selected_group] = pd.to_datetime(
                            chart_data[selected_group], errors="coerce",
                            format="mixed",
                        ).dt.to_period("M").astype(str)
                    grouped = (
                        chart_data.dropna()
                        .groupby(selected_group, as_index=False)[
                            selected_metric
                        ]
                        .sum()
                    )

                    if not grouped.empty:
                        st.subheader(
                            f"{selected_metric} by {selected_group}"
                        )

                        if selected_group == year_col:
                            grouped = grouped.sort_values(selected_group)
                            fig = px.line(
                                grouped,
                                x=selected_group,
                                y=selected_metric,
                                markers=True,
                            )
                        else:
                            grouped = grouped.sort_values(
                                selected_metric,
                                ascending=False,
                            )
                            fig = px.bar(
                                grouped,
                                x=selected_group,
                                y=selected_metric,
                            )

                        st.plotly_chart(
                            fig, use_container_width=True
                        )
                        st.dataframe(
                            grouped, use_container_width=True
                        )

                if year_col and revenue_col and expenditure_col:
                    trend = finance_df[
                        [year_col, revenue_col, expenditure_col]
                    ].copy()

                    for col in (revenue_col, expenditure_col):
                        position = next(
                            item["position"] for item in dataset_profile["columns"]
                            if item["column"] == col
                        )
                        trend[col] = numeric_values(finance_df.iloc[:, position])

                    trend = trend.dropna(subset=[year_col])
                    trend = trend.groupby(
                        year_col, as_index=False
                    )[[revenue_col, expenditure_col]].sum()
                    trend = trend.sort_values(year_col)

                    st.subheader("Revenue vs Expenditure Trend")
                    st.plotly_chart(
                        px.line(
                            trend,
                            x=year_col,
                            y=[revenue_col, expenditure_col],
                            markers=True,
                        ),
                        use_container_width=True,
                    )
            else:
                st.info(
                    "No numeric measures are available to plot. "
                    "Review the uploaded data in Data & Quality."
                )

            category_summary = next(
                (
                    summary for summary in dynamic_analytics["distributions"]
                    if "top_categories" in summary
                    and summary["top_categories"]
                ),
                None,
            )
            if category_summary:
                st.subheader(f"Most common values: {category_summary['column']}")
                st.plotly_chart(
                    px.bar(
                        pd.DataFrame(category_summary["top_categories"]),
                        x="category",
                        y="count",
                        title=f"Category counts for {category_summary['column']}",
                    ),
                    use_container_width=True,
                )

        # ----------------------------------------------------
        # TAB 2: AI ASSISTANT
        # ----------------------------------------------------
        with ai_tab:
            st.header("AI Financial Assistant")
            st.write(
                "Ask questions about the uploaded financial dataset "
                "or generate an AI-assisted summary."
            )

            finance_context = {
                "dataset_type": "dataset_driven",
                "profile": dataset_profile,
                "analytics": dynamic_analytics,
                "sample_records": finance_df.head(50).to_dict(
                    orient="records"
                ),
            }

            finance_context_json = json.dumps(
                finance_context,
                indent=2,
                default=str,
            )

            if st.button(
                "Generate Financial Insights",
                key="general_finance_generate_insights",
                type="primary",
            ):
                with st.spinner("Generating financial insights..."):
                    try:
                        result = generate_dataset_summary(
                            finance_context_json
                        )
                        st.session_state[
                            "general_finance_summary"
                        ] = result or ""
                    except Exception:
                        st.warning(
                            "AI insights are currently unavailable. "
                            "You can still use the financial analysis."
                        )

            summary = st.session_state.get(
                "general_finance_summary", ""
            )
            if summary:
                st.subheader("Financial Insights")
                st.markdown(summary)

            question = st.text_input(
                "Ask a question about this dataset",
                placeholder=(
                    "Example: Which year has the highest revenue?"
                ),
                key="general_finance_question",
            )

            if st.button(
                "Ask InsightForge",
                key="general_finance_ask",
            ):
                if question.strip():
                    with st.spinner("Analyzing financial data..."):
                        try:
                            answer = answer_dataset_question(
                                question.strip(),
                                finance_context_json,
                            )
                            st.session_state[
                                "general_finance_answer"
                            ] = answer
                        except Exception:
                            st.warning(
                                "The AI assistant is temporarily "
                                "unavailable. Please try again."
                            )
                else:
                    st.warning("Please enter a question.")

            answer = st.session_state.get(
                "general_finance_answer", ""
            )
            if answer:
                st.subheader("Answer")
                st.write(answer)

            st.caption(
                "Verify AI-generated interpretations against the "
                "original dataset."
            )

        # ----------------------------------------------------
        # TAB 3: DATA AND QUALITY
        # ----------------------------------------------------
        with data_tab:
            st.header("Dataset Overview")

            a, b, c = st.columns(3)
            a.metric("Total Records", f"{len(finance_df):,}")
            b.metric("Total Columns", f"{len(finance_df.columns):,}")
            c.metric(
                "Numeric Measures", f"{len(numeric_columns):,}"
            )

            st.divider()
            st.subheader("Column Profile")
            st.dataframe(
                pd.DataFrame(dataset_profile["columns"]),
                use_container_width=True,
                hide_index=True,
            )
            if dataset_profile["warnings"]:
                with st.expander("Data-quality warnings", expanded=False):
                    for warning in dataset_profile["warnings"]:
                        st.warning(warning)

            st.subheader("Generated KPIs")
            if dynamic_analytics["kpis"]:
                st.dataframe(
                    pd.DataFrame(dynamic_analytics["kpis"]),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No suitable numeric measures were detected.")

            if dynamic_analytics["date_summaries"]:
                st.subheader("Date coverage")
                st.dataframe(
                    pd.DataFrame(dynamic_analytics["date_summaries"]),
                    use_container_width=True,
                    hide_index=True,
                )

            if dynamic_analytics["distributions"]:
                st.subheader("Numeric distributions and category counts")
                st.dataframe(
                    pd.DataFrame(dynamic_analytics["distributions"]),
                    use_container_width=True,
                    hide_index=True,
                )

            if dynamic_analytics["grouped_summaries"]:
                st.subheader("Grouped measure summaries")
                for summary in dynamic_analytics["grouped_summaries"][:10]:
                    with st.expander(
                        f"{summary['measure']} by {summary['dimension']}"
                    ):
                        st.dataframe(
                            pd.DataFrame(summary["values"]),
                            use_container_width=True,
                            hide_index=True,
                        )

            if dynamic_analytics["period_summaries"]:
                st.subheader("Period-wise measure summaries")
                for summary in dynamic_analytics["period_summaries"][:10]:
                    with st.expander(
                        f"{summary['measure']} by {summary['date_column']} (monthly)"
                    ):
                        st.dataframe(
                            pd.DataFrame(summary["values"]),
                            use_container_width=True,
                            hide_index=True,
                        )

            st.divider()
            st.subheader("Data Quality Check")

            missing_cells = int(
                finance_df.isna().sum().sum()
            )
            duplicate_rows = int(
                finance_df.duplicated().sum()
            )

            a, b = st.columns(2)
            a.metric("Missing Cells", f"{missing_cells:,}")
            b.metric("Duplicate Rows", f"{duplicate_rows:,}")

            if missing_cells == 0 and duplicate_rows == 0:
                st.success(
                    "No missing cells or duplicate rows detected."
                )
            else:
                st.warning(
                    "Review missing cells and duplicate rows "
                    "before interpreting results."
                )

            st.subheader("Full Dataset")
            st.dataframe(finance_df, use_container_width=True)

        # ----------------------------------------------------
        # TAB 4: REPORTS AND DOWNLOADS
        # ----------------------------------------------------
        with reports_tab:
            st.header("Reports & Downloads")

            
            st.subheader("Financial Analysis PDF")

            if st.button(
                "Generate Financial Analysis PDF",
                key="generate_general_finance_pdf",
                type="primary",
            ):
                try:
                    pdf_bytes = generate_general_finance_report(
                        finance_df,
                        numeric_columns,
                        st.session_state.get(
                            "general_finance_summary", ""
                        ),
                    )
                    st.session_state["general_finance_pdf"] = pdf_bytes
                    st.success("Financial analysis PDF generated.")
                except Exception as error:
                    st.error(f"Could not generate PDF: {error}")

            if st.session_state.get("general_finance_pdf") is not None:
                st.download_button(
                    "Download Financial Analysis PDF",
                    data=st.session_state["general_finance_pdf"],
                    file_name="InsightForge_General_Financial_Analysis.pdf",
                    mime="application/pdf",
                    key="download_general_finance_pdf",
                    type="primary",
                )

            st.divider()


            csv_data = finance_df.to_csv(
                index=False
            ).encode("utf-8-sig")

            st.download_button(
                "Download Financial Data (CSV)",
                data=csv_data,
                file_name="insightforge_financial_data.csv",
                mime="text/csv",
                key="general_finance_download_csv",
                type="primary",
            )

            json_data = finance_df.to_json(
                orient="records",
                indent=2,
            ).encode("utf-8")

            st.download_button(
                "Download Financial Data (JSON)",
                data=json_data,
                file_name="insightforge_financial_data.json",
                mime="application/json",
                key="general_finance_download_json",
                type="primary",
            )

            st.caption(
                "Exports preserve the uploaded columns and rows. "
                "Receivables risk and anomaly reports are not generated "
                "for this dataset type."
            )

        # Do not continue into receivables mapping or risk scoring.
        st.stop()
    
    # Receivables dataset: preserve the existing mapping and risk workflow.
    from upload_processor import detect_column_mapping
    st.subheader("Column Mapping")
    st.caption("Review the automatically detected columns and change any selection that is incorrect.")
    detected_mapping = detect_column_mapping(raw_df.columns)
    required_fields = {"Account_ID": "Account ID", "Customer_Name": "Customer name", "Outstanding_Amount": "Outstanding amount"}
    optional_fields = {"Region": "Region (optional)", "Account_Status": "Account status (optional)"}
    selected_mapping = {}
    options = ["-- Select a column --"] + list(raw_df.columns)
    for field, label in required_fields.items():
        detected_column = detected_mapping.get(field)
        default_index = options.index(detected_column) if detected_column in options else 0
        selected_mapping[field] = st.selectbox(label, options=options, index=default_index, key=f"mapping_{field}")
    optional_mapping = {}
    optional_options = ["-- Not available --"] + list(raw_df.columns)
    for field, label in optional_fields.items():
        detected_column = detected_mapping.get(field)
        default_index = optional_options.index(detected_column) if detected_column in optional_options else 0
        optional_mapping[field] = st.selectbox(label, options=optional_options, index=default_index, key=f"optional_mapping_{field}")
    mapping_complete = all(selected_mapping[f] != "-- Select a column --" for f in required_fields)
    selected_required_sources = list(selected_mapping.values())
    if len(set(selected_required_sources)) != len(selected_required_sources):
        mapping_complete = False
        st.warning("Each required field must map to a different source column.")
    selected_optional_sources = [v for v in optional_mapping.values() if v != "-- Not available --"]
    if len(set(selected_optional_sources)) != len(selected_optional_sources) or set(selected_required_sources).intersection(selected_optional_sources):
        mapping_complete = False
        st.warning("A source column cannot be assigned to multiple fields.")
    if mapping_complete:
        st.success("Required columns are mapped.")
    else:
        st.warning("Please correct the column mapping before processing.")

    mapping_signature = (uploaded_file.name, getattr(uploaded_file, "size", None), int(header_row), tuple(raw_df.columns), tuple(selected_mapping.items()), tuple(optional_mapping.items()))
    if st.session_state.get("mapping_signature") != mapping_signature:
        st.session_state["mapped_financial_df"] = None
        st.session_state["mapping_success"] = False
        st.session_state["financial_summary"] = ""
        st.session_state["last_financial_answer"] = ""
        st.session_state["financial_pdf"] = None
    apply_clicked = st.button("Process Dataset", key="apply_column_mapping", disabled=not mapping_complete, type="primary")
    if apply_clicked and mapping_complete:
        rename_mapping = {source: target for target, source in selected_mapping.items()}
        for field, source in optional_mapping.items():
            if source != "-- Not available --":
                rename_mapping[source] = field
        mapped_df = raw_df.rename(columns=rename_mapping).copy()
        if "Region" not in mapped_df.columns: mapped_df["Region"] = "Unknown"
        if "Account_Status" not in mapped_df.columns: mapped_df["Account_Status"] = "Unknown"
        try:
            risk_config = st.session_state.get("risk_config", DEFAULT_RISK_CONFIG.copy())
            processed_df = prepare_uploaded_data(mapped_df, risk_config=risk_config)
            st.session_state["mapped_financial_df"] = processed_df
            st.session_state["mapping_signature"] = mapping_signature
            st.session_state["mapping_success"] = True
            st.session_state["financial_summary"] = ""
            st.session_state["last_financial_answer"] = ""
            st.session_state["financial_pdf"] = None
            st.success(f"Dataset processed successfully! {len(processed_df):,} accounts analyzed.")
        except Exception as error:
            st.session_state["mapping_success"] = False
            st.error(f"Could not process mapped data: {error}")
            st.stop()
    if st.session_state.get("mapped_financial_df") is None or st.session_state.get("mapping_signature") != mapping_signature:
        st.info("Review the mappings and click Process Dataset.")
        st.stop()
    df = st.session_state["mapped_financial_df"].copy()

except Exception as error:
    st.error(f"Could not read or process the uploaded file: {error}")
    st.stop()

# ============================================================
# RISK THRESHOLD CONTROLS
# ============================================================

st.sidebar.title("InsightForge Controls")
st.sidebar.header("Risk Thresholds")

saved_config = st.session_state.get(
    "risk_config",
    DEFAULT_RISK_CONFIG.copy(),
)

with st.sidebar.expander("Ageing thresholds (days)", expanded=True):
    ageing_medium = st.slider(
        "Medium ageing threshold",
        min_value=1,
        max_value=90,
        value=int(saved_config["ageing_medium"]),
        key="ageing_medium_slider",
    )

    ageing_high = st.slider(
        "High ageing threshold",
        min_value=ageing_medium + 1,
        max_value=180,
        value=min(
            180,
            max(int(saved_config["ageing_high"]), ageing_medium + 1),
        ),
        key="ageing_high_slider",
    )

    ageing_critical = st.slider(
        "Critical ageing threshold",
        min_value=ageing_high + 1,
        max_value=365,
        value=min(
            365,
            max(int(saved_config["ageing_critical"]), ageing_high + 1),
        ),
        key="ageing_critical_slider",
    )

with st.sidebar.expander("Exposure thresholds (₹)", expanded=True):
    exposure_low = st.number_input(
        "Low exposure threshold (₹)",
        min_value=0.0,
        value=float(saved_config["exposure_low"]),
        step=0.1,
        format="%.1f",
        key="exposure_low_input",
    )

    exposure_medium = st.number_input(
        "Medium exposure threshold (₹)",
        min_value=0.1,
        value=float(saved_config["exposure_medium"]),
        step=0.1,
        format="%.1f",
        key="exposure_medium_input",
    )

    exposure_high = st.number_input(
        "High exposure threshold (₹)",
        min_value=0.1,
        value=float(saved_config["exposure_high"]),
        step=0.1,
        format="%.1f",
        key="exposure_high_input",
    )
if not (exposure_low < exposure_medium < exposure_high):
    st.sidebar.error(
        "Set exposure thresholds in increasing order: "
        "Low < Medium < High."
    )
    st.stop()

risk_config = {
    "ageing_medium": ageing_medium,
    "ageing_high": ageing_high,
    "ageing_critical": ageing_critical,
    "exposure_low": exposure_low,
    "exposure_medium": exposure_medium,
    "exposure_high": exposure_high,
}

st.session_state["risk_config"] = risk_config

try:
    df = perform_risk_analysis(
        st.session_state["mapped_financial_df"].copy(),
        config=risk_config,
    )
except Exception as error:
    st.error(f"Financial risk or anomaly analysis failed: {error}")
    st.stop()

# ============================================================
# FINANCIAL CONTEXT AND SUMMARY VALUES
# ============================================================

try:
    context = create_financial_context(df)
    financial_data = json.dumps(context, indent=2, default=str)
except Exception as error:
    st.error(f"Could not prepare the financial context: {error}")
    st.stop()

total_accounts = len(df)
total_outstanding = df["Outstanding_Amount"].sum()

high_risk = int((df["Risk_Category"] == "High").sum())
medium_risk = int((df["Risk_Category"] == "Medium").sum())
low_risk = int((df["Risk_Category"] == "Low").sum())


# ============================================================
# FINANCIAL SUMMARY
# ============================================================

st.divider()
st.header("Financial Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Accounts", f"{total_accounts:,}")

with col2:
    st.metric("Total Outstanding", format_inr(total_outstanding))

with col3:
    st.metric("High-Risk Accounts", f"{high_risk:,}")

with col4:
    st.metric("Medium-Risk Accounts", f"{medium_risk:,}")

st.caption(f"Low-Risk Accounts: {low_risk:,}")

st.divider()


# ============================================================
# MAIN DASHBOARD TABS
# ============================================================

analytics_tab, ai_tab, data_tab, reports_tab = st.tabs(
    [
        "📊 Risk & Exposure",
        "🤖 AI Assistant",
        "📋 Data & Quality",
        "📥 Reports & Downloads",
    ]
)


# ============================================================
# TAB 1: RISK AND EXPOSURE ANALYTICS
# ============================================================

with analytics_tab:
    st.header("Risk Overview")

    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(
            risk_category_chart(df),
            use_container_width=True,
        )

    with col2:
        st.plotly_chart(
            risk_exposure_chart(df),
            use_container_width=True,
        )

    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(
            risk_score_chart(df),
            use_container_width=True,
        )

    with col2:
        st.plotly_chart(
            ageing_distribution_chart(df),
            use_container_width=True,
        )

    st.divider()
    st.header("Exposure Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(
            top_exposure_chart(df),
            use_container_width=True,
        )

    with col2:
        st.plotly_chart(
            regional_exposure_chart(df),
            use_container_width=True,
        )

    st.subheader("Regional Risk")
    st.plotly_chart(
        regional_risk_chart(df),
        use_container_width=True,
    )

    st.divider()
    st.header("High-Risk Accounts")

    high_risk_accounts = df[
        df["Risk_Category"] == "High"
    ].copy()

    if "Risk_Score" in high_risk_accounts.columns:
        high_risk_accounts = high_risk_accounts.sort_values(
            by="Risk_Score",
            ascending=False,
        )

    display_columns = safe_columns(
        high_risk_accounts,
        [
            "Account_ID",
            "Customer_Name",
            "Outstanding_Amount",
            "Ageing_Days",
            "Risk_Score",
            "Risk_Category",
            "Risk_Reason",
        ],
    )

    if high_risk_accounts.empty:
        st.info(
            "No high-risk accounts identified under the current thresholds."
        )
    else:
        st.dataframe(
            high_risk_accounts[display_columns],
            use_container_width=True,
        )


# ============================================================
# TAB 2: AI INSIGHTS AND FINANCIAL QUESTIONS
# ============================================================

with ai_tab:
    st.header("AI-Generated Financial Insights")

    st.write(
        "Generate a narrative summary of the analyzed portfolio using "
        "the validated financial context."
    )

    if st.button(
        "Generate Financial Insights",
        key="generate_financial_insights",
        type="primary",
    ):
        with st.spinner("Generating financial insights..."):
            try:
                insight = generate_financial_summary(financial_data)

                if insight:
                    st.session_state["financial_summary"] = insight
                else:
                    st.warning("The AI returned an empty summary.")

            except Exception:
                st.warning(
                    "AI insights are temporarily unavailable. "
                    "Your financial analysis is still available. "
                    "Please try again shortly."
                )

    if st.session_state.get("financial_summary"):
        st.subheader("Financial Insights")
        st.markdown(st.session_state["financial_summary"])

    st.divider()
    st.header("Ask InsightForge")

    question = st.text_input(
        "Ask a question about your financial data",
        placeholder=(
            "Example: Which region has the highest outstanding exposure?"
        ),
        key="financial_question",
    )

    if st.button("Ask InsightForge", key="ask_insightforge"):
        if question.strip():
            with st.spinner("Analyzing financial data..."):
                try:
                    answer = answer_financial_question(
                        question.strip(),
                        financial_data,
                    )
                    st.session_state["last_financial_answer"] = answer

                except Exception:
                    st.error(
                        "Unable to answer your question right now. "
                        "Please try again shortly."
                    )
        else:
            st.warning("Please enter a question.")

    if st.session_state.get("last_financial_answer"):
        st.subheader("Answer")
        st.write(st.session_state["last_financial_answer"])

    st.caption(
        "AI-generated text is intended to support interpretation. "
        "Use the analyzed dataset and verified calculations as the "
        "source of financial figures."
    )


# ============================================================
# TAB 3: DATA TABLES AND QUALITY CHECKS
# ============================================================

with data_tab:
    st.header("Dataset Overview")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Records", f"{len(df):,}")

    with col2:
        st.metric("Total Columns", f"{len(df.columns):,}")

    with col3:
        st.metric("High-Risk Accounts", f"{high_risk:,}")

    st.divider()
    st.header("Data Quality Check")

    quality_columns = safe_columns(
        df,
        [
            "Account_ID",
            "Customer_Name",
            "Outstanding_Amount",
            "Ageing_Days",
            "Risk_Category",
        ],
    )

    missing_values = df[quality_columns].isna().sum()
    total_missing = int(missing_values.sum())

    negative_amounts = df[df["Outstanding_Amount"] < 0]

    if total_missing == 0 and negative_amounts.empty:
        st.success(
            "Data quality check passed — no missing values in key fields "
            "or negative outstanding amounts detected."
        )
    else:
        st.warning(
            "Data review recommended. Review the checks below before "
            "interpreting the results."
        )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Missing Values")

        if total_missing == 0:
            st.success("No missing values found in the checked fields.")
        else:
            st.warning(f"{total_missing:,} missing values detected.")

            st.dataframe(
                missing_values[missing_values > 0].rename(
                    "Missing Values"
                ).to_frame(),
                use_container_width=True,
            )

    with col2:
        st.subheader("Negative Outstanding Amounts")

        if negative_amounts.empty:
            st.success("No negative outstanding amounts found.")
        else:
            st.warning(
                f"{len(negative_amounts):,} records have negative "
                "outstanding amounts."
            )

            negative_columns = safe_columns(
                negative_amounts,
                [
                    "Account_ID",
                    "Customer_Name",
                    "Outstanding_Amount",
                ],
            )

            st.dataframe(
                negative_amounts[negative_columns],
                use_container_width=True,
            )

    st.caption(
        "Negative balances may represent legitimate credits or refunds. "
        "Review them rather than automatically treating them as errors."
    )

    st.divider()
    st.header("All Account-Level Data")

    st.dataframe(
        df,
        use_container_width=True,
    )


# ============================================================
# TAB 4: REPORTS AND DOWNLOADS
# ============================================================

with reports_tab:
    st.header("Reports & Downloads")

    st.write(
        "Generate an executive PDF report or export the analyzed "
        "dataset and anomaly details."
    )

    st.divider()
    st.subheader("Executive PDF Report")

    if st.button(
        "Generate PDF Report",
        key="generate_pdf_report",
        type="primary",
    ):
        try:
            pdf_bytes = generate_financial_report(
                df=df,
                summary_text=st.session_state.get("financial_summary", ""),
            )

            st.session_state["financial_pdf"] = pdf_bytes
            st.success("PDF report generated successfully.")

        except Exception as error:
            st.session_state["financial_pdf"] = None
            st.error(f"Could not generate PDF report: {error}")

    if st.session_state.get("financial_pdf") is not None:
        st.download_button(
            label="Download PDF Report",
            data=st.session_state["financial_pdf"],
            file_name="InsightForge_Financial_Report.pdf",
            mime="application/pdf",
            key="download_pdf_report",
        )

    st.divider()
    st.subheader("Risk Analysis (CSV)")

    risk_csv = df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="Download Risk Analysis (CSV)",
        data=risk_csv,
        file_name="risk_analysis.csv",
        mime="text/csv",
        key="download_risk_csv",
    )

    st.divider()
    st.subheader("Anomaly Analysis (JSON)")

    anomaly_columns = safe_columns(
        df,
        [
            "Account_ID",
            "Customer_Name",
            "Outstanding_Amount",
            "Ageing_Days",
            "Anomaly_Score",
            "Anomaly_Type",
            "Anomaly_Category",
            "Anomaly_Reason",
        ],
    )

    anomaly_json = df[anomaly_columns].to_json(
        orient="records",
        indent=2,
    ).encode("utf-8")

    st.download_button(
        label="Download Anomaly Analysis (JSON)",
        data=anomaly_json,
        file_name="anomaly_analysis.json",
        mime="application/json",
        key="download_anomaly_json",
    )

    st.caption(
        "Exports contain the results of the currently analyzed dataset "
        "and risk thresholds."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()
st.caption("InsightForge — Hybrid Financial Intelligence System")
