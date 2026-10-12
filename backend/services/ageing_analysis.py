import pandas as pd


def calculate_ageing(df):
    """Calculate outstanding amount by ageing category."""

    ageing_columns = {
        "0-30": "0-30",
        "31-60": "31-60",
        "61-90": "61-90",
        "91-120": "91-120",
        "121-150": "121-150",
        "151-180": "151-180",
        "181-210": "181-210",
        "211-335": "211-335",
        "335-365": "335-365",
        "366-395": "366-395",
        "396-730": "396-730",
        "731-760": "731-760",
        "761-1028": "761-1028",
        "1028+": ">_1028"
    }

    ageing = {}

    for label, column in ageing_columns.items():
        values = pd.to_numeric(
            df[column],
            errors="coerce"
        ).fillna(0)

        ageing[label] = round(float(values.sum()), 2)

    return ageing