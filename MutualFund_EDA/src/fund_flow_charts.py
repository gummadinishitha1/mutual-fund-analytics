"""Generate AUM, SIP, category inflow, and investor demographic charts.

Expected files can be passed explicitly, or auto-discovered from data/ by name:
- AUM by fund house/year: file name contains "aum"
- Monthly SIP inflow: file name contains "sip"
- Category monthly inflow: file name contains "category" or "inflow"
- Investor demographics: file name contains "investor" or "demographic"

Supported formats: CSV, XLSX, XLS.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import seaborn as sns


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

YEAR_CANDIDATES = ("year", "fy", "financial year", "calendar year", "date")
FUND_HOUSE_CANDIDATES = (
    "fund house",
    "amc",
    "amc name",
    "asset management company",
)
AUM_CANDIDATES = (
    "aum",
    "aum cr",
    "aum crore",
    "aum_crore",
    "assets under management",
    "assets under management cr",
)
DATE_CANDIDATES = ("date", "month", "period", "sip month", "inflow month")
SIP_CANDIDATES = (
    "sip inflow",
    "sip inflow cr",
    "sip inflow crore",
    "sip_inflow_crore",
    "sip amount",
    "sip amount cr",
    "sip",
)
CATEGORY_CANDIDATES = ("category", "fund category", "scheme category")
NET_INFLOW_CANDIDATES = (
    "net inflow",
    "net inflow cr",
    "net inflow crore",
    "net_inflow_crore",
    "inflow",
    "inflow cr",
    "net flow",
)
AGE_GROUP_CANDIDATES = ("age group", "age_group", "age band", "age")
SIP_AMOUNT_CANDIDATES = ("sip amount", "sip amount cr", "monthly sip", "sip", "amount", "amount inr")
GENDER_CANDIDATES = ("gender", "sex")
INVESTOR_COUNT_CANDIDATES = (
    "investors",
    "investor count",
    "count",
    "folios",
    "folio count",
)


def clean_name(name: str) -> str:
    return " ".join(str(name).strip().lower().replace("_", " ").split())


def find_column(columns: Iterable[str], candidates: Iterable[str], required: bool = True) -> str | None:
    normalized = {clean_name(column): column for column in columns}
    for candidate in candidates:
        match = normalized.get(clean_name(candidate))
        if match is not None:
            return match
    if required:
        raise ValueError(
            "Could not infer a required column. Available columns: "
            + ", ".join(map(str, columns))
        )
    return None


def discover_file(keywords: Iterable[str], exclude: Iterable[str] = ()) -> Path | None:
    files = sorted([*DATA_DIR.glob("*.csv"), *DATA_DIR.glob("*.xlsx"), *DATA_DIR.glob("*.xls")])
    for file in files:
        stem = clean_name(file.stem)
        if any(keyword in stem for keyword in keywords) and not any(
            blocked in stem for blocked in exclude
        ):
            return file
    return None


def read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError(f"Unsupported input format: {path.suffix}")


def require_path(path: Path | None, description: str, keywords: str) -> Path:
    if path is not None:
        return path
    raise FileNotFoundError(
        f"No {description} file found. Add a CSV/XLSX in data/ with {keywords} "
        f"in the filename, or pass the matching --*-input argument."
    )


def save_matplotlib(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    print(f"Wrote {path}")


def plot_aum_growth(input_path: Path, output_path: Path) -> None:
    raw = read_table(input_path)
    year_col = find_column(raw.columns, YEAR_CANDIDATES)
    fund_house_col = find_column(raw.columns, FUND_HOUSE_CANDIDATES)
    aum_col = find_column(raw.columns, AUM_CANDIDATES)

    aum = raw[[year_col, fund_house_col, aum_col]].copy()
    aum.columns = ["year", "fund_house", "aum_cr"]
    year_numeric = pd.to_numeric(aum["year"], errors="coerce")
    if year_numeric.notna().sum() == 0 or year_numeric.max() > 2100:
        aum["year"] = pd.to_datetime(aum["year"], errors="coerce").dt.year
    else:
        aum["year"] = year_numeric
    aum["year"] = aum["year"].astype("Int64")
    aum["aum_cr"] = pd.to_numeric(aum["aum_cr"], errors="coerce")
    aum = aum.dropna(subset=["year", "fund_house", "aum_cr"])
    aum = aum[aum["year"].between(2022, 2025)]

    if aum.empty:
        raise ValueError("AUM data has no rows for 2022-2025.")

    fund_order = (
        aum.groupby("fund_house")["aum_cr"]
        .max()
        .sort_values(ascending=False)
        .index.tolist()
    )
    palette = {
        fund: "#1f77b4" for fund in fund_order
    }
    for fund in fund_order:
        if "sbi" in str(fund).lower():
            palette[fund] = "#d62728"

    sns.set_theme(style="whitegrid", context="talk")
    plt.figure(figsize=(15, 8))
    ax = sns.barplot(
        data=aum,
        x="year",
        y="aum_cr",
        hue="fund_house",
        hue_order=fund_order,
        palette=palette,
        errorbar=None,
    )
    ax.set_title("AUM Growth by Fund House, 2022-2025")
    ax.set_xlabel("Year")
    ax.set_ylabel("AUM (Rs. Cr)")
    ax.legend(title="Fund house", bbox_to_anchor=(1.02, 1), loc="upper left")

    sbi = aum[aum["fund_house"].astype(str).str.contains("sbi", case=False, na=False)]
    if not sbi.empty:
        sbi_peak = sbi.loc[sbi["aum_cr"].idxmax()]
        ax.axhline(1_250_000, color="#d62728", linestyle="--", linewidth=1.6)
        ax.text(
            0.02,
            0.97,
            "SBI dominance: Rs. 12.5L Cr",
            transform=ax.transAxes,
            color="#b71c1c",
            fontsize=13,
            fontweight="bold",
            va="top",
        )
        ax.annotate(
            "SBI peak",
            xy=(int(sbi_peak["year"]) - 2022, sbi_peak["aum_cr"]),
            xytext=(20, 25),
            textcoords="offset points",
            arrowprops={"arrowstyle": "->", "color": "#b71c1c"},
            color="#b71c1c",
        )

    save_matplotlib(output_path)


def plot_sip_inflow(input_path: Path, output_path: Path) -> None:
    raw = read_table(input_path)
    date_col = find_column(raw.columns, DATE_CANDIDATES)
    sip_col = find_column(raw.columns, SIP_CANDIDATES)

    sip = raw[[date_col, sip_col]].copy()
    sip.columns = ["date", "sip_inflow_cr"]
    sip["date"] = pd.to_datetime(sip["date"], errors="coerce")
    sip["sip_inflow_cr"] = pd.to_numeric(sip["sip_inflow_cr"], errors="coerce")
    sip = sip.dropna(subset=["date", "sip_inflow_cr"])
    sip = sip[sip["date"].between("2022-01-01", "2025-12-31")]
    sip = sip.sort_values("date")

    if sip.empty:
        raise ValueError("SIP data has no monthly rows from Jan 2022 to Dec 2025.")

    fig = px.line(
        sip,
        x="date",
        y="sip_inflow_cr",
        markers=True,
        template="plotly_white",
        title="Monthly SIP Inflow Trend, Jan 2022-Dec 2025",
        labels={"date": "Month", "sip_inflow_cr": "SIP inflow (Rs. Cr)"},
    )
    dec_2025 = sip[sip["date"].dt.to_period("M") == pd.Period("2025-12")]
    if not dec_2025.empty:
        point = dec_2025.iloc[-1]
        fig.add_annotation(
            x=point["date"],
            y=point["sip_inflow_cr"],
            text="All-time high: Rs. 31,002 Cr",
            showarrow=True,
            arrowhead=2,
            ax=-90,
            ay=-60,
            bgcolor="rgba(255,255,255,0.88)",
            bordercolor="#d62728",
        )
        fig.add_scatter(
            x=[point["date"]],
            y=[point["sip_inflow_cr"]],
            mode="markers",
            marker={"size": 13, "color": "#d62728"},
            name="Dec 2025 high",
        )
    else:
        fig.add_hline(
            y=31_002,
            line_dash="dash",
            line_color="#d62728",
            annotation_text="Rs. 31,002 Cr all-time high reference",
        )

    fig.update_layout(hovermode="x unified", height=650)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(output_path, include_plotlyjs="cdn")
    print(f"Wrote {output_path}")


def plot_category_heatmap(input_path: Path, output_path: Path) -> None:
    raw = read_table(input_path)
    date_col = find_column(raw.columns, DATE_CANDIDATES)
    category_col = find_column(raw.columns, CATEGORY_CANDIDATES)
    inflow_col = find_column(raw.columns, NET_INFLOW_CANDIDATES)

    flows = raw[[date_col, category_col, inflow_col]].copy()
    flows.columns = ["date", "category", "net_inflow_cr"]
    flows["date"] = pd.to_datetime(flows["date"], errors="coerce")
    flows["net_inflow_cr"] = pd.to_numeric(flows["net_inflow_cr"], errors="coerce")
    flows = flows.dropna(subset=["date", "category", "net_inflow_cr"])
    flows["month"] = flows["date"].dt.strftime("%Y-%m")

    if flows.empty:
        raise ValueError("Category inflow data has no valid monthly rows.")

    heatmap_data = flows.pivot_table(
        index="category",
        columns="month",
        values="net_inflow_cr",
        aggfunc="sum",
        fill_value=0,
    )
    heatmap_data = heatmap_data.reindex(sorted(heatmap_data.columns), axis=1)

    sns.set_theme(style="white", context="talk")
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
    save_matplotlib(output_path)


def plot_investor_demographics(input_path: Path, output_dir: Path) -> None:
    raw = read_table(input_path)
    age_col = find_column(raw.columns, AGE_GROUP_CANDIDATES)
    sip_col = find_column(raw.columns, SIP_AMOUNT_CANDIDATES, required=False)
    gender_col = find_column(raw.columns, GENDER_CANDIDATES, required=False)
    count_col = find_column(raw.columns, INVESTOR_COUNT_CANDIDATES, required=False)
    transaction_col = find_column(raw.columns, ("transaction type", "type"), required=False)

    demo = raw.copy()
    if transaction_col:
        demo = demo[demo[transaction_col].astype(str).str.upper().str.strip() == "SIP"]
    demo[age_col] = demo[age_col].astype(str).str.strip()
    weights = pd.to_numeric(demo[count_col], errors="coerce") if count_col else None

    age_counts = (
        demo.groupby(age_col)[count_col].sum()
        if count_col
        else demo[age_col].value_counts()
    )
    sns.set_theme(style="whitegrid", context="talk")
    plt.figure(figsize=(9, 9))
    plt.pie(
        age_counts,
        labels=age_counts.index,
        autopct="%1.1f%%",
        startangle=90,
        wedgeprops={"linewidth": 1, "edgecolor": "white"},
    )
    plt.title("Investor Age Group Distribution")
    save_matplotlib(output_dir / "investor_age_group_pie.png")

    if sip_col:
        box = demo[[age_col, sip_col]].copy()
        box.columns = ["age_group", "sip_amount"]
        box["sip_amount"] = pd.to_numeric(box["sip_amount"], errors="coerce")
        box = box.dropna(subset=["age_group", "sip_amount"])
        if not box.empty:
            plt.figure(figsize=(12, 7))
            ax = sns.boxplot(data=box, x="age_group", y="sip_amount", color="#4c78a8")
            ax.set_title("SIP Amount Distribution by Age Group")
            ax.set_xlabel("Age group")
            ax.set_ylabel("SIP amount")
            plt.xticks(rotation=25, ha="right")
            save_matplotlib(output_dir / "sip_amount_box_by_age_group.png")

    if gender_col:
        gender_counts = (
            demo.groupby(gender_col)[count_col].sum()
            if count_col
            else demo[gender_col].astype(str).value_counts()
        )
        plt.figure(figsize=(9, 6))
        ax = sns.barplot(
            x=gender_counts.index.astype(str),
            y=gender_counts.values,
            hue=gender_counts.index.astype(str),
            palette="Set2",
            legend=False,
        )
        ax.set_title("Investor Gender Split")
        ax.set_xlabel("Gender")
        ax.set_ylabel("Investors" if count_col else "Records")
        save_matplotlib(output_dir / "investor_gender_split.png")

    if weights is not None and weights.notna().any():
        print("Used investor/count weights where available.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aum-input", type=Path)
    parser.add_argument("--sip-input", type=Path)
    parser.add_argument("--category-input", type=Path)
    parser.add_argument("--demographics-input", type=Path)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        aum_input = args.aum_input or discover_file(["aum"])
        sip_input = args.sip_input or discover_file(["sip"])
        category_input = args.category_input or discover_file(["category", "inflow"], exclude=["sip"])
        demographics_input = args.demographics_input or discover_file(["investor", "demographic"])

        plot_aum_growth(
            require_path(aum_input, "AUM", "aum"),
            args.output_dir / "aum_growth_by_fund_house_2022_2025.png",
        )
        plot_sip_inflow(
            require_path(sip_input, "SIP inflow", "sip"),
            args.output_dir / "sip_inflow_jan2022_dec2025_plotly.html",
        )
        plot_category_heatmap(
            require_path(category_input, "category inflow", "category or inflow"),
            args.output_dir / "category_inflow_heatmap.png",
        )
        plot_investor_demographics(
            require_path(demographics_input, "investor demographics", "investor or demographic"),
            args.output_dir,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise SystemExit(f"Error: {exc}") from None


if __name__ == "__main__":
    main()
