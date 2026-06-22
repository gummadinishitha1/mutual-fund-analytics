import pandas as pd
import os

# Folder path
folder = "data/raw"

# Loop through all CSV files
for file in os.listdir(folder):
    if file.endswith(".csv"):
        
        file_path = os.path.join(folder, file)
        df = pd.read_csv(file_path)

        print("\n" + "="*60)
        print("FILE:", file)
        print("="*60)

        # Shape
        print("\nShape:", df.shape)

        # Data types
        print("\nData Types:")
        print(df.dtypes)

        # First 5 rows
        print("\nFirst 5 rows:")
        print(df.head())

        # ---------------- ANOMALY CHECKS ----------------
        print("\nAnomalies Check:")

        # Missing values
        missing = df.isnull().sum().sum()
        print("Total Missing Values:", missing)

        # Duplicate rows
        duplicates = df.duplicated().sum()
        print("Duplicate Rows:", duplicates)

        # Column names check
        print("Columns:", list(df.columns))

        # Basic info summary
        print("\nInfo:")
        df.info()