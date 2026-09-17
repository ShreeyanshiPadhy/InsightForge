from backend.services.data_loader import load_dataset
from backend.services.data_cleaning import clean_dataset
from backend.services.validation import validate_dataset
from backend.services.financial_analysis import calculate_kpis
from backend.services.ageing_analysis import calculate_ageing
from backend.services.regional_analysis import calculate_regional_exposure
from backend.services.json_export import export_results

DATA_PATH = "backend/data/Lighting_CB May 26 Final for chatgpt.xlsx"
OUTPUT_PATH = "backend/outputs/financial_results.json"


def main():

    # 1. Load dataset
    df = load_dataset(DATA_PATH)
    print("\nCOLUMN NAMES:")
    for i, column in enumerate(df.columns, start=1):
        print(f"{i}. {column}")

    # 2. Clean dataset
    df = clean_dataset(df)

    # 3. Validate dataset
    validation = validate_dataset(df)

    # 4. Calculate KPIs
    kpis = calculate_kpis(df)

    # 5. Ageing analysis
    ageing = calculate_ageing(df)

    # 6. Regional analysis
    regions = calculate_regional_exposure(df)

    # 7. Combine results
    results = {
        "dataset": {
            "name": "Debtors May 26",
            "total_records": len(df),
            "status": "validated"
        },
        "kpis": kpis,
        "ageing": ageing,
        "regions": regions,
        "validation": validation
    }

    # 8. Export JSON
    export_results(results, OUTPUT_PATH)

    print("\nInsightForge analysis completed!")


if __name__ == "__main__":
    main()