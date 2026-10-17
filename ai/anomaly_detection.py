import pandas as pd
import json
import os

DATA_FILE="data/dummy_debtors.csv"
OUTPUT_DIR="outputs"
ANOMALY_FILE=os.path.join(OUTPUT_DIR,"anomaly_analysis.csv")
ANOMALY_JSON_FILE=os.path.join(OUTPUT_DIR,"anomaly_analysis.json")

REQUIRED_COLUMNS=[
    "Account_ID",
    "Customer_Name",
    "Outstanding_Amount",
    "Ageing_Days",
    "Account_Status",
    "Region"
]

def load_data(file_path=DATA_FILE):
    try:
        df=pd.read_csv(file_path)
        print(f"\nData loaded successfully: {len(df)} records")
        return df
    except FileNotFoundError:
        print(f"\nERROR: File not found: {file_path}")
    except Exception as e:
        print(f"\nERROR while loading data: {e}")
    return None

def validate_data(df):
    if df is None or df.empty:
        print("\nERROR: Dataset is empty.")
        return False

    missing=[column for column in REQUIRED_COLUMNS if column not in df.columns]

    if missing:
        print("\nERROR: Missing required columns: "+", ".join(missing))
        return False

    return True

def prepare_data(df):
    df=df.copy()

    for column in ["Outstanding_Amount","Ageing_Days"]:
        df[column]=pd.to_numeric(df[column],errors="coerce")

    df["Outstanding_Amount"]=df["Outstanding_Amount"].fillna(0).clip(lower=0)
    df["Ageing_Days"]=df["Ageing_Days"].fillna(0).clip(lower=0)

    return df

def calculate_amount_threshold(df,percentile=0.90):
    return float(df["Outstanding_Amount"].quantile(percentile))

def calculate_ageing_threshold(df,percentile=0.90):
    return float(df["Ageing_Days"].quantile(percentile))

def detect_high_amount(df,threshold):
    return df["Outstanding_Amount"]>threshold

def detect_high_ageing(df,threshold):
    return df["Ageing_Days"]>threshold

def detect_combined_anomaly(row):
    amount=row["High_Amount_Anomaly"]
    ageing=row["High_Ageing_Anomaly"]

    if amount and ageing:
        return "High Amount and High Ageing"
    if amount:
        return "Unusually High Outstanding Amount"
    if ageing:
        return "Unusually High Ageing"
    return "No Anomaly"

def calculate_anomaly_score(row):
    return int(row["High_Amount_Anomaly"])+int(row["High_Ageing_Anomaly"])

def get_anomaly_category(score):
    if score>=2:
        return "High"
    if score==1:
        return "Medium"
    return "Normal"

def generate_anomaly_reason(row):
    reasons=[]

    if row["High_Amount_Anomaly"]:
        reasons.append("Outstanding amount is above the dataset percentile threshold")

    if row["High_Ageing_Anomaly"]:
        reasons.append("Ageing is above the dataset percentile threshold")

    if not reasons:
        reasons.append("No percentile-based anomaly detected")

    return ", ".join(reasons)

def perform_anomaly_analysis(df,percentile=0.90):
    if not 0<percentile<1:
        raise ValueError("Percentile must be between 0 and 1.")

    if df is None or df.empty:
        raise ValueError("Cannot analyze an empty dataset.")

    missing=[column for column in ["Outstanding_Amount","Ageing_Days"] if column not in df.columns]

    if missing:
        raise ValueError("Missing anomaly input columns: "+", ".join(missing))

    df=prepare_data(df)

    amount_threshold=calculate_amount_threshold(df,percentile)
    ageing_threshold=calculate_ageing_threshold(df,percentile)

    df["High_Amount_Anomaly"]=detect_high_amount(df,amount_threshold)
    df["High_Ageing_Anomaly"]=detect_high_ageing(df,ageing_threshold)

    df["Anomaly_Score"]=df.apply(calculate_anomaly_score,axis=1)
    df["Anomaly_Category"]=df["Anomaly_Score"].apply(get_anomaly_category)
    df["Anomaly_Type"]=df.apply(detect_combined_anomaly,axis=1)
    df["Anomaly_Reason"]=df.apply(generate_anomaly_reason,axis=1)

    return df,amount_threshold,ageing_threshold

def get_anomalous_accounts(df):
    return df[df["Anomaly_Category"]!="Normal"].sort_values(
        by="Anomaly_Score",
        ascending=False
    )

def get_high_anomaly_accounts(df):
    return df[df["Anomaly_Category"]=="High"].sort_values(
        by="Anomaly_Score",
        ascending=False
    )

def get_medium_anomaly_accounts(df):
    return df[df["Anomaly_Category"]=="Medium"].sort_values(
        by="Anomaly_Score",
        ascending=False
    )

def create_anomaly_summary(df,amount_threshold,ageing_threshold):
    anomalies=get_anomalous_accounts(df)

    return {
        "total_accounts":int(len(df)),
        "high_anomaly_accounts":int((df["Anomaly_Category"]=="High").sum()),
        "medium_anomaly_accounts":int((df["Anomaly_Category"]=="Medium").sum()),
        "normal_accounts":int((df["Anomaly_Category"]=="Normal").sum()),
        "total_anomalous_accounts":int(len(anomalies)),
        "anomalous_outstanding_exposure":float(anomalies["Outstanding_Amount"].sum()),
        "amount_anomaly_threshold":float(amount_threshold),
        "ageing_anomaly_threshold":float(ageing_threshold)
    }

def save_results(df,summary):
    os.makedirs(OUTPUT_DIR,exist_ok=True)
    df.to_csv(ANOMALY_FILE,index=False)

    output={
        "anomaly_summary":summary,
        "account_analysis":df.to_dict(orient="records")
    }

    with open(ANOMALY_JSON_FILE,"w",encoding="utf-8") as file:
        json.dump(output,file,indent=4,default=str)

def display_results(df,summary):
    print("\n"+"="*60)
    print("INSIGHTFORGE - ANOMALY DETECTION")
    print("="*60)

    for key,value in summary.items():
        print(f"{key.replace('_',' ').title():35}: {value}")

    anomalies=get_anomalous_accounts(df)

    print("\nANOMALOUS ACCOUNTS")
    print("-"*60)

    columns=[
        "Account_ID",
        "Customer_Name",
        "Outstanding_Amount",
        "Ageing_Days",
        "Anomaly_Score",
        "Anomaly_Category",
        "Anomaly_Type",
        "Anomaly_Reason"
    ]

    if not anomalies.empty:
        print(anomalies[columns].to_string(index=False))
    else:
        print("No anomalous accounts found.")

    print("="*60)

def main():
    df=load_data()

    if df is None or not validate_data(df):
        return

    df=prepare_data(df)
    df,amount_threshold,ageing_threshold=perform_anomaly_analysis(df)

    summary=create_anomaly_summary(
        df,
        amount_threshold,
        ageing_threshold
    )

    display_results(df,summary)
    save_results(df,summary)

if __name__=="__main__":
    main()