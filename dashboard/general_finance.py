
import re
import pandas as pd


def normalize_name(value):
    """Normalize a column name for matching."""
    return re.sub(r"[^a-z0-9]+", "", str(value).strip().lower())


def detect_general_header_row(preview):
    """Find a likely header row in a general financial dataset."""
    if preview is None or preview.empty:
        return None

    terms = (
        "state", "year", "revenue", "expenditure",
        "capitaloutlay", "expense", "income", "profit",
        "loss", "debt", "tax", "budget", "sales",
        "amount", "total", "date", "category",
        "region", "country", "department"
    )

    best_row = None
    best_score = -1

    for index, row in preview.iterrows():
        values = [
            str(value).strip()
            for value in row.tolist()
            if pd.notna(value) and str(value).strip()
        ]

        if len(values) < 2:
            continue

        names = [normalize_name(value) for value in values]

        text_ratio = (
            sum(any(char.isalpha() for char in value) for value in values)
            / len(values)
        )

        term_hits = sum(
            any(term in name for term in terms)
            for name in names
        )

        unique_ratio = len(set(names)) / len(names)
        score = term_hits * 2 + text_ratio * 3 + unique_ratio

        if text_ratio < 0.35:
            score -= 4

        if score > best_score:
            best_score = score
            best_row = int(index)

    return best_row if best_score >= 4 else None


def prepare_general_finance_data(df):
    """Clean a financial dataset without requiring receivables columns."""
    result = df.copy()

    result.columns = [
        str(column).replace("\u00a0", " ").strip()
        for column in result.columns
    ]

    result = result.dropna(how="all").dropna(axis=1, how="all")

    # Convert numeric-looking text columns to numbers.
    for column in result.columns:
        if result[column].dtype == "object":
            cleaned = (
                result[column]
                .astype(str)
                .str.strip()
                .str.replace(",", "", regex=False)
                .str.replace("$", "", regex=False)
                .str.replace("₹", "", regex=False)
                .str.replace("%", "", regex=False)
            )

            converted = pd.to_numeric(cleaned, errors="coerce")
            nonempty = result[column].notna().sum()

            if (
                nonempty > 0
                and converted.notna().sum() / nonempty >= 0.85
            ):
                result[column] = converted

    return result


def get_numeric_columns(df):
    """Return numeric columns that contain at least one value."""
    return [
        column
        for column in df.columns
        if pd.api.types.is_numeric_dtype(df[column])
        and df[column].notna().any()
    ]
