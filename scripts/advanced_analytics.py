from __future__ import annotations

from pathlib import Path

import nbformat as nbf
import numpy as np
import pandas as pd

import matplotlib


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "processed"
PERFORMANCE_DIR = PROJECT_ROOT / "reports" / "performance_analytics"

VAR_CVAR_PATH = PROJECT_ROOT / "var_cvar_report.csv"
RECOMMENDER_PATH = PROJECT_ROOT / "recommender.py"
ROLLING_SHARPE_PATH = PROJECT_ROOT / "rolling_sharpe_chart.png"
NOTEBOOK_PATH = PROJECT_ROOT / "Advanced_Analytics.ipynb"

TRADING_DAYS = 252
ROLLING_WINDOW = 90
VAR_CONFIDENCE = 0.95


def load_inputs() -> dict[str, pd.DataFrame]:
    return {
        "nav": pd.read_csv(DATA_DIR / "nav_history_cleaned.csv", parse_dates=["date"]),
        "fund_master": pd.read_csv(DATA_DIR / "fund_master_cleaned.csv", parse_dates=["launch_date"]),
        "transactions": pd.read_csv(DATA_DIR / "investor_transactions_cleaned.csv", parse_dates=["transaction_date"]),
        "holdings": pd.read_csv(DATA_DIR / "portfolio_holdings_cleaned.csv", parse_dates=["portfolio_date"]),
        "scorecard": pd.read_csv(PERFORMANCE_DIR / "fund_scorecard.csv"),
    }


def compute_daily_returns(nav: pd.DataFrame) -> pd.DataFrame:
    nav_wide = nav.sort_values(["amfi_code", "date"]).pivot(index="date", columns="amfi_code", values="nav")
    return nav_wide.pct_change(fill_method=None)


def compute_var_cvar(returns: pd.DataFrame, fund_master: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for amfi_code in returns.columns:
        series = returns[amfi_code].dropna()
        var_95 = series.quantile(1 - VAR_CONFIDENCE)
        tail_returns = series[series < var_95]
        cvar_95 = tail_returns.mean() if not tail_returns.empty else series[series <= var_95].mean()
        rows.append(
            {
                "amfi_code": int(amfi_code),
                "observations": int(series.count()),
                "var_95_daily_return": var_95,
                "cvar_95_daily_return": cvar_95,
                "var_95_loss_pct": -var_95 * 100,
                "cvar_95_loss_pct": -cvar_95 * 100,
            }
        )

    report = pd.DataFrame(rows).merge(
        fund_master[
            [
                "amfi_code",
                "scheme_name",
                "fund_house",
                "category",
                "sub_category",
                "plan",
                "risk_category",
            ]
        ],
        on="amfi_code",
        how="left",
    )
    return report[
        [
            "amfi_code",
            "scheme_name",
            "fund_house",
            "category",
            "sub_category",
            "plan",
            "risk_category",
            "observations",
            "var_95_daily_return",
            "cvar_95_daily_return",
            "var_95_loss_pct",
            "cvar_95_loss_pct",
        ]
    ].sort_values("var_95_daily_return")


def plot_rolling_sharpe(returns: pd.DataFrame, fund_master: pd.DataFrame, scorecard: pd.DataFrame) -> list[int]:
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    top_funds = (
        scorecard.sort_values("fund_score", ascending=False)
        .head(5)["amfi_code"]
        .astype(int)
        .tolist()
    )
    rolling_sharpe = returns[top_funds].rolling(ROLLING_WINDOW).mean() / returns[top_funds].rolling(ROLLING_WINDOW).std()
    rolling_sharpe = rolling_sharpe * np.sqrt(TRADING_DAYS)

    name_map = fund_master.set_index("amfi_code")["scheme_name"].to_dict()
    label_map = {code: name_map.get(code, str(code)).replace(" - Regular - Growth", "").replace(" - Direct - Growth", "") for code in top_funds}

    plt.figure(figsize=(14, 7))
    for code in top_funds:
        plt.plot(rolling_sharpe.index, rolling_sharpe[code], linewidth=1.8, label=label_map[code])
    plt.axhline(0, color="#555555", linewidth=0.8, alpha=0.7)
    plt.title("Rolling 90-Day Sharpe Ratio - Top 5 Funds by Fund Score")
    plt.xlabel("Date")
    plt.ylabel("Rolling Sharpe Ratio")
    plt.legend(loc="best", fontsize=8)
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(ROLLING_SHARPE_PATH, dpi=180)
    plt.close()
    return top_funds


def compute_investor_cohorts(transactions: pd.DataFrame, fund_master: pd.DataFrame) -> pd.DataFrame:
    first_year = transactions.groupby("investor_id")["transaction_date"].min().dt.year.rename("first_transaction_year")
    enriched = transactions.merge(first_year, on="investor_id", how="left").merge(
        fund_master[["amfi_code", "scheme_name"]], on="amfi_code", how="left"
    )
    sip = enriched[enriched["transaction_type"].str.upper().eq("SIP")].copy()
    top_pref = (
        sip.groupby(["first_transaction_year", "scheme_name"])["amount_inr"]
        .sum()
        .reset_index()
        .sort_values(["first_transaction_year", "amount_inr"], ascending=[True, False])
        .drop_duplicates("first_transaction_year")
        .rename(columns={"scheme_name": "top_fund_preference", "amount_inr": "top_fund_sip_amount"})
    )
    cohort = (
        sip.groupby("first_transaction_year")
        .agg(
            investors=("investor_id", "nunique"),
            sip_transactions=("transaction_date", "count"),
            avg_sip_amount=("amount_inr", "mean"),
            total_invested=("amount_inr", "sum"),
        )
        .reset_index()
        .merge(top_pref, on="first_transaction_year", how="left")
        .sort_values("first_transaction_year")
    )
    return cohort


def compute_sip_continuity(transactions: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    sip = transactions[transactions["transaction_type"].str.upper().eq("SIP")].sort_values(["investor_id", "transaction_date"])
    sip_counts = sip.groupby("investor_id").size()
    eligible_ids = sip_counts[sip_counts >= 6].index
    eligible = sip[sip["investor_id"].isin(eligible_ids)].copy()
    eligible["gap_days"] = eligible.groupby("investor_id")["transaction_date"].diff().dt.days
    actual_counts = eligible.groupby("investor_id").size().rename("sip_transactions")
    continuity = (
        eligible.dropna(subset=["gap_days"])
        .groupby("investor_id")
        .agg(
            avg_gap_days=("gap_days", "mean"),
            max_gap_days=("gap_days", "max"),
            total_sip_amount=("amount_inr", "sum"),
        )
        .reset_index()
        .merge(actual_counts, on="investor_id", how="left")
    )
    continuity = continuity[["investor_id", "sip_transactions", "avg_gap_days", "max_gap_days", "total_sip_amount"]]
    continuity["status"] = np.where(continuity["avg_gap_days"] > 35, "at-risk", "continuous")
    summary = {
        "eligible_investors": float(continuity["investor_id"].nunique()),
        "at_risk_investors": float((continuity["status"] == "at-risk").sum()),
        "continuity_rate_pct": float((continuity["status"] == "continuous").mean() * 100),
        "avg_gap_days": float(continuity["avg_gap_days"].mean()),
    }
    return continuity.sort_values(["status", "avg_gap_days"], ascending=[False, False]), summary


def compute_sector_hhi(holdings: pd.DataFrame, fund_master: pd.DataFrame) -> pd.DataFrame:
    equity_codes = fund_master.loc[fund_master["category"].eq("Equity"), "amfi_code"]
    sector_weights = (
        holdings[holdings["amfi_code"].isin(equity_codes)]
        .groupby(["amfi_code", "sector"], as_index=False)["weight_pct"]
        .sum()
    )
    hhi = (
        sector_weights.assign(weight_share=lambda df: df["weight_pct"] / 100)
        .assign(weight_squared=lambda df: df["weight_share"] ** 2)
        .groupby("amfi_code", as_index=False)["weight_squared"]
        .sum()
        .rename(columns={"weight_squared": "sector_hhi"})
        .merge(
            fund_master[["amfi_code", "scheme_name", "fund_house", "sub_category", "risk_category"]],
            on="amfi_code",
            how="left",
        )
        .sort_values("sector_hhi", ascending=False)
    )
    return hhi


def recommendation_table(scorecard: pd.DataFrame, fund_master: pd.DataFrame, appetite: str) -> pd.DataFrame:
    risk_map = {
        "low": ["Low"],
        "moderate": ["Moderate"],
        "high": ["High", "Very High"],
    }
    key = appetite.strip().lower()
    if key not in risk_map:
        raise ValueError("Risk appetite must be Low, Moderate, or High.")

    merged = scorecard.merge(fund_master[["amfi_code", "risk_category"]], on="amfi_code", how="left")
    return (
        merged[merged["risk_category"].isin(risk_map[key])]
        .sort_values("sharpe_ratio", ascending=False)
        .head(3)[
            [
                "amfi_code",
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
    )


def write_recommender() -> None:
    RECOMMENDER_PATH.write_text(
        '''from __future__ import annotations

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
    print("\\nTop 3 fund recommendations by Sharpe ratio\\n")
    print(table.to_string(index=False, formatters={
        "sharpe_ratio": "{:.3f}".format,
        "annualized_return": "{:.2%}".format,
        "annualized_volatility": "{:.2%}".format,
        "fund_score": "{:.2f}".format,
    }))


if __name__ == "__main__":
    main()
''',
        encoding="utf-8",
    )


def money(value: float) -> str:
    return f"Rs {value:,.0f}"


def pct(value: float) -> str:
    return f"{value:.2f}%"


def write_notebook(
    var_cvar: pd.DataFrame,
    cohorts: pd.DataFrame,
    continuity: pd.DataFrame,
    continuity_summary: dict[str, float],
    hhi: pd.DataFrame,
    recommendations: pd.DataFrame,
    top_funds: list[int],
) -> None:
    highest_var = var_cvar.iloc[0]
    highest_cvar = var_cvar.sort_values("cvar_95_daily_return").iloc[0]
    top_cohort = cohorts.sort_values("total_invested", ascending=False).iloc[0]
    highest_hhi = hhi.iloc[0]
    lowest_hhi = hhi.iloc[-1]
    at_risk_rate = 100 - continuity_summary["continuity_rate_pct"]
    top_continuity = continuity.head(10)

    md_insights = f"""
## Advanced Insights

1. **Highest daily VaR risk:** {highest_var['scheme_name']} has the deepest 95% historical VaR at {highest_var['var_95_daily_return']:.4%}, implying a one-day tail loss of about {highest_var['var_95_loss_pct']:.2f}% at the 5th percentile.
2. **Worst expected tail loss:** {highest_cvar['scheme_name']} has the weakest CVaR at {highest_cvar['cvar_95_daily_return']:.4%}, meaning days beyond its VaR threshold averaged a {highest_cvar['cvar_95_loss_pct']:.2f}% loss.
3. **Largest investor cohort:** Investors whose first transaction year was {int(top_cohort['first_transaction_year'])} invested the most via SIPs, with {money(top_cohort['total_invested'])} total SIP investment and average SIP size of {money(top_cohort['avg_sip_amount'])}.
4. **SIP continuity:** Among investors with at least 6 SIP transactions, the continuity rate is {continuity_summary['continuity_rate_pct']:.2f}%; {at_risk_rate:.2f}% are flagged as at-risk because their average SIP gap is above 35 days.
5. **Sector concentration:** {highest_hhi['scheme_name']} is the most concentrated equity portfolio with HHI {highest_hhi['sector_hhi']:.4f}, while {lowest_hhi['scheme_name']} is the most diversified among equity funds with HHI {lowest_hhi['sector_hhi']:.4f}.
"""

    nb = nbf.v4.new_notebook()
    nb["cells"] = [
        nbf.v4.new_markdown_cell("# Advanced Mutual Fund Analytics"),
        nbf.v4.new_markdown_cell(
            "This notebook computes 95% Historical VaR/CVaR, rolling 90-day Sharpe, investor cohorts, SIP continuity, a simple Sharpe-based recommender, and sector HHI concentration."
        ),
        nbf.v4.new_code_cell(
            """from pathlib import Path
import numpy as np
import pandas as pd
from IPython.display import display

ROOT = Path.cwd()
var_cvar = pd.read_csv(ROOT / "var_cvar_report.csv")
fund_master = pd.read_csv(ROOT / "data" / "processed" / "fund_master_cleaned.csv")
transactions = pd.read_csv(ROOT / "data" / "processed" / "investor_transactions_cleaned.csv", parse_dates=["transaction_date"])
holdings = pd.read_csv(ROOT / "data" / "processed" / "portfolio_holdings_cleaned.csv")
scorecard = pd.read_csv(ROOT / "reports" / "performance_analytics" / "fund_scorecard.csv")
display(var_cvar.head())"""
        ),
        nbf.v4.new_markdown_cell("## Historical VaR and CVaR"),
        nbf.v4.new_code_cell(
            """display(
    var_cvar.sort_values("var_95_daily_return")
    .head(10)
    [["scheme_name", "risk_category", "var_95_daily_return", "cvar_95_daily_return", "var_95_loss_pct", "cvar_95_loss_pct"]]
)"""
        ),
        nbf.v4.new_markdown_cell("## Rolling 90-Day Sharpe"),
        nbf.v4.new_code_cell(
            f"""from IPython.display import Image
top_5_rolling_sharpe_amfi_codes = {top_funds}
Image(filename="rolling_sharpe_chart.png")"""
        ),
        nbf.v4.new_markdown_cell("## Investor Cohort Analysis"),
        nbf.v4.new_code_cell(f"display(pd.DataFrame({cohorts.to_dict(orient='records')}))"),
        nbf.v4.new_markdown_cell("## SIP Continuity Analysis"),
        nbf.v4.new_code_cell(
            f"""sip_continuity_summary = {continuity_summary}
display(pd.DataFrame([sip_continuity_summary]))
display(pd.DataFrame({top_continuity.to_dict(orient='records')}))"""
        ),
        nbf.v4.new_markdown_cell("## Simple Fund Recommender"),
        nbf.v4.new_code_cell(f"display(pd.DataFrame({recommendations.to_dict(orient='records')}))"),
        nbf.v4.new_markdown_cell("## Sector HHI Concentration"),
        nbf.v4.new_code_cell(f"display(pd.DataFrame({hhi.to_dict(orient='records')}))"),
        nbf.v4.new_markdown_cell(md_insights),
    ]
    nbf.write(nb, NOTEBOOK_PATH)


def main() -> None:
    inputs = load_inputs()
    returns = compute_daily_returns(inputs["nav"])
    var_cvar = compute_var_cvar(returns, inputs["fund_master"])
    var_cvar.to_csv(VAR_CVAR_PATH, index=False)

    top_funds = plot_rolling_sharpe(returns, inputs["fund_master"], inputs["scorecard"])
    cohorts = compute_investor_cohorts(inputs["transactions"], inputs["fund_master"])
    continuity, continuity_summary = compute_sip_continuity(inputs["transactions"])
    hhi = compute_sector_hhi(inputs["holdings"], inputs["fund_master"])
    recommendations = recommendation_table(inputs["scorecard"], inputs["fund_master"], "Moderate")

    write_recommender()
    write_notebook(var_cvar, cohorts, continuity, continuity_summary, hhi, recommendations, top_funds)

    print(f"Wrote {VAR_CVAR_PATH.name}: {len(var_cvar)} schemes")
    print(f"Wrote {ROLLING_SHARPE_PATH.name}: {len(top_funds)} funds")
    print(f"Wrote {RECOMMENDER_PATH.name}")
    print(f"Wrote {NOTEBOOK_PATH.name}")
    print(f"SIP continuity rate: {continuity_summary['continuity_rate_pct']:.2f}%")


if __name__ == "__main__":
    main()
