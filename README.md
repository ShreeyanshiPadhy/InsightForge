# InsightForge

## Hybrid Financial Intelligence System

InsightForge is a hybrid financial intelligence system designed to analyze financial receivables and debtor information using deterministic data processing and AI-based interpretation.

The system combines Python-based financial calculations with the Google Gemini Large Language Model to provide reliable financial analysis, risk identification, anomaly detection, interactive visualizations and natural-language financial insights.

## Problem Statement

Large financial spreadsheets can contain a large number of records and multiple financial attributes. Manually analyzing these datasets can be time-consuming and may make it difficult to identify important risk patterns, ageing issues and exposure concentrations.

General-purpose AI systems may also struggle with large datasets and financial calculations.

InsightForge addresses this problem by separating numerical processing from AI interpretation.

Python is used for reliable data processing, financial calculations, validation and risk analysis, while Gemini is used to interpret validated results and generate natural-language insights.

## Objectives

- Process financial debtor data efficiently
- Clean and validate financial records
- Calculate financial KPIs
- Identify high-risk accounts
- Detect unusual exposure and ageing patterns
- Analyze regional exposure
- Generate financial visualizations
- Generate AI-based financial insights
- Support natural-language financial questions
- Provide an interactive Streamlit dashboard
- Maintain separation between deterministic calculations and AI interpretation

## System Architecture

```text
Financial Dataset
       |
       v
Data Cleaning & Validation
       |
       v
Financial Calculations
       |
       v
Validated Financial Data
       |
       +----------------------+
       |                      |
       v                      v
Risk & Anomaly Analysis    Financial Context
                              |
                              v
                         Gemini AI
                              |
                    +---------+---------+
                    |                   |
                    v                   v
              AI Insights          Q&A System
                    |                   |
                    +---------+---------+
                              |
                              v
                     Streamlit Dashboard
Technologies Used
Python
Pandas
NumPy
Streamlit
Plotly
Google Gemini API
google-genai
python-dotenv
JSON
Git/GitHub
Dataset

The project uses a debtor/receivables dataset containing account-level financial information.

The dataset includes fields such as:

Account ID
Customer Name
Outstanding Amount
Ageing Days
Account Status
Region

The current development version uses a sample debtor dataset for testing and demonstration.

Data Processing

The financial analytics layer processes the dataset before the information is passed to the AI layer.

The processing includes:

Data loading
Data type validation
Missing value handling
Duplicate handling
Financial calculations
KPI generation
Ageing analysis
Regional analysis
Data validation
Structured output generation

The validated financial results are stored in structured CSV and JSON outputs.

Risk Detection

InsightForge uses deterministic rules to calculate risk indicators.

Risk is based on two primary components:

Ageing Score
Exposure Score
Ageing Score
Ageing Days	Score
90 or more	3
60-89	2
30-59	1
Below 30	0
Exposure Score
Outstanding Amount	Score
₹5,00,000 or more	3
₹3,00,000-₹4,99,999	2
₹1,00,000-₹2,99,999	1
Below ₹1,00,000	0

The total risk score is calculated as:

Risk Score = Ageing Score + Exposure Score
Risk Categories
Risk Score	Risk Category
5 or more	High
3-4	Medium
Below 3	Low

The risk classification is performed using Python before the data is provided to the AI layer.

Anomaly Detection

InsightForge also identifies unusual financial records using percentile-based thresholds.

The anomaly detection process examines:

Outstanding amount
Ageing days

Records that exceed the calculated thresholds receive anomaly indicators.

The anomaly score is based on the number of unusual conditions detected.

Anomaly Score 0 → Normal
Anomaly Score 1 → Medium
Anomaly Score 2 → High
Financial Context

Before sending information to Gemini, InsightForge creates a structured financial context.

The context includes:

Total number of accounts
Total outstanding exposure
High-risk account count
Medium-risk account count
Low-risk account count
Overdue account count
90+ day ageing account count
High-risk exposure
Medium-risk exposure
Low-risk exposure
Regional exposure
Top exposure accounts
Account-level validated information

This structured approach reduces the possibility of the AI inventing financial values.

AI Layer

Google Gemini is used as the natural-language intelligence layer of InsightForge.

The AI layer provides:

Financial portfolio summaries
Risk explanations
Exposure observations
Ageing observations
Regional observations
Natural-language question answering

The AI does not replace the deterministic financial calculation layer.

Instead, validated financial results are generated by Python and then provided to Gemini for interpretation.

Prompt Design

The prompts instruct the AI to:

Use only the supplied validated financial information
Preserve the supplied financial values
Use Indian Rupee (₹)
Avoid converting values into other currencies
Avoid inventing financial figures
Avoid unsupported assumptions
Clearly distinguish observations from assumptions
Provide professional financial explanations

This design helps maintain consistency between the calculated results and the generated AI report.

AI-Generated Financial Insights

InsightForge can generate a professional financial portfolio analysis report containing sections such as:

Executive Summary
Portfolio Overview
Risk Patterns
Ageing Patterns
Exposure Concentrations
Regional Exposure
Conclusion

The report is generated using validated financial context.

The reporting date is generated by Python and passed to the AI rather than being generated independently by the language model.

Natural-Language Q&A

Users can ask financial questions directly through the Streamlit dashboard.

Examples include:

Which account has the highest outstanding amount?
Which region has the highest outstanding exposure?
How many high-risk accounts are there?
What is the total high-risk exposure?
Which accounts have ageing above 90 days?

The questions are answered using the validated financial context.

If the required information is unavailable, the AI is instructed to state that it is unavailable instead of inventing an answer.

Dashboard

The Streamlit dashboard provides an interactive interface for financial analysis.

Dashboard Features
Total account count
Total outstanding amount
High-risk account count
Medium-risk account count
Risk distribution chart
Risk exposure chart
Risk score chart
Ageing distribution chart
Top exposure accounts chart
Regional exposure chart
Regional risk chart
High-risk account table
Account-level data table
AI-generated financial insights
Natural-language Q&A
Visualizations

Plotly is used to create interactive charts.

The dashboard includes visualizations for:

Risk Analysis
Risk category distribution
Risk exposure
Risk score distribution
Ageing distribution
Exposure Analysis
Top exposure accounts
Regional exposure
Regional risk

These visualizations allow users to identify important financial patterns quickly.

Sample Portfolio Results

For the current sample dataset, the validated analysis produces:

Total accounts: 20
Total outstanding: ₹7,640,000
High-risk accounts: 7
Medium-risk accounts: 5
Low-risk accounts: 8
High-risk exposure: ₹5,220,000
Medium-risk exposure: ₹1,570,000
Low-risk exposure: ₹850,000
Accounts with 90+ days ageing: 7
Overdue accounts: 7
Regional Exposure
West: ₹2,560,000
South: ₹2,065,000
East: ₹1,940,000
North: ₹1,075,000
Top Exposure Accounts

The current sample dataset identifies the following five accounts as the highest exposure accounts:

Account ID	Customer Name	Outstanding Amount	Ageing Days	Risk Category
A020	Global Tech	₹1,100,000	180	High
A009	Vertex Systems	₹920,000	150	High
A001	Alpha Traders	₹850,000	120	High
A015	Galaxy Exports	₹720,000	110	High
A005	Epsilon Corp	₹650,000	105	High
Hybrid AI Approach

The main design principle of InsightForge is the separation of computation and interpretation.

Python Layer

Python is responsible for:

Data loading
Data cleaning
Data validation
Financial calculations
KPI generation
Risk scoring
Anomaly detection
Regional analysis
Ageing analysis
Structured financial context
AI Layer

Gemini is responsible for:

Natural-language interpretation
Financial summaries
Risk explanations
Financial observations
Natural-language question answering

This architecture allows the system to use deterministic processing for financial calculations while using AI for flexible human-readable explanations.

Project Structure
InsightForge/
│
├── .env
├── .gitignore
├── requirements.txt
├── README.md
│
├── data/
│   └── dummy_debtors.csv
│
├── ai/
│   ├── __init__.py
│   ├── risk_detection.py
│   ├── anomaly_detection.py
│   ├── llm.py
│   ├── prompts.py
│   ├── financial_context.py
│   ├── test_llm.py
│   └── test_qa.py
│
├── dashboard/
│   ├── __init__.py
│   ├── app.py
│   └── visualizations.py
│
└── outputs/
    ├── risk_analysis.csv
    ├── risk_analysis.json
    ├── anomaly_analysis.csv
    └── anomaly_analysis.json
Installation

Clone or download the InsightForge project.

Install the required Python packages:

pip install -r requirements.txt
Gemini API Configuration

Create a .env file in the main InsightForge folder.

Add:

GEMINI_API_KEY=your_api_key_here

The API key should not be included directly in Python source code.

The .env file should not be committed to GitHub.

Running the Application

Open a terminal in the main InsightForge folder.

Run:

streamlit run dashboard/app.py

The Streamlit application will open in the browser.

Testing the AI Layer

The financial summary can be tested using:

cd ai
python test_llm.py

Natural-language Q&A can be tested using:

python test_qa.py
Testing the Dashboard

The dashboard should be checked for:

Successful CSV loading
Correct KPI values
Correct risk categories
Correct exposure values
Correct charts
Correct high-risk account table
Successful AI-generated insights
Successful natural-language Q&A
Graceful handling of temporary Gemini API errors
Error Handling

The AI layer includes handling for temporary Gemini service errors.

If the Gemini service returns a temporary 503 UNAVAILABLE error, InsightForge retries the request and displays a user-friendly message if the service remains unavailable.

This prevents a temporary AI service issue from crashing the dashboard.

Security

The Gemini API key is stored in the .env file.

The .gitignore file prevents the .env file from being committed to Git.

Example .gitignore:

.env
__pycache__/
*.pyc

API keys should never be shared publicly or uploaded to GitHub.

Testing Results
Test Case	Expected Result	Status
Load financial data	Dataset loads successfully	Pass
Data validation	Required financial fields are validated	Pass
Risk classification	High/Medium/Low categories generated	Pass
Risk scoring	Risk scores generated correctly	Pass
Anomaly detection	Anomaly indicators generated	Pass
Risk charts	Charts displayed correctly	Pass
Exposure charts	Exposure visualizations displayed	Pass
Regional analysis	Regional exposure displayed	Pass
Dashboard loading	Streamlit dashboard opens	Pass
AI summary	Gemini generates financial summary	Pass
Currency handling	Monetary values displayed in ₹	Pass
Natural-language Q&A	Questions answered using validated context	Pass
API error handling	Temporary API errors handled gracefully	Pass
Account-level analysis	Account information displayed	Pass
Student Contributions
Student 1 — Shreeyanshi

Contribution:

Dataset ingestion
Data cleaning and preprocessing
Missing value handling
Duplicate handling
Financial calculations
KPI generation
Regional analysis
Ageing analysis
Data validation
Structured JSON output
Calculation accuracy testing
Student 2 — Abha Kiran Dongre

Contribution:

Risk indicators
High-risk account identification
Anomaly detection
Gemini API integration
Prompt engineering
Validated financial context integration
AI-generated financial insights
Natural-language Q&A
Streamlit dashboard
Plotly visualizations
AI and application-layer integration
AI error handling
Testing of AI outputs against validated financial data
Conclusion

InsightForge demonstrates a hybrid approach to financial intelligence by combining deterministic data processing with generative AI.

The system first processes and validates financial information using Python. Risk indicators, financial metrics, ageing analysis and exposure analysis are calculated before the information is provided to the AI layer.

Gemini then interprets these validated results and generates natural-language financial insights and answers to user questions.

The Streamlit dashboard brings the complete workflow together by providing interactive visualizations, financial risk information, AI-generated reports and natural-language interaction in a single application.

Future Enhancements

Potential future improvements include:

Support for larger Excel workbooks
Automated advanced data cleaning
More financial KPIs
Historical trend analysis
More advanced anomaly detection
Automated financial alerts
PDF financial report generation
User authentication
Role-based access
Database integration
More advanced natural-language query processing
Deployment to a cloud platform
Integration with live financial systems
Authors
Student 1

Shreeyanshi

Financial Analytics & Data Engineering

Student 2

Abha Kiran Dongre

AI, Risk & Application Layer

InsightForge — Hybrid Financial Intelligence System