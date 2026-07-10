from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "scheme_performance_cleaned.csv"
)


def recommend_funds(top_n: int = 5) -> pd.DataFrame:
    """
    Recommend top mutual funds based on performance metrics.
    """

    try:
        df = pd.read_csv(DATA_PATH)

    except FileNotFoundError:
        print(f"File not found: {DATA_PATH}")
        return pd.DataFrame()

    except Exception as e:
        print(f"Error loading dataset: {e}")
        return pd.DataFrame()


    if df.empty:
        print("Dataset is empty.")
        return pd.DataFrame()


    required_columns = [
        "scheme_name",
        "return_1yr_pct",
        "return_3yr_pct",
        "return_5yr_pct"
    ]


    missing = [
        col for col in required_columns
        if col not in df.columns
    ]


    if missing:
        print(f"Missing columns: {missing}")
        return pd.DataFrame()


    # Composite performance score
    df["recommendation_score"] = (
        df["return_1yr_pct"] * 0.3 +
        df["return_3yr_pct"] * 0.3 +
        df["return_5yr_pct"] * 0.4
    )


    recommendations = (
        df.sort_values(
            by="recommendation_score",
            ascending=False
        )
        .head(top_n)
    )


    return recommendations[
        [
            "scheme_name",
            "fund_house",
            "category",
            "return_1yr_pct",
            "return_3yr_pct",
            "return_5yr_pct",
            "sharpe_ratio",
            "recommendation_score"
        ]
    ]


if __name__ == "__main__":

    result = recommend_funds(5)

    print("\nTop Recommended Mutual Funds")
    print("=" * 70)

    if result.empty:
        print("No recommendations generated.")

    else:
        print(result.to_string(index=False))