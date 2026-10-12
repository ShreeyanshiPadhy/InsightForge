import pandas as pd
import json
from llm import answer_financial_question
from financial_context import create_financial_context

DATA_FILE="../outputs/risk_analysis.csv"

try:
    df=pd.read_csv(DATA_FILE)
    context=create_financial_context(df)
    financial_data=json.dumps(context,indent=2)

    question=input("\nAsk InsightForge a financial question: ")

    answer=answer_financial_question(question,financial_data)

    print("\nINSIGHTFORGE AI ANSWER\n")
    print(answer)
except FileNotFoundError:
    print(f"\nERROR: File not found: {DATA_FILE}")
except Exception as e:
    print(f"\nERROR: {e}")