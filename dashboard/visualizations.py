import pandas as pd
import plotly.express as px

def risk_category_chart(df):
    risk_counts=df["Risk_Category"].value_counts().reset_index()
    risk_counts.columns=["Risk_Category","Account_Count"]
    fig=px.bar(
        risk_counts,
        x="Risk_Category",
        y="Account_Count",
        title="Risk Category Distribution",
        labels={"Risk_Category":"Risk Category","Account_Count":"Number of Accounts"}
    )
    return fig

def risk_exposure_chart(df):
    exposure=df.groupby("Risk_Category")["Outstanding_Amount"].sum().reset_index()
    fig=px.bar(
        exposure,
        x="Risk_Category",
        y="Outstanding_Amount",
        title="Outstanding Exposure by Risk Category",
        labels={"Risk_Category":"Risk Category","Outstanding_Amount":"Outstanding Amount"}
    )
    return fig

def top_exposure_chart(df,n=10):
    top_accounts=df.sort_values(
        by="Outstanding_Amount",
        ascending=False
    ).head(n)
    fig=px.bar(
        top_accounts,
        x="Customer_Name",
        y="Outstanding_Amount",
        title=f"Top {n} Accounts by Outstanding Amount",
        labels={"Customer_Name":"Customer","Outstanding_Amount":"Outstanding Amount"}
    )
    return fig

def ageing_distribution_chart(df):
    fig=px.histogram(
        df,
        x="Ageing_Days",
        nbins=10,
        title="Ageing Distribution",
        labels={"Ageing_Days":"Ageing Days","count":"Number of Accounts"}
    )
    return fig

def risk_score_chart(df):
    score_counts=df["Risk_Score"].value_counts().sort_index().reset_index()
    score_counts.columns=["Risk_Score","Account_Count"]
    fig=px.bar(
        score_counts,
        x="Risk_Score",
        y="Account_Count",
        title="Risk Score Distribution",
        labels={"Risk_Score":"Risk Score","Account_Count":"Number of Accounts"}
    )
    return fig

def regional_exposure_chart(df):
    regional_data=df.groupby("Region")["Outstanding_Amount"].sum().reset_index()
    fig=px.bar(
        regional_data,
        x="Region",
        y="Outstanding_Amount",
        title="Outstanding Exposure by Region",
        labels={"Region":"Region","Outstanding_Amount":"Outstanding Amount"}
    )
    return fig

def regional_risk_chart(df):
    regional_risk=df.groupby(
        ["Region","Risk_Category"]
    ).size().reset_index(name="Account_Count")
    fig=px.bar(
        regional_risk,
        x="Region",
        y="Account_Count",
        color="Risk_Category",
        barmode="group",
        title="Risk Distribution by Region",
        labels={"Region":"Region","Account_Count":"Number of Accounts","Risk_Category":"Risk Category"}
    )
    return fig