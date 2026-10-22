import pandas as pd

from dashboard.dataset_analytics import (
    generate_dynamic_kpis,
    numeric_values,
    profile_dataset,
)


def test_profile_classifies_columns_and_preserves_source_values():
    dataframe = pd.DataFrame({
        "Customer ID": [1001, 1002, 1003],
        "Sales Amount": ["$1,200", "2,500", None],
        "Department": ["North", "South", "North"],
        "Transaction Date": ["2025-01-10", "2025-02-10", "2025-02-20"],
        "Active": [True, False, True],
        "Mixed Values": [1, "not numeric", 3],
    })
    original = dataframe.copy(deep=True)

    profile = profile_dataset(dataframe)
    analytics = generate_dynamic_kpis(dataframe, profile)
    labels = {metric["label"]: metric for metric in analytics["kpis"]}

    assert profile["row_count"] == 3
    assert profile["column_count"] == 6
    assert profile["identifier_columns"] == ["Customer ID"]
    assert profile["date_columns"] == ["Transaction Date"]
    assert profile["boolean_columns"] == ["Active"]
    assert "Sales Amount" in profile["candidate_measures"]
    assert "Customer ID" not in profile["candidate_measures"]
    assert labels["Total Revenue"]["value"] == 3700
    assert analytics["financial_columns"]["revenue"] == ["Sales Amount"]
    assert labels["Missing values: Sales Amount"]["value"] == 1
    assert analytics["period_summaries"][0]["source_columns"] == [
        "Transaction Date",
        "Sales Amount",
    ]
    assert dataframe.equals(original)
    assert "Mixed Values: mixed underlying value types" in " ".join(profile["warnings"])


def test_profile_handles_empty_and_duplicate_column_names():
    empty_profile = profile_dataset(pd.DataFrame())
    assert empty_profile["row_count"] == 0
    assert empty_profile["column_count"] == 0
    assert empty_profile["warnings"]

    dataframe = pd.DataFrame([[1, 2]], columns=["Measure", "Measure"])
    profile = profile_dataset(dataframe)
    assert profile["column_count"] == 2
    assert profile["columns"][0]["position"] == 0
    assert profile["columns"][1]["position"] == 1
    assert any("Duplicate column names" in warning for warning in profile["warnings"])


def test_profile_reports_unparseable_values_in_date_columns():
    dataframe = pd.DataFrame({
        "Transaction Date": [
            "2025-01-01", "2025-02-01", "2025-03-01",
            "2025-04-01", "not a date",
        ],
    })

    profile = profile_dataset(dataframe)

    assert profile["date_columns"] == ["Transaction Date"]
    assert profile["columns"][0]["unparseable_values"] == 1
    assert any("could not be parsed as dates" in warning for warning in profile["warnings"])


def test_numeric_conversion_is_a_derived_view_only():
    original = pd.Series(["1,200", "₹500", "(USD 125)", "unavailable"])
    converted = numeric_values(original)

    assert converted.tolist()[:3] == [1200, 500, -125]
    assert pd.isna(converted.iloc[3])
    assert original.tolist() == ["1,200", "₹500", "(USD 125)", "unavailable"]
