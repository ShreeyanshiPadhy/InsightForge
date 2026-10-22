import pandas as pd

from dashboard.pdf_generator import generate_financial_report
from ai.risk_detection import DEFAULT_RISK_CONFIG, perform_risk_analysis


def test_financial_report_builds_with_risk_and_exposure_analysis():
    source = pd.DataFrame(
        {
            "Account_ID": ["A001", "A002", "A003"],
            "Customer_Name": ["Northwind", "Contoso", "Fabrikam"],
            "Region": ["North", "South", "North"],
            "Account_Status": ["Overdue", "Active", "Active"],
            "Outstanding_Amount": [950000, 120000, 350000],
            "Ageing_Days": [120, 15, 65],
        }
    )
    analyzed = perform_risk_analysis(source, config=DEFAULT_RISK_CONFIG)

    pdf_bytes = generate_financial_report(
        analyzed,
        summary_text="Portfolio risk summary",
        risk_config=DEFAULT_RISK_CONFIG,
    )

    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 5000
