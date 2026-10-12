import streamlit as st
import pandas as pd
import json
import sys
import os
import re

from visualizations import risk_category_chart,risk_exposure_chart,top_exposure_chart,ageing_distribution_chart,risk_score_chart,regional_exposure_chart,regional_risk_chart
from upload_processor import prepare_uploaded_data

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"../ai")))

from financial_context import create_financial_context
from llm import answer_financial_question,generate_financial_summary

st.set_page_config(page_title="InsightForge",page_icon="📊",layout="wide")

DATA_FILE=os.path.abspath(os.path.join(os.path.dirname(__file__),"../outputs/risk_analysis.csv"))

@st.cache_data
def load_data():
    return pd.read_csv(DATA_FILE)


HEADER_HINTS = {
    "account_id": [
        "cust code", "cust.code", "customer code",
        "customer id", "account id", "debtor code"
    ],
    "customer_name": [
        "customer name", "client name", "debtor name",
        "account name", "customer", "debtor"
    ],
    "outstanding": [
        "outstanding amount", "outstanding balance",
        "receivable amount", "open balance",
        "may'26 exp.", "amount due", "balance due"
    ],
    "region": ["region", "territory", "sales region"],
    "status": [
        "active / inactive", "account status",
        "customer status", "status"
    ],
}


def normalize_header(value):
    value = str(value).replace("\u00a0", " ").strip().lower()
    return re.sub(r"[^a-z0-9]+", "", value)


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

        # Ageing headings can help identify multi-purpose
        # financial reports even when other labels vary.
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

    # Avoid confidently selecting a report title or data row
    # when there is too little evidence of actual headings.
    if best_score < 6:
        return None

    return best_row


st.title("InsightForge")
st.subheader("Financial Intelligence Dashboard")
st.write("Interactive analysis of financial receivables, risk and outstanding exposure.")

st.divider()

st.header("Upload Financial Dataset")

uploaded_file=st.file_uploader(
    "Upload debtor/receivables data",
    type=["csv","xlsx","xls"],
    key="financial_upload"
)

if uploaded_file is not None:
    try:
        uploaded_file.seek(0)

        if uploaded_file.name.lower().endswith(".csv"):
            preview = pd.read_csv(
                uploaded_file,
                header=None,
                nrows=30
            )
        else:
            preview = pd.read_excel(
                uploaded_file,
                header=None,
                nrows=30
            )

        detected_row = detect_header_row(preview)

        if detected_row is not None:
            st.success(
                f"Suggested header row: {detected_row + 1}"
            )
            default_row = detected_row + 1
        else:
            st.warning(
                "Could not confidently detect the header row. "
                "Please select it manually."
            )
            default_row = 5

        manual_override = st.checkbox(
            "Choose header row manually",
            value=detected_row is None
        )

        if manual_override:
            header_row = st.number_input(
                "Header row number",
                min_value=1,
                max_value=100,
                value=default_row,
                step=1,
                help="Enter the spreadsheet row containing the column names."
            )
        else:
            header_row = default_row

        uploaded_file.seek(0)

        if uploaded_file.name.lower().endswith(".csv"):
            raw_df = pd.read_csv(
                uploaded_file,
                header=int(header_row) - 1
            )
        else:
            raw_df = pd.read_excel(
                uploaded_file,
                header=int(header_row) - 1
            )

        raw_df.columns = [
            str(column).replace("\u00a0", " ").strip()
            for column in raw_df.columns
        ]
        raw_df = raw_df.dropna(how="all")

        st.subheader("Uploaded Data Preview")
        st.dataframe(raw_df.head(10), use_container_width=True)
        st.caption(
            f"Rows: {len(raw_df)} | Columns: {len(raw_df.columns)}"
        )

        df = prepare_uploaded_data(raw_df)
        st.success("Uploaded dataset processed successfully.")

    except Exception as e:
        st.error(f"Could not process uploaded file: {e}")
        st.stop()

else:
    try:
        df=load_data()
        st.info("Using the default processed dataset. Upload a file to analyze another dataset.")
    except Exception as e:
        st.error(f"Could not load the default dataset: {e}")
        st.stop()

context=create_financial_context(df)
financial_data=json.dumps(context,indent=2)

st.divider()

st.header("Financial Summary")

total_accounts=len(df)
total_outstanding=df["Outstanding_Amount"].sum()
high_risk=(df["Risk_Category"]=="High").sum()
medium_risk=(df["Risk_Category"]=="Medium").sum()
low_risk=(df["Risk_Category"]=="Low").sum()

col1,col2,col3,col4=st.columns(4)

with col1:
    st.metric("Total Accounts",total_accounts)

with col2:
    st.metric("Total Outstanding",f"₹{total_outstanding:,.0f}")

with col3:
    st.metric("High Risk Accounts",high_risk)

with col4:
    st.metric("Medium Risk Accounts",medium_risk)

st.caption(f"Low Risk Accounts: {low_risk}")

st.divider()

st.header("Risk Overview")

col1,col2=st.columns(2)

with col1:
    st.plotly_chart(risk_category_chart(df),use_container_width=True)

with col2:
    st.plotly_chart(risk_exposure_chart(df),use_container_width=True)

col1,col2=st.columns(2)

with col1:
    st.plotly_chart(risk_score_chart(df),use_container_width=True)

with col2:
    st.plotly_chart(ageing_distribution_chart(df),use_container_width=True)

st.divider()

st.header("Exposure Analysis")

col1,col2=st.columns(2)

with col1:
    st.plotly_chart(top_exposure_chart(df),use_container_width=True)

with col2:
    st.plotly_chart(regional_exposure_chart(df),use_container_width=True)

st.plotly_chart(regional_risk_chart(df),use_container_width=True)

st.divider()

st.header("AI-Generated Financial Insights")

if st.button("Generate Financial Insights"):
    with st.spinner("Generating financial insights..."):
        try:
            insight=generate_financial_summary(financial_data)
            st.write(insight)
        except Exception as e:
            st.error(f"Unable to generate financial insights: {e}")

st.divider()

st.header("High-Risk Accounts")

high_risk_accounts=df[df["Risk_Category"]=="High"].sort_values(
    by="Risk_Score",
    ascending=False
)

display_columns=[
    "Account_ID",
    "Customer_Name",
    "Outstanding_Amount",
    "Ageing_Days",
    "Risk_Score",
    "Risk_Category",
    "Risk_Reason"
]

st.dataframe(
    high_risk_accounts[display_columns],
    use_container_width=True
)

st.divider()

st.header("Account-Level Data")

st.dataframe(df,use_container_width=True)

st.divider()

st.header("Ask InsightForge")

question=st.text_input("Ask a financial question")

if st.button("Ask InsightForge"):
    if question.strip():
        with st.spinner("Analyzing financial data..."):
            try:
                answer=answer_financial_question(question,financial_data)
                st.write(answer)
            except Exception as e:
                st.error(f"Unable to answer your question: {e}")
    else:
        st.warning("Please enter a question.")

st.caption("InsightForge — Hybrid Financial Intelligence System")
