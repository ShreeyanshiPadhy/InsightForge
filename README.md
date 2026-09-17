# InsightForge

### AI-Powered Financial Intelligence and Analysis System

InsightForge is a hybrid financial intelligence platform designed to automate the analysis of large financial datasets and convert raw financial data into reliable, interpretable insights.

The system combines **deterministic financial computation using Python, Pandas, and NumPy** with **AI-powered interpretation using Large Language Models (LLMs)**.

> **Compute deterministically. Interpret intelligently.**

---

## 📌 Problem Statement

Large financial spreadsheets often contain hundreds or thousands of records and numerous financial attributes, making manual analysis time-consuming and error-prone.

While general-purpose AI tools can assist with interpretation, directly relying on an LLM for financial calculations can lead to unreliable or unverifiable results.

InsightForge addresses this problem through a **hybrid architecture**:

- Financial calculations are performed deterministically using Python.
- Data is cleaned and validated before analysis.
- Structured analytical results are generated in JSON format.
- An LLM uses the validated results to generate natural-language insights.
- A Streamlit-based interface presents the analysis interactively.

---

## 🎯 Objectives

- Automate financial data ingestion and preprocessing.
- Calculate important financial KPIs.
- Analyse debtor ageing and regional exposure.
- Validate financial calculations and ensure data consistency.
- Detect financial risks and anomalies.
- Generate natural-language financial insights using an LLM.
- Support natural-language financial queries.
- Provide interactive financial visualizations.
- Produce structured outputs that can be consumed by the AI layer.

---

## 🏗️ System Architecture

```text
                    Financial Dataset
                           │
                           ▼
                  ┌─────────────────┐
                  │  Data Ingestion  │
                  │     Pandas      │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Data Cleaning & │
                  │ Preprocessing   │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Data Validation │
                  │ & Reconciliation│
                  └────────┬────────┘
                           │
                           ▼
              ┌──────────────────────────┐
              │   Financial Analytics   │
              │                          │
              │ • KPIs                   │
              │ • Ageing Analysis        │
              │ • Regional Analysis      │
              │ • Trend Analysis         │
              └────────────┬─────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Structured JSON │
                  │     Output      │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │   AI / LLM      │
                  │ Interpretation  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Streamlit       │
                  │ Dashboard       │
                  └─────────────────┘
```

---

## 🔄 Hybrid Intelligence Approach

InsightForge separates **calculation** from **interpretation**.

### Deterministic Layer

The financial analytics layer uses:

- Python
- Pandas
- NumPy

This layer performs:

- Data loading
- Data cleaning
- Financial calculations
- KPI generation
- Ageing calculations
- Regional analysis
- Validation
- Financial reconciliation

This ensures that numerical results are generated through reproducible computations rather than LLM reasoning.

### AI Interpretation Layer

The AI layer is responsible for:

- Risk identification
- Anomaly detection
- Natural-language financial insights
- Financial summaries
- Natural-language Q&A
- AI-assisted interpretation of validated results

The AI layer receives structured and validated financial information instead of directly performing the core financial calculations.

---

## 📊 Current Implementation

The current financial analytics pipeline has been tested on the project's financial debtor dataset.

### Current Dataset Processing

- **Records processed:** 819
- **Columns:** 51
- **Duplicate records detected:** 0
- **Financial reconciliation:** Passed

The financial validation process verifies that the calculated outstanding amount reconciles with the total amount across the ageing buckets.

Example validation result:

```text
Outstanding Total : 6402.48
Ageing Total      : 6402.48
Difference        : 0.00
Consistency       : True
```

> **Note:** The original financial dataset is not included in the public repository because it may contain sensitive financial information.

---

## 📈 Financial Analytics

The backend currently provides the following analytical capabilities.

### Key Performance Indicators

- Total outstanding
- Number of accounts
- Average outstanding per account

### Ageing Analysis

The system analyses outstanding amounts across multiple ageing buckets:

```text
0-30
31-60
61-90
91-120
121-150
151-180
181-210
211-335
335-365
366-395
396-730
731-760
761-1028
1028+
```

### Regional Analysis

Outstanding exposure is grouped by region to identify areas with higher financial exposure.

### Validation

The validation layer currently performs:

- Missing-value count
- Duplicate-record detection
- Outstanding-vs-ageing reconciliation
- Financial consistency verification

---

## 📁 Project Structure

```text
InsightForge/
│
├── README.md
├── .gitignore
├── requirements.txt
│
├── backend/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── data/
│   │   └── <financial_dataset>.xlsx
│   │
│   ├── outputs/
│   │   └── financial_results.json
│   │
│   └── services/
│       ├── __init__.py
│       ├── data_loader.py
│       ├── data_cleaning.py
│       ├── validation.py
│       ├── financial_analysis.py
│       ├── ageing_analysis.py
│       ├── regional_analysis.py
│       └── json_export.py
│
├── frontend/
│   └── components/
│
├── tests/
│   └── test_calculations.py
│
└── ai/
    └── ...
```

The `frontend` and `ai` components are being developed alongside the financial analytics backend and will be integrated into the complete system in a subsequent phase.

---

## ⚙️ Technologies Used

| Component | Technology |
|---|---|
| Programming Language | Python |
| Data Processing | Pandas |
| Numerical Computation | NumPy |
| Data Input | Excel |
| Data Exchange | JSON |
| AI Layer | Google Gemini API / LLM |
| Dashboard | Streamlit |
| Visualization | Plotly / Matplotlib |
| Testing | Python Testing Framework |
| Version Control | Git & GitHub |

---

## 🚀 Running the Backend

### 1. Clone the Repository

```bash
git clone <repository-url>
cd InsightForge
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

### 3. Activate the Virtual Environment

#### Windows

```powershell
.venv\Scripts\activate
```

#### Linux / macOS

```bash
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Add the Dataset

Place the authorized financial Excel dataset inside:

```text
backend/data/
```

The dataset is intentionally excluded from GitHub because it may contain sensitive financial information.

### 6. Run the Financial Analytics Pipeline

From the project root:

```bash
python -m backend.main
```

The pipeline will:

1. Load the Excel dataset.
2. Clean the data.
3. Validate the dataset.
4. Calculate financial KPIs.
5. Perform ageing analysis.
6. Perform regional analysis.
7. Export the structured results.

---

## 📄 Output

The analytics pipeline generates a structured JSON output:

```text
backend/outputs/financial_results.json
```

Example structure:

```json
{
    "dataset": {
        "name": "Debtors May 26",
        "total_records": 819,
        "status": "validated"
    },
    "kpis": {
        "total_outstanding": 6402.48,
        "total_accounts": 819,
        "average_outstanding": 7.82
    },
    "ageing": {
        "0-30": 2594.19,
        "31-60": 1652.55,
        "61-90": 1243.69
    },
    "validation": {
        "duplicate_records": 0,
        "financial_consistency": true,
        "validated": true
    }
}
```

This JSON acts as the structured communication layer between the financial analytics backend and the AI layer.

---

## 🧪 Testing

The project includes tests for financial calculations.

Run the tests using:

```bash
python -m pytest
```

Testing focuses on verifying the correctness and consistency of financial calculations.

---

## 👥 Team Contributions

### Shreeyanshi Padhy — 24BDS0303

**Financial Analytics & Data Engineering**

- Dataset ingestion
- Data cleaning and preprocessing
- Financial KPI calculations
- Debtor ageing analysis
- Regional exposure analysis
- Financial validation and reconciliation
- Structured JSON output generation
- Calculation testing

### Abha Kiran Dongre — 24BDS0304

**AI, Risk Analysis & Application Layer**

- Risk indicators and risk scoring
- Anomaly detection
- Google Gemini API integration
- AI prompt design
- AI-generated financial insights
- Natural-language financial Q&A
- Streamlit dashboard
- Plotly financial visualizations
- AI/application-layer integration

---

## 🔮 Future Work

The next development phase will focus on integrating the independently developed modules into a unified application.

Planned improvements include:

- Integration of the financial analytics backend with the AI layer.
- Automated risk and anomaly analysis using validated financial results.
- Interactive Streamlit dashboard integration.
- Natural-language querying over financial data.
- Additional financial trend analysis.
- More comprehensive data-quality validation.
- Improved testing and error handling.
- End-to-end system testing.
- Deployment of the integrated application.

---

## 💡 Core Design Principle

```text
             COMPUTE DETERMINISTICALLY
                         ↓
                  VALIDATE RESULTS
                         ↓
              STRUCTURE THE OUTPUT
                         ↓
             INTERPRET INTELLIGENTLY
```

InsightForge is designed around the principle that **AI should interpret reliable financial computations rather than replace them**.

---

## 📌 Project Status

**Current Phase:** Review 2 — Core Implementation

The project currently has independently implemented financial analytics and AI/application modules. The financial analytics backend has a working pipeline using the actual project dataset, while the AI and application components are being developed as a separate module.

The modules will be integrated into a unified InsightForge application in the next development phase.

---

## 📜 License

This project is developed for academic purposes as part of the B.Tech Computer Science (Data Science) curriculum.
