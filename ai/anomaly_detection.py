import pandas as pd
import json
import os

DATA_FILE="data/dummy_debtors.csv"
OUTPUT_DIR="outputs"
ANOMALY_FILE=os.path.join(OUTPUT_DIR,"anomaly_analysis.csv")
ANOMALY_JSON_FILE=os.path.join(OUTPUT_DIR,"anomaly_analysis.json")

REQUIRED_COLUMNS=["Account_ID","Customer_Name","Outstanding_Amount","Ageing_Days","Account_Status","Region"]

def load_data(file_path):
    try:
        df=pd.read_csv(file_path)
        print("\nData loaded successfully.")
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
    df["Outstanding_Amount"]=pd.to_numeric(df["Outstanding_Amount"],errors="coerce")
    df["Ageing_Days"]=pd.to_numeric(df["Ageing_Days"],errors="coerce")
    df["Outstanding_Amount"]=df["Outstanding_Amount"].fillna(0)
    df["Ageing_Days"]=df["Ageing_Days"].fillna(0)
    return df

def calculate_amount_threshold(df):
    return df["Outstanding_Amount"].quantile(0.90)

def calculate_ageing_threshold(df):
    return df["Ageing_Days"].quantile(0.90)

def detect_high_amount(df,threshold):
    return df["Outstanding_Amount"]>=threshold

def detect_high_ageing(df,threshold):
    return df["Ageing_Days"]>=threshold

def detect_combined_anomaly(row):
    amount_anomaly=row["High_Amount_Anomaly"]
    ageing_anomaly=row["High_Ageing_Anomaly"]
    if amount_anomaly and ageing_anomaly:
        return "High Amount and High Ageing"
    elif amount_anomaly:
        return "Unusually High Outstanding Amount"
    elif ageing_anomaly:
        return "Unusually High Ageing"
    else:
        return "No Anomaly"

def calculate_anomaly_score(row):
    score=0
    if row["High_Amount_Anomaly"]:
        score+=1
    if row["High_Ageing_Anomaly"]:
        score+=1
    return score

def get_anomaly_category(score):
    if score==2:
        return "High"
    elif score==1:
        return "Medium"
    else:
        return "Normal"

def generate_anomaly_reason(row):
    reasons=[]
    if row["High_Amount_Anomaly"]:
        reasons.append("Outstanding amount is unusually high")
    if row["High_Ageing_Anomaly"]:
        reasons.append("Ageing is unusually high")
    if not reasons:
        reasons.append("No unusual financial pattern detected")
    return ", ".join(reasons)

def perform_anomaly_analysis(df):
    df=df.copy()
    amount_threshold=calculate_amount_threshold(df)
    ageing_threshold=calculate_ageing_threshold(df)
    df["High_Amount_Anomaly"]=detect_high_amount(df,amount_threshold)
    df["High_Ageing_Anomaly"]=detect_high_ageing(df,ageing_threshold)
    df["Anomaly_Score"]=df.apply(calculate_anomaly_score,axis=1)
    df["Anomaly_Category"]=df["Anomaly_Score"].apply(get_anomaly_category)
    df["Anomaly_Type"]=df.apply(detect_combined_anomaly,axis=1)
    df["Anomaly_Reason"]=df.apply(generate_anomaly_reason,axis=1)
    return df,amount_threshold,ageing_threshold

def get_anomalous_accounts(df):
    return df[df["Anomaly_Category"]!="Normal"].sort_values(by="Anomaly_Score",ascending=False)

def get_high_anomaly_accounts(df):
    return df[df["Anomaly_Category"]=="High"].sort_values(by="Anomaly_Score",ascending=False)

def get_medium_anomaly_accounts(df):
    return df[df["Anomaly_Category"]=="Medium"].sort_values(by="Anomaly_Score",ascending=False)

def create_anomaly_summary(df,amount_threshold,ageing_threshold):
    total_accounts=len(df)
    high_anomaly_count=(df["Anomaly_Category"]=="High").sum()
    medium_anomaly_count=(df["Anomaly_Category"]=="Medium").sum()
    normal_count=(df["Anomaly_Category"]=="Normal").sum()
    anomalous_accounts=df[df["Anomaly_Category"]!="Normal"]
    anomalous_exposure=anomalous_accounts["Outstanding_Amount"].sum()
    summary={
        "total_accounts":int(total_accounts),
        "high_anomaly_accounts":int(high_anomaly_count),
        "medium_anomaly_accounts":int(medium_anomaly_count),
        "normal_accounts":int(normal_count),
        "total_anomalous_accounts":int(len(anomalous_accounts)),
        "anomalous_outstanding_exposure":float(anomalous_exposure),
        "amount_anomaly_threshold":float(amount_threshold),
        "ageing_anomaly_threshold":float(ageing_threshold)
    }
    return summary

def save_results(df,summary):
    os.makedirs(OUTPUT_DIR,exist_ok=True)
    df.to_csv(ANOMALY_FILE,index=False)
    output={
        "anomaly_summary":summary,
        "account_analysis":df.to_dict(orient="records")
    }
    with open(ANOMALY_JSON_FILE,"w",encoding="utf-8") as file:
        json.dump(output,file,indent=4)
    print("\nResults saved successfully.")
    print(f"CSV: {ANOMALY_FILE}")
    print(f"JSON: {ANOMALY_JSON_FILE}")

def display_results(df,summary):
    print("\n")
    print("="*60)
    print("INSIGHTFORGE - ANOMALY DETECTION")
    print("="*60)
    print("\nANOMALY SUMMARY")
    print("-"*60)
    print(f"Total Accounts          : {summary['total_accounts']}")
    print(f"High Anomaly Accounts   : {summary['high_anomaly_accounts']}")
    print(f"Medium Anomaly Accounts : {summary['medium_anomaly_accounts']}")
    print(f"Normal Accounts         : {summary['normal_accounts']}")
    print(f"Total Anomalous Accounts: {summary['total_anomalous_accounts']}")
    print(f"Anomalous Exposure      : ₹{summary['anomalous_outstanding_exposure']:,.2f}")
    print(f"Amount Threshold        : ₹{summary['amount_anomaly_threshold']:,.2f}")
    print(f"Ageing Threshold        : {summary['ageing_anomaly_threshold']:.2f} days")
    print("\nANOMALOUS ACCOUNTS")
    print("-"*60)
    anomalies=get_anomalous_accounts(df)
    if len(anomalies)>0:
        print(anomalies[["Account_ID","Customer_Name","Outstanding_Amount","Ageing_Days","Anomaly_Score","Anomaly_Category","Anomaly_Type","Anomaly_Reason"]].to_string(index=False))
    else:
        print("No anomalous accounts found.")
    print("\n")
    print("="*60)

def main():
    df=load_data(DATA_FILE)
    if df is None:
        return
    if not validate_data(df):
        return
    df=prepare_data(df)
    df,amount_threshold,ageing_threshold=perform_anomaly_analysis(df)
    summary=create_anomaly_summary(df,amount_threshold,ageing_threshold)
    display_results(df,summary)
    save_results(df,summary)

if __name__=="__main__":
    main()