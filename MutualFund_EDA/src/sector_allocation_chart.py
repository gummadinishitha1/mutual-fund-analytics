"""Generate an equity-fund sector allocation donut chart.

The chart joins portfolio holdings to fund master data, filters to equity funds,
aggregates sector market value across those funds, and writes a donut PNG.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"


def build_sector_allocation(
    holdings_path: Path,
    fund_master_path: Path,
    top_n: int,
) -> pd.DataFrame:
    holdings = pd.read_csv(holdings_path)
    funds = pd.read_csv(fund_master_path)

    required_holdings = {"amfi_code", "sector", "market_value_cr"}
    required_funds = {"amfi_code", "category"}
    missing = required_holdings - set(holdings.columns)
    missing |= required_funds - set(funds.columns)
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))

    merged = holdings.merge(
        funds[["amfi_code", "category", "sub_category", "scheme_name"]],
        on="amfi_code",
        how="inner",
    )
    equity = merged[
        merged["category"].astype(str).str.contains("equity", case=False, na=False)
    ].copy()
    equity["market_value_cr"] = pd.to_numeric(equity["market_value_cr"], errors="coerce")
    equity = equity.dropna(subset=["sector", "market_value_cr"])
    if equity.empty:
        raise ValueError("No equity fund holdings found after joining holdings to fund master.")

    sector = (
        equity.groupby("sector", as_index=False)
        .agg(market_value_cr=("market_value_cr", "sum"))
        .sort_values("market_value_cr", ascending=False)
    )
    if len(sector) > top_n:
        top = sector.head(top_n).copy()
        other = pd.DataFrame(
            {
                "sector": ["Others"],
                "market_value_cr": [sector.iloc[top_n:]["market_value_cr"].sum()],
            }
        )
        sector = pd.concat([top, other], ignore_index=True)
    sector["allocation_pct"] = sector["market_value_cr"] / sector["market_value_cr"].sum() * 100
    return sector


def plot_sector_donut(sector: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 8))
    colors = plt.get_cmap("tab20").colors[: len(sector)]
    wedges, _, autotexts = ax.pie(
        sector["market_value_cr"],
        labels=sector["sector"],
        autopct=lambda pct: f"{pct:.1f}%" if pct >= 3 else "",
        startangle=90,
        colors=colors,
        pctdistance=0.78,
        labeldistance=1.06,
        wedgeprops={"width": 0.42, "edgecolor": "white", "linewidth": 1.2},
    )
    for text in autotexts:
        text.set_fontsize(9)
        text.set_color("#222222")
    ax.set_title("Sector Allocation Across Equity Fund Holdings")
    ax.text(
        0,
        0,
        "Equity\nFunds",
        ha="center",
        va="center",
        fontsize=16,
        fontweight="bold",
        color="#333333",
    )
    ax.legend(
        wedges,
        sector["sector"],
        title="Sector",
        loc="center left",
        bbox_to_anchor=(1.18, 0.5),
        fontsize=9,
    )
    fig.subplots_adjust(right=0.72)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--holdings-input", type=Path, default=DATA_DIR / "09_portfolio_holdings.csv")
    parser.add_argument("--fund-master-input", type=Path, default=DATA_DIR / "01_fund_master.csv")
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR / "sector_allocation_donut.png")
    parser.add_argument("--top-n", type=int, default=10)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        sector = build_sector_allocation(args.holdings_input, args.fund_master_input, args.top_n)
        plot_sector_donut(sector, args.output)
    except (FileNotFoundError, ValueError) as exc:
        raise SystemExit(f"Error: {exc}") from None


if __name__ == "__main__":
    main()
