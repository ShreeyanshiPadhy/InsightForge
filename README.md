# InsightForge

### AI-Powered Financial Intelligence and Analysis System

InsightForge is a hybrid financial intelligence platform that transforms large financial datasets into **reliable financial analysis and actionable insights**.

It combines **deterministic data processing and financial computation** with **AI-powered interpretation**, ensuring that financial calculations remain accurate and verifiable while allowing users to interact with the results naturally.

> **Compute deterministically. Interpret intelligently.**

---

## 🎯 Problem

Large financial spreadsheets can be difficult and time-consuming to analyse manually. Extracting meaningful patterns, identifying risks, and generating useful insights from raw financial data often requires significant effort.

General-purpose AI systems can assist with interpretation, but relying on them directly for financial calculations may produce results that are difficult to verify.

InsightForge addresses this by separating **financial computation from AI interpretation**.

---

## 💡 Solution

InsightForge follows a hybrid approach:

**Financial Data → Processing → Validation → Analysis → Structured Results → AI Interpretation → Insights**

### Financial Analytics

The deterministic analytics layer handles:

- Data ingestion and preprocessing
- Data cleaning
- Financial KPI calculation
- Debtor ageing analysis
- Regional exposure analysis
- Financial validation and reconciliation
- Structured JSON output generation

### AI Intelligence

The AI layer handles:

- Risk analysis
- Anomaly detection
- Natural-language financial insights
- Financial summaries
- Natural-language queries
- AI-assisted interpretation of validated results

This approach allows the AI to work with **validated financial results instead of performing critical calculations itself**.

---

## 🏗️ Architecture

```text
              Financial Dataset
                     │
                     ▼
              Data Ingestion
                     │
                     ▼
            Data Cleaning
                     │
                     ▼
          Validation & Checks
                     │
                     ▼
         Financial Analytics
          ┌──────────┼──────────┐
          ▼          ▼          ▼
        KPIs      Ageing     Regional
                  Analysis    Analysis
          └──────────┼──────────┘
                     ▼
              Structured JSON
                     │
                     ▼
                 AI Layer
          ┌──────────┼──────────┐
          ▼          ▼          ▼
        Risk      Insights      Q&A
       Analysis
                     │
                     ▼
             Streamlit Dashboard
```

---

## 📊 Key Features

- **Automated Financial Analysis**
- **KPI Generation**
- **Debtor Ageing Analysis**
- **Regional Exposure Analysis**
- **Financial Data Validation**
- **Risk & Anomaly Detection**
- **AI-Generated Financial Insights**
- **Natural-Language Financial Q&A**
- **Interactive Dashboard**
- **Structured JSON Data Exchange**

---

## 🛠️ Tech Stack

| Area | Technology |
|---|---|
| Programming | Python |
| Data Processing | Pandas, NumPy |
| Data Input | Excel |
| Data Exchange | JSON |
| AI | Google Gemini API / LLM |
| Dashboard | Streamlit |
| Visualization | Plotly, Matplotlib |
| Testing | Pytest |
| Version Control | Git, GitHub |

---

## 📁 Project Structure

```text
InsightForge/
│
├── backend/
│   ├── data/
│   ├── outputs/
│   ├── services/
│   │   ├── data_loader.py
│   │   ├── data_cleaning.py
│   │   ├── validation.py
│   │   ├── financial_analysis.py
│   │   ├── ageing_analysis.py
│   │   ├── regional_analysis.py
│   │   └── json_export.py
│   │
│   └── main.py
│
├── frontend/
│   └── components/
│
├── ai/
│   └── ...
│
├── tests/
│   └── test_calculations.py
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🚀 Getting Started

### Clone the repository

```bash
git clone <repository-url>
cd InsightForge
```

### Create a virtual environment

```bash
python -m venv .venv
```

### Activate the environment

**Windows:**

```powershell
.venv\Scripts\activate
```

**Linux / macOS:**

```bash
source .venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Add the dataset

Place the financial dataset inside:

```text
backend/data/
```

### Run the backend

```bash
python -m backend.main
```

The processed financial results are exported as a structured JSON file for use by the AI layer.

---

## 👥 Team

### Shreeyanshi Padhy
**Financial Analytics & Data Engineering**

- Data processing and cleaning
- Financial analysis
- KPI calculation
- Ageing and regional analysis
- Data validation
- JSON output pipeline

### Abha Kiran Dongre
**AI, Risk Analysis & Application Layer**

- Risk and anomaly detection
- Gemini API integration
- AI prompts and financial insights
- Natural-language Q&A
- Streamlit dashboard
- Financial visualizations

---

## 🌟 Core Principle

> **Compute deterministically. Interpret intelligently.**

InsightForge is built around the idea that **reliable financial computation and AI-powered interpretation should complement each other rather than replace one another.**
