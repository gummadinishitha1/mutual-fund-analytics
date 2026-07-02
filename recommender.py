from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent
FUND_MASTER_PATH = PROJECT_ROOT / "data" / "processed" / "fund_master_cleaned.csv"
SCORECARD_PATH = PROJECT_ROOT / "reports" / "performance_analytics" / "fund_scorecard.csv"

RISK_MAP = {
    "low": ["Low"],
    "moderate": ["Moderate"],
    "high": ["High", "Very High"],
}


def recommend(risk_appetite: str) -> pd.DataFrame:
    key = risk_appetite.strip().lower()
    if key not in RISK_MAP:
        raise ValueError("Risk appetite must be Low, Moderate, or High.")

    fund_master = pd.read_csv(FUND_MASTER_PATH)
    scorecard = pd.read_csv(SCORECARD_PATH)
    funds = scorecard.merge(fund_master[["amfi_code", "risk_category"]], on="amfi_code", how="left")

    table = (
        funds[funds["risk_category"].isin(RISK_MAP[key])]
        .sort_values("sharpe_ratio", ascending=False)
        .head(3)[
            [
                "scheme_name",
                "fund_house",
                "category",
                "sub_category",
                "risk_category",
                "sharpe_ratio",
                "annualized_return",
                "annualized_volatility",
                "fund_score",
            ]
        ]
        .reset_index(drop=True)
    )
    return table


def main() -> None:
    appetite = input("Enter risk appetite (Low / Moderate / High): ")
    table = recommend(appetite)
    print("\nTop 3 fund recommendations by Sharpe ratio\n")
    print(table.to_string(index=False, formatters={
        "sharpe_ratio": "{:.3f}".format,
        "annualized_return": "{:.2%}".format,
        "annualized_volatility": "{:.2%}".format,
        "fund_score": "{:.2f}".format,
    }))


if __name__ == "__main__":
    main()
