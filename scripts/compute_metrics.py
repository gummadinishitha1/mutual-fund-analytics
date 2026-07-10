from __future__ import annotations

from pathlib import Path
import os

import nbformat as nbf
import numpy as np
import pandas as pd

try:
    from scipy.stats import linregress as scipy_linregress
except ModuleNotFoundError:
    scipy_linregress = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "reports" / "performance_analytics"
NOTEBOOK_PATH = PROJECT_ROOT / "notebooks" / "Performance_Analytics.ipynb"

os.environ.setdefault("MPLCONFIGDIR", str(OUTPUT_DIR / ".matplotlib"))
import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

TRADING_DAYS = 252
RISK_FREE_RATE = 0.065
BENCHMARK_FOR_REGRESSION = "NIFTY100"
COMPARISON_BENCHMARKS = ["NIFTY50", "NIFTY100"]


class RegressionResult:
    def __init__(self, slope: float, intercept: float, rvalue: float, pvalue: float) -> None:
        self.slope = slope
        self.intercept = intercept
        self.rvalue = rvalue
        self.pvalue = pvalue


def run_linregress(x: pd.Series, y: pd.Series):
    if scipy_linregress is not None:
        return scipy_linregress(x, y)

    x_values = x.to_numpy(dtype=float)
    y_values = y.to_numpy(dtype=float)
    slope, intercept = np.polyfit(x_values, y_values, 1)
    rvalue = np.corrcoef(x_values, y_values)[0, 1]
    return RegressionResult(slope=slope, intercept=intercept, rvalue=rvalue, pvalue=np.nan)


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    nav = pd.read_csv(DATA_DIR / "nav_history_cleaned.csv", parse_dates=["date"])
    benchmarks = pd.read_csv(DATA_DIR / "benchmark_indices_cleaned.csv", parse_dates=["date"])
    fund_master = pd.read_csv(DATA_DIR / "fund_master_cleaned.csv")

    nav = nav.sort_values(["amfi_code", "date"]).copy()
    benchmarks = benchmarks.sort_values(["index_name", "date"]).copy()
    return nav, benchmarks, fund_master


def compute_returns(nav: pd.DataFrame, benchmarks: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    nav_wide = nav.pivot(index="date", columns="amfi_code", values="nav").sort_index()
    fund_returns = nav_wide.pct_change()

    benchmark_wide = benchmarks.pivot(index="date", columns="index_name", values="close_value").sort_index()
    benchmark_returns = benchmark_wide.pct_change()

    daily_return_long = (
        fund_returns.stack()
        .rename("daily_return")
        .reset_index()
        .sort_values(["amfi_code", "date"])
    )
    return nav_wide, fund_returns, benchmark_wide, benchmark_returns, daily_return_long


def distribution_check(daily_return_long: pd.DataFrame) -> pd.DataFrame:
    grouped = daily_return_long.groupby("amfi_code")["daily_return"]
    summary = grouped.agg(["count", "mean", "std", "min", "max", "skew"]).reset_index()
    summary["p01"] = grouped.quantile(0.01).values
    summary["p05"] = grouped.quantile(0.05).values
    summary["p95"] = grouped.quantile(0.95).values
    summary["p99"] = grouped.quantile(0.99).values
    summary["abs_return_gt_10pct_days"] = grouped.apply(lambda s: (s.abs() > 0.10).sum()).values
    summary["looks_reasonable"] = (
        (summary["std"].between(0, 0.10, inclusive="neither"))
        & (summary["min"] > -0.50)
        & (summary["max"] < 0.50)
        & (summary["abs_return_gt_10pct_days"] == 0)
    )
    return summary


def nearest_nav_on_or_after(series: pd.Series, target_date: pd.Timestamp) -> float:
    eligible = series.loc[series.index >= target_date].dropna()
    return np.nan if eligible.empty else float(eligible.iloc[0])


def compute_cagr(nav_wide: pd.DataFrame, fund_master: pd.DataFrame) -> pd.DataFrame:
    end_date = nav_wide.index.max()
    records = []

    for amfi_code, series in nav_wide.items():
        clean = series.dropna()
        end_nav = float(clean.iloc[-1])
        record = {
            "amfi_code": amfi_code,
            "start_date_available": clean.index.min().date().isoformat(),
            "end_date": end_date.date().isoformat(),
            "end_nav": end_nav,
        }

        for years in [1, 3, 5]:
            target = end_date - pd.DateOffset(years=years)
            start_nav = nearest_nav_on_or_after(clean, target)
            has_full_period = clean.index.min() <= target
            cagr = (end_nav / start_nav) ** (1 / years) - 1 if has_full_period and start_nav > 0 else np.nan
            record[f"cagr_{years}yr"] = cagr
            record[f"cagr_{years}yr_start_nav"] = start_nav
            record[f"cagr_{years}yr_has_full_period"] = has_full_period

        records.append(record)

    cagr = pd.DataFrame(records)
    return cagr.merge(
        fund_master[["amfi_code", "scheme_name", "fund_house", "category", "sub_category", "plan", "expense_ratio_pct"]],
        on="amfi_code",
        how="left",
    )


def downside_std(series: pd.Series) -> float:
    downside = series[series < 0].dropna()
    return float(downside.std(ddof=1)) if len(downside) > 1 else np.nan


def max_drawdown_details(nav_series: pd.Series) -> tuple[float, pd.Timestamp, pd.Timestamp]:
    clean = nav_series.dropna()
    running_max = clean.cummax()
    drawdown = clean / running_max - 1
    trough_date = drawdown.idxmin()
    peak_date = clean.loc[:trough_date].idxmax()
    return float(drawdown.loc[trough_date]), peak_date, trough_date


def compute_metrics(
    nav_wide: pd.DataFrame,
    fund_returns: pd.DataFrame,
    benchmark_returns: pd.DataFrame,
    cagr: pd.DataFrame,
    fund_master: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rf_daily = RISK_FREE_RATE / TRADING_DAYS
    nifty100 = benchmark_returns[BENCHMARK_FOR_REGRESSION]
    records = []

    for amfi_code, returns in fund_returns.items():
        clean_returns = returns.dropna()
        sharpe = ((clean_returns.mean() - rf_daily) / clean_returns.std(ddof=1)) * np.sqrt(TRADING_DAYS)
        sortino = ((clean_returns.mean() - rf_daily) / downside_std(clean_returns)) * np.sqrt(TRADING_DAYS)

        aligned = pd.concat(
            [clean_returns.rename("fund_return"), nifty100.rename("benchmark_return")],
            axis=1,
            sort=False,
        ).dropna()
        if len(aligned) > 2:
            regression = run_linregress(aligned["benchmark_return"], aligned["fund_return"])
            beta = regression.slope
            alpha = regression.intercept * TRADING_DAYS
            r_value = regression.rvalue
            p_value = regression.pvalue
        else:
            beta = alpha = r_value = p_value = np.nan

        max_dd, peak_date, trough_date = max_drawdown_details(nav_wide[amfi_code])

        records.append(
            {
                "amfi_code": amfi_code,
                "annualized_return": clean_returns.mean() * TRADING_DAYS,
                "annualized_volatility": clean_returns.std(ddof=1) * np.sqrt(TRADING_DAYS),
                "sharpe_ratio": sharpe,
                "sortino_ratio": sortino,
                "alpha": alpha,
                "beta": beta,
                "r_squared": r_value**2 if pd.notna(r_value) else np.nan,
                "regression_p_value": p_value,
                "max_drawdown": max_dd,
                "max_drawdown_peak_date": peak_date.date().isoformat(),
                "max_drawdown_trough_date": trough_date.date().isoformat(),
            }
        )

    metrics = pd.DataFrame(records)
    metrics = metrics.merge(
        fund_master[["amfi_code", "scheme_name", "fund_house", "category", "sub_category", "plan", "expense_ratio_pct"]],
        on="amfi_code",
        how="left",
    ).merge(
        cagr[["amfi_code", "cagr_1yr", "cagr_3yr", "cagr_5yr"]],
        on="amfi_code",
        how="left",
    )

    alpha_beta = metrics[
        [
            "amfi_code",
            "scheme_name",
            "fund_house",
            "category",
            "sub_category",
            "plan",
            "alpha",
            "beta",
            "r_squared",
            "regression_p_value",
        ]
    ].sort_values("alpha", ascending=False)
    return metrics, alpha_beta


def score_from_rank(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    rank = series.rank(ascending=not higher_is_better, method="min", na_option="bottom")
    n = series.notna().sum()
    if n <= 1:
        return pd.Series(np.where(series.notna(), 100.0, np.nan), index=series.index)
    return (n - rank) / (n - 1) * 100


def build_scorecard(metrics: pd.DataFrame) -> pd.DataFrame:
    scorecard = metrics.copy()
    scorecard["score_3yr_return"] = score_from_rank(scorecard["cagr_3yr"], higher_is_better=True)
    scorecard["score_sharpe"] = score_from_rank(scorecard["sharpe_ratio"], higher_is_better=True)
    scorecard["score_alpha"] = score_from_rank(scorecard["alpha"], higher_is_better=True)
    scorecard["score_expense_ratio"] = score_from_rank(scorecard["expense_ratio_pct"], higher_is_better=False)
    scorecard["score_max_drawdown"] = score_from_rank(scorecard["max_drawdown"], higher_is_better=True)
    scorecard["fund_score"] = (
        0.30 * scorecard["score_3yr_return"]
        + 0.25 * scorecard["score_sharpe"]
        + 0.20 * scorecard["score_alpha"]
        + 0.15 * scorecard["score_expense_ratio"]
        + 0.10 * scorecard["score_max_drawdown"]
    )

    output_columns = [
        "amfi_code",
        "scheme_name",
        "fund_house",
        "category",
        "sub_category",
        "plan",
        "fund_score",
        "cagr_1yr",
        "cagr_3yr",
        "cagr_5yr",
        "sharpe_ratio",
        "sortino_ratio",
        "alpha",
        "beta",
        "expense_ratio_pct",
        "max_drawdown",
        "max_drawdown_peak_date",
        "max_drawdown_trough_date",
        "annualized_return",
        "annualized_volatility",
        "score_3yr_return",
        "score_sharpe",
        "score_alpha",
        "score_expense_ratio",
        "score_max_drawdown",
    ]
    return scorecard[output_columns].sort_values("fund_score", ascending=False)


def compute_tracking_error(
    fund_returns: pd.DataFrame,
    benchmark_returns: pd.DataFrame,
    top_funds: list[int],
) -> pd.DataFrame:
    records = []
    for amfi_code in top_funds:
        for benchmark in COMPARISON_BENCHMARKS:
            aligned = pd.concat(
                [
                    fund_returns[amfi_code].rename("fund_return"),
                    benchmark_returns[benchmark].rename("benchmark_return"),
                ],
                axis=1,
                sort=False,
            ).dropna()
            active_return = aligned["fund_return"] - aligned["benchmark_return"]
            records.append(
                {
                    "amfi_code": amfi_code,
                    "benchmark": benchmark,
                    "tracking_error": active_return.std(ddof=1) * np.sqrt(TRADING_DAYS),
                    "observations": len(active_return),
                }
            )
    return pd.DataFrame(records)


def make_benchmark_chart(
    nav_wide: pd.DataFrame,
    benchmark_wide: pd.DataFrame,
    scorecard: pd.DataFrame,
    fund_master: pd.DataFrame,
) -> tuple[Path, pd.DataFrame]:
    top_funds = scorecard.head(5)["amfi_code"].tolist()
    end_date = nav_wide.index.max()
    start_date = end_date - pd.DateOffset(years=3)

    fund_series = nav_wide.loc[nav_wide.index >= start_date, top_funds]
    benchmark_series = benchmark_wide.loc[benchmark_wide.index >= start_date, COMPARISON_BENCHMARKS]

    indexed_funds = fund_series.divide(fund_series.iloc[0]).mul(100)
    indexed_benchmarks = benchmark_series.divide(benchmark_series.iloc[0]).mul(100)

    names = fund_master.set_index("amfi_code")["scheme_name"].to_dict()
    plot_df = indexed_funds.rename(columns=names).join(indexed_benchmarks)

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(13, 7.5))
    colors = ["#1565c0", "#2e7d32", "#ef6c00", "#6a1b9a", "#00838f", "#424242", "#9e9e9e"]
    for idx, column in enumerate(plot_df.columns):
        linewidth = 2.4 if column in COMPARISON_BENCHMARKS else 1.9
        linestyle = "--" if column in COMPARISON_BENCHMARKS else "-"
        ax.plot(plot_df.index, plot_df[column], label=column, linewidth=linewidth, linestyle=linestyle, color=colors[idx])

    ax.set_title("Top 5 Fund Scorecard Leaders vs Nifty 50 and Nifty 100, Indexed to 100", fontsize=14, pad=14)
    ax.set_xlabel("Date")
    ax.set_ylabel("Indexed value")
    ax.legend(loc="upper left", fontsize=8, frameon=True)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()

    chart_path = OUTPUT_DIR / "benchmark_comparison_top5.png"
    fig.savefig(chart_path, dpi=180)
    plt.close(fig)
    return chart_path, plot_df


def write_notebook() -> None:
    notebook = nbf.v4.new_notebook()
    notebook.cells = [
        nbf.v4.new_markdown_cell(
            "# Fund Performance Analytics\n\n"
            "This notebook computes daily returns, CAGR, Sharpe, Sortino, alpha/beta, maximum drawdown, "
            "a 0-100 composite scorecard, benchmark tracking error, and a top-5 benchmark comparison chart."
        ),
        nbf.v4.new_code_cell(
            "from pathlib import Path\n"
            "import sys\n\n"
            "PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()\n"
            "sys.path.append(str(PROJECT_ROOT / 'src'))\n\n"
            "from performance_analytics import run_analysis\n\n"
            "results = run_analysis()\n"
            "results"
        ),
        nbf.v4.new_markdown_cell("## Top Fund Scorecard"),
        nbf.v4.new_code_cell(
            "import pandas as pd\n\n"
            "scorecard = pd.read_csv(PROJECT_ROOT / 'reports' / 'performance_analytics' / 'fund_scorecard.csv')\n"
            "scorecard.head(10)"
        ),
        nbf.v4.new_markdown_cell("## Alpha and Beta"),
        nbf.v4.new_code_cell(
            "alpha_beta = pd.read_csv(PROJECT_ROOT / 'reports' / 'performance_analytics' / 'alpha_beta.csv')\n"
            "alpha_beta.head(10)"
        ),
        nbf.v4.new_markdown_cell("## Daily Return Distribution Validation"),
        nbf.v4.new_code_cell(
            "distribution = pd.read_csv(PROJECT_ROOT / 'reports' / 'performance_analytics' / 'daily_return_distribution.csv')\n"
            "distribution[['amfi_code', 'count', 'mean', 'std', 'min', 'max', 'p01', 'p99', 'looks_reasonable']].head()"
        ),
        nbf.v4.new_markdown_cell("## CAGR Comparison"),
        nbf.v4.new_code_cell(
            "cagr = pd.read_csv(PROJECT_ROOT / 'reports' / 'performance_analytics' / 'cagr_comparison.csv')\n"
            "cagr[['scheme_name', 'cagr_1yr', 'cagr_3yr', 'cagr_5yr', 'cagr_5yr_has_full_period']].head(10)"
        ),
        nbf.v4.new_markdown_cell("## Tracking Error"),
        nbf.v4.new_code_cell(
            "tracking_error = pd.read_csv(PROJECT_ROOT / 'reports' / 'performance_analytics' / 'tracking_error_top5.csv')\n"
            "tracking_error"
        ),
    ]
    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(notebook, NOTEBOOK_PATH)


def run_analysis() -> dict[str, str]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    nav, benchmarks, fund_master = load_data()
    nav_wide, fund_returns, benchmark_wide, benchmark_returns, daily_return_long = compute_returns(nav, benchmarks)

    distribution = distribution_check(daily_return_long)
    cagr = compute_cagr(nav_wide, fund_master)
    metrics, alpha_beta = compute_metrics(nav_wide, fund_returns, benchmark_returns, cagr, fund_master)
    scorecard = build_scorecard(metrics)

    top_funds = scorecard.head(5)["amfi_code"].tolist()
    tracking_error = compute_tracking_error(fund_returns, benchmark_returns, top_funds)
    tracking_error = tracking_error.merge(
        fund_master[["amfi_code", "scheme_name", "fund_house"]],
        on="amfi_code",
        how="left",
    )[["amfi_code", "scheme_name", "fund_house", "benchmark", "tracking_error", "observations"]]
    chart_path, _ = make_benchmark_chart(nav_wide, benchmark_wide, scorecard, fund_master)

    daily_return_long.to_csv(OUTPUT_DIR / "daily_returns.csv", index=False)
    distribution.to_csv(OUTPUT_DIR / "daily_return_distribution.csv", index=False)
    cagr.sort_values("cagr_3yr", ascending=False).to_csv(OUTPUT_DIR / "cagr_comparison.csv", index=False)
    alpha_beta.to_csv(OUTPUT_DIR / "alpha_beta.csv", index=False)
    scorecard.to_csv(OUTPUT_DIR / "fund_scorecard.csv", index=False)
    tracking_error.to_csv(OUTPUT_DIR / "tracking_error_top5.csv", index=False)

    write_notebook()

    return {
        "notebook": str(NOTEBOOK_PATH.relative_to(PROJECT_ROOT)),
        "fund_scorecard": str((OUTPUT_DIR / "fund_scorecard.csv").relative_to(PROJECT_ROOT)),
        "alpha_beta": str((OUTPUT_DIR / "alpha_beta.csv").relative_to(PROJECT_ROOT)),
        "benchmark_chart": str(chart_path.relative_to(PROJECT_ROOT)),
    }


if __name__ == "__main__":
    outputs = run_analysis()
    for name, path in outputs.items():
        print(f"{name}: {path}")
