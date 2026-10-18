import pytest
import pandas as pd
from backend.services.data_loader import load_dataset
from ai.risk_detection import perform_risk_analysis, create_risk_summary, DEFAULT_RISK_CONFIG
from ai.anomaly_detection import perform_anomaly_analysis, create_anomaly_summary

@pytest.fixture
def sample_dataframe():
    """Provides sample financial data for testing."""
    return pd.DataFrame({
        "Account_ID": ["ACC001", "ACC002", "ACC003", "ACC004"],
        "Customer_Name": ["Alpha Corp", "Beta LLC", "Gamma Inc", "Delta Co"],
        "Outstanding_Amount": [50000, 150000, 350000, 600000],
        "Ageing_Days": [15, 45, 75, 120],
        "Account_Status": ["Active", "Active", "Pending", "Overdue"],
        "Region": ["North", "South", "East", "West"]
    })

def test_risk_analysis_default_config(sample_dataframe):
    """Tests risk calculation using standard default thresholds."""
    df_res = perform_risk_analysis(sample_dataframe)
    summary = create_risk_summary(df_res)

    assert len(df_res) == 4
    assert "Risk_Category" in df_res.columns
    assert summary["total_accounts"] == 4
    assert summary["total_outstanding"] == 1150000.0

def test_risk_analysis_custom_config(sample_dataframe):
    """Tests risk scoring when dynamic user thresholds are provided."""
    custom_cfg = {
        "ageing_medium": 20,
        "ageing_high": 40,
        "ageing_critical": 60,
        "exposure_low": 50000,
        "exposure_medium": 100000,
        "exposure_high": 200000
    }
    df_res = perform_risk_analysis(sample_dataframe, config=custom_cfg)
    
    # Delta Co (600,000 exposure & 120 days) must be marked High Risk
    delta_row = df_res[df_res["Account_ID"] == "ACC004"].iloc[0]
    assert delta_row["Risk_Category"] == "High"
    assert delta_row["Risk_Score"] == 6

def test_anomaly_detection_fixed_thresholds(sample_dataframe):
    """Tests anomaly detection using fixed monetary & ageing limits."""
    df_res, amt_thresh, age_thresh = perform_anomaly_analysis(
        sample_dataframe,
        fixed_amount_threshold=500000,
        fixed_ageing_threshold=100
    )
    assert amt_thresh == 500000
    assert age_thresh == 100
    
    acc4 = df_res[df_res["Account_ID"] == "ACC004"].iloc[0]
    assert acc4["Anomaly_Category"] == "High"