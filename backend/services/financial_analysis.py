import pandas as pd


def calculate_kpis(df):
    """Calculate key financial performance indicators."""

    outstanding_col = "may'26_exp."

    # Convert outstanding values to numeric
    outstanding = pd.to_numeric(
        df[outstanding_col],
        errors="coerce"
    ).fillna(0)

    total_outstanding = outstanding.sum()
    total_accounts = df["cust.code"].nunique()
    average_outstanding = (
        total_outstanding / total_accounts
        if total_accounts > 0
        else 0
    )

    kpis = {
        "total_outstanding": round(float(total_outstanding), 2),
        "total_accounts": int(total_accounts),
        "average_outstanding": round(float(average_outstanding), 2)
    }

    return kpis