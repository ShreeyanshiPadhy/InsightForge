import pandas as pd

def create_financial_context(df):
    total_accounts=len(df)
    total_outstanding=df["Outstanding_Amount"].sum()
    high_risk=df[df["Risk_Category"]=="High"]
    medium_risk=df[df["Risk_Category"]=="Medium"]
    low_risk=df[df["Risk_Category"]=="Low"]
    overdue=df[df["Account_Status"].str.lower()=="overdue"]
    high_ageing=df[df["Ageing_Days"]>=90]
    regional_exposure=df.groupby("Region")["Outstanding_Amount"].sum().to_dict()
    top_accounts=df.nlargest(5,"Outstanding_Amount")[["Account_ID","Customer_Name","Outstanding_Amount","Ageing_Days","Risk_Category"]].to_dict(orient="records")
    account_details=df[["Account_ID","Customer_Name","Outstanding_Amount","Ageing_Days","Account_Status","Region","Risk_Score","Risk_Category"]].to_dict(orient="records")
    context={
        "portfolio_summary":{
            "total_accounts":int(total_accounts),
            "total_outstanding":float(total_outstanding),
            "high_risk_accounts":int(len(high_risk)),
            "medium_risk_accounts":int(len(medium_risk)),
            "low_risk_accounts":int(len(low_risk)),
            "overdue_accounts":int(len(overdue)),
            "accounts_with_90_plus_days_ageing":int(len(high_ageing))
        },
        "risk_exposure":{
            "high_risk_exposure":float(high_risk["Outstanding_Amount"].sum()),
            "medium_risk_exposure":float(medium_risk["Outstanding_Amount"].sum()),
            "low_risk_exposure":float(low_risk["Outstanding_Amount"].sum())
        },
        "regional_exposure":{str(k):float(v) for k,v in regional_exposure.items()},
        "top_exposure_accounts":top_accounts,
        "account_details":account_details
    }
    return context