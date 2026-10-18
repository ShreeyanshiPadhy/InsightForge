import os
import pandas as pd

def get_excel_sheet_names(file_path: str) -> list:
    """Inspect and return list of sheet names in an Excel workbook."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ['.xlsx', '.xls']:
        raise ValueError("File must be an Excel workbook (.xlsx or .xls).")
    
    excel_file = pd.ExcelFile(file_path)
    return excel_file.sheet_names

def load_dataset(file_path: str, sheet_name=0, header: int = 0) -> pd.DataFrame:
    """
    Load financial datasets from CSV, XLSX, or XLS files using pandas.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext == '.csv':
            df = pd.read_csv(file_path, header=header)
        elif ext in ['.xlsx', '.xls']:
            engine = 'openpyxl' if ext == '.xlsx' else 'xlrd'
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=header, engine=engine)
        else:
            raise ValueError(f"Unsupported format: {ext}. Supported: .csv, .xlsx, .xls")

        # Clean empty rows/cols and whitespace
        df = df.dropna(how="all").dropna(how="all", axis=1)
        df.columns = [str(col).strip() for col in df.columns]

        print(f"Loaded '{file_path}' ({ext}): {df.shape[0]} rows, {df.shape[1]} columns.")
        return df

    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        raise e