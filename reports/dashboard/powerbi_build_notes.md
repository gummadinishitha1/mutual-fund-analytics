# Bluestock MF Dashboard - Power BI Build Notes

## Data Load Verification

SQLite source: `bluestock_mf.db`

| Table | Rows |
| --- | ---: |
| `dim_fund` | 40 |
| `fact_aum_by_fund_house` | 90 |
| `fact_benchmark_indices` | 8,050 |
| `fact_category_inflows` | 144 |
| `fact_industry_folio_count` | 21 |
| `fact_monthly_sip_inflows` | 48 |
| `fact_nav` | 64,320 |
| `fact_performance` | 40 |
| `fact_portfolio_holdings` | 322 |
| `fact_transactions` | 32,778 |

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
