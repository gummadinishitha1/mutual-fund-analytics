# Fund Performance Analytics

## Morning Work Summary

This folder contains the performance analytics work completed on June 29, 2026. The analysis extends the cleaned mutual fund dataset into return, risk, benchmark, and scorecard outputs for comparing fund performance.

## What Was Built

- Created a reusable Python analysis script: `src/performance_analytics.py`
- Generated a Jupyter notebook wrapper: `notebooks/Performance_Analytics.ipynb`
- Calculated daily fund returns from cleaned NAV history
- Calculated 1-year, 3-year, and 5-year CAGR values where enough history exists
- Built risk metrics including annualized volatility, Sharpe ratio, Sortino ratio, and maximum drawdown
- Estimated alpha, beta, R-squared, and regression p-values against `NIFTY100`
- Compared top funds against `NIFTY50` and `NIFTY100`
- Created tracking error outputs for the top 5 scorecard funds
- Built a weighted fund scorecard to rank schemes across return, risk, alpha, expense ratio, and drawdown

## Scorecard Methodology

The final `fund_score` is a weighted 0-100 ranking based on:

| Metric | Weight | Direction |
| --- | ---: | --- |
| 3-year CAGR | 30% | Higher is better |
| Sharpe ratio | 25% | Higher is better |
| Alpha | 20% | Higher is better |
| Expense ratio | 15% | Lower is better |
| Maximum drawdown | 10% | Less negative is better |

## Key Outputs

| File | Description |
| --- | --- |
| `reports/performance_analytics/daily_returns.csv` | Daily percentage returns by AMFI code |
| `reports/performance_analytics/daily_return_distribution.csv` | Return distribution checks and outlier validation |
| `reports/performance_analytics/cagr_comparison.csv` | 1-year, 3-year, and 5-year CAGR comparison |
| `reports/performance_analytics/alpha_beta.csv` | Alpha, beta, R-squared, and p-value by fund |
| `reports/performance_analytics/fund_scorecard.csv` | Ranked fund scorecard with return and risk metrics |
| `reports/performance_analytics/tracking_error_top5.csv` | Tracking error for top 5 funds vs NIFTY50 and NIFTY100 |
| `reports/performance_analytics/benchmark_comparison_top5.png` | Indexed benchmark comparison chart for top 5 funds |

## Top Scorecard Funds

The highest ranked schemes in the generated scorecard are:

1. Mirae Asset Large Cap Fund - Regular - Growth
2. ICICI Pru Midcap Fund - Regular - Growth
3. Kotak Flexicap Fund - Regular - Growth
4. HDFC Mid-Cap Opportunities Fund - Regular - Growth
5. ICICI Pru Bluechip Fund - Direct - Growth

## How To Rerun

From the main repository root:

```powershell
python src/performance_analytics.py
```

The script reads cleaned input files from:

```text
data/processed/
```

It writes updated analytics outputs to:

```text
reports/performance_analytics/
```

## Source Data Used

The analysis uses these cleaned datasets:

- `nav_history_cleaned.csv`
- `benchmark_indices_cleaned.csv`
- `fund_master_cleaned.csv`

## Technologies Used

- Python
- pandas
- NumPy
- Matplotlib
- SciPy, with a NumPy fallback for regression
- nbformat
- Jupyter Notebook

## Status

Morning performance analytics deliverables are complete. The generated outputs are ready for review, presentation, or use in downstream dashboard work.
