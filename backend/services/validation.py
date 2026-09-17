def validate_dataset(df):
    """Perform data validation and financial consistency checks."""

    missing_values = int(df.isnull().sum().sum())
    duplicate_records = int(df.duplicated().sum())

    outstanding = df["may'26_exp."].sum()

    ageing_columns = [
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
        ">_1028"
    ]

    ageing_total = sum(
        df[column].sum()
        for column in ageing_columns
    )

    ageing_difference = abs(outstanding - ageing_total)

    financial_consistency = bool(ageing_difference < 0.01)

    validation_result = {
    "missing_values": int(missing_values),
    "duplicate_records": int(duplicate_records),
    "invalid_records": 0,
    "ageing_total": round(float(ageing_total), 2),
    "outstanding_total": round(float(outstanding), 2),
    "ageing_difference": round(float(ageing_difference), 2),
    "financial_consistency": bool(financial_consistency),
    "validated": bool(
        duplicate_records == 0
        and financial_consistency
    )
}
    return validation_result