from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from textwrap import shorten

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch, Rectangle
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "bluestock_mf.db"
OUT_DIR = ROOT / "reports" / "dashboard"
PNG_DIR = OUT_DIR / "png"

BLUE = "#0A4D8F"
CYAN = "#22A7F0"
NAVY = "#082B4C"
INK = "#162033"
MUTED = "#5B6B7F"
GRID = "#D7E2EE"
BG = "#F4F8FC"
CARD = "#FFFFFF"
GREEN = "#22A06B"
ORANGE = "#F5A524"
RED = "#D64545"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "axes.titlesize": 13,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "figure.facecolor": BG,
        "axes.facecolor": CARD,
        "axes.edgecolor": "#D8E3EF",
        "axes.titleweight": "bold",
        "savefig.facecolor": BG,
    }
)


def read_table(conn: sqlite3.Connection, table: str) -> pd.DataFrame:
    return pd.read_sql_query(f'SELECT * FROM "{table}"', conn)


def load_data() -> dict[str, pd.DataFrame]:
    with sqlite3.connect(DB_PATH) as conn:
        tables = [
            "dim_fund",
            "fact_aum_by_fund_house",
            "fact_benchmark_indices",
            "fact_category_inflows",
            "fact_industry_folio_count",
            "fact_monthly_sip_inflows",
            "fact_nav",
            "fact_performance",
            "fact_portfolio_holdings",
            "fact_transactions",
        ]
        data = {name: read_table(conn, name) for name in tables}

    for name, frame in data.items():
        for col in ["date", "month", "transaction_date", "portfolio_date"]:
            if col in frame.columns:
                frame[col] = pd.to_datetime(frame[col])
    return data


def style_axis(ax, grid_axis: str = "y") -> None:
    ax.grid(True, axis=grid_axis, color=GRID, linewidth=0.8, alpha=0.8)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color("#D8E3EF")
    ax.tick_params(colors=MUTED)
    ax.title.set_color(INK)
    ax.xaxis.label.set_color(MUTED)
    ax.yaxis.label.set_color(MUTED)


def year_ticks(ax) -> None:
    ticks = pd.to_datetime(["2022-01-01", "2023-01-01", "2024-01-01", "2025-01-01"])
    ax.set_xticks(ticks)
    ax.set_xlim(pd.Timestamp("2022-01-01"), pd.Timestamp("2025-12-31"))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))


def add_header(fig, title: str, subtitle: str) -> None:
    fig.text(0.035, 0.965, "Bluestock", color=BLUE, fontsize=18, fontweight="bold", va="top")
    fig.text(0.127, 0.963, "Mutual Fund Analytics", color=NAVY, fontsize=10, va="top")
    fig.text(0.035, 0.925, title, color=INK, fontsize=23, fontweight="bold", va="top")
    fig.text(0.035, 0.893, subtitle, color=MUTED, fontsize=10, va="top")
    fig.add_artist(Rectangle((0.035, 0.875), 0.93, 0.004, transform=fig.transFigure, color=CYAN, alpha=0.95))


def card(fig, x: float, y: float, w: float, h: float, title: str, value: str, note: str, color: str = BLUE) -> None:
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.006,rounding_size=0.008",
        transform=fig.transFigure,
        facecolor=CARD,
        edgecolor="#D9E6F2",
        linewidth=1.0,
    )
    fig.add_artist(patch)
    fig.text(x + 0.018, y + h - 0.027, title.upper(), color=MUTED, fontsize=8, fontweight="bold", va="top")
    fig.text(x + 0.018, y + 0.044, value, color=color, fontsize=17.5, fontweight="bold", va="center")
    fig.text(x + 0.018, y + 0.012, note, color=MUTED, fontsize=7.2, va="bottom")


def add_footer(fig, page: str, filters: str) -> None:
    fig.text(0.035, 0.022, page, color=MUTED, fontsize=8)
    fig.text(0.965, 0.022, filters, color=MUTED, fontsize=8, ha="right")


def save_fig(fig, name: str) -> Path:
    path = PNG_DIR / name
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def nifty_50(bench: pd.DataFrame) -> pd.DataFrame:
    normalized = bench["index_name"].str.upper().str.replace("_", "", regex=False)
    return bench[normalized.eq("NIFTY50")].sort_values("date")


def industry_page(data: dict[str, pd.DataFrame]) -> Path:
    aum = data["fact_aum_by_fund_house"].copy()
    sip = data["fact_monthly_sip_inflows"].copy()
    folios = data["fact_industry_folio_count"].copy()
    period_end = pd.Timestamp("2025-12-31")
    aum = aum[aum["date"] <= period_end]
    sip = sip[sip["month"] <= period_end]
    folios = folios[folios["month"] <= period_end]

    latest_aum = aum[aum["date"] == aum["date"].max()].copy()

    fig = plt.figure(figsize=(16, 9), constrained_layout=False)
    add_header(fig, "Industry Overview", "AUM, SIP, folios, and AMC concentration across 2022-2025")
    card(fig, 0.035, 0.745, 0.21, 0.105, "Total AUM", "Rs 81L Cr", "Industry headline KPI")
    card(fig, 0.275, 0.745, 0.21, 0.105, "SIP Inflows", "Rs 31K Cr", "Monthly SIP inflow KPI")
    card(fig, 0.515, 0.745, 0.21, 0.105, "Folios", "26.12 Cr", "Total investor folios")
    card(fig, 0.755, 0.745, 0.21, 0.105, "Schemes", "1,908", "Industry scheme count")

    ax1 = fig.add_axes([0.055, 0.43, 0.56, 0.25])
    trend = aum.groupby("date", as_index=False)["aum_lakh_crore"].sum()
    ax1.plot(trend["date"], trend["aum_lakh_crore"], color=BLUE, linewidth=2.8, marker="o", markersize=4)
    ax1.fill_between(trend["date"], trend["aum_lakh_crore"], color=CYAN, alpha=0.13)
    ax1.set_title("Industry AUM Trend")
    ax1.set_ylabel("Lakh crore")
    year_ticks(ax1)
    style_axis(ax1)

    ax2 = fig.add_axes([0.66, 0.43, 0.29, 0.25])
    top_amc = latest_aum.sort_values("aum_crore", ascending=True).tail(10)
    ax2.barh(top_amc["fund_house"], top_amc["aum_lakh_crore"], color=BLUE)
    ax2.set_title("AUM by AMC")
    ax2.set_xlabel("Lakh crore")
    style_axis(ax2, "x")

    ax3 = fig.add_axes([0.055, 0.10, 0.40, 0.23])
    ax3.bar(sip["month"], sip["sip_inflow_crore"], color=CYAN, width=22)
    ax3.set_title("Monthly SIP Inflow")
    ax3.set_ylabel("Crore")
    year_ticks(ax3)
    style_axis(ax3)

    ax4 = fig.add_axes([0.52, 0.10, 0.43, 0.23])
    ax4.plot(folios["month"], folios["total_folios_crore"], color=GREEN, linewidth=2.6)
    ax4.plot(folios["month"], folios["equity_folios_crore"], color=ORANGE, linewidth=1.8)
    ax4.legend(["Total folios", "Equity folios"], frameon=False, loc="upper left")
    ax4.set_title("Folio Growth")
    ax4.set_ylabel("Crore")
    year_ticks(ax4)
    style_axis(ax4)

    add_footer(fig, "Page 1 of 4", "Tooltips: latest value, period, AMC/category details")
    return save_fig(fig, "page_1_industry_overview.png")


def performance_page(data: dict[str, pd.DataFrame]) -> Path:
    perf = data["fact_performance"].copy()
    nav = data["fact_nav"].copy()
    bench = data["fact_benchmark_indices"].copy()
    score = pd.read_csv(ROOT / "reports" / "performance_analytics" / "fund_scorecard.csv")
    score = score.merge(perf[["amfi_code", "aum_crore", "return_3yr_pct", "std_dev_ann_pct"]], on="amfi_code", how="left")
    top_score = score.sort_values("fund_score", ascending=False).head(8)
    selected = int(top_score.iloc[0]["amfi_code"])
    selected_name = top_score.iloc[0]["scheme_name"]
    nav_sel = nav[nav["amfi_code"] == selected].sort_values("date").tail(650)
    n50 = nifty_50(bench).tail(650)

    nav_index = nav_sel.assign(indexed=nav_sel["nav"] / nav_sel["nav"].iloc[0] * 100)
    nifty_index = n50.assign(indexed=n50["close_value"] / n50["close_value"].iloc[0] * 100)

    fig = plt.figure(figsize=(16, 9), constrained_layout=False)
    add_header(fig, "Fund Performance", "Risk-return position, scorecard, and NAV versus benchmark")

    ax1 = fig.add_axes([0.055, 0.50, 0.44, 0.33])
    sizes = np.clip(perf["aum_crore"] / perf["aum_crore"].max() * 1200, 80, 1200)
    scatter = ax1.scatter(
        perf["return_3yr_pct"],
        perf["std_dev_ann_pct"],
        s=sizes,
        c=perf["aum_crore"],
        cmap="Blues",
        edgecolor=BLUE,
        linewidth=0.6,
        alpha=0.78,
    )
    ax1.set_title("Return vs Risk")
    ax1.set_xlabel("3Y return (%)")
    ax1.set_ylabel("StdDev annualized (%)")
    style_axis(ax1)
    cbar = fig.colorbar(scatter, ax=ax1, fraction=0.035, pad=0.025)
    cbar.set_label("AUM crore", color=MUTED)

    ax2 = fig.add_axes([0.55, 0.50, 0.40, 0.33])
    ax2.plot(nav_index["date"], nav_index["indexed"], color=BLUE, linewidth=2.5)
    ax2.plot(nifty_index["date"], nifty_index["indexed"], color=ORANGE, linewidth=2.0)
    ax2.set_title("NAV vs Nifty 50 Benchmark")
    ax2.set_ylabel("Indexed to 100")
    ax2.legend([shorten(selected_name, width=40), "Nifty 50"], frameon=False, loc="upper left")
    style_axis(ax2)

    ax3 = fig.add_axes([0.055, 0.09, 0.90, 0.31])
    ax3.axis("off")
    columns = ["scheme_name", "fund_house", "category", "fund_score", "cagr_3yr", "sharpe_ratio", "alpha", "aum_crore"]
    table_data = top_score[columns].copy()
    table_data["scheme_name"] = table_data["scheme_name"].map(lambda x: shorten(str(x), width=42))
    for col in ["fund_score", "cagr_3yr", "sharpe_ratio", "alpha", "aum_crore"]:
        table_data[col] = table_data[col].map(lambda x: f"{x:,.2f}")
    table = ax3.table(
        cellText=table_data.values,
        colLabels=["Scheme", "Fund house", "Category", "Score", "3Y CAGR", "Sharpe", "Alpha", "AUM Cr"],
        cellLoc="left",
        colLoc="left",
        loc="center",
        bbox=[0, 0, 1, 1],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#D9E6F2")
        if row == 0:
            cell.set_facecolor(BLUE)
            cell.get_text().set_color("white")
            cell.get_text().set_fontweight("bold")
        elif row % 2:
            cell.set_facecolor("#F7FAFE")

    add_footer(fig, "Page 2 of 4", "Slicers: fund house, category, plan | Drill-through: fund table to NAV detail")
    return save_fig(fig, "page_2_fund_performance.png")


def investor_page(data: dict[str, pd.DataFrame]) -> Path:
    tx = data["fact_transactions"].copy()
    tx["month"] = tx["transaction_date"].dt.to_period("M").dt.to_timestamp()
    state_amt = tx.groupby("state", as_index=False)["amount_inr"].sum().sort_values("amount_inr", ascending=True).tail(12)
    split = tx.groupby("transaction_type", as_index=False)["amount_inr"].sum()
    sip_age = (
        tx[tx["transaction_type"].str.upper().eq("SIP")]
        .groupby("age_group", as_index=False)["amount_inr"]
        .mean()
        .sort_values("age_group")
    )
    volume = tx.groupby("month", as_index=False)["investor_id"].count()

    fig = plt.figure(figsize=(16, 9), constrained_layout=False)
    add_header(fig, "Investor Analytics", "Transaction geography, mode mix, SIP behavior, and monthly activity")

    ax1 = fig.add_axes([0.055, 0.52, 0.42, 0.31])
    ax1.barh(state_amt["state"], state_amt["amount_inr"] / 1e7, color=BLUE)
    ax1.set_title("Transaction Amount by State")
    ax1.set_xlabel("Rs crore")
    style_axis(ax1, "x")

    ax2 = fig.add_axes([0.55, 0.52, 0.22, 0.31])
    colors = [CYAN, ORANGE, RED, GREEN, BLUE]
    ax2.pie(
        split["amount_inr"],
        labels=split["transaction_type"],
        autopct="%1.0f%%",
        startangle=90,
        colors=colors[: len(split)],
        textprops={"fontsize": 8, "color": INK},
    )
    ax2.set_title("SIP / Lumpsum / Redemption Split")

    ax3 = fig.add_axes([0.81, 0.52, 0.14, 0.31])
    ax3.bar(sip_age["age_group"], sip_age["amount_inr"], color=GREEN)
    ax3.set_title("Age vs Avg SIP")
    ax3.set_ylabel("Rs")
    ax3.tick_params(axis="x", rotation=35)
    style_axis(ax3)

    ax4 = fig.add_axes([0.055, 0.10, 0.90, 0.30])
    ax4.plot(volume["month"], volume["investor_id"], color=BLUE, linewidth=2.6)
    ax4.fill_between(volume["month"], volume["investor_id"], color=CYAN, alpha=0.14)
    ax4.set_title("Monthly Transaction Volume")
    ax4.set_ylabel("Transactions")
    style_axis(ax4)

    add_footer(fig, "Page 3 of 4", "Slicers: state, age group, city tier | Tooltips: amount, count, transaction type")
    return save_fig(fig, "page_3_investor_analytics.png")


def sip_market_page(data: dict[str, pd.DataFrame]) -> Path:
    sip = data["fact_monthly_sip_inflows"].copy()
    bench = data["fact_benchmark_indices"].copy()
    cat = data["fact_category_inflows"].copy()
    period_start = pd.Timestamp("2022-01-01")
    period_end = pd.Timestamp("2025-12-31")
    sip = sip[(sip["month"] >= period_start) & (sip["month"] <= period_end)]
    bench = bench[(bench["date"] >= period_start) & (bench["date"] <= period_end)]
    cat = cat[(cat["month"] >= period_start) & (cat["month"] <= period_end)]
    n50 = nifty_50(bench)
    n50_month = n50.set_index("date")["close_value"].resample("MS").last().reset_index()
    merged = sip.merge(n50_month, left_on="month", right_on="date", how="left")
    heat = cat.pivot_table(index="category", columns="month", values="net_inflow_crore", aggfunc="sum")
    heat = heat.reindex(sorted(heat.columns), axis=1)
    heat = heat.reindex(heat.sum(axis=1).sort_values(ascending=False).index)
    fy25 = cat[(cat["month"] >= "2024-04-01") & (cat["month"] <= "2025-03-31")]
    top5 = fy25.groupby("category", as_index=False)["net_inflow_crore"].sum().sort_values("net_inflow_crore", ascending=True).tail(5)

    fig = plt.figure(figsize=(16, 9), constrained_layout=False)
    add_header(fig, "SIP & Market Trends", "SIP inflows, Nifty 50 movement, and category net inflow patterns")

    ax1 = fig.add_axes([0.055, 0.52, 0.56, 0.31])
    ax1.bar(merged["month"], merged["sip_inflow_crore"], color=CYAN, width=22, alpha=0.82)
    ax1.set_title("SIP Inflow and Nifty 50")
    ax1.set_ylabel("SIP inflow crore", color=BLUE)
    ax1.tick_params(axis="y", labelcolor=BLUE)
    year_ticks(ax1)
    style_axis(ax1)
    ax1b = ax1.twinx()
    ax1b.plot(merged["month"], merged["close_value"], color=ORANGE, linewidth=2.4)
    ax1b.set_ylabel("Nifty 50 close", color=ORANGE)
    ax1b.tick_params(axis="y", labelcolor=ORANGE)

    ax2 = fig.add_axes([0.68, 0.52, 0.27, 0.31])
    ax2.barh(top5["category"], top5["net_inflow_crore"], color=BLUE)
    ax2.set_title("Top 5 Categories by Net Inflow FY25")
    ax2.set_xlabel("Crore")
    style_axis(ax2, "x")

    ax3 = fig.add_axes([0.085, 0.09, 0.87, 0.31])
    shown = heat.iloc[:8, -12:]
    im = ax3.imshow(shown.values, aspect="auto", cmap="Blues")
    ax3.set_title("Category Inflow Heatmap")
    ax3.set_yticks(range(len(shown.index)))
    ax3.set_yticklabels([shorten(str(label), width=17, placeholder="...") for label in shown.index])
    ax3.set_xticks(range(len(shown.columns)))
    ax3.set_xticklabels([pd.Timestamp(col).strftime("%b-%y") for col in shown.columns], rotation=45, ha="right")
    for spine in ax3.spines.values():
        spine.set_color("#D8E3EF")
    cbar = fig.colorbar(im, ax=ax3, fraction=0.020, pad=0.015)
    cbar.set_label("Net inflow crore", color=MUTED)

    add_footer(fig, "Page 4 of 4", "Tooltips: month, SIP inflow, Nifty close, category net inflow")
    return save_fig(fig, "page_4_sip_market_trends.png")


def write_power_bi_support(data: dict[str, pd.DataFrame]) -> None:
    theme = {
        "name": "Bluestock MF Theme",
        "dataColors": [BLUE, CYAN, GREEN, ORANGE, RED, NAVY, "#6C7A89", "#8E44AD"],
        "background": BG,
        "foreground": INK,
        "tableAccent": BLUE,
        "visualStyles": {
            "*": {
                "*": {
                    "title": [{"fontColor": {"solid": {"color": INK}}, "fontSize": 12}],
                    "labels": [{"color": {"solid": {"color": MUTED}}}],
                }
            }
        },
    }
    (OUT_DIR / "bluestock_powerbi_theme.json").write_text(json.dumps(theme, indent=2), encoding="utf-8")

    counts = {name: len(frame) for name, frame in data.items()}
    guide = f"""# Bluestock MF Dashboard - Power BI Build Notes

## Data Load Verification

SQLite source: `{DB_PATH.name}`

| Table | Rows |
| --- | ---: |
{chr(10).join(f"| `{name}` | {rows:,} |" for name, rows in counts.items())}

The loaded model has 8 fact tables plus `dim_fund`. Relate `dim_fund[amfi_code]` one-to-many to `fact_nav`, `fact_performance`, `fact_transactions`, and `fact_portfolio_holdings`. Relate date/month fields through a calendar table if using Power BI time intelligence.

## Pages

1. Industry Overview: KPI cards, industry AUM trend, AUM by AMC.
2. Fund Performance: return vs StdDev scatter with AUM bubble size, scorecard table, NAV vs Nifty 50, slicers for fund house/category/plan.
3. Investor Analytics: state amount bar, transaction split donut, age group vs average SIP, monthly volume, slicers for state/age/city tier.
4. SIP & Market Trends: SIP inflow bars plus Nifty 50 line, category inflow heatmap, top 5 FY25 categories.

## Interactivity

Add a drill-through page filtered by `amfi_code` from the scorecard to NAV detail. Add report page tooltips carrying period, fund, category, AUM, return, risk, amount, and count fields.

## Exported Static Package

The generated PNGs and `Dashboard.pdf` are static equivalents of the requested report pages. Use `bluestock_powerbi_theme.json` as the Power BI theme.
"""
    (OUT_DIR / "powerbi_build_notes.md").write_text(guide, encoding="utf-8")


def pngs_to_pdf(png_paths: list[Path]) -> Path:
    images = [Image.open(path).convert("RGB") for path in png_paths]
    pdf_path = OUT_DIR / "Dashboard.pdf"
    images[0].save(pdf_path, save_all=True, append_images=images[1:], resolution=150)
    return pdf_path


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PNG_DIR.mkdir(parents=True, exist_ok=True)
    data = load_data()
    png_paths = [
        industry_page(data),
        performance_page(data),
        investor_page(data),
        sip_market_page(data),
    ]
    pdf_path = pngs_to_pdf(png_paths)
    write_power_bi_support(data)
    print("Created:")
    for path in png_paths:
        print(path)
    print(pdf_path)


if __name__ == "__main__":
    main()
