from pathlib import Path
import sqlite3

import pandas as pd


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
DB_PATH = Path("bluestock_mf.db")


def clean_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    text_columns = df.select_dtypes(include=["object", "string"]).columns
    for column in text_columns:
        df[column] = df[column].astype("string").str.strip()
    return df


def save_to_sqlite(df: pd.DataFrame, table_name: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql(table_name, conn, if_exists="replace", index=False)

    print(f"Saved table {table_name} | shape={df.shape}")


def save_processed_csv(df: pd.DataFrame, file_name: str) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    path = PROCESSED_DIR / file_name
    df.to_csv(path, index=False)
    print(f"Saved cleaned CSV {path} | shape={df.shape}")


def clean_nav_history() -> None:
    df = pd.read_csv(RAW_DIR / "02_nav_history.csv")
    df = clean_text_columns(df)
    df = df.drop_duplicates(subset=["amfi_code", "date"], keep="last")

    df["amfi_code"] = pd.to_numeric(df["amfi_code"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")

    df = df.dropna(subset=["amfi_code", "date"])
    df = df[df["nav"].gt(0) | df["nav"].isna()]
    df = df.sort_values(["amfi_code", "date"]).reset_index(drop=True)

    filled_groups = []
    for amfi_code, fund_nav in df.groupby("amfi_code", sort=True):
        fund_nav = fund_nav.set_index("date").sort_index()
        daily_index = pd.date_range(fund_nav.index.min(), fund_nav.index.max(), freq="D")
        fund_nav = fund_nav.reindex(daily_index)
        fund_nav["amfi_code"] = amfi_code
        fund_nav["nav_was_forward_filled"] = fund_nav["nav"].isna()
        fund_nav["nav"] = fund_nav["nav"].ffill()
        fund_nav = fund_nav.dropna(subset=["nav"])
        fund_nav.index.name = "date"
        filled_groups.append(fund_nav.reset_index())

    cleaned = pd.concat(filled_groups, ignore_index=True)
    cleaned = cleaned[cleaned["nav"].gt(0)]
    cleaned["amfi_code"] = cleaned["amfi_code"].astype("int64")
    cleaned["date"] = cleaned["date"].dt.strftime("%Y-%m-%d")
    cleaned = cleaned.sort_values(["amfi_code", "date"]).reset_index(drop=True)

    save_processed_csv(cleaned, "nav_history_cleaned.csv")


def clean_investor_transactions() -> None:
    df = pd.read_csv(RAW_DIR / "08_investor_transactions.csv")
    df = clean_text_columns(df)
    df = df.drop_duplicates()

    transaction_type_map = {
        "sip": "SIP",
        "systematic investment plan": "SIP",
        "lumpsum": "Lumpsum",
        "lump sum": "Lumpsum",
        "redemption": "Redemption",
        "redeem": "Redemption",
    }
    df["transaction_type"] = (
        df["transaction_type"]
        .astype("string")
        .str.strip()
        .str.lower()
        .map(transaction_type_map)
    )

    kyc_status_map = {
        "verified": "Verified",
        "pending": "Pending",
        "rejected": "Rejected",
    }
    df["kyc_status"] = (
        df["kyc_status"]
        .astype("string")
        .str.strip()
        .str.lower()
        .map(kyc_status_map)
    )

    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df["amfi_code"] = pd.to_numeric(df["amfi_code"], errors="coerce")
    df["amount_inr"] = pd.to_numeric(df["amount_inr"], errors="coerce")
    df["annual_income_lakh"] = pd.to_numeric(df["annual_income_lakh"], errors="coerce")

    valid_transaction_types = {"SIP", "Lumpsum", "Redemption"}
    valid_kyc_statuses = {"Verified", "Pending", "Rejected"}

    df = df.dropna(subset=["investor_id", "transaction_date", "amfi_code", "transaction_type", "amount_inr"])
    df = df[df["transaction_type"].isin(valid_transaction_types)]
    df = df[df["kyc_status"].isin(valid_kyc_statuses)]
    df = df[df["amount_inr"].gt(0)]
    df["amfi_code"] = df["amfi_code"].astype("int64")
    df["transaction_date"] = df["transaction_date"].dt.strftime("%Y-%m-%d")
    df = df.sort_values(["transaction_date", "investor_id", "amfi_code"]).reset_index(drop=True)

    save_processed_csv(df, "investor_transactions_cleaned.csv")


def clean_scheme_performance() -> None:
    df = pd.read_csv(RAW_DIR / "07_scheme_performance.csv")
    df = clean_text_columns(df)
    df = df.drop_duplicates(subset=["amfi_code"], keep="last")

    numeric_columns = [
        "amfi_code",
        "return_1yr_pct",
        "return_3yr_pct",
        "return_5yr_pct",
        "benchmark_3yr_pct",
        "alpha",
        "beta",
        "sharpe_ratio",
        "sortino_ratio",
        "std_dev_ann_pct",
        "max_drawdown_pct",
        "aum_crore",
        "expense_ratio_pct",
        "morningstar_rating",
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    return_columns = ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct", "benchmark_3yr_pct"]
    df["has_non_numeric_return"] = df[return_columns].isna().any(axis=1)
    df["expense_ratio_out_of_range"] = ~df["expense_ratio_pct"].between(0.1, 2.5, inclusive="both")
    df["performance_anomaly_flag"] = df["has_non_numeric_return"] | df["expense_ratio_out_of_range"]

    def anomaly_reason(row: pd.Series) -> str:
        reasons = []
        if row["has_non_numeric_return"]:
            reasons.append("non_numeric_return")
        if row["expense_ratio_out_of_range"]:
            reasons.append("expense_ratio_out_of_range")
        return ";".join(reasons)

    df["performance_anomaly_reason"] = df.apply(anomaly_reason, axis=1)

    df = df.dropna(subset=["amfi_code", "scheme_name", "fund_house"])
    df["amfi_code"] = df["amfi_code"].astype("int64")
    df = df.sort_values(["fund_house", "scheme_name"]).reset_index(drop=True)

    save_processed_csv(df, "scheme_performance_cleaned.csv")


def clean_fund_master() -> None:
    df = pd.read_csv(RAW_DIR / "01_fund_master.csv")
    df = clean_text_columns(df)
    df = df.drop_duplicates()

    df["launch_date"] = pd.to_datetime(df["launch_date"], errors="coerce")

    numeric_columns = [
        "amfi_code",
        "expense_ratio_pct",
        "exit_load_pct",
        "min_sip_amount",
        "min_lumpsum_amount",
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=["amfi_code", "scheme_name", "fund_house"])
    df = df[df["expense_ratio_pct"].between(0, 3)]
    df = df[df["exit_load_pct"].ge(0)]
    df = df[df["min_sip_amount"].ge(0)]
    df = df[df["min_lumpsum_amount"].ge(0)]
    df = df.sort_values(["fund_house", "scheme_name"]).reset_index(drop=True)

    save_to_sqlite(df, "dim_fund")


def clean_aum_by_fund_house() -> None:
    df = pd.read_csv(RAW_DIR / "03_aum_by_fund_house.csv")
    df = clean_text_columns(df)
    df = df.drop_duplicates()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for column in ["aum_lakh_crore", "aum_crore", "num_schemes"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=["date", "fund_house"])
    df = df[df["aum_lakh_crore"].ge(0)]
    df = df[df["aum_crore"].ge(0)]
    df = df[df["num_schemes"].ge(0)]
    df = df.sort_values(["date", "fund_house"]).reset_index(drop=True)

    save_to_sqlite(df, "fact_aum_by_fund_house")


def clean_monthly_sip_inflows() -> None:
    df = pd.read_csv(RAW_DIR / "04_monthly_sip_inflows.csv")
    df = clean_text_columns(df)
    df = df.drop_duplicates()

    df["month"] = pd.to_datetime(df["month"], errors="coerce").dt.to_period("M").astype("string")
    numeric_columns = [
        "sip_inflow_crore",
        "active_sip_accounts_crore",
        "new_sip_accounts_lakh",
        "sip_aum_lakh_crore",
        "yoy_growth_pct",
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=["month"])
    for column in numeric_columns[:-1]:
        df = df[df[column].ge(0)]

    df = df.sort_values("month").reset_index(drop=True)

    save_to_sqlite(df, "fact_monthly_sip_inflows")


def clean_category_inflows() -> None:
    df = pd.read_csv(RAW_DIR / "05_category_inflows.csv")
    df = clean_text_columns(df)
    df = df.drop_duplicates()

    df["month"] = pd.to_datetime(df["month"], errors="coerce").dt.to_period("M").astype("string")
    df["net_inflow_crore"] = pd.to_numeric(df["net_inflow_crore"], errors="coerce")

    df = df.dropna(subset=["month", "category", "net_inflow_crore"])
    df = df.sort_values(["month", "category"]).reset_index(drop=True)

    save_to_sqlite(df, "fact_category_inflows")


def clean_industry_folio_count() -> None:
    df = pd.read_csv(RAW_DIR / "06_industry_folio_count.csv")
    df = clean_text_columns(df)
    df = df.drop_duplicates()

    df["month"] = pd.to_datetime(df["month"], errors="coerce").dt.to_period("M").astype("string")
    folio_columns = [
        "total_folios_crore",
        "equity_folios_crore",
        "debt_folios_crore",
        "hybrid_folios_crore",
        "others_folios_crore",
    ]
    for column in folio_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=["month"])
    for column in folio_columns:
        df = df[df[column].ge(0)]

    df = df.sort_values("month").reset_index(drop=True)

    save_to_sqlite(df, "fact_industry_folio_count")


def clean_portfolio_holdings() -> None:
    df = pd.read_csv(RAW_DIR / "09_portfolio_holdings.csv")
    df = clean_text_columns(df)
    df = df.drop_duplicates()

    df["stock_symbol"] = df["stock_symbol"].str.upper()
    df["portfolio_date"] = pd.to_datetime(df["portfolio_date"], errors="coerce")

    numeric_columns = ["amfi_code", "weight_pct", "market_value_cr", "current_price_inr"]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=["amfi_code", "stock_symbol", "portfolio_date"])
    df = df[df["weight_pct"].between(0, 100)]
    df = df[df["market_value_cr"].ge(0)]
    df = df[df["current_price_inr"].ge(0)]
    df = df.sort_values(["amfi_code", "portfolio_date", "weight_pct"], ascending=[True, True, False])
    df = df.reset_index(drop=True)

    save_to_sqlite(df, "fact_portfolio_holdings")


def clean_benchmark_indices() -> None:
    df = pd.read_csv(RAW_DIR / "10_benchmark_indices.csv")
    df = clean_text_columns(df)
    df = df.drop_duplicates()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["close_value"] = pd.to_numeric(df["close_value"], errors="coerce")

    df = df.dropna(subset=["date", "index_name", "close_value"])
    df = df[df["close_value"].gt(0)]
    df = df.sort_values(["index_name", "date"]).reset_index(drop=True)

    save_to_sqlite(df, "fact_benchmark_indices")


def main() -> None:
    clean_nav_history()
    clean_investor_transactions()
    clean_scheme_performance()
    clean_fund_master()
    clean_aum_by_fund_house()
    clean_monthly_sip_inflows()
    clean_category_inflows()
    clean_industry_folio_count()
    clean_portfolio_holdings()
    clean_benchmark_indices()


if __name__ == "__main__":
    main()
