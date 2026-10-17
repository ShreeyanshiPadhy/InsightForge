# InsightForge

**Hybrid Financial Intelligence System**

InsightForge analyzes financial receivables and debtor data using deterministic Python calculations and AI-assisted interpretation. It combines validated financial metrics, risk indicators, anomaly detection, interactive visualizations, and natural-language insights in a Streamlit dashboard.

> **Core principle:** Compute deterministically. Interpret intelligently.

## Problem and approach

Large financial spreadsheets can be difficult to review manually. InsightForge processes and validates financial data before passing structured results to Google Gemini for interpretation. Python remains responsible for financial calculations; the language model explains the validated results rather than acting as the source of financial figures.

## Key features

- Upload and process financial datasets.
- Detect and map common financial column names.
- Validate records and prepare normalized account-level data.
- Calculate financial KPIs and ageing metrics.
- Classify account risk using ageing and exposure indicators.
- Flag unusual exposure and ageing patterns.
- Analyze regional exposure and risk.
- Explore interactive charts and account-level tables.
- Generate AI-assisted financial summaries.
- Ask natural-language questions about the analyzed portfolio.
- Export structured analysis results as CSV and JSON.

## Architecture

```text
Financial Dataset
       |
       v
Upload, Header Detection & Column Mapping
       |
       v
Cleaning and Validation
       |
       v
Financial Metrics and Structured Data
       |
       +---------------------------+
       |                           |
       v                           v
Risk and Anomaly Analysis    Financial Context
                                   |
                                   v
                              Google Gemini
                                   |
                         +---------+---------+
                         |                   |
                         v                   v
                    AI Insights          Financial Q&A
                         |                   |
                         +---------+---------+
                                   |
                                   v
                          Streamlit Dashboard
```

## Technology stack

| Area            | Technology                         |
| --------------- | ---------------------------------- |
| Language        | Python                             |
| Data processing | Pandas, NumPy                      |
| Dashboard       | Streamlit                          |
| Visualization   | Plotly                             |
| AI              | Google Gemini API (`google-genai`) |
| Configuration   | `python-dotenv`                    |
| Data exchange   | CSV, JSON                          |
| Version control | Git, GitHub                        |

## Project structure

```text
InsightForge/
├── .env
├── .gitignore
├── requirements.txt
├── README.md
├── data/
│   └── dummy_debtors.csv
├── ai/
│   ├── __init__.py
│   ├── risk_detection.py
│   ├── anomaly_detection.py
│   ├── llm.py
│   ├── prompts.py
│   ├── financial_context.py
│   ├── test_llm.py
│   └── test_qa.py
├── dashboard/
│   ├── app.py
│   ├── upload_processor.py
│   └── visualizations.py
└── outputs/
    ├── risk_analysis.csv
    ├── risk_analysis.json
    ├── anomaly_analysis.csv
    └── anomaly_analysis.json
```

This tree reflects the current documented application structure. New modules should be added here when they are implemented.

## Getting started

### 1. Set up the environment

From the project root, create and activate a virtual environment if desired.

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux/macOS:**

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Gemini

Create a `.env` file in the project root:

```dotenv
GEMINI_API_KEY=your_api_key_here
```

Keep the real API key private. Do not commit `.env` to version control. A placeholder key is not a working credential.

### 4. Run the dashboard

Run this command from the project root:

```bash
streamlit run dashboard/app.py
```

The application should open in your browser. Upload a supported financial dataset and follow the header detection and column mapping prompts.

## Financial analysis

### Risk detection

The risk engine uses deterministic indicators based on account ageing and outstanding exposure. The current documented baseline is:

**Ageing score**

| Ageing days | Score |
| ----------- | ----: |
| 90 or more  |     3 |
| 60–89       |     2 |
| 30–59       |     1 |
| Below 30    |     0 |

**Exposure score**

| Outstanding amount  | Score |
| ------------------- | ----: |
| ₹5,00,000 or more   |     3 |
| ₹3,00,000–₹4,99,999 |     2 |
| ₹1,00,000–₹2,99,999 |     1 |
| Below ₹1,00,000     |     0 |

The documented total score is the sum of ageing and exposure scores:

`Risk Score = Ageing Score + Exposure Score`

| Total score | Category |
| ----------- | -------- |
| 5 or more   | High     |
| 3–4         | Medium   |
| Below 3     | Low      |

These are the thresholds described in the existing project documentation. Confirm them against the current implementation if the risk engine changes.

### Anomaly detection

The anomaly layer examines unusual outstanding amounts and ageing patterns. Records can receive anomaly indicators based on the configured thresholds. An anomaly is a signal for review, not proof of fraud or error.

### AI insights and financial Q&A

The application prepares structured financial context from calculated results before sending it to Gemini. Prompts are designed to preserve supplied values, use Indian Rupees (₹), avoid invented figures, and distinguish observations from assumptions. If a value is not available in the supplied context, the AI should say so.

AI service failures should be handled gracefully so that a temporary Gemini outage does not prevent users from accessing the deterministic analysis.

## Dashboard features

The documented dashboard includes:

- Account and outstanding-exposure KPIs.
- Risk category and risk score distributions.
- Ageing analysis.
- Top exposure accounts.
- Regional exposure and risk charts.
- High-risk and account-level tables.
- AI-generated financial insights.
- Natural-language financial Q&A.

The exact visible features depend on the current implementation and the dataset uploaded.

## Testing

Run the existing AI tests from the project root:

```bash
python ai/test_llm.py
python ai/test_qa.py
```

Check the dashboard manually for:

- Successful upload and header detection.
- Correct column mapping.
- Expected KPI, risk, ageing, and exposure results.
- Correct chart and table rendering.
- Successful AI insights and financial Q&A when the API is available.
- Graceful behavior when Gemini is temporarily unavailable.
- Correct CSV and JSON output.

These are test instructions, not a claim that every test has been run in every environment.

## Security

- Store the Gemini API key in `.env`.
- Ensure `.env` is listed in `.gitignore`.
- Never commit API keys or credentials.
- Treat uploaded financial data as potentially sensitive.

Example `.gitignore` entries:

```gitignore
.env
.venv/
__pycache__/
*.py[cod]
```

## Team contributions

### Shreeyanshi — Financial Analytics & Data Engineering

- Dataset ingestion and preprocessing
- Data cleaning and validation
- Financial calculations and KPI generation
- Ageing and regional analysis
- Structured output generation
- Calculation accuracy testing

### Abha Kiran Dongre — AI, Risk & Application Layer

- Risk indicators and high-risk account identification
- Anomaly detection
- Gemini API integration and prompt design
- Financial insights and natural-language Q&A
- Streamlit dashboard and Plotly visualizations
- AI/application integration and error handling
- Validation of AI outputs against calculated results

## Future enhancements

Potential next steps include configurable risk thresholds, expanded Excel workbook support, consolidated automated tests, PDF executive reports, downloadable exports, historical run logging, database integration, containerization, authentication, and cloud deployment. These should be marked as complete only after implementation and testing.

---

**InsightForge — Hybrid Financial Intelligence System**
