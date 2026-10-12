import pandas as pd
import numpy as np
import re

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


def detect_age_bucket_columns(df):
    """Match ageing columns to the existing AGE_BUCKETS midpoints."""
    bucket_columns = {}

    for column in df.columns:
        heading = str(column).replace("\u00a0", " ").strip().lower()

        # Check for open-ended buckets such as "> 1028".
        open_ended = re.findall(r">\s*(\d{1,4})", heading)
        for number in open_ended:
            bucket_label = f"> {int(number)}"
            if bucket_label in AGE_BUCKETS:
                bucket_columns[column] = AGE_BUCKETS[bucket_label]
                break

        if column in bucket_columns:
            continue

        # Check all ranges in the heading, including headings with prefixes.
        # Supports forms such as "0-30 days", "0 to 30", and "Age 0–30".
        ranges = re.findall(
            r"(?<!\d)(\d{1,4})\s*(?:-|–|—|to)\s*(\d{1,4})(?!\d)",
            heading,
        )

        for start, end in ranges:
            start, end = int(start), int(end)

            for bucket_label, midpoint in AGE_BUCKETS.items():
                match = re.fullmatch(
                    r"\s*(\d+)\s*-\s*(\d+)\s*",
                    bucket_label,
                )

                if match:
                    expected_start = int(match.group(1))
                    expected_end = int(match.group(2))

                    if (start, end) == (expected_start, expected_end):
                        bucket_columns[column] = midpoint
                        break

            if column in bucket_columns:
                break

    return bucket_columns



COLUMN_ALIASES = {
    "Account_ID": [
        "Cust.Code", "Cust Code", "Customer Code",
        "Customer ID", "Account ID", "Account Number",
        "Debtor Code", "Debtor ID", "Party Code",
        "Party ID", "Customer Account"
    ],
    "Customer_Name": [
        "Customer Name", "Client", "Client Name",
        "Debtor Name", "Account Name", "Customer",
        "Debtor", "Party Name", "Customer Legal Name"
    ],
    "Outstanding_Amount": [
        "May'26 Exp.", "Outstanding Balance",
        "Outstanding Amount", "Receivable Amount",
        "Accounts Receivable", "Open Balance",
        "Amount Outstanding", "Total Receivables",
        "Balance Due", "Net Outstanding",
        "Closing Balance", "Total Due"
    ],
    "Region": [
        "Region", "Area", "Territory",
        "Sales Region", "Geography", "Zone",
        "State", "Market"
    ],
    "Account_Status": [
        "Active / Inactive", "Account Status",
        "Customer Status", "Status",
        "Active Status", "Customer Activity Status"
    ],
}


def normalize_column_name(name):
    name = str(name).replace("\u00a0", " ").strip().lower()
    return re.sub(r"[^a-z0-9]+", "", name)


def map_financial_columns(df):
    """Map uploaded headings to InsightForge's standard field names."""
    normalized_columns = {}

    for column in df.columns:
        key = normalize_column_name(column)
        normalized_columns.setdefault(key, []).append(column)

    mapped = {}
    missing = []

    for standard_name, aliases in COLUMN_ALIASES.items():
        candidates = [standard_name] + aliases
        matches = []

        for alias in candidates:
            key = normalize_column_name(alias)
            matches.extend(normalized_columns.get(key, []))

        matches = list(dict.fromkeys(matches))

        if matches:
            # Prefer an exact standard-name match when available.
            standard_key = normalize_column_name(standard_name)
            exact = [
                col for col in matches
                if normalize_column_name(col) == standard_key
            ]
            mapped[standard_name] = exact[0] if exact else matches[0]
        else:
            missing.append(standard_name)

    if missing:
        raise ValueError(
            "Could not identify required fields: "
            + ", ".join(missing)
            + ". Available columns: "
            + ", ".join(map(str, df.columns))
        )

    return mapped



def clean_number(series):
    return pd.to_numeric(
        series.astype(str)
        .str.replace(",","",regex=False)
        .str.replace("₹","",regex=False)
        .str.strip()
        .replace({"-":None,"":None,"nan":None,"None":None}),
        errors="coerce"
    ).fillna(0)

def prepare_uploaded_data(raw_df):
    df=raw_df.copy()
    df.columns=[
        str(c).replace("\u00a0"," ").strip()
        for c in df.columns
    ]
    df=df.dropna(how="all")
    df=df.loc[:,~df.columns.duplicated()].copy()

    
    column_map = map_financial_columns(df)

    result = pd.DataFrame(index=df.index)
    result["Account_ID"] = (
        df[column_map["Account_ID"]]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    result["Customer_Name"] = (
        df[column_map["Customer_Name"]]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
    )
    result["Outstanding_Amount"] = clean_number(
        df[column_map["Outstanding_Amount"]]
    )
    result["Region"] = (
        df[column_map["Region"]]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
    )
    result["Account_Status"] = (
        df[column_map["Account_Status"]]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
    )

    bucket_columns = detect_age_bucket_columns(df)

    if bucket_columns:
        amounts=pd.DataFrame({
            column:clean_number(df[column])
            for column in bucket_columns
        },index=df.index)
        weighted_days=sum(
            amounts[column]*midpoint
            for column,midpoint in bucket_columns.items()
        )
        bucket_total=amounts.sum(axis=1)
        result["Ageing_Days"]=np.where(
            bucket_total>0,
            weighted_days/bucket_total,
            0
        )
        result["Ageing_Over_90"]=sum(
            amounts[column]
            for column,midpoint in bucket_columns.items()
            if midpoint>90
        )
    else:
        raise ValueError(
            "No recognized ageing bucket columns were found."
        )

    result=result[result["Account_ID"].ne("")].copy()
    result["Outstanding_Amount"]=result["Outstanding_Amount"].clip(lower=0)
    result["Ageing_Days"]=result["Ageing_Days"].fillna(0)

    exposure=result["Outstanding_Amount"]
    p50=exposure.quantile(0.50)
    p75=exposure.quantile(0.75)
    p90=exposure.quantile(0.90)

    result["Exposure_Score"]=np.select(
        [exposure>=p90,exposure>=p75,exposure>=p50],
        [3,2,1],
        default=0
    )

    ageing=result["Ageing_Days"]
    result["Ageing_Score"]=np.select(
        [ageing>=90,ageing>=60,ageing>=30],
        [3,2,1],
        default=0
    )

    result["Risk_Score"]=result["Exposure_Score"]+result["Ageing_Score"]
    result["Risk_Category"]=np.select(
        [result["Risk_Score"]>=5,result["Risk_Score"]>=3],
        ["High","Medium"],
        default="Low"
    )

    result["Risk_Reason"]=np.select(
        [
            (result["Ageing_Score"]>=2)&(result["Exposure_Score"]>=2),
            result["Ageing_Score"]>=2,
            result["Exposure_Score"]>=2
        ],
        [
            "High ageing and high exposure",
            "High ageing",
            "High exposure"
        ],
        default="Lower relative risk indicators"
    )

    amount_threshold=exposure.quantile(0.90)
    ageing_threshold=ageing.quantile(0.90)
    high_amount=exposure>amount_threshold
    high_ageing=ageing>ageing_threshold

    result["Anomaly_Score"]=high_amount.astype(int)+high_ageing.astype(int)
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
        [result["Anomaly_Score"]>=2,result["Anomaly_Score"]==1],
        ["High","Medium"],
        default="Normal"
    )

    return result.reset_index(drop=True)
