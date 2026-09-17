import pandas as pd


def calculate_regional_exposure(df):
    """Calculate outstanding exposure by region."""

    outstanding_col = "may'26_exp."

    df[outstanding_col] = pd.to_numeric(
        df[outstanding_col],
        errors="coerce"
    ).fillna(0)

    regional_data = (
        df.groupby("region")[outstanding_col]
        .sum()
        .sort_values(ascending=False)
    )

    regions = {
        str(region): round(float(amount), 2)
        for region, amount in regional_data.items()
    }

    return regions