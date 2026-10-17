import os
import sys

PROJECT_ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0,PROJECT_ROOT)

import pandas as pd
import numpy as np

from ai.risk_detection import DEFAULT_RISK_CONFIG,perform_risk_analysis


COLUMN_ALIASES = {
    "Account_ID": [
        "cust code", "cust.code", "customer code",
        "customer id", "account id", "debtor code",
        "debtor number", "account number", "client id"
    ],
    "Customer_Name": [
        "customer name", "client name", "debtor name",
        "account name", "customer", "debtor", "party"
    ],
    "Outstanding_Amount": [
        "may'26 exp.", "outstanding amount",
        "outstanding balance", "balance due",
        "amount due", "open balance",
        "receivable amount", "total outstanding"
    ],
    "Region": [
        "region", "territory", "sales region",
        "geography", "location"
    ],
    "Account_Status": [
        "active / inactive", "account status",
        "customer status", "status"
    ],
}

def normalize_column_name(name):
    """Normalize headings for case- and punctuation-insensitive matching."""
    import re
    return re.sub(
        r"[^a-z0-9]+",
        "",
        str(name).replace("\u00a0", " ").strip().lower()
    )

def detect_column_mapping(columns):
    """Map recognized input headings to InsightForge's internal fields."""
    normalized_columns = {}
    for column in columns:
        key = normalize_column_name(column)
        normalized_columns.setdefault(key, []).append(column)

    mapping = {}
    for target, aliases in COLUMN_ALIASES.items():
        candidates = [target] + aliases
        for candidate in candidates:
            key = normalize_column_name(candidate)
            if key in normalized_columns:
                mapping[target] = normalized_columns[key][0]
                break

    return mapping

AGE_BUCKETS={
    "0-30":15,
    "31-60":45,
    "61-90":75,
    "91-120":105,
    "121-150":135,
    "151-180":165,
    "181-210":195,
    "211-335":273,
    "335-365":350,
    "366-395":380,
    "396-730":563,
    "731-760":745,
    "761-1028":895,
    "> 1028":1029
}



def detect_ageing_columns(columns):
    """Recognize individual ageing buckets, excluding summary columns."""
    import re

    detected = {}

    for column in columns:
        name = str(column).lower().strip()

        # Normalize dash characters.
        name = (
            name.replace("\u2013", "-")
                .replace("\u2014", "-")
                .replace("\u2212", "-")
        )

        # Exclude totals and known aggregate ageing summaries.
        if any(word in name for word in [
            "total", "subtotal", "grand total", "overall"
        ]):
            continue

        # Exclude aggregate summary headings such as "> 90 days".
        if re.search(r">\s*90\s*days?", name):
            continue

        # Exclude duplicate/summary ranges such as "91-120 .1".
        if re.search(r"\.\d+$", name):
            continue

        # Match ranges such as "0-30", "31-60 days".
        match = re.search(
            r"(\d+)\s*(?:-|to)\s*(\d+)\s*(?:days?)?",
            name
        )

        if match:
            lower = int(match.group(1))
            upper = int(match.group(2))

            if upper > lower:
                detected[column] = (lower + upper) / 2
                continue

        # Match open-ended buckets such as "> 1028".
        match = re.search(r"(?:>|>=)\s*(\d+)", name)
        if match:
            detected[column] = float(match.group(1)) + 1
            continue

        # Match buckets such as "1028+".
        match = re.search(r"(\d+)\s*\+", name)
        if match:
            detected[column] = float(match.group(1))
            continue

    return detected

def clean_number(series):
    return pd.to_numeric(
        series.astype(str)
        .str.replace(",","",regex=False)
        .str.replace("₹","",regex=False)
        .str.strip()
        .replace({"-":None,"":None,"nan":None,"None":None}),
        errors="coerce"
    ).fillna(0)

def prepare_uploaded_data(raw_df, risk_config=None):
    df=raw_df.copy()

    df.columns=[
        str(column).replace("\u00a0"," ").strip()
        for column in df.columns
    ]

    df=df.dropna(how="all")
    df=df.loc[:,~df.columns.duplicated()].copy()

    
    mapping = detect_column_mapping(df.columns)

    required_fields = [
        "Account_ID",
        "Customer_Name",
        "Outstanding_Amount",
    ]

    missing = [
        field for field in required_fields
        if field not in mapping
    ]

    if missing:
        raise ValueError(
            "Could not identify these required fields: "
            + ", ".join(missing)
            + ". Available columns: "
            + ", ".join(map(str, df.columns))
        )

    # Optional fields can be absent in some financial reports.
    for field in ["Region", "Account_Status"]:
        if field not in mapping:
            mapping[field] = None


    result=pd.DataFrame(index=df.index)

    
    result["Account_ID"] = (
        df[mapping["Account_ID"]]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    result["Customer_Name"] = (
        df[mapping["Customer_Name"]]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
    )

    result["Outstanding_Amount"] = clean_number(
        df[mapping["Outstanding_Amount"]]
    )

    result["Region"] = (
        df[mapping["Region"]].fillna("Unknown").astype(str).str.strip()
        if mapping["Region"] is not None
        else "Unknown"
    )

    result["Account_Status"] = (
        df[mapping["Account_Status"]].fillna("Unknown").astype(str).str.strip()
        if mapping["Account_Status"] is not None
        else "Unknown"
    )


    
    
    # Support either an existing Ageing_Days field or ageing buckets.
    existing_ageing_column = next(
        (
            column for column in df.columns
            if normalize_column_name(column) in [
                "ageingdays", "agingdays", "daysoverdue",
                "dayspastdue", "daysoutstanding"
            ]
        ),
        None
    )

    if existing_ageing_column is not None:
        result["Ageing_Days"] = clean_number(
            df[existing_ageing_column]
        ).clip(lower=0)

        result["Ageing_Over_90"] = np.where(
            result["Ageing_Days"] > 90,
            result["Outstanding_Amount"],
            0
        )

    else:
        bucket_columns = detect_ageing_columns(df.columns)

        if not bucket_columns:
            raise ValueError(
                "No ageing data found. Provide an Ageing_Days column "
                "or individual ageing buckets such as '0-30' and '31-60'."
            )

        amounts = pd.DataFrame(
            {
                column: clean_number(df[column])
                for column in bucket_columns
            },
            index=df.index
        )

        weighted_days = sum(
            amounts[column] * midpoint
            for column, midpoint in bucket_columns.items()
        )

        bucket_total = amounts.sum(axis=1)

        result["Ageing_Days"] = np.where(
            bucket_total > 0,
            weighted_days / bucket_total,
            0
        )

        result["Ageing_Over_90"] = sum(
            amounts[column]
            for column, midpoint in bucket_columns.items()
            if midpoint > 90
        )

    result=result[result["Account_ID"].ne("")].copy()

    result["Outstanding_Amount"]=result["Outstanding_Amount"].clip(lower=0)
    result["Ageing_Days"]=result["Ageing_Days"].fillna(0)

    if result.empty:
        raise ValueError(
            "No valid accounts were found. Check the account ID column."
        )

    result = perform_risk_analysis(
        result,
        risk_config or DEFAULT_RISK_CONFIG
    )

    exposure=result["Outstanding_Amount"]
    ageing=result["Ageing_Days"]

    amount_threshold=exposure.quantile(0.90)
    ageing_threshold=ageing.quantile(0.90)

    high_amount=exposure>=amount_threshold
    high_ageing=ageing>=ageing_threshold

    result["Anomaly_Score"]=(
        high_amount.astype(int)+high_ageing.astype(int)
    )

    result["Anomaly_Type"]=np.select(
        [
            high_amount&high_ageing,
            high_amount,
            high_ageing
        ],
        [
            "High exposure and ageing",
            "Unusually high exposure",
            "Unusually high ageing"
        ],
        default="Normal"
    )

    result["Anomaly_Category"]=np.select(
        [
            result["Anomaly_Score"]>=2,
            result["Anomaly_Score"]==1
        ],
        [
            "High",
            "Medium"
        ],
        default="Normal"
    )

    result["Anomaly_Reason"]=np.select(
        [
            high_amount&high_ageing,
            high_amount,
            high_ageing
        ],
        [
            "Exposure and ageing are both at or above their dataset's 90th percentile",
            "Exposure is at or above its dataset's 90th percentile",
            "Ageing is at or above its dataset's 90th percentile"
        ],
        default="No percentile-based anomaly detected"
    )

    return result.reset_index(drop=True)

test_columns = [
    "0-30",
    "31-60",
    "61-90",
    "91-120",
    "121-150",
    "151-180",
    "181-210",
    "211-335",
    "335-365",
    "366-395",
    "396-730",
    "731-760",
    "761-1028",
    "> 1028",
    "> 90 days",
    "91-120 .1",
    "121-180",
    "181-365",
    ">365",
]

print(detect_ageing_columns(test_columns).keys())