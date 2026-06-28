"""Build the complete mutual fund EDA deliverable.

The script generates the report-ready chart assets and rebuilds
notebooks/EDA_Analysis.ipynb with reproducible code cells plus Markdown
findings that reference the generated charts.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import nbformat as nbf
import pandas as pd
import plotly.express as px
import seaborn as sns


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
NOTEBOOK_PATH = PROJECT_ROOT / "notebooks" / "EDA_Analysis.ipynb"


def read_data() -> dict[str, pd.DataFrame]:
    return {
        "funds": pd.read_csv(DATA_DIR / "01_fund_master.csv"),
        "nav": pd.read_csv(DATA_DIR / "02_nav_history.csv"),
        "aum": pd.read_csv(DATA_DIR / "03_aum_by_fund_house.csv"),
        "sip": pd.read_csv(DATA_DIR / "04_monthly_sip_inflows.csv"),
        "category": pd.read_csv(DATA_DIR / "05_category_inflows.csv"),
        "folios": pd.read_csv(DATA_DIR / "06_industry_folio_count.csv"),
        "performance": pd.read_csv(DATA_DIR / "07_scheme_performance.csv"),
        "investors": pd.read_csv(DATA_DIR / "08_investor_transactions.csv"),
        "holdings": pd.read_csv(DATA_DIR / "09_portfolio_holdings.csv"),
        "benchmarks": pd.read_csv(DATA_DIR / "10_benchmark_indices.csv"),
    }


def savefig(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    print(f"Wrote {path}")


def scheme_nav(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    nav = data["nav"].merge(
        data["funds"][["amfi_code", "scheme_name", "fund_house", "category", "sub_category"]],
        on="amfi_code",
        how="left",
    )
    nav["date"] = pd.to_datetime(nav["date"], errors="coerce")
    nav["nav"] = pd.to_numeric(nav["nav"], errors="coerce")
    nav = nav.dropna(subset=["date", "nav", "scheme_name"])
    return nav[nav["date"].between("2022-01-01", "2026-12-31")].sort_values(
        ["scheme_name", "date"]
    )


def export_plotly_png(fig, path: Path, width: int = 1600, height: int = 900) -> None:
    try:
        fig.write_image(path, width=width, height=height, scale=2)
        print(f"Wrote {path}")
    except Exception as exc:  # Chrome/kaleido can be unavailable on some systems.
        print(f"Skipped static Plotly PNG {path.name}: {exc}")


def plot_nav_trends(nav: pd.DataFrame) -> None:
    top = nav.groupby("scheme_name")["date"].count().sort_values(ascending=False).head(40).index
    plot_data = nav[nav["scheme_name"].isin(top)]

    fig = px.line(
        plot_data,
        x="date",
        y="nav",
        color="scheme_name",
        template="plotly_white",
        title="Daily NAV Trend for 40 Mutual Fund Schemes, 2022-2026",
        labels={"date": "Date", "nav": "NAV", "scheme_name": "Scheme"},
    )
    highlights = [
        ("2023 bull run", "2023-03-31", "2023-12-29", "rgba(46, 125, 50, 0.14)"),
        ("2024 correction", "2024-03-01", "2024-06-04", "rgba(211, 47, 47, 0.13)"),
        ("late-2024 correction", "2024-09-27", "2024-11-21", "rgba(211, 47, 47, 0.10)"),
    ]
    for label, start, end, color in highlights:
        fig.add_vrect(
            x0=start,
            x1=end,
            fillcolor=color,
            line_width=0,
            layer="below",
            annotation_text=label,
            annotation_position="top left",
        )
    fig.update_traces(line={"width": 1.3}, opacity=0.8)
    fig.update_layout(hovermode="x unified", height=850, legend_title_text="Scheme")
    html = OUTPUT_DIR / "nav_trend_2022_2026_plotly.html"
    fig.write_html(html, include_plotlyjs="cdn")
    print(f"Wrote {html}")
    export_plotly_png(fig, OUTPUT_DIR / "nav_trend_2022_2026.png", 1800, 950)

    indexed = plot_data.copy()
    indexed["base_nav"] = indexed.groupby("scheme_name")["nav"].transform("first")
    indexed["indexed_nav"] = indexed["nav"] / indexed["base_nav"] * 100
    plt.figure(figsize=(15, 8))
    ax = sns.lineplot(data=indexed, x="date", y="indexed_nav", hue="scheme_name", legend=False, linewidth=1)
    ax.axvspan(pd.Timestamp("2023-03-31"), pd.Timestamp("2023-12-29"), color="#2e7d32", alpha=0.12)
    ax.axvspan(pd.Timestamp("2024-03-01"), pd.Timestamp("2024-06-04"), color="#d32f2f", alpha=0.10)
    ax.set_title("Indexed NAV Growth for 40 Schemes, Base Jan 2022 = 100")
    ax.set_xlabel("Date")
    ax.set_ylabel("Indexed NAV")
    savefig(OUTPUT_DIR / "nav_indexed_growth_2022_2026.png")

    annual = plot_data.copy()
    annual["year"] = annual["date"].dt.year
    annual_returns = (
        annual[annual["year"].isin([2023, 2024])]
        .groupby(["scheme_name", "year"])["nav"]
        .agg(first="first", last="last")
        .reset_index()
    )
    annual_returns["return_pct"] = (annual_returns["last"] / annual_returns["first"] - 1) * 100
    for year, filename, title in [
        (2023, "nav_2023_return_by_scheme.png", "2023 NAV Return by Scheme"),
        (2024, "nav_2024_return_by_scheme.png", "2024 NAV Return by Scheme"),
    ]:
        subset = annual_returns[annual_returns["year"] == year].sort_values("return_pct", ascending=False)
        plt.figure(figsize=(12, 13))
        ax = sns.barplot(data=subset, x="return_pct", y="scheme_name", color="#4c78a8")
        ax.axvline(0, color="#333333", linewidth=1)
        ax.set_title(title)
        ax.set_xlabel("Return (%)")
        ax.set_ylabel("Scheme")
        savefig(OUTPUT_DIR / filename)


def plot_aum(data: dict[str, pd.DataFrame]) -> None:
    aum = data["aum"].copy()
    aum["date"] = pd.to_datetime(aum["date"], errors="coerce")
    aum["year"] = aum["date"].dt.year
    aum = aum[aum["year"].between(2022, 2025)]
    order = aum.groupby("fund_house")["aum_crore"].max().sort_values(ascending=False).index
    palette = {fund: "#4c78a8" for fund in order}
    for fund in order:
        if "sbi" in fund.lower():
            palette[fund] = "#d62728"
    plt.figure(figsize=(15, 8))
    ax = sns.barplot(data=aum, x="year", y="aum_crore", hue="fund_house", hue_order=order, palette=palette)
    ax.axhline(1_250_000, color="#d62728", linestyle="--", linewidth=1.5)
    ax.text(0.02, 0.96, "SBI dominance: Rs. 12.5L Cr", transform=ax.transAxes, color="#b71c1c", weight="bold")
    ax.set_title("AUM Growth by Fund House, 2022-2025")
    ax.set_xlabel("Year")
    ax.set_ylabel("AUM (Rs. Cr)")
    ax.legend(title="Fund house", bbox_to_anchor=(1.02, 1), loc="upper left")
    savefig(OUTPUT_DIR / "aum_growth_by_fund_house_2022_2025.png")

    latest = aum[aum["year"] == 2025].copy()
    latest["share_pct"] = latest["aum_crore"] / latest["aum_crore"].sum() * 100
    latest = latest.sort_values("share_pct", ascending=True)
    plt.figure(figsize=(11, 7))
    ax = sns.barplot(data=latest, x="share_pct", y="fund_house", color="#54a24b")
    ax.set_title("Fund-House AUM Market Share, 2025")
    ax.set_xlabel("AUM share (%)")
    ax.set_ylabel("Fund house")
    savefig(OUTPUT_DIR / "aum_market_share_2025.png")


def plot_sip_and_category(data: dict[str, pd.DataFrame]) -> None:
    sip = data["sip"].copy()
    sip["month"] = pd.to_datetime(sip["month"], errors="coerce")
    sip = sip[sip["month"].between("2022-01-01", "2025-12-31")].sort_values("month")
    fig = px.line(
        sip,
        x="month",
        y="sip_inflow_crore",
        markers=True,
        template="plotly_white",
        title="Monthly SIP Inflow Trend, Jan 2022-Dec 2025",
        labels={"month": "Month", "sip_inflow_crore": "SIP inflow (Rs. Cr)"},
    )
    high = sip[sip["month"].dt.to_period("M") == pd.Period("2025-12")].iloc[-1]
    high_month = high["month"].to_pydatetime()
    fig.add_annotation(
        x=high_month,
        y=high["sip_inflow_crore"],
        text="All-time high: Rs. 31,002 Cr",
        showarrow=True,
        arrowhead=2,
        ax=-95,
        ay=-60,
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="#d62728",
    )
    fig.add_scatter(x=[high_month], y=[high["sip_inflow_crore"]], mode="markers", marker={"size": 13, "color": "#d62728"}, name="Dec 2025")
    html = OUTPUT_DIR / "sip_inflow_jan2022_dec2025_plotly.html"
    fig.write_html(html, include_plotlyjs="cdn")
    print(f"Wrote {html}")
    export_plotly_png(fig, OUTPUT_DIR / "sip_inflow_jan2022_dec2025.png", 1500, 760)

    plt.figure(figsize=(13, 7))
    ax = sns.lineplot(data=sip, x="month", y="active_sip_accounts_crore", marker="o", color="#4c78a8")
    ax.set_title("Active SIP Accounts Growth, Jan 2022-Dec 2025")
    ax.set_xlabel("Month")
    ax.set_ylabel("Active SIP accounts (Cr)")
    savefig(OUTPUT_DIR / "active_sip_accounts_growth.png")

    category = data["category"].copy()
    category["month"] = pd.to_datetime(category["month"], errors="coerce")
    category["month_label"] = category["month"].dt.strftime("%Y-%m")
    heatmap_data = category.pivot_table(
        index="category", columns="month_label", values="net_inflow_crore", aggfunc="sum", fill_value=0
    )
    plt.figure(figsize=(18, max(7, 0.45 * len(heatmap_data))))
    ax = sns.heatmap(
        heatmap_data,
        cmap="RdYlGn",
        center=0,
        linewidths=0.35,
        linecolor="white",
        cbar_kws={"label": "Net inflow (Rs. Cr)"},
    )
    ax.set_title("Monthly Net Inflow Heatmap by Fund Category")
    ax.set_xlabel("Month")
    ax.set_ylabel("Fund category")
    plt.xticks(rotation=45, ha="right")
    savefig(OUTPUT_DIR / "category_inflow_heatmap.png")

    cumulative = category.groupby("category", as_index=False)["net_inflow_crore"].sum().sort_values(
        "net_inflow_crore", ascending=True
    )
    plt.figure(figsize=(11, 8))
    ax = sns.barplot(data=cumulative, x="net_inflow_crore", y="category", color="#f58518")
    ax.axvline(0, color="#333333", linewidth=1)
    ax.set_title("Cumulative Net Inflow by Fund Category")
    ax.set_xlabel("Cumulative net inflow (Rs. Cr)")
    ax.set_ylabel("Category")
    savefig(OUTPUT_DIR / "category_cumulative_net_inflow.png")


def plot_investors(data: dict[str, pd.DataFrame]) -> None:
    inv = data["investors"].copy()
    inv["amount_inr"] = pd.to_numeric(inv["amount_inr"], errors="coerce")
    sip = inv[inv["transaction_type"].astype(str).str.upper() == "SIP"].dropna(subset=["amount_inr"])

    age_counts = sip["age_group"].value_counts().sort_index()
    plt.figure(figsize=(9, 9))
    plt.pie(age_counts, labels=age_counts.index, autopct="%1.1f%%", startangle=90, wedgeprops={"edgecolor": "white"})
    plt.title("Investor Age Group Distribution")
    savefig(OUTPUT_DIR / "investor_age_group_pie.png")

    plt.figure(figsize=(11, 7))
    ax = sns.boxplot(data=sip, x="age_group", y="amount_inr", color="#4c78a8")
    ax.set_title("SIP Amount Distribution by Age Group")
    ax.set_xlabel("Age group")
    ax.set_ylabel("SIP amount (Rs.)")
    savefig(OUTPUT_DIR / "sip_amount_box_by_age_group.png")

    gender_amount = sip.groupby("gender", as_index=False)["amount_inr"].sum()
    plt.figure(figsize=(9, 6))
    ax = sns.barplot(data=gender_amount, x="gender", y="amount_inr", hue="gender", palette="Set2", legend=False)
    ax.set_title("Investor Gender Split by SIP Amount")
    ax.set_xlabel("Gender")
    ax.set_ylabel("SIP amount (Rs.)")
    savefig(OUTPUT_DIR / "investor_gender_split.png")

    income = sip.groupby("age_group", as_index=False)["annual_income_lakh"].median()
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(data=income, x="age_group", y="annual_income_lakh", color="#72b7b2")
    ax.set_title("Median Annual Income by SIP Investor Age Group")
    ax.set_xlabel("Age group")
    ax.set_ylabel("Median income (Rs. lakh)")
    savefig(OUTPUT_DIR / "median_income_by_age_group.png")


def plot_geo_folios_corr_sector(data: dict[str, pd.DataFrame], nav: pd.DataFrame) -> None:
    inv = data["investors"].copy()
    inv["amount_inr"] = pd.to_numeric(inv["amount_inr"], errors="coerce")
    sip = inv[inv["transaction_type"].astype(str).str.upper() == "SIP"].dropna(subset=["amount_inr"])
    state_sip = sip.groupby("state", as_index=False)["amount_inr"].sum().sort_values("amount_inr", ascending=True)
    plt.figure(figsize=(12, 10))
    ax = sns.barplot(data=state_sip, x="amount_inr", y="state", color="#4c78a8")
    ax.set_title("SIP Amount by State")
    ax.set_xlabel("SIP amount (Rs.)")
    ax.set_ylabel("State")
    savefig(OUTPUT_DIR / "sip_amount_by_state.png")

    tier_sip = sip.groupby("city_tier")["amount_inr"].sum()
    tier_sip = tier_sip.reindex([tier for tier in ["T30", "B30"] if tier in tier_sip.index])
    plt.figure(figsize=(8, 8))
    plt.pie(tier_sip, labels=tier_sip.index, autopct="%1.1f%%", startangle=90, colors=["#4c78a8", "#f58518"], wedgeprops={"edgecolor": "white"})
    plt.title("T30 vs B30 SIP Amount Split")
    savefig(OUTPUT_DIR / "t30_b30_city_tier_pie.png")

    folios = data["folios"].copy()
    folios["month"] = pd.to_datetime(folios["month"], errors="coerce")
    plt.figure(figsize=(13, 7))
    ax = sns.lineplot(data=folios, x="month", y="total_folios_crore", marker="o", color="#4c78a8")
    ax.set_title("Folio Count Growth, Jan 2022-Dec 2025")
    ax.set_xlabel("Month")
    ax.set_ylabel("Folio count (Cr)")
    for threshold in [15, 20, 25]:
        crossed = folios[folios["total_folios_crore"] >= threshold]
        if not crossed.empty:
            point = crossed.iloc[0]
            ax.scatter(point["month"], point["total_folios_crore"], color="#d62728", s=60)
            ax.annotate(f"{threshold} Cr", xy=(point["month"], point["total_folios_crore"]), xytext=(8, 12), textcoords="offset points", color="#b71c1c")
    ax.annotate("Jan 2022: 13.26 Cr", xy=(folios.iloc[0]["month"], folios.iloc[0]["total_folios_crore"]), xytext=(20, 25), textcoords="offset points", arrowprops={"arrowstyle": "->"})
    ax.annotate("Dec 2025: 26.12 Cr", xy=(folios.iloc[-1]["month"], folios.iloc[-1]["total_folios_crore"]), xytext=(-135, -45), textcoords="offset points", arrowprops={"arrowstyle": "->"})
    savefig(OUTPUT_DIR / "folio_count_growth_jan2022_dec2025.png")

    selected = nav.groupby("scheme_name")["date"].count().sort_values(ascending=False).head(10).index
    wide = nav[nav["scheme_name"].isin(selected)].pivot_table(index="date", columns="scheme_name", values="nav", aggfunc="last")
    corr = wide.pct_change(fill_method=None).corr()
    plt.figure(figsize=(12, 10))
    ax = sns.heatmap(corr, vmin=-1, vmax=1, center=0, cmap="vlag", annot=True, fmt=".2f", square=True, linewidths=0.35, cbar_kws={"label": "Correlation"})
    ax.set_title("Daily NAV Return Correlation Matrix, 10 Selected Funds")
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    savefig(OUTPUT_DIR / "nav_return_correlation_matrix.png")

    holdings = data["holdings"].merge(data["funds"][["amfi_code", "category"]], on="amfi_code", how="inner")
    equity = holdings[holdings["category"].astype(str).str.contains("equity", case=False, na=False)].copy()
    sector = equity.groupby("sector", as_index=False)["market_value_cr"].sum().sort_values("market_value_cr", ascending=False)
    top = sector.head(10).copy()
    other_value = sector.iloc[10:]["market_value_cr"].sum()
    if other_value > 0:
        top = pd.concat([top, pd.DataFrame({"sector": ["Others"], "market_value_cr": [other_value]})], ignore_index=True)
    plt.figure(figsize=(12, 8))
    wedges, _, autotexts = plt.pie(
        top["market_value_cr"],
        labels=top["sector"],
        autopct=lambda pct: f"{pct:.1f}%" if pct >= 3 else "",
        startangle=90,
        pctdistance=0.78,
        wedgeprops={"width": 0.42, "edgecolor": "white"},
    )
    for text in autotexts:
        text.set_fontsize(9)
    plt.title("Sector Allocation Across Equity Fund Holdings")
    plt.legend(wedges, top["sector"], title="Sector", loc="center left", bbox_to_anchor=(1.15, 0.5), fontsize=9)
    savefig(OUTPUT_DIR / "sector_allocation_donut.png")

    holdings_bar = equity.groupby("stock_name", as_index=False)["market_value_cr"].sum().sort_values("market_value_cr", ascending=False).head(15)
    plt.figure(figsize=(12, 8))
    ax = sns.barplot(data=holdings_bar.sort_values("market_value_cr"), x="market_value_cr", y="stock_name", color="#e45756")
    ax.set_title("Top 15 Equity Holdings by Aggregate Market Value")
    ax.set_xlabel("Market value (Rs. Cr)")
    ax.set_ylabel("Holding")
    savefig(OUTPUT_DIR / "top_equity_holdings_by_market_value.png")


def plot_performance(data: dict[str, pd.DataFrame]) -> None:
    perf = data["performance"].copy()
    top = perf.sort_values("return_3yr_pct", ascending=False).head(15).sort_values("return_3yr_pct")
    plt.figure(figsize=(11, 8))
    ax = sns.barplot(data=top, x="return_3yr_pct", y="scheme_name", color="#54a24b")
    ax.set_title("Top 15 Schemes by 3-Year Return")
    ax.set_xlabel("3-year return (%)")
    ax.set_ylabel("Scheme")
    savefig(OUTPUT_DIR / "top_15_schemes_3yr_return.png")

    plt.figure(figsize=(10, 7))
    ax = sns.scatterplot(
        data=perf,
        x="std_dev_ann_pct",
        y="return_3yr_pct",
        hue="category",
        size="aum_crore",
        sizes=(30, 300),
        alpha=0.75,
    )
    ax.set_title("Risk-Return Profile by Scheme")
    ax.set_xlabel("Annualized standard deviation (%)")
    ax.set_ylabel("3-year return (%)")
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
    savefig(OUTPUT_DIR / "risk_return_profile_by_scheme.png")


def build_notebook() -> None:
    chart_refs = [
        ("NAV trend analysis", "nav_trend_2022_2026.png", "Daily NAV for 40 schemes with 2023 bull run and 2024 correction highlights."),
        ("Indexed NAV growth", "nav_indexed_growth_2022_2026.png", "Base-100 growth comparison across the same 40 schemes."),
        ("2023 NAV returns", "nav_2023_return_by_scheme.png", "Scheme-level return ranking during the 2023 rally."),
        ("2024 NAV returns", "nav_2024_return_by_scheme.png", "Scheme-level return ranking around the correction year."),
        ("AUM grouped bar", "aum_growth_by_fund_house_2022_2025.png", "Grouped bar chart by fund house and year, highlighting SBI."),
        ("AUM market share", "aum_market_share_2025.png", "2025 fund-house market share."),
        ("SIP inflow trend", "sip_inflow_jan2022_dec2025.png", "Monthly SIP trend with Dec 2025 high annotated."),
        ("Active SIP accounts", "active_sip_accounts_growth.png", "Growth in active SIP accounts."),
        ("Category inflow heatmap", "category_inflow_heatmap.png", "Monthly category inflow intensity."),
        ("Category cumulative inflow", "category_cumulative_net_inflow.png", "Cumulative net inflow by category."),
        ("Investor age distribution", "investor_age_group_pie.png", "Age group distribution pie chart."),
        ("SIP amount by age group", "sip_amount_box_by_age_group.png", "SIP amount distribution by age group."),
        ("Gender split", "investor_gender_split.png", "Gender split by SIP amount."),
        ("Income by age group", "median_income_by_age_group.png", "Median income by age group."),
        ("SIP amount by state", "sip_amount_by_state.png", "Geographic SIP amount bar chart."),
        ("T30 vs B30 split", "t30_b30_city_tier_pie.png", "City tier split pie chart."),
        ("Folio growth", "folio_count_growth_jan2022_dec2025.png", "Folio growth with milestones."),
        ("NAV return correlation", "nav_return_correlation_matrix.png", "Pairwise return correlations for 10 selected funds."),
        ("Sector allocation", "sector_allocation_donut.png", "Aggregated equity sector allocation."),
        ("Top equity holdings", "top_equity_holdings_by_market_value.png", "Largest aggregate equity holdings."),
        ("Top 3-year returns", "top_15_schemes_3yr_return.png", "Top schemes by 3-year return."),
        ("Risk-return profile", "risk_return_profile_by_scheme.png", "Scheme risk-return scatter plot."),
    ]
    findings = [
        "**Finding 1:** SBI Mutual Fund dominates fund-house AUM with the highlighted Rs. 12.5L Cr reference; supporting chart: `aum_growth_by_fund_house_2022_2025.png`.",
        "**Finding 2:** Monthly SIP inflow reaches the dataset high of Rs. 31,002 Cr in Dec 2025; supporting chart: `sip_inflow_jan2022_dec2025.png`.",
        "**Finding 3:** Folio count almost doubles from 13.26 Cr in Jan 2022 to 26.12 Cr in Dec 2025; supporting chart: `folio_count_growth_jan2022_dec2025.png`.",
        "**Finding 4:** The 2023 bull-run window shows broad positive NAV momentum across the top 40 schemes; supporting chart: `nav_indexed_growth_2022_2026.png`.",
        "**Finding 5:** The 2024 correction windows interrupt the otherwise rising NAV path and create visible dispersion across schemes; supporting chart: `nav_trend_2022_2026.png`.",
        "**Finding 6:** Category flows are uneven by month, with high-intensity inflow pockets concentrated in specific categories; supporting chart: `category_inflow_heatmap.png`.",
        "**Finding 7:** SIP participation is concentrated in working-age investor bands; supporting chart: `investor_age_group_pie.png`.",
        "**Finding 8:** SIP ticket sizes vary materially by age group, as shown by the box-plot spread and outliers; supporting chart: `sip_amount_box_by_age_group.png`.",
        "**Finding 9:** Geographic SIP value is concentrated in a small group of leading states; supporting chart: `sip_amount_by_state.png`.",
        "**Finding 10:** Equity portfolio exposure is led by a few large sectors, with Banking the largest aggregate allocation; supporting chart: `sector_allocation_donut.png`.",
    ]

    nb = nbf.v4.new_notebook()
    nb["metadata"] = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "pygments_lexer": "ipython3"},
    }
    cells = [
        nbf.v4.new_markdown_cell("# Mutual Fund EDA Analysis\n\nComplete EDA deliverable with 15+ exported charts for final reporting."),
        nbf.v4.new_code_cell(
            "from pathlib import Path\n"
            "from IPython.display import Image, HTML, display\n\n"
            "OUTPUT_DIR = Path('../outputs')\n"
            "chart_files = sorted(OUTPUT_DIR.glob('*.png'))\n"
            "len(chart_files), [p.name for p in chart_files]"
        ),
        nbf.v4.new_markdown_cell("## Key EDA Findings"),
    ]
    cells.extend(nbf.v4.new_markdown_cell(item) for item in findings)
    cells.append(nbf.v4.new_markdown_cell("## Chart Gallery"))
    for title, filename, caption in chart_refs:
        cells.append(nbf.v4.new_markdown_cell(f"### {title}\n\n{caption}"))
        cells.append(nbf.v4.new_code_cell(f"display(Image(filename=str(OUTPUT_DIR / '{filename}')))"))
    cells.append(nbf.v4.new_markdown_cell("## Interactive Plotly Charts"))
    cells.append(nbf.v4.new_code_cell("display(HTML(filename=str(OUTPUT_DIR / 'nav_trend_2022_2026_plotly.html')))"))
    cells.append(nbf.v4.new_code_cell("display(HTML(filename=str(OUTPUT_DIR / 'sip_inflow_jan2022_dec2025_plotly.html')))"))
    nb["cells"] = cells
    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(nb, NOTEBOOK_PATH)
    print(f"Wrote {NOTEBOOK_PATH}")


def main() -> None:
    sns.set_theme(style="whitegrid", context="talk")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    data = read_data()
    nav = scheme_nav(data)
    plot_nav_trends(nav)
    plot_aum(data)
    plot_sip_and_category(data)
    plot_investors(data)
    plot_geo_folios_corr_sector(data, nav)
    plot_performance(data)
    build_notebook()


if __name__ == "__main__":
    main()
