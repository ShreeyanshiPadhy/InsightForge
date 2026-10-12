import pandas as pd
import json
from llm import generate_financial_summary
from financial_context import create_financial_context

DATA_FILE="../outputs/risk_analysis.csv"

try:
    df=pd.read_csv(DATA_FILE)
    context=create_financial_context(df)
    financial_data=json.dumps(context,indent=2)
    result=generate_financial_summary(financial_data)
    print("\nVALIDATED FINANCIAL CONTEXT\n")
    print(financial_data)
    print("\nAI-GENERATED FINANCIAL SUMMARY\n")
    print(result)
except FileNotFoundError:
    print(f"\nERROR: File not found: {DATA_FILE}")
except Exception as e:
    print(f"\nERROR: {e}")