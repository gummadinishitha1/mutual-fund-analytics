from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DB_PATH = PROJECT_ROOT / "bluestock_mf.db"

DATASETS = {
    "fund_master_cleaned.csv": "dim_fund",
    "nav_history_cleaned.csv": "fact_nav",
    "investor_transactions_cleaned.csv": "fact_transactions",
    "scheme_performance_cleaned.csv": "fact_performance",
    "aum_by_fund_house_cleaned.csv": "fact_aum_by_fund_house",
    "monthly_sip_inflows_cleaned.csv": "fact_monthly_sip_inflows",
    "category_inflows_cleaned.csv": "fact_category_inflows",
    "industry_folio_count_cleaned.csv": "fact_industry_folio_count",
    "portfolio_holdings_cleaned.csv": "fact_portfolio_holdings",
    "benchmark_indices_cleaned.csv": "fact_benchmark_indices",
}


def load_csv_to_sqlite(csv_path: Path, table_name: str, engine) -> tuple[int, int]:
    df = pd.read_csv(csv_path)
    source_rows = len(df)

    df.to_sql(
        table_name,
        con=engine,
        if_exists="replace",
        index=False,
        chunksize=10_000,
    )

    with engine.connect() as conn:
        loaded_rows = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar_one()

    return source_rows, loaded_rows


def main() -> None:
    if not PROCESSED_DIR.exists():
        raise FileNotFoundError(f"Processed data folder not found: {PROCESSED_DIR}")

    engine = create_engine(f"sqlite:///{DB_PATH}")
    mismatches = []

    print(f"Loading cleaned CSVs into SQLite: {DB_PATH}")
    print("-" * 72)

    for csv_file, table_name in DATASETS.items():
        csv_path = PROCESSED_DIR / csv_file
        if not csv_path.exists():
            raise FileNotFoundError(f"Missing cleaned dataset: {csv_path}")

        source_rows, loaded_rows = load_csv_to_sqlite(csv_path, table_name, engine)
        status = "OK" if source_rows == loaded_rows else "MISMATCH"

        print(
            f"{status:8} {csv_file:36} -> {table_name:30} "
            f"csv={source_rows:,} sqlite={loaded_rows:,}"
        )

        if source_rows != loaded_rows:
            mismatches.append((csv_file, table_name, source_rows, loaded_rows))

    print("-" * 72)

    if mismatches:
        details = "\n".join(
            f"{csv_file} -> {table_name}: csv={source_rows}, sqlite={loaded_rows}"
            for csv_file, table_name, source_rows, loaded_rows in mismatches
        )
        raise RuntimeError(f"Row count verification failed:\n{details}")

    print("All cleaned datasets loaded successfully. Row counts match.")


if __name__ == "__main__":
    main()
