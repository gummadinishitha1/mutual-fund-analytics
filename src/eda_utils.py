from pathlib import Path

import pandas as pd


def run_csv_eda(csv_path: str) -> None:
    """Print a compact EDA summary for one CSV file."""
    path = Path(csv_path)
    df = pd.read_csv(path)

    print("\n" + "=" * 70)
    print(f"FILE: {path.name}")
    print("=" * 70)

    print("\nShape:")
    print(df.shape)

    print("\nColumns:")
    print(list(df.columns))

    print("\nData Types:")
    print(df.dtypes)

    print("\nMissing Values By Column:")
    print(df.isnull().sum())
    print("Total Missing Values:", df.isnull().sum().sum())

    print("\nDuplicate Rows:")
    print(df.duplicated().sum())

    print("\nFirst 5 Rows:")
    print(df.head())

    print("\nNumeric Summary:")
    print(df.describe(include="number"))

    print("\nCategorical Summary:")
    print(df.describe(include="object"))
