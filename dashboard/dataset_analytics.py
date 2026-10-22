"""Dataset profiling and column-aware analytics for uploaded tabular data."""

import re
from datetime import date, datetime

import numpy as np
import pandas as pd


_IDENTIFIER_NAME = re.compile(
    r"(^|_)(id|code|number|no|zip|postal|postcode|phone|accountnum|"
    r"customernum|invoicenum|ordernum|invoice|order)(_|$)",
    re.IGNORECASE,
)
_FINANCIAL_TERMS = {
    "revenue": ("revenue", "sales", "income", "turnover"),
    "expense": ("expense", "expenditure", "cost", "spending"),
    "outstanding": ("outstanding", "receivable", "balance due", "amount due"),
    "balance": ("balance", "cash", "asset", "liability", "equity"),
    "profit": ("profit", "margin", "earnings"),
}
_DATETIME_FORMATS = (
    "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y",
    "%Y/%m/%d", "%b %Y", "%B %Y",
)


def _normalized_name(value):
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def numeric_values(series):
    """Return a numeric view of a Series without changing the source."""
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")

    values = (
        series.astype("string")
        .str.strip()
        .str.replace(r"^\((.*)\)$", r"-\1", regex=True)
        .str.replace(
            r"^(-?)\s*(?:INR|USD|EUR|GBP|Rs\.?)\s*",
            r"\1",
            regex=True,
            case=False,
        )
        .str.replace(",", "", regex=False)
        .str.replace("$", "", regex=False)
        .str.replace("₹", "", regex=False)
        .str.replace("€", "", regex=False)
        .str.replace("£", "", regex=False)
        .str.replace("%", "", regex=False)
    )
    return pd.to_numeric(values, errors="coerce")


def _is_identifier(name, series, numeric):
    normalized = _normalized_name(name)
    if _IDENTIFIER_NAME.search(normalized):
        return True

    present = series.dropna()
    if present.empty or pd.api.types.is_numeric_dtype(series):
        return False

    unique_ratio = present.nunique(dropna=True) / len(present)
    values = present.astype(str).str.strip()
    looks_like_code = values.str.fullmatch(r"[A-Za-z]*[\d_-]+").mean() >= 0.8
    return bool(unique_ratio >= 0.8 and looks_like_code and numeric.notna().sum() == 0)


def _parse_datetime(series):
    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series, errors="coerce")
    if not (
        pd.api.types.is_object_dtype(series)
        or pd.api.types.is_string_dtype(series)
    ):
        return None

    present = series.dropna()
    if present.empty:
        return None
    sample = present.astype(str).head(100)
    parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
    if parsed.notna().mean() < 0.8:
        parsed = pd.Series(index=sample.index, dtype="datetime64[ns]")
        for fmt in _DATETIME_FORMATS:
            candidate = pd.to_datetime(sample, errors="coerce", format=fmt)
            parsed = parsed.fillna(candidate)
        if parsed.notna().mean() < 0.8:
            return None
    return pd.to_datetime(series, errors="coerce", format="mixed")


def _column_role(name, kind, identifier):
    if identifier:
        return "identifier"
    if kind in {"date/time", "boolean", "categorical"}:
        return kind
    normalized = _normalized_name(name).replace("_", " ")
    if any(term in normalized for term in (
        "percent", "percentage", "rate", "ratio", "growth",
    )):
        return "rate measure"
    for role, terms in _FINANCIAL_TERMS.items():
        if any(term in normalized for term in terms):
            return f"financial {role}"
    return "numeric measure"


def profile_dataset(dataframe):
    """Describe a DataFrame without modifying its values or dropping records."""
    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError("Expected a pandas DataFrame.")

    row_count, column_count = dataframe.shape
    duplicate_rows = int(dataframe.duplicated().sum()) if column_count else 0
    columns = []
    measures = []
    dimensions = []
    date_columns = []
    warnings = []

    if row_count == 0:
        warnings.append("The dataset contains no data rows.")
    if column_count == 0:
        warnings.append("The dataset contains no columns.")
    if dataframe.columns.duplicated().any():
        warnings.append("Duplicate column names are present; positions distinguish them.")
    if duplicate_rows:
        warnings.append(f"{duplicate_rows} duplicate row(s) were found; none were removed.")

    for position in range(column_count):
        name = str(dataframe.columns[position])
        series = dataframe.iloc[:, position]
        missing = int(series.isna().sum())
        distinct = int(series.nunique(dropna=True))
        numeric = numeric_values(series)
        numeric_ratio = numeric.notna().sum() / max(1, series.notna().sum())
        parsed_dates = (
            _parse_datetime(series)
            if not pd.api.types.is_numeric_dtype(series) and numeric_ratio < 0.8
            else None
        )

        if pd.api.types.is_bool_dtype(series):
            kind = "boolean"
        elif parsed_dates is not None:
            kind = "date/time"
            date_columns.append(name)
        elif pd.api.types.is_numeric_dtype(series) or (
            series.notna().any() and numeric_ratio >= 0.8
        ):
            kind = "numeric"
        else:
            kind = "categorical"

        if kind == "date/time" and parsed_dates is not None:
            unparseable_values = int(
                (series.notna() & parsed_dates.isna()).sum()
            )
        elif kind == "numeric":
            unparseable_values = int(
                (series.notna() & numeric.isna()).sum()
            )
        else:
            unparseable_values = 0

        identifier = kind != "date/time" and _is_identifier(name, series, numeric)
        role = _column_role(name, kind, identifier)
        values = series.dropna().drop_duplicates().head(5).tolist()
        values = [
            value.isoformat() if isinstance(value, (date, datetime, pd.Timestamp))
            else str(value) if isinstance(value, (np.generic,))
            else value
            for value in values
        ]
        column_profile = {
            "column": name,
            "position": position,
            "dtype": str(series.dtype),
            "kind": kind,
            "role": role,
            "identifier_like": identifier,
            "distinct_values": distinct,
            "missing_values": missing,
            "missing_percent": round(missing / row_count * 100, 2) if row_count else 0.0,
            "unparseable_values": unparseable_values,
            "representative_values": values,
        }
        columns.append(column_profile)
        if role == "identifier":
            continue
        if kind == "numeric":
            measures.append(column_profile)
        elif kind in {"categorical", "date/time", "boolean"}:
            dimensions.append(column_profile)

        if missing:
            warnings.append(f"{name}: {missing} missing value(s) ({column_profile['missing_percent']}%).")
        if series.notna().any() and kind == "numeric" and numeric_ratio < 1:
            warnings.append(
                f"{name}: values are mixed or non-numeric; numeric analysis uses only parseable values."
            )
        if unparseable_values and kind == "date/time":
            warnings.append(
                f"{name}: {unparseable_values} non-missing value(s) could not be parsed as dates."
            )
        elif series.notna().any() and (
            pd.api.types.is_object_dtype(series)
            or pd.api.types.is_string_dtype(series)
        ):
            value_types = series.dropna().map(type).nunique()
            if value_types > 1:
                warnings.append(f"{name}: mixed underlying value types were detected.")

    return {
        "row_count": row_count,
        "column_count": column_count,
        "duplicate_rows": duplicate_rows,
        "missing_cells": int(dataframe.isna().sum().sum()),
        "columns": columns,
        "numeric_columns": [column["column"] for column in measures],
        "categorical_columns": [
            column["column"] for column in columns if column["kind"] == "categorical"
        ],
        "date_columns": date_columns,
        "boolean_columns": [
            column["column"] for column in columns if column["kind"] == "boolean"
        ],
        "identifier_columns": [
            column["column"] for column in columns if column["identifier_like"]
        ],
        "candidate_dimensions": [column["column"] for column in dimensions],
        "candidate_measures": [column["column"] for column in measures],
        "warnings": list(dict.fromkeys(warnings)),
    }


def _financial_label(name, role, statistic):
    if statistic == "sum" and role.startswith("financial "):
        label = role.removeprefix("financial ").removesuffix(" measure").title()
        return f"Total {label}"
    if statistic == "mean" and role == "rate measure":
        return f"Average {name}"
    return f"{statistic.title()} {name}"


def generate_dynamic_kpis(dataframe, profile=None):
    """Generate traceable metrics using only columns suitable for measures."""
    profile = profile or profile_dataset(dataframe)
    kpis = []
    grouped_summaries = []

    for item in profile["columns"]:
        if item["kind"] != "numeric" or item["identifier_like"]:
            continue
        position = item["position"]
        values = numeric_values(dataframe.iloc[:, position])
        valid = values.dropna()
        role = item["role"]
        missing_count = int(values.isna().sum())
        missing_percent = (
            missing_count / len(dataframe) * 100 if len(dataframe) else 0.0
        )
        for label, value, calculation in [
            ("Valid values", int(valid.size), "count"),
            ("Missing values", missing_count, "missing_count"),
            ("Missing values (%)", round(missing_percent, 2), "missing_percent"),
        ]:
            kpis.append({
                "label": f"{label}: {item['column']}",
                "value": value,
                "source_columns": [item["column"]],
                "column_positions": [position],
                "calculation": calculation,
                "valid_values": int(valid.size),
                "missing_values": missing_count,
                "interpretation": "Column-level data-quality metric.",
            })
        if valid.empty:
            continue
        stats = [
            (_financial_label(item["column"], role, "sum"), float(valid.sum()), "sum"),
            (_financial_label(item["column"], role, "mean"), float(valid.mean()), "mean"),
            (f"Median {item['column']}", float(valid.median()), "median"),
            (f"Minimum {item['column']}", float(valid.min()), "min"),
            (f"Maximum {item['column']}", float(valid.max()), "max"),
        ]
        for label, value, calculation in stats:
            if calculation == "sum" and role == "rate measure":
                continue
            kpis.append({
                "label": label,
                "value": value,
                "source_columns": [item["column"]],
                "column_positions": [position],
                "calculation": calculation,
                "valid_values": int(valid.size),
                "missing_values": int(values.isna().sum()),
                "interpretation": (
                    "Column meaning inferred from its name."
                    if role.startswith("financial ")
                    else "Descriptive statistic; not assigned a financial meaning."
                ),
            })

        q1, q3 = valid.quantile([0.25, 0.75])
        lower, upper = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
        outliers = int(((valid < lower) | (valid > upper)).sum())
        grouped_summaries.append({
            "column": item["column"],
            "position": position,
            "distribution": valid.describe().to_dict(),
            "outlier_count_iqr": outliers,
            "outlier_method": "Values outside 1.5×IQR fences",
        })

    for item in profile["columns"]:
        if item["kind"] not in {"categorical", "boolean"} or item["identifier_like"]:
            continue
        series = dataframe.iloc[:, item["position"]]
        counts = series.value_counts(dropna=True).head(10)
        grouped_summaries.append({
            "column": item["column"],
            "position": item["position"],
            "distinct_values": item["distinct_values"],
            "top_categories": [
                {"category": str(category), "count": int(count)}
                for category, count in counts.items()
            ],
        })

    return {
        "kpis": kpis,
        "distributions": grouped_summaries,
        "financial_columns": {
            role: [
                item["column"]
                for item in profile["columns"]
                if item["role"] == f"financial {role}"
                and not item["identifier_like"]
            ]
            for role in _FINANCIAL_TERMS
        },
        "date_summaries": _date_summaries(dataframe, profile),
        "period_summaries": _period_summaries(dataframe, profile),
        "grouped_summaries": _grouped_summaries(dataframe, profile),
    }


def _date_summaries(dataframe, profile):
    summaries = []
    for item in profile["columns"]:
        if item["kind"] != "date/time":
            continue
        parsed = _parse_datetime(dataframe.iloc[:, item["position"]]).dropna()
        if parsed.empty:
            continue
        summaries.append({
            "column": item["column"],
            "position": item["position"],
            "minimum": parsed.min().isoformat(),
            "maximum": parsed.max().isoformat(),
            "valid_dates": int(parsed.size),
            "records_over_time": parsed.dt.to_period("M").value_counts().sort_index().astype(int).to_dict(),
        })
    return summaries


def _period_summaries(dataframe, profile):
    summaries = []
    measures = [
        item for item in profile["columns"]
        if item["kind"] == "numeric" and not item["identifier_like"]
    ]
    for date_item in profile["columns"]:
        if date_item["kind"] != "date/time":
            continue
        dates = _parse_datetime(dataframe.iloc[:, date_item["position"]])
        periods = dates.dt.to_period("M").astype("string")
        for measure in measures:
            values = numeric_values(dataframe.iloc[:, measure["position"]])
            grouped = pd.DataFrame({
                "period": periods,
                measure["column"]: values,
            }).dropna().groupby("period")[measure["column"]].agg(
                ["count", "sum", "mean"]
            ).reset_index()
            if len(grouped) < 2:
                continue
            summaries.append({
                "date_column": date_item["column"],
                "measure": measure["column"],
                "source_columns": [date_item["column"], measure["column"]],
                "period": "month",
                "calculation": "grouped count, sum, and mean",
                "values": grouped.to_dict(orient="records"),
            })
    return summaries


def _grouped_summaries(dataframe, profile):
    results = []
    dimensions = [
        item for item in profile["columns"]
        if item["kind"] in {"categorical", "boolean"}
        and not item["identifier_like"]
        and 1 < item["distinct_values"] <= 50
    ]
    measures = [
        item for item in profile["columns"]
        if item["kind"] == "numeric" and not item["identifier_like"]
    ]
    for dimension in dimensions:
        for measure in measures:
            values = numeric_values(dataframe.iloc[:, measure["position"]])
            grouped = pd.DataFrame({
                dimension["column"]: dataframe.iloc[:, dimension["position"]],
                measure["column"]: values,
            }).dropna().groupby(dimension["column"], dropna=False)[
                measure["column"]
            ].agg(
                ["count", "sum", "mean"]
            ).reset_index()
            results.append({
                "dimension": dimension["column"],
                "measure": measure["column"],
                "source_columns": [dimension["column"], measure["column"]],
                "calculation": "grouped count, sum, and mean",
                "values": grouped.head(50).to_dict(orient="records"),
            })
    return results
