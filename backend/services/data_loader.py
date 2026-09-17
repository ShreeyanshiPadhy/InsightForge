import pandas as pd


def load_dataset(file_path):
    """Load the financial dataset from Excel."""

    df = pd.read_excel(file_path, header=4)

    print("\nFIRST 5 DATA ROWS:")
    print(df.iloc[:5, [0, 2, 3, 20]].to_string(index=False))

    df = df.dropna(how="all")

    print("Dataset loaded successfully!")
    print(f"Rows: {df.shape[0]}")
    print(f"Columns: {df.shape[1]}")

    print("\nCOLUMN NAMES:")
    for i, column in enumerate(df.columns, start=1):
        print(f"{i}. {column}")

    return df