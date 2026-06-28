"""Plot daily mutual fund NAV trends with Plotly.

Expected input: one CSV/XLSX file with at least these logical fields:
- date column, for example: Date, NAV Date, nav_date
- scheme column, for example: Scheme Name, scheme_name, scheme
- NAV column, for example: NAV, Net Asset Value, nav

The script filters daily observations to 2022-01-01 through 2026-12-31,
keeps the first 40 schemes by observation count unless --top-schemes is changed,
and highlights the 2023 bull run plus 2024 correction windows.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "nav_trend_2022_2026_plotly.html"

DATE_CANDIDATES = (
    "date",
    "nav_date",
    "nav date",
    "navdate",
    "as_of_date",
    "valuation_date",
)
SCHEME_CANDIDATES = (
    "scheme",
    "scheme_name",
    "scheme name",
    "fund",
    "fund_name",
    "fund name",
)
NAV_CANDIDATES = (
    "nav",
    "net_asset_value",
    "net asset value",
    "netassetvalue",
    "nav_rs",
    "nav (rs)",
)


def normalize_column_name(name: str) -> str:
    return " ".join(str(name).strip().lower().replace("_", " ").split())


def find_column(columns: Iterable[str], candidates: Iterable[str]) -> str:
    normalized = {normalize_column_name(col): col for col in columns}
    for candidate in candidates:
        key = normalize_column_name(candidate)
        if key in normalized:
            return normalized[key]
    raise ValueError(
        "Could not infer required column. Available columns: "
        + ", ".join(map(str, columns))
    )


def find_input_file(data_dir: Path) -> Path:
    files = sorted(
        [
            *data_dir.glob("*.csv"),
            *data_dir.glob("*.xlsx"),
            *data_dir.glob("*.xls"),
        ]
    )
    if not files:
        raise FileNotFoundError(
            f"No CSV/XLSX files found in {data_dir}. "
            "Add the daily NAV dataset there or pass --input."
        )
    if len(files) > 1:
        preferred = [file for file in files if "nav" in file.stem.lower()]
        if len(preferred) == 1:
            return preferred[0]
        raise ValueError(
            "Multiple data files found. Pass --input explicitly. Candidates: "
            + ", ".join(str(file) for file in files)
        )
    return files[0]


def read_nav_data(input_path: Path) -> pd.DataFrame:
    if input_path.suffix.lower() == ".csv":
        return pd.read_csv(input_path)
    if input_path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(input_path)
    raise ValueError(f"Unsupported input format: {input_path.suffix}")


def prepare_nav_data(
    raw: pd.DataFrame,
    start_date: str,
    end_date: str,
    top_schemes: int,
) -> pd.DataFrame:
    date_col = find_column(raw.columns, DATE_CANDIDATES)
    scheme_col = find_column(raw.columns, SCHEME_CANDIDATES)
    nav_col = find_column(raw.columns, NAV_CANDIDATES)

    nav = raw[[date_col, scheme_col, nav_col]].copy()
    nav.columns = ["date", "scheme", "nav"]
    nav["date"] = pd.to_datetime(nav["date"], errors="coerce")
    nav["nav"] = pd.to_numeric(nav["nav"], errors="coerce")
    nav["scheme"] = nav["scheme"].astype(str).str.strip()
    nav = nav.dropna(subset=["date", "scheme", "nav"])

    date_mask = nav["date"].between(pd.Timestamp(start_date), pd.Timestamp(end_date))
    nav = nav.loc[date_mask]
    if nav.empty:
        raise ValueError(f"No NAV rows found between {start_date} and {end_date}.")

    scheme_counts = nav.groupby("scheme")["date"].count().sort_values(ascending=False)
    selected_schemes = scheme_counts.head(top_schemes).index
    nav = nav[nav["scheme"].isin(selected_schemes)].sort_values(["scheme", "date"])

    return nav


def add_market_highlights(fig: go.Figure) -> None:
    highlights = [
        {
            "name": "2023 bull run",
            "start": "2023-03-31",
            "end": "2023-12-29",
            "color": "rgba(46, 125, 50, 0.14)",
            "label_y": 1.07,
        },
        {
            "name": "2024 correction window",
            "start": "2024-03-01",
            "end": "2024-06-04",
            "color": "rgba(211, 47, 47, 0.13)",
            "label_y": 1.01,
        },
        {
            "name": "late-2024 correction",
            "start": "2024-09-27",
            "end": "2024-11-21",
            "color": "rgba(211, 47, 47, 0.10)",
            "label_y": 0.95,
        },
    ]

    for item in highlights:
        fig.add_vrect(
            x0=item["start"],
            x1=item["end"],
            fillcolor=item["color"],
            line_width=0,
            layer="below",
            annotation_text=item["name"],
            annotation_position="top left",
        )


def build_figure(nav: pd.DataFrame) -> go.Figure:
    fig = px.line(
        nav,
        x="date",
        y="nav",
        color="scheme",
        title="Daily NAV Trend for Mutual Fund Schemes, 2022-2026",
        labels={"date": "Date", "nav": "NAV", "scheme": "Scheme"},
        template="plotly_white",
    )
    add_market_highlights(fig)
    fig.update_traces(line={"width": 1.4}, opacity=0.82)
    fig.update_layout(
        hovermode="x unified",
        legend_title_text="Scheme",
        height=850,
        margin={"l": 70, "r": 40, "t": 90, "b": 70},
        xaxis={
            "rangeslider": {"visible": True},
            "rangeselector": {
                "buttons": [
                    {"count": 1, "label": "1Y", "step": "year", "stepmode": "backward"},
                    {"count": 2, "label": "2Y", "step": "year", "stepmode": "backward"},
                    {"step": "all", "label": "All"},
                ]
            },
        },
        yaxis={"tickformat": ".2f"},
    )
    return fig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Path to NAV CSV/XLSX file.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--start-date", default="2022-01-01")
    parser.add_argument("--end-date", default="2026-12-31")
    parser.add_argument("--top-schemes", type=int, default=40)
    parser.add_argument(
        "--png",
        type=Path,
        help="Optional PNG export path. Requires the kaleido package.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        input_path = args.input or find_input_file(DEFAULT_DATA_DIR)
        raw = read_nav_data(input_path)
        nav = prepare_nav_data(raw, args.start_date, args.end_date, args.top_schemes)
        fig = build_figure(nav)

        args.output.parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(args.output, include_plotlyjs="cdn")
        print(f"Wrote interactive Plotly chart: {args.output}")
        print(f"Schemes plotted: {nav['scheme'].nunique()}")
        print(f"Rows plotted: {len(nav):,}")

        if args.png:
            if args.png.parent.exists() and not args.png.parent.is_dir():
                raise ValueError(
                    f"PNG output parent exists but is not a directory: {args.png.parent}"
                )
            args.png.parent.mkdir(parents=True, exist_ok=True)
            fig.write_image(args.png, width=1800, height=950, scale=2)
            print(f"Wrote PNG chart: {args.png}")
    except (FileNotFoundError, ValueError) as exc:
        raise SystemExit(f"Error: {exc}") from None


if __name__ == "__main__":
    main()
