import os
from dotenv import load_dotenv
from google import genai
import time

load_dotenv()

if __package__:
    from .prompts import DATASET_QA_PROMPT, DATASET_SUMMARY_PROMPT
else:
    from prompts import DATASET_QA_PROMPT, DATASET_SUMMARY_PROMPT

def get_client():
    api_key=os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set.")
    return genai.Client(api_key=api_key)

def generate_insight(financial_data,prompt):
    client=get_client()
    for attempt in range(3):
        try:
            response=client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"{prompt}\n\nValidated Financial Data:\n{financial_data}"
            )
            return response.text
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                if attempt<2:
                    time.sleep(2**attempt)
                else:
                    return "Gemini AI is temporarily unavailable due to high demand. Please try again in a few minutes."
            else:
                raise

from datetime import date

def generate_financial_summary(financial_data):
    report_date=date.today().strftime("%d-%m-%Y")
    prompt=f"""You are a financial intelligence assistant for an Indian financial analysis system.
Prepare a professional financial portfolio analysis report.

Report Date: {report_date}

Analyze only the validated financial context provided.
Use Indian Rupee (₹) for all monetary values.
Do not convert ₹ to dollars or any other currency.
Do not invent or estimate financial values.
Do not perform new financial calculations unless directly supported by the supplied values.
Clearly distinguish observations from assumptions.

Include:
1. Executive Summary
2. Portfolio Overview
3. Risk Patterns
4. Ageing Patterns
5. Exposure Concentrations
6. Regional Exposure
7. Conclusion

Use the Report Date provided above exactly.
Do not replace it with [Current Date] or another date.

Validated Financial Data:
"""
    return generate_insight(financial_data,prompt)

def answer_financial_question(question,financial_data):
    client=get_client()
    prompt=f"""You are InsightForge, a financial intelligence assistant for an Indian financial analysis system.
Answer the user's question using only the validated financial data provided.
Use Indian Rupee (₹) for monetary values.
Do not invent financial figures or accounts.
Do not change validated values.
If the answer cannot be determined from the provided data, clearly say so.
Keep the answer concise and professional.

User Question:
{question}

Validated Financial Data:
{financial_data}"""
    response=client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text


def generate_dataset_summary(dataset_data):
    """Explain dataset-driven analysis without imposing debtor assumptions."""
    return generate_insight(dataset_data, DATASET_SUMMARY_PROMPT)


def answer_dataset_question(question, dataset_data):
    """Answer a question using a dataset-neutral context and prompt."""
    prompt = DATASET_QA_PROMPT.format(question=question)
    return generate_insight(dataset_data, prompt)