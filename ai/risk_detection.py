import pandas as pd
import json
import os

DATA_FILE="data/dummy_debtors.csv"
OUTPUT_DIR="outputs"
PROCESSED_FILE=os.path.join(OUTPUT_DIR,"risk_analysis.csv")
JSON_FILE=os.path.join(OUTPUT_DIR,"risk_analysis.json")

REQUIRED_COLUMNS=["Account_ID","Customer_Name","Outstanding_Amount","Ageing_Days","Account_Status","Region"]

def load_data(file_path):
    try:
        df=pd.read_csv(file_path)
        print(f"\nData loaded successfully.")
        print(f"Number of records: {len(df)}")
        return df
    except FileNotFoundError:
        print(f"\nERROR: File not found: {file_path}")
        return None
    except Exception as e:
        print(f"\nERROR while loading data: {e}")
        return None

def validate_data(df):
    missing_columns=[column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        print("\nERROR: Missing required columns:")
        for column in missing_columns:
            print(f"- {column}")
        return False
    print("\nData validation successful.")
    return True

def prepare_data(df):
    df=df.copy()
    df["Outstanding_Amount"]=pd.to_numeric(df["Outstanding_Amount"],errors="coerce").fillna(0)
    df["Ageing_Days"]=pd.to_numeric(df["Ageing_Days"],errors="coerce").fillna(0)
    return df


DEFAULT_RISK_CONFIG={
    "ageing_medium":30,
    "ageing_high":60,
    "ageing_critical":90,
    "exposure_low":100000,
    "exposure_medium":300000,
    "exposure_high":500000
}

def validate_risk_config(config):
    required=list(DEFAULT_RISK_CONFIG)
    missing=[key for key in required if key not in config]
    if missing:
        raise ValueError(f"Missing risk settings: {missing}")

    if not (
        0<=config["ageing_medium"]<config["ageing_high"]<config["ageing_critical"]
    ):
        raise ValueError("Ageing thresholds must be in ascending order.")

    if not (
        0<=config["exposure_low"]<config["exposure_medium"]<config["exposure_high"]
    ):
        raise ValueError("Exposure thresholds must be in ascending order.")

def calculate_ageing_score(ageing_days,config=None):
    config=config or DEFAULT_RISK_CONFIG
    if ageing_days>=config["ageing_critical"]:
        return 3
    elif ageing_days>=config["ageing_high"]:
        return 2
    elif ageing_days>=config["ageing_medium"]:
        return 1
    return 0

def calculate_exposure_score(outstanding_amount,config=None):
    config=config or DEFAULT_RISK_CONFIG
    if outstanding_amount>=config["exposure_high"]:
        return 3
    elif outstanding_amount>=config["exposure_medium"]:
        return 2
    elif outstanding_amount>=config["exposure_low"]:
        return 1
    return 0

def calculate_total_risk_score(ageing_score,exposure_score):
    return ageing_score+exposure_score

def get_risk_category(total_score):
    if total_score>=5:
        return "High"
    elif total_score>=3:
        return "Medium"
    return "Low"

def generate_risk_reason(ageing_days,outstanding_amount,config=None):
    config=config or DEFAULT_RISK_CONFIG
    reasons=[]

    if ageing_days>=config["ageing_critical"]:
        reasons.append(f"Ageing at least {config['ageing_critical']} days")
    elif ageing_days>=config["ageing_high"]:
        reasons.append(f"Ageing at least {config['ageing_high']} days")
    elif ageing_days>=config["ageing_medium"]:
        reasons.append(f"Ageing at least {config['ageing_medium']} days")

    if outstanding_amount>=config["exposure_high"]:
        reasons.append("Very high outstanding exposure")
    elif outstanding_amount>=config["exposure_medium"]:
        reasons.append("High outstanding exposure")
    elif outstanding_amount>=config["exposure_low"]:
        reasons.append("Moderate outstanding exposure")

    if not reasons:
        reasons.append("No elevated ageing or exposure indicators")
    return ", ".join(reasons)

def perform_risk_analysis(df,config=None):
    config=config or DEFAULT_RISK_CONFIG
    validate_risk_config(config)
    df=df.copy()

    df["Ageing_Risk_Score"]=df["Ageing_Days"].apply(
        lambda value:calculate_ageing_score(value,config)
    )
    df["Exposure_Risk_Score"]=df["Outstanding_Amount"].apply(
        lambda value:calculate_exposure_score(value,config)
    )
    df["Risk_Score"]=df["Ageing_Risk_Score"]+df["Exposure_Risk_Score"]
    df["Risk_Category"]=df["Risk_Score"].apply(get_risk_category)
    df["Risk_Reason"]=df.apply(
        lambda row:generate_risk_reason(
            row["Ageing_Days"],
            row["Outstanding_Amount"],
            config
        ),
        axis=1
    )
    return df

def get_high_risk_accounts(df):
    return df[df["Risk_Category"]=="High"].sort_values(by="Risk_Score",ascending=False)

def get_medium_risk_accounts(df):
    return df[df["Risk_Category"]=="Medium"].sort_values(by="Risk_Score",ascending=False)

def get_low_risk_accounts(df):
    return df[df["Risk_Category"]=="Low"].sort_values(by="Risk_Score",ascending=False)

def get_top_exposure_accounts(df,n=10):
    return df.sort_values(by="Outstanding_Amount",ascending=False).head(n)

def create_risk_summary(df):
    total_accounts=len(df)
    total_outstanding=df["Outstanding_Amount"].sum()
    high_risk_count=(df["Risk_Category"]=="High").sum()
    medium_risk_count=(df["Risk_Category"]=="Medium").sum()
    low_risk_count=(df["Risk_Category"]=="Low").sum()
    high_risk_exposure=df.loc[df["Risk_Category"]=="High","Outstanding_Amount"].sum()
    medium_risk_exposure=df.loc[df["Risk_Category"]=="Medium","Outstanding_Amount"].sum()
    low_risk_exposure=df.loc[df["Risk_Category"]=="Low","Outstanding_Amount"].sum()
    return {
        "total_accounts":int(total_accounts),
        "total_outstanding":float(total_outstanding),
        "high_risk_accounts":int(high_risk_count),
        "medium_risk_accounts":int(medium_risk_count),
        "low_risk_accounts":int(low_risk_count),
        "high_risk_exposure":float(high_risk_exposure),
        "medium_risk_exposure":float(medium_risk_exposure),
        "low_risk_exposure":float(low_risk_exposure)
    }

def save_results(df,summary):
    os.makedirs(OUTPUT_DIR,exist_ok=True)
    df.to_csv(PROCESSED_FILE,index=False)
    output={
        "risk_summary":summary,
        "account_analysis":df.to_dict(orient="records")
    }
    with open(JSON_FILE,"w",encoding="utf-8") as file:
        json.dump(output,file,indent=4)
    print("\nResults saved successfully.")
    print(f"CSV: {PROCESSED_FILE}")
    print(f"JSON: {JSON_FILE}")

def display_results(df,summary):
    print("\n")
    print("="*60)
    print("INSIGHTFORGE - RISK ANALYSIS")
    print("="*60)
    print("\nRISK SUMMARY")
    print("-"*60)
    print(f"Total Accounts       : {summary['total_accounts']}")
    print(f"Total Outstanding    : ₹{summary['total_outstanding']:,.2f}")
    print(f"High Risk Accounts   : {summary['high_risk_accounts']}")
    print(f"Medium Risk Accounts : {summary['medium_risk_accounts']}")
    print(f"Low Risk Accounts    : {summary['low_risk_accounts']}")
    print("\nHIGH-RISK ACCOUNTS")
    print("-"*60)
    high_risk=get_high_risk_accounts(df)
    if len(high_risk)>0:
        print(high_risk[["Account_ID","Customer_Name","Outstanding_Amount","Ageing_Days","Risk_Score","Risk_Category","Risk_Reason"]].to_string(index=False))
    else:
        print("No high-risk accounts found.")
    print("\nTOP 10 EXPOSURE ACCOUNTS")
    print("-"*60)
    top_exposure=get_top_exposure_accounts(df,10)
    print(top_exposure[["Account_ID","Customer_Name","Outstanding_Amount","Ageing_Days","Risk_Category"]].to_string(index=False))
    print("\n")
    print("="*60)

def main():
    df=load_data(DATA_FILE)
    if df is None:
        return
    if not validate_data(df):
        return
    df=prepare_data(df)
    df=perform_risk_analysis(df)
    summary=create_risk_summary(df)
    display_results(df,summary)
    save_results(df,summary)

if __name__=="__main__":
    main()