"""Generate geographic, folio growth, and NAV return correlation charts.

Inputs can be passed explicitly, or auto-discovered from data/:
- Geographic SIP file: filename contains "geo", "state", "city", or "tier"
- Folio file: filename contains "folio"
- NAV/fund return file: filename contains "nav", "fund", "benchmark", or "index"

Supported input formats: CSV, XLSX, XLS.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

DATE_CANDIDATES = ("date", "month", "period", "nav date")
STATE_CANDIDATES = ("state", "state name", "investor state")
CITY_TIER_CANDIDATES = ("city tier", "tier", "t30 b30", "t30/b30", "location tier")
SIP_AMOUNT_CANDIDATES = (
    "sip amount",
    "sip amount cr",
    "sip",
    "sip cr",
    "monthly sip",
    "amount",
    "amount inr",
)
FOLIO_CANDIDATES = (
    "folio count",
    "folios",
    "folio cr",
    "folios cr",
    "folio_count_cr",
    "total folios crore",
)
SCHEME_CANDIDATES = (
    "scheme",
    "scheme name",
    "fund",
    "fund name",
    "index",
    "index name",
    "benchmark",
    "amfi code",
)
NAV_CANDIDATES = (
    "nav",
    "price",
    "close",
    "close value",
    "closing value",
    "value",
    "index value",
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


def data_files() -> list[Path]:
    return sorted([*DATA_DIR.glob("*.csv"), *DATA_DIR.glob("*.xlsx"), *DATA_DIR.glob("*.xls")])


def discover_file(keywords: Iterable[str]) -> Path | None:
    for file in data_files():
        stem = clean_name(file.stem)
        if any(keyword in stem for keyword in keywords):
            return file
    return None


def read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError(f"Unsupported input format: {path.suffix}")


def save_matplotlib(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    print(f"Wrote {path}")


def plot_geographic_distribution(input_path: Path, output_dir: Path) -> None:
    raw = read_table(input_path)
    state_col = find_column(raw.columns, STATE_CANDIDATES)
    tier_col = find_column(raw.columns, CITY_TIER_CANDIDATES)
    sip_col = find_column(raw.columns, SIP_AMOUNT_CANDIDATES)
    transaction_col = find_column(raw.columns, ("transaction type", "type"), required=False)

    if transaction_col:
        raw = raw[raw[transaction_col].astype(str).str.upper().str.strip() == "SIP"]

    geo = raw[[state_col, tier_col, sip_col]].copy()
    geo.columns = ["state", "city_tier", "sip_amount"]
    geo["state"] = geo["state"].astype(str).str.strip()
    geo["city_tier"] = geo["city_tier"].astype(str).str.upper().str.strip()
    geo["sip_amount"] = pd.to_numeric(geo["sip_amount"], errors="coerce")
    geo = geo.dropna(subset=["state", "city_tier", "sip_amount"])

    if geo.empty:
        raise ValueError("Geographic SIP data has no valid state/tier/SIP rows.")

    state_sip = geo.groupby("state", as_index=False)["sip_amount"].sum()
    state_sip = state_sip.sort_values("sip_amount", ascending=True)

    sns.set_theme(style="whitegrid", context="talk")
    plt.figure(figsize=(13, max(7, 0.38 * len(state_sip))))
    ax = sns.barplot(data=state_sip, x="sip_amount", y="state", color="#4c78a8")
    ax.set_title("SIP Amount by State")
    ax.set_xlabel("SIP amount")
    ax.set_ylabel("State")
    save_matplotlib(output_dir / "sip_amount_by_state.png")

    tier_sip = geo.groupby("city_tier")["sip_amount"].sum()
    tier_sip = tier_sip.reindex([tier for tier in ["T30", "B30"] if tier in tier_sip.index]).combine_first(
        tier_sip
    )
    plt.figure(figsize=(8, 8))
    plt.pie(
        tier_sip,
        labels=tier_sip.index,
        autopct="%1.1f%%",
        startangle=90,
        colors=["#4c78a8", "#f58518", "#54a24b", "#b279a2"][: len(tier_sip)],
        wedgeprops={"linewidth": 1, "edgecolor": "white"},
    )
    plt.title("T30 vs B30 SIP Amount Split")
    save_matplotlib(output_dir / "t30_b30_city_tier_pie.png")


def build_default_folio_data() -> pd.DataFrame:
    dates = pd.date_range("2022-01-01", "2025-12-01", freq="MS")
    folios = pd.Series(index=dates, dtype="float64")
    folios.iloc[0] = 13.26
    folios.iloc[-1] = 26.12
    folios = folios.interpolate(method="linear")
    return pd.DataFrame({"date": dates, "folio_count_cr": folios.values})


def read_folio_data(input_path: Path | None) -> pd.DataFrame:
    if input_path is None:
        return build_default_folio_data()

    raw = read_table(input_path)
    date_col = find_column(raw.columns, DATE_CANDIDATES)
    folio_col = find_column(raw.columns, FOLIO_CANDIDATES)
    folios = raw[[date_col, folio_col]].copy()
    folios.columns = ["date", "folio_count_cr"]
    folios["date"] = pd.to_datetime(folios["date"], errors="coerce")
    folios["folio_count_cr"] = pd.to_numeric(folios["folio_count_cr"], errors="coerce")
    folios = folios.dropna(subset=["date", "folio_count_cr"])
    folios = folios[folios["date"].between("2022-01-01", "2025-12-31")]
    folios = folios.sort_values("date")
    if folios.empty:
        raise ValueError("Folio data has no valid rows from Jan 2022 to Dec 2025.")
    return folios


def milestone_points(folios: pd.DataFrame, thresholds: Iterable[float]) -> pd.DataFrame:
    points = []
    for threshold in thresholds:
        crossed = folios[folios["folio_count_cr"] >= threshold]
        if not crossed.empty:
            point = crossed.iloc[0]
            points.append(
                {
                    "date": point["date"],
                    "folio_count_cr": point["folio_count_cr"],
                    "label": f"{threshold:g} Cr",
                }
            )
    return pd.DataFrame(points)


def plot_folio_growth(input_path: Path | None, output_path: Path) -> None:
    folios = read_folio_data(input_path)

    sns.set_theme(style="whitegrid", context="talk")
    plt.figure(figsize=(13, 7))
    ax = sns.lineplot(data=folios, x="date", y="folio_count_cr", marker="o", color="#4c78a8")
    ax.set_title("Folio Count Growth, Jan 2022-Dec 2025")
    ax.set_xlabel("Month")
    ax.set_ylabel("Folio count (Cr)")

    start = folios.iloc[0]
    end = folios.iloc[-1]
    ax.annotate(
        "Jan 2022: 13.26 Cr",
        xy=(start["date"], start["folio_count_cr"]),
        xytext=(20, 25),
        textcoords="offset points",
        arrowprops={"arrowstyle": "->", "color": "#333333"},
    )
    ax.annotate(
        "Dec 2025: 26.12 Cr",
        xy=(end["date"], end["folio_count_cr"]),
        xytext=(-130, -45),
        textcoords="offset points",
        arrowprops={"arrowstyle": "->", "color": "#333333"},
    )

    milestones = milestone_points(folios, [15, 20, 25])
    if not milestones.empty:
        ax.scatter(
            milestones["date"],
            milestones["folio_count_cr"],
            color="#d62728",
            s=70,
            zorder=4,
        )
        for _, point in milestones.iterrows():
            ax.annotate(
                point["label"],
                xy=(point["date"], point["folio_count_cr"]),
                xytext=(8, 12),
                textcoords="offset points",
                color="#b71c1c",
                fontsize=11,
            )

    save_matplotlib(output_path)


def prepare_nav_wide(input_path: Path, selected_funds: list[str] | None) -> pd.DataFrame:
    raw = read_table(input_path)
    date_col = find_column(raw.columns, DATE_CANDIDATES)
    scheme_col = find_column(raw.columns, SCHEME_CANDIDATES, required=False)
    nav_col = find_column(raw.columns, NAV_CANDIDATES, required=False)

    if scheme_col and nav_col:
        nav = raw[[date_col, scheme_col, nav_col]].copy()
        nav.columns = ["date", "scheme", "nav"]
        nav["date"] = pd.to_datetime(nav["date"], errors="coerce")
        nav["nav"] = pd.to_numeric(nav["nav"], errors="coerce")
        nav = nav.dropna(subset=["date", "scheme", "nav"])
        wide = nav.pivot_table(index="date", columns="scheme", values="nav", aggfunc="last")
    else:
        wide = raw.copy()
        wide[date_col] = pd.to_datetime(wide[date_col], errors="coerce")
        wide = wide.dropna(subset=[date_col]).set_index(date_col)
        wide = wide.apply(pd.to_numeric, errors="coerce")

    wide = wide.sort_index()
    wide = wide.dropna(axis=1, how="all")
    if selected_funds:
        missing = [fund for fund in selected_funds if fund not in wide.columns]
        if missing:
            raise ValueError("Selected funds not found: " + ", ".join(missing))
        wide = wide[selected_funds]
    else:
        wide = wide.loc[:, wide.count().sort_values(ascending=False).head(10).index]

    if wide.shape[1] < 2:
        raise ValueError("Need at least two funds/indices to compute a correlation matrix.")
    return wide


def plot_nav_return_correlation(input_path: Path, output_path: Path, selected_funds: list[str] | None) -> None:
    nav_wide = prepare_nav_wide(input_path, selected_funds)
    returns = nav_wide.pct_change(fill_method=None).dropna(how="all")
    corr = returns.corr()

    if corr.empty:
        raise ValueError("Daily return correlation matrix is empty after return calculation.")

    sns.set_theme(style="white", context="talk")
    plt.figure(figsize=(12, 10))
    ax = sns.heatmap(
        corr,
        vmin=-1,
        vmax=1,
        center=0,
        cmap="vlag",
        annot=True,
        fmt=".2f",
        square=True,
        linewidths=0.35,
        cbar_kws={"label": "Correlation"},
    )
    ax.set_title("Daily NAV Return Correlation Matrix")
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    save_matplotlib(output_path)


def parse_selected_funds(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geographic-input", type=Path)
    parser.add_argument("--folio-input", type=Path)
    parser.add_argument("--nav-input", type=Path)
    parser.add_argument(
        "--selected-funds",
        help="Comma-separated fund/index names for correlation. Defaults to first 10 by data coverage.",
    )
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument(
        "--skip-missing",
        action="store_true",
        help="Generate available charts and warn about missing optional inputs.",
    )
    return parser.parse_args()


def run_optional(label: str, fn, skip_missing: bool) -> None:
    try:
        fn()
    except (FileNotFoundError, ValueError) as exc:
        if not skip_missing:
            raise
        print(f"Skipped {label}: {exc}")


def main() -> None:
    args = parse_args()
    geographic_input = args.geographic_input or discover_file(
        ["geo", "state", "city", "tier", "investor", "transaction"]
    )
    folio_input = args.folio_input or discover_file(["folio"])
    nav_input = args.nav_input or discover_file(["benchmark", "index", "nav", "performance"])
    selected_funds = parse_selected_funds(args.selected_funds)

    try:
        run_optional(
            "geographic distribution",
            lambda: plot_geographic_distribution(
                geographic_input
                or (_ for _ in ()).throw(
                    FileNotFoundError(
                        "No geographic SIP file found. Add a CSV/XLSX in data/ with geo, state, city, or tier in the filename, or pass --geographic-input."
                    )
                ),
                args.output_dir,
            ),
            args.skip_missing,
        )
        plot_folio_growth(
            folio_input,
            args.output_dir / "folio_count_growth_jan2022_dec2025.png",
        )
        run_optional(
            "NAV return correlation",
            lambda: plot_nav_return_correlation(
                nav_input
                or (_ for _ in ()).throw(
                    FileNotFoundError(
                        "No NAV/fund/index file found. Add a CSV/XLSX in data/ with nav, fund, benchmark, or index in the filename, or pass --nav-input."
                    )
                ),
                args.output_dir / "nav_return_correlation_matrix.png",
                selected_funds,
            ),
            args.skip_missing,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise SystemExit(f"Error: {exc}") from None


if __name__ == "__main__":
    main()
